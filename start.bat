@echo off
REM PhishLens Quick Start Script for Windows

echo ========================================
echo PhishLens AI Phishing Protection
echo ========================================
echo.

REM Check Python
echo Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed
    echo Please install Python from https://python.org
    pause
    exit /b 1
)
echo Python is installed
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

echo.
echo Checking Ollama...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Ollama is not installed
    echo Install from: https://ollama.ai
    echo.
) else (
    echo Ollama is installed
    ollama list | findstr "llama3.2" >nul 2>&1
    if %errorlevel% neq 0 (
        echo Pulling Llama 3.2 model...
        ollama pull llama3.2
    )
)

echo.
REM Check if model exists
if not exist "artifacts\xgb_model.joblib" (
    echo WARNING: Model not found at artifacts\xgb_model.joblib
    echo Please place your trained model there
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /i not "%continue%"=="y" exit /b 1
)

echo.
echo ========================================
echo Starting Flask API...
echo Access at: http://localhost:5000
echo.
echo Next steps:
echo   1. Open Chrome and go to chrome://extensions/
echo   2. Enable Developer Mode
echo   3. Click 'Load unpacked'
echo   4. Select this directory
echo   5. Browse safely with PhishLens protection!
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start Flask API
python flask_api.py
