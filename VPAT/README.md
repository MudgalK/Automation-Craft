# VPAT — LoadRunner Result Analyzer (LRA)

VPAT is a Python-based tool designed to analyze **LoadRunner test results** from **`.lra`** files and present performance insights through an interactive UI and APIs.

**Tech stack**
- **Python**
- **ML**
- **FastAPI** (backend APIs)
- **Streamlit** (web UI)

---

## What VPAT does

- Upload and parse LoadRunner **`.lra`** result files
- Extract transactions and response-time metrics (e.g., percentiles)
- Allow users to define a **baseline SLA** (commonly 90th percentile) per transaction
- Provide views for:
  - **SLA view** (baseline entry + validation)
  - **Results view** (percentile RT table with color coding + CSV download)
  - **Graphical view** (charts for transaction metrics)
  - **Log level analysis** (log-level data exploration, if available)

---

## Architecture / Working

![VPAT Architecture](./docs/architecture.png)

### Flow Summary (based on architecture)
1. **Upload Page (Streamlit)**
   - User uploads `.lra` file
   - Tool asks whether baseline should be set (Yes/No)

2. **Backend processing (FastAPI)**
   - Streamlit calls backend APIs (e.g., `GetData`) to parse the uploaded file and return structured output (JSON)
   - If required artifacts are missing (implementation dependent), user is blocked with an error

3. **SLA View**
   - Tool prompts user that **90th percentile** can be used as baseline, or allows manual entry per transaction
   - Baseline values are stored for subsequent comparisons

4. **Results View**
   - User selects percentile RT (radio button)
   - Table is shown with **color coding**
   - User can **download results as CSV**

5. **Graphical View**
   - Charts for metrics associated with the test/run

6. **Log Level Analysis**
   - Log-level data analysis associated with the test (if present)

---

## Prerequisites

All Python dependencies required to run VPAT are listed in **`requirements.txt`**.

Install them using:

```bash
pip install -r requirements.txt
```

> Recommended: Use a virtual environment before installing dependencies.

---

## Setup

### 1) Create and activate a virtual environment

**Windows (PowerShell)**
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

---

## Run the FastAPI server (Backend)

Your FastAPI application entry file is: **`APIs.py`**.

### Start the server with Uvicorn
From the folder that contains `APIs.py` (or from repo root if that path is on your Python import path), run:

```bash
uvicorn APIs:app --host 0.0.0.0 --port 8000 --reload
```

- API base URL: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

> Note: This assumes your FastAPI instance is named `app` inside `APIs.py` (i.e., `app = FastAPI()`).
> If it’s named differently (e.g., `api`), run `uvicorn APIs:api ...`.

---

## Run the Streamlit server (UI)

Your Streamlit entry file is: **`Main Page.py`**.

In a **separate terminal** (same venv activated), run:

```bash
streamlit run "Main Page.py" --server.port 8501
```

- UI URL: `http://localhost:8501`

> Quoting is important because the filename contains a space.

---

## Run both together (typical local workflow)

1. Terminal 1 — start backend:
   ```bash
   uvicorn APIs:app --host 0.0.0.0 --port 8000 --reload
   ```

2. Terminal 2 — start UI:
   ```bash
   streamlit run "Main Page.py" --server.port 8501
   ```

---

## Configuration (optional but recommended)

If Streamlit needs to know where FastAPI is running, set an environment variable such as:

- `VPAT_API_URL` = `http://localhost:8000`

**Windows (PowerShell)**
```bash
$env:VPAT_API_URL="http://localhost:8000"
```

**macOS/Linux**
```bash
export VPAT_API_URL="http://localhost:8000"
```

---

## Troubleshooting

- **Port already in use**
  - FastAPI: change `--port 8001`
  - Streamlit: change `--server.port 8502`

- **Uvicorn import errors**
  - Make sure you run the command from the directory containing `APIs.py`, or adjust to a dotted module path (example):
    - If the file is `backend/APIs.py`, run:
      ```bash
      uvicorn backend.APIs:app --reload --port 8000
      ```

- **Streamlit filename issues**
  - Always run with quotes: `streamlit run "Main Page.py"`

---
**VPAT** converts raw LoadRunner outputs into SLA-focused insights, tables, and charts—through a Streamlit UI backed by FastAPI.
