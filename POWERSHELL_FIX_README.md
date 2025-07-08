# PowerShell Command Issues - Fix Guide

## 🚨 Problem

PowerShell commands are hanging or failing due to:
- Syntax differences (e.g., `&&` not supported)
- Command parsing issues
- Terminal output formatting problems

## ✅ Solutions

We've created three alternatives to avoid PowerShell issues:

### 1. **Python Command Runner (Recommended)**

The most reliable option - uses Python subprocess to run commands:

```bash
# Usage
python run_cmd.py commit "Your commit message"
python run_cmd.py push
python run_cmd.py deploy
python run_cmd.py test
python run_cmd.py status
```

**Benefits:**
- Cross-platform compatible
- Better error handling
- Colored output
- No PowerShell syntax issues

### 2. **Batch File (Windows CMD)**

Simple batch file for common commands:

```cmd
# Usage
commands.bat commit "Your commit message"
commands.bat push
commands.bat deploy
commands.bat test
commands.bat status
```

**Benefits:**
- Works in Windows Command Prompt
- No PowerShell required
- Simple and fast

### 3. **PowerShell Helper Script**

If you must use PowerShell, load the helper functions:

```powershell
# Load the script
. .\run_commands.ps1

# Use the functions
Git-SafeCommit "Your commit message"
Git-SafePush
Run-NodeScript "test.js"
Run-PythonScript "test.py"
```

## 🔧 Common Tasks

### Git Operations

Instead of PowerShell hanging on:
```powershell
# This fails in PowerShell
git add -A && git commit -m "message" && git push
```

Use:
```bash
# Python runner (recommended)
python run_cmd.py commit "message"
python run_cmd.py push

# OR Batch file
commands.bat commit "message"
commands.bat push
```

### Running Scripts

Instead of:
```powershell
# May hang
node test_script.js
```

Use:
```bash
# Python runner
python run_cmd.py deploy

# Direct Python subprocess
python -c "import subprocess; subprocess.run(['node', 'test_script.js'])"
```

## 💡 Tips

1. **Use Python Runner First** - It's the most reliable
2. **Avoid chaining commands** with `&&` or `||` in PowerShell
3. **Use semicolons** (`;`) instead of `&&` if you must use PowerShell
4. **Consider using Git Bash** on Windows for better compatibility

## 🎯 Quick Reference

| Task | Python Runner | Batch File | PowerShell Fix |
|------|--------------|------------|----------------|
| Commit | `python run_cmd.py commit "msg"` | `commands.bat commit "msg"` | `Git-SafeCommit "msg"` |
| Push | `python run_cmd.py push` | `commands.bat push` | `Git-SafePush` |
| Deploy Check | `python run_cmd.py deploy` | `commands.bat deploy` | `Check-Deployment` |
| Run Tests | `python run_cmd.py test` | `commands.bat test` | `Run-Tests` |

## 🛠️ Installation

No installation needed! The scripts are ready to use:

1. **Python Runner**: Requires Python (already installed)
2. **Batch File**: Works on any Windows system
3. **PowerShell Script**: Run `. .\run_commands.ps1` to load functions

Choose the method that works best for you! 