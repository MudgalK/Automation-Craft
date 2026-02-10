import streamlit as st
import requests 
from pathlib import Path
from zipfile import ZipFile
import pandas as pd
from pandas import json_normalize
import json
from operator import add
from streamlit_option_menu import option_menu
from streamlit_extras.switch_page_button import switch_page
from current_test_v1 import working_with_currentTestData
from previous_test_v1 import working_with_previousTestData
from PIL import Image

##Declaring Constraints
vars = ['previous', 'current']
#st.set_page_config(layout="wide")
st.markdown(
    f'''
        <style>
        .stApp{{
            background: linear-gradient(150deg,#ab8fd7 10%, #441b6f 90%);
            background-attachment: fixed;
            height: 100%;
            background-size: cover
        }}
        </style>
    ''',
    unsafe_allow_html = True)
    
for _ in vars:
    if _ not in st.session_state:
        st.session_state[_] = ''

image_path = r"C:\Users\SharmaK21\OneDrive - Vodafone Group\Desktop\Practice\Experiment\Images"



    
selected_1 = option_menu(
    menu_title = None,
    options =["Select","Have Previous results to compare","Continue With Current Data"],
    icons =["signpost","grip-vertical","grip-vertical"],
    menu_icon = "cast",
    default_index = 0,
    orientation= "horizontal",
    styles={
        #"container": {"padding": "0!important", "background-color": "#fafafa"},
        #"icon": {"color": "orange", "font-size": "25px"},
        "nav-link": {"font-size": "11px", "text-align": "left"},
        }
)


def working_with_current_test():
    working_with_currentTestData()

def compare_with_previous_results():
    working_with_previousTestData()



if selected_1 == "Have Previous results to compare":
    compare_with_previous_results()
    
elif selected_1 == 'Continue With Current Data':
    working_with_current_test()
else:
    st.write(f"You have now uploaded {st.session_state.file1.name} file.\n Below is the tabulate data for Response Time for uploaded file")
    if st.session_state.session_state_variable == 0:
        st.dataframe(st.session_state.RT_Sheet.style.set_properties(**{'background-color': 'black','color': 'yellow'}))
        st.session_state.session_state_variable +=1
    else:
        st.dataframe(st.session_state.RT_Sheet.set_properties(**{'background-color': 'black','color': 'yellow'}))
        
    st.write("Please select from above ☝️ Tiles to continue.")
    st.markdown(
    '''
    - If this is a regression test and you have previous records to compare, then click **Have Previous results to compare** tile to proceed.
    - If this is a progression test and don't have any past data to compare with, then click **Continue With Current Data** 
    
    '''
    )

    
    
# else:
    # working_with_previous_test()
#"nav-link-selected": {"background-color": "crimson"},
#"nav-link": {"font-size": "11px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
