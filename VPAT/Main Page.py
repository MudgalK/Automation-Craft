import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_extras.switch_page_button import switch_page
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import tempfile
import pandas as pd
from pandas import json_normalize
import json
import requests
import os,re
from datetime import datetime
import csv, pyodbc
#import Let's_Kick_Start
#from current_TestFile import main

import warnings

warnings.filterwarnings('ignore')


def functionForCalculatingtheResponseTime():
    
    data_json = {"mdb_filepath" : f"{st.session_state.mdb_path}".replace("\+","\\"), "ramp_up":st.session_state.rampup_time, "steady_state":st.session_state.steady_state}
    response = requests.post(f"{st.session_state.host_url}/fetchdata",json = data_json , headers = {'Content-Type': "application/json; charset=utf-8"})
    json_response = response.text
    json_data = json.loads(json_response)
    final_df =json_normalize(json_data)
    
    return (final_df,response.status_code)
    

def functionForHighLevelReport(masterDataFrameForEvent_mapForEntireRun, masterDataFrameForResult, masterDataFrameForEventWeb_Meter,masterDataFrameForVuserEvent_meter, masterDataFrameForError_meter):
    
    period = datetime.utcfromtimestamp(masterDataFrameForResult['Result End Time']) - datetime.utcfromtimestamp(masterDataFrameForResult['Start Time'])
    timePeriod = str(period).split(':')
    timePeriod_String = f"{timePeriod[0]} Hours, {timePeriod[1]} Minutes, {timePeriod[2]} Seconds"

    st.session_state.generalDetailsDataFrameForHLR = pd.DataFrame({
       "Parameters": ["Scenario Name","Result Name","Run Date","Period","Run Duration"],
       "Values": [
            #Scenario Name
       masterDataFrameForResult.loc[0,"Scenario Name"],
            #Result Name
       masterDataFrameForResult.loc[0,"Result Name"],
            #Run Date
       datetime.utcfromtimestamp(masterDataFrameForResult['Start Time']),
            #Period
       f"{datetime.utcfromtimestamp(masterDataFrameForResult['Start Time'])} - {datetime.utcfromtimestamp(masterDataFrameForResult['Result End Time'])}",
            #Run Duration
       timePeriod_String]
    })
    masterDataFrameForEventWeb_Meter["Value*Acount"] = masterDataFrameForEventWeb_Meter["Value"]*masterDataFrameForEventWeb_Meter["Acount"]
    throughputEventId = int(masterDataFrameForEvent_mapForEntireRun[(masterDataFrameForEvent_mapForEntireRun["Event Type"] == "Web") & (masterDataFrameForEvent_mapForEntireRun["Event Name"] == "Throughput")]["Event ID"])
    
    totalTransaction = st.session_state.RT_Sheet[['Passed trx', 'Failed trx']].sum(axis=1)
    
    st.session_state.Workload_Characteristics_df = pd.DataFrame({
        "Parameters": ["Maximum Running Vusers","Average Hits per Second","Total Hits","Total Passed Transactions per Second","Total Passed Transactions per Minute","Total Transactions Number"],
        "Values": [ 
            #Maximum Running Vusers
        masterDataFrameForVuserEvent_meter["InOut Flag"].sum(),
            #Average Hits per Second
        round(masterDataFrameForEventWeb_Meter[~masterDataFrameForEventWeb_Meter['Event ID'].isin([throughputEventId])]["Value*Acount"].sum())/period.total_seconds(),
            #Total Hits
        round(masterDataFrameForEventWeb_Meter[~masterDataFrameForEventWeb_Meter['Event ID'].isin([throughputEventId])]["Value*Acount"].sum()),
            #Total Passed Transactions per Second
        st.session_state.RT_Sheet['Passed trx'].sum()/period.total_seconds(),
            #Total Passed Transactions per Minute
        (st.session_state.RT_Sheet['Passed trx'].sum()*60)/period.total_seconds(),
            #Total Transactions Number
        totalTransaction.sum()]
    })
    
    st.session_state.Performance_Overview_df = pd.DataFrame({
        "Parameters": ["Weighted Average of Transaction Response Time","Total Passed Transactions","Total Failed Transactions","Transactions Success Rate, %","Total Errors per Second","Total Errors"],
        "Values": [ 
            #Weighted Average of Transaction Response Time
        round(st.session_state.RT_Sheet["Average response time"].mean(),3),
            #Total Passed Transactions
        st.session_state.RT_Sheet['Passed trx'].sum(),
            #Total Failed Transactions
        st.session_state.RT_Sheet['Failed trx'].sum(),
            #Transactions Success Rate, %
        round((st.session_state.RT_Sheet['Passed trx'].sum()/totalTransaction.sum())*100,3),
            #Total Errors per Second
        round(len(masterDataFrameForError_meter)/period.total_seconds(),3),
            #Total Errors
        len(masterDataFrameForError_meter)]
    })
    
    st.session_state.Business_Process_df = pd.DataFrame({
        "Parameters": ["Result Name","Transactions per Seconds","Transactions per Minute","Transactions per Hour","Total Throughput","Throughput per Second"],
        "Values": [ 
            #Weighted Average of Transaction Response Time
        st.session_state.generalDetailsDataFrameForHLR.loc[1,'Values'],
            #Transactions per Seconds
        round(totalTransaction.sum()/period.total_seconds(),3),
            #Transactions per Minute
        round((totalTransaction.sum()/period.total_seconds())*60,3),
            #Transactions per Hour
        round((totalTransaction.sum()/period.total_seconds())*3600,3),
            #Total Throughput
        masterDataFrameForEventWeb_Meter[masterDataFrameForEventWeb_Meter['Event ID'].isin([throughputEventId])]["Value*Acount"].sum(),
            #Throughput per Second
        round(masterDataFrameForEventWeb_Meter[masterDataFrameForEventWeb_Meter['Event ID'].isin([throughputEventId])]["Value*Acount"].sum()/period.total_seconds(),3)]
    })
    
    st.session_state.masterDataFrameForEvent_mapForEntireRun = masterDataFrameForEvent_mapForEntireRun
    st.session_state.masterDataFrameForEventWeb_Meter = masterDataFrameForEventWeb_Meter
    st.session_state.timePeriodInSec = period.total_seconds()
    

