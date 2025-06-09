@echo off
echo Starting Trading System Local Development...
echo.

REM Start Backend in new window
echo Starting Backend Server...
start "Trading System Backend" cmd /k "cd /d %~dp0 && trading_env\Scripts\activate && python main.py"

REM Wait a bit for backend to start
timeout /t 5 /nobreak > nul

REM Start Frontend in new window
echo Starting Frontend Development Server...
start "Trading System Frontend" cmd /k "cd /d %~dp0\src\frontend && npm run dev"

echo.
echo ============================================
echo Trading System is starting up!
echo ============================================
echo.
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Default Login:
echo Username: admin
echo Password: admin123
echo.
echo Press any key to open the frontend in your browser...
pause > nul

REM Open browser
start http://localhost:3000

echo.
echo Both servers are running in separate windows.
echo Close this window when done.
pause 