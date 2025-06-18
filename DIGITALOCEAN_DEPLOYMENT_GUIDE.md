# DigitalOcean Deployment Fix Guide

## 🚨 Critical Issues Found

Based on your current configuration, here are the main issues that need to be fixed:

### 1. **TrueData Configuration Mismatch**
```bash
# ❌ Current (Problematic)
TRUEDATA_SANDBOX=true
TRUEDATA_PORT=8084  # This should be TRUEDATA_LIVE_PORT

# ✅ Fixed
TRUEDATA_IS_SANDBOX=false
TRUEDATA_LIVE_PORT=8084
```

### 2. **Missing Environment Variables**
Your current `.env` is missing several variables that our new TrueData configuration expects.

## 🔧 Required Changes

### Step 1: Update DigitalOcean Environment Variables

In your DigitalOcean App Platform dashboard, update these environment variables:

#### **Remove/Replace These:**
```bash
TRUEDATA_SANDBOX=true
TRUEDATA_PORT=8084
```

#### **Add These New Variables:**
```bash
TRUEDATA_LIVE_PORT=8084
TRUEDATA_IS_SANDBOX=false
TRUEDATA_LOG_LEVEL=INFO
TRUEDATA_DATA_TIMEOUT=60
TRUEDATA_RETRY_ATTEMPTS=3
TRUEDATA_RETRY_DELAY=5
TRUEDATA_MAX_CONNECTION_ATTEMPTS=3
REDIS_DB=0
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
ROOT_PATH=/api
WS_MAX_CONNECTIONS=1000
WS_HEARTBEAT_INTERVAL=30
WS_CONNECTION_TIMEOUT=60
ENABLE_METRICS=true
ENABLE_HEALTH_CHECKS=true
HEALTH_CHECK_INTERVAL=30
```

### Step 2: DigitalOcean App Platform Settings

#### **Build Command:**
```bash
pip install -r requirements.txt && pip install truedata-ws
```

#### **Run Command:**
```bash
python main.py
```

#### **Environment:**
- **Python Version**: 3.10 (current) or 3.11 (recommended)
- **Port**: 8000
- **Health Check Path**: `/health/ready`

### Step 3: Verify TrueData Installation

Add this to your `requirements.txt`:
```txt
truedata-ws>=1.0.0
websocket-client>=1.8.0
```

## 📋 Complete Environment Variables for DigitalOcean

Copy this complete configuration to your DigitalOcean App Platform environment variables:

```bash
# =============================================================================
# FRONTEND CONFIGURATION
# =============================================================================
VITE_API_URL=https://algoauto-jd32t.ondigitalocean.app/api
VITE_WS_URL=wss://algoauto-jd32t.ondigitalocean.app/ws
VITE_APP_NAME=AlgoAuto Trading
VITE_APP_VERSION=1.0.0
VITE_APP_ENV=production

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
DATABASE_URL=postgresql://doadmin:AVNS_LpaPpsdL4CtOii03MnN@app-81cd3b75-f46c-49f9-8f76-09040fd8fc68-do-user-23093341-0.k.db.ondigitalocean.com:25060/defaultdb?sslmode=require
DATABASE_HOST=app-81cd3b75-f46c-49f9-8f76-09040fd8fc68-do-user-23093341-0.k.db.ondigitalocean.com
DATABASE_PORT=25060
DATABASE_NAME=defaultdb
DATABASE_USER=doadmin
DATABASE_PASSWORD=AVNS_LpaPpsdL4CtOii03MnN
DATABASE_SSL=require

# =============================================================================
# REDIS CONFIGURATION
# =============================================================================
REDIS_URL=rediss://default:AVNS_TSCy17L6f9z0CdWgcvW@redis-cache-do-user-23093341-0.k.db.ondigitalocean.com:25061
REDIS_HOST=redis-cache-do-user-23093341-0.k.db.ondigitalocean.com
REDIS_PORT=25061
REDIS_PASSWORD=AVNS_TSCy17L6f9z0CdWgcvW
REDIS_USERNAME=default
REDIS_SSL=true
REDIS_DB=0

# =============================================================================
# TRUEDATA CONFIGURATION (FIXED)
# =============================================================================
TRUEDATA_USERNAME=tdwsp697
TRUEDATA_PASSWORD=shyam@697
TRUEDATA_LIVE_PORT=8084
TRUEDATA_URL=push.truedata.in
TRUEDATA_LOG_LEVEL=INFO
TRUEDATA_IS_SANDBOX=false
TRUEDATA_DATA_TIMEOUT=60
TRUEDATA_RETRY_ATTEMPTS=3
TRUEDATA_RETRY_DELAY=5
TRUEDATA_MAX_CONNECTION_ATTEMPTS=3

# =============================================================================
# ZERODHA CONFIGURATION
# =============================================================================
ZERODHA_API_KEY=sylcoq492qz6f7ej
ZERODHA_API_SECRET=jm3h4iejwnxr4ngmma2qxccpkhevo8sy
ZERODHA_USER_ID=QSW899

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================
JWT_SECRET=K5ewmaPLwWLzqcFa2ne6dLpk_5YbUa1NC-xR9N8ig74TnENXKUnnK1UTs3xcaE8IRIEMYRVSCN-co2vEPTeq9A
ENCRYPTION_KEY=lulCrXu3nDX6I18WYuPpWcIrgf2IUGAGLS93ZDwczpQ

# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================
APP_URL=https://algoauto-jd32t.ondigitalocean.app
FRONTEND_URL=https://algoauto-jd32t.ondigitalocean.app
NODE_ENV=production
ENVIRONMENT=production
DEBUG=false
PYTHONPATH=/workspace

# =============================================================================
# CORS AND NETWORKING
# =============================================================================
CORS_ORIGINS=["https://algoauto-jd32t.ondigitalocean.app", "http://localhost:3000", "http://localhost:5173"]
ENABLE_CORS=true

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# =============================================================================
# TRADING CONFIGURATION
# =============================================================================
PAPER_TRADING=true
PAPER_TRADING_ENABLED=true
AUTONOMOUS_TRADING_ENABLED=true

# =============================================================================
# PERFORMANCE CONFIGURATION
# =============================================================================
MAX_CONNECTIONS=20
POOL_SIZE=10
CACHE_TTL=300

# =============================================================================
# API CONFIGURATION
# =============================================================================
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
ROOT_PATH=/api

# =============================================================================
# WEBSOCKET CONFIGURATION
# =============================================================================
WS_MAX_CONNECTIONS=1000
WS_HEARTBEAT_INTERVAL=30
WS_CONNECTION_TIMEOUT=60

# =============================================================================
# MONITORING CONFIGURATION
# =============================================================================
ENABLE_METRICS=true
ENABLE_HEALTH_CHECKS=true
HEALTH_CHECK_INTERVAL=30
```

