#!/usr/bin/env python3
"""
Windows-Compatible Trading System Startup Script
This script properly starts the trading system on Windows without Redis/TrueData dependencies
"""

import os
import sys
import subprocess
import time
import socket
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_port(port):
    """Check if a port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('', port))
        sock.close()
        return True
    except:
        return False

def set_environment():
    """Set up environment variables for local development"""
    env_vars = {
        'ENVIRONMENT': 'development',
        'REDIS_URL': 'redis://localhost:6379',  # Will work even if Redis isn't running
        'DATABASE_URL': 'postgresql://postgres:password@localhost:5432/trading_system_dev',
        'JWT_SECRET': 'development-secret-key',
        'FRONTEND_URL': 'http://localhost:3000',
        'ALLOWED_ORIGINS': 'http://localhost:3000,http://localhost:3001,http://localhost:8000',
        # Disable external dependencies for development
        'DISABLE_REDIS': 'true',
        'DISABLE_TRUEDATA': 'true',
        'DISABLE_ZERODHA': 'true'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    logger.info("✅ Environment variables set for development")

def start_api_server():
    """Start the FastAPI server using uvicorn directly"""
    logger.info("Starting API Server...")
    
    # Check if port 8000 is available
    if not check_port(8000):
        logger.warning("Port 8000 is already in use")
        return None
    
    # Start uvicorn directly (works on Windows)
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    
    try:
        process = subprocess.Popen(cmd)
        logger.info("✅ API Server started on http://localhost:8000")
        logger.info("📚 API Documentation: http://localhost:8000/docs")
        return process
    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")
        return None

def start_frontend():
    """Start the frontend development server"""
    logger.info("Starting Frontend...")
    
    frontend_path = Path("src/frontend")
    if not frontend_path.exists():
        logger.error("❌ Frontend directory not found")
        return None
    
    # Check for available port
    port = 3000
    if not check_port(port):
        port = 3001
        if not check_port(port):
            logger.error("❌ No available ports for frontend")
            return None
    
    # Use PowerShell to run npm in the frontend directory
    cmd = f'cd "{frontend_path}" ; npm run dev'
    
    try:
        process = subprocess.Popen(
            ["powershell", "-Command", cmd],
            shell=False
        )
        logger.info(f"✅ Frontend started on http://localhost:{port}")
        return process
    except Exception as e:
        logger.error(f"❌ Failed to start frontend: {e}")
        return None

def main():
    """Main startup function"""
    print("=" * 60)
    print("🚀 TRADING SYSTEM STARTUP (Windows)")
    print("=" * 60)
    
    # Set environment variables
    set_environment()
    
    # Start services
    processes = []
    
    # Start API server
    api_process = start_api_server()
    if api_process:
        processes.append(api_process)
        time.sleep(3)  # Give API time to start
    
    # Start frontend
    frontend_process = start_frontend()
    if frontend_process:
        processes.append(frontend_process)
    
    if not processes:
        logger.error("❌ No services could be started")
        return
    
    print("\n" + "=" * 60)
    print("✅ SYSTEM STARTED SUCCESSFULLY!")
    print("=" * 60)
    print("\n📍 Access Points:")
    print("   - Frontend: http://localhost:3000 (or 3001)")
    print("   - API: http://localhost:8000")
    print("   - API Docs: http://localhost:8000/docs")
    print("\n⚠️  Note: Running without Redis/TrueData - using mock data")
    print("\n🛑 Press Ctrl+C to stop all services")
    print("=" * 60)
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        for process in processes:
            process.terminate()
        print("✅ All services stopped")

if __name__ == "__main__":
    main() 