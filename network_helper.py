#!/usr/bin/env python3
"""
Network Helper for AlgoAuto Trading System
Prevents console hangs by adding proper timeout handling
"""

import requests
import aiohttp
import asyncio
import time
from typing import Optional, Dict, Any
from urllib.parse import urljoin
import sys
from contextlib import asynccontextmanager

class NetworkHelper:
    """Helper class to prevent network-related console hangs"""
    
    def __init__(self, base_url: str = "https://algoauto-9gx56.ondigitalocean.app", timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
        self.session = None
        
    def safe_get(self, endpoint: str, timeout: Optional[int] = None, **kwargs) -> requests.Response:
        """
        Make a safe GET request with proper timeout handling
        Prevents console hangs by adding timeout and error handling
        """
        url = urljoin(self.base_url, endpoint)
        request_timeout = timeout or self.timeout
        
        try:
            print(f"🌐 GET {url} (timeout: {request_timeout}s)")
            response = requests.get(
                url, 
                timeout=request_timeout,
                **kwargs
            )
            print(f"✅ Response: {response.status_code} ({len(response.content)} bytes)")
            return response
            
        except requests.exceptions.Timeout:
            print(f"⏰ Request timed out after {request_timeout}s")
            # Create a mock response to prevent further hangs
            mock_response = requests.Response()
            mock_response.status_code = 408
            mock_response._content = b'{"error": "Request timeout"}'
            return mock_response
            
        except requests.exceptions.ConnectionError:
            print(f"🔌 Connection failed to {url}")
            mock_response = requests.Response()
            mock_response.status_code = 503
            mock_response._content = b'{"error": "Connection failed"}'
            return mock_response
            
        except Exception as e:
            print(f"❌ Request failed: {e}")
            mock_response = requests.Response()
            mock_response.status_code = 500
            mock_response._content = b'{"error": "Request failed"}'
            return mock_response
    
    def safe_post(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None, 
                  timeout: Optional[int] = None, **kwargs) -> requests.Response:
        """
        Make a safe POST request with proper timeout handling
        """
        url = urljoin(self.base_url, endpoint)
        request_timeout = timeout or self.timeout
        
        try:
            print(f"🌐 POST {url} (timeout: {request_timeout}s)")
            response = requests.post(
                url,
                data=data,
                json=json,
                timeout=request_timeout,
                **kwargs
            )
            print(f"✅ Response: {response.status_code} ({len(response.content)} bytes)")
            return response
            
        except requests.exceptions.Timeout:
            print(f"⏰ Request timed out after {request_timeout}s")
            mock_response = requests.Response()
            mock_response.status_code = 408
            mock_response._content = b'{"error": "Request timeout"}'
            return mock_response
            
        except requests.exceptions.ConnectionError:
            print(f"🔌 Connection failed to {url}")
            mock_response = requests.Response()
            mock_response.status_code = 503
            mock_response._content = b'{"error": "Connection failed"}'
            return mock_response
            
        except Exception as e:
            print(f"❌ Request failed: {e}")
            mock_response = requests.Response()
            mock_response.status_code = 500
            mock_response._content = b'{"error": "Request failed"}'
            return mock_response
    
    @asynccontextmanager
    async def async_session(self):
        """Async context manager for aiohttp sessions"""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            yield session
    
    async def async_get(self, endpoint: str, timeout: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """
        Make an async GET request with proper timeout handling
        """
        url = urljoin(self.base_url, endpoint)
        request_timeout = timeout or self.timeout
        
        try:
            print(f"🌐 Async GET {url} (timeout: {request_timeout}s)")
            
            async with self.async_session() as session:
                async with session.get(url, **kwargs) as response:
                    data = await response.json()
                    print(f"✅ Async Response: {response.status}")
                    return {
                        'status': response.status,
                        'data': data,
                        'success': 200 <= response.status < 300
                    }
                    
        except asyncio.TimeoutError:
            print(f"⏰ Async request timed out after {request_timeout}s")
            return {
                'status': 408,
                'data': {'error': 'Request timeout'},
                'success': False
            }
            
        except aiohttp.ClientError as e:
            print(f"🔌 Async connection failed: {e}")
            return {
                'status': 503,
                'data': {'error': 'Connection failed'},
                'success': False
            }
            
        except Exception as e:
            print(f"❌ Async request failed: {e}")
            return {
                'status': 500,
                'data': {'error': 'Request failed'},
                'success': False
            }
    
    def test_connection(self) -> bool:
        """Test if the base URL is reachable"""
        try:
            response = self.safe_get("/health")
            return response.status_code == 200
        except:
            return False
    
    def wait_for_service(self, max_attempts: int = 10, wait_seconds: int = 5) -> bool:
        """Wait for the service to become available"""
        for attempt in range(max_attempts):
            print(f"🔄 Checking service availability (attempt {attempt + 1}/{max_attempts})")
            
            if self.test_connection():
                print("✅ Service is available!")
                return True
            
            if attempt < max_attempts - 1:
                print(f"⏳ Waiting {wait_seconds}s before retry...")
                time.sleep(wait_seconds)
        
        print("❌ Service is not available after all attempts")
        return False

# Global instance for easy usage
network = NetworkHelper()

# Backward compatibility functions
def safe_get(url: str, timeout: int = 10, **kwargs) -> requests.Response:
    """Backward compatible safe GET function"""
    return network.safe_get(url, timeout, **kwargs)

def safe_post(url: str, timeout: int = 10, **kwargs) -> requests.Response:
    """Backward compatible safe POST function"""
    return network.safe_post(url, timeout, **kwargs)

# Helper function for existing test files
def fix_test_requests():
    """
    Monkey patch requests to add timeout by default
    Call this at the beginning of test files to prevent hangs
    """
    original_get = requests.get
    original_post = requests.post
    
    def patched_get(url, **kwargs):
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 10
        return original_get(url, **kwargs)
    
    def patched_post(url, **kwargs):
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 10
        return original_post(url, **kwargs)
    
    requests.get = patched_get
    requests.post = patched_post
    print("🔧 Patched requests with default timeout to prevent hangs")

if __name__ == "__main__":
    # Test the network helper
    print("🧪 Testing Network Helper")
    
    # Test connection
    if network.test_connection():
        print("✅ Connection test passed")
    else:
        print("❌ Connection test failed")
    
    # Test safe GET
    response = network.safe_get("/api/v1/autonomous/status")
    print(f"Status endpoint: {response.status_code}")
    
    # Test async GET
    async def test_async():
        result = await network.async_get("/api/v1/autonomous/status")
        print(f"Async status endpoint: {result['status']}")
    
    asyncio.run(test_async())
    
    print("✅ Network helper test completed") 