import uvicorn
from pydantic import BaseModel
from datetime import date
from fastapi import FastAPI
from fastapi import File, UploadFile, Form
import csv, pyodbc
import json
import pandas as pd
from operator import add
import joblib
import webbrowser
import warnings
from pandas import json_normalize
from io import BytesIO
#import httplib

# def patch_http_response_read(func):
    # def inner(*args):
        # try:
            # return func(*args)
        # except httplib.IncompleteRead as e:
            # return e.partial
    # return inner

# httplib.HTTPResponse.read = patch_http_response_read(httplib.HTTPResponse.read)

warnings.filterwarnings('ignore')

app = FastAPI()

classifier=joblib.load('classifier.pkl')

class Record(BaseModel):
    mdb_filepath: str
    ramp_up: int
    steady_state: int
    
# class Data(BaseModel):
    # df_in: str
    # flow_type: str

def functionThatConnectsDatabase(mdb_filepath, rampup_time, steady_state):
    

    MDB = f'{mdb_filepath}'
    DRV = '{Microsoft Access Driver (*.mdb, *.accdb)}'
    PWD = 'pw'
    con = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(DRV,MDB,PWD))
    cur = con.cursor()
    
    ramp_up_duration = rampup_time
    steadystateEndTime = steady_state

    #### Creating a Master Dataframe for Event_meter that stores All data associated to Test
            # Event_meter: Stores metadata corresponding to event ID that generated during the run 
    masterDataFrameForEvent_meterForSteadyState = pd.read_sql_query(f'Select * from Event_meter where Event_meter.[End Time] > {ramp_up_duration} and Event_meter.[End Time] < {steadystateEndTime};',con)
            #Event_map: Stores medadata about Events IDs that generated during the run 
    masterDataFrameForEvent_mapForEntireRun = pd.read_sql_query(f'Select * from Event_map;',con)
    
    return (masterDataFrameForEvent_meterForSteadyState, masterDataFrameForEvent_mapForEntireRun)

##################################################### API#1 That will read the MDB file f current test and load it as Json: Starts ###################################################

def callPercentileFunction(df, value):
    df = df[df['Event ID'] == value]
    numberOfIteration = len(df['Value'])
    df = df.sort_values('Value')
    
    if numberOfIteration > 0:
        perc75 = df.loc[df.index[round((numberOfIteration*0.75)-1)],'Value']
        perc80 = df.loc[df.index[round((numberOfIteration*0.80)-1)],'Value']
        perc85 = df.loc[df.index[round((numberOfIteration*0.85)-1)],'Value']
        perc90 = df.loc[df.index[round((numberOfIteration*0.90)-1)],'Value']
        perc95 = df.loc[df.index[round((numberOfIteration*0.95)-1)],'Value']
    else:
        perc75 = 0
        perc80 = 0
        perc85 = 0
        perc90 = 0
        perc95 = 0
    return perc75,perc80,perc85,perc90,perc95

def clean_NANValue(dummy_df):
    dummy_df['Standard SLA'] = dummy_df['Standard SLA'].fillna(0)
    dummy_df['Baseline SLA'] = dummy_df['Baseline SLA'].fillna(0)
    dummy_df['Expected Volume'] = dummy_df['Expected Volume'].fillna(0)
    dummy_df['Response time difference (when compared to SLA)'] = dummy_df['Response time difference (when compared to SLA)'].fillna(0)
    
    return dummy_df


