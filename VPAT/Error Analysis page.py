import streamlit as st
import requests
import json
from pandas import json_normalize
import pandas as pd 
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import seaborn as sns
import matplotlib as mpl
from tempfile import NamedTemporaryFile
import tempfile,re

if "constraints_variable" not in st.session_state:
    st.session_state["host_url"] = r'http://127.0.0.1:8000'
    st.session_state["return_value_df"] = pd.DataFrame()

##############################____________________________________  Function That Rename Column Name of Error Table: Begins ___________________#######################################
def enhancingErrorTypedf(df):
    df.rename(columns = {'Event Name':'Error Code'}, inplace = True)
    df.rename(columns = {'Expr1001':'Count'}, inplace = True)
    return df
##############################____________________________________  Function That Rename Column Name of Error Table: Ends _____________________#######################################

##############################____________________________________  Function That Enhancing of Error Table: Begins ____________________________#######################################
def enhancingCountErrorDf(df1):
    try:
        df1.rename(columns = {'Event Name':'Transaction Name'}, inplace = True)
        df1.rename(columns = {'Expr1001':'Count'}, inplace = True)
        df1['name'] = df1['Error Message'].str.split('-2').str[0]
        df1['e_code'] = df1['Error Message'].str.split(' ').str[2]
        df1['Error Count'] = df1['name']+df1['e_code']
        df1.style.set_properties(**{'background-color': 'black','color': 'yellow'})
        #df1['Error Count']
        df2 = df1.pivot_table(index=['Error Count'], aggfunc='size')
        #df3 = df2["Error Count"]
        #df3 = df1.drop(["name","e_code"])
        cols_name = ["Transaction Name","Count","Error Message", "Error Count"]
        last_df = df1.drop(df1.columns.difference(cols_name), axis=1)
        st.dataframe(last_df.style.set_properties(**{'background-color': 'black','color': 'yellow'}), hide_index = True,)
        st.session_state.errorType = last_df
        return df2
    except:
        pass
    
##############################____________________________________  Function That Enhancing of Error Table: Ends ____________________________#######################################

########################____________________________________  Function That creating DF to hold Final Transaction status: Begins __________________##################################
def call_statusCount():
    red_count = 0
    green_count = 0
    amber_count = 0
    st.dataframe(st.session_state.RT_Sheet)
    df = st.session_state.RT_Sheet.data
    for i in df["color"]:
        if i == "Green":
            green_count +=1
        elif i == "Red":
            red_count +=1
        elif i == "Amber":
            amber_count +=1
    total_count = red_count + green_count + amber_count
    statusCount_df = pd.DataFrame(data = [[total_count,green_count,amber_count,red_count]] , columns = ["Total Transaction","Total Green Transaction","Total Amber Transaction","Total Red Transaction"])
    return statusCount_df

######################_______________________________________  Function That Plot BAR chart for RT for Error Summary: Begins _________________________###############################
def plotingBARGraphForErrorSummary(enhanced_errorType_df):
    fig2 , ax1 = plt.subplots(figsize=(60,20),dpi = 40)
    barwidth = 0.3
    barspace = 0
    bar_position = np.arange(len(enhanced_errorType_df['Error Code']))
    plt.bar(bar_position, enhanced_errorType_df['Count'], width = barwidth, edgecolor = 'grey', color = 'red')
    #ax1 = sns.barplot(data =enhanced_errorType_df, x = enhanced_errorType_df["Error Code"]  , y = "Count")
    plt.xticks([barspace+r for r in range(len(enhanced_errorType_df['Error Code']))], enhanced_errorType_df['Error Code'],rotation=0,fontsize = 42)
    plt.yticks(fontsize = 32)
    plt.xlabel('Error Code', fontweight ='bold', fontsize = 32, color = "white")
    plt.ylabel('Count', fontweight ='bold', fontsize = 32, color = "white")
    plt.rcParams['axes.facecolor']='black'
    plt.rcParams['savefig.facecolor']='black'
    plt.tick_params(axis='x', colors='white')
    plt.tick_params(axis='y', colors='white')
    
    st.pyplot(fig2)
    return fig2

def calculatePCTforStatus(return_value):
   total_count = return_value.loc[0,"Total Transaction"] 
   green_count = return_value.loc[0,"Total Green Transaction"]
   amber_count = return_value.loc[0,"Total Amber Transaction"]
   red_count = return_value.loc[0,"Total Red Transaction"]
   green_pct = (green_count/total_count)*100
   return_value.loc[0,"Green %"] = "%.2f"%green_pct
   amber_pct = (amber_count/total_count)*100
   return_value.loc[0,"Amber %"] = "%.2f"%amber_pct
   red_pct = (red_count/total_count)*100
   return_value.loc[0,"Red %"] = "%.2f"%red_pct
   ####Dummy Data Need to update
   return_value.loc[0,"Error %"] = 100 - round(st.session_state.Performance_Overview_df.loc[4,'Values'],3)
   
   return return_value
   
