import streamlit as st
import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker
import datetime
from prophet.plot import plot_plotly, plot_components_plotly
import plotly.graph_objects as go
from pathlib import Path
import os
import time

st.set_page_config(layout="wide")
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
if 'key' in st.session_state:
    st.session_state['productSelection'] = ''
    st.session_state['resourceSelection'] = ''
    st.session_state['forecastSelection'] = ''
    st.session_state['spSelection']
if 'show_advanced' not in st.session_state:
    st.session_state['show_advanced'] = False
def toggle_advanced():
    st.session_state['show_advanced'] = not st.session_state['show_advanced']
# Widget Function Starts 
def productSelection():
    left,  right = st.columns(2)
    st.session_state['productSelection'] = left.selectbox(
        "Select Product ",
        ("CCH Axcess", "Axcess Workflow", "Client Collaboration"),
        index=None,
        placeholder="Select Product...",
        on_change=toggle_advanced,
    )
    st.session_state['resourceSelection'] = right.radio(
        "Select the Field to Analyis",
        ("DMV Stats", "Database Resource Utilization", "Logs Analysis"),
        index=None,
        on_change=toggle_advanced,
    )
    st.markdown(
    '''
        <!DOCTYPE html>
        <html>
            <head>
                <br>
                <br>
                <br>
                <br>
            </head>
        </html>
    ''',
    unsafe_allow_html = True
    )
    return True
# Widget Function Ends
# DMV selection Starts 
def DMVSelection():
    left, middle, right = st.columns(3)
    if st.session_state['resourceSelection'] == "DMV Stats":
        st.session_state['forecastSelection'] = middle.radio(
            "# Pick What you'd like to Forecast",
            ("AvgCPU", "CPUPerHr", "MaxCPU","CallPerHr"),
            index=None,
            on_change=toggle_advanced,
            horizontal=True
        )
        if st.session_state['forecastSelection']:
            forecast()
    return True
# DMV Selection Ends
# File Path Function Starts
def selectFilePath():
    spNameList = []
    # Enhance the path for Other Products
    if st.session_state['productSelection'] == 'Axcess Workflow':
        folder_path = Path(r"C:\Users\Kapil.Sharma1\Desktop\CodeGame\Files\XCM")  # Replace with the actual path
        try:
            file_names = [item.name for item in folder_path.iterdir() if item.is_file()]
            for file_name in file_names:
                name, ext = os.path.splitext(file_name)
                spNameList.append(name)
        except FileNotFoundError:
            st.write(f"Error: Folder not found at {folder_path}")
        except OSError as e:
            st.write(f"Error accessing folder: {e}")
    st.session_state['spSelection'] = st.selectbox(
        "Select Your Store Procedure ",
        spNameList,
        index=None,
        placeholder="Store Procedure Name...",
        on_change=toggle_advanced,
    )
    if st.session_state['spSelection'] is not None:
        return rf'Files\XCM\{st.session_state['spSelection']}.xlsx'
