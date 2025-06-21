#!/usr/bin/env python3
"""
Test environment configuration for DigitalOcean deployment
"""

import os
import asyncio
import asyncpg
import redis.asyncio as redis
from datetime import datetime

# Set environment variables for testing
env_vars = {
    'DATABASE_HOST': 'app-81cd3b75-f46c-49f9-8f76-09040fd8fc68-do-user-23093341-0.k.db.ondigitalocean.com',
    'DATABASE_PORT': '25060',
    'DATABASE_NAME': 'defaultdb',
    'DATABASE_USER': 'doadmin',
    'DATABASE_PASSWORD': 'AVNS_LpaPpsdL4CtOii03MnN',
    'DATABASE_SSL': 'require',
    'REDIS_HOST': 'redis-cache-do-user-23093341-0.k.db.ondigitalocean.com',
    'REDIS_PORT': '25061',
    'REDIS_PASSWORD': 'AVNS_TSCy17L6f9z0CdWgcvW',
    'REDIS_USERNAME': 'default',
    'REDIS_SSL': 'true',
    'REDIS_URL': 'rediss://default:AVNS_TSCy17L6f9z0CdWgcvW@redis-cache-do-user-23093341-0.k.db.ondigitalocean.com:25061',
    'DATABASE_URL': 'postgresql://doadmin:AVNS_LpaPpsdL4CtOii03MnN@app-81cd3b75-f46c-49f9-8f76-09040fd8fc68-do-user-23093341-0.k.db.ondigitalocean.com:25060/defaultdb?ssl=true',
    'JWT_SECRET': 'K5ewmaPLwWLzqcFa2ne6dLpk_5YbUa1NC-xR9N8ig74TnENXKUnnK1UTs3xcaE8IRIEMYRVSCN-co2vEPTeq9A',
    'APP_PORT': '8000',
    'PORT': '8000',
    'NODE_ENV': 'production',
    'ENVIRONMENT': 'production'
}

# Set environment variables
for key, value in env_vars.items():
    os.environ[key] = value

async def test_database_connection():
    """Test PostgreSQL connection"""
    print("Testing PostgreSQL connection...")
    try:
        # Use the DATABASE_URL but remove ssl parameter to avoid conflict
        db_url = os.environ['DATABASE_URL'].replace('?ssl=true', '')
        conn = await asyncpg.connect(db_url, ssl='require')
        
        # Test basic query
        version = await conn.fetchval('SELECT version()')
        print(f"✅ PostgreSQL connected successfully!")
        print(f"   Version: {version[:50]}...")
        
        # Test if tables exist
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        if tables:
            print(f"   Found {len(tables)} tables: {[t['table_name'] for t in tables]}")
        else:
            print("   No tables found (this is normal for new database)")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

async def test_redis_connection():
    """Test Redis connection"""
    print("\nTesting Redis connection...")
    try:
        # Use REDIS_URL
        client = redis.from_url(
            os.environ['REDIS_URL'],
            decode_responses=True,
            ssl_cert_reqs=None,
            ssl_check_hostname=False,
            socket_timeout=10,
            socket_connect_timeout=10
        )
        
        # Test connection
        await client.ping()
        print("✅ Redis connected successfully!")
        
        # Test basic operations
        await client.set("test_key", "test_value", ex=60)
        value = await client.get("test_key")
        if value == "test_value":
            print("✅ Redis read/write operations successful!")
        else:
            print("❌ Redis read/write test failed")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

async def test_environment_variables():
    """Test environment variable configuration"""
    print("\nTesting environment variables...")
    
    required_vars = [
        'DATABASE_URL', 'REDIS_URL', 'JWT_SECRET', 
        'APP_PORT', 'ENVIRONMENT', 'NODE_ENV'
    ]
    
    all_good = True
    for var in required_vars:
        if var in os.environ:
            value = os.environ[var]
            if var in ['JWT_SECRET', 'DATABASE_PASSWORD', 'REDIS_PASSWORD']:
                print(f"✅ {var}: {'*' * min(len(value), 10)}...")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
            all_good = False
    
    return all_good

async def main():
    """Run all tests"""
    print("=== DigitalOcean Environment Configuration Test ===")
    print(f"Test timestamp: {datetime.now().isoformat()}")
    
    # Test environment variables
    env_ok = await test_environment_variables()
    
    # Test database connection
    db_ok = await test_database_connection()
    
    # Test Redis connection
    redis_ok = await test_redis_connection()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Environment Variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Database Connection: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"Redis Connection: {'✅ PASS' if redis_ok else '❌ FAIL'}")
    
    if env_ok and db_ok and redis_ok:
        print("\n🎉 All tests passed! Your environment is ready for deployment.")
        print("\nNext steps:")
        print("1. Commit and push your changes to your repository")
        print("2. Redeploy on DigitalOcean App Platform")
        print("3. The routing issues should be resolved with the new main.py")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration before deploying.")

if __name__ == "__main__":
    asyncio.run(main()) 