## 🚀 Deployment Steps

### 1. **Update Environment Variables**
1. Go to your DigitalOcean App Platform dashboard
2. Navigate to your app settings
3. Go to "Environment Variables" section
4. Add/update all the variables above
5. **Important**: Remove `TRUEDATA_SANDBOX=true` and `TRUEDATA_PORT=8084`

### 2. **Update Build Settings**
1. Go to "Settings" → "Build & Deploy"
2. Set build command: `pip install -r requirements.txt && pip install truedata-ws`
3. Set run command: `python main.py`
4. Set port: `8000`

### 3. **Update Health Check**
1. Go to "Settings" → "Health Checks"
2. Set health check path: `/health/ready`
3. Set initial delay: `30 seconds`
4. Set interval: `30 seconds`
5. Set timeout: `10 seconds`

### 4. **Deploy**
1. Click "Deploy" to trigger a new deployment
2. Monitor the build logs for any errors
3. Check the application logs after deployment

## 🔍 Troubleshooting

### **If the app still fails to start:**

1. **Check Python Version**:
   ```bash
   # In DigitalOcean logs, look for:
   Python version: 3.10.x
   ```

2. **Check TrueData Installation**:
   ```bash
   # Add this to your requirements.txt
   truedata-ws>=1.0.0
   ```

3. **Check Import Errors**:
   - The main issue was `TrueDataConfig` import - this is now fixed
   - Make sure all environment variables are set correctly

4. **Check Redis Connection**:
   - Your Redis configuration looks correct
   - The SSL settings should work with DigitalOcean Redis

### **Expected Success Logs:**
```
✅ Redis connection successful!
✅ Database manager initialized successfully
✅ TrueData configuration loaded successfully
✅ Application started successfully
```

## 📞 Support

If you still encounter issues after making these changes:

1. **Check the deployment logs** in DigitalOcean dashboard
2. **Verify all environment variables** are set correctly
3. **Test the health endpoint**: `https://algoauto-jd32t.ondigitalocean.app/health/ready`
4. **Check TrueData connection**: The app will log TrueData connection status

## 🎯 Expected Result

After making these changes, your application should:
- ✅ Start without import errors
- ✅ Connect to Redis successfully
- ✅ Load TrueData configuration properly
- ✅ Be ready to handle market data requests
- ✅ Respond to health checks

The main fix is changing `TRUEDATA_SANDBOX=true` to `TRUEDATA_IS_SANDBOX=false` and updating the port variable name to match our new configuration structure. 