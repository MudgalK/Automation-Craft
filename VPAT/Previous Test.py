import streamlit as st
import requests 
from pathlib import Path
from zipfile import ZipFile
import pandas as pd
from pandas import json_normalize
import json
from functools import reduce
from operator import add
from io import BytesIO

#st.set_page_config(layout="wide")
#####__________________________________________________________________Main Function for Previous Test Records:Begins_____________________________________##########
def working_with_previousTestData():
    #########--------------------------------Decalring Function To Set Variable constraints for Session:Begins-------------------------------------------###########
    if "constraints_variable" not in st.session_state:
        st.session_state["finalRT_df"] = pd.DataFrame()
        st.session_state["uploaded_data"] = []
        st.session_state["previousTest1_df"] = pd.DataFrame()
        st.session_state["previousTest2_df"] = pd.DataFrame()
        st.session_state["previousTest3_df"] = pd.DataFrame()
        st.session_state["previousTest4_df"] = pd.DataFrame()
        st.session_state["button_clicked"] = False
        st.session_state["cols"] = ""
        st.session_state["host_url"] = r'http://127.0.0.1:8000'
        st.session_state["constraints_variable"] = 0
        st.session_state["session_variable"] = 0
        st.session_state["dropDown_data"] = pd.DataFrame(columns = ["Transaction Name","Standard SLA","Expected Volume"])
        st.session_state['Test_type'] = 'Previous'
    #########---------------------------------Decalring Function To Set Variable constraints for Session:Completed----------------------------------------###########

    def functionForPullingDataFromMDBFile(mdb_filepath):
        rampup_time = st.number_input("Please Enter the timestamp when Ramp-up Ends in Sec.", min_value=0, step=1)
        steady_state = st.number_input("Please Enter the timestamp when Steady State Ends in Sec.", min_value=0, step=1)
        if rampup_time != 0 and  steady_state !=0:
            try:
                if st.session_state.status_code == 200:
                    return st.session_state.previousResultsDataFrame
            except:
                data_json = {"mdb_filepath" : f"{mdb_filepath}", "ramp_up":rampup_time, "steady_state":st.session_state.steady_state}
                previousTestResults_response = requests.post(f"{st.session_state.host_url}/previousResults",json = data_json, headers = {'Content-Type': "application/json; charset=utf-8"})
                details =json_normalize(previousTestResults_response.json())
                st.session_state.previousResultsDataFrame = details
                st.session_state.status_code = previousTestResults_response.status_code
                return details
        else:
            st.info("Awaiting for User Input")
    #####--------------------------------------------Defining a Function that will convert a previous test results in to a DataFrame: Begins------------------#######
    def convert_file2df(new_file):
        st.write("Entered")
        file_type = new_file.type
        st.write(file_type)
        if file_type == "application/msaccess":
            try:
                save_path_file2 = Path(st.session_state.mdb_filepath, new_file.name)
                #---------------------------------------------Writing the Entire file to given Directory, cause in streamlit you can't fetch directory while uploading -----------------
                with open(save_path_file2, mode='wb') as w:
                    w.write(new_file.getvalue())
                    if save_path_file2.exists():
                        #------------------------------------------------Writing the Success Msg upon uploading------------------------------------------------------------------------
                        st.success(f'File {new_file.name} is successfully uploaded, please Continue!')
                #--------------------------------------------------------Pulling MDB data in a fetchdata API------------------------------------------------------------------------
            except PermissionError:
                pass
            previousTestResults_df1 = functionForPullingDataFromMDBFile(save_path_file2)
            return previousTestResults_df1
            
        elif file_type == "text/csv":
            st.info("Please Make Sure that csv file has columns with Names like, 'Transaction Name','Average response time', and '90%', else it will throw an error", icon = "⚠️")
            details = pd.read_csv(new_file, encoding= 'unicode_escape')
            previousTestResults_df2 = details.sort_values(by = 'Transaction Name')
            return previousTestResults_df2
            
        elif file_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            st.info("Please Make Sure that csv file has columns with Names like, 'Transaction Name','Average response time', and '90%', else it will throw an error", icon = "⚠️")
            details = pd.read_excel(new_file)
            previousTestResults_df3 = details.sort_values(by = 'Transaction Name')
            return previousTestResults_df3
        
    #####------------------------------------------------------Defining a Function that will convert a previous test results in to a DataFrame:Completed----------------------#######


    #####----------------------------------------Defining a Function that will list the Previous Records to concatenate the dataframe into one:Begins----------------------#######
    
    # @st.cache_data
    # def concatinatingDataFrame(previousTest_df):
        # #st.session_state.uploaded_data.append(previousTest_df)
        # st.session_state.uploaded_data.insert(0,previousTest_df["Average response time"])
        # st.session_state.uploaded_data.insert(1,previousTest_df["90%"])
    
    # @st.cache_data
    # def concatinatingDataFrame(previousTest_df):
        # uploaded_data = []
        # #st.session_state.uploaded_data.append(previousTest_df)
        # uploaded_data.insert(0,previousTest_df["Average response time"])
        # uploaded_data.insert(1,previousTest_df["90%"])
        # return uploaded_data
    #####----------------------------------------Defining a Function that will list the Previous Records to concatenate the dataframe into one:Completed----------------------#######

    def evaluatingRTSLA_AsPerBaseline(df1, benchmark_selectedValue):
        
        if benchmark_selectedValue == "Average RT":
            df1["Response time difference (when compared to SLA)"] = df1["Average response time"] - df1["Baseline SLA"]
        if benchmark_selectedValue == "75th Percentile RT":
            df1["Response time difference (when compared to SLA)"] = df1["75%"] - df1["Baseline SLA"]
        if benchmark_selectedValue == "80th Percentile RT":
            df1["Response time difference (when compared to SLA)"] = df1["80%"] - df1["Baseline SLA"]
        if benchmark_selectedValue == "85th Percentile RT":
            df1["Response time difference (when compared to SLA)"] = df1["85%"] - df1["Baseline SLA"]
        if benchmark_selectedValue == "90th Percentile RT":
            df1["Response time difference (when compared to SLA)"] = df1["90%"] - df1["Baseline SLA"]
        if benchmark_selectedValue == "95th Percentile RT":
            df1["Response time difference (when compared to SLA)"] = df1["95%"] - df1["Baseline SLA"]
        
        return df1        
        

    #####------------------------------------------Defining a Function that will Evaluate Baseline SLA on basis of Latest Test Records:Begins----------------------------------#######
    def evaluatingBaselineSLA_df2(new_df):
        length = len(new_df["Transaction Name"])
        j = 0
        while j < length:
            new_df.loc[j,"Baseline SLA"] = st.session_state.finalRT_df["Previous Test #1 Records"]["90 percentile RT"][j]
            
            j +=1
        return new_df
    #####----------------------------------------Defining a Function that will Evaluate Baseline SLA on basis of Latest Test Records:Completed--------------------------------#######
    
    #####---------------------------------Defining a Function that will Evaluate Standard SLA Transaction Wise in Accordance with user input:Begins----------------------------#######
    def evaluatingStandardSLA_TransactionWise_df2(new_df_2):
        transactionName_list = list(new_df_2["Transaction Name"])
        a = 0
                #Assigning DataFrame outside the form
        df_table = st.session_state.dropDown_data
        length = len(transactionName_list)
        x_list = list(df_table["Transaction Name"])
                #To Assign the SLA value corresponding to each transaction
        while a<length :
            val = transactionName_list[a]
            if val in x_list:
                for j in range(len(x_list)):
                    if val == x_list[j]:
                        new_df_2.loc[a,"Standard SLA"] = df_table["Standard SLA"][j]
                        new_df_2.loc[a,"Expected Volume"] = df_table["Expected Volume"][j]
            else:
                new_df_2.loc[a,"Standard SLA"] = 0
                new_df_2.loc[a,"Expected Volume"] = 0
            a +=1
        return new_df_2
    #####-------------------------------Defining a Function that will Evaluate Standard SLA Transaction Wise in Accordance with user input:Completed---------------------------#######
    
    #####--------------------------Defining a Function that will Evaluate Standard SLA Uniform to All Transaction in Accordance with user input:Begins-------------------------#######
    def evaluatingStandardSLA_UnifornToAllTransaction_df2(new_df_3):
                #Assigning Constrainsts to invoke the data of existing list
        transactionName_list = list(new_df_3["Transaction Name"])
        a = 0
                #Assigning DataFrame outside the form
        df_table = st.session_state.dropDown_data
        length = len(transactionName_list)
                #To Assign the SLA value to every transaction
        while a<length :
            new_df_3.loc[a,"Standard SLA"] = df_table["Standard SLA"][0]
            new_df_3.loc[a,"Expected Volume"] = df_table["Expected Volume"][0]
            a +=1
        return new_df_3
    #####-----------------------Defining a Function that will Evaluate Standard SLA Uniform to All Transaction in Accordance with user input:Completed------------------------#######
    
    
    #######------------------------------Decalring Function to Estimate Standard SLA and Expected Volume Column on Basis of Records: Begins--------------------------------##########
    def allocatingValuesToStanSLA_ExpCol(currentTest_df1,expected_standardSLA2,local_list):
        length = len(currentTest_df1["Transaction Name"])
        j = 0
        while j < length :
            currentTest_df1.loc[j,"Standard SLA"] = expected_standardSLA2[j]
            currentTest_df1.loc[j,"Expected Volume"] = local_list[j]
            j +=1
        return currentTest_df1
    #######------------------------------Decalring Function to Estimate Standard SLA and Expected Volume Column on Basis of Records: Completed-----------------------------##########

    
    #######------------------------------Decalring Function to Check whether Previous data holds Records for Expected Volume or Not: Begins--------------------------------##########
    def checkingForExpectedVolCol(new_df_3,expected_standardSLA1):
        passed_transaction = list(new_df_3["Passed trx"])
        failed_transaction = list(new_df_3["Failed trx"])
        df_table = st.session_state.finalRT_df
        dummy_list = []
        required_col = ["Passed trx","Failed trx","Total Transaction","Volume"]
        cols_name = st.session_state.previousTest1_df.columns
        for cols_value in cols_name:
            if cols_value in required_col:
                if cols_value == "Passed trx":
                    dummy_list.append(cols_value)
                elif cols_value == "Failed trx":
                    dummy_list.append(cols_value)
                elif cols_value == "Total Transaction":
                    dummy_list.append(cols_value)
                elif cols_value == "Volume":
                    dummy_list.append(cols_value)
        ####---In Case, Previous Records doesn't holds records for expected volume then would consider Total Transaction as Expected Volume
        if len(dummy_list) == 0:
            st.info("Uploaded Records doesn't have any columns for Passed trx,Failed trx,Total Transaction and Volume; Thus can't predict expected volume on basis of previous test. Therefore, Considering Total Transaction as Expected volume in such case.", icon = "⚠️")
            expected_volume = list(map(add, passed_transaction, failed_transaction))
            completed_df = allocatingValuesToStanSLA_ExpCol(new_df_3,expected_standardSLA1,expected_volume)
        else:
            if "Total Transaction" in dummy_list:
                st.write("Out of Uploaded Records, Most recent Test has records having column as \"Total Transaction\", thus considering this data for expected volume")
                expected_volume = list(st.session_state.previousTest1_df["Total Transaction"])
                completed_df = allocatingValuesToStanSLA_ExpCol(new_df_3,expected_standardSLA1,expected_volume)
            elif "Passed trx" in dummy_list:
                if "Failed trx" in dummy_list:
                    passed_transaction1 = list(st.session_state.previousTest1_df["Passed trx"])
                    failed_transaction1 = list(st.session_state.previousTest1_df["Failed trx"])
                    expected_volume = list(map(add, passed_transaction1, failed_transaction1))
                    completed_df = allocatingValuesToStanSLA_ExpCol(new_df_3,expected_standardSLA1,expected_volume)
                else:
                    st.info("Uploaded Records doesn't have columns for Failed trx; Thus can't predict expected volume on basis of previous test. Therefore, Considering Total Transaction as Expected volume in such case.", icon = "⚠️")
                    expected_volume = list(map(add, passed_transaction, failed_transaction))
                    completed_df = allocatingValuesToStanSLA_ExpCol(new_df_3,expected_standardSLA1,expected_volume)
            elif "Volume" in dummy_list:
                passed_transaction1 = list(st.session_state.previousTest1_df["Volume"])
                completed_df = allocatingValuesToStanSLA_ExpCol(new_df_3,expected_standardSLA1,expected_volume)
        return completed_df
    #######------------------------------Decalring Function to Check whether Previous data holds Records for Expected Volume or Not: Completed---------------------------------#######
    
    
    #######------------------------------Decalring Function to Estimate Standard SLA and Expected Volume Column on Basis of Uploaded Data: Begins---------------------------##########
    def evaluatingStandardSLA_WhenChooseFromData(new_df_3, selectedValue):
        
        if selectedValue == "Same as Baseline SLA which is 90th% of Previous Test #1 Records":
            expected_standardSLA = list(new_df_3["Baseline SLA"])
            completed_df = checkingForExpectedVolCol(new_df_3,expected_standardSLA)
        
        elif selectedValue == "90th% of Previous Test #2 Records":
            expected_standardSLA = list(st.session_state.finalRT_df["Previous Test #2 Records"]["90 percentile RT"])
            completed_df = checkingForExpectedVolCol(new_df_3,expected_standardSLA)
        
        elif selectedValue == "90th% of Previous Test #3 Records":
            expected_standardSLA = list(st.session_state.finalRT_df["Previous Test #3 Records"]["90 percentile RT"])
            completed_df = checkingForExpectedVolCol(new_df_3,expected_standardSLA)
        
        elif selectedValue == "90th% of Previous Test #4 Records":
            expected_standardSLA = list(st.session_state.finalRT_df["Previous Test #4 Records"]["90 percentile RT"])
            completed_df = checkingForExpectedVolCol(new_df_3,expected_standardSLA)

        return completed_df
    #######------------------------------Decalring Function to Estimate Standard SLA and Expected Volume Column on Basis of Uploaded Data: Completed------------------------##########
    
    
    #####-----------------------------------------------------Defining a Function that will predict status of transaction color wise: Begins----------------------------------#######
    def evaluatingFinalResults(df,flow_type):
        csv_bytes = df.to_csv(index=False).encode()
        csv_buffer = BytesIO(csv_bytes)
        files = {'file': ('data.csv',csv_buffer)}
        data = {'Flow_Type': flow_type}
        #response = requests.post(f"{st.session_state.host_url}/predict", files=files,data=data, headers = {'Content-Type': "application/json; charset=utf-8"})
        response = requests.post(f"{st.session_state.host_url}/predict", files=files,data=data)
        # payload = df.to_json(orient = "records")
        # response = requests.post(f"{st.session_state.host_url}/predict?df_in={payload}&flow_type={flow_type}", headers = {'Content-Type': "application/json; charset=utf-8"})
        json_response = response.text
        json_data = json.loads(json_response)
        final_df =json_normalize(json_data)
        return final_df
    #####-----------------------------------------------------Defining a Function that will predict status of transaction color wise: Ends------------------------------------#######
    
    
    #####-----------------------------------------------------Defining a Function that will highlight status column on basis of color: Begins----------------------------------#######
    def highlighter(series):
        return ["background-color: green;" if e == "Green" else "background-color: red;" if e == "Red" else "background-color: orange;" if e == "Amber" else "background-color: white;" for e in series]
    #####-----------------------------------------------------Defining a Function that will highlight status column on basis of color: completed-------------------------------#######
    @st.cache_data
    def creatingAConcatinatingDataframe(listThatHold_DfRecord_returnValue):

        dummy_df = pd.DataFrame()
        for i in range(len(listThatHold_DfRecord_returnValue)):
            dummy_df[f'Average RT Test{i}'] = listThatHold_DfRecord_returnValue[i]["Average response time"]
            dummy_df[f'90% RT Test{i}'] = listThatHold_DfRecord_returnValue[i]["90%"]
            

        #dummy_df = pd.concat(st.session_state.uploaded_data, join='outer', axis = 1)
        #length = len(st.session_state.previousTest1_df["Transaction Name"])
        length = len(st.session_state.RT_Sheet["Transaction Name"])
        st.session_state.finalRT_df = pd.DataFrame([dummy_df.loc[j, :].values for j in range(0,length,1)],columns = st.session_state.cols, index= st.session_state.RT_Sheet["Transaction Name"])
        #st.session_state.finalRT_df = st.session_state.finalRT_df.insert(0,"Transaction Name", st.session_state.previousTest1_df["Transaction Name"])
        #st.write(st.session_state.finalRT_df.columns.tolist())
        st.dataframe(st.session_state.finalRT_df)
        return st.session_state.finalRT_df
        
    @st.cache_data
    def fileUploaderFunction(*inputFile_df):
        listThatHold_DfRecord = []
        for value in inputFile_df:
            listThatHold_DfRecord.append(value)
        return listThatHold_DfRecord
    
    def callbackfunction():
        st.session_state.button_clicked = True
                
    ###########################################################   Streamlit Code Begins   ###########################################################################
    
    #####---------------------------------------------Asking for previous test records: Begins---------------------------------------------------------------#######

    #------------------------------------------------Pulling MDB data in a fetchdata API-----------------------------------------------------------------------------
    # response_data = requests.post(f"{st.session_state.host_url}/fetchdata?path={st.session_state.mdb_path}", headers = {'Content-Type': "application/json; charset=utf-8"})
    # #----------------------------------------------converting Json data into a DataFrame so that it can be used further--------------------------------------------
    # currentTest_df =json_normalize(response_data.json())
    # fetchdata_url = f"{st.session_state.host_url}/fetchdata"
    # string = f'{st.session_state.mdb_path}'
    # updated_path = string.replace("\+","\\")
    # data_json = {"path" : updated_path, "ramp_up":st.session_state.rampup_time, "steady_state":st.session_state.steady_state}
    # response_data = requests.post(fetchdata_url,json = data_json , headers = {'Content-Type': "application/json; charset=utf-8"})
    # #------------------------------------------------converting Json data into a DataFrame so that it can be used further--------------------------------------------
    # currentTest_df =json_normalize(response_data.json())
    currentTest_df = st.session_state.RT_Sheet
    
    #---------------------------------------------Decalring number box to insert integer number to track records of uploaded test-----------------------------------------------------
    number = st.number_input("Enter Number of Previous records you want to compare, make sure you enter interger between 1 to 4", min_value = 0, max_value = 4, step = 1)
    
    if number == 1:
        file2 = st.file_uploader("Choose File from Previous Test",key = "file2", label_visibility="visible",type = [".mdb",".csv",".xlsx"])
        st.write(file2)
        st.session_state.cols = pd.MultiIndex.from_product([["Current Test Records","Previous Test #1 Records"],["Average RT","90 percentile RT"]],names = ["Test Name","RT type"])
        if file2 is not None:
            st.session_state.previousTest1_df = convert_file2df(file2)
            listThatHold_DfRecord_returnValue = fileUploaderFunction(currentTest_df,st.session_state.previousTest1_df)
            
    elif number == 2:
        file2 = st.file_uploader("Choose File #1 from Previous Test", type = [".mdb",".csv",".xlsx"])
        st.session_state.cols = pd.MultiIndex.from_product([["Current Test Records","Previous Test #1 Records","Previous Test #2 Records"],["Average RT","90 percentile RT"]],names = ["Test Name","RT type"])
        if file2 is not None:
            st.session_state.previousTest1_df = convert_file2df(file2)
                
        file3 = st.file_uploader("Choose File #2 from Previous Test", type = [".mdb",".csv",".xlsx"])
        if file3 is not None:
            st.session_state.previousTest2_df = convert_file2df(file3)
            
        if file2 is not None and file3 is not None:
            listThatHold_DfRecord_returnValue = fileUploaderFunction(currentTest_df,st.session_state.previousTest1_df,st.session_state.previousTest2_df)
            
    elif number == 3:
        file2 = st.file_uploader("Choose File #1 from Previous Test", type = [".mdb",".csv",".xlsx"])
        st.session_state.cols = pd.MultiIndex.from_product([["Current Test Records","Previous Test #1 Records","Previous Test #2 Records","Previous Test #3 Records"],["Average RT","90 percentile RT"]],names = ["Test Name","RT type"])
        if file2 is not None:
            st.session_state.previousTest1_df = convert_file2df(file2)

        file3 = st.file_uploader("Choose File #2 from Previous Test", type = [".mdb",".csv",".xlsx"])
        if file3 is not None:
            st.session_state.previousTest2_df = convert_file2df(file3)

        file4 = st.file_uploader("Choose File #3 from Previous Test", type = [".mdb",".csv",".xlsx"])
        if file4 is not None:
            st.session_state.previousTest3_df = convert_file2df(file4)
        if file2 is not None and file3 is not None and file4 is not None:
            listThatHold_DfRecord_returnValue = fileUploaderFunction(currentTest_df,st.session_state.previousTest1_df,st.session_state.previousTest2_df,st.session_state.previousTest3_df)

    elif number == 4:
        file2 = st.file_uploader("Choose File #1 from Previous Test", type = [".mdb",".csv",".xlsx"])
        st.session_state.cols = pd.MultiIndex.from_product([["Current Test Records","Previous Test #1 Records","Previous Test #2 Records","Previous Test #3 Records","Previous Test #4 Records"],["Average RT","90 percentile RT"]],names = ["Test Name","RT type"])
        if file2 is not None:
            st.session_state.previousTest1_df = convert_file2df(file2)

        file3 = st.file_uploader("Choose File #2 from Previous Test", type = [".mdb",".csv",".xlsx"])
        if file3 is not None:
            st.session_state.previousTest2_df = convert_file2df(file3)

        file4 = st.file_uploader("Choose File #3 from Previous Test", type = [".mdb",".csv",".xlsx"])
        if file4 is not None:
            st.session_state.previousTest3_df = convert_file2df(file4)

        file5 = st.file_uploader("Choose File #4 from Previous Test", type = [".mdb",".csv",".xlsx"])
        if file5 is not None:
            st.session_state.previousTest4_df = convert_file2df(file5)
            
        if file2 is not None and file3 is not None and file4 is not None and file5 is not None:
            listThatHold_DfRecord_returnValue = fileUploaderFunction(currentTest_df,st.session_state.previousTest1_df,st.session_state.previousTest2_df,st.session_state.previousTest3_df,st.session_state.previousTest4_df)
   
    #####------------------------------------------Asking for previous test records:Completed-----------------------------------------------------------------#######
    
    
    ##Nested Button To Continue
    st.button("Submits", on_click = callbackfunction)
    if st.session_state.button_clicked:
        # for i in range(len(listThatHold_DfRecord_returnValue)):
            # concatinatingDataFrame(listThatHold_DfRecord_returnValue[i])
        
        #Using Try and Except Method to validate in case of session failure
        st.session_state.finalRT_df = creatingAConcatinatingDataframe(listThatHold_DfRecord_returnValue)
        #####   evaluating Baseline SLA
        updated_df = evaluatingBaselineSLA_df2(currentTest_df)
        
        #----------------------Decalring Radio Button For Flow Type--------------------------
        radio_options1 = ["Select","GUI Flow", "API Flow"]
        flowType_choice  = st.radio(label = "Please choose for Flow Type", options = radio_options1, horizontal = True)
        
        ####################evaluating Standard SLA
        
        benchmarkSelectBox_list = ["Average RT","75th Percentile RT","80th Percentile RT","85th Percentile RT","90th Percentile RT","95th Percentile RT"]
        benchmarkSelectBox = st.selectbox("Please Select from below options As Benchmark",benchmarkSelectBox_list)
        
        checkbox3 = st.checkbox("Proceed")
        if checkbox3:
            update_new_df = evaluatingRTSLA_AsPerBaseline(updated_df,benchmarkSelectBox)
        
            standardSLA_recordList = ["Select","Enter Standard SLA Manually","Enter Standard SLA from uploaded data"]
            standardSLA_record_radioBox = st.radio("Please Pick from below option for Standard SLAs", options = standardSLA_recordList, horizontal = True)
        
        
            if standardSLA_record_radioBox == standardSLA_recordList[1]:
                standardSLA_optionList = ["Select","Transaction wise","Uniform to All Transactions"]
                standardSLA_SelectBox = st.selectbox("Please Select below options to enter NFRs",standardSLA_optionList)
                
                #####   evaluating Standard SLA Transaction Wise
                if standardSLA_SelectBox == standardSLA_optionList[1]:
                    col1 , col2, col3 = st.columns(3)
        #-----------------------------------------Getting Transaction Column from the mdb Reader function----------------------------------------------------------------
                    transactionName_list = list(currentTest_df["Transaction Name"])
        #------------------------------------------Creating a form that keep the entire batch as one unit else all data would render on each call------------------------
                    with st.form("my_form"):
                        with col1:
                            dropDown = st.selectbox("Pick Transaction Name",transactionName_list)
                        with col2: 
                            standardSLA_number = st.number_input("Enter Standard SLA Value")
                        with col3: 
                            standardExpectedVolume_number = st.number_input("Enter Expected Volume")
                #-----------------------------------------form won't work without form_submit_button in streamlit-----------------------------------------------------------
                        submit = st.form_submit_button("Submit")
                        if submit:
                            st.session_state.dropDown_data.loc[st.session_state.constraints_variable] = [dropDown,standardSLA_number,standardExpectedVolume_number]
                            st.session_state.constraints_variable +=1
                            st.table(st.session_state.dropDown_data)
                            dataframe_with_standardSLA = evaluatingStandardSLA_TransactionWise_df2(updated_df)
                            colored_df = evaluatingFinalResults(dataframe_with_standardSLA,flowType_choice)
                            drop_list = ['TransactionName','Standard_SLA','Baseline_SLA','Expected_Volume','Passed_trx','Failed_trx','Average response time','Min','Max','RTSLA','90%','95%','color','comment']
                            last_df = colored_df.drop(colored_df.columns.difference(drop_list), axis=1)
                            last_df1 = last_df.style.set_properties(**{'background-color': 'black','color': 'yellow'})
                            st.session_state.RT_Sheet = last_df1.apply(highlighter, subset = ["color"], axis = 0)
                            st.dataframe(st.session_state.RT_Sheet)
                            
                            # st.session_state.RT_Sheet = last_df1.apply(highlighter, subset = ["color"], axis = 0)
                            # st.dataframe(st.session_state.RT_Sheet)
                            # json_string = last_df.to_json(orient = "records")
                            # st.session_state.JsonResponse_df = requests.post(f"{st.session_state.host_url}/FinalResults?df_jsonString={json_string}", headers = {'Content-Type': "application/json; charset=utf-8"})


                #####   evaluating Standard SLA Uniform To All Transaction
                elif standardSLA_SelectBox == standardSLA_optionList[2]:
                    col1 , col2 = st.columns(2)
                    transactionName_list = list(currentTest_df["Transaction Name"])
        #------------------------------------------Creating a form that keep the entire batch as one unit else all data would render on each call------------------------
                    with st.form("my_form"):
                        with col1: 
                            standardSLA_number = st.number_input("Enter Standard SLA Value")
                        with col2: 
                            standardExpectedVolume_number = st.number_input("Enter Expected Volume")    
        #-----------------------------------------form won't work without form_submit_button in streamlit-----------------------------------------------------------
                        submit = st.form_submit_button("Submit")
                        if submit:
                            st.session_state.dropDown_data.loc[st.session_state.constraints_variable] = ["NA",standardSLA_number,standardExpectedVolume_number]
                            st.session_state.constraints_variable +=1
                            st.table(st.session_state.dropDown_data)
                            dataframe_with_standardSLA = evaluatingStandardSLA_UnifornToAllTransaction_df2(updated_df)
                            colored_df = evaluatingFinalResults(dataframe_with_standardSLA,flowType_choice)
                            drop_list = ['TransactionName','Standard_SLA','Baseline_SLA','Expected_Volume','Passed_trx','Failed_trx','Average response time','Min','Max','RTSLA','90%','95%','color','comment']
                            last_df = colored_df.drop(colored_df.columns.difference(drop_list), axis=1)
                            last_df1 = last_df.style.set_properties(**{'background-color': 'black','color': 'yellow'})
                            st.session_state.RT_Sheet = last_df1.apply(highlighter, subset = ["color"], axis = 0)
                            st.dataframe(st.session_state.RT_Sheet)
                            json_string = last_df.to_json(orient = "records")
                            st.session_state.JsonResponse_df = requests.post(f"{st.session_state.host_url}/FinalResults?df_jsonString={json_string}", headers = {'Content-Type': "application/json; charset=utf-8"})

            #####   evaluating Standard SLA on Basis of Uploaded File
            elif standardSLA_record_radioBox == standardSLA_recordList[2]:
                standardSLA_SelectBoxFromUploadedData1 = ["Select","Same as Baseline SLA which is 90th% of Previous Test #1 Records"]
                standardSLA_SelectBoxFromUploadedData2 = ["Select","Same as Baseline SLA which is 90th% of Previous Test #1 Records","90th% of Previous Test #2 Records"]
                standardSLA_SelectBoxFromUploadedData3 = ["Select","Same as Baseline SLA which is 90th% of Previous Test #1 Records","90th% of Previous Test #2 Records","90th% of Previous Test #3 Records"]
                standardSLA_SelectBoxFromUploadedData4 = ["Select","Same as Baseline SLA which is 90th% of Previous Test #1 Records","90th% of Previous Test #2 Records","90th% of Previous Test #3 Records","90th% of Previous Test #4 Records"]
                if number == 1:
                    standardSLA_SelectBox1 = st.selectbox("Please Pick from below option to select SLA type",standardSLA_SelectBoxFromUploadedData1)
                elif number == 2:
                    standardSLA_SelectBox1 = st.selectbox("Please Pick from below option to select SLA type",standardSLA_SelectBoxFromUploadedData2)
                elif number == 3:
                    standardSLA_SelectBox1 = st.selectbox("Please Pick from below option to select SLA type",standardSLA_SelectBoxFromUploadedData3)
                elif number == 4:
                    standardSLA_SelectBox1 = st.selectbox("Please Pick from below option to select SLA type",standardSLA_SelectBoxFromUploadedData5)
                checkbox2 = st.checkbox("Continue")
                if checkbox2:
                    dataframe_with_standardSLA = evaluatingStandardSLA_WhenChooseFromData(updated_df,standardSLA_SelectBox1)
                    colored_df = evaluatingFinalResults(dataframe_with_standardSLA,flowType_choice)

