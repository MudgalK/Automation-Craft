import streamlit as st
import requests 
from pathlib import Path
from zipfile import ZipFile
import pandas as pd
from pandas import json_normalize
import json
from functools import reduce
from operator import add
import re
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import seaborn as sns
import matplotlib as mpl
from PIL import Image
import base64
import numpy as np
from tempfile import NamedTemporaryFile
import tempfile
#import xlsxwriter
from fpdf import FPDF
from datetime import date
import dataframe_image as dfi
from IPython.display import display
import sys
from termcolor import colored, cprint
from colored import fg
from datetime import datetime
import matplotlib.style as mplstyle
from html2image import Html2Image



class PDF(FPDF):
    def __init__(self):
        super().__init__()
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'Test Report', 0, 1, 'C')
        today = date.today()
        self.cell(0, 8, f'{today}', 0, 1, 'R')
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', '', 12)
        self.cell(0, 8, f'Page {self.page_no()}', 0, 0, 'C')

# from openpyxl import Workbook
# from openpyxl.drawing.image import Image
# import plotly.io as pio

if "constraints_variable" not in st.session_state:
    st.session_state["host_url"] = r'http://127.0.0.1:8000'
    st.session_state["return_value_df"] = pd.DataFrame()
    #st.session_state['df_xlsx'] = io.BytesIO()

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
   return_value.loc[0,"Error %"] = "%.2f"%(100 - float(st.session_state.Performance_Overview_df.loc[5,f"{st.session_state.Performance_Overview_df.columns.tolist()[1]}"]))
   
   return return_value

########################____________________________________  Function That creating DF to hold Final Transaction status: Begins __________________##################################
def call_statusCount():
    red_count = 0
    green_count = 0
    amber_count = 0
    df4 = st.session_state.RT_Sheet.data
    for i in df4["color"]:
        if i == "Green":
            green_count +=1
        elif i == "Red":
            red_count +=1
        elif i == "Amber":
            amber_count +=1
    total_count = red_count + green_count + amber_count
    statusCount_df = pd.DataFrame(data = [[total_count,green_count,amber_count,red_count]] , columns = ["Total Transaction","Total Green Transaction","Total Amber Transaction","Total Red Transaction"])
    return statusCount_df
########################____________________________________  Function That creating DF to hold Final Transaction status: Ends __________________####################################

###########################_______________________________________  Function That Plot PIE chart for Final Status: Begins _________________________##################################

# Creating autocpt arguments
def func(pct, allvalues):
	absolute = int(pct / 100.*np.sum(allvalues))
	return "{:.1f}%".format(pct)
    
def plotingPIEChartForFinalStatus(final_status_df):

    column_list = final_status_df.loc[0,:].values.tolist()
    data = column_list[1:4]
    status = ['Green Status','Amber Status','Red Status']
    # Creating color parameters
    colors = ( "green","orange","red")
    
    # Creating plot
    # fig, ax = plt.subplots(figsize=(6,5),dpi = 80,facecolor=(0.364705,0.207843,0.572549,0.8))
    totalSum = sum(data)
    titleDict = {
     'color': 'white'

    }
    fig, (ax1,ax2) = plt.subplots(2,1,facecolor=(0.031, 0.031, 0.031),figsize=(8,10))
    plt.subplots_adjust(left=0.1, bottom=0.1, right =0.9, 
                        top=0.9, wspace=0.4,hspace=0.4)
    ax1.bar(status,data,color ='#2a94ed',width = 0.2)
    ax1.set_title("Transaction Value Per Status In Numbers",fontdict = titleDict)
    ax1.set_xlabel('Transaction Status', fontweight ='bold', fontsize = 12, color = "white")
    ax1.set_ylabel('Number of Transaction', fontweight ='bold', fontsize = 12, color = "white")
    ax1.tick_params(axis='both', colors='white')
    
    ax2.set_title("Transaction Value Per Status In Percentages",fontdict = titleDict    )
    ax2.pie(data, wedgeprops=dict(width=0.3), radius = 1,autopct=lambda pct: func(pct,data),
            shadow=True, startangle=90,pctdistance = 1.2,textprops=dict(color="w",size = 15.0),colors = colors)
    sumstr = "Total Transactions = \n" + str(totalSum)
    ax2.text(0.0, 0.0, sumstr, horizontalalignment='center', verticalalignment='center',backgroundcolor = 'black', color = 'white',size = 11.0)
    ax2.legend(labels = status, loc='center right', bbox_to_anchor=(1.5, 0.5), fontsize = 12, labelcolor = "white", facecolor = "black")


    # ax.pie(data,
            # autopct = lambda pct: func(pct, data),
            # colors = colors,
            # radius = 1,
            # startangle = 90,
            # textprops={"fontsize":12})
    # ax.legend(labels = status, loc='right', bbox_to_anchor=(1.1, 1.0), fontsize = 12, labelcolor = "white")
    # plt.rc('font', size=32)
    buf = BytesIO()
    fig.savefig(buf, format="png")
    st.image(buf)
    buf.seek(0)
    return fig
