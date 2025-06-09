@echo off
echo 🚀 Trading System - Environment Activation
echo =======================================

echo 📁 Activating virtual environment...
call .\venv\Scripts\activate.bat

echo ✅ Virtual environment activated!
echo.
echo 💡 You can now:
echo    - Start server: python run_server.py
echo    - Run tests: python -m pytest
echo    - View docs: http://localhost:8000/docs
echo.
echo 🔄 To deactivate: type 'deactivate'
echo.

