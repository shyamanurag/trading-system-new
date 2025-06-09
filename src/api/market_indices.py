"""
Market Indices API endpoints for live market data
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
import random
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Mock data for demonstration (replace with real TrueData integration)
MARKET_INDICES = {
    "NIFTY50": {"base": 22000, "volatility": 0.02},
    "SENSEX": {"base": 72000, "volatility": 0.02},
    "BANKNIFTY": {"base": 48000, "volatility": 0.03},
    "FINNIFTY": {"base": 21000, "volatility": 0.025}
}

def generate_market_data(index_name: str, base_value: float, volatility: float) -> Dict[str, Any]:
    """Generate realistic market data for an index"""
    # Simulate market movement
    change_percent = random.uniform(-volatility, volatility)
    change = base_value * change_percent
    current_value = base_value + change
    
    # Generate high/low based on volatility
    daily_range = base_value * volatility * 2
    high = current_value + random.uniform(0, daily_range/2)
    low = current_value - random.uniform(0, daily_range/2)
    
    # Ensure current is within high/low
    current_value = max(low, min(high, current_value))
    
    return {
        "value": round(current_value, 2),
        "change": round(change, 2),
        "changePercent": round(change_percent * 100, 2),
        "volume": random.randint(1000000, 5000000),
        "high": round(high, 2),
        "low": round(low, 2),
        "open": round(base_value, 2),
        "previousClose": round(base_value, 2),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/indices")
async def get_market_indices():
    """Get current market indices data"""
    try:
        indices_data = {}
        for index_name, config in MARKET_INDICES.items():
            indices_data[index_name] = generate_market_data(
                index_name, 
                config["base"], 
                config["volatility"]
            )
        
        return {
            "success": True,
            "data": indices_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching market indices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/movers")
async def get_top_movers():
    """Get top gainers and losers"""
    try:
        # Mock data for top movers
        stocks = [
            {"symbol": "RELIANCE", "name": "Reliance Industries", "sector": "Energy"},
            {"symbol": "TCS", "name": "Tata Consultancy Services", "sector": "IT"},
            {"symbol": "HDFC", "name": "HDFC Bank", "sector": "Banking"},
            {"symbol": "INFY", "name": "Infosys", "sector": "IT"},
            {"symbol": "ICICIBANK", "name": "ICICI Bank", "sector": "Banking"},
            {"symbol": "SBIN", "name": "State Bank of India", "sector": "Banking"},
            {"symbol": "BHARTIARTL", "name": "Bharti Airtel", "sector": "Telecom"},
            {"symbol": "ITC", "name": "ITC Limited", "sector": "FMCG"},
            {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank", "sector": "Banking"},
            {"symbol": "LT", "name": "Larsen & Toubro", "sector": "Infrastructure"}
        ]
        
        # Generate random price movements
        movers = []
        for stock in stocks:
            change_percent = random.uniform(-5, 5)
            price = random.uniform(500, 5000)
            movers.append({
                **stock,
                "price": round(price, 2),
                "changePercent": round(change_percent, 2),
                "change": round(price * change_percent / 100, 2),
                "volume": random.randint(100000, 10000000)
            })
        
        # Sort by change percentage
        movers.sort(key=lambda x: x["changePercent"], reverse=True)
        
        return {
            "success": True,
            "data": {
                "gainers": [m for m in movers if m["changePercent"] > 0][:5],
                "losers": [m for m in movers if m["changePercent"] < 0][:5]
            }
        }
    except Exception as e:
        logger.error(f"Error fetching top movers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sectors")
async def get_sector_performance():
    """Get sector-wise performance"""
    try:
        sectors = [
            {"name": "Banking", "value": random.uniform(-3, 3)},
            {"name": "IT", "value": random.uniform(-3, 3)},
            {"name": "Pharma", "value": random.uniform(-3, 3)},
            {"name": "Auto", "value": random.uniform(-3, 3)},
            {"name": "FMCG", "value": random.uniform(-3, 3)},
            {"name": "Metal", "value": random.uniform(-3, 3)},
            {"name": "Realty", "value": random.uniform(-3, 3)},
            {"name": "Energy", "value": random.uniform(-3, 3)},
            {"name": "Telecom", "value": random.uniform(-3, 3)},
            {"name": "Infrastructure", "value": random.uniform(-3, 3)}
        ]
        
        # Add size for treemap visualization
        for sector in sectors:
            sector["size"] = random.randint(1000, 5000)
            sector["value"] = round(sector["value"], 2)
        
        return {
            "success": True,
            "data": sectors
        }
    except Exception as e:
        logger.error(f"Error fetching sector performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity")
async def get_market_activity():
    """Get recent market activity"""
    try:
        activities = []
        symbols = ["RELIANCE", "TCS", "HDFC", "INFY", "ICICIBANK"]
        
        for i in range(10):
            activity = {
                "symbol": random.choice(symbols),
                "type": random.choice(["buy", "sell"]),
                "quantity": random.randint(100, 1000),
                "price": round(random.uniform(1000, 3000), 2),
                "time": (datetime.now() - timedelta(minutes=i)).strftime("%H:%M:%S"),
                "latency": random.randint(10, 100)
            }
            activities.append(activity)
        
        return {
            "success": True,
            "data": activities
        }
    except Exception as e:
        logger.error(f"Error fetching market activity: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 