import streamlit as st
import requests 
from pathlib import Path
from zipfile import ZipFile
import pandas as pd
from pandas import json_normalize
import json
from operator import add
import cryptpandas as crp
from io import BytesIO


#####____________________________________________________________________________Main Function for Previous Test Records:Begins_____________________________________________##########
def working_with_currentTestData():

    #########-----------------------------------------Decalring Function To Set Variable constraints for Session:Begins----------------------------------------------------###########
    if "constraints_variable" not in st.session_state:
        st.session_state["constraints_variable"] = 0
        st.session_state["dropDown_data"] = pd.DataFrame(columns = ["Transaction Name","Standard SLA","Expected Volume"])
        st.session_state["host_url"] = r'http://127.0.0.1:8000'
        st.session_state['JsonResponse_df'] = ""
        st.session_state['Test_type'] = 'current'
        
    #########-----------------------------------------Decalring Function To Set Variable constraints for Session:Completed-------------------------------------------------###########
    
    #########--------------------------------------Decalring Function To Highlight Color Column as per Color Coding:Begins-------------------------------------------------###########
    def highlighter(series):
        return ["background-color: green;" if e == "Green" else "background-color: red;" if e == "Red" else "background-color: orange;" if e == "Amber" else "background-color: white;" for e in series]
    #########-------------------------------------Decalring Function To Highlight Color Column as per Color Coding:Completed-----------------------------------------------###########
    
    
    #####----------------------------------------------Defining a Function that will Evalute RTSLA When Standard SLA Given:Begins----------------------------------------------#######
    
    def evaluatingRTSLA_WhenStandardSLANotNone(df1,location_value,entered_value):
        if entered_value == "Average RT":
            df1.loc[location_value,"Response time difference (when compared to SLA)"] = df1.loc[location_value,"Average response time"] - df1.loc[location_value,"Standard SLA"]
        if entered_value == "75th Percentile RT":
            df1.loc[location_value,"Response time difference (when compared to SLA)"] = df1.loc[location_value,"75%"] - df1.loc[location_value,"Standard SLA"]
        if entered_value == "80th Percentile RT":
            df1.loc[location_value,"Response time difference (when compared to SLA)"] = df1.loc[location_value,"80%"] - df1.loc[location_value,"Standard SLA"]
        if entered_value == "85th Percentile RT":
            df1.loc[location_value,"Response time difference (when compared to SLA)"] = df1.loc[location_value,"85%"] - df1.loc[location_value,"Standard SLA"]
        if entered_value == "90th Percentile RT":
            df1.loc[location_value,"Response time difference (when compared to SLA)"] = df1.loc[location_value,"90%"] - df1.loc[location_value,"Standard SLA"]
        if entered_value == "95th Percentile RT":
            df1.loc[location_value,"Response time difference (when compared to SLA)"] = df1.loc[location_value,"75%"] - df1.loc[location_value,"Standard SLA"]
        return df1
        
    #####----------------------------------------------Defining a Function that will Evalute RTSLA When Standard SLA Given:Ends----------------------------------------------#######
    
    #####--------------------------------------------Defining a Function that will Evalute RTSLA in accordance to User Input:Begins--------------------------------------------#######
    def evaluatingRTSLA_WhenStandardSLA_None(df2,location_value,entered_value):
        if entered_value == "Average RT":
            df2.loc[location_value,"Response time difference (when compared to SLA)"] = df2.loc[location_value,"Average response time"]
        if entered_value == "75th Percentile RT":
            df2.loc[location_value,"Response time difference (when compared to SLA)"] = df2.loc[location_value,"75%"]
        if entered_value == "80th Percentile RT":
            df2.loc[location_value,"Response time difference (when compared to SLA)"] = df2.loc[location_value,"80%"]
        if entered_value == "85th Percentile RT":
            df2.loc[location_value,"Response time difference (when compared to SLA)"] = df2.loc[location_value,"85%"]
        if entered_value == "90th Percentile RT":
            df2.loc[location_value,"Response time difference (when compared to SLA)"] = df2.loc[location_value,"90%"]
        if entered_value == "95th Percentile RT":
            df2.loc[location_value,"Response time difference (when compared to SLA)"] = df2.loc[location_value,"75%"]
        return df2
    #####--------------------------------------------Defining a Function that will Evalute RTSLA in accordance to User Input:Ends----------------------------------------------#######
    
    #####------------------------------------Defining a Function that will Evalute Standard, Baseline and expectedc volume column:Begins---------------------------------------#######
    def evalution_dfTransaction_wise(currentTest_df1, entered_value):
        transactionName_list = list(currentTest_df1["Transaction Name"])
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
                        currentTest_df1.loc[a,"Standard SLA"] = df_table["Standard SLA"][j]
                        currentTest_df1.loc[a,"Expected Volume"] = df_table["Expected Volume"][j]
                        currentTest_df1.loc[a,"Baseline SLA"] = 0
                        updated_currentTest_df1 = evaluatingRTSLA_WhenStandardSLANotNone(currentTest_df1,a,entered_value)
            else:
                currentTest_df1.loc[a,"Standard SLA"] = 0
                currentTest_df1.loc[a,"Expected Volume"] = 0
                currentTest_df1.loc[a,"Baseline SLA"] = 0
                updated_currentTest_df1 = evaluatingRTSLA_WhenStandardSLA_None(currentTest_df1,a,entered_value)
            a +=1
        return updated_currentTest_df1
    #####------------------------------------Defining a Function that will Evalute Standard, Baseline and expectedc volume column:Ends---------------------------------------#######


    #####------------------------------------Defining a Function that will Evalute Standard SLAs uniform to All Transactions as per User Input: Begins------------------------#######
    def evalution_dfSameToAllTransaction(currentTest_df1,entered_value):
                #Assigning Constrainsts to invoke the data of existing list
        transactionName_list = list(currentTest_df1["Transaction Name"])
        a = 0
                #Assigning DataFrame outside the form
        df_table = st.session_state.dropDown_data
        length = len(transactionName_list)
                #To Assign the SLA value to every transaction
        while a<length :
            currentTest_df1.loc[a,"Standard SLA"] = df_table["Standard SLA"][0]
            currentTest_df1.loc[a,"Expected Volume"] = df_table["Expected Volume"][0]
            currentTest_df1.loc[a,"Baseline SLA"] = 0
            updated_currentTest_df1 = evaluatingRTSLA_WhenStandardSLANotNone(currentTest_df1,a,entered_value)
            a +=1
        return updated_currentTest_df1

    #####------------------------------------Defining a Function that will Evalute Standard SLAs uniform to All Transactions as per User Input: Ends------------------------#######
    
    
    #####------------------------------------------------Defining a Function that will predict status of transaction color wise: Begins---------------------------------------#######
    def results(df,flow_type):
        
        csv_bytes = df.to_csv(index=False).encode()
        csv_buffer = BytesIO(csv_bytes)
        files = {'file': ('data.csv',csv_buffer)}
        data = {'Flow_Type': flow_type}
        #response = requests.post(f"{st.session_state.host_url}/predict", files=files,data=data, headers = {'Content-Type': "application/json; charset=utf-8"})
        response = requests.post(f"{st.session_state.host_url}/predict", files=files,data=data)
        #payload = df.to_json(orient = "records")
        #crp.to_encrypted(df, password='mypassword123', path='file.crypt')
        #st.write('file.crypt')
        #dataset = df.to_dict(orient='list')
        #post_data = {'df_in': payload, 'flow_type': flow_type}
        #url = f"{st.session_state.host_url}/predict"
        #print(payload)
        # proxies = {
          # #"http": "http://127.0.0.1:8080",
          # "http": "http://172.29.19.4:8080"
        # }
        #response = requests.post(f"{st.session_state.host_url}/predict?df_in={payload}&df_in={flow_type}", headers = {'Content-Type': "application/json; charset=utf-8"})
        #response = requests.post(url, json=post_data, headers = {'Content-Type': "application/json; charset=utf-8"})
        json_response = response.text
        json_data = json.loads(json_response)
        final_df =json_normalize(json_data)
        return final_df
    #####-------------------------------------------------Defining a Function that will predict status of transaction color wise: Ends-----------------------------------------#######

    def evaluatingStandardSLA_whenNoSLAGUI(currentTest_df1,entered_value):
                #Assigning Constrainsts to invoke the data of existing list
        transactionName_list = list(currentTest_df1["Transaction Name"])
        passed_transaction = list(currentTest_df1["Passed trx"])
        failed_transaction = list(currentTest_df1["Failed trx"])
        total_transaction_count = list(map(add, passed_transaction, failed_transaction))
        a = 0
        length = len(transactionName_list)
                #To Assign the SLA value to every transaction
        while a<length :
            currentTest_df1.loc[a,"Standard SLA"] = 0
            currentTest_df1.loc[a,"Expected Volume"] = total_transaction_count[a]
            currentTest_df1.loc[a,"Baseline SLA"] = 0
            updated_currentTest_df1 = evaluatingRTSLA_WhenStandardSLA_None(currentTest_df1,a,entered_value)
            a +=1
        
        return updated_currentTest_df1
        
    def functionToHoldCompleteRTDataFrame(final_df):
        pass
    
    ###################################################################   Streamlit Code Begins   #################################################################################
   
    #------------------------------------------------------Assigning Processed MDB data to a Variabe ------------------------------------------------------------------------------

    currentTest_df = st.session_state.RT_Sheet
    
    #---------------------------------------------------------------- Asking For the Flow Type ---------------------------------------------------------------------------------
    st.info("Since you have not uploaded previous test results, thus we are considering existing RT as Baselines", icon = "⚠️")
    radio_options1 = ["Select","GUI Flow", "API Flow"]
    flowType_choice  = st.radio(label = "Please choose for Flow Type", options = radio_options1, horizontal = True)
    
    #------------------------------------------- Asking for Standard SLAs and Expected Volume in case of no previous results ------------------------------------------------------
    radio_options = ["Select","Yes", "No"]
    st.header("_Preparing_ _for_ _Response_ _Time_ _Sheet_")
    choice  = st.radio(label = "Have Business NFRs (Standard SLAs and Expected Volume) ? ", options = radio_options, horizontal = True)
    
    #----------------------------------------------------------------- Default Selection -----------------------------------------------------------------------------------------
    if choice == radio_options[0]:
        st.write("Click Yes if you have Standard SLAs Else click No")
    
    #------------------------------------------------ Situation when user enters Standard SLAs : Begins---------------------------------------------------------------------------
    elif choice == radio_options[1]:
        
        currentTest_Selectboxlist = ["Select","Transaction wise","Uniform to All Transactions"]
        currentTest_standadSLADropdown = st.selectbox("Please Select below options to enter NFRs",currentTest_Selectboxlist)
        
        #####   evaluating Standard SLA Transaction Wise
        if currentTest_standadSLADropdown == currentTest_Selectboxlist[1]:
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
            proceed_1 = st.checkbox("I Confirm To Continue")

            if proceed_1:
                currentTest_BaselineSelectboxlist = ["Average RT","75th Percentile RT","80th Percentile RT","85th Percentile RT","90th Percentile RT","95th Percentile RT"]
                currentTest_BaselineSelectboxDropdown = st.selectbox("Since, You don't have any previous records for Baseline. Thus,Please Select from below options As Benchmark",currentTest_BaselineSelectboxlist)
                final_updated_df = evalution_dfTransaction_wise(currentTest_df,currentTest_BaselineSelectboxDropdown)

                submit_1 = st.checkbox("I confirm")
                if submit_1:
                    #update_df = evaluatingFinal_df(final_updated_df,currentTest_BaselineSelectboxDropdown)
                    #update_df = evaluatingBaselineSLA_df(final_updated_df,currentTest_BaselineSelectboxlist,currentTest_BaselineSelectboxDropdown)
                    colored_df = results(final_updated_df,flowType_choice)
                    if currentTest_BaselineSelectboxDropdown == "Entered Standard SLAs":
                        dropList_value = "Standard_SLA"
                    elif currentTest_BaselineSelectboxDropdown == "Average RT":
                        dropList_value = "Average RT"
                    elif currentTest_BaselineSelectboxDropdown == "75th Percentile RT":
                        dropList_value = "75%"
                    elif currentTest_BaselineSelectboxDropdown == "80th Percentile RT":
                        dropList_value = "80%"
                    elif currentTest_BaselineSelectboxDropdown == "85th Percentile RT":
                        dropList_value = "85%"
                    elif currentTest_BaselineSelectboxDropdown == "95th Percentile RT":
                        dropList_value = "95%"
                    else:
                        dropList_value = "95%"
                    drop_list = ['TransactionName','Standard_SLA','Baseline_SLA','Expected_Volume','Passed_trx','Failed_trx','Average response time','Min','Max','RTSLA',"90%",f'{dropList_value}','color','Comments']
                    last_df = colored_df.drop(colored_df.columns.difference(drop_list), axis=1)
                    st.session_state.RT_Sheet = last_df
                    last_df1 = last_df.style.set_properties(**{'background-color': 'black','color': 'yellow'})
                    st.session_state.RT_Sheet = last_df1.apply(highlighter, subset = ["color"], axis = 0)
                    st.dataframe(st.session_state.RT_Sheet)
                    
                    # json_string = last_df.to_json(orient = "records")
                    # st.session_state.JsonResponse_df = requests.post(f"{st.session_state.host_url}/FinalResults?df_jsonString={json_string}", headers = {'Content-Type': "application/json; charset=utf-8"})
                    
                    #st.table(last_df)
                    
        
        #####   evaluating Standard SLA Uniform To All Transaction
        elif currentTest_standadSLADropdown == currentTest_Selectboxlist[2]:
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
            proceed_1 = st.checkbox("I Confirm To Continue")
            if proceed_1:
                
                currentTest_BaselineSelectboxlist = ["Average RT","75th Percentile RT","80th Percentile RT","85th Percentile RT","90th Percentile RT","95th Percentile RT"]
                currentTest_BaselineSelectboxDropdown = st.selectbox("Since, You don't have any previous records for Baseline. Thus,Please Select from below options As Benchmark",currentTest_BaselineSelectboxlist)
                
                final_updated_df = evalution_dfSameToAllTransaction(currentTest_df,currentTest_BaselineSelectboxDropdown)
                submit_1 = st.checkbox("I confirm")
                if submit_1:
                    #update_df = evaluatingBaselineSLA_df(final_updated_df,currentTest_BaselineSelectboxlist,currentTest_BaselineSelectboxDropdown)
                    colored_df = results(final_updated_df,flowType_choice)
                    if currentTest_BaselineSelectboxDropdown == "Entered Standard SLAs":
                        dropList_value = "Standard_SLA"
                    elif currentTest_BaselineSelectboxDropdown == "Average RT":
                        dropList_value = "Average RT"
                    elif currentTest_BaselineSelectboxDropdown == "75th Percentile RT":
                        dropList_value = "75%"
                    elif currentTest_BaselineSelectboxDropdown == "80th Percentile RT":
                        dropList_value = "80%"
                    elif currentTest_BaselineSelectboxDropdown == "85th Percentile RT":
                        dropList_value = "85%"
                    elif currentTest_BaselineSelectboxDropdown == "95th Percentile RT":
                        dropList_value = "95%"
                    else:
                        dropList_value = "95%"
                    drop_list = ['TransactionName','Standard_SLA','Baseline_SLA','Expected_Volume','Passed_trx','Failed_trx','Average response time','Min','Max','RTSLA',"90%",f'{dropList_value}','color','Comments']
                    last_df = colored_df.drop(colored_df.columns.difference(drop_list), axis=1)
                    last_df1 = last_df.style.set_properties(**{'background-color': 'black','color': 'yellow'})
                    st.session_state.RT_Sheet = last_df1.apply(highlighter, subset = ["color"], axis = 0)
                    st.dataframe(st.session_state.RT_Sheet)
                    
                    #json_string = last_df.to_json(orient = "records")
                    #st.session_state.JsonResponse_df = requests.post(f"{st.session_state.host_url}/FinalResults?df_jsonString={json_string}", headers = {'Content-Type': "application/json; charset=utf-8"})
                    #st.table(last_df)


    ###---------------------------When No SLA been Provided-----------------------------
    elif choice == radio_options[2]:
        st.info("As you Don't have Standard SLAs with you, thus we are marking 5Sec for GUI file and 3Sec for API flows", icon = "⚠️")
        
        ### For GUI Flow
        if flowType_choice == radio_options1[1]:
            currentTest_BaselineSelectboxlist = ["Average RT","75th Percentile RT","80th Percentile RT","85th Percentile RT","90th Percentile RT","95th Percentile RT"]
            currentTest_BaselineSelectboxDropdown = st.selectbox("Since, You don't have any previous records for Baseline. Thus,Please Select from below options As Benchmark",currentTest_BaselineSelectboxlist)
            
            final_updated_df = evaluatingStandardSLA_whenNoSLAGUI(currentTest_df,currentTest_BaselineSelectboxDropdown)
            submit_1 = st.checkbox("I confirm")
            if submit_1:
                
                #update_df = evaluatingBaselineSLA_df_WhenNoSLAGiven(final_updated_df,currentTest_BaselineSelectboxlist,currentTest_BaselineSelectboxDropdown)
                colored_df = results(final_updated_df,flowType_choice)
                if currentTest_BaselineSelectboxDropdown == "Entered Standard SLAs":
                    dropList_value = "Standard_SLA"
                elif currentTest_BaselineSelectboxDropdown == "Average RT":
                    dropList_value = "Average RT"
                elif currentTest_BaselineSelectboxDropdown == "75th Percentile RT":
                    dropList_value = "75%"
                elif currentTest_BaselineSelectboxDropdown == "80th Percentile RT":
                    dropList_value = "80%"
                elif currentTest_BaselineSelectboxDropdown == "85th Percentile RT":
                    dropList_value = "85%"
                elif currentTest_BaselineSelectboxDropdown == "95th Percentile RT":
                    dropList_value = "95%"
                else:
                    dropList_value = "95%"
                drop_list = ['TransactionName','Standard_SLA','Baseline_SLA','Expected_Volume','Passed_trx','Failed_trx','Average response time','Min','Max','RTSLA',"90%",f'{dropList_value}','color','Comments']
                last_df = colored_df.drop(colored_df.columns.difference(drop_list), axis=1)
                last_df1 = last_df.style.set_properties(**{'background-color': 'black','color': 'yellow'})
                st.session_state.RT_Sheet = last_df1.apply(highlighter, subset = ["color"], axis = 0)
                st.dataframe(st.session_state.RT_Sheet)
                
                #st.session_state.JsonResponse_df = requests.post(f"{st.session_state.host_url}/FinalResults?df_jsonString={json_string}", headers = {'Content-Type': "application/json; charset=utf-8"})
                    
                
        ### For API Flow
        elif flowType_choice == radio_options1[2]:
            currentTest_BaselineSelectboxlist = ["Average RT","75th Percentile RT","80th Percentile RT","85th Percentile RT","90th Percentile RT","95th Percentile RT"]
            currentTest_BaselineSelectboxDropdown = st.selectbox("Since, You don't have any previous records for Baseline. Thus,Please Select from below options As Benchmark",currentTest_BaselineSelectboxlist)
            
            final_updated_df = evaluatingStandardSLA_whenNoSLAGUI(currentTest_df,currentTest_BaselineSelectboxDropdown)
            submit_1 = st.checkbox("I confirm")
            if submit_1:
                #update_df = evaluatingBaselineSLA_df_WhenNoSLAGiven(final_updated_df,currentTest_BaselineSelectboxlist,currentTest_BaselineSelectboxDropdown)
                colored_df = results(final_updated_df,flowType_choice)
                if currentTest_BaselineSelectboxDropdown == "Entered Standard SLAs":
                    dropList_value = "Standard_SLA"
                elif currentTest_BaselineSelectboxDropdown == "Average RT":
                    dropList_value = "Average RT"
                elif currentTest_BaselineSelectboxDropdown == "75th Percentile RT":
                    dropList_value = "75%"
                elif currentTest_BaselineSelectboxDropdown == "80th Percentile RT":
                    dropList_value = "80%"
                elif currentTest_BaselineSelectboxDropdown == "85th Percentile RT":
                    dropList_value = "85%"
                elif currentTest_BaselineSelectboxDropdown == "95th Percentile RT":
                    dropList_value = "95%"
                else:
                    dropList_value = "95%"
                drop_list = ['TransactionName','Standard_SLA','Baseline_SLA','Expected_Volume','Passed_trx','Failed_trx','Average response time','Min','Max','RTSLA',"90%",f'{dropList_value}','color','Comments']
                last_df = colored_df.drop(colored_df.columns.difference(drop_list), axis=1)
                last_df1 = last_df.style.set_properties(**{'background-color': 'black','color': 'yellow'})
                st.session_state.RT_Sheet = last_df1.apply(highlighter, subset = ["color"], axis = 0)
                st.dataframe(st.session_state.RT_Sheet)
                # json_string = last_df.to_json(orient = "records")
                # st.session_state.JsonResponse_df = requests.post(f"{st.session_state.host_url}/FinalResults?df_jsonString={json_string}", headers = {'Content-Type': "application/json; charset=utf-8"})
                    

    ###################################################################   Streamlit Code Ends   #####################################################################################
#####____________________________________________________________________________Main Function for Previous Test Records:Completed_____________________________________________#######
                
