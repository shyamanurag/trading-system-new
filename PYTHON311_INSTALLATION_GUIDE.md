# 🚀 Python 3.11 Installation & Setup Guide

## 📥 **Step 1: Install Python 3.11**

### **Option A: Download from Official Website**
1. Go to: https://www.python.org/downloads/release/python-3118/
2. Scroll down to "Files" section
3. Download: `Windows installer (64-bit)`
4. Run the installer with these settings:
   - ✅ **Add Python 3.11 to PATH**
   - ✅ **Install for all users**
   - ✅ **Create shortcuts for installed applications**

### **Option B: Using Windows Store**
1. Open Microsoft Store
2. Search for "Python 3.11"
3. Install "Python 3.11" by Python Software Foundation

### **Option C: Using Chocolatey (if installed)**
```powershell
choco install python311
```

## 🔍 **Step 2: Verify Installation**

Open a **NEW** PowerShell window and run:
```powershell
python3.11 --version
# Should show: Python 3.11.8

# Or try:
py -3.11 --version
```

## 🔄 **Step 3: Create New Virtual Environment**

```powershell
# Navigate to your project
cd D:\trading-system-new

# Remove old environment (if exists)
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue

# Create new environment with Python 3.11
python3.11 -m venv .venv

# Activate the environment
.venv\Scripts\activate
```

## 📦 **Step 4: Install Dependencies**

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements_python311.txt
```

## ✅ **Step 5: Test Everything**

```powershell
# Test Python version
python --version
# Should show: Python 3.11.8

# Test TrueData
python -c "from truedata_ws.websocket.TD import TD; print('✅ TrueData works!')"

# Test all imports
python migrate_to_python311.py
```

## 🚀 **Step 6: Update DigitalOcean**

1. Go to your DigitalOcean App Platform
2. Update your app spec with the new configuration
3. Use the `digitalocean_app_spec_python311.yml` file
4. Deploy the updated configuration

## 🔧 **Troubleshooting**

### **Issue: "python3.11 not found"**
**Solution:** 
- Make sure you installed Python 3.11 with "Add to PATH" checked
- Restart PowerShell after installation
- Try: `py -3.11 --version`

### **Issue: "Permission denied"**
**Solution:**
- Run PowerShell as Administrator
- Or install for current user only

### **Issue: "pip not found"**
**Solution:**
```powershell
python -m ensurepip --upgrade
```

## 📋 **Complete Commands Sequence**

```powershell
# 1. Install Python 3.11 (manual download required)
# 2. Open NEW PowerShell window
cd D:\trading-system-new

# 3. Remove old environment
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue

# 4. Create new environment
python3.11 -m venv .venv

# 5. Activate
.venv\Scripts\activate

# 6. Install dependencies
pip install -r requirements_python311.txt

# 7. Test
python migrate_to_python311.py
```

## 🎯 **Expected Results**

After successful migration:
- ✅ Python 3.11.8 running
- ✅ TrueData imports working
- ✅ All trading libraries compatible
- ✅ No more compatibility errors
- ✅ Ready for DigitalOcean deployment

## 📞 **Need Help?**

If you encounter any issues:
1. Make sure Python 3.11 is properly installed
2. Restart PowerShell after installation
3. Check that "Add to PATH" was selected during installation
4. Run the migration script to test everything

Your trading system will be much more stable with Python 3.11! 🚀 