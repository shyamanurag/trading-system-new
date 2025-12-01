@echo off
echo ==========================================
echo PUSHING CRITICAL FIXES TO GITHUB
echo ==========================================
echo.
echo FIXES IN THIS PUSH:
echo 1. NFO cache now EXCHANGE-SPECIFIC (prevents NSE/NFO cross-contamination)
echo 2. get_quotes method is now async (fixes 'dict can't be awaited' error)
echo 3. Added NFO sanity check to detect cache contamination
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
git commit -m "CRITICAL Dec 1 2025: Exchange-specific NFO cache + async get_quotes fix"

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
