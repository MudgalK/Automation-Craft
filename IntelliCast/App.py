import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
#----------------------------------------------------------------------------------------------------------------------------------------------------------------
# TO Write a Testing Objective::


st.set_page_config(layout="wide")
# vars = ['file1', 'Exposition', 'Features']
# for _ in vars:
#     if _ not in st.session_state:
#         st.session_state[_] = ''
#         st.session_state["host_url"] = r'http://127.0.0.1:8000'
#         st.session_state["session_state_variable"] = 0
        
# image_path = r"C:\Users\SharmaK21\OneDrive - Vodafone Group\Desktop\Practice\Experiment\Images"
# # Sidebar Widgets
# # st.sidebar.markdown('# Streamlit')
# # sidebar_pages = st.sidebar.radio('Menu', ['Page 1', 'Page 2', 'Page 3'])
# image = Image.open(f'{image_path}\\icon_Logo.jpg')
# st.image(image, caption=None, width=None, use_column_width="auto", clamp=False, channels="RGB", output_format="auto")

selected = option_menu(
    menu_title = None,
    options =["Home","Analyze","Exposition","Features"],
    icons =["house","magic","easel","tag-fill"],
    menu_icon = "cast",
    default_index = 0,
    orientation= "horizontal",
    styles={
        "icon": {"color": "orange", "font-size": "25px"}, 
        "nav-link": {"font-size": "20px", "text-align": "left", "margin":"0px", "--hover-color": "#73008c"},
        "nav-link-selected": {"background-color": "green"},
    }
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
    st.markdown(
    """
    <!DOCTYPE html>
    <html>
    <head>
        <h1 style="text-align: center">
            Welcome To IntelliCast - Predictive production analytics
        </h1>
    </head>
    <body>
        <br>
        <h3>
            IntelliCast helps you to Visualize the Intelligence Forecasting of Production Stats.
        </h3>
        <br>
        <h5 style="margin-left: 2em"><b>Select Exposition Tile Placed at the TOP ☝️</b> to see some examples of what can be done!</h5>
        <p style="text-align: left">    
            <ul style="list-style-type:circle ; margin-left: 6em ; font-size: 1.2em">
                <li>Utilize AI and ML methodologies to predict future trends</li>
                <li>Allows teams to make necessary infrastructure and code adjustments, preventing production issues and enhancing operational efficiency</li>
            </ul>
            <h4 style="margin-left: 2em">What's Holding us Back?</h4>
            <ul style="list-style-type:disc ; margin-left: 6em; font-size: 1.2em">
                <li>Can’t proactively scale resources, leading to performance bottlenecks or outages during traffic spikes.</li>
                <li>Overprovision or underutilize infrastructure, wasting cloud or server costs.</li>
                <li>Fail to plan infrastructure or staffing needs if future load is unknown.</li>
            </ul>
            <h4 style="margin-left: 2em">What makes it different from others</h4>
            <ul style="list-style-type:square ; margin-left: 6em; font-size: 1.2em">
                <li>Able to forecast individual SPs</li>
                <li>Flexibility During Deployment</li>
                <li>In-house Dashboard</li>
            </ul>  
        </p>
    </body>
    </html>       
    """,
    unsafe_allow_html = True
    )
# Page 2
def Analyse():
    st.switch_page("Pages/Analyse.py")
def features():
   st.write("Code to be inserted for Upcoming Feature")        
# Page 3
def Exposition():
    st.switch_page("Pages/Exposition.py")
    
# Navigate through pages
if selected == 'Home':
    Home()
elif selected == 'Analyze':
    Analyse()
elif selected == 'Features':
    features()
else:
    Exposition()
