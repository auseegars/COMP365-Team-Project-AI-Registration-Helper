# Advisor Hub

COMP365 AI Registration Helper component owned by the Advisor Hub and Interface
Developer. All component code, dependencies, sample data, and tests live here,
separate from teammates' work.

## Stage 1: Project setup

The Python package and Streamlit entry point are ready. The classifier is an
explicit, unimplemented stub for Stage 2. The interface displays only a project
placeholder; the full dashboard is deferred.

## Local setup

Use Python 3.10 or later. From the repository root on Windows:

```powershell
py -3.12 -m venv advisor_hub/.venv
advisor_hub/.venv/Scripts/python.exe -m pip install -r advisor_hub/requirements.txt
advisor_hub/.venv/Scripts/python.exe -m unittest discover -s advisor_hub/tests -v
advisor_hub/.venv/Scripts/python.exe -m streamlit run advisor_hub/app.py
```

The classifier package and its import checks use only the Python standard library.
Streamlit is imported only when the interface runs.

## Structure

```text
advisor_hub/
  .gitignore
  __init__.py
  app.py                  # Minimal Streamlit entry point
  classifier.py           # Request classification entry point
  requirements.txt
  README.md
  sample_data/            # Reserved for clearly labeled synthetic requests
  tests/                  # Standard-library unittest tests
```
