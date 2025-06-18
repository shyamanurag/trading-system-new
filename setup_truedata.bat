@echo off
REM TrueData Setup Script for Windows

echo Setting up TrueData for trading system...

REM Check Python
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11 first.
    pause
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install TrueData dependencies
echo Installing TrueData dependencies...
pip install -r requirements_truedata.txt

REM Install TrueData
echo Installing TrueData...
pip install truedata-ws

REM Test installation
echo Testing installation...
python quick_test_truedata.py

echo Setup complete!
echo Next steps:
echo 1. Copy .env.template to .env
echo 2. Update .env with your TrueData credentials
echo 3. Run: python test_truedata.py
pause
