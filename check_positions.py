#!/usr/bin/env python3
"""Quick script to check current Zerodha positions"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from brokers.zerodha import ZerodhaIntegration as ZerodhaClient

async def check_positions():
    """Check current positions"""
    try:
        # Initialize Zerodha client
        zerodha = ZerodhaClient()
        
        # Get current positions
        positions = await zerodha.get_positions()
        
        if not positions:
            print("❌ No positions data available")
            return
            
        print("\n" + "="*60)
        print("📊 CURRENT ZERODHA POSITIONS")
        print("="*60)
        
        all_positions = []
        
        # Check net positions
        if 'net' in positions:
            for pos in positions['net']:
                if pos.get('quantity', 0) != 0:
                    all_positions.append(pos)
        
        # Check day positions
        if 'day' in positions:
            for pos in positions['day']:
                if pos.get('quantity', 0) != 0 and pos not in all_positions:
                    all_positions.append(pos)
        
        if not all_positions:
            print("✅ No open positions")
        else:
            total_pnl = 0.0
            print(f"\n{'Symbol':<15} {'Qty':>8} {'Avg Price':>10} {'LTP':>10} {'P&L':>12} {'P&L %':>8}")
            print("-"*75)
            
            for pos in all_positions:
                symbol = pos.get('tradingsymbol', 'UNKNOWN')
                qty = pos.get('quantity', 0)
                avg_price = float(pos.get('average_price', 0) or pos.get('buy_price', 0) or 0)
                ltp = float(pos.get('last_price', 0) or pos.get('ltp', 0) or 0)
                
                # Calculate P&L
                if qty != 0 and avg_price > 0 and ltp > 0:
                    pnl = (ltp - avg_price) * qty
                    pnl_pct = ((ltp - avg_price) / avg_price) * 100
                else:
                    pnl = float(pos.get('pnl', 0) or pos.get('unrealised', 0) or pos.get('realised', 0) or 0)
                    pnl_pct = 0
                
                total_pnl += pnl
                
                # Highlight MANAPPURAM if it exists
                highlight = "🚨 " if symbol == "MANAPPURAM" else "   "
                
                # Color code P&L
                if pnl < -1000:
                    pnl_str = f"❌ ₹{pnl:,.2f}"
                elif pnl < 0:
                    pnl_str = f"📉 ₹{pnl:,.2f}"
                elif pnl > 0:
                    pnl_str = f"📈 ₹{pnl:,.2f}"
                else:
                    pnl_str = f"   ₹{pnl:,.2f}"
                
                print(f"{highlight}{symbol:<15} {qty:>8} {avg_price:>10.2f} {ltp:>10.2f} {pnl_str:>12} {pnl_pct:>7.2f}%")
            
            print("-"*75)
            print(f"{'TOTAL P&L':<15} {'':<30} {'₹'+str(round(total_pnl,2)):>22}")
            print(f"Total Positions: {len(all_positions)}")
        
        # Check margins
        margins = await zerodha.get_margins()
        if margins and 'equity' in margins:
            available = margins['equity'].get('available', {})
            cash = available.get('cash', 0)
            print(f"\n💰 Available Cash: ₹{cash:,.2f}")
            
    except Exception as e:
        print(f"❌ Error checking positions: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_positions())
