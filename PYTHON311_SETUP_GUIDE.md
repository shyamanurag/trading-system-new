# Python 3.11 Setup Guide for Trading System

## 🚨 **Why Python 3.11?**

Python 3.13 has compatibility issues with:
- TrueData library (`distutils` removed)
- Pandas 2.2.0 (requires older Python)
- Many other trading libraries
- NumPy compatibility issues

Python 3.11 is the **recommended version** for trading systems.

## 📥 **Step 1: Install Python 3.11**

### Windows:
1. Download Python 3.11 from: https://www.python.org/downloads/release/python-3118/
2. Choose: `Windows installer (64-bit)`
3. Install with "Add to PATH" checked

### Verify Installation:
```bash
python3.11 --version
# Should show: Python 3.11.8
```

## 🔄 **Step 2: Create New Virtual Environment**

```bash
# Remove old environment
rm -rf .venv

# Create new environment with Python 3.11
python3.11 -m venv .venv

# Activate environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

## 📦 **Step 3: Install Dependencies**

```bash
# Upgrade pip
pip install --upgrade pip

# Install core dependencies
pip install fastapi uvicorn gunicorn redis sqlalchemy

# Install data science packages (compatible with Python 3.11)
pip install pandas==2.2.0 numpy==1.26.4

# Install TrueData (will work with Python 3.11)
pip install truedata-ws

# Install other trading dependencies
pip install websocket-client requests python-dateutil

# Install development dependencies
pip install pytest black flake8
```

## ✅ **Step 4: Verify TrueData Works**

```python
# Test TrueData import
python -c "from truedata_ws.websocket.TD import TD; print('TrueData works!')"
```

## 🔧 **Step 5: Update DigitalOcean Configuration**

### Update your DigitalOcean app spec:

```yaml
name: trading-system
services:
- name: web
  source_dir: /
  github:
    repo: shyamanurag/trading-system-new
    branch: main
  run_command: gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
  build_command: pip install -r requirements.txt
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  health_check:
    http_path: /health/ready
  envs:
  - key: PYTHON_VERSION
    value: "3.11"
  - key: PIP_REQUIREMENTS
    value: "fastapi uvicorn gunicorn redis sqlalchemy pandas==2.2.0 numpy==1.26.4 truedata-ws websocket-client requests python-dateutil"
```

## 📋 **Step 6: Update requirements.txt**

Create/update `requirements.txt`:

```txt
fastapi==0.104.1
uvicorn==0.24.0
gunicorn==21.2.0
redis==5.0.1
sqlalchemy==2.0.23
pandas==2.2.0
numpy==1.26.4
truedata-ws==1.0.0
websocket-client==1.6.4
requests==2.31.0
python-dateutil==2.8.2
pydantic==2.5.0
python-multipart==0.0.6
```

## 🚀 **Step 7: Test Everything**

```bash
# Test imports
python -c "import pandas; import numpy; from truedata_ws.websocket.TD import TD; print('All imports work!')"

# Test your app
python main.py
```

## 🔍 **Step 8: Common Issues & Solutions**

### Issue: "No module named 'distutils'"
**Solution:** Use Python 3.11 (distutils was removed in 3.13)

### Issue: "pandas._libs.pandas_parser not found"
**Solution:** Use pandas 2.2.0 with Python 3.11

### Issue: "NumPy compatibility"
**Solution:** Use numpy 1.26.4 with Python 3.11

## 📊 **Benefits of Python 3.11**

✅ **Stable & Mature** - No breaking changes
✅ **TrueData Compatible** - Works with all trading libraries
✅ **Better Performance** - Faster than Python 3.10
✅ **Wide Library Support** - All major trading libraries work
✅ **Production Ready** - Used by major trading firms

## 🎯 **Next Steps**

1. Follow this guide to set up Python 3.11
2. Update your DigitalOcean app spec
3. Test TrueData integration
4. Deploy with confidence!

Your trading system will be much more stable and compatible with Python 3.11! 🚀
