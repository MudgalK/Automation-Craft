import streamlit as st
import base64
import warnings
warnings.filterwarnings("ignore")
st.set_page_config(layout="wide")
file_ = open("Images\Analysis.gif", "rb")
contents = file_.read()
data_url = base64.b64encode(contents).decode("utf-8")
file_.close()
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
st.markdown(
    f"""
    <style>
        .center {{
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 50%;
        }}
    </style>
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="Styles\styles.css">
        <h1>
            Fundamental concepts
        </h1>
        <p style="text-align: Left">
            Are you new to IntelliCast and want the grand tour? If so, you're in the right place! 
            <br>
            <br>
            This Get Started guide explains how IntelliCast works and can enable product teams to make necessary infrastructure and code adjustments, preventing production issues and enhancing operational efficiency.
        </p>
    </head>
    <br>
    <br>
    <body>
        <p>
            Working with IntelliCast is simple. First you need to Click on Analyze Tab as shown below or click <a href="/Analyse">Analyse</a>
            <br>
            <br>
            <img src="data:image/gif;base64,{data_url}" alt="Analyis" class="center">
            <br>
            As soon as you're done with steps as shown above, a IntelliCast welcomes you in the world where you can see the future Right Now !!. The app is your own Customizable Workspace, where you can  arrange, modify, or create data that suit your needs.
        </p>
    </body>
    </html>      
    """,
    unsafe_allow_html = True
    )
left, middle, right = st.columns(3)
# if left.button("Plain button", use_container_width=True):
#     left.markdown("You clicked the plain button.")
# if middle.button("Emoji button", icon="😃", use_container_width=True):
#     middle.markdown("You clicked the emoji button.")
if right.button("Back", icon=":material/arrow_back_ios:", use_container_width=True):
    st.switch_page("App.py")
