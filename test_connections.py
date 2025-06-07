#!/usr/bin/env python3
"""
Database & Redis Connection Test Script
Tests connectivity to DigitalOcean managed databases
"""

import asyncio
import asyncpg
import redis.asyncio as redis
import os
import ssl
from pathlib import Path

# Load environment variables
def load_env():
    env_file = Path('config/production.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

async def test_postgresql():
    """Test PostgreSQL connection"""
    print("🔍 Testing PostgreSQL connection...")
    
    try:
        # Get connection parameters
        host = os.getenv('DATABASE_HOST')
        port = int(os.getenv('DATABASE_PORT', 25060))
        database = os.getenv('DATABASE_NAME')
        user = os.getenv('DATABASE_USER')
        password = os.getenv('DATABASE_PASSWORD')
        
        print(f"📍 Connecting to: {host}:{port}/{database}")
        
        # Create SSL context for DigitalOcean
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Connect to database
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            ssl=ssl_context,
            command_timeout=10
        )
        
        # Test basic query
        version = await conn.fetchval('SELECT version()')
        print(f"✅ PostgreSQL connected successfully!")
        print(f"📊 Version: {version[:50]}...")
        
        # Test table creation
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS connection_test (
                id SERIAL PRIMARY KEY,
                test_time TIMESTAMP DEFAULT NOW(),
                message TEXT
            )
        ''')
        
        # Insert test record
        await conn.execute(
            "INSERT INTO connection_test (message) VALUES ($1)",
            "Connection test successful"
        )
        
        # Query test record
        count = await conn.fetchval("SELECT COUNT(*) FROM connection_test")
        print(f"📈 Test table has {count} records")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

async def test_redis():
    """Test Redis connection"""
    print("\n🔍 Testing Redis connection...")
    
    try:
        # Get Redis URL
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            # Build from components
            host = os.getenv('REDIS_HOST')
            port = os.getenv('REDIS_PORT', 25061)
            password = os.getenv('REDIS_PASSWORD')
            username = os.getenv('REDIS_USERNAME', 'default')
            redis_url = f"rediss://{username}:{password}@{host}:{port}"
        
        print(f"📍 Connecting to: {redis_url[:50]}...")
        
        # Create Redis client with proper SSL configuration for DigitalOcean
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            ssl_cert_reqs=None,  # DigitalOcean managed Redis - no cert verification needed
            ssl_check_hostname=False,  # Disable hostname checking for managed service
            ssl_ca_certs=None,  # Use system CA bundle
            socket_connect_timeout=15,  # Longer timeout for SSL handshake
            socket_timeout=15,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test connection with SSL handshake
        await client.ping()
        print("✅ Redis SSL connection successful!")
        
        # Test basic operations
        await client.set("connection_test", "success", ex=60)
        value = await client.get("connection_test")
        print(f"📊 Test value: {value}")
        
        # Test list operations (fix async issues)
        list_length = await client.lpush("test_list", "item1", "item2", "item3")
        print(f"📋 List length after push: {list_length}")
        
        list_items = await client.lrange("test_list", 0, -1)
        print(f"📋 Test list items: {list_items}")
        
        # Test hash operations
        await client.hset("test_hash", mapping={"field1": "value1", "field2": "value2"})
        hash_data = await client.hgetall("test_hash")
        print(f"📊 Hash data: {hash_data}")
        
        # Clean up
        await client.delete("connection_test", "test_list", "test_hash")
        
        # Get Redis info to verify SSL and server details
        info = await client.info()
        print(f"📈 Redis version: {info.get('redis_version', 'unknown')}")
        print(f"🔒 SSL enabled: {'Yes' if redis_url.startswith('rediss://') else 'No'}")
        print(f"🌐 Connected clients: {info.get('connected_clients', 'unknown')}")
        
        # Test pipeline for performance
        pipe = client.pipeline()
        pipe.set("pipeline_test_1", "value1")
        pipe.set("pipeline_test_2", "value2")
        pipe.get("pipeline_test_1")
        pipe.get("pipeline_test_2")
        results = await pipe.execute()
        print(f"🚀 Pipeline results: {results}")
        
        # Clean up pipeline test
        await client.delete("pipeline_test_1", "pipeline_test_2")
        
        await client.aclose()
        print("🔐 Redis SSL connection closed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Redis SSL connection failed: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        return False

async def test_all_connections():
    """Test all database connections"""
    print("🚀 Testing DigitalOcean Database Connections")
    print("=" * 50)
    
    # Load environment
    load_env()
    
    # Test connections
    db_success = await test_postgresql()
    redis_success = await test_redis()
    
    print("\n" + "=" * 50)
    print("📊 Connection Test Results:")
    print(f"   PostgreSQL: {'✅ SUCCESS' if db_success else '❌ FAILED'}")
    print(f"   Redis:      {'✅ SUCCESS' if redis_success else '❌ FAILED'}")
    
    if db_success and redis_success:
        print("\n🎉 All connections successful! Ready for deployment.")
        return True
    else:
        print("\n⚠️ Some connections failed. Check credentials and network.")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_all_connections())
    exit(0 if success else 1) 