###########################_______________________________________  Function That Plot PIE chart for Final Status: Ends ___________________________##################################

########################_______________________________________  Function That Plot BAR chart for RT for current Test: Begins _________________________###############################
def responseTimeGraph_CurrentTest(final_df):
    column_list = final_df.columns.values.tolist()
    barGraphFig1 , ax = plt.subplots(figsize=(60,30),dpi = 100)
    mplstyle.use('fast')
    barspace = 0.12
    require_columnList = [column_list[1],column_list[6],column_list[10],column_list[11]]
    x_axisPlot = final_df['TransactionName']
    br1 = np.arange(len(x_axisPlot))
    br_position = br1
    for i in range(len(require_columnList)):
        br_new = br_position
        plt.bar(br_new,final_df[f'{require_columnList[i]}'], width = barspace, edgecolor = 'grey')
        br_position = [x + barspace for x in br_new ]
    plt.xticks([barspace+r for r in range(len(final_df["TransactionName"]))], final_df["TransactionName"],rotation=270,fontsize = 32)
    plt.yticks(fontsize = 32)
    #plt.xticks(rotation=90)
    plt.xlabel('Transaction Name', fontweight ='bold', fontsize = 40, color = "white")
    plt.ylabel('Response Time (in Sec)', fontweight ='bold', fontsize = 40, color = "white")
    labels_title = require_columnList
    plt.legend(labels = labels_title, loc='right', bbox_to_anchor=(0.8, 0.9), fontsize = 44, labelcolor = "white")
    plt.rcParams['axes.facecolor']='black'
    plt.rcParams['savefig.facecolor']='black'
    plt.tick_params(axis='x', colors='white')
    plt.tick_params(axis='y', colors='white')
    #st.pyplot(barGraphFig1)
    barGraphBuf = BytesIO()
    barGraphFig1.savefig(barGraphBuf, format="jpg",bbox_inches='tight')

    st.image(barGraphBuf)

    barGraphBuf.seek(0)
    return barGraphFig1
########################_______________________________________  Function That Plot BAR chart for RT for current Test: Ends _________________________###############################

########################_______________________________________  Function That Plot BAR chart for RT for current Test: Begins _________________________###############################
def responseTimeComparisionGraph(df5):
    barGraphFigPreviousTest, ax5 = plt.subplots(figsize =(60, 30),dpi = 100)
    mplstyle.use('fast')
    barspace = 0.12
    #barwidth = 0.15
    
    column_list = df5.columns.tolist()
    require_columnList = column_list[1:]
    br1 = np.arange(len(df5[f'{require_columnList[0]}']))
    br_position = br1
    for i in range(len(require_columnList)):
        br_new = br_position
        plt.bar(br_new,df5[f'{require_columnList[i]}'], width = barspace, edgecolor = 'grey')
        br_position = [x + barspace for x in br_new ]
    plt.xticks([barspace+r for r in range(len(df5["TransactionName"]))], df5["TransactionName"],rotation=270,fontsize = 32)
    plt.yticks(fontsize = 32)
    #plt.xticks(rotation=90)
    plt.xlabel('Transaction Name', fontweight ='bold', fontsize = 40, color = "white")
    plt.ylabel('Response Time (in Sec)', fontweight ='bold', fontsize = 40, color = "white")
    labels_title = require_columnList
    plt.legend(labels = labels_title, loc='right', bbox_to_anchor=(0.8, 0.9), fontsize = 44, labelcolor = "white")
    plt.rcParams['axes.facecolor']='black'
    plt.rcParams['savefig.facecolor']='black'
    plt.tick_params(axis='x', colors='white')
    plt.tick_params(axis='y', colors='white')
    #st.pyplot(barGraphFigPreviousTest)
    
    barGraphBuf = BytesIO()
    barGraphFigPreviousTest.savefig(barGraphBuf, format="png",bbox_inches='tight')

    st.image(barGraphBuf)
    
    return barGraphFigPreviousTest
########################_______________________________________  Function That Plot BAR chart for RT for current Test: Ends __________________________###############################

def create_download_link(val, filename):
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download file</a>'

def highlighter(series):
    return ["background-color: green;" if e == "Green" else "background-color: red;" if e == "Red" else "background-color: orange;" if e == "Amber" else "background-color: white;" for e in series]

def colorhighlighter(val):
    if val > 5:
        color = 'Red'
    else:
        color = 'black'
    return 'color: %s' % color

st.set_page_config(layout="wide")

st.header('    Conclusion')

st.markdown(
    f'''
        <style>
        .stApp{{
            background-color: black;
            background-attachment: fixed;
            height: 100%;
            background-size: cover
        }}
        </style>
    ''',
    unsafe_allow_html = True)


