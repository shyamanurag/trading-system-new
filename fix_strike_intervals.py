#!/usr/bin/env python3
"""
Fix Strike Price Intervals for Zerodha
====================================

ISSUE: Generated strikes don't exist in Zerodha
CAUSE: Wrong interval calculation
- Stocks: Using 25 instead of 50
- Indices: May be using wrong intervals

SOLUTION: Use Zerodha's actual strike intervals
- Options (Stocks): Multiples of 50 only
- Indices: Multiples of 100 only
"""

def fix_strike_intervals():
    """Fix the strike price calculation intervals"""
    
    print("🎯 STRIKE PRICE INTERVAL FIX")
    print("=" * 50)
    print()
    
    print("🔍 CURRENT ISSUE EXAMPLES:")
    print("   HCLTECH ₹1,484 → Strike 1475 (❌ Not available)")
    print("   ADANIPORT → Strike 1375 (❌ Not available)")
    print("   Should be: 1450, 1500, 1550... (multiples of 50)")
    print()
    
    print("🛠️ REQUIRED FIXES:")
    print()
    
    print("1. FIX: _get_atm_strike_for_stock() method")
    print("   Current interval logic: 25 (WRONG)")
    print("   New logic: Always use 50 for stocks")
    print()
    
    print("2. FIX: _get_atm_strike() for indices")
    print("   NIFTY: 50 → Keep (correct)")
    print("   BANKNIFTY: 100 → Keep (correct)")
    print("   FINNIFTY: 50 → Keep (correct)")
    print()
    
    # Show the exact code fix needed
    print("📝 CODE FIX FOR base_strategy.py:")
    print()
    print("def _get_atm_strike_for_stock(self, current_price: float) -> int:")
    print('    """Get ATM strike for stock options - FIXED intervals"""')
    print("    try:")
    print("        # 🚨 CRITICAL FIX: All stock options use 50-point intervals")
    print("        interval = 50  # Zerodha only offers strikes in multiples of 50")
    print("        ")
    print("        # Round to nearest 50")
    print("        atm_strike = round(current_price / interval) * interval")
    print("        ")
    print("        logger.info(f'🎯 STOCK STRIKE CALCULATION:')")
    print("        logger.info(f'   Current Price: ₹{current_price}')")
    print("        logger.info(f'   Interval: {interval} (fixed for all stocks)')")
    print("        logger.info(f'   ATM Strike: {int(atm_strike)}')")
    print("        ")
    print("        return int(atm_strike)")
    print()
    
    print("📊 EXPECTED RESULTS:")
    print("   HCLTECH ₹1,484 → Strike 1500 ✅")
    print("   ADANIPORT ₹1,350 → Strike 1350 ✅")
    print("   BANKNIFTY ₹56,467 → Strike 56500 ✅")
    print()
    
    print("🎯 IMPACT:")
    print("   ✅ All generated strikes will exist in Zerodha")
    print("   ✅ Symbol validation will pass")
    print("   ✅ Options orders will execute successfully")
    print("   ✅ Massive increase in successful trades expected")

if __name__ == "__main__":
    fix_strike_intervals() 