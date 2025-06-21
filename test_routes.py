#!/usr/bin/env python3
"""
Test script to check FastAPI route registration locally
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi.testclient import TestClient
from main import app

def test_routes():
    """Test if routes are registered properly"""
    client = TestClient(app)
    
    print("🔍 Testing FastAPI route registration...")
    print("=" * 60)
    
    # Test basic endpoints
    response = client.get("/")
    print(f"✅ / - Status: {response.status_code}")
    
    response = client.get("/health")
    print(f"✅ /health - Status: {response.status_code}")
    
    # Test API endpoints
    response = client.get("/api/v1/auth/test")
    print(f"✅ /api/v1/auth/test - Status: {response.status_code}")
    
    response = client.get("/api/v1/market/indices")
    print(f"✅ /api/v1/market/indices - Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")
    
    response = client.get("/api/v1/market/market-status")
    print(f"✅ /api/v1/market/market-status - Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")
    
    # Test other API endpoints
    response = client.get("/api/v1/dashboard/data")
    print(f"✅ /api/v1/dashboard/data - Status: {response.status_code}")
    
    response = client.get("/api/v1/health/data")
    print(f"✅ /api/v1/health/data - Status: {response.status_code}")
    
    print("=" * 60)
    print("🏁 Local testing complete!")

if __name__ == "__main__":
    test_routes() 