@app.post("/fetchdata")
def call(item : Record):
    
    event_MeterDataFrame, event_MapDataFrame = functionThatConnectsDatabase(item.mdb_filepath, item.ramp_up, item.steady_state)
    
    # Defining Some List Variables to hold value and can convert to DataFrame easily
    listOfEventsOccursInSteadyState = []
    averageValue = []
    percentile75 = []
    percentile80 = []
    percentile85 = []
    percentile90 = []
    percentile95 = []
    passedTransaction = []
    failedTransaction = []
    
    finalObtainedDataframe = pd.DataFrame(
    columns = ["Transaction Name","Standard SLA","Baseline SLA","Expected Volume","Passed trx","Failed trx","Average response time","Min","Max","Response time difference (when compared to SLA)","75%","80%","85%","90%","95%"]
    )
        # Creating a DataFrame that hold Event_Map data only for those data which are transaction in nature
    transactionDataframeFromEvent_MapForEntireRun = event_MapDataFrame[event_MapDataFrame['Event Type'] == 'Transaction']
            
    #creating a condition where Compiler picks only those events Ids which occurs in Steady state
    for eventNumber in transactionDataframeFromEvent_MapForEntireRun['Event ID']:
        if eventNumber in event_MeterDataFrame['Event ID'].unique():
            listOfEventsOccursInSteadyState.append(eventNumber)
    finalObtainedDataframe['Transaction Name'] = transactionDataframeFromEvent_MapForEntireRun[transactionDataframeFromEvent_MapForEntireRun["Event ID"].isin(listOfEventsOccursInSteadyState)]['Event Name']
    finalObtainedDataframe['Max'] = event_MeterDataFrame[event_MeterDataFrame['Event ID'].isin(listOfEventsOccursInSteadyState)]['Amaximum']
    finalObtainedDataframe['Min'] = event_MeterDataFrame[event_MeterDataFrame['Event ID'].isin(listOfEventsOccursInSteadyState)]['Aminimum']
    
    
    #finalObtainedDataframe['Passed trx'] = event_MeterDataFrame[(event_MeterDataFrame['Status1'] == 1).isin(listOfEventsOccursInSteadyState)]['Status1']
    
    event_MeterDataFrame['Value*Acount'] = event_MeterDataFrame['Value']*event_MeterDataFrame['Acount']
        
    for value in listOfEventsOccursInSteadyState:
        averageValue.append(event_MeterDataFrame[event_MeterDataFrame['Event ID'] == value]['Value*Acount'].sum()/event_MeterDataFrame[event_MeterDataFrame['Event ID'] == value]['Acount'].sum())
        perc75, perc80, perc85, perc90, perc95 = callPercentileFunction(event_MeterDataFrame, value)
        percentile75.append(perc75)
        percentile80.append(perc80)
        percentile85.append(perc85)
        percentile90.append(perc90)
        percentile95.append(perc95)
        passedTransaction.append(len(event_MeterDataFrame[(event_MeterDataFrame['Status1'] == 1) & event_MeterDataFrame['Event ID'].isin([value])]))
        failedTransaction.append(len(event_MeterDataFrame[(event_MeterDataFrame['Status1'] == 0) & event_MeterDataFrame['Event ID'].isin([value])]))
    finalObtainedDataframe['Average response time'] = averageValue
    finalObtainedDataframe['75%'] = percentile75
    finalObtainedDataframe['80%'] = percentile80
    finalObtainedDataframe['85%'] = percentile85
    finalObtainedDataframe['90%'] = percentile90
    finalObtainedDataframe['95%'] = percentile95
    finalObtainedDataframe['Passed trx'] = passedTransaction
    finalObtainedDataframe['Failed trx'] = failedTransaction
    finalObtainedDataframe = clean_NANValue(finalObtainedDataframe)
    json_string = finalObtainedDataframe.to_json(orient='records')
        #getdataApi(json_string)
    json_data = json.loads(json_string)
    return json_data
        
    
#-------------------------------------------------------------------Creating API To Change column Name-------------------------------------------------------------------------------
############################################# API#3 That will read the dataframe, predict color for the transaction and load it as Json: Starts #####################################
#Declaring clean_file function to rename the columns name
def clean_file(df1) :
    df1.rename(columns = {'Transaction Name':'TransactionName'}, inplace = True)
    df1.rename(columns = {'Response time difference (when compared to SLA)':'RTSLA'}, inplace = True)
    df1.rename(columns = {'Standard SLA':'Standard_SLA'}, inplace = True)
    df1.rename(columns = {'Baseline SLA':'Baseline_SLA'}, inplace = True)
    df1.rename(columns = {'Expected Volume':'Expected_Volume'}, inplace = True)
    df1.rename(columns = {'Passed trx':'Passed_trx'}, inplace = True)
    df1.rename(columns = {'Failed trx':'Failed_trx'}, inplace = True)
    df1['Average response time'] = df1['Average response time'].fillna(0)
    df1['80%'] = df1['80%'].fillna(0)
    df1['85%'] = df1['85%'].fillna(0)
    df1['90%'] = df1['90%'].fillna(0)
    df1['95%'] = df1['95%'].fillna(0)
    df1['Min'] = df1['Min'].fillna(0)
    df1['Max'] = df1['Max'].fillna(0)
    df1['Baseline_SLA'] = df1['Baseline_SLA'].fillna(0)
    return df1
#-------------------------------------------------------------------Function to highlighting RTSLA column----------------------------------------------------------------------------
def evaluatingRTSLA(df_old):
    #reading data of Baseline_SLA column only as a Dataframe
    #BaselineSLA_df = pd.read_csv(csvFile, usecols = ['Baseline SLA'])
    BaselineSLA_list = df_old['Baseline_SLA'].values.tolist()
    #AverageRT_df = pd.read_csv(csvFile, usecols = ['Average response time'])
    NinetyPercentage_list = df_old['90%'].values.tolist()
    difference_list = []
    print(NinetyPercentage_list)
    print(BaselineSLA_list)
    l = len(NinetyPercentage_list)
    for i in range(l):
        difference_list.append(NinetyPercentage_list[i]- BaselineSLA_list[i])
    difference_df = pd.DataFrame(difference_list)
    df_old["RTSLA"] = difference_df[0]
    #print(df_old)
    return df_old

