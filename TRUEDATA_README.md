# TrueData Integration for Trading System

This integration provides real-time market data from TrueData using the **official TrueData Python SDK**.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_truedata.txt
```

### 2. Set Environment Variables
```bash
export TRUEDATA_USERNAME="your_username"
export TRUEDATA_PASSWORD="your_password"
```

### 3. Run Standalone Script
```bash
python truedata_standalone.py
```

## 📊 Features

### Real-time Data Types (Official SDK)
- **Tick Data**: Live price updates (`@td_obj.trade_callback`)
- **Bid-Ask Data**: Real-time bid/ask spreads (`@td_obj.bidask_callback`)
- **Greek Data**: Options Greeks (Delta, Gamma, Theta, Vega) (`@td_obj.greek_callback`)
- **Bar Data**: 1-minute and 5-minute OHLCV bars (`@td_obj.one_min_bar_callback`, `@td_obj.five_min_bar_callback`)

### Supported Symbols
- **Indices**: NIFTY, BANKNIFTY, SENSEX
- **Stocks**: RELIANCE, TCS, HDFC, INFY, etc.
- **Options**: All NSE options with Greeks
- **Futures**: All NSE futures
- **Commodities**: CRUDEOIL, GOLD, SILVER, etc.

## 🔧 Integration Options

### Option 1: Standalone Script (Recommended)
Use `truedata_standalone.py` for immediate data collection using the official SDK:

```python
python truedata_standalone.py
```

This uses the **exact same approach** as the official TrueData documentation:
- Official `TD_live` class
- Official callback decorators
- Official `start_live_data()` method
- Official keep-alive mechanism

### Option 2: API Integration
Integrate with your FastAPI trading system:

```python
# Add to main.py
from src.api.truedata_integration import router as truedata_router
app.include_router(truedata_router, prefix="/api/v1")
```

### Option 3: Custom Integration
Use the TrueData client directly:

```python
from src.data.truedata_client import init_truedata_client, get_truedata_client

# Initialize (uses official SDK internally)
client = await init_truedata_client()

# Subscribe to symbols
await client.subscribe_symbols(['NIFTY', 'BANKNIFTY'])

# Get data
data = client.get_market_data('NIFTY')
```

## 📈 API Endpoints

Once integrated with your FastAPI app:

### Connection Management
- `POST /api/v1/truedata/connect` - Connect to TrueData
- `POST /api/v1/truedata/disconnect` - Disconnect from TrueData
- `GET /api/v1/truedata/status` - Get connection status

### Data Management
- `POST /api/v1/truedata/subscribe` - Subscribe to symbols
- `POST /api/v1/truedata/unsubscribe` - Unsubscribe from symbols
- `GET /api/v1/truedata/data/{symbol}` - Get data for specific symbol
- `GET /api/v1/truedata/data` - Get all market data

### WebSocket
- `WS /api/v1/truedata/ws/{symbol}` - Real-time data stream

## 📁 Data Storage

The standalone script saves data to JSON files:

- `tick_data.json` - Live tick data
- `bidask_data.json` - Bid-ask spreads
- `greek_data.json` - Options Greeks
- `one_min_bars.json` - 1-minute OHLCV bars
- `five_min_bars.json` - 5-minute OHLCV bars

## 🔄 Callback System

The integration supports custom callbacks using the official SDK:

```python
from src.data.truedata_client import get_truedata_client

client = get_truedata_client()

def my_tick_callback(symbol, data):
    print(f"New tick for {symbol}: {data}")

client.add_callback('tick', my_tick_callback)
```

## ⚙️ Configuration

### Environment Variables
```bash
TRUEDATA_USERNAME=your_username
TRUEDATA_PASSWORD=your_password
TRUEDATA_PORT=8084  # Optional, default: 8084
TRUEDATA_URL=push.truedata.in  # Optional, default: push.truedata.in
```

### Custom Symbols
Modify the symbols list in `truedata_standalone.py`:

```python
symbols = [
    'CRUDEOIL2506165300CE',  # Crude Oil Call Option
    'CRUDEOIL2506165300PE',  # Crude Oil Put Option
    'NIFTY',                 # Nifty Index
    'BANKNIFTY',             # Bank Nifty Index
    'RELIANCE',              # Reliance Industries
    'TCS',                   # Tata Consultancy Services
    'HDFC',                  # HDFC Bank
    'INFY'                   # Infosys
]
```

## 🛠️ Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check your TrueData credentials
   - Verify internet connection
   - Ensure TrueData account is active

2. **No Data Received**
   - Check if symbols are valid
   - Verify market hours
   - Check subscription status

3. **Import Errors**
   - Install TrueData: `pip install truedata>=7.0.0`
   - Check Python version compatibility

### Debug Mode
Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Data Format Examples

### Tick Data
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "type": "tick",
  "data": {
    "symbol": "NIFTY",
    "ltp": 22450.75,
    "volume": 1250000,
    "change": 125.50,
    "change_percent": 0.56
  }
}
```

### Greek Data
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "type": "greek",
  "data": {
    "symbol": "NIFTY2506165300CE",
    "delta": 0.4567,
    "gamma": 0.0234,
    "theta": -0.0123,
    "vega": 0.0789
  }
}
```

## 🔗 Integration with Trading Strategies

### Example: Moving Average Strategy
```python
def ma_strategy_callback(symbol, data):
    # Calculate moving average
    prices = get_price_history(symbol)
    ma_20 = calculate_ma(prices, 20)
    current_price = data['ltp']
    
    if current_price > ma_20:
        # Buy signal
        place_buy_order(symbol, current_price)
    elif current_price < ma_20:
        # Sell signal
        place_sell_order(symbol, current_price)

client.add_callback('tick', ma_strategy_callback)
```

## 📞 Support

For TrueData-specific issues:
- TrueData Documentation: https://truedata.in/docs
- TrueData Support: support@truedata.in

For integration issues:
- Check the trading system logs
- Verify environment variables
- Test with standalone script first

## 🔄 Next Steps

1. **Test the standalone script** with your credentials
2. **Integrate with your trading system** using the API endpoints
3. **Add custom callbacks** for your trading strategies
4. **Set up data storage** in your database
5. **Implement real-time alerts** based on market conditions

## 🎯 Official SDK Usage

This integration uses the **official TrueData Python SDK** exactly as documented:

```python
from truedata import TD_live
import time
import logging

username = "your_username"
password = "your_password"

port = 8084
url = "push.truedata.in"

td_obj = TD_live(username, password, live_port=port, 
                 log_level=logging.WARNING, url=url, compression=False)

symbols = ['CRUDEOIL2506165300CE', 'CRUDEOIL2506165300PE']
req_ids = td_obj.start_live_data(symbols)
time.sleep(1)

@td_obj.trade_callback
def my_tick_data(tick_data):
    print("tick data", tick_data)

@td_obj.greek_callback
def mygreek_bidask(greek_data):
    print("greek >", greek_data)

# Keep your thread alive
while True:
    time.sleep(120)
``` 