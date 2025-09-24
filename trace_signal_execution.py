#!/usr/bin/env python3
"""
🔍 SIGNAL EXECUTION TRACER
=========================
Traces exactly where signals are getting lost in the execution pipeline
"""

import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def trace_signal_execution():
    """Trace the signal execution pipeline to find where signals are getting lost"""
    
    print("🔍 TRACING SIGNAL EXECUTION PIPELINE")
    print("=" * 50)
    
    try:
        # Import the orchestrator
        from src.core.orchestrator import get_orchestrator_instance
        
        orchestrator = get_orchestrator_instance()
        if not orchestrator:
            print("❌ ISSUE 1: No orchestrator instance available")
            return
        else:
            print("✅ Step 1: Orchestrator instance found")
        
        # Check if trade engine exists
        if not hasattr(orchestrator, 'trade_engine') or not orchestrator.trade_engine:
            print("❌ ISSUE 2: No trade engine in orchestrator")
            return
        else:
            print("✅ Step 2: Trade engine exists")
            print(f"   Trade engine type: {type(orchestrator.trade_engine)}")
        
        # Check if strategies are loaded
        if not hasattr(orchestrator, 'strategies') or not orchestrator.strategies:
            print("❌ ISSUE 3: No strategies loaded")
            return
        else:
            active_strategies = [k for k, v in orchestrator.strategies.items() if v.get('active', False)]
            print(f"✅ Step 3: {len(active_strategies)} active strategies loaded")
            for strategy in active_strategies:
                print(f"   - {strategy}")
        
        # Check signal deduplicator
        if hasattr(orchestrator, 'signal_deduplicator') and orchestrator.signal_deduplicator:
            print("✅ Step 4: Signal deduplicator exists")
        else:
            print("⚠️ Step 4: No signal deduplicator (signals may not be filtered)")
        
        # Check Zerodha client
        if hasattr(orchestrator, 'zerodha_client') and orchestrator.zerodha_client:
            print("✅ Step 5: Zerodha client exists")
            
            # Test Zerodha connection
            try:
                margins = orchestrator.zerodha_client.get_margins_sync()
                if margins and margins.get('equity', {}).get('available', {}).get('live_balance', 0) > 0:
                    balance = margins['equity']['available']['live_balance']
                    print(f"✅ Step 6: Zerodha connected (Balance: ₹{balance:,.2f})")
                else:
                    print("❌ ISSUE 6: Zerodha connected but no balance data")
            except Exception as e:
                print(f"❌ ISSUE 6: Zerodha connection failed: {e}")
        else:
            print("❌ ISSUE 5: No Zerodha client")
            return
        
        # Check if there are any current signals in strategies
        total_signals = 0
        for strategy_key, strategy_info in orchestrator.strategies.items():
            if strategy_info.get('active', False) and 'instance' in strategy_info:
                strategy_instance = strategy_info['instance']
                if hasattr(strategy_instance, 'current_positions'):
                    signals = len([s for s in strategy_instance.current_positions.values() 
                                 if isinstance(s, dict) and s.get('action') != 'HOLD'])
                    total_signals += signals
                    if signals > 0:
                        print(f"📊 {strategy_key}: {signals} signals pending")
        
        if total_signals > 0:
            print(f"✅ Step 7: {total_signals} signals found in strategies")
        else:
            print("⚠️ Step 7: No signals currently pending in strategies")
        
        # Check trade engine initialization
        if hasattr(orchestrator.trade_engine, 'zerodha_client'):
            if orchestrator.trade_engine.zerodha_client:
                print("✅ Step 8: Trade engine has Zerodha client")
            else:
                print("❌ ISSUE 8: Trade engine missing Zerodha client")
        
        # Check order manager
        if hasattr(orchestrator.trade_engine, 'order_manager'):
            if orchestrator.trade_engine.order_manager:
                print("✅ Step 9: Trade engine has order manager")
            else:
                print("⚠️ Step 9: Trade engine has no order manager (will use direct Zerodha)")
        
        # Check rate limiter
        if hasattr(orchestrator.trade_engine, 'rate_limiter'):
            if orchestrator.trade_engine.rate_limiter:
                print("✅ Step 10: Rate limiter exists")
                
                # Check if any symbols are banned
                if hasattr(orchestrator.trade_engine.rate_limiter, 'banned_symbols'):
                    banned = orchestrator.trade_engine.rate_limiter.banned_symbols
                    if banned:
                        print(f"⚠️ WARNING: {len(banned)} symbols are banned: {list(banned)}")
                    else:
                        print("✅ No symbols are banned")
                
                # Check daily order count
                if hasattr(orchestrator.trade_engine.rate_limiter, 'daily_order_count'):
                    daily_count = orchestrator.trade_engine.rate_limiter.daily_order_count
                    daily_limit = orchestrator.trade_engine.rate_limiter.limits.get('daily_max', 1800)
                    print(f"📊 Daily orders: {daily_count}/{daily_limit}")
                    
                    if daily_count >= daily_limit:
                        print("❌ ISSUE 10: Daily order limit reached!")
            else:
                print("❌ ISSUE 10: No rate limiter")
        
        print("\n" + "=" * 50)
        print("🎯 DIAGNOSIS COMPLETE")
        
        # Summary
        print("\n📋 NEXT STEPS:")
        print("1. Check logs for 'SENDING signals to trade engine' messages")
        print("2. Check logs for 'STARTING SIGNAL EXECUTION' messages") 
        print("3. Check logs for rate limiting blocks")
        print("4. Verify signals have proper action/quantity/symbol fields")
        
    except Exception as e:
        print(f"❌ ERROR during diagnosis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(trace_signal_execution())