#####Printing Results######################################
                    # if benchmarkSelectBox_list == 'Average RT':
                        # drop_list_value = 'Average response time'
                    # elif benchmarkSelectBox_list ==    ,"75th Percentile RT","80th Percentile RT","85th Percentile RT","90th Percentile RT","95th Percentile RT"'
                    drop_list = ['TransactionName','Standard_SLA','Baseline_SLA','Expected_Volume','Passed_trx','Failed_trx','Average response time','Min','Max','RTSLA','90%','95%','color','comment']
                    last_df = colored_df.drop(colored_df.columns.difference(drop_list), axis=1)
                    last_df1 = last_df.style.set_properties(**{'background-color': 'black','color': 'yellow'})
                    st.session_state.RT_Sheet = last_df1.apply(highlighter, subset = ["color"], axis = 0)
                    st.dataframe(st.session_state.RT_Sheet)
                    # st.session_state.RT_Sheet = last_df1.apply(highlighter, subset = ["color"], axis = 0)
                    # st.dataframe(st.session_state.RT_Sheet)
                    # json_string = last_df.to_json(orient = "records")
                    # st.session_state.JsonResponse_df = requests.post(f"{st.session_state.host_url}/FinalResults?df_jsonString={json_string}", headers = {'Content-Type': "application/json; charset=utf-8"})
                    
    #########################################################   Streamlit Code Ends   ##############################################################################
#####________________________________________________________________Main Function for Previous Test Records:Completed_______________________________________#######