def functionForMasterDataFrames(mdbFilePath):
    MDB = f'{mdbFilePath}'
    DRV = '{Microsoft Access Driver (*.mdb, *.accdb)}'
    PWD = 'pw'
    con = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(DRV,MDB,PWD))
    cur = con.cursor()
    
    ramp_up_duration = st.session_state.rampup_time
    steadystateEndTime = st.session_state.steady_state

    #### Creating a Master Dataframe for Event_meter that stores All data associated to Test
            # Event_meter: Stores metadata corresponding to event ID that generated during the run 
    #masterDataFrameForEvent_meterForSteadyState = pd.read_sql_query(f'Select * from Event_meter where Event_meter.[End Time] > {ramp_up_duration} and Event_meter.[End Time] < {steadystateEndTime};',con)
            #Event_map: Stores medadata about Events IDs that generated during the run 
    masterDataFrameForEvent_mapForEntireRun = pd.read_sql_query(f'Select * from Event_map;',con)
            # Result: Table holds the record like Scenario Name ResultsName test start time and end time
    masterDataFrameForResult = pd.read_sql_query(f'Select * from Result',con)
            # WebEvent_meter: Table That holds data for Throughput and Hits per Sec.
    masterDataFrameForWebEvent_meter = pd.read_sql_query(f'Select * from WebEvent_meter;',con)
            # VuserEvent_meter: Table That holds data for Vuser Events.
    masterDataFrameForVuserEvent_meter = pd.read_sql_query(f'Select * from VuserEvent_meter;',con)
            #masterDataFrameForError_meter : Table that hold data for Vuser Errors
    masterDataFrameForError_meter = pd.read_sql_query(f'Select * from Error_meter;',con)
    
    return (masterDataFrameForEvent_mapForEntireRun, masterDataFrameForResult, masterDataFrameForWebEvent_meter,masterDataFrameForVuserEvent_meter, masterDataFrameForError_meter)

def functionForVuserEvent_meter(mdbFilePath):
    MDB = f'{mdbFilePath}'
    DRV = '{Microsoft Access Driver (*.mdb, *.accdb)}'
    PWD = 'pw'
    con = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(DRV,MDB,PWD))
    cur = con.cursor()
    
    masterDataFrameForVuserEvent_meter = pd.read_sql_query(f'Select * from VuserEvent_meter;',con)
    
    return (masterDataFrameForVuserEvent_meter)

