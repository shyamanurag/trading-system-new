@echo off
echo ==========================================
echo PUSHING CRITICAL FIXES TO GITHUB
echo ==========================================
echo.
echo FIXES IN THIS PUSH:
echo 1. Fixed f-string backslash syntax error in zerodha.py line 2575
echo 2. Added missing positions router import in main.py
echo ==========================================

cd /d C:\trading-system-new

echo.
echo === Current Git Status ===
git status

echo.
echo === Adding all changes ===
git add -A

echo.
echo === Committing ===
git commit -m "Fix: f-string backslash syntax error in zerodha.py + add missing positions router import"

echo.
echo === Pushing to GitHub ===
git push origin main

echo.
echo === Verifying Push ===
git log origin/main --oneline -5

echo.
echo ==========================================
echo DONE - Check output above for errors
echo If push succeeded, DigitalOcean will auto-deploy
echo ==========================================
pause
