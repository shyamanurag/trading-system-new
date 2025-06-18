# TrueData Installation Guide for Trading System

## What is TrueData?

TrueData is a comprehensive market data provider for Indian markets offering:
- Real-time market data
- Historical data
- Options chain data
- WebSocket streaming
- Technical indicators

## Available TrueData Packages

### 1. truedata-ws (Recommended)
- **Package**: `truedata-ws`
- **Description**: WebSocket-based TrueData client
- **Install**: `pip install truedata-ws`
- **Documentation**: https://pypi.org/project/truedata-ws/

### 2. truedata (Legacy)
- **Package**: `truedata`
- **Description**: Legacy TrueData client
- **Install**: `pip install truedata`
- **Status**: May have compatibility issues

### 3. truedata-python (GitHub)
- **Repository**: https://github.com/truedata/truedata-python
- **Install**: `pip install git+https://github.com/truedata/truedata-python.git`

## Installation Steps

### Step 1: Install TrueData Package

```bash
# Recommended: Install truedata-ws
pip install truedata-ws

# Alternative: Install legacy package
pip install truedata

# Alternative: Install from GitHub
pip install git+https://github.com/truedata/truedata-python.git
```

### Step 2: Get TrueData Credentials

1. Visit: https://truedata.in/
2. Sign up for an account
3. Get your credentials:
   - Username
   - Password
   - API Key (if required)

### Step 3: Test Installation

```python
# Test script
try:
    from truedata_ws import TD_live, TD_hist
    print("✅ TrueData WebSocket package installed successfully")
except ImportError:
    try:
        from truedata import TD_live, TD_hist
        print("✅ TrueData legacy package installed successfully")
    except ImportError:
        print("❌ TrueData not installed")
```

## Configuration Files

### 1. TrueData Configuration (`config/truedata_config.py`)

```python
# TrueData Configuration
TRUEDATA_CONFIG = {
    'username': 'your_username',
    'password': 'your_password',
    'live_port': 8084,
    'url': 'push.truedata.in',
    'log_level': 'INFO',
    'is_sandbox': False,
    'data_timeout': 60,
    'retry_attempts': 3,
    'retry_delay': 5,
    'redis_host': 'localhost',
    'redis_port': 6379,
    'redis_db': 0
}
```

### 2. Environment Variables (`.env`)

```env
# TrueData Configuration
TRUEDATA_USERNAME=your_username
TRUEDATA_PASSWORD=your_password
TRUEDATA_LIVE_PORT=8084
TRUEDATA_URL=push.truedata.in
TRUEDATA_LOG_LEVEL=INFO
TRUEDATA_IS_SANDBOX=false

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## Usage Examples

### 1. Basic Connection

```python
from truedata_ws import TD_live, TD_hist

# Initialize clients
live_client = TD_live(
    username='your_username',
    password='your_password',
    live_port=8084
)

hist_client = TD_hist(
    username='your_username',
    password='your_password'
)

# Connect
live_client.connect()
```

### 2. Get Market Data

```python
# Get live data
symbols = ['NIFTY-I', 'BANKNIFTY-I', 'RELIANCE']
live_client.start_live_data(symbols)

# Get historical data
from datetime import datetime, timedelta