def checkForTestTimestamp(mdbFilePath):
    
    selectBoxForScenario = st.selectbox("Do You Have SCENARIO SCHEDULE With you ?", ["Select","YES","NO"])
    if selectBoxForScenario == "YES":
        st.session_state.rampup_time = st.number_input("Please Enter the timestamp when Ramp-up Ends in Sec.", min_value=0, step=1)
        st.session_state.steady_state = st.number_input("Please Enter the timestamp when Steady State Ends in Sec.", min_value=0, step=1)
        #st.session_state.rampdown_time = st.number_input("Please Enter Your Ramp down duration in Sec.", min_value=0, step=1)
        st.session_state.codeBase = st.text_input('Please Enter the Code base version upon which test was executed', value="")
        
    elif selectBoxForScenario == "NO":
        masterDataFrameForVuserEvent_meter = functionForVuserEvent_meter(mdbFilePath)
        st.session_state.rampup_time = masterDataFrameForVuserEvent_meter[masterDataFrameForVuserEvent_meter["Vuser Status ID"] == 1]["End Time"].max()
        st.session_state.steady_state = masterDataFrameForVuserEvent_meter[masterDataFrameForVuserEvent_meter["Vuser Status ID"] == 2]["End Time"].max()
        st.session_state.codeBase = st.text_input('Please Enter the Code base version upon which test was executed', value="")
    return selectBoxForScenario



# def fetchRunTimeData(test_typeSelect):
    # fetchRunTimeData_url = f"{st.session_state.host_url}/runTimeData"
    # #string = f'{st.session_state.mdb_path}'
    # #updated_path = string.replace("\+","\\")
    # responseContent = requests.post(f"{fetchRunTimeData_url}?mdbPath={st.session_state.mdb_path}", headers = {'Content-Type': "application/json; charset=utf-8"})
    # st.session_state.runTime_df =json_normalize(responseContent.json())
    
    
#----------------------------------------------------------------------------------------------------------------------------------------------------------------

# TO Write a Testing Objective::



st.set_page_config(layout="wide")
vars = ['file1', 'Exposition', 'Features']
for _ in vars:
    if _ not in st.session_state:
        st.session_state[_] = ''
        st.session_state["save_file_Temp_path"] = ""
        st.session_state["temp_path"] = r"C:\Users\SharmaK21\OneDrive - Vodafone Group\Desktop\Practice\Experiment\Temp"
        st.session_state["mdb_filepath"] = r"C:\Users\SharmaK21\OneDrive - Vodafone Group\Desktop\Practice\Experiment\Temp\MDBFiles"
        st.session_state["mdb_path"] = ""
        st.session_state["test_Type"] = ""
        st.session_state["rampup_time"] = 0
        st.session_state["steady_state"] = 0
        st.session_state["rampdown_time"] = 0
        st.session_state["codeBase"] = ''
        st.session_state["host_url"] = r'http://127.0.0.1:8000'
        st.session_state["RT_Sheet"] = pd.DataFrame()
        st.session_state["session_state_variable"] = 0
        
image_path = r"C:\Users\SharmaK21\OneDrive - Vodafone Group\Desktop\Practice\Experiment\Images"
# Sidebar Widgets
# st.sidebar.markdown('# Streamlit')
# sidebar_pages = st.sidebar.radio('Menu', ['Page 1', 'Page 2', 'Page 3'])
image = Image.open(f'{image_path}\\icon_Logo.jpg')
st.image(image, caption=None, width=None, use_column_width="auto", clamp=False, channels="RGB", output_format="auto")


selected = option_menu(
    menu_title = None,
    options =["Home","Analyze","Exposition","Features"],
    icons =["house","magic","easel","tag-fill"],
    menu_icon = "cast",
    default_index = 0,
    orientation= "horizontal",
)

#### Code to Change Background Color
st.markdown(
    f'''
        <style>
        .stApp{{
            background-color: #33063d;
            background-attachment: fixed;
            height: 100%;
            background-size: cover
        }}
        </style>
    ''',
    unsafe_allow_html = True)