def writing_PDF_file(observationDf,image_df,*callable_value):
    
    test_summarydf = callable_value[0]
    test_observationdf = image_df[0]
    performanceTestReportSummary = image_df[1]
    imageForTransactionSatus = image_df[0]
    imageForTransactionTrend = image_df[2]
    #response_timedf = image_df[1]
    response_timedf = st.session_state.RT_Sheet.hide_index()
    pdf = PDF()
    ch = 12
    m = 10
    pw = 210 - 2*m
    pdf.add_page(orientation = 'L')
    # pdf.set_font('Arial', 'B', 24)
    # pdf.cell(w=0, h=20, txt="Performance Test Report", ln=1)
    pdf.ln(ch)
        ## Adding Table Header for Summary Table
    pdf.image(performanceTestReportSummary,1.5*m,2*ch,1.4*pw,pw)
        ### Adding Image for Transaction Status
    pdf.add_page(orientation = 'L')
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(w= m, h= ch, txt = "Graphical Views For The Executed Test",ln=1,align='L')
    pdf.cell(w= m, h= ch, txt = "A) Transaction Status",ln=1,align='L')
    
    tempDirForGraphicalViewOfTransactionStatus = tempfile.NamedTemporaryFile()
    with open(f"{tempDirForGraphicalViewOfTransactionStatus.name}.png",'wb') as tempImage_TransactionStatus:
        tempImage_TransactionStatus.write(imageForTransactionSatus.getvalue())
        pdf.image(tempImage_TransactionStatus.name,4*m,4.2*ch,1.05*pw,0.72*pw)
    tempDirForGraphicalViewOfTransactionStatus.close()
    
        ## Adding Image for Transaction Trends
    pdf.add_page(orientation = 'L')
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(w= m, h= ch, txt = "B) Transaction Response Time Trend",ln=1,align='L')
    tempDirForGraphicalViewOfTransactionTrends = tempfile.NamedTemporaryFile()
    with open(f"{tempDirForGraphicalViewOfTransactionTrends.name}.jpg",'wb') as tempImage_TransactionTrends:
        tempImage_TransactionTrends.write(imageForTransactionTrend.getvalue())
        pdf.image(tempImage_TransactionTrends.name,m,3.05*ch,1.45*pw,0.8*pw)
    tempDirForGraphicalViewOfTransactionTrends.close()
    
    if st.session_state.Test_type == 'Previous':
        compare_df = callable_value[2]
        pdf.add_page(orientation = 'L')
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(w= m, h= ch, txt = "C) Response Time Comparison",ln=1,align='L')
        pdf.image(compare_df.name, m, 3.05*ch, 1.45*pw,0.8*pw)
        
        ## Adding High Level Reports
    pdf.add_page(orientation = 'L')
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(w=m, h=ch, txt="High Level Test Report", ln=1,align='L')
    pdf.cell(w=m, h=ch, txt='A) Workload Characteristics', ln=1,align='L')
    pdf.ln(ch)
            ## Adding Table Header for Summary Table
    pdf.set_font('Arial', 'B', 16)
    pdf.set_xy(x = 4*m, y = 4.2*ch)
    pdf.cell(w=110, h=ch, txt='Parameters', border=1, ln=0, align='C')
    pdf.cell(w=80, h=ch, txt='Measured Values', border=1, ln=1, align='C')
                # Table contents
    pdf.set_font('Arial', '', 12)
    col_lst_workload = st.session_state.Workload_Characteristics_df.columns.tolist()
     
    for i in range(0, len(st.session_state.Workload_Characteristics_df)):
        pdf.set_x(x = 4*m)
        pdf.cell(w=110, h=ch, 
                 txt=st.session_state.Workload_Characteristics_df['Parameters'].iloc[i], 
                 border=1, ln=0, align='L')
        pdf.cell(w=80, h=ch, 
                 txt=st.session_state.Workload_Characteristics_df['Values'].iloc[i].astype(str), 
                 border=1, ln=1, align='C')
    pdf.ln(4*ch)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_x(x = 4*m)
    pdf.cell(w=m, h=ch, txt='B) Performance Overview', ln=1, align='C')
    pdf.ln(ch)
    ## Adding Table Header for Summary Table
    pdf.set_x(x = 4*m)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(w=110, h=ch, txt='Parameters', border=1, ln=0, align='C')
    pdf.cell(w=80, h=ch, txt='Measured Values', border=1, ln=1, align='C')
    # Table contents
    pdf.set_font('Arial', '', 12)
    col_lst_performanceOverview = st.session_state.Performance_Overview_df.columns.tolist()
    for i in range(0, len(st.session_state.Performance_Overview_df)):
        pdf.set_x(x = 4*m)
        pdf.cell(w=110, h=ch, 
                 txt=st.session_state.Performance_Overview_df['Parameters'].iloc[i], 
                 border=1, ln=0, align='L')
        pdf.cell(w=80, h=ch, 
                 txt=st.session_state.Performance_Overview_df['Values'].iloc[i].astype(str), 
                 border=1, ln=1, align='C')
    # ##########Adding Response Time Page#########################
    pdf.add_page(orientation = 'L')
    pdf.set_font('Arial', 'B', 16)
    # pdf.set_fill_color(r= 255, g= 0, b = 0)
    # pdf.set_text_color(r= 255, g= 255, b = 255)
    #pdf.cell(w=m, h=ch, txt="Response Timesheet", ln=1,fill=True,align='L')
    pdf.cell(w=m, h=ch, txt="Response Timesheet", ln=1,align='L')
    temp_dir_RTSheet = tempfile.NamedTemporaryFile()
    #with open(f"{temp_dir_RTSheet.name}.jpg",'wb') as tempImage_RTSheet:
    with open(f"{temp_dir_RTSheet.name}.png",'wb') as tempImage_RTSheet:
        dfi.export(response_timedf, tempImage_RTSheet)
        pdf.image(tempImage_RTSheet.name, m, 3.05*ch, 1.45*pw,0.8*pw)
        tempImage_RTSheet.close()
    temp_dir_RTSheet.close()

        #### Adding Error Page#########################
    pdf.add_page(orientation = 'L')
    pdf.set_font('Arial', 'B', 16)
    # pdf.set_fill_color(r= 255, g= 0, b = 0)
    # pdf.set_text_color(r= 255, g= 255, b = 255)
    # pdf.cell(w=m, h=ch, txt="Error Report", ln=1,fill=True,align='L')
    pdf.cell(w=m, h=ch, txt="Error Report", ln=1,align='L')
    pdf.set_font('Arial', 'B', 16)
    #st.session_state.statusCode_df
    pdf.cell(w=0, h=ch, txt='A) HTTP Code with Count', ln=1, align='L')
    statusCodeDf = st.session_state.statusCode_df.style.hide(axis='index')
    pdf.set_text_color(r= 0, g= 0, b = 0)
    pdf.set_font('Arial', 'B', 16)
    pdf.set_x(x = 4*m)
    pdf.cell(w=80, h=ch, txt='HTTP Code Status', border=1, ln=0, align='C')
    pdf.cell(w=40, h=ch, txt='Total Value', border=1, ln=0, align='C')
    pdf.cell(w=40, h=ch, txt='Values Per Sec', border=1, ln=1, align='C')
        # Table contents
    for i in range(0, len(st.session_state.statusCode_df)):
        pdf.set_x(x = 4*m)
        pdf.set_font('Arial', '', 9)
        pdf.cell(w=80, h=ch, 
            txt=str(st.session_state.statusCode_df['HTTP Code Status'].iloc[i]), 
            border=1, ln=0, align='L')
        pdf.cell(w=40, h=ch, 
            txt=str(st.session_state.statusCode_df['Total Value'].iloc[i]), 
            border=1, ln=0, align='C')
        pdf.cell(w=40, h=ch, 
            txt=str(st.session_state.statusCode_df['Values Per Sec'].iloc[i]), 
            border=1, ln=1, align='C')
    try:
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(w=m, h=ch, txt='B) Error Summary Table', ln=1, align='L')
        pdf.set_text_color(r= 0, g= 0, b = 0)
        pdf.set_font('Arial', 'B', 16)
        pdf.set_x(x = 4*m)
        pdf.cell(w=80, h=ch, txt='Script Name', border=1, ln=0, align='C')
        pdf.cell(w=40, h=ch, txt='Count', border=1, ln=0, align='C')
        pdf.cell(w=40, h=ch, txt='Error Code', border=1, ln=1, align='C')
        # Table contents
        for i in range(0, len(st.session_state.errorsummary)):
            pdf.set_x(x = 4*m)
            pdf.set_font('Arial', '', 9)
            pdf.cell(w=80, h=ch, 
                     txt=str(st.session_state.errorsummary['Script Name'].iloc[i]), 
                     border=1, ln=0, align='L')
            pdf.cell(w=40, h=ch, 
                     txt=str(st.session_state.errorsummary['Count'].iloc[i]), 
                     border=1, ln=0, align='C')
            pdf.cell(w=40, h=ch, 
                     txt=str(st.session_state.errorsummary['Error Code'].iloc[i]), 
                     border=1, ln=1, align='C')
        pdf.add_page(orientation = 'L')
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(w=m, h=ch, txt='C) Graphical view for Error Summary', ln=1, align='L')
        # with NamedTemporaryFile(delete=False, suffix=".png") as tmpfile1:
            # st.session_state.error_bargraph_path.savefig(tmpfile1.name)
            # pdf.image(tmpfile1.name, 5, 150, 200, 100)
            # tmpfile.close()
        pdf.image(st.session_state.error_bargraph_path, m, 3.05*ch, 1.45*pw,0.8*pw)
    except:
        pass
    
    return pdf
 


