@echo off
REM Python 3.11 Setup Script for Trading System

echo Setting up trading system with Python 3.11...

REM Check if Python 3.11 is available
python --version 2>nul
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11 first.
    echo See PYTHON311_SETUP_GUIDE.md for instructions.
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv .venv311

REM Activate virtual environment
echo Activating virtual environment...
call .venv311\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements_python311.txt

REM Install TrueData
echo Installing TrueData...
pip install truedata-ws

echo Setup complete!
echo To activate: .venv311\Scripts\activate.bat
pause
