#!/bin/bash

# DigitalOcean Deployment Script
# This script helps update your DigitalOcean App Platform configuration

echo "🚀 DigitalOcean Deployment Configuration Script"
echo "================================================"

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "❌ doctl CLI not found. Please install it first:"
    echo "   https://docs.digitalocean.com/reference/doctl/how-to/install/"
    exit 1
fi

# Check if user is authenticated
if ! doctl auth list &> /dev/null; then
    echo "❌ Not authenticated with DigitalOcean. Please run:"
    echo "   doctl auth init"
    exit 1
fi

echo "✅ DigitalOcean CLI authenticated"

# Get app ID (you'll need to provide this)
echo ""
echo "📋 Please provide your DigitalOcean App ID:"
echo "   You can find this in your DigitalOcean App Platform dashboard"
echo "   Or run: doctl apps list"
echo ""
read -p "Enter your App ID: " APP_ID

if [ -z "$APP_ID" ]; then
    echo "❌ App ID is required"
    exit 1
fi

echo ""
echo "🔧 Updating DigitalOcean App Configuration..."
echo ""

# Create a temporary spec file with updated environment variables
cat > temp_app_spec.yaml << 'EOF'
name: algoauto-trading
services:
- name: web
  source_dir: /
  github:
    repo: your-username/your-repo
    branch: main
  run_command: python main.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8000
  routes:
  - path: /
  envs:
  - key: VITE_API_URL
    value: https://algoauto-jd32t.ondigitalocean.app/api
  - key: VITE_WS_URL
    value: wss://algoauto-jd32t.ondigitalocean.app/ws
  - key: VITE_APP_NAME
    value: AlgoAuto Trading
  - key: VITE_APP_VERSION
    value: "1.0.0"
  - key: VITE_APP_ENV
    value: production
  - key: DATABASE_URL
    value: postgresql://doadmin:AVNS_LpaPpsdL4CtOii03MnN@app-81cd3b75-f46c-49f9-8f76-09040fd8fc68-do-user-23093341-0.k.db.ondigitalocean.com:25060/defaultdb?sslmode=require
  - key: DATABASE_HOST
    value: app-81cd3b75-f46c-49f9-8f76-09040fd8fc68-do-user-23093341-0.k.db.ondigitalocean.com
  - key: DATABASE_PORT
    value: "25060"
  - key: DATABASE_NAME
    value: defaultdb
  - key: DATABASE_USER
    value: doadmin
  - key: DATABASE_PASSWORD
    value: AVNS_LpaPpsdL4CtOii03MnN
  - key: DATABASE_SSL
    value: require
  - key: REDIS_URL
    value: rediss://default:AVNS_TSCy17L6f9z0CdWgcvW@redis-cache-do-user-23093341-0.k.db.ondigitalocean.com:25061
  - key: REDIS_HOST
    value: redis-cache-do-user-23093341-0.k.db.ondigitalocean.com
  - key: REDIS_PORT
    value: "25061"
  - key: REDIS_PASSWORD
    value: AVNS_TSCy17L6f9z0CdWgcvW
  - key: REDIS_USERNAME
    value: default
  - key: REDIS_SSL
    value: "true"
  - key: REDIS_DB
    value: "0"
  - key: TRUEDATA_USERNAME
    value: tdwsp697
  - key: TRUEDATA_PASSWORD
    value: shyam@697
  - key: TRUEDATA_LIVE_PORT
    value: "8084"
  - key: TRUEDATA_URL
    value: push.truedata.in
  - key: TRUEDATA_LOG_LEVEL
    value: INFO
  - key: TRUEDATA_IS_SANDBOX
    value: "false"
  - key: TRUEDATA_DATA_TIMEOUT
    value: "60"
  - key: TRUEDATA_RETRY_ATTEMPTS
    value: "3"
  - key: TRUEDATA_RETRY_DELAY
    value: "5"
  - key: TRUEDATA_MAX_CONNECTION_ATTEMPTS
    value: "3"
  - key: ZERODHA_API_KEY
    value: sylcoq492qz6f7ej
  - key: ZERODHA_API_SECRET
    value: jm3h4iejwnxr4ngmma2qxccpkhevo8sy
  - key: ZERODHA_USER_ID
    value: QSW899
  - key: JWT_SECRET
    value: K5ewmaPLwWLzqcFa2ne6dLpk_5YbUa1NC-xR9N8ig74TnENXKUnnK1UTs3xcaE8IRIEMYRVSCN-co2vEPTeq9A
  - key: ENCRYPTION_KEY
    value: lulCrXu3nDX6I18WYuPpWcIrgf2IUGAGLS93ZDwczpQ
  - key: APP_URL
    value: https://algoauto-jd32t.ondigitalocean.app
  - key: FRONTEND_URL
    value: https://algoauto-jd32t.ondigitalocean.app
  - key: NODE_ENV
    value: production
  - key: ENVIRONMENT
    value: production
  - key: DEBUG
    value: "false"
  - key: PYTHONPATH
    value: /workspace
  - key: CORS_ORIGINS
    value: '["https://algoauto-jd32t.ondigitalocean.app", "http://localhost:3000", "http://localhost:5173"]'
  - key: ENABLE_CORS
    value: "true"
  - key: LOG_LEVEL
    value: INFO
  - key: LOG_FORMAT
    value: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  - key: PAPER_TRADING
    value: "true"
  - key: PAPER_TRADING_ENABLED
    value: "true"
  - key: AUTONOMOUS_TRADING_ENABLED
    value: "true"
  - key: MAX_CONNECTIONS
    value: "20"
  - key: POOL_SIZE
    value: "10"
  - key: CACHE_TTL
    value: "300"
  - key: API_HOST
    value: 0.0.0.0
  - key: API_PORT
    value: "8000"
  - key: API_DEBUG
    value: "false"
  - key: ROOT_PATH
    value: /api
  - key: WS_MAX_CONNECTIONS
    value: "1000"
  - key: WS_HEARTBEAT_INTERVAL
    value: "30"
  - key: WS_CONNECTION_TIMEOUT
    value: "60"
  - key: ENABLE_METRICS
    value: "true"
  - key: ENABLE_HEALTH_CHECKS
    value: "true"
  - key: HEALTH_CHECK_INTERVAL
    value: "30"
  health_check:
    http_path: /health/ready
    initial_delay_seconds: 30
    period_seconds: 30
    timeout_seconds: 10
    success_threshold: 1
    failure_threshold: 3