#background-image: url("https://media.istockphoto.com/id/173242643/photo/financial-chart.jpg?s=612x612&w=0&k=20&c=sgXAyV0s4_F0MRLmMVaH8X5odYQVT5l5--6SiWcw8zU=");
def callback_function(state, key):
    # 1. Access the widget's setting via st.session_state[key]
    # 2. Set the session state you intended to set in the widget
    st.session_state[state] = st.session_state[key]

# def button_callback():
    # st.session_state.button_clicked = True
    

# Page 1
def Home():
    st.write("# Welcome To Vois PAT(VPAT) Analyser Tool")

    st.sidebar.success("Select a Exposition Tile To View demo.")

    st.markdown(
        """
        VPAT helps you to analyze your test result with just a snap.
        **☝️ Select Exposition Tile Placed at the TOP** to see some examples
        of what this tool can do!
        ### Want to Analyze test results in one go?
        - Provide the compressed .lra file for current test
        - Provide the Baselines to compare
        - And Let the Tool do rest.
        ### Why go for complexity, When VPAT is here for you
        - Can give you the precise results within a minute
        - Graphical and tabulate analyze makes the results easy to understand
        - Complete automation, eliminates the manual faults    
    """
    )

# Page 2
def Analyse():
    st.header("Upload _LoadRunner_ _Analysis_ File")
#-----------------------------------------Browseing file for Current Test in .zip extension------------------------------------------------------------------------
    file1 = st.file_uploader("Tip: Choose compress file (*.zip) for better experience", label_visibility="visible",type = [".zip"], key = "currentTest_key", on_change = callback_function, args =("file1","currentTest_key"))
    check_1 = st.checkbox("Click Checkbox to successfully Upload the browsed file")
    if check_1:
        if file1 is None:
            st.error("Please Upload the the before proceeding", icon = "⚠️")
        else:
#---------------------------------------------Extarcting a mdb file from a zipped analysed file--------------------------------------------------------------
#---------------------------------Pulling the path of the extracted mdb file which can be used to find values------------------------------------------------
            
            
                    # Checking if File Already Exists or Not
            try:
                st.session_state.save_file_Temp_path = Path(st.session_state.temp_path , file1.name)
                with open(st.session_state.save_file_Temp_path, mode='wb') as w:
                    w.write(file1.getvalue())
                    if st.session_state.save_file_Temp_path.exists():
                        st.info("File Uploaded Successfully", icon = "✅")
                with ZipFile(st.session_state.save_file_Temp_path, 'r') as zObject:
                    files = zObject.namelist()
                    for file in files:
                        filename, extension = os.path.splitext(file)

                        if extension == '.mdb':
                            zObject.extract(file, path = f'{st.session_state.mdb_filepath}')
                            st.session_state.mdb_path = Path(st.session_state.mdb_filepath, f'{filename}.mdb')

                zObject.close()
            except PermissionError:
                pass
            # st.session_state.mdb_path = Path(st.session_state.mdb_filepath, f'{test_name[0]}.mdb')

        test_typeSelect = st.selectbox("Please choose you Test type from the Following", ["Select","Load Test", "Smoke Test", "Soak or Endurance Test","Page Performance Test"])
        st.session_state.test_Type = test_typeSelect
        
        check_2 = st.checkbox("Check To Proceed with Test Durations")
        
        if check_2:
                # Function For Getting Values Like Ramp-up, Steady State and Code Base.
            selectBoxForScenario = checkForTestTimestamp(st.session_state.mdb_path)
            
            if (selectBoxForScenario == "YES" or selectBoxForScenario == "NO"):
                # Function For Connecting the Database and storing all data into Master DataFrames.
                
                masterDataFrameForEvent_mapForEntireRun, masterDataFrameForResult, masterDataFrameForEventWeb_Meter,masterDataFrameForVuserEvent_meter, masterDataFrameForError_meter = functionForMasterDataFrames(st.session_state.mdb_path)
            
                    # API For Indetifying Response
                if st.session_state.RT_Sheet.empty:
                    progressInfo = st.info("Your Data is been Progress, Please wait...", icon = "⏳")
                    st.session_state.RT_Sheet, statusCode = functionForCalculatingtheResponseTime()
                    if statusCode == 200:
                        progressInfo.empty()
                else:
                    pass
                    
                    # Function For Generating High Level Report from Master DataFrames.
                functionForHighLevelReport(masterDataFrameForEvent_mapForEntireRun, masterDataFrameForResult, masterDataFrameForEventWeb_Meter,masterDataFrameForVuserEvent_meter, masterDataFrameForError_meter)
            
            #fetchRunTimeData(test_typeSelect)  #   This will fetch Run Duration time from MDB file and ask for ramp_up and steady_state duration
                                    
            button1 = st.button("Navigate To Response Time Analysis")
            
            if button1:
                if st.session_state.rampup_time ==0 and st.session_state.steady_state == 0:
                    st.error("You have Not Entered Rampup Value and Steady State Value, Please Enter these Details before Navigating to Response Time Page", icon = "🚫")
                else:
        #####------------------------------------------creating a dataframe that holds data of current test: Begins------------------------------------------------#######
                    switch_page("Response_Time_Analysis_v1")
        #####-----------------------------------------------Current test extracted to DataFrame: completed-------------------------------------------------------#########
            

