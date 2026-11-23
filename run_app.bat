@echo off
TITLE TREKVERSE - AI-Powered Student Success System
echo =========================================================================
echo Starting TREKVERSE AI-Powered Student Success Platform...
echo =========================================================================
cd /d "%~dp0"

SET PYTHON_PATH="C:\Users\Tharun Reddy\AppData\Local\Python\pythoncore-3.14-64\python.exe"

IF EXIST %PYTHON_PATH% (
    %PYTHON_PATH% -m streamlit run app/app.py --server.port 8501
) ELSE (
    python -m streamlit run app/app.py --server.port 8501
)

pause

