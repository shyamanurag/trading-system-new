#!/usr/bin/env python3
"""
Comprehensive Trading System Test Suite
Tests all critical fixes and system components after market close
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all critical imports work"""
    print("🔍 Testing Critical Imports...")
    try:
        from src.core.risk_manager import RiskManager, GreeksRiskManager
        from src.core.position_tracker import ProductionPositionTracker
        from src.events import EventBus, EventType, TradingEvent
        from src.core.models import Position, OptionType
        from src.core.orchestrator import TradingOrchestrator
        print("✅ All critical imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_risk_manager_initialization():
    """Test RiskManager initialization with all fixes"""
    print("\n🔍 Testing RiskManager Initialization...")
    try:
        from src.core.risk_manager import RiskManager
        from src.core.position_tracker import ProductionPositionTracker
        from src.events import EventBus
        
        # Create test config
        config = {
            'redis': None,  # Test without Redis
            'max_position_size': 0.1,
            'max_daily_loss': 0.02
        }
        
        # Create dependencies - FIXED: No capital parameter
        position_tracker = ProductionPositionTracker()
        event_bus = EventBus()
        
        # Test RiskManager creation
        risk_manager = RiskManager(config, position_tracker, event_bus)
        
        # Check critical attributes
        assert hasattr(risk_manager, '_position_lock'), "Missing _position_lock"
        assert hasattr(risk_manager, '_stats_lock'), "Missing _stats_lock"
        assert hasattr(risk_manager, 'strategy_stats'), "Missing strategy_stats"
        assert hasattr(risk_manager.risk_state, 'portfolio_greeks'), "Missing portfolio_greeks"
        
        print("✅ RiskManager initialization successful")
        print(f"   - Async locks: ✓")
        print(f"   - Strategy stats: ✓")
        print(f"   - Portfolio Greeks: ✓")
        return True
        
    except Exception as e:
        print(f"❌ RiskManager initialization error: {e}")
        return False

def test_position_constructor():
    """Test Position constructor with all required parameters"""
    print("\n🔍 Testing Position Constructor...")
    try:
        from src.core.models import Position, OptionType
        from datetime import datetime
        
        # Test Position creation with all parameters
        position = Position(
            position_id="TEST_001",
            symbol="FINNIFTY-I",
            option_type=OptionType.CALL,
            strike=27000.0,
            quantity=50,
            entry_price=26947.5,
            entry_time=datetime.now(),
            strategy_name="momentum_surfer"
        )
        
        assert position.position_id == "TEST_001"
        assert position.symbol == "FINNIFTY-I"
        assert position.quantity == 50
        
        print("✅ Position constructor successful")
        print(f"   - All required parameters: ✓")
        print(f"   - Option type: {position.option_type}")
        print(f"   - Strike: {position.strike}")
        return True
        
    except Exception as e:
        print(f"❌ Position constructor error: {e}")
        return False

def test_greeks_risk_manager():
    """Test GreeksRiskManager with missing methods"""
    print("\n🔍 Testing GreeksRiskManager...")
    try:
        from src.core.greeks_risk_manager import GreeksRiskManager
        
        # Create GreeksRiskManager
        greeks_manager = GreeksRiskManager()
        
        # Check critical methods exist
        assert hasattr(greeks_manager, 'validate_new_position_greeks'), "Missing validate_new_position_greeks"
        assert hasattr(greeks_manager, 'update_portfolio_greeks'), "Missing update_portfolio_greeks"
        
        print("✅ GreeksRiskManager methods available")
        print(f"   - validate_new_position_greeks: ✓")
        print(f"   - update_portfolio_greeks: ✓")
        return True
        
    except Exception as e:
        print(f"❌ GreeksRiskManager error: {e}")
        return False

async def test_position_sizing():
    """Test position sizing calculation"""
    print("\n🔍 Testing Position Sizing Calculation...")
    try:
        from src.core.risk_manager import RiskManager
        from src.core.position_tracker import ProductionPositionTracker
        from src.events import EventBus
        
        # Create simple test signal class
        class TestSignal:
            def __init__(self):
                self.signal_id = "TEST_SIGNAL_001"
                self.symbol = "FINNIFTY-I"
                self.action = "SELL"
                self.quantity = 50
                self.entry_price = 26947.5
                self.expected_price = 26947.5
                self.stop_loss = 27136.13
                self.target = 26683.42
                self.strategy_name = "momentum_surfer"
                self.confidence = 0.9
        
        # Create test components - FIXED: No capital parameter
        config = {'redis': None}
        position_tracker = ProductionPositionTracker()
        event_bus = EventBus()
        risk_manager = RiskManager(config, position_tracker, event_bus)
        
        # Initialize RiskManager
        await risk_manager.initialize()
        
        # Create test signal
        signal = TestSignal()
        
        # Test position size calculation
        position_size = await risk_manager.calculate_position_size(signal, risk_score=30)
        
        print(f"✅ Position sizing calculation successful")
        print(f"   - Calculated position size: {position_size}")
        print(f"   - Original signal quantity: {signal.quantity}")
        
        return position_size > 0
        
    except Exception as e:
        print(f"❌ Position sizing error: {e}")
        return False

def test_division_by_zero_fixes():
    """Test all division by zero fixes"""
    print("\n🔍 Testing Division by Zero Fixes...")
    try:
        from src.core.risk_manager import DynamicPositionSizer
        
        # Test Kelly calculation with zero avg_loss
        sizer = DynamicPositionSizer()
        
        # This should not crash (avg_loss = 0)
        kelly_result = sizer.calculate_kelly(
            win_rate=0.6,
            avg_win=100.0,
            avg_loss=0.0,  # This would cause division by zero
            capital=1000000
        )
        
        print(f"✅ Division by zero fixes working")
        print(f"   - Kelly with zero avg_loss: {kelly_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Division by zero test error: {e}")
        return False

async def test_signal_validation():
    """Test complete signal validation pipeline"""
    print("\n🔍 Testing Signal Validation Pipeline...")
    try:
        from src.core.risk_manager import RiskManager
        from src.core.position_tracker import ProductionPositionTracker
        from src.events import EventBus
        
        # Create simple test signal class
        class TestSignal:
            def __init__(self):
                self.signal_id = "TEST_VALIDATION_001"
                self.symbol = "FINNIFTY-I"
                self.action = "SELL"
                self.quantity = 50
                self.entry_price = 26947.5
                self.expected_price = 26947.5
                self.stop_loss = 27136.13
                self.target = 26683.42
                self.strategy_name = "momentum_surfer"
                self.confidence = 0.9
        
        # Create test components - FIXED: No capital parameter
        config = {'redis': None}
        position_tracker = ProductionPositionTracker()
        event_bus = EventBus()
        risk_manager = RiskManager(config, position_tracker, event_bus)
        
        # Initialize RiskManager
        await risk_manager.initialize()
        
        # Create test signal
        signal = TestSignal()
        
        # Test signal validation
        validation_result = await risk_manager.validate_signal(signal)
        
        print(f"✅ Signal validation completed")
        print(f"   - Approved: {validation_result.get('approved', False)}")
        print(f"   - Risk score: {validation_result.get('risk_score', 0)}")
        print(f"   - Position size: {validation_result.get('position_size', 0)}")
        print(f"   - Reason: {validation_result.get('reason', 'None')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Signal validation error: {e}")
        return False

def test_trading_event_constructor():
    """Test TradingEvent constructor with event_type"""
    print("\n🔍 Testing TradingEvent Constructor...")
    try:
        from src.events import TradingEvent, EventType
        
        # Test TradingEvent creation - FIXED: Use correct constructor
        event = TradingEvent(
            event_type=EventType.TRADE_SIGNAL,
            data={'test': 'data'}
        )
        
        assert event.type == EventType.TRADE_SIGNAL
        assert event.data == {'test': 'data'}
        
        print("✅ TradingEvent constructor successful")
        print(f"   - Event type: {event.type}")
        return True
        
    except Exception as e:
        print(f"❌ TradingEvent constructor error: {e}")
        return False

async def run_comprehensive_test():
    """Run all comprehensive tests"""
    print("🚀 COMPREHENSIVE TRADING SYSTEM TEST SUITE")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(("Import Tests", test_imports()))
    test_results.append(("RiskManager Initialization", test_risk_manager_initialization()))
    test_results.append(("Position Constructor", test_position_constructor()))
    test_results.append(("GreeksRiskManager", test_greeks_risk_manager()))
    test_results.append(("Position Sizing", await test_position_sizing()))
    test_results.append(("Division by Zero Fixes", test_division_by_zero_fixes()))
    test_results.append(("Signal Validation", await test_signal_validation()))
    test_results.append(("TradingEvent Constructor", test_trading_event_constructor()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"Total Tests: {len(test_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_results)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! System is ready for trading.")
    else:
        print(f"\n⚠️  {failed} tests failed. Review issues before trading.")
    
    return failed == 0

if __name__ == "__main__":
    print(f"Starting comprehensive test at {datetime.now()}")
    success = asyncio.run(run_comprehensive_test())
    sys.exit(0 if success else 1) 