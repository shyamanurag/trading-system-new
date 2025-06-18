#!/usr/bin/env python3
"""
DigitalOcean Environment Variables Setup Script
This script helps format environment variables for DigitalOcean App Platform
"""

import os
import json

def create_digitalocean_env_vars():
    """Create environment variables for DigitalOcean"""
    
    env_vars = {
        # Frontend Configuration
        "VITE_API_URL": "https://algoauto-jd32t.ondigitalocean.app/api",
        "VITE_WS_URL": "wss://algoauto-jd32t.ondigitalocean.app/ws",
        "VITE_APP_NAME": "AlgoAuto Trading",
        "VITE_APP_VERSION": "1.0.0",
        "VITE_APP_ENV": "production",
        
        # Database Configuration
        "DATABASE_URL": "postgresql://doadmin:AVNS_LpaPpsdL4CtOii03MnN@app-81cd3b75-f46c-49f9-8f76-09040fd8fc68-do-user-23093341-0.k.db.ondigitalocean.com:25060/defaultdb?sslmode=require",
        "DATABASE_HOST": "app-81cd3b75-f46c-49f9-8f76-09040fd8fc68-do-user-23093341-0.k.db.ondigitalocean.com",
        "DATABASE_PORT": "25060",
        "DATABASE_NAME": "defaultdb",
        "DATABASE_USER": "doadmin",
        "DATABASE_PASSWORD": "AVNS_LpaPpsdL4CtOii03MnN",
        "DATABASE_SSL": "require",
        
        # Redis Configuration
        "REDIS_URL": "rediss://default:AVNS_TSCy17L6f9z0CdWgcvW@redis-cache-do-user-23093341-0.k.db.ondigitalocean.com:25061",
        "REDIS_HOST": "redis-cache-do-user-23093341-0.k.db.ondigitalocean.com",
        "REDIS_PORT": "25061",
        "REDIS_PASSWORD": "AVNS_TSCy17L6f9z0CdWgcvW",
        "REDIS_USERNAME": "default",
        "REDIS_SSL": "true",
        "REDIS_DB": "0",
        
        # TrueData Configuration (FIXED)
        "TRUEDATA_USERNAME": "tdwsp697",
        "TRUEDATA_PASSWORD": "shyam@697",
        "TRUEDATA_LIVE_PORT": "8084",
        "TRUEDATA_URL": "push.truedata.in",
        "TRUEDATA_LOG_LEVEL": "INFO",
        "TRUEDATA_IS_SANDBOX": "false",
        "TRUEDATA_DATA_TIMEOUT": "60",
        "TRUEDATA_RETRY_ATTEMPTS": "3",
        "TRUEDATA_RETRY_DELAY": "5",
        "TRUEDATA_MAX_CONNECTION_ATTEMPTS": "3",
        
        # Zerodha Configuration
        "ZERODHA_API_KEY": "sylcoq492qz6f7ej",
        "ZERODHA_API_SECRET": "jm3h4iejwnxr4ngmma2qxccpkhevo8sy",
        "ZERODHA_USER_ID": "QSW899",
        
        # Security Configuration
        "JWT_SECRET": "K5ewmaPLwWLzqcFa2ne6dLpk_5YbUa1NC-xR9N8ig74TnENXKUnnK1UTs3xcaE8IRIEMYRVSCN-co2vEPTeq9A",
        "ENCRYPTION_KEY": "lulCrXu3nDX6I18WYuPpWcIrgf2IUGAGLS93ZDwczpQ",
        
        # Application Configuration
        "APP_URL": "https://algoauto-jd32t.ondigitalocean.app",
        "FRONTEND_URL": "https://algoauto-jd32t.ondigitalocean.app",
        "NODE_ENV": "production",
        "ENVIRONMENT": "production",
        "DEBUG": "false",
        "PYTHONPATH": "/workspace",
        
        # CORS and Networking
        "CORS_ORIGINS": '["https://algoauto-jd32t.ondigitalocean.app", "http://localhost:3000", "http://localhost:5173"]',
        "ENABLE_CORS": "true",
        
        # Logging Configuration
        "LOG_LEVEL": "INFO",
        "LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        
        # Trading Configuration
        "PAPER_TRADING": "true",
        "PAPER_TRADING_ENABLED": "true",
        "AUTONOMOUS_TRADING_ENABLED": "true",
        
        # Performance Configuration
        "MAX_CONNECTIONS": "20",
        "POOL_SIZE": "10",
        "CACHE_TTL": "300",
        
        # API Configuration
        "API_HOST": "0.0.0.0",
        "API_PORT": "8000",
        "API_DEBUG": "false",
        "ROOT_PATH": "/api",
        
        # WebSocket Configuration
        "WS_MAX_CONNECTIONS": "1000",
        "WS_HEARTBEAT_INTERVAL": "30",
        "WS_CONNECTION_TIMEOUT": "60",
        
        # Monitoring Configuration
        "ENABLE_METRICS": "true",
        "ENABLE_HEALTH_CHECKS": "true",
        "HEALTH_CHECK_INTERVAL": "30",
        
        # Python Version
        "PYTHON_VERSION": "3.11.2"
    }
    
    return env_vars

def generate_formats():
    """Generate different formats for the environment variables"""
    
    env_vars = create_digitalocean_env_vars()
    
    print("🚀 DigitalOcean Environment Variables Setup")
    print("=" * 50)
    
    # Format 1: Simple key=value format
    print("\n📋 FORMAT 1: Simple Key=Value (for .env file)")
    print("-" * 40)
    for key, value in env_vars.items():
        print(f"{key}={value}")
    
    # Format 2: JSON format for DigitalOcean
    print("\n📋 FORMAT 2: JSON Format (for DigitalOcean API)")
    print("-" * 40)
    json_vars = []
    for key, value in env_vars.items():
        json_vars.append({
            "key": key,
            "value": value,
            "scope": "RUN_AND_BUILD_TIME"
        })
    print(json.dumps(json_vars, indent=2))
    
    # Format 3: YAML format
    print("\n📋 FORMAT 3: YAML Format (for DigitalOcean App Spec)")
    print("-" * 40)
    for key, value in env_vars.items():
        print(f"- key: {key}")
        print(f"  scope: RUN_AND_BUILD_TIME")
        print(f"  value: {value}")
        print()
    
    # Instructions
    print("\n📋 INSTRUCTIONS:")
    print("-" * 40)
    print("1. Go to your DigitalOcean App Platform dashboard")
    print("2. Click on your 'algoauto' app")
    print("3. Go to 'Settings' → 'Environment Variables'")
    print("4. IMPORTANT: Remove these old variables first:")
    print("   - TRUEDATA_PORT")
    print("   - TRUEDATA_SANDBOX")
    print("5. Add each variable using Format 1 (key=value)")
    print("6. Set scope to 'RUN_AND_BUILD_TIME' for all variables")
    print("7. Click 'Deploy' to trigger new deployment")
    
    # Save to files
    print("\n💾 Saving to files...")
    
    # Save simple format
    with open("digitalocean_env_simple.txt", "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    # Save JSON format
    with open("digitalocean_env_json.json", "w") as f:
        json.dump(json_vars, f, indent=2)
    
    print("✅ Files saved:")
    print("   - digitalocean_env_simple.txt (simple format)")
    print("   - digitalocean_env_json.json (JSON format)")

if __name__ == "__main__":
    generate_formats() 