# PowerShell Script: Python 3.11 Setup for Trading System
# Run this script AFTER installing Python 3.11

Write-Host "🚀 Python 3.11 Setup Script for Trading System" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

# Check if Python 3.11 is available
Write-Host "`n🔍 Checking Python 3.11 installation..." -ForegroundColor Yellow

try {
    $python311Version = & python3.11 --version 2>$null
    if ($python311Version) {
        Write-Host "✅ Python 3.11 found: $python311Version" -ForegroundColor Green
    }
    else {
        throw "Python 3.11 not found"
    }
}
catch {
    Write-Host "❌ Python 3.11 not found. Please install it first:" -ForegroundColor Red
    Write-Host "   Download from: https://www.python.org/downloads/release/python-3118/" -ForegroundColor Cyan
    Write-Host "   Make sure to check 'Add Python 3.11 to PATH' during installation" -ForegroundColor Cyan
    exit 1
}

# Remove old environment
Write-Host "`n🗑️  Removing old virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Remove-Item -Recurse -Force .venv
    Write-Host "✅ Old environment removed" -ForegroundColor Green
}
else {
    Write-Host "ℹ️  No old environment found" -ForegroundColor Blue
}

# Create new environment
Write-Host "`n🔧 Creating new Python 3.11 virtual environment..." -ForegroundColor Yellow
try {
    & python3.11 -m venv .venv
    Write-Host "✅ Virtual environment created successfully" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to create virtual environment: $_" -ForegroundColor Red
    exit 1
}

# Activate environment
Write-Host "`n🔌 Activating virtual environment..." -ForegroundColor Yellow
try {
    & .venv\Scripts\Activate.ps1
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to activate environment: $_" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "`n⬆️  Upgrading pip..." -ForegroundColor Yellow
try {
    & python -m pip install --upgrade pip
    Write-Host "✅ Pip upgraded" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to upgrade pip: $_" -ForegroundColor Red
}

# Install dependencies
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Yellow
try {
    & pip install -r requirements_python311.txt
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to install dependencies: $_" -ForegroundColor Red
    Write-Host "💡 Try running: pip install -r requirements_python311.txt manually" -ForegroundColor Cyan
}

# Test imports
Write-Host "`n🧪 Testing imports..." -ForegroundColor Yellow
try {
    $testResult = & python -c "import pandas; import numpy; from truedata_ws.websocket.TD import TD; print('All imports successful')" 2>$null
    if ($testResult) {
        Write-Host "✅ All imports working correctly" -ForegroundColor Green
    }
    else {
        throw "Import test failed"
    }
}
catch {
    Write-Host "❌ Import test failed: $_" -ForegroundColor Red
    Write-Host "💡 Some packages may need manual installation" -ForegroundColor Cyan
}

# Run migration script
Write-Host "`n🔍 Running migration verification..." -ForegroundColor Yellow
try {
    & python migrate_to_python311.py
    Write-Host "✅ Migration verification completed" -ForegroundColor Green
}
catch {
    Write-Host "⚠️  Migration verification had issues: $_" -ForegroundColor Yellow
}

# Final summary
Write-Host "`n📊 Setup Summary:" -ForegroundColor Green
Write-Host "=" * 30 -ForegroundColor Green

$pythonVersion = & python --version 2>$null
Write-Host "Python Version: $pythonVersion" -ForegroundColor Cyan

if (Test-Path ".venv") {
    Write-Host "Virtual Environment: ✅ Created and activated" -ForegroundColor Green
}
else {
    Write-Host "Virtual Environment: ❌ Not found" -ForegroundColor Red
}

Write-Host "`n🎯 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Your Python 3.11 environment is ready!" -ForegroundColor Green
Write-Host "2. Update your DigitalOcean app spec with the new configuration" -ForegroundColor Green
Write-Host "3. Deploy your trading system with confidence!" -ForegroundColor Green

Write-Host "`n🚀 Your trading system is now ready for Python 3.11!" -ForegroundColor Green
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 