EOF

echo "📝 Created temporary app specification file"
echo ""

echo "⚠️  IMPORTANT: Manual Steps Required"
echo "===================================="
echo ""
echo "1. Go to your DigitalOcean App Platform dashboard"
echo "2. Navigate to your app settings"
echo "3. Go to 'Environment Variables' section"
echo "4. Remove these variables:"
echo "   - TRUEDATA_SANDBOX"
echo "   - TRUEDATA_PORT"
echo ""
echo "5. Add these new variables:"
echo "   - TRUEDATA_LIVE_PORT=8084"
echo "   - TRUEDATA_IS_SANDBOX=false"
echo "   - TRUEDATA_LOG_LEVEL=INFO"
echo "   - TRUEDATA_DATA_TIMEOUT=60"
echo "   - TRUEDATA_RETRY_ATTEMPTS=3"
echo "   - TRUEDATA_RETRY_DELAY=5"
echo "   - TRUEDATA_MAX_CONNECTION_ATTEMPTS=3"
echo "   - REDIS_DB=0"
echo "   - API_HOST=0.0.0.0"
echo "   - API_PORT=8000"
echo "   - API_DEBUG=false"
echo "   - ROOT_PATH=/api"
echo "   - WS_MAX_CONNECTIONS=1000"
echo "   - WS_HEARTBEAT_INTERVAL=30"
echo "   - WS_CONNECTION_TIMEOUT=60"
echo "   - ENABLE_METRICS=true"
echo "   - ENABLE_HEALTH_CHECKS=true"
echo "   - HEALTH_CHECK_INTERVAL=30"
echo ""
echo "6. Update Health Check settings:"
echo "   - Path: /health/ready"
echo "   - Initial delay: 30 seconds"
echo "   - Interval: 30 seconds"
echo "   - Timeout: 10 seconds"
echo ""
echo "7. Click 'Deploy' to trigger a new deployment"
echo ""

echo "🔍 To check deployment status:"
echo "   doctl apps get $APP_ID"
echo ""

echo "📊 To view logs:"
echo "   doctl apps logs $APP_ID"
echo ""

echo "✅ Configuration script completed!"
echo "   Please follow the manual steps above to update your DigitalOcean app."
echo ""

# Clean up
rm -f temp_app_spec.yaml

echo "🧹 Cleaned up temporary files" 