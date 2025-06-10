#!/usr/bin/env python3
"""
Windows-compatible startup script for the trading system
Runs in development mode without external dependencies
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def set_environment_variables():
    """Set environment variables for development mode"""
    env_vars = {
        'ENVIRONMENT': 'development',
        'NODE_ENV': 'development',
        'DEBUG': 'true',
        'PORT': '8000',
        'APP_PORT': '8000',
        'DATABASE_URL': 'postgresql://postgres:password@localhost:5432/trading_system_dev',
        'REDIS_URL': 'redis://localhost:6379',
        'JWT_SECRET': 'development-secret-key',
        'DISABLE_REDIS': 'true',  # Run without Redis
        'DISABLE_TRUEDATA': 'true',  # Run without TrueData
        'DISABLE_ZERODHA': 'true',  # Run without Zerodha
        'PAPER_TRADING': 'true',
        'ENABLE_CORS': 'true',
        'ALLOWED_ORIGINS': 'http://localhost:3000,http://localhost:3001,http://localhost:5173',
        'LOG_LEVEL': 'INFO',
        'PYTHONPATH': str(Path.cwd()),
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        logger.info(f"Set {key}={value}")

def check_port(port):
    """Check if a port is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result != 0

def start_backend():
    """Start the FastAPI backend"""
    logger.info("Starting backend server...")
    
    if not check_port(8000):
        logger.warning("Port 8000 is already in use. Backend might be running.")
        return None
    
    # Use uvicorn directly (works on Windows)
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=Path.cwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        logger.info("Backend server started successfully")
        return process
    except Exception as e:
        logger.error(f"Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the React frontend"""
    logger.info("Starting frontend server...")
    
    frontend_dir = Path("src/frontend")
    if not frontend_dir.exists():
        logger.error("Frontend directory not found")
        return None
    
    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        logger.info("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True)
    
    # Use npm run dev
    cmd = ["npm", "run", "dev"]
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=frontend_dir,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        logger.info("Frontend server started successfully")
        return process
    except Exception as e:
        logger.error(f"Failed to start frontend: {e}")
        return None

def main():
    """Main entry point"""
    logger.info("Starting Trading System (Windows Development Mode)")
    logger.info("=" * 60)
    
    # Set environment variables
    set_environment_variables()
    
    # Start services
    backend_process = start_backend()
    time.sleep(5)  # Wait for backend to start
    
    frontend_process = start_frontend()
    
    if not backend_process and not frontend_process:
        logger.error("Failed to start any services")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Trading System is running!")
    logger.info("Backend: http://localhost:8000")
    logger.info("Frontend: http://localhost:3000 or http://localhost:3001")
    logger.info("API Docs: http://localhost:8000/docs")
    logger.info("Press Ctrl+C to stop all services")
    logger.info("=" * 60)
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process and backend_process.poll() is not None:
                logger.error("Backend process died")
                break
            if frontend_process and frontend_process.poll() is not None:
                logger.error("Frontend process died")
                break
                
    except KeyboardInterrupt:
        logger.info("\nShutting down services...")
        
        # Terminate processes
        if backend_process:
            backend_process.terminate()
            backend_process.wait()
        if frontend_process:
            frontend_process.terminate()
            frontend_process.wait()
            
        logger.info("All services stopped")

if __name__ == "__main__":
    main() 