# DigitalOcean Configuration Changes Required

## 🚨 Critical Changes Needed

Based on your current configuration, here are the exact changes you need to make in your DigitalOcean App Platform dashboard:

### ❌ **REMOVE These Variables:**
```yaml
- key: TRUEDATA_PORT
  scope: RUN_AND_BUILD_TIME
  value: "8084"

- key: TRUEDATA_SANDBOX
  scope: RUN_AND_BUILD_TIME
  value: "true"
```

### ✅ **ADD These New Variables:**

#### **TrueData Configuration (Fixed):**
```yaml
- key: TRUEDATA_LIVE_PORT
  scope: RUN_AND_BUILD_TIME
  value: "8084"

- key: TRUEDATA_IS_SANDBOX
  scope: RUN_AND_BUILD_TIME
  value: "false"

- key: TRUEDATA_LOG_LEVEL
  scope: RUN_AND_BUILD_TIME
  value: INFO

- key: TRUEDATA_DATA_TIMEOUT
  scope: RUN_AND_BUILD_TIME
  value: "60"

- key: TRUEDATA_RETRY_ATTEMPTS
  scope: RUN_AND_BUILD_TIME
  value: "3"

- key: TRUEDATA_RETRY_DELAY
  scope: RUN_AND_BUILD_TIME
  value: "5"

- key: TRUEDATA_MAX_CONNECTION_ATTEMPTS
  scope: RUN_AND_BUILD_TIME
  value: "3"
```

#### **Redis Configuration:**
```yaml
- key: REDIS_DB
  scope: RUN_AND_BUILD_TIME
  value: "0"
```

#### **API Configuration:**
```yaml
- key: API_HOST
  scope: RUN_AND_BUILD_TIME
  value: 0.0.0.0

- key: API_PORT
  scope: RUN_AND_BUILD_TIME
  value: "8000"

- key: API_DEBUG
  scope: RUN_AND_BUILD_TIME
  value: "false"

- key: ROOT_PATH
  scope: RUN_AND_BUILD_TIME
  value: /api
```

#### **WebSocket Configuration:**
```yaml
- key: WS_MAX_CONNECTIONS
  scope: RUN_AND_BUILD_TIME
  value: "1000"

- key: WS_HEARTBEAT_INTERVAL
  scope: RUN_AND_BUILD_TIME
  value: "30"

- key: WS_CONNECTION_TIMEOUT
  scope: RUN_AND_BUILD_TIME
  value: "60"
```

#### **Trading Configuration:**
```yaml
- key: PAPER_TRADING
  scope: RUN_AND_BUILD_TIME
  value: "true"

- key: PAPER_TRADING_ENABLED
  scope: RUN_AND_BUILD_TIME
  value: "true"

- key: AUTONOMOUS_TRADING_ENABLED
  scope: RUN_AND_BUILD_TIME
  value: "true"
```

#### **Performance Configuration:**
```yaml
- key: MAX_CONNECTIONS
  scope: RUN_AND_BUILD_TIME
  value: "20"

- key: POOL_SIZE
  scope: RUN_AND_BUILD_TIME
  value: "10"

- key: CACHE_TTL
  scope: RUN_AND_BUILD_TIME
  value: "300"
```

#### **Monitoring Configuration:**
```yaml
- key: ENABLE_METRICS
  scope: RUN_AND_BUILD_TIME
  value: "true"

- key: ENABLE_HEALTH_CHECKS
  scope: RUN_AND_BUILD_TIME
  value: "true"

- key: HEALTH_CHECK_INTERVAL
  scope: RUN_AND_BUILD_TIME
  value: "30"
```

#### **Security Configuration:**
```yaml
- key: ENCRYPTION_KEY
  scope: RUN_AND_BUILD_TIME
  value: lulCrXu3nDX6I18WYuPpWcIrgf2IUGAGLS93ZDwczpQ
```

#### **CORS Configuration:**
```yaml
- key: ENABLE_CORS
  scope: RUN_AND_BUILD_TIME
  value: "true"
```

## 🔧 **Update PIP_REQUIREMENTS**

In the `services.api.envs` section, update the `PIP_REQUIREMENTS` to include TrueData:

```yaml
- key: PIP_REQUIREMENTS
  scope: RUN_AND_BUILD_TIME
  value: |-
    fastapi>=0.68.0,<0.69.0
    uvicorn>=0.15.0,<0.16.0
    pydantic>=2.0.0,<3.0.0
    pydantic-settings>=2.0.0,<3.0.0
    sqlalchemy>=1.4.0,<2.0.0
    asyncpg>=0.27.0,<0.28.0
    redis>=4.5.0,<5.0.0
    python-dotenv>=0.19.0,<1.0.0
    psycopg2-binary==2.9.10 --only-binary :all:
    gunicorn>=20.1.0,<21.0.0
    python-jose>=3.3.0,<4.0.0
    python-multipart==0.0.6
    PyJWT>=2.3.0,<3.0.0
    jinja2>=3.0.0,<4.0.0
    truedata-ws>=1.0.0
    websocket-client>=1.8.0
    pandas>=1.5.3
    numpy>=1.24.3
    httpx>=0.25.2
    aiohttp>=3.9.1
    websockets>=12.0
    prometheus-client>=0.19.0
    psutil>=5.9.6
    structlog>=23.2.0
    rich>=13.7.0
    pyyaml>=6.0.1
    bcrypt>=4.0.1
    cryptography>=41.0.7
    kiteconnect>=4.2.0
    yfinance>=0.2.28
```

## 📋 **Step-by-Step Instructions**

### 1. **Access DigitalOcean Dashboard**
   - Go to https://cloud.digitalocean.com/apps
   - Click on your `algoauto` app

### 2. **Remove Old Variables**
   - Go to "Settings" → "Environment Variables"
   - Find and delete:
     - `TRUEDATA_PORT`
     - `TRUEDATA_SANDBOX`

### 3. **Add New Variables**
   - Click "Add Variable" for each new variable listed above
   - Make sure to set the scope to `RUN_AND_BUILD_TIME`

### 4. **Update PIP_REQUIREMENTS**
   - Find the `PIP_REQUIREMENTS` variable in the API service
   - Replace the entire value with the updated requirements above

### 5. **Deploy**
   - Click "Deploy" to trigger a new deployment
   - Monitor the build logs for any errors

## 🎯 **Expected Result**

After making these changes, your app should:
- ✅ Start without import errors
- ✅ Connect to Redis successfully  
- ✅ Load TrueData configuration properly
- ✅ Respond to health checks at `/health/ready`
- ✅ Handle market data requests through TrueData

## 🔍 **Verification**

After deployment, test these endpoints:
- Health check: `https://algoauto-jd32t.ondigitalocean.app/health/ready`
- API docs: `https://algoauto-jd32t.ondigitalocean.app/docs`
- Market data: `https://algoauto-jd32t.ondigitalocean.app/api/market-data/`

The main issue was the mismatch between your old environment variable names (`TRUEDATA_PORT`, `TRUEDATA_SANDBOX`) and the new configuration structure (`TRUEDATA_LIVE_PORT`, `TRUEDATA_IS_SANDBOX`). 