# File Path Function Ends 
# Function Declartion Starts
def forecast():
    path = selectFilePath()
    while(path is None):
        time.sleep(2)
    future = pd.DataFrame()
    # Step 1: Load Excel
    df = pd.read_excel(path)
    spName = df['Sp_Name'].unique()
    # Step 2: Prepare Data (Assuming your data has 'Date' and 'StatValue' columns)
        # Convert time columns
    df['PeriodStart'] = pd.to_datetime(df['PeriodStart'])
    df['PeriodEnd'] = pd.to_datetime(df['PeriodEnd'])
    # Option B (better for longer ranges): Use midpoint time
    # df['ds'] = df['PeriodStart'] + (df['PeriodEnd'] - df['PeriodStart']) / 2
    df['ds'] = df['PeriodEnd']
    if(st.session_state['forecastSelection'] == "AvgCPU"):
        # Choose your metric to forecast (e.g., LogicalReads)
        df['y'] = df['AvgCPU']
        nameString = "Avg CPU"
    
    elif(st.session_state['forecastSelection'] == "CPUPerHr"):
        # Choose your metric to forecast (e.g., LogicalReads)
        df['y'] = df['CPUPerHr']
        nameString = "CPU Per Hour Consumption"
    
    elif(st.session_state['forecastSelection'] == "MaxCPU"):
        # Choose your metric to forecast (e.g., LogicalReads)
        df['y'] = df['MaxCPU']
        nameString = "Max CPU Consumption"
    elif(st.session_state['forecastSelection'] == "CallPerHr"):
        # Choose your metric to forecast (e.g., LogicalReads)
        df['y'] = df['CallPerHr']
        nameString = "Calls Per Hour Consumption"
    # Drop extra columns
    df = df[['ds', 'y']]
    # Taking Log to eliminate the probability of having negative Forecast
    df['y'] = np.log1p(df['y'])
    # Step 3: Initialize and Fit Model
    model = Prophet()
    model.fit(df)
    #Pick Frequency 
    option = st.selectbox(
    "How would you like to Forecast?",
    ('Custom Date', 'Day', 'Week', 'Month', 'Quarter', 'Year', 'Hour'),
    index=None,
    placeholder="Select Forecast method...",
    )
    if option == 'Custom Date': 
        today = datetime.datetime.now()
        year_range = today.year + 5
        next_year = today.year + 1
        jan_1 = datetime.date(today.year, today.month, today.day)
        dec_31 = datetime.date(year_range, 12, 31)
        d = st.date_input(
            "Select your date range",
            # (jan_1, datetime.date(next_year, today.month, today.day)),
            (),
            jan_1,
            dec_31,
            format="MM.DD.YYYY",
            )
        if len(d)>0:
            # Create the dynamic future DataFrame
            future_df = pd.date_range(start=d[0], end=d[1], freq='D')
            future = pd.DataFrame({'ds': future_df})
    elif option == 'Day':
        # Step 4: Make Future DataFrame
        future = model.make_future_dataframe(periods=480,freq='h')  # or 'D' for daily
    
    elif option == 'Week':
        # Step 4: Make Future DataFrame
        future = model.make_future_dataframe(periods=20,freq='W-FRI')  # or 'W-FRI' for Week ending with Friday
    elif option == 'Month':
        # Step 4: Make Future DataFrame
        future = model.make_future_dataframe(periods=6,freq='ME')
    elif option == 'Quarter':
        # Step 4: Make Future DataFrame
        future = model.make_future_dataframe(periods=5,freq='QE')
    elif option == 'Year':
        # Step 4: Make Future DataFrame
        future = model.make_future_dataframe(periods=17520,freq='h')
    elif option == 'Hour':
        # Step 4: Make Future DataFrame
        future = model.make_future_dataframe(periods=24,freq='h')
    
    if not future.empty:
        forecast = model.predict(future)
        # Using exponent to return the original value
        forecast['yhat'] = np.expm1(forecast['yhat'])
        forecast['yhat_lower'] = np.expm1(forecast['yhat_lower'])
        forecast['yhat_upper'] = np.expm1(forecast['yhat_upper'])
        df['y'] = np.expm1(df['y'])
        
        # Step 5: Plot the forecast
        # Plot the forecast
        # fig, ax = plt.subplots(figsize=(10,5))
        
        # Get the Matplotlib figure from Prophet's plot method
        fig = model.plot(forecast)
        ax = fig.gca() # Get the current axes
        # Determine the range of your forecasted 'yhat' values
        forecast_min_y = forecast['yhat'].min()
        forecast_max_y = forecast['yhat'].max()
        # Add a small buffer for better visualization
        y_lower_limit = forecast_min_y - 0.1 * abs(forecast_min_y)
        y_upper_limit = forecast_max_y + 0.1 * abs(forecast_max_y)
        # Set the y-axis limits
        ax.set_ylim(y_lower_limit, y_upper_limit)
        # Get the lines plotted by Prophet
        lines = ax.get_lines()
        # ax.plot(df['ds'], df['y'], 'k.', label='Historical Data')
        future_dates = forecast[forecast['ds'] > df['ds'].max()]
        predicted_line, = ax.plot(future_dates['ds'], future_dates['yhat'], 'r-', label='Predited Data')
        handles, labels = ax.get_legend_handles_labels()
        # Create a legend with custom labels for the lines
        # Assuming the first line is the forecast and the points are the actual data
        legend_elements = [
                        plt.Line2D([0], [0], marker='.', color='blue', linestyle='', label='Actual Data'),
                        predicted_line,  # Use the handle of the predicted linepredicted_line,
                        ax.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], color='lightblue', alpha=0.2, label='Uncertainty')]
        # ax.legend(handles=legend_elements,loc='upper left') # You can adjust the 'loc' parameter
        # Get the handles and labels of the plot elements
        
        # Specify the color for each label
        label_colors = ['blue', 'red', 'black']  # Corresponding to Forecast, Actual Data, Adjusted Forecast
        # Create the legend with custom font color
        legend = ax.legend(handles=legend_elements, labelcolor=label_colors, loc='upper left', prop={'size': 16})
        # # Plot past data
        # # ax.scatter(df['ds'], df['y'], color='black', label='Past Data')
        # ax.bar(df['ds'], df['y'], color='black', label='Past Data')
        # # Plot future predictions
        # future_dates = forecast[forecast['ds'] > df['ds'].max()]
        # # ax.scatter(future_dates['ds'], future_dates['yhat'], color='blue', label='Future Predictions')
        # ax.bar(future_dates['ds'], future_dates['yhat'], color='blue', label='Future Predictions')
        # plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        # y_min = 1
        # ax.set_ylim(bottom=y_min)
        # # ax.set_yscale('symlog')
        # #ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{:.0f}'.format(x)))
        # 4. Manually build Plotly figure
        
        plt.title(f'{nameString} for SP {spName[0]}',color='white', fontsize=16)
        #st.pyplot(fig)
        st.plotly_chart(fig)
    
# Function Declartion Ends
st.markdown(
'''
    <!DOCTYPE html>
    <html>
        <head>
            <h1 style="text-align: center">
                Future is Right Here !!
            </h1>
            <br>
            <br>
        </head>
    </html>
''',
unsafe_allow_html = True
)
productSelection()
DMVSelection()
left, middle, right = st.columns(3)
# if left.button("Plain button", use_container_width=True):
#     left.markdown("You clicked the plain button.")
# if middle.button("Emoji button", icon="😃", use_container_width=True):
#     middle.markdown("You clicked the emoji button.")
if right.button("Back", icon=":material/arrow_back_ios:", use_container_width=True):
    st.switch_page("App.py")
