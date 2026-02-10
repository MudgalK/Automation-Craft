import zipfile
import sqlite3
import pandas as pd
import re
import os
import tempfile

# Function to extract status code from Message_String
def extract_status_code(msg):
    # Look for HTTP Status-Code=XXX or (XXX ...) or Error -XXXXX: HTTP Status-Code=XXX
    match = re.search(r'HTTP Status-Code=(\d{3})', msg)
    if match:
        return match.group(1)
    match = re.search(r'\((\d{3}) [^\)]*\)', msg)
    
    if match:
        return match.group(1)
    match = re.search(r'(\d{3}) (Internal Server Error|Bad Request|Unauthorized|)', msg)
    if match:
        return match.group(1)
    return 'Other'

def extract_url(msg):
    # Extract URL between for " and next "
    match = re.search(r'for\s+"([^"]+)"', msg)
    if match:
        return match.group(1)
    # Sometimes it's after Request "
    match = re.search(r'Request\s+"([^"]+)"', msg)
    if match:
        return match.group(1)
    return None

def automate_flow(zip_path):
    # 1. Unzip to a temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)
        # 2. Find sqliteDb.db
        db_path = None
        for root, dirs, files in os.walk(tmpdir):
            for file in files:
                if file.lower().endswith('.db'):
                    db_path = os.path.join(root, file)
                    break
        if not db_path:
            raise FileNotFoundError("sqliteDb.db not found in the zip file.")

        # 3. Connect and run query
        conn = sqlite3.connect(db_path)
        query = """
        SELECT e.Message_ID, e.Message_String, s.Script_Name
        FROM ErrorMessages e
        JOIN Main m ON e.Message_ID = m.Message_ID
        JOIN Scripts s ON m.Script_ID = s.Script_ID
        WHERE e.Message_String LIKE '%Error%';
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        # 4. Extract status code and URL
        df['Error Status Code'] = df['Message_String'].apply(extract_status_code)
        df['URL'] = df['Message_String'].apply(extract_url)

        # 5. Filter valid rows
        df_valid = df[df['Error Status Code'].notnull() & df['URL'].notnull()]

        # 6. Create summary DataFrame
        summary_df = df_valid.groupby('Error Status Code').agg(
            Count=('URL', 'count'),
            URLs=('URL', lambda x: ', '.join(sorted(set(x))))
        ).reset_index()

        return summary_df

# Example usage:
if __name__ == "__main__":
    zip_file_path = r"C:\Users\Kapil.Sharma1\Downloads\SqliteDb.db (3).zip"  # Change this to your zip file path
    summary = automate_flow(zip_file_path)
    print(summary)

GitHub Copilot: Certainly! Here’s a line-by-line explanation of your code, with reasoning for each step:

```python
import zipfile
import sqlite3
import pandas as pd
import re
import os
import tempfile
```
- **Imports**: You import libraries for handling zip files, SQLite databases, dataframes, regex, file paths, and temporary directories.

---

```python
# Function to extract status code from Message_String
def extract_status_code(msg):
    # Look for HTTP Status-Code=XXX or (XXX ...) or Error -XXXXX: HTTP Status-Code=XXX
    match = re.search(r'HTTP Status-Code=(\d{3})', msg)
    if match:
        return match.group(1)
    match = re.search(r'\((\d{3}) [^\)]*\)', msg)
    if match:
        return match.group(1)
    match = re.search(r'(\d{3}) (Internal Server Error|Bad Request|Unauthorized|)', msg)
    if match:
        return match.group(1)
    return 'Other'
```
- **extract_status_code**: This function tries to extract a 3-digit HTTP status code from a message string using regex.  
  - First, it looks for `HTTP Status-Code=XXX`.
  - If not found, it looks for a pattern like `(XXX ...)`.
  - Then, it looks for codes followed by common error phrases.
  - If none match, returns `'Other'`.

---

```python
def extract_url(msg):
    # Extract URL between for " and next "
    match = re.search(r'for\s+"([^"]+)"', msg)
    if match:
        return match.group(1)
    # Sometimes it's after Request "
    match = re.search(r'Request\s+"([^"]+)"', msg)
    if match:
        return match.group(1)
    return None
```
- **extract_url**: This function extracts a URL from the message string.
  - First, it looks for `for "URL"`.
  - If not found, it looks for `Request "URL"`.
  - If neither is found, returns `None`.

---

```python
def automate_flow(zip_path):
    # 1. Unzip to a temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)
```
- **automate_flow**: Main function to automate the process.
  - Creates a temporary directory.
  - Unzips the provided zip file into this directory.

---

```python
        # 2. Find sqliteDb.db
        db_path = None
        for root, dirs, files in os.walk(tmpdir):
            for file in files:
                if file.lower().endswith('.db'):
                    db_path = os.path.join(root, file)
                    break
        if not db_path:
            raise FileNotFoundError("sqliteDb.db not found in the zip file.")
```
- **Find .db file**: Walks through the extracted files to find any file ending with `.db`.
  - If not found, raises an error.

---

```python
        # 3. Connect and run query
        conn = sqlite3.connect(db_path)
        query = """
        SELECT e.Message_ID, e.Message_String, s.Script_Name
        FROM ErrorMessages e
        JOIN Main m ON e.Message_ID = m.Message_ID
        JOIN Scripts s ON m.Script_ID = s.Script_ID
        WHERE e.Message_String LIKE '%Error%';
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
```
- **Query database**: Connects to the SQLite database, runs a SQL query to get error messages and script names, and loads the result into a pandas DataFrame.

---

```python
        # 4. Extract status code and URL
        df['Error Status Code'] = df['Message_String'].apply(extract_status_code)
        df['URL'] = df['Message_String'].apply(extract_url)
```
- **Extract info**: Adds two new columns to the DataFrame by applying the earlier functions to each message string.

---

```python
        # 5. Filter valid rows
        df_valid = df[df['Error Status Code'].notnull() & df['URL'].notnull()]
```
- **Filter**: Keeps only rows where both status code and URL were found.

---

```python
        # 6. Create summary DataFrame
        summary_df = df_valid.groupby('Error Status Code').agg(
            Count=('URL', 'count'),
            URLs=('URL', lambda x: ', '.join(sorted(set(x))))
        ).reset_index()
```
- **Summarize**: Groups by error status code, counts occurrences, and lists unique URLs for each code.

---

```python
        return summary_df
```
- **Return**: Returns the summary DataFrame.

---

```python
# Example usage:
if __name__ == "__main__":
    zip_file_path = r"C:\Users\Kapil.Sharma1\Downloads\SqliteDb.db (3).zip"  # Change this to your zip file path
    summary = automate_flow(zip_file_path)
    print(summary)
```
- **Main block**: If run as a script, calls `automate_flow` with a zip file path and prints the summary.

---

**Summary:**  
- The script unzips a file, finds a database, extracts error messages, parses out HTTP status codes and URLs, and summarizes the errors by code and URL.  
- The logic is modular, using helper functions for parsing, and pandas for data manipulation.  
- The approach is systematic: unzip → find DB → query → parse → filter → summarize.