def Summary(conclusion_df1,tran_df) :
    if st.session_state.test_Type == "Load Test":
        conclusion_df1['Objective'] = 'Execute Load tests on application with 100% load to check the system performance against Peak Load'
    elif st.session_state.test_Type == "Smoke Test":
        conclusion_df1['Objective'] = 'Execute Smoke tests to Verify and validate application performance against minimum load'
    elif st.session_state.test_Type == "Soak or Endurance Test":
        conclusion_df1['Objective'] = 'Execute Soak or Endurance test on the application to determine the Memory related issue of the application and system performance under 100% Load'
    elif st.session_state.test_Type == "Page Performance Test":
        conclusion_df1['Objective'] = 'Execute Page Performance Test on application to evaluate the Client side Response time '

    summary_df = pd.DataFrame()
    
    summary_df.loc['Objective:','value'] = conclusion_df1._get_value(0,'Objective')
    summary_df.loc['Test Status:','value'] = conclusion_df1._get_value(0,'Result')
    indentitingPoints = ""
    green_val=conclusion_df1['Green %'][0]
    if (conclusion_df1['Total Red Transaction'][0]>0 and conclusion_df1['Total Amber Transaction'][0] == 0):
        pointer2_forHighRT = "2.  Below are the RED listed Transactions with high response time:"
        
        for i in range(conclusion_df1['Total Transaction'][0]) :
            if (tran_df['color'][i] == 'Red'):
                transaction_value = tran_df['TransactionName'][i]
                rt_value=tran_df['RTSLA'][i]
                indentitingPoints += f"\t 🔴 {transaction_value} degraded by : {rt_value} Secs \n"

    elif (conclusion_df1['Total Amber Transaction'][0]>0 and conclusion_df1['Total Red Transaction'][0] == 0):
        pointer2_forHighRT = "2.  Below are the AMBER listed Transactions with high response time:"
        
        for i in range(conclusion_df1['Total Transaction'][0]) :
            if (tran_df['color'][i] == 'Amber'):
                transaction_value = tran_df['TransactionName'][i]
                rt_value=tran_df['RTSLA'][i]
                indentitingPoints += f"\t 🟡 {transaction_value} degraded by : {rt_value} Secs \n"
    
    elif (conclusion_df1['Total Red Transaction'][0]>0 and conclusion_df1['Total Amber Transaction'][0]>0):
        pointer2_forHighRT = "2.  Below are the listed Transactions which needs to be highlighte"
        
        for i in range(conclusion_df1['Total Transaction'][0]) :
            if (tran_df['color'][i] == 'Red'):
                transaction_value = tran_df['TransactionName'][i]
                rt_value=tran_df['RTSLA'][i]
                indentitingPoints += f"\t 🔴 {transaction_value} degraded by : {rt_value} Secs \n"
        
        for i in range(conclusion_df1['Total Transaction'][0]) :
            if (tran_df['color'][i] == 'Amber'):
                transaction_value = tran_df['TransactionName'][i]
                rt_value=tran_df['RTSLA'][i]
                indentitingPoints += f"\t 🟡 {transaction_value} degraded by : {rt_value} Secs \n"
               
    else:
        pointer2_forHighRT = ""
        
    observation_data = f"""1.  Overall : {str(green_val)}% of Transactions are within SLA, Improved and comparable with previous tests
    {pointer2_forHighRT}
    {indentitingPoints}
    """