def features():
    st.markdown(
    '''
    ## <div style="text-align: center"> Features </div>
    ## <div style="text-align: center"> How Much Manual Efforts of Yours VPAT Can Save </div>
    <body>
    <div style="text-align: center">
        Due to time constaints,team finds it difficult to make proper analysis for the executed test. This could create a possibility of missing out the major pointers. VPAT not only reduces the manual task but also eases the way of reporting
        </div>
    ''',
    unsafe_allow_html = True
    )
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Analyze Response Time", "Analyze Errors", "Analyze Logs","Analyze Heap Dump","Populate Final Test Report"])
    with tab1:
        st.header("Analyze Response Time")
        col1, col2 = st.columns([1,3])
        image = Image.open(f'{image_path}\\RT_image.jpg')
        with col1:
            st.image(image, caption=None, width=None, use_column_width="auto", clamp=False, channels="RGB", output_format="auto")
        with col2:
            st.markdown(
            '''
            VPAT Helps you to calculate Response time of you test on basis of user input.
            - Apart from .lra file, user needs to provide Non-Functional requirements like (Standard SLAs, Expected Volume and Baseline SLAs).
            - Once the pre-requisite data be provided, VPAT analyze it and tabulates the **Response Time** data with final status for all business transaction as Red, Amber and Green
            - In case of absence of NFRs like Standard SLAs and Baseline SLAs, final status for business transaction is estimated againts standard values. i.e., 5 Sec. for GUI flow and 3 Sec. for API flow
            '''
            )
    with tab2:
        st.header("Analyze Errors")
        col1, col2 = st.columns([1,3])
        image = Image.open(f'{image_path}\\error_2.jpg')
        with col1:
            st.image(image, caption=None, width=None, use_column_width="auto", clamp=False, channels="RGB", output_format="auto")
        with col2:
            st.markdown(
            '''
            '''
            )
    with tab3:
        st.header("Analyze Logs")
        #col1, col2 = st.columns([1,3])
        image = Image.open(f'{image_path}\\coming_soon.jpg')
        #with col1:
        st.image(image, caption=None, width=None, use_column_width="auto", clamp=False, channels="RGB", output_format="auto")
        # with col2:
            # st.markdown(
            # '''
            # '''
            # )
    with tab4:
        st.header("Analyze Heap Dump")
        #col1, col2 = st.columns([1,3])
        image = Image.open(f'{image_path}\\coming_soon.jpg')
        #with col1:
        st.image(image, caption=None, width=None, use_column_width="auto", clamp=False, channels="RGB", output_format="auto")
        # with col2:
            # st.markdown(
            # '''
            # '''
            # )
    with tab5:
        st.header("Populate Final Test Report")
        #col1, col2 = st.columns([1,3])
        image = Image.open(f'{image_path}\\coming_soon.jpg')
        #with col1:
        st.image(image, caption=None, width=None, use_column_width="auto", clamp=False, channels="RGB", output_format="auto")
        # with col2:
            # st.markdown(
            # '''
            # '''
            # )
# Page 3
def Exposition():
    switch_page("Exposition")
    

# Navigate through pages
if selected == 'Home':
    Home()
elif selected == 'Analyze':
    Analyse()
elif selected == 'Features':
    features()
else:
    Exposition()



