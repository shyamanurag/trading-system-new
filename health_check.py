#!/usr/bin/env python3
"""
Health Check Script for DigitalOcean App Platform
Verifies the application is ready to receive traffic
"""

import asyncio
import aiohttp
import sys
import os

async def check_health():
    """Check if the application is healthy"""
    port = os.getenv('APP_PORT', '8000')
    # Use the new database-independent endpoint for deployment checks
    health_url = f"http://0.0.0.0:{port}/health/ready"
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(health_url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data.get('status', 'unknown')}")
                    return True
                else:
                    print(f"❌ Health check failed: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

async def main():
    """Main health check"""
    print("🏥 Running health check...")
    
    # Wait for application to start
    await asyncio.sleep(5)
    
    # Check health multiple times
    for attempt in range(3):
        if await check_health():
            print("🎉 Application is healthy!")
            sys.exit(0)
        
        if attempt < 2:
            print(f"⏳ Retrying health check in 5 seconds... (attempt {attempt + 2}/3)")
            await asyncio.sleep(5)
    
    print("💥 Health check failed after 3 attempts")
    sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 