#---------------------------------Expose the prediction functionality, make a prediction from the passed JSON data and return the predicted Bank Note with the confidence----------

#def predict_color(df_in, flow_type : str):
#async def predict_color(file: UploadFile = File(...), flow_type: str = Form(...)):
@app.post('/predict')
async def predict_color(
        file: UploadFile = File(...),
        Flow_Type: str = Form(...),
        ):
    contents = await file.read()
#    data_str = contents.decode('utf-8')
    df = pd.read_csv(BytesIO(contents))
    flow_type = Flow_Type
    #print(df_method1)
# reading csvFile as a dataframe 
    #df = pd.read_csv(file.read())
    #df = pd.read_csv(csvFile, encoding= 'unicode_escape')
    #df = pd.read_json(df_in)
    #df = df_in
    df_test_org = clean_file(df)
    #calculating RT differnce RTSLA
    #df_update = evaluatingRTSLA(df_test_org)
    df_update = df_test_org
    df_test = df_update.drop('TransactionName',axis=1)
#     test_data=np.array(pd.DataFrame(df_test))
    test_data=df_test.to_numpy()
#predicting the color based on pickle    
    prediction = classifier.predict(test_data)
    df_test_org['color'] = prediction
    df_test_org['Comments'] = ""
    # Checking for 0 value in Baseline and standard SLA column
    for i in range(len(df_test_org['color'])) :
        if flow_type == "GUI Flow": 
            if (df_test_org.loc[i,"RTSLA"]<=5):
                df_test_org.loc[i,'color'] = 'Green'
            if (df_test_org['Baseline_SLA'][i] == 0 and df_test_org['Standard_SLA'][i] == 0) :
                if (df_test_org.loc[i,"RTSLA"]<=5) :
                    df_test_org.loc[i,'color'] = 'Green'
                if ((df_test_org.loc[i,"RTSLA"]>5) and (df_test_org.loc[i,"RTSLA"]<=10)) :
                    df_test_org.loc[i,'color'] = 'Amber'
                    df_test_org.loc[i,'Comments'] = 'As no SLA is provided, and Response time is 5 secs, hence needs to be investigated'
                if (df_test_org.loc[i,"RTSLA"]>10):
                    df_test_org.loc[i,'color'] = 'Red'
                    df_test_org.loc[i,'Comments'] = 'As no SLA is provided, and Response time is 5 secs, hence needs to be investigated'
                
        if flow_type == "API Flow":
            if (df_test_org.loc[i,"RTSLA"]<=3):
                df_test_org.loc[i,'color'] = 'Green'
                
            if (df_test_org['Baseline_SLA'][i] == 0 and df_test_org['Standard_SLA'][i] == 0) :
                if (df_test_org.loc[i,"RTSLA"]<=3) :
                    df_test_org.loc[i,'Comments'] = 'Green'
                if ((df_test_org.loc[i,"RTSLA"]>3) and (df_test_org.loc[i,"RTSLA"]<=5)) :
                    df_test_org.loc[i,'color'] = 'Amber'
                    df_test_org.loc[i,'Comments'] = 'As no SLA is provided, and Response time is 3 secs, hence needs to be investigated'
                if (df_test_org.loc[i,"RTSLA"]>5):
                    df_test_org.loc[i,'color'] = 'Red'
                    df_test_org.loc[i,'Comments'] = 'As no SLA is provided, and Response time is 3 secs, hence needs to be investigated'

#converting dataframe to string
    json_data = df_test_org.to_json(orient='records')
#converting json to json dictionary 
    json_file = json.loads(json_data)
#Returing json dictionary to web API  
    return json_file
############################################# API#3 That will read the dataframe, predict color for the transaction and load it as Json: Ends #######################################

    
@app.post("/ErrorAnalysis")
def errorData(path3: str):
    MDB = r''+path3
    DRV = '{Microsoft Access Driver (*.mdb, *.accdb)}'
    PWD = 'pw'
    #conn = pyodbc. connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:\Users\PawarP2\Downloads\Excelerator\Results_4092\Results_4092.mdb;')
    conn = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(DRV,MDB,PWD))
    cursor = conn. cursor()
    sql_read = pd. read_sql_query('''SELECT Script.[Script Name],Count(Script.[Script Name]),event_map.[Event Name] FROM Script,WebEvent_meter,event_map WHERE (((WebEvent_Meter.[Script ID])=Script.[Script ID]) AND ((event_map.[Event ID])=WebEvent_meter.[Event ID]) AND ((event_map.[Event Name]) Like 'HTTP_3%' Or (event_map.[Event Name]) Like 'HTTP_4%' Or (event_map.[Event Name]) Like 'HTTP_5%')) GROUP BY Script.[Script Name], event_map.[Event Name]''',conn)
    error_df = pd.DataFrame(sql_read)
    json_string = error_df.to_json(orient='records')
    json_data = json.loads(json_string)