data = hist_client.get_historical_data(
    symbol='NIFTY-I',
    start_time=datetime.now() - timedelta(days=1),
    end_time=datetime.now(),
    bar_size='1 min'
)
```

### 3. Get Options Chain

```python
# Get options chain
chain = live_client.get_option_chain('NIFTY')
print(chain)
```

## Integration with Trading System

### 1. Updated TrueData Provider

The `data/truedata_provider.py` file has been updated to:
- Handle missing TrueData gracefully
- Support multiple TrueData packages
- Provide better error messages
- Include fallback mechanisms

### 2. WebSocket Manager Integration

TrueData integrates with the WebSocket manager for:
- Real-time data streaming
- Market data distribution
- Redis caching
- Event broadcasting

### 3. Configuration Management

TrueData configuration is managed through:
- Environment variables
- Configuration files
- Runtime settings

## Troubleshooting

### Common Issues

1. **Import Error**: TrueData not installed
   ```bash
   pip install truedata-ws
   ```

2. **Connection Error**: Check credentials
   - Verify username/password
   - Check network connection
   - Ensure account is active

3. **Port Issues**: Change live_port
   ```python
   live_client = TD_live(
       username='your_username',
       password='your_password',
       live_port=8086  # Try different port
   )
   ```

4. **Authentication Error**: Check account status
   - Verify account is not suspended
   - Check subscription status
   - Contact TrueData support

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Initialize with debug
live_client = TD_live(
    username='your_username',
    password='your_password',
    log_level=logging.DEBUG
)
```

## Testing TrueData Installation

### 1. Basic Test Script

```python
# test_truedata.py
import asyncio
from datetime import datetime, timedelta

async def test_truedata():
    try:
        from truedata_ws import TD_live, TD_hist
        
        # Test connection
        live_client = TD_live(
            username='your_username',
            password='your_password'
        )
        
        live_client.connect()
        print("✅ TrueData connection successful")
        
        # Test historical data
        hist_client = TD_hist(
            username='your_username',
            password='your_password'
        )
        
        data = hist_client.get_historical_data(
            symbol='NIFTY-I',
            start_time=datetime.now() - timedelta(days=1),
            end_time=datetime.now(),
            bar_size='1 min'
        )
        
        print(f"✅ Historical data retrieved: {len(data)} records")
        
    except Exception as e:
        print(f"❌ TrueData test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_truedata())
```

### 2. Integration Test

```python
# test_truedata_integration.py
import asyncio
from data.truedata_provider import TrueDataProvider

async def test_integration():
    config = {
        'username': 'your_username',
        'password': 'your_password',
        'live_port': 8084,
        'log_level': 'INFO'
    }
    
    try:
        provider = TrueDataProvider(config)
        await provider.connect()
        print("✅ TrueData provider integration successful")
        
        # Test market data subscription
        symbols = ['NIFTY-I', 'BANKNIFTY-I']
        await provider.subscribe_market_data(symbols)
        print("✅ Market data subscription successful")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_integration())
```

## Security Considerations

### 1. Credential Management
- Store credentials in environment variables
- Never commit credentials to version control
- Use secure credential storage

### 2. Network Security
- Use HTTPS connections
- Implement proper authentication
- Monitor for unauthorized access

### 3. Data Security
- Encrypt sensitive data
- Implement access controls
- Regular security audits

## Performance Optimization

### 1. Connection Pooling
- Reuse connections
- Implement connection pooling
- Monitor connection health

### 2. Caching
- Cache frequently accessed data
- Use Redis for caching
- Implement cache invalidation

### 3. Error Handling
- Implement retry mechanisms
- Handle connection failures
- Log errors for debugging

## Support and Resources

### 1. Documentation
- TrueData API Documentation
- WebSocket Protocol Guide
- Integration Examples

### 2. Community
- TrueData Community Forum
- GitHub Issues
- Stack Overflow

### 3. Support
- TrueData Support Email
- Technical Support
- Account Management

## Next Steps

1. Install TrueData package: `pip install truedata-ws`
2. Configure credentials in `.env` file
3. Test installation with provided scripts
4. Integrate with trading system
5. Monitor performance and errors

## Files Created/Updated

- ✅ `data/truedata_provider.py` - Enhanced with better error handling
- ✅ `config/truedata_config.py` - Configuration template
- ✅ `.env` - Environment variables template
- ✅ `test_truedata.py` - Basic test script
- ✅ `test_truedata_integration.py` - Integration test
- ✅ `TRUEDATA_INSTALLATION_GUIDE.md` - This guide

---

**Note**: Replace `your_username` and `your_password` with your actual TrueData credentials. 