#    \n{pointer2_forHighRT} \n{indentitingPoints}"""
    # 
    # 

    summary_df.loc['Observations:','value'] = observation_data
    # summary_df = summary_df.append(pd.Series('Recommendation : Raise defects for the above mentioned transactions as these needs to be investigated  '))
    # if (conclusion_df1['Total Amber Transaction'][0]>0) :
        # summary_df = summary_df.append(pd.Series('Below are the Transactions with high response time which is  :  '))
        # for i in range(conclusion_df1['Total Transaction'][0]) :
            # if (tran_df['color'][i] == 'Amber') :
                # transaction_value = tran_df['TransactionName'][i]
                # rt_value=tran_df['RTSLA'][i]
                # summary_df = summary_df.append(pd.Series(transaction_value) + ['   degraded by :  '] + str(rt_value)+[' Secs'])
        # summary_df = summary_df.append(pd.Series('Recommendation : Raise defects for the above mentioned transactions as these needs to be investigated  '))
     
    return summary_df

def Conclusion(conclusion_df,transaction_summary_df) :

    if (float((conclusion_df['Red %'])) == 0.0 and float((conclusion_df['Amber %'])) == 0.0 and float((conclusion_df['Error %']))< 5.0) :
        conclusion_df['Result'] = 'Passed'
    elif ((float((conclusion_df['Red %'])) < 5.0) and (float((conclusion_df['Amber %'])< 10.0)) and (float((conclusion_df['Error %']) < 5.0))) :
        conclusion_df['Result'] = 'Partially Passed'
    elif (float((conclusion_df['Red %'])) > 5.0) :
        conclusion_df['Result'] = 'Failed'
    elif (float((conclusion_df['Red %'])) < 5.0 and float((conclusion_df['Amber %']))> 10.0) :
        conclusion_df['Result'] = 'Failed'    
    elif (float((conclusion_df['Red %'])) < 5.0 and float((conclusion_df['Amber %'])< 10.0) and float((conclusion_df['Error %']))>10.0) :
        conclusion_df['Result'] = 'Failed'
    #if (float((conclusion_df['Error %'][i]))>10) :
    elif (float((conclusion_df['Error %'])) > 10.0) :
        conclusion_df['Result'] = 'Failed'
    failed_sum = sum(transaction_summary_df["Failed_trx"])
    passed_sum = sum(transaction_summary_df ["Passed_trx"])
    final_df1 = Summary(conclusion_df,transaction_summary_df)

    #final_df1_new = pd.DataFrame(final_df1, index =final_df1)
    #########final_df1_new = final_df1.to_frame(name = 'Test Observations').reset_index(drop = True)
    #st.session_state.final_df = final_df1_new
    #final_df1_new.set_index(col_list[1])
    #final_df1_new.drop(["index"],axis = 1)
    observation_string = final_df1._get_value('Observations:','value').replace("\n","<br/>")
    
    #st.session_state.Business_Process_df[["Transactions per Hour"]] = st.session_state.Business_Process_df[["Transactions per Hour"]].apply(pd.to_numeric) # converting Dataype of string to numeric

    st.markdown(
        '''
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        #customers {
          font-family: Arial, Helvetica, sans-serif;
          border-collapse: collapse;
          width: 100%;
          body text = ="#FFFF00"
        }
        #customers td {
          border: 1px solid #ddd;
          padding: 8px
          word-wrap: break-word;
          color:yellow;
        }
        #customers th {
          border: 1px outset #ddd
          padding-top: 12px;
          padding-bottom: 12px;
          text-align: left;
          background-color: #7e1313;
          color: white;
        }

        </style>
        </head>
        <body>
        ''',unsafe_allow_html = True)
    st.markdown(
        f'''
        <h1>Performance Test Report</h1>

        <table id="customers">
        <tr>
            <th colspan="3"><h3 style="text-align:center;">Performance Test Report</h3></th>

        </tr>
            <th colspan="2"><p style="text-align:center;">Test Summary<p></th>
            <th><p style="text-align:center;">Conclusion<p></th>
        <tr>

        </tr>
          <tr>
            <td>Test Name</td>
            <td>{st.session_state.test_Type}</td>
            <td>Test Objective: {final_df1._get_value('Objective:',"value")}</td>
          </tr>
          <tr>
            <td>Codebase</td>
            <td>{st.session_state.codeBase}</td>
            <td>Test Status: {final_df1._get_value('Test Status:','value')}</td>
          </tr>
          <tr>
            <td>Number of V-User</td>
            <td>{st.session_state.Workload_Characteristics_df.loc[0,'Values']}</td>
            <td rowspan="4">Test Observations:<br/>Response Time Summary<br/> {observation_string}</td>
          </tr>
          <tr>
            <td>Number of Concurrent V-User</td>
            <td>{st.session_state.Workload_Characteristics_df.loc[0,'Values']}</td>
          </tr>
          <tr>
            <td>Steady State Duration(in sec)</td>
            <td>{st.session_state.steady_state - st.session_state.rampup_time}</td>
          </tr>
          <tr>
            <td>Total Failed Transaction</td>
            <td>{failed_sum}</td>
          </tr>
          <tr>
            <td>Total Passed Transaction</td>
            <td>{passed_sum}</td>
            <td></td>
          </tr>
          <tr>
            <td>Avg TPH Achived</td>
            <td>{st.session_state.Business_Process_df.loc[3,'Values']}</td>
            <td></td>
          </tr>
          <tr>
            <td>Test Duration</td>
            <td>{st.session_state.generalDetailsDataFrameForHLR.loc[4,'Values']}</td>
            <td></td>
          </tr>
          <tr>
            <td>Execution Time</td>
            <td>{st.session_state.generalDetailsDataFrameForHLR.loc[3,'Values']}</td>
            <td></td>
          </tr>
        </table>

        </body>
        </html>
        ''',unsafe_allow_html = True
    )
    tableStringInHTML = f'''
        <h1>Performance Test Report</h1>

        <table id="customers">
        <tr>
            <th colspan="3"><h3 style="text-align:center;">Performance Test Report</h3></th>

        </tr>
            <th colspan="2"><p style="text-align:center;">Test Summary<p></th>
            <th><p style="text-align:center;">Conclusion<p></th>
        <tr>

        </tr>
          <tr>
            <td>Test Name</td>
            <td>{st.session_state.test_Type}</td>
            <td>Test Objective: {final_df1._get_value('Objective:',"value")}</td>
          </tr>
          <tr>
            <td>Codebase</td>
            <td>{st.session_state.codeBase}</td>
            <td>Test Status: {final_df1._get_value('Test Status:','value')}</td>
          </tr>
          <tr>
            <td>Number of V-User</td>
            <td>{st.session_state.Workload_Characteristics_df.loc[0,'Values']}</td>
            <td rowspan="4">Test Observations:<br/>Response Time Summary<br/> {observation_string}</td>
          </tr>
          <tr>
            <td>Number of Concurrent V-User</td>
            <td>{st.session_state.Workload_Characteristics_df.loc[0,'Values']}</td>
          </tr>
          <tr>
            <td>Steady State Duration(in sec)</td>
            <td>{st.session_state.steady_state - st.session_state.rampup_time}</td>
          </tr>
          <tr>
            <td>Total Failed Transaction</td>
            <td>{failed_sum}</td>
          </tr>
          <tr>
            <td>Total Passed Transaction</td>
            <td>{passed_sum}</td>
            <td></td>
          </tr>
          <tr>
            <td>Avg TPH Achived</td>
            <td>{st.session_state.Business_Process_df.loc[3,'Values']}</td>
            <td></td>
          </tr>
          <tr>
            <td>Test Duration</td>
            <td>{st.session_state.generalDetailsDataFrameForHLR.loc[4,'Values']}</td>
            <td></td>
          </tr>
          <tr>
            <td>Execution Time</td>
            <td>{st.session_state.generalDetailsDataFrameForHLR.loc[3,'Values']}</td>
            <td></td>
          </tr>
        </table>

        </body>
        </html>
    '''
    cssStringForPerformanceReportTable = '''
    <style>
        #customers {
          font-family: Arial, Helvetica, sans-serif;
          border-collapse: collapse;
          width: 100%;
          body text = ="#FFFF00"
        }
        #customers td {
          border: 1px solid #ddd;
          padding: 8px
          word-wrap: break-word;
          color:black;
        }
        #customers th {
          border: 1px outset #ddd
          padding-top: 12px;
          padding-bottom: 12px;
          text-align: left;
          background-color: #7e1313;
          color: white;
        }

    </style>
    '''
    
    tableStringInHTML_df = pd.read_html(tableStringInHTML)
    
    # tempDirForScreenshotPath = tempfile.TemporaryDirectory()
    # st.write(tempDirForScreenshotPath)
    hti = Html2Image(keep_temp_files = True,size = (1080,550))
    # with open(f"{tempDirForScreenshotPath.name}.png",'wb') as tempImage_ScreenshotPath:
    #with open(f"{tempDirForScreenshotPath.name}.png",'wb') as tempImage_ScreenshotPath:
    #hti.output_path = r'C:\Users\SharmaK21\OneDrive - Vodafone Group\Desktop\Practice\Experiment\Temp'
    #hti.output_path = tempImage_ScreenshotPath
    screenshotPath = hti.screenshot(html_str=tableStringInHTML, css_str=cssStringForPerformanceReportTable, save_as = f'{st.session_state.Business_Process_df.loc[0,"Values"]}.png')
    #st.write(screenshotPath)
    # with open(f'C:\\Users\\SHARMA~1\\AppData\Local\\Temp\\html2image{screenshotPath[0]}.html', 'rb') as file:
        # performanceTestReportbuf = BytesIO(file.read())
    # st.image(performanceTestReportbuf)
    # tempDirForScreenshotPath.close()
    
    ######################  Calling a Function That Count Red Amber Green ###################################################
    return_value = call_statusCount()
    st.write("# Graphical Views For The Executed Test")
    ########################    Calling Function that Calculate Percentage for End Status   ######################################
    #st.session_state.return_value_df = calculatePCTforStatus(return_value)
    
    #st.dataframe(st.session_state.return_value_df.style.set_properties(**{'background-color': 'black','color': 'yellow'}))
    
    st.write("Transaction Status")
    # Creating dataset
    #data = return_value.loc[0,:].values.tolist()

    #fp = tempfile.NamedTemporaryFile()
    pieChart = plotingPIEChartForFinalStatus(return_value)
    
    pieChartbuf = BytesIO()
    pieChart.savefig(pieChartbuf, format="png")

    # print(fp.name) return file name 
    # with open(f"{fp.name}.jpg",'wb') as ff:
        # pieChart.savefig(ff)
    figsList = [pieChartbuf,screenshotPath[0]]
    pieChartbuf.seek(0)

    #-----------------------------------Code to Import Response time Graph
    st.write("Transaction Response Time Trend")

    if st.session_state.Test_type == 'Previous':
        df_thatHoldPreviousDataInOne = pd.DataFrame()
        df_thatHoldPreviousDataInOne['TransactionName'] = st.session_state.RT_Sheet.data['TransactionName']
        dummy_var = 0
        column_list1 = st.session_state.finalRT_df.columns.tolist()
        
        for i in range(len(column_list1)):
            if i%2 != 0:
                if dummy_var ==0:
                    df_thatHoldPreviousDataInOne['Current Test'] = st.session_state.finalRT_df[column_list1[i][0]][column_list1[i][1]].reset_index(drop = True)
                    dummy_var +=1
                else:
                    df_thatHoldPreviousDataInOne[f'Previous Test #{dummy_var}'] = st.session_state.finalRT_df[column_list1[i][0]][column_list1[i][1]].reset_index(drop = True)
                    dummy_var +=1
        #df_thatHoldPreviousDataInOne[f'Current Test'] = st.session_state.uploaded_data[len(st.session_state.uploaded_data)-1]   
        bargraph = responseTimeComparisionGraph(df_thatHoldPreviousDataInOne)
        # fp1 = tempfile.NamedTemporaryFile()
        # with open(f"{fp1.name}.jpg",'wb') as ff1:
            # bargraph.savefig(ff1,figsize =(10, 10),dpi= 50)
        
    else :
        bargraph = responseTimeGraph_CurrentTest(st.session_state.RT_Sheet.data)
        #bargraph.set_figwidth(15)
        #bargraph.set_figheight(6)
        # fp1 = tempfile.NamedTemporaryFile()
        # with open(f"{fp1.name}.jpg",'wb') as ff1:
            # #bargraph.savefig(ff1,figsize=(10,5))
            # bargraph.set_size_inches(30, 11)
            # bargraph.set_dpi(60)
            # bargraph.savefig(ff1)
    barGraphBuf = BytesIO()
    bargraph.savefig(barGraphBuf, format="jpg",bbox_inches='tight')
    figsList.append(barGraphBuf)
    barGraphBuf.seek(0)
    
    st.write('#  High Level Report Summary')
    st.write('Workload Characteristics')
    
    hide_dataframe_row_index = """
            <style>
            .row_heading.level0 {display:none}
            .blank {display:none}
            </style>
            """

        # Inject CSS with Markdown
    st.table(st.session_state.Workload_Characteristics_df.style.set_properties(**{'background-color': 'black','color': 'yellow'}))
    
    st.write('Performance Overview')
    st.table(st.session_state.Performance_Overview_df.style.set_properties(**{'background-color': 'black','color': 'yellow'}))
    st.write('Business Process')
    st.table(st.session_state.Business_Process_df.style.set_properties(**{'background-color': 'black','color': 'yellow'}))

    st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)
    
    

    if st.session_state.Test_type == 'Previous':
        temp_dir_concatDdf = tempfile.NamedTemporaryFile()
        with open(f"{temp_dir_concatDdf.name}.png",'wb') as tempImage_concatDdf:
            dfi.export(st.session_state.finalRT_df.style.set_properties(**{'background-color': 'black','color': 'yellow'}), tempImage_concatDdf)
        pdf = writing_PDF_file(final_df1,figsList,transaction_summary_df,tempImage_concatDdf)
        html = create_download_link(pdf.output(dest="S").encode("latin-1"), "Result")
        st.markdown(html, unsafe_allow_html=True)
    else:
        pdf = writing_PDF_file(final_df1,figsList,transaction_summary_df)
        html = create_download_link(pdf.output(dest="S").encode("latin-1"), "Result")
        st.markdown(html, unsafe_allow_html=True)
    return conclusion_df

