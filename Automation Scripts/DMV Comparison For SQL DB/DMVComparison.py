import pandas as pd
from azure.storage.blob import BlobServiceClient
from datetime import datetime, timedelta, timezone, date
from dateutil.relativedelta import relativedelta
import io
import concurrent.futures
import warnings
import ast # For safely evaluating string representations of tuples (if needed for column renaming)
from pathlib import Path

warnings.filterwarnings("ignore")

# --- Configuration ---
connection_string = "DefaultEndpointsProtocol=https;AccountName={AzureAccountName};AccountKey={AzureAccountKey};EndpointSuffix=core.windows.net"
container_name = "sql-xevents"
# For LT1
prefix = "TestDMV_tcp:zuscultclbsql001"
# For LT2
# prefix = "TestDMV_tcp:zuse2ltclbsql001"
output_path = Path('C:/Users/Kapil.Sharma1/Desktop/DMVAutomation/')

# --- Global/Reused Client (initialized once) ---
global_blob_service_client = None
global_container_client = None

# --- Helper Functions ---

# calculating % diff
def calculate_percentange_difference_forAchievedDuration(baseline, regression):
    # baseline and regression are pandas Series
    # Handle division by zero and None/NaN values gracefully
    result = ((regression - baseline) / baseline) * 100
    # Replace inf/-inf with 0 if baseline is 0 and regression is 0, else inf
    result = result.mask((baseline == 0) & (regression == 0), 0.0)
    result = result.replace([float('inf'), -float('inf')], float('inf')) # Keep inf for non-zero regression / 0 baseline
    return result.round(2)

# calculating % diff
def calculate_percentange_difference_forAchievedCount(baseline, regression):
    # baseline and regression are pandas Series
    # Handle division by zero and None/NaN values gracefully
    result = ((baseline - regression) / baseline) * 100
    # Replace inf/-inf with 0 if baseline is 0 and regression is 0, else 0.0
    result = result.mask((baseline == 0) & (regression == 0), 0.0)
    result = result.replace([float('inf'), -float('inf')], float('inf')) # Keep inf for non-zero regression / 0 baseline
    return result.round(2)

# --- Styling Logic ---
def highlight_diff_forAchievedDuration(s):
    # s is a Series (column) of the diff percentages
    is_red = (s > 10)
    is_green = (s < 1)
    is_amber = (s >= 1) & (s <= 10)

    # Return a Series of CSS styles
    return [
        'background-color: #FFC7CE' if r else
        'background-color: #C6EFCE' if g else
        'background-color: #FFC000' if a else
        '' # Default no background
        for r, g, a in zip(is_red, is_green, is_amber)
    ]

def highlight_diff_forAchievedCount(s):
    # s is a Series (column) of the diff percentages
    is_red = (s < 0)
    is_green = (s > 10)
    is_amber = (s >= 1) & (s <= 10)

    # Return a Series of CSS styles
    return [
        'background-color: #FFC7CE' if r else
        'background-color: #C6EFCE' if g else
        'background-color: #FFC000' if a else
        '' # Default no background
        for r, g, a in zip(is_red, is_green, is_amber)
    ]
# --- Core Blob Operations ---
def list_blobs_past_month(container_client, prefix=None, months_ago=2):
    """
    Lists blob names in the specified container that were last modified in the past X months.
    Uses an existing ContainerClient.
    """
    if not container_client:
        print("Container client not initialized. Cannot list blobs.")
        return []

    try:
        now_naive = datetime.utcnow()
        now = now_naive.replace(tzinfo=timezone.utc)
        target_date_naive = now_naive - relativedelta(months=months_ago)
        target_date = target_date_naive.replace(tzinfo=timezone.utc)

        past_month_blobs = []
        # Use a generator for large lists for better memory management
        blob_generator = container_client.list_blobs(name_starts_with=prefix)

        for blob in blob_generator:
            if blob.last_modified is not None and target_date <= blob.last_modified < now:
                past_month_blobs.append(blob.name)

        return past_month_blobs

    except Exception as e:
        print(f"An error occurred while listing blobs: {e}")
        return []