def functionForHTTStatus():
    httpStatusTotalValue = []
    st.session_state.masterDataFrameForEventWeb_Meter["Value*Acount"] = st.session_state.masterDataFrameForEventWeb_Meter["Value"]*st.session_state.masterDataFrameForEventWeb_Meter["Acount"]
    masterDataFrameForEventWeb_Meter = st.session_state.masterDataFrameForEventWeb_Meter
    masterDataFrameForEvent_mapForEntireRun = st.session_state.masterDataFrameForEvent_mapForEntireRun
    httpEventName = masterDataFrameForEvent_mapForEntireRun[(masterDataFrameForEvent_mapForEntireRun["Event Type"] == "Web") & (masterDataFrameForEvent_mapForEntireRun["Event Name"] != "Throughput") & (masterDataFrameForEvent_mapForEntireRun["Event Name"] != "Hits")]["Event ID"]
    
    for i in httpEventName.values.tolist():
        httpStatusTotalValue.append(masterDataFrameForEventWeb_Meter[masterDataFrameForEventWeb_Meter['Event ID'].isin([i])]['Value*Acount'].sum())
    
    httpStatusCode_df = pd.DataFrame({
    "HTTP Code Status": [value for value in masterDataFrameForEvent_mapForEntireRun[masterDataFrameForEvent_mapForEntireRun['Event ID'].isin(httpEventName)]['Event Name']],
    "Total Value": httpStatusTotalValue,
    "Values Per Sec": [i/st.session_state.timePeriodInSec for i in httpStatusTotalValue]
    })
    return httpStatusCode_df

#Setting Background color of the Page
#            background-image: url("https://images.unsplash.com/photo-1501426026826-31c667bdf23d");
#background-color: #8861d0;
st.markdown(
    f'''
        <style>
        .stApp{{
            background: linear-gradient(110deg,#553189 30%, #bd67d8 70%);
            background-attachment: fixed;
            height: 100%;
            background-size: cover
        }}
        </style>
    ''',
    unsafe_allow_html = True)

#user_color = st.color_picker(label = " ", value = "#736eaf")

#Fetching Error Rate Details from the API
response = requests.post(f"{st.session_state.host_url}/ErrorAnalysis?path3={st.session_state.mdb_path}", headers = {'Content-Type': "application/json; charset=utf-8"})
json_response = response.text
data = json.loads(json_response)

#Creating DataFrame for Error Summary
errorType_df = json_normalize(data[0])
enhanced_errorType_df = enhancingErrorTypedf(errorType_df)
st.write("#   Error Summary")
#Enhancing the DataFrame
httpStatusCode_df = functionForHTTStatus()

if enhanced_errorType_df.empty:
    pass
    # st.markdown('''
        # <div class="container">
        # <p class="typed">Executed Test has No Events having <strong> 3xx, 4xx or even 5xx</strong> https status codes</p>
        # </div>
    # ''',unsafe_allow_html = True)
else:
    
    st.session_state.errorsummary = enhanced_errorType_df
    st.dataframe(enhanced_errorType_df.style.set_properties(**{'background-color': 'black','color': 'yellow'}), hide_index = True,)
    #st.dataframe(enhanced_errorType_df)

    error_Bargraph_fig = plotingBARGraphForErrorSummary(enhanced_errorType_df)
    fp = tempfile.NamedTemporaryFile()
    with open(f"{fp.name}.png",'wb') as ff:
        error_Bargraph_fig.savefig(ff)
        st.session_state.error_bargraph_path = ff.name
        ff.close()
    fp.close()

#st.bar_chart(data=enhanced_errorType_df, x="Error Code", y="Count", width=10, height=0, use_container_width=True)


#Creating DataFrame for Detailed Error Description
countError_df = json_normalize(data[1])
#st.dataframe(countError_df)
st.write("Detailed Error Description")
enhanced_countError_df = enhancingCountErrorDf(countError_df)
#st.dataframe(enhanced_countError_df.style.set_properties(**{'background-color': 'black','color': 'yellow'}))
if enhanced_countError_df is None:
    pass
else:
    st.dataframe(enhanced_countError_df)
#st.session_state.errorCountdf = enhanced_countError_df

####################    Fetching Json From API with Transaction Status ################################################ 
# json_data = json.loads(st.session_state.JsonResponse_df.text)
# final_df =json_normalize(json_data)
return_value = call_statusCount()

# st.write("Tabulate Representation for Test Status")
return_value_df = calculatePCTforStatus(return_value)
st.dataframe(return_value_df.style.set_properties(**{'background-color': 'black','color': 'yellow'}), hide_index = True,)

st.write("HTTP Code with Count")
st.dataframe(httpStatusCode_df.style.set_properties(**{'background-color': 'black','color': 'yellow'}), hide_index = True,)
st.session_state.statusCode_df = httpStatusCode_df
    
