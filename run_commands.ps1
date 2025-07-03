# PowerShell Helper Script for Trading System
# This script provides functions to run common commands without hanging

# Function to run git commands safely
function Git-SafeCommit {
    param(
        [string]$message
    )
    Write-Host "Adding files..." -ForegroundColor Green
    git add -A
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Committing..." -ForegroundColor Green
        git commit -m $message
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Commit successful!" -ForegroundColor Green
        } else {
            Write-Host "Commit failed!" -ForegroundColor Red
        }
    } else {
        Write-Host "Git add failed!" -ForegroundColor Red
    }
}

# Function to run git push safely
function Git-SafePush {
    Write-Host "Pushing to origin main..." -ForegroundColor Green
    git push origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Push successful!" -ForegroundColor Green
    } else {
        Write-Host "Push failed!" -ForegroundColor Red
    }
}

# Function to run node scripts safely
function Run-NodeScript {
    param(
        [string]$scriptName
    )
    Write-Host "Running $scriptName..." -ForegroundColor Green
    $process = Start-Process -FilePath "node" -ArgumentList $scriptName -NoNewWindow -PassThru -Wait
    if ($process.ExitCode -eq 0) {
        Write-Host "Script completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Script failed with exit code: $($process.ExitCode)" -ForegroundColor Red
    }
}

# Function to run Python scripts safely
function Run-PythonScript {
    param(
        [string]$scriptName
    )
    Write-Host "Running $scriptName..." -ForegroundColor Green
    $process = Start-Process -FilePath "python" -ArgumentList $scriptName -NoNewWindow -PassThru -Wait
    if ($process.ExitCode -eq 0) {
        Write-Host "Script completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Script failed with exit code: $($process.ExitCode)" -ForegroundColor Red
    }
}

# Function to check deployment status
function Check-Deployment {
    Write-Host "Checking deployment status..." -ForegroundColor Green
    node check_deployment.js
}

# Function to run all tests
function Run-Tests {
    Write-Host "Running test suite..." -ForegroundColor Green
    python test_deployment_status.py
}

# Function to start local development
function Start-Local {
    Write-Host "Starting local development server..." -ForegroundColor Green
    python run_local.py
}

# Display available commands
Write-Host @"
PowerShell Helper Script Loaded!
================================

Available Commands:
- Git-SafeCommit "Your commit message"    # Add and commit files
- Git-SafePush                           # Push to origin main
- Run-NodeScript "script.js"             # Run a Node.js script
- Run-PythonScript "script.py"           # Run a Python script
- Check-Deployment                       # Check deployment status
- Run-Tests                             # Run test suite
- Start-Local                           # Start local dev server

Example Usage:
> Git-SafeCommit "Fixed API endpoints"
> Git-SafePush

"@ -ForegroundColor Cyan 