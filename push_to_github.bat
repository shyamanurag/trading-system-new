@echo off
echo ==========================================
echo PUSHING CRITICAL FIXES TO GITHUB
echo ==========================================
echo.

cd /d C:\trading-system-new

echo === Current Git Status ===
git status
echo.

echo === Adding all changes ===
git add -A
echo.

echo === Committing ===
git commit -m "CRITICAL Dec 1 2025: get_quotes + previous_close + daily_loss_limit + NFO fixes"
echo.

echo === Pushing to GitHub ===
git push origin main
echo.

echo === Verifying Push ===
git log origin/main --oneline -5
echo.

echo ==========================================
echo DONE - Check output above for errors
echo ==========================================
pause

