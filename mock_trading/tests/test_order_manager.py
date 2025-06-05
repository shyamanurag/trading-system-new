"""
Test suite for order management system
"""
import unittest
from datetime import datetime
import pandas as pd
import numpy as np
import time
import threading
from ..order_manager import OrderManager, Order, OrderType, OrderStatus, OrderSide
from ..market_simulator import MarketSimulator
from config.loader import config_loader

class TestOrderManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.config = config_loader.load_config("config.yaml", env="test")
        self.market = MarketSimulator(self.config)
        self.order_manager = OrderManager(self.market, self.config)
        
    def test_order_size_limits(self):
        """Test order size validation"""
        # Test minimum order size
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=0,
                order_type=OrderType.MARKET
            )
            
        # Test maximum order size
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=self.config['trading']['limits']['max_order_size'] + 1,
                order_type=OrderType.MARKET
            )
            
        # Test fractional quantities
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=100.5,
                order_type=OrderType.MARKET
            )
            
        # Test valid order size
        order = self.order_manager.create_order(
            symbol="AAPL",
            quantity=100,
            order_type=OrderType.MARKET
        )
        self.assertEqual(order.quantity, 100)
        
    def test_price_validation(self):
        """Test price validation for different order types"""
        # Test market order price validation
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=100,
                order_type=OrderType.MARKET,
                price=150.00  # Market orders shouldn't have price
            )
            
        # Test limit order price validation
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=100,
                order_type=OrderType.LIMIT,
                price=-150.00  # Invalid negative price
            )
            
        # Test stop order price validation
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=100,
                order_type=OrderType.STOP,
                stop_price=0  # Invalid stop price
            )
            
        # Test valid limit order
        order = self.order_manager.create_order(
            symbol="AAPL",
            quantity=100,
            order_type=OrderType.LIMIT,
            price=150.00
        )
        self.assertEqual(order.price, 150.00)
        
    def test_time_in_force_validation(self):
        """Test time-in-force rules"""
        # Test GTC order
        order = self.order_manager.create_order(
            symbol="AAPL",
            quantity=100,
            order_type=OrderType.LIMIT,
            price=150.00,
            time_in_force="GTC"
        )
        self.assertEqual(order.time_in_force, "GTC")
        
        # Test IOC order
        order = self.order_manager.create_order(
            symbol="AAPL",
            quantity=100,
            order_type=OrderType.LIMIT,
            price=150.00,
            time_in_force="IOC"
        )
        self.assertEqual(order.time_in_force, "IOC")
        
        # Test FOK order
        order = self.order_manager.create_order(
            symbol="AAPL",
            quantity=100,
            order_type=OrderType.LIMIT,
            price=150.00,
            time_in_force="FOK"
        )
        self.assertEqual(order.time_in_force, "FOK")
        
        # Test invalid time-in-force
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=100,
                order_type=OrderType.LIMIT,
                price=150.00,
                time_in_force="INVALID"
            )
            
    def test_account_balance_validation(self):
        """Test account balance validation"""
        # Test insufficient funds
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=1000,
                order_type=OrderType.MARKET,
                price=150.00
            )
            
        # Test valid order within balance
        order = self.order_manager.create_order(
            symbol="AAPL",
            quantity=100,
            order_type=OrderType.MARKET,
            price=150.00
        )
        self.assertIsNotNone(order)
        
    def test_position_limits(self):
        """Test position limit validation"""
        # Test exceeding position limit
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=self.config['trading']['limits']['max_position_size'] + 1,
                order_type=OrderType.MARKET
            )
            
        # Test valid position size
        order = self.order_manager.create_order(
            symbol="AAPL",
            quantity=100,
            order_type=OrderType.MARKET
        )
        self.assertIsNotNone(order)
        
    def test_oco_order_creation(self):
        """Test OCO order creation and cancellation"""
        # Create OCO order
        limit_id, stop_id = self.order_manager.create_oco_order(
            symbol="AAPL",
            quantity=100,
            limit_price=150.00,
            stop_price=145.00
        )
        
        # Verify orders exist
        self.assertIn(limit_id, self.order_manager.orders)
        self.assertIn(stop_id, self.order_manager.orders)
        
        # Verify order linkage
        limit_order = self.order_manager.orders[limit_id]
        stop_order = self.order_manager.orders[stop_id]
        self.assertEqual(limit_order.related_orders, [stop_id])
        self.assertEqual(stop_order.related_orders, [limit_id])
        
        # Test cancellation
        self.order_manager.cancel_order(limit_id)
        self.assertEqual(limit_order.status, OrderStatus.CANCELLED)
        self.assertEqual(stop_order.status, OrderStatus.CANCELLED)
        
    def test_trailing_stop(self):
        """Test trailing stop functionality"""
        # Create trailing stop
        trail_id = self.order_manager.create_trailing_stop(
            symbol="AAPL",
            quantity=100,
            trailing_percent=0.01,
            initial_price=150.00
        )
        
        # Verify initial setup
        self.assertIn(trail_id, self.order_manager.active_trailing_stops)
        initial_stop = self.order_manager.active_trailing_stops[trail_id]['stop_price']
        self.assertEqual(initial_stop, 148.50)  # 150 * (1 - 0.01)
        
        # Test price increase
        self.order_manager.update_trailing_stops("AAPL", 155.00)
        new_stop = self.order_manager.active_trailing_stops[trail_id]['stop_price']
        self.assertEqual(new_stop, 153.45)  # 155 * (1 - 0.01)
        
        # Test stop hit
        self.order_manager.update_trailing_stops("AAPL", 153.00)
        self.assertNotIn(trail_id, self.order_manager.active_trailing_stops)
        
    def test_order_routing(self):
        """Test order routing optimization"""
        # Test market order routing
        market_order = Order(
            order_id=self.order_manager._generate_order_id(),
            symbol="AAPL",
            order_type=OrderType.MARKET,
            quantity=1000
        )
        
        routing = self.order_manager.optimize_order_routing(market_order)
        self.assertIn(routing['strategy'], ['TWAP', 'IMMEDIATE'])
        
        # Test limit order routing
        limit_order = Order(
            order_id=self.order_manager._generate_order_id(),
            symbol="AAPL",
            order_type=OrderType.LIMIT,
            quantity=100,
            price=150.00
        )
        
        routing = self.order_manager.optimize_order_routing(limit_order)
        self.assertIn(routing['strategy'], ['PEGGED', 'LIMIT'])
        
    def test_order_execution(self):
        """Test order execution with different strategies"""
        # Test TWAP execution
        large_order = Order(
            order_id=self.order_manager._generate_order_id(),
            symbol="AAPL",
            order_type=OrderType.MARKET,
            quantity=10000
        )
        
        result = self.order_manager.execute_order(large_order)
        self.assertEqual(result['status'], 'FILLED')
        self.assertIn('executions', result)
        self.assertIn('average_price', result)
        
        # Test immediate execution
        small_order = Order(
            order_id=self.order_manager._generate_order_id(),
            symbol="AAPL",
            order_type=OrderType.MARKET,
            quantity=100
        )
        
        result = self.order_manager.execute_order(small_order)
        self.assertEqual(result['status'], 'FILLED')
        
    def test_order_synchronization(self):
        """Test order synchronization and race conditions"""
        def create_orders():
            for _ in range(10):
                self.order_manager.create_oco_order(
                    symbol="AAPL",
                    quantity=100,
                    limit_price=150.00,
                    stop_price=145.00
                )
                time.sleep(0.01)
        
        # Create multiple threads
        threads = [threading.Thread(target=create_orders) for _ in range(5)]
        
        # Start threads
        for thread in threads:
            thread.start()
            
        # Wait for completion
        for thread in threads:
            thread.join()
            
        # Verify no duplicate order IDs
        order_ids = set()
        for order in self.order_manager.orders.values():
            self.assertNotIn(order.order_id, order_ids)
            order_ids.add(order.order_id)
            
    def test_error_handling(self):
        """Test error handling and edge cases"""
        # Test invalid order cancellation
        with self.assertRaises(ValueError):
            self.order_manager.cancel_order("invalid_id")
            
        # Test invalid trailing stop parameters
        with self.assertRaises(ValueError):
            self.order_manager.create_trailing_stop(
                symbol="AAPL",
                quantity=100,
                trailing_percent=1.5,  # Invalid trailing percentage
                initial_price=150.00
            )
            
        # Test invalid OCO parameters
        with self.assertRaises(ValueError):
            self.order_manager.create_oco_order(
                symbol="AAPL",
                quantity=100,
                limit_price=145.00,  # Limit price below stop price
                stop_price=150.00
            )
            
    def test_advanced_order_types(self):
        """Test advanced order types"""
        # Test bracket order
        bracket_id = self.order_manager.create_bracket_order(
            symbol="AAPL",
            quantity=100,
            entry_price=150.00,
            take_profit_price=160.00,
            stop_loss_price=145.00
        )
        
        self.assertIn(bracket_id, self.order_manager.orders)
        bracket_order = self.order_manager.orders[bracket_id]
        self.assertEqual(len(bracket_order.related_orders), 2)
        
        # Test conditional order
        cond_id = self.order_manager.create_conditional_order(
            symbol="AAPL",
            quantity=100,
            condition="PRICE_ABOVE",
            trigger_price=155.00,
            order_type=OrderType.MARKET
        )
        
        self.assertIn(cond_id, self.order_manager.orders)
        cond_order = self.order_manager.orders[cond_id]
        self.assertEqual(cond_order.trigger_price, 155.00)
        
        # Test scale order
        scale_id = self.order_manager.create_scale_order(
            symbol="AAPL",
            total_quantity=1000,
            num_orders=5,
            price_increment=1.00,
            initial_price=150.00
        )
        
        self.assertIn(scale_id, self.order_manager.orders)
        scale_order = self.order_manager.orders[scale_id]
        self.assertEqual(len(scale_order.child_orders), 5)
        
    def test_execution_strategies(self):
        """Test different execution strategies"""
        # Test VWAP execution
        vwap_order = Order(
            order_id=self.order_manager._generate_order_id(),
            symbol="AAPL",
            order_type=OrderType.MARKET,
            quantity=5000
        )
        
        vwap_result = self.order_manager.execute_vwap(vwap_order)
        self.assertEqual(vwap_result['status'], 'FILLED')
        self.assertIn('vwap_price', vwap_result)
        
        # Test POV execution
        pov_order = Order(
            order_id=self.order_manager._generate_order_id(),
            symbol="AAPL",
            order_type=OrderType.MARKET,
            quantity=3000
        )
        
        pov_result = self.order_manager.execute_pov(pov_order)
        self.assertEqual(pov_result['status'], 'FILLED')
        self.assertIn('participation_rate', pov_result)
        
        # Test implementation shortfall
        is_order = Order(
            order_id=self.order_manager._generate_order_id(),
            symbol="AAPL",
            order_type=OrderType.MARKET,
            quantity=2000
        )
        
        is_result = self.order_manager.execute_implementation_shortfall(is_order)
        self.assertEqual(is_result['status'], 'FILLED')
        self.assertIn('shortfall', is_result)
        
    def test_order_amendment(self):
        """Test order amendment functionality"""
        # Create initial order
        order = self.order_manager.create_order(
            symbol="AAPL",
            quantity=100,
            order_type=OrderType.LIMIT,
            price=150.00
        )
        
        # Test quantity amendment
        amended = self.order_manager.amend_order(
            order_id=order.order_id,
            quantity=200
        )
        self.assertEqual(amended.quantity, 200)
        
        # Test price amendment
        amended = self.order_manager.amend_order(
            order_id=order.order_id,
            price=155.00
        )
        self.assertEqual(amended.price, 155.00)
        
        # Test invalid amendment
        with self.assertRaises(ValueError):
            self.order_manager.amend_order(
                order_id=order.order_id,
                quantity=-100
            )
            
    def test_order_aggregation(self):
        """Test order aggregation and smart order routing"""
        # Create multiple orders
        orders = []
        for i in range(5):
            order = self.order_manager.create_order(
                symbol="AAPL",
                quantity=100,
                order_type=OrderType.LIMIT,
                price=150.00 + i
            )
            orders.append(order)
            
        # Test order aggregation
        aggregated = self.order_manager.aggregate_orders(orders)
        self.assertEqual(aggregated['total_quantity'], 500)
        self.assertIn('average_price', aggregated)
        
        # Test smart order routing
        routed = self.order_manager.smart_order_route(aggregated)
        self.assertIn('venue_allocations', routed)
        self.assertIn('execution_plan', routed)
        
    def test_market_conditions(self):
        """Test order handling under different market conditions"""
        # Test pre-market orders
        pre_market_order = self.order_manager.create_order(
            symbol="AAPL",
            quantity=100,
            order_type=OrderType.LIMIT,
            price=150.00,
            time_in_force="GTC",
            extended_hours=True
        )
        self.assertTrue(pre_market_order.extended_hours)
        
        # Test after-hours orders
        after_hours_order = self.order_manager.create_order(
            symbol="AAPL",
            quantity=100,
            order_type=OrderType.LIMIT,
            price=150.00,
            time_in_force="GTC",
            extended_hours=True
        )
        self.assertTrue(after_hours_order.extended_hours)
        
        # Test market closed
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=100,
                order_type=OrderType.MARKET,
                time_in_force="IOC"  # IOC not allowed when market is closed
            )
            
    def test_risk_limits(self):
        """Test risk limit enforcement"""
        # Test daily loss limit
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=1000,
                order_type=OrderType.MARKET,
                price=150.00
            )
            
        # Test position concentration limit
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=5000,
                order_type=OrderType.MARKET
            )
            
        # Test sector exposure limit
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="MSFT",  # Same sector as AAPL
                quantity=3000,
                order_type=OrderType.MARKET
            )
            
    def test_order_cancellation(self):
        """Test order cancellation scenarios"""
        # Create and cancel limit order
        order = self.order_manager.create_order(
            symbol="AAPL",
            quantity=100,
            order_type=OrderType.LIMIT,
            price=150.00
        )
        
        self.order_manager.cancel_order(order.order_id)
        self.assertEqual(order.status, OrderStatus.CANCELLED)
        
        # Test cancel all orders
        self.order_manager.create_order(
            symbol="AAPL",
            quantity=100,
            order_type=OrderType.LIMIT,
            price=150.00
        )
        self.order_manager.create_order(
            symbol="MSFT",
            quantity=100,
            order_type=OrderType.LIMIT,
            price=250.00
        )
        
        self.order_manager.cancel_all_orders()
        for order in self.order_manager.orders.values():
            self.assertEqual(order.status, OrderStatus.CANCELLED)
            
    def test_order_rejection(self):
        """Test order rejection scenarios"""
        # Test invalid symbol
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="INVALID",
                quantity=100,
                order_type=OrderType.MARKET
            )
            
        # Test invalid order type
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=100,
                order_type="INVALID"
            )
            
        # Test invalid side
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=100,
                order_type=OrderType.MARKET,
                side="INVALID"
            )
            
    def test_order_modification(self):
        """Test order modification scenarios"""
        # Create initial order
        order = self.order_manager.create_order(
            symbol="AAPL",
            quantity=100,
            order_type=OrderType.LIMIT,
            price=150.00
        )
        
        # Test modify quantity
        modified = self.order_manager.modify_order(
            order_id=order.order_id,
            quantity=200
        )
        self.assertEqual(modified.quantity, 200)
        
        # Test modify price
        modified = self.order_manager.modify_order(
            order_id=order.order_id,
            price=155.00
        )
        self.assertEqual(modified.price, 155.00)
        
        # Test modify time in force
        modified = self.order_manager.modify_order(
            order_id=order.order_id,
            time_in_force="IOC"
        )
        self.assertEqual(modified.time_in_force, "IOC")
        
        # Test invalid modification
        with self.assertRaises(ValueError):
            self.order_manager.modify_order(
                order_id=order.order_id,
                quantity=-100
            )

    def test_performance_order_throughput(self):
        """Test order processing throughput"""
        start_time = time.time()
        orders_processed = 0
        
        # Process orders for 5 seconds
        while time.time() - start_time < 5:
            order = self.order_manager.create_order(
                symbol="AAPL",
                quantity=100,
                order_type=OrderType.MARKET
            )
            orders_processed += 1
            
        # Calculate orders per second
        orders_per_second = orders_processed / (time.time() - start_time)
        self.assertGreater(orders_per_second, 100)  # Minimum 100 orders per second
        
    def test_performance_concurrent_orders(self):
        """Test concurrent order processing"""
        def create_orders():
            for _ in range(100):
                self.order_manager.create_order(
                    symbol="AAPL",
                    quantity=100,
                    order_type=OrderType.MARKET
                )
                
        # Create multiple threads
        threads = [threading.Thread(target=create_orders) for _ in range(10)]
        
        # Start threads
        start_time = time.time()
        for thread in threads:
            thread.start()
            
        # Wait for completion
        for thread in threads:
            thread.join()
            
        # Calculate total time
        total_time = time.time() - start_time
        self.assertLess(total_time, 5)  # Should complete within 5 seconds
        
    def test_performance_order_latency(self):
        """Test order processing latency"""
        latencies = []
        
        for _ in range(100):
            start_time = time.time()
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=100,
                order_type=OrderType.MARKET
            )
            latency = time.time() - start_time
            latencies.append(latency)
            
        # Calculate average latency
        avg_latency = sum(latencies) / len(latencies)
        self.assertLess(avg_latency, 0.01)  # Average latency should be less than 10ms
        
    def test_performance_memory_usage(self):
        """Test memory usage under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create large number of orders
        for _ in range(1000):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=100,
                order_type=OrderType.MARKET
            )
            
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024)
        
    def test_security_order_validation(self):
        """Test security of order validation"""
        # Test SQL injection attempt
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL'; DROP TABLE orders; --",
                quantity=100,
                order_type=OrderType.MARKET
            )
            
        # Test XSS attempt
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="<script>alert('xss')</script>",
                quantity=100,
                order_type=OrderType.MARKET
            )
            
        # Test command injection attempt
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL; rm -rf /",
                quantity=100,
                order_type=OrderType.MARKET
            )
            
    def test_security_rate_limiting(self):
        """Test rate limiting functionality"""
        # Test rapid order creation
        for _ in range(100):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=100,
                order_type=OrderType.MARKET
            )
            
        # Should be rate limited after 100 orders
        with self.assertRaises(Exception):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=100,
                order_type=OrderType.MARKET
            )
            
    def test_security_order_authorization(self):
        """Test order authorization"""
        # Test unauthorized order modification
        order = self.order_manager.create_order(
            symbol="AAPL",
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        with self.assertRaises(Exception):
            self.order_manager.modify_order(
                order_id=order.order_id,
                quantity=200,
                user_id="unauthorized_user"
            )
            
        # Test unauthorized order cancellation
        with self.assertRaises(Exception):
            self.order_manager.cancel_order(
                order_id=order.order_id,
                user_id="unauthorized_user"
            )
            
    def test_security_data_validation(self):
        """Test data validation security"""
        # Test invalid order ID format
        with self.assertRaises(ValueError):
            self.order_manager.cancel_order("invalid_id_format")
            
        # Test invalid quantity format
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity="100; DROP TABLE orders",
                order_type=OrderType.MARKET
            )
            
        # Test invalid price format
        with self.assertRaises(ValueError):
            self.order_manager.create_order(
                symbol="AAPL",
                quantity=100,
                order_type=OrderType.LIMIT,
                price="150.00; DROP TABLE orders"
            )
            
    def test_security_audit_logging(self):
        """Test audit logging functionality"""
        # Create and modify an order
        order = self.order_manager.create_order(
            symbol="AAPL",
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        self.order_manager.modify_order(
            order_id=order.order_id,
            quantity=200
        )
        
        self.order_manager.cancel_order(order.order_id)
        
        # Verify audit log entries
        audit_log = self.order_manager.get_audit_log(order.order_id)
        self.assertEqual(len(audit_log), 3)  # Create, modify, cancel
        self.assertEqual(audit_log[0]['action'], 'CREATE')
        self.assertEqual(audit_log[1]['action'], 'MODIFY')
        self.assertEqual(audit_log[2]['action'], 'CANCEL')
        
    def test_security_error_handling(self):
        """Test security error handling"""
        # Test error message sanitization
        try:
            self.order_manager.create_order(
                symbol="AAPL",
                quantity="invalid",
                order_type=OrderType.MARKET
            )
        except Exception as e:
            self.assertNotIn("stack trace", str(e))
            self.assertNotIn("internal error", str(e))
            
        # Test error logging
        error_log = self.order_manager.get_error_log()
        self.assertIn("Invalid quantity format", error_log[-1])

if __name__ == '__main__':
    unittest.main() 