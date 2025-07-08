#!/usr/bin/env python3
"""
Debug Elite Recommendations Scoring
"""
import json
import requests

def test_scoring_logic():
    """Test the scoring logic locally"""
    
    # Test data similar to what we get from the API
    test_symbols = {
        "RELIANCE": {"current_price": 1519.3, "volume": 6018616, "change_percent": 0},
        "HDFCBANK": {"current_price": 1987.4, "volume": 5565168, "change_percent": 0},
        "TCS": {"current_price": 3403.6, "volume": 2030470, "change_percent": 0},
        "ICICIBANK": {"current_price": 1425.6, "volume": 7485305, "change_percent": 0},
        "BAJFINANCE": {"current_price": 909.05, "volume": 6231567, "change_percent": 0}
    }
    
    min_confluence_score = 7.5
    
    for symbol, data in test_symbols.items():
        current_price = data["current_price"]
        volume = data["volume"]
        change_pct = data.get("change_percent", 0)
        
        # Enhanced analysis based on real current data
        price_action_score = 8.0  # Base score for having real data
        volume_analysis = 8.5 if volume > 100000 else 7.5  # Volume-based score
        
        # Fixed momentum scoring - handle zero change_percent case
        if abs(change_pct) < 0.01:  # Near zero change
            momentum_score = 8.0  # Neutral momentum
        else:
            momentum_score = 8.0 + (abs(change_pct) * 0.2)  # Momentum from real change
        
        # Technical strength based on price levels
        price_strength = 8.0 + (volume / 1000000 * 0.5)  # Price strength from volume
        
        # Ensure scores are within bounds
        momentum_score = max(7.0, min(10.0, momentum_score))
        price_strength = max(7.0, min(10.0, price_strength))
        
        confluence_score = (price_action_score + volume_analysis + momentum_score + price_strength) / 4
        
        print(f"\n{symbol}:")
        print(f"  Current Price: ₹{current_price:,.2f}")
        print(f"  Volume: {volume:,}")
        print(f"  Change %: {change_pct}")
        print(f"  Price Action Score: {price_action_score}")
        print(f"  Volume Analysis: {volume_analysis}")
        print(f"  Momentum Score: {momentum_score}")
        print(f"  Price Strength: {price_strength}")
        print(f"  Confluence Score: {confluence_score:.2f}")
        print(f"  Meets Threshold ({min_confluence_score}): {'YES' if confluence_score >= min_confluence_score else 'NO'}")

def test_real_api():
    """Test the real API"""
    try:
        print("\nTesting Real Market Data API...")
        response = requests.get("https://algoauto-9gx56.ondigitalocean.app/api/v1/market-data")
        if response.status_code == 200:
            data = response.json()
            print(f"API Success: {data.get('success')}")
            print(f"Symbol count: {data.get('symbol_count', 0)}")
            
            # Check specific symbols
            symbols_to_check = ["RELIANCE", "HDFCBANK", "TCS", "ICICIBANK", "BAJFINANCE"]
            for symbol in symbols_to_check:
                if symbol in data.get('data', {}):
                    symbol_data = data['data'][symbol]
                    print(f"{symbol}: Price={symbol_data.get('current_price')}, Volume={symbol_data.get('volume')}")
                else:
                    print(f"{symbol}: NOT FOUND in API data")
        else:
            print(f"API Error: {response.status_code}")
            
    except Exception as e:
        print(f"API Test Error: {e}")

if __name__ == "__main__":
    print("Elite Recommendations Debug")
    print("=" * 50)
    
    test_scoring_logic()
    test_real_api() 