# Local PostgreSQL Setup Guide

## Problem Solved

**Issue**: Mismatch between local SQLite and production PostgreSQL causing schema errors and deployment issues.

**Solution**: Use PostgreSQL locally to match production exactly.

## Benefits

✅ **Schema Parity**: Identical database structure between development and production  
✅ **Test Real Constraints**: Test foreign keys, sequences, and PostgreSQL-specific features locally  
✅ **Eliminate Surprises**: No deployment-time database errors  
✅ **Production Debugging**: Test fixes against the same database type  
✅ **Team Consistency**: All developers use the same database setup  

## Quick Setup (Recommended)

### Option 1: Docker Setup (Easiest)

```bash
# 1. Run the setup script
python setup_local_postgresql.py

# 2. Install PostgreSQL driver
pip install psycopg2-binary

# 3. Set environment variables
# Windows PowerShell:
$env:DATABASE_URL="postgresql://trading_user:trading_password@localhost:5432/trading_system"
$env:REDIS_URL="redis://localhost:6379/0"

# Linux/Mac:
export DATABASE_URL="postgresql://trading_user:trading_password@localhost:5432/trading_system"
export REDIS_URL="redis://localhost:6379/0"

# 4. Run the application
python -m src.main
```

### Option 2: Docker Compose (Advanced)

```bash
# 1. Start services
docker-compose up -d postgres redis

# 2. Create schema
python setup_local_postgresql.py --schema-only

# 3. Run application with environment file
python -m src.main --env-file config/local.env
```

## Manual Setup

### 1. Install PostgreSQL Locally

**Windows:**
```bash
# Download from: https://www.postgresql.org/download/windows/
# Or use chocolatey:
choco install postgresql
```

**Mac:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create Database and User

```sql
-- Connect as postgres user
sudo -u postgres psql

-- Create user and database
CREATE USER trading_user WITH PASSWORD 'trading_password';
CREATE DATABASE trading_system OWNER trading_user;
GRANT ALL PRIVILEGES ON DATABASE trading_system TO trading_user;

-- Exit
\q
```

### 3. Update Environment

Create `.env.local`:
```env
DATABASE_URL=postgresql://trading_user:trading_password@localhost:5432/trading_system
REDIS_URL=redis://localhost:6379/0
APP_ENV=development
DEBUG=true
```

### 4. Install Dependencies

```bash
pip install psycopg2-binary
```

## Database Management

### Start/Stop Services (Docker)

```bash
# Start
docker start trading-postgres trading-redis

# Stop  
docker stop trading-postgres trading-redis

# Remove
docker rm trading-postgres trading-redis
```

### Connect to Database

```bash
# Using psql
psql postgresql://trading_user:trading_password@localhost:5432/trading_system

# Using pgAdmin (if installed)
# URL: http://localhost:5050
# Email: admin@trading.com
# Password: admin123
```

### Reset Database

```bash
# Drop and recreate
docker exec -it trading-postgres psql -U trading_user -d postgres -c "DROP DATABASE IF EXISTS trading_system;"
docker exec -it trading-postgres psql -U trading_user -d postgres -c "CREATE DATABASE trading_system;"

# Recreate schema
python setup_local_postgresql.py --schema-only
```

## Migration from SQLite

### 1. Export Existing Data (if any)

```python
# If you have important data in SQLite, export it first
import sqlite3
import json

conn = sqlite3.connect('trading_system.db')
# Export your data as JSON or CSV
```

### 2. Update Code (Already Done)

The schema manager now handles PostgreSQL properly:
- Automatic PRIMARY KEY constraint repair
- Proper SERIAL sequences
- Foreign key constraint validation

### 3. Test the Fix

```bash
# Run the application
python -m src.main

# Check logs - should see:
# ✅ PostgreSQL database configured with SSL requirements
# ✅ Users table already has primary key  
# ✅ Database schema verification completed successfully
```

## Configuration Files

### Updated `src/config/database.py`
- Now defaults to PostgreSQL URL
- Proper constraint handling
- Production parity

### Schema Manager Enhancement
- Added `_fix_users_primary_key()` function
- Automatic constraint repair
- Better error handling

## Troubleshooting

### Connection Refused
```bash
# Check if PostgreSQL is running
docker ps
# or
pg_isready -h localhost -p 5432
```

### Permission Denied
```bash
# Ensure user has proper permissions
docker exec -it trading-postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE trading_system TO trading_user;"
```

### Schema Errors
```bash
# Reset schema
python setup_local_postgresql.py --reset
```

### Port Conflicts
```bash
# Check what's using port 5432
netstat -an | grep 5432
# Kill process or change port in docker command
```

## Benefits Realized

1. **No More Schema Mismatches**: PostgreSQL locally = PostgreSQL in production
2. **Real Constraint Testing**: Foreign keys work the same way
3. **Production Debugging**: Can reproduce production issues locally
4. **Team Consistency**: Everyone uses the same setup
5. **CI/CD Benefits**: Same database in all environments

## Next Steps

1. ✅ Setup PostgreSQL locally
2. ✅ Test the schema fix
3. ✅ Verify paper trading works
4. ✅ Deploy with confidence

The database schema issue that caused your deployment problems will now be caught and fixed locally before deployment! 