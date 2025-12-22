# PIVOT FIX - Copy this into stock_analysis.py

def calculate_support_resistance(highs: List[float], lows: List[float], 
                                   closes: List[float], current_price: float,
                                   today_high: float = None, today_low: float = None,
                                   yesterday_close: float = None) -> Dict:
    """
    Calculate Support/Resistance using Standard Pivot Points.
    
    For accurate intraday pivots, pass:
        today_high: Today's intraday high (from live_data)
        today_low: Today's intraday low (from live_data)
        yesterday_close: Previous day's close (from live_data.previous_close)
    
    Standard Pivot Formula: PP = (High + Low + Close) / 3
    """
    try:
        if len(closes) < 5:
            return {"error": "Insufficient data"}
        
        # Use live data for accurate intraday pivots (SIMPLE - no API calls!)
        if today_high and today_high > 0 and today_low and today_low > 0 and yesterday_close and yesterday_close > 0:
            pivot_high = today_high
            pivot_low = today_low
            pivot_close = yesterday_close
            data_source = "live_intraday_pivots"
        else:
            # Fallback: estimate from historical candles (less accurate)
            pivot_high = max(highs[-20:]) if len(highs) >= 20 else max(highs)
            pivot_low = min(lows[-20:]) if len(lows) >= 20 else min(lows)
            pivot_close = closes[-2] if len(closes) > 1 else closes[-1]
            data_source = "historical_estimate"
        
        # Calculate Pivot Points (Standard Floor Trader Formula)
        pivot = (pivot_high + pivot_low + pivot_close) / 3
        
        # Standard Pivot Levels
        r1 = 2 * pivot - pivot_low
        r2 = pivot + (pivot_high - pivot_low)
        r3 = pivot_high + 2 * (pivot - pivot_low)
        
        s1 = 2 * pivot - pivot_high
        s2 = pivot - (pivot_high - pivot_low)
        s3 = pivot_low - 2 * (pivot_high - pivot)
        
        # Find swing highs/lows (local extrema)
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(closes) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append(highs[i])
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append(lows[i])
        
        # Find nearest support/resistance
        all_resistance = sorted([r1, r2, r3] + swing_highs)
        all_support = sorted([s1, s2, s3] + swing_lows, reverse=True)
        
        nearest_resistance = None
        nearest_support = None
        
        for level in all_resistance:
            if level > current_price * 1.001:  # At least 0.1% above
                nearest_resistance = level
                break
        
        for level in all_support:
            if level < current_price * 0.999:  # At least 0.1% below
                nearest_support = level
                break
        
        # Price position relative to pivot
        if current_price > r1:
            position = "ABOVE_R1"
        elif current_price > pivot:
            position = "ABOVE_PIVOT"
        elif current_price > s1:
            position = "BELOW_PIVOT"
        else:
            position = "BELOW_S1"
        
        return {
            "pivot": round(pivot, 2),
            "resistance": {
                "r1": round(r1, 2),
                "r2": round(r2, 2),
                "r3": round(r3, 2)
            },
            "support": {
                "s1": round(s1, 2),
                "s2": round(s2, 2),
                "s3": round(s3, 2)
            },
            "nearest_resistance": round(nearest_resistance, 2) if nearest_resistance else None,
            "nearest_support": round(nearest_support, 2) if nearest_support else None,
            "position": position,
            "swing_highs": [round(x, 2) for x in sorted(swing_highs)[-3:]] if swing_highs else [],
            "swing_lows": [round(x, 2) for x in sorted(swing_lows)[:3]] if swing_lows else [],
            "calculation_inputs": {
                "high": round(pivot_high, 2),
                "low": round(pivot_low, 2),
                "close": round(pivot_close, 2),
                "data_source": data_source
            }
        }
        
    except Exception as e:
        return {"error": str(e)}


# ALSO UPDATE THE CALL SITE:
# In get_stock_analysis(), change:
# analysis["support_resistance"] = calculate_support_resistance(
#     highs, lows, closes, current_price
# )
#
# TO:
# analysis["support_resistance"] = calculate_support_resistance(
#     highs, lows, closes, current_price,
#     today_high=float(live_data.get('high', 0) or 0),
#     today_low=float(live_data.get('low', 0) or 0),
#     yesterday_close=float(live_data.get('previous_close', 0) or live_data.get('close', 0) or 0)
# )