####################################changes Made###########################################
    sql_read1 = pd. read_sql_query('''Select C.[Event Name],Count(C.[Event Name]), B.[Error Message] from [Event_map] as C ,[Error_meter] as A,[ErrorMessage] as B where A.[Error ID]=B.[Error ID] and C.[Event ID]=A.[Father ID] Group By C.[Event Name],B.[Error Message]''',conn)
    TransactionError_df = pd.DataFrame(sql_read1)
    json_string1 = TransactionError_df.to_json(orient='records')
    json_data1 = json.loads(json_string1)

    
    return [json_data,json_data1]
@app.post("/previousResults")
def previousResults(item : Record):
    
    event_MeterDataFrame, event_MapDataFrame = functionThatConnectsDatabase(item.mdb_filepath, item.ramp_up, item.steady_state)
    
    # Defining Some List Variables to hold value and can convert to DataFrame easily
    listOfEventsOccursInSteadyState = []
    averageValue = []
    percentile75 = []
    percentile80 = []
    percentile85 = []
    percentile90 = []
    percentile95 = []
    passedTransaction = []
    failedTransaction = []
    
    finalObtainedDataframe = pd.DataFrame(
    columns = ["Transaction Name","Standard SLA","Baseline SLA","Expected Volume","Passed trx","Failed trx","Average response time","Min","Max","Response time difference (when compared to SLA)","75%","80%","85%","90%","95%"]
    )
        # Creating a DataFrame that hold Event_Map data only for those data which are transaction in nature
    transactionDataframeFromEvent_MapForEntireRun = event_MapDataFrame[event_MapDataFrame['Event Type'] == 'Transaction']
            
    #creating a condition where Compiler picks only those events Ids which occurs in Steady state
    for eventNumber in transactionDataframeFromEvent_MapForEntireRun['Event ID']:
        if eventNumber in event_MeterDataFrame['Event ID'].unique():
            listOfEventsOccursInSteadyState.append(eventNumber)
    finalObtainedDataframe['Transaction Name'] = transactionDataframeFromEvent_MapForEntireRun[transactionDataframeFromEvent_MapForEntireRun["Event ID"].isin(listOfEventsOccursInSteadyState)]['Event Name']
    finalObtainedDataframe['Max'] = event_MeterDataFrame[event_MeterDataFrame['Event ID'].isin(listOfEventsOccursInSteadyState)]['Amaximum']
    finalObtainedDataframe['Min'] = event_MeterDataFrame[event_MeterDataFrame['Event ID'].isin(listOfEventsOccursInSteadyState)]['Aminimum']
    
    
    #finalObtainedDataframe['Passed trx'] = event_MeterDataFrame[(event_MeterDataFrame['Status1'] == 1).isin(listOfEventsOccursInSteadyState)]['Status1']
    
    event_MeterDataFrame['Value*Acount'] = event_MeterDataFrame['Value']*event_MeterDataFrame['Acount']
        
    for value in listOfEventsOccursInSteadyState:
        averageValue.append(event_MeterDataFrame[event_MeterDataFrame['Event ID'] == value]['Value*Acount'].sum()/event_MeterDataFrame[event_MeterDataFrame['Event ID'] == value]['Acount'].sum())
        perc75, perc80, perc85, perc90, perc95 = callPercentileFunction(event_MeterDataFrame, value)
        percentile75.append(perc75)
        percentile80.append(perc80)
        percentile85.append(perc85)
        percentile90.append(perc90)
        percentile95.append(perc95)
        passedTransaction.append(len(event_MeterDataFrame[(event_MeterDataFrame['Status1'] == 1) & event_MeterDataFrame['Event ID'].isin([value])]))
        failedTransaction.append(len(event_MeterDataFrame[(event_MeterDataFrame['Status1'] == 0) & event_MeterDataFrame['Event ID'].isin([value])]))
    finalObtainedDataframe['Average response time'] = averageValue
    finalObtainedDataframe['75%'] = percentile75
    finalObtainedDataframe['80%'] = percentile80
    finalObtainedDataframe['85%'] = percentile85
    finalObtainedDataframe['90%'] = percentile90
    finalObtainedDataframe['95%'] = percentile95
    finalObtainedDataframe['Passed trx'] = passedTransaction
    finalObtainedDataframe['Failed trx'] = failedTransaction
    finalObtainedDataframe = clean_NANValue(finalObtainedDataframe)
    json_string = finalObtainedDataframe.to_json(orient='records')
        #getdataApi(json_string)
    json_data = json.loads(json_string)
    return json_data 
 
if __name__ == "__main__":
    uvicorn.run(app, host = "127.0.0.1", port = "8000")
