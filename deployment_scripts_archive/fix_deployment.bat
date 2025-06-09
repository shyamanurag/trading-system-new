@echo off
echo Preparing for deployment...

echo Creating frontend .env.production...
echo VITE_API_URL=https://algoauto-ua2iq.ondigitalocean.app > src\frontend\.env.production

echo Fixing health check...
powershell -Command "(Get-Content health_check.py) -replace 'localhost:', '0.0.0.0:' | Set-Content health_check.py"

echo Checking JWT_SECRET...
findstr /C:"JWT_SECRET" .env.local >nul 2>&1
if errorlevel 1 (
    echo JWT_SECRET=your-secret-key-here-change-in-production >> .env.local
)

echo Updating package.json...
cd src\frontend
call npm pkg set scripts.build="vite build --mode production"
cd ..\..

echo Deployment preparation complete!
echo.
echo Next steps:
echo 1. Review changes
echo 2. Commit: git add -A ^&^& git commit -m "Fix deployment issues"
echo 3. Push: git push origin main
echo 4. Deploy will start automatically on DigitalOcean 