def download_and_read_blob(blob_name, blob_service_client, container_name):
    """
    Downloads the content of a single blob and reads it into a pandas DataFrame (assuming .xlsx).
    Accepts an already initialized BlobServiceClient.
    """
    try:
        blob_client = blob_service_client.get_blob_client(container_name, blob_name)
        download_stream = blob_client.download_blob()
        blob_data = download_stream.readall()
        df = pd.read_excel(io.BytesIO(blob_data), engine='openpyxl')
        return blob_name, df
    except Exception as e:
        print(f"Error processing blob '{blob_name}': {e}")
        return blob_name, None

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting script execution...")

    # 1. Initialize global clients once
    try:
        global_blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        global_container_client = global_blob_service_client.get_container_client(container_name)
        print("Blob service and container clients initialized.")
    except Exception as e:
        print(f"FATAL: Error initializing BlobServiceClient or ContainerClient: {e}")
        exit(1) # Exit if we can't connect to blob storage

    # 2. List blobs (using the global container client)
    # Using 'months_ago=2' as per your code's relativedelta
    past_month_files = list_blobs_past_month(global_container_client, prefix, months_ago=2)

    if not past_month_files:
        print(f"No blobs found in container '{container_name}' modified in the past 2 months (starting with '{prefix if prefix else 'any'}'). Exiting.")
        exit(0)

    print(f"Found {len(past_month_files)} relevant blobs. Downloading and processing...")

    # 3. Parallel Download and DataFrame Creation
    # Use ThreadPoolExecutor for concurrent download and processing
    # Adjust max_workers based on your network bandwidth and CPU cores.
    # A common starting point for I/O bound tasks is (number of cores * 2) + 1, or higher.
    # For a machine with decent network, 10-20 can be a good range.
    all_dataframes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Map the download_and_read_blob function to each file name
        # We pass the global client objects to the worker function
        future_to_blob_name = {
            executor.submit(download_and_read_blob, name, global_blob_service_client, container_name): name
            for name in past_month_files
        }

        for future in concurrent.futures.as_completed(future_to_blob_name):
            blob_name, df = future.result()
            if df is not None:
                all_dataframes.append(df)
                print(f"Processed '{blob_name}' successfully.")
            else:
                print(f"Skipping '{blob_name}' due to processing error.")

    if not all_dataframes:
        print("No DataFrames were successfully created from the blobs. Exiting.")
        exit(0)

    # 4. Concatenate all DataFrames once
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    print(f"Combined {len(all_dataframes)} DataFrames into a single DataFrame with {len(combined_df)} rows.")

    overallRunIds = sorted(combined_df['RunID'].unique().tolist())
    if not overallRunIds:
        print("No 'RunID's found in the combined DataFrame. Exiting.")
        exit(0)

    # --- User Input ---
    # Using a loop for robust input handling
    baseline_TestId = None
    while baseline_TestId is None:
        try:
            baseline_input = input(f"Enter the Baseline Run Id from {overallRunIds}: ")
            baseline_TestId = int(baseline_input)
            if baseline_TestId not in overallRunIds:
                print(f"Error: {baseline_TestId} is not a valid Run ID. Please try again.")
                baseline_TestId = None
        except ValueError:
            print("Invalid input. Please enter a number.")

    regression_TestValues = []
    available_regression_ids = [x for x in overallRunIds if x != baseline_TestId]
    if not available_regression_ids:
        print("No available Run IDs for regression testing. Exiting.")
        exit(0)

    while not regression_TestValues:
        regression_TestId_str = input(f"Enter the Regression Run Id or Ids from {available_regression_ids.sort()} separated by commas: ")
        try:
            temp_values = [int(x.strip()) for x in regression_TestId_str.split(',')]
            valid_values = [val for val in temp_values if val in available_regression_ids]
            if valid_values:
                regression_TestValues = valid_values
            else:
                print("No valid Regression IDs entered. Please try again.")
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas.")

    # --- DataFrame Preparation and Calculations ---
    print("Preparing data for comparison...")
    mainHeader = ['Count', 'Reads_AVG', 'Writes_AVG', 'Duration_AVG', 'CPU_AVG', 'TotalAvgCPU', 'Database_name', 'Schema_Name']
    
    # Pre-filter baseline and regression data once for efficiency
    baseline_df_raw = combined_df[combined_df['RunID'] == baseline_TestId].copy()
    baseline_df_unique = baseline_df_raw.drop_duplicates(subset='sp_Name', keep='first').set_index('sp_Name')

    # Get unique SP_Names from baseline to ensure consistent row order
    # This also helps if some SPs are missing in regression runs.
    sp_names_for_report = baseline_df_unique.index.tolist()

    # Create MultiIndex for the result DataFrame
    # Start with SP_Name first, then add the dynamic columns
    columns_list = [('SP_Name', '')]
    for col in mainHeader:
        columns_list.append((col, 'Baseline'))
        for run_id in regression_TestValues:
            columns_list.append((col, f'Regression#{run_id}'))
            columns_list.append((col, f'Baseline_vs_Regression#{run_id}_%diff')) # Add diff column here for correct order

    resulted_df = pd.DataFrame(index=sp_names_for_report, columns=pd.MultiIndex.from_tuples(columns_list))
    resulted_df[('SP_Name', '')] = resulted_df.index # Populate SP_Name column

    # Populate Baseline data
    for col in mainHeader:
        resulted_df[(col, 'Baseline')] = resulted_df.index.map(baseline_df_unique[col])

    # Populate Regression and calculate differences
    calculated_header = ['Count', 'Reads_AVG', 'Writes_AVG', 'Duration_AVG', 'CPU_AVG', 'TotalAvgCPU']
    for run_id in regression_TestValues:
        source_df_raw = combined_df[combined_df['RunID'] == run_id].copy()
        source_df_unique = source_df_raw.drop_duplicates(subset='sp_Name', keep='first').set_index('sp_Name')

        for col in mainHeader:
            # Populate Regression data
            resulted_df[(col, f'Regression#{run_id}')] = resulted_df.index.map(source_df_unique[col])

            # Calculate and insert diff
            if col in calculated_header: # Only calculate diff for these columns
                baselineValues = resulted_df[(col, 'Baseline')]
                regressionValues = resulted_df[(col, f'Regression#{run_id}')]
                diff_col = (col, f'Baseline_vs_Regression#{run_id}_%diff')

                if col in ['Count', 'Reads_AVG', 'Writes_AVG']:
                    resulted_df[diff_col] = calculate_percentange_difference_forAchievedCount(baselineValues, regressionValues)
                else:
                    resulted_df[diff_col] = calculate_percentange_difference_forAchievedDuration(baselineValues, regressionValues)
    
    # Reset index to make 'SP_Name' a regular column for styling and output
    resulted_df = resulted_df.reset_index(drop=True)

    # --- Apply Styling ---
    print("Applying styling...")
    styled_df = resulted_df.style

    for col_param in calculated_header:
        if col_param in ['Count', 'Reads_AVG', 'Writes_AVG']:
            for run_id in regression_TestValues:
                diff_col_name = (col_param, f'Baseline_vs_Regression#{run_id}_%diff')
                if diff_col_name in resulted_df.columns:
                    styled_df = styled_df.apply(highlight_diff_forAchievedCount, subset=[diff_col_name])
        else:
            for run_id in regression_TestValues:
                diff_col_name = (col_param, f'Baseline_vs_Regression#{run_id}_%diff')
                if diff_col_name in resulted_df.columns:
                    styled_df = styled_df.apply(highlight_diff_forAchievedDuration, subset=[diff_col_name])
    # -- Compute SPs which are there in regression but not in baseline
    baseline_sps = list(resulted_df['SP_Name'].unique())
    missing_sps_dict = {}
    dfs = {}
    for run_id in regression_TestValues:
        regression_sps = list(combined_df[combined_df['RunID'] == run_id]['sp_Name'].unique())
        missing = [item for item in regression_sps if item not in baseline_sps] #baseline_sps - regression_sps
        if missing:
            missing_sps_dict[f'Regression#{run_id}'] = list(missing)
    regression_df_raw = combined_df[combined_df['RunID'].isin(regression_TestValues)].copy()
    regression_df_unique = regression_df_raw.drop_duplicates(subset='sp_Name', keep='first').set_index('sp_Name')
    columns = ['SP_Name','Count', 'Reads_AVG', 'Writes_AVG', 'Duration_AVG', 'CPU_AVG', 'TotalAvgCPU','Database_name','Schema_Name']
    for i in range(len(missing_sps_dict.keys())):
        dfs[f'df_{i}'] = pd.DataFrame(columns = columns)
        dfs[f'df_{i}']['SP_Name'] = missing_sps_dict.get(list(missing_sps_dict.keys())[i])
        dfs[f'df_{i}'] = dfs[f'df_{i}'].set_index('SP_Name')
        for col in columns[1:]:
            dfs[f'df_{i}'][col] = dfs[f'df_{i}'].index.map(regression_df_unique[col])
    
    # --- Save Output ---
    output_filename = output_path / f"DMVComparison_{date.today().strftime('%d_%m_%y')}.xlsx"
    # styled_df.to_excel(output_filename, index=False)
    with pd.ExcelWriter(output_filename) as writer:
        styled_df.to_excel(writer, sheet_name='DMVComparisonWithBaseline')
        for i in range(len(missing_sps_dict.keys())):
            dfs[f'df_{i}'].to_excel(writer, sheet_name=f'{list(missing_sps_dict.keys())[i]}')
    print(f"Excel created at: {output_filename}")
    print("Script finished.")
