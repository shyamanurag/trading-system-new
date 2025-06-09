# Local Deployment Guide - Trading System

## Quick Start

### One-Click Start (Windows)
```bash
# Simply double-click or run:
start_local.bat
```

This will:
1. Start the backend server (FastAPI)
2. Start the frontend development server (Vite)
3. Open the application in your browser

## Manual Setup

### Prerequisites
- Python 3.10+ 
- Node.js 18+
- Git

### Step 1: Backend Setup

1. **Create Virtual Environment**
```bash
python -m venv trading_env
```

2. **Activate Virtual Environment**
```bash
# Windows
.\trading_env\Scripts\activate

# Linux/Mac
source trading_env/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt

# Additional dependencies that might be needed:
pip install structlog aiohttp numpy pandas ta backoff schedule psutil plotly kaleido
```

4. **Configure Environment**
```bash
# Copy the production env template
cp config/production.env .env.local

# Edit .env.local and update:
# - JWT_SECRET (change from default)
# - Database settings (optional, uses SQLite by default)
# - Redis settings (optional for local dev)
```

### Step 2: Frontend Setup

1. **Navigate to Frontend Directory**
```bash
cd src/frontend
```

2. **Install Dependencies**
```bash
npm install
```

3. **Return to Root Directory**
```bash
cd ../..
```

### Step 3: Start the Application

#### Option A: Using the Startup Script
```bash
# Windows
start_local.bat

# Linux/Mac (create start_local.sh with similar commands)
```

#### Option B: Manual Start

**Terminal 1 - Backend:**
```bash
# Activate virtual environment
.\trading_env\Scripts\activate  # Windows
source trading_env/bin/activate  # Linux/Mac

# Start backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd src/frontend
npm run dev
```

## Access Points

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws/{user_id}

## Default Credentials

- **Username**: admin
- **Password**: admin123

⚠️ **Important**: Change these credentials before deploying to production!

## Features Available in Local Development

### 1. Trading Dashboard
- Real-time market data (simulated in paper trading mode)
- Position management
- Order placement
- P&L tracking

### 2. User Management
- User creation and management
- Role-based access control
- Performance analytics per user

### 3. Elite Recommendations
- AI-powered trading signals
- Backtesting capabilities
- Risk management

### 4. Real-time Features
- WebSocket connections for live updates
- Market data streaming
- Position updates
- System alerts

### 5. Monitoring
- System health checks
- Performance metrics
- Resource usage monitoring

## Troubleshooting

### Backend Won't Start

1. **Missing Dependencies**
```bash
# Check error message and install missing package
pip install [missing_package]
```

2. **Port Already in Use**
```bash
# Check if port 8000 is in use
netstat -an | findstr :8000

# Kill the process or change port in main.py
```

3. **Database Connection Issues**
- For local development, SQLite is used by default
- Check .env.local for database settings

### Frontend Won't Start

1. **Node Modules Issues**
```bash
cd src/frontend
rm -rf node_modules package-lock.json
npm install
```

2. **Port Conflicts**
- Frontend runs on port 3000 by default
- Check if port is available

### Authentication Issues

1. **Can't Login**
- Ensure backend is running
- Check browser console for errors
- Verify API endpoint is accessible

2. **CORS Errors**
- Backend CORS is configured for localhost:3000
- If using different port, update CORS in main.py

## Development Tips

### 1. API Testing
- Use the Swagger UI at http://localhost:8000/docs
- Test endpoints directly with authentication

### 2. WebSocket Testing
- Connect to ws://localhost:8000/ws/test_user
- Send/receive real-time messages

### 3. Database Management
- SQLite database file: trading_system.db
- Use any SQLite browser to inspect data

### 4. Logging
- Backend logs are in the console
- Set LOG_LEVEL=DEBUG in .env.local for verbose logging

### 5. Hot Reload
- Backend: Automatic with uvicorn
- Frontend: Automatic with Vite

## Next Steps

1. **Customize Configuration**
   - Update trading strategies
   - Configure broker APIs
   - Set risk parameters

2. **Add Real Data Sources**
   - Configure TrueData API
   - Set up Zerodha KiteConnect
   - Enable live market data

3. **Deploy to Production**
   - See PRODUCTION_DEPLOYMENT_GUIDE.md
   - Configure proper secrets
   - Set up monitoring

## Support

For issues or questions:
1. Check the comprehensive audit report
2. Review error logs
3. Consult API documentation
4. Check WebSocket connections

Happy Trading! 🚀 