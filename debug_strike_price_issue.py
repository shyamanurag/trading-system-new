#!/usr/bin/env python3
"""
Debug Strike Price Calculation Issue
==================================

ISSUE: Still generating wrong strikes despite fix
- HCLTECH: Generated 1475 vs Expected ~1480-1485
- System should use real market price, not calculated entry price

ANALYSIS: Check if _get_real_market_price is working
"""

def analyze_strike_issue():
    """Analyze the strike price generation issue"""
    
    print("🔍 STRIKE PRICE ISSUE ANALYSIS")
    print("=" * 50)
    
    # From logs analysis
    print("📊 LOG EVIDENCE:")
    print("   HCLTECH Current Price: ~₹1,484 (from market data logs)")
    print("   Generated Strike: 1475")
    print("   Expected Strike: 1480 or 1485")
    print()
    
    print("🚨 POSSIBLE CAUSES:")
    print()
    print("1. 🔍 DEPLOYMENT LAG:")
    print("   • Current deployment: deploy_1753767950_0bdb6ed2")
    print("   • Our fixes may not be deployed yet")
    print("   • Still using old strike calculation")
    print()
    
    print("2. 🔍 REAL PRICE LOOKUP FAILING:")
    print("   • _get_real_market_price() returns None")
    print("   • Falls back to wrong entry_price")
    print("   • Need better logging to confirm")
    print()
    
    print("3. 🔍 STRIKE INTERVAL CALCULATION:")
    print("   • HCLTECH price: ₹1,484")
    print("   • For price range 1000-2000: interval = 25")
    print("   • Expected: round(1484/25)*25 = round(59.36)*25 = 59*25 = 1475 ✓")
    print("   • Actually this calculation is CORRECT!")
    print()
    
    print("🎯 REAL ISSUE IDENTIFIED:")
    print("   Strike calculation is MATHEMATICALLY CORRECT")
    print("   1484 → interval 25 → strike 1475 ✓")
    print("   Problem is: 1475 strike DOESN'T EXIST in Zerodha!")
    print()
    
    print("💡 SOLUTION NEEDED:")
    print("   Check available strikes and pick nearest")
    print("   Don't just calculate - VALIDATE against Zerodha list")
    print()
    
    # Proposed fix logic
    print("🛠️ PROPOSED FIX:")
    print("""
def _get_nearest_available_strike(self, calculated_strike, available_strikes):
    # Find the closest actual strike from Zerodha list
    closest_strike = min(available_strikes, key=lambda x: abs(x - calculated_strike))
    logger.info(f"Strike correction: {calculated_strike} → {closest_strike} (nearest available)")
    return closest_strike
    """)

if __name__ == "__main__":
    analyze_strike_issue() 