def read_summary(summary_df,count_df ) :
    
    transaction_summary_df = summary_df
    
    ## PCT DF return_value_df
    transaction_count_df = count_df

    conclusion_df = transaction_count_df
    conclusion_df['Result'] = ""
    Conclusion(conclusion_df,transaction_summary_df)
    return conclusion_df,transaction_summary_df






####################    Fetching Json From API with Transaction Status ################################################ 
#json_data = json.loads(st.session_state.JsonResponse_df.text)
#final_df =json_normalize(json_data)

return_value = call_statusCount()

# st.write("Tabulate Representation for Test Status")
return_value_df = calculatePCTforStatus(return_value)
data = read_summary(st.session_state.RT_Sheet.data,return_value_df)


# def to_excel(*callable_value):
    
    # output = BytesIO()
    # writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # df1 = callable_value[0]
    # df2 = callable_value[1]
    # df3 = callable_value[2]
    
    # df1.to_excel(writer, sheet_name='Test Summary')
    # df2.to_excel(writer, sheet_name='Test Summary', startcol = 3,index = False)
    # #df3.to_excel(writer, sheet_name='Response Time Sheet',index = False)
    # if len(callable_value) ==6:
        # df4 = callable_value[4]
        # length = len(df3['TransactionName'])
        # df4.to_excel(writer, sheet_name='Response Time Sheet',startrow = length+2)
    # workbook = writer.book
    
    # #xlswritefig(callable_value[3], 'Test Summary', length1)
    # worksheet = writer.sheets['Test Summary']
    # ##### Adding images to excel
    # path = callable_value[2]
    # file = open(path, 'rb')
    # data = BytesIO(file.read())
    # file.close()
    # worksheet.insert_image('B15','image.jpg', {'image_data': data})
    
    # path1 = callable_value[3]
    # file1 = open(path1, 'rb')
    # data1 = BytesIO(file1.read())
    # file1.close()
    # worksheet.insert_image('L15','image.jpg', {'image_data': data1})
    
    # format1 = workbook.add_format({'num_format': '0.00'}) 
    # worksheet.set_column('A:A', None, format1)  
    # writer.save()
    # processed_data = output.getvalue()
    # return processed_data
