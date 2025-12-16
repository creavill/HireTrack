@echo off
REM Hammy the Hire Tracker - Windows Setup Script
REM This script sets up a virtual environment and installs dependencies

echo.
echo ========================================
echo   Hammy the Hire Tracker - Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

echo [1/5] Checking Python version...
python --version

echo.
echo [2/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Skipping creation.
) else (
    python -m venv venv
    echo Virtual environment created successfully!
)

echo.
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [4/5] Installing dependencies...
pip install -r requirements-local.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies
    echo Try running: python -m pip install -r requirements-local.txt
    pause
    exit /b 1
)

echo.
echo [5/5] Checking configuration files...

if not exist config.yaml (
    echo WARNING: config.yaml not found
    echo Creating from template...
    copy config.example.yaml config.yaml
    echo.
    echo IMPORTANT: Edit config.yaml with your information!
    echo You can use: notepad config.yaml
)

if not exist .env (
    echo WARNING: .env file not found
    echo Creating template...
    echo ANTHROPIC_API_KEY=your_key_here > .env
    echo.
    echo IMPORTANT: Edit .env and add your Anthropic API key!
    echo You can use: notepad .env
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Edit config.yaml with your information
echo   2. Edit .env and add your ANTHROPIC_API_KEY
echo   3. Run: python local_app.py
echo.
echo To activate the virtual environment later, run:
echo   venv\Scripts\activate
echo.
pause
