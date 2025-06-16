import redis.asyncio as redis
import asyncio
import ssl

async def test_redis_connection():
    try:
        # Create Redis client using URL format
        redis_url = "rediss://default:AVNS_TSCy17L6f9z0CdWgcvW@redis-cache-do-user-23093341-0.k.db.ondigitalocean.com:25061"
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            ssl_cert_reqs=None,
            ssl_check_hostname=False,
            socket_timeout=10,
            socket_connect_timeout=10,
            retry_on_timeout=True
        )
        
        # Test connection
        await client.ping()
        print("✅ Redis connection successful!")
        
        # Test basic operations
        await client.set("test_key", "test_value")
        value = await client.get("test_key")
        print(f"✅ Test value retrieved: {value}")
        
        # Clean up
        await client.delete("test_key")
        await client.close()
        
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_redis_connection()) 