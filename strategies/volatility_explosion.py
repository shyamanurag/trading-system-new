"""
Nifty Intelligence Engine - NIFTY INDEX SPECIALIST
Advanced Nifty futures and options strategy with GARCH volatility modeling,
regime detection, and sophisticated position management.
"""

import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class EnhancedVolatilityExplosion(BaseStrategy):
    """
    NIFTY INDEX SPECIALIST ENGINE
    - GARCH volatility modeling
    - Regime detection (trending/sideways/volatile)
    - Nifty futures with point-based targets
    - Index options strategies
    - Intelligent trailing stops
    """
    
    def __init__(self, config: Dict = None):
        if config is None:
            config = {}
        super().__init__(config)
        self.strategy_name = "nifty_intelligence_engine"
        self.description = "Nifty Intelligence Engine with advanced pattern recognition"
        
        # CONFIGURABLE NIFTY PARAMETERS (NO HARDCODED VALUES)
        self.nifty_symbols = config.get('nifty_symbols', ['NIFTY-I', 'NIFTY-FUT', 'BANKNIFTY-I', 'FINNIFTY-I'])

        # CONFIGURABLE POINT-BASED TARGETS
        self.nifty_target_points = config.get('nifty_target_points', 75)
        self.nifty_stop_points = config.get('nifty_stop_points', 12)

        # CONFIGURABLE GARCH VOLATILITY PARAMETERS
        self.volatility_window = config.get('volatility_window', 20)
        self.volatility_history = []

        # CONFIGURABLE REGIME DETECTION
        self.regime_states = config.get('regime_states', ['trending_up', 'trending_down', 'sideways', 'volatile'])
        self.current_regime = config.get('initial_regime', 'sideways')

        # CONFIGURABLE POSITION MANAGEMENT
        self.max_positions_per_symbol = config.get('max_positions_per_symbol', 2)
        self.trailing_stop_activation = config.get('trailing_stop_activation', 0.6)

        # BACKTESTING FRAMEWORK
        self.backtest_mode = config.get('backtest_mode', False)
        self.backtest_results = {
            'total_signals': 0,
            'profitable_signals': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'sharpe_ratio': 0.0,
            'avg_profit': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'signals_by_regime': {}
        }
        self.backtest_trades = []

        # ENHANCED RISK MANAGEMENT
        self.max_daily_loss = config.get('max_daily_loss', -2500)  # Nifty strategy more conservative
        self.max_single_trade_loss = config.get('max_single_trade_loss', -600)  # Point-based limits
        self.max_daily_trades = config.get('max_daily_trades', 12)  # Moderate trading frequency
        self.max_consecutive_losses = config.get('max_consecutive_losses', 3)

        # DYNAMIC RISK ADJUSTMENT
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.emergency_stop = False
        
        logger.info("✅ NiftyIntelligenceEngine strategy initialized")

    # BACKTESTING METHODS
    async def run_backtest(self, historical_data: Dict[str, List], start_date: str = None, end_date: str = None) -> Dict:
        """
        Run comprehensive backtest on historical Nifty data
        Args:
            historical_data: Dict[symbol, List[price_data]]
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
        Returns:
            Backtest results dictionary
        """
        logger.info("🔬 STARTING NIFTY INTELLIGENCE BACKTEST")
        self.backtest_mode = True
        self.backtest_trades = []
        self.backtest_results = {
            'total_signals': 0,
            'profitable_signals': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'sharpe_ratio': 0.0,
            'avg_profit': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'signals_by_regime': {}
        }

        try:
            # Process each Nifty symbol's historical data
            for symbol in self.nifty_symbols:
                if symbol not in historical_data:
                    logger.warning(f"⚠️ No historical data for {symbol}")
                    continue

                price_history = historical_data[symbol]
                if len(price_history) < 50:  # Minimum data requirement
                    logger.warning(f"⚠️ Insufficient data for {symbol}: {len(price_history)} points")
                    continue

                logger.info(f"📊 Backtesting {symbol} with {len(price_history)} data points")

                # Simulate trading through historical data
                await self._simulate_historical_trading(symbol, price_history)

            # Calculate comprehensive backtest statistics
            self._calculate_backtest_statistics()

            logger.info("✅ NIFTY BACKTEST COMPLETED")
            logger.info(f"📈 Total Signals: {self.backtest_results['total_signals']}")
            logger.info(f"💰 Total P&L: ₹{self.backtest_results['total_pnl']:,.2f}")
            logger.info(f"🎯 Win Rate: {self.backtest_results['win_rate']:.1%}")
            logger.info(f"📊 Sharpe Ratio: {self.backtest_results['sharpe_ratio']:.2f}")

            return self.backtest_results

        except Exception as e:
            logger.error(f"❌ Nifty backtest failed: {e}")
            return self.backtest_results

    async def _simulate_historical_trading(self, symbol: str, price_history: List[Dict]):
        """Simulate trading through historical Nifty data"""
        try:
            # Reset strategy state for this symbol
            self.current_regime = 'sideways'
            self.volatility_history = []

            # Process each historical data point
            for i, data_point in enumerate(price_history):
                if i < 30:  # Skip initial data for indicator warmup
                    continue

                # Create market data dict for strategy
                market_data = {symbol: data_point}

                # Generate signals (run async method synchronously for backtest)
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    signals = loop.run_until_complete(self.generate_signals(market_data))
                    loop.close()
                except Exception as e:
                    logger.warning(f"⚠️ Signal generation failed for {symbol}: {e}")
                    continue

                # Process each generated signal
                for signal in signals:
                    await self._process_backtest_signal(signal, price_history[i:], symbol)

        except Exception as e:
            logger.error(f"❌ Historical trading simulation failed for {symbol}: {e}")

    async def _process_backtest_signal(self, signal: Dict, future_prices: List[Dict], symbol: str):
        """Process a signal in backtest mode"""
        try:
            entry_price = signal.get('entry_price', 0)
            confidence = signal.get('confidence', 0)

            if entry_price <= 0:
                return

            # For Nifty futures, calculate stop loss and target based on points
            stop_loss = entry_price - (self.nifty_stop_points if signal.get('action') == 'BUY' else -self.nifty_stop_points)
            target = entry_price + (self.nifty_target_points if signal.get('action') == 'BUY' else -self.nifty_target_points)

            # Record signal
            self.backtest_results['total_signals'] += 1
            regime = signal.get('regime', self.current_regime)

            if regime not in self.backtest_results['signals_by_regime']:
                self.backtest_results['signals_by_regime'][regime] = 0
            self.backtest_results['signals_by_regime'][regime] += 1

            # Simulate trade execution and exit
            trade_pnl, exit_reason = self._simulate_trade_exit(entry_price, stop_loss, target, future_prices, signal.get('action'))

            # Record trade
            trade_record = {
                'symbol': symbol,
                'entry_price': entry_price,
                'exit_price': entry_price + trade_pnl,
                'pnl': trade_pnl,
                'confidence': confidence,
                'regime': regime,
                'exit_reason': exit_reason,
                'action': signal.get('action')
            }

            self.backtest_trades.append(trade_record)

            if trade_pnl > 0:
                self.backtest_results['profitable_signals'] += 1

            self.backtest_results['total_pnl'] += trade_pnl

            logger.debug(f"📊 Nifty Backtest Trade: {symbol} @ {entry_price:.2f} → {trade_record['exit_price']:.2f} (P&L: ₹{trade_pnl:.2f})")

        except Exception as e:
            logger.error(f"❌ Backtest signal processing failed: {e}")

    def _simulate_trade_exit(self, entry_price: float, stop_loss: float, target: float, future_prices: List[Dict], action: str) -> Tuple[float, str]:
        """Simulate when a Nifty trade would exit based on stop loss or target"""
        try:
            # Simulate holding for up to 20 periods (Nifty futures are shorter-term)
            for i, future_data in enumerate(future_prices[:20]):
                high = future_data.get('high', future_data.get('close', 0))
                low = future_data.get('low', future_data.get('close', 0))

                if action == 'BUY':
                    # Check for stop loss hit (price drops below stop)
                    if low <= stop_loss:
                        pnl = stop_loss - entry_price
                        return pnl, 'stop_loss'

                    # Check for target hit (price reaches target)
                    if high >= target:
                        pnl = target - entry_price
                        return pnl, 'target'

                else:  # SELL
                    # Check for stop loss hit (price rises above stop)
                    if high >= stop_loss:
                        pnl = entry_price - stop_loss
                        return pnl, 'stop_loss'

                    # Check for target hit (price drops to target)
                    if low <= target:
                        pnl = entry_price - target
                        return pnl, 'target'

            # Exit at end of simulation period
            exit_price = future_prices[-1].get('close', entry_price)
            pnl = exit_price - entry_price if action == 'BUY' else entry_price - exit_price
            return pnl, 'time_exit'

        except Exception as e:
            logger.error(f"❌ Nifty trade exit simulation failed: {e}")
            return 0.0, 'error'

    def _calculate_backtest_statistics(self):
        """Calculate comprehensive backtest statistics for Nifty strategy"""
        try:
            if not self.backtest_trades:
                logger.warning("⚠️ No trades recorded in Nifty backtest")
                return

            trades = self.backtest_trades

            # Basic statistics
            self.backtest_results['total_signals'] = len(trades)
            self.backtest_results['profitable_signals'] = sum(1 for t in trades if t['pnl'] > 0)

            if self.backtest_results['total_signals'] > 0:
                self.backtest_results['win_rate'] = self.backtest_results['profitable_signals'] / self.backtest_results['total_signals']

            # P&L statistics
            pnl_values = [t['pnl'] for t in trades]
            self.backtest_results['total_pnl'] = sum(pnl_values)

            if pnl_values:
                profitable_trades = [p for p in pnl_values if p > 0]
                losing_trades = [p for p in pnl_values if p < 0]

                if profitable_trades:
                    self.backtest_results['avg_profit'] = sum(profitable_trades) / len(profitable_trades)
                if losing_trades:
                    self.backtest_results['avg_loss'] = abs(sum(losing_trades) / len(losing_trades))

                if self.backtest_results['avg_loss'] > 0:
                    self.backtest_results['profit_factor'] = (self.backtest_results['avg_profit'] * len(profitable_trades)) / (self.backtest_results['avg_loss'] * len(losing_trades))

            # Sharpe ratio calculation
            if len(pnl_values) > 1:
                returns = np.array(pnl_values)
                sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
                self.backtest_results['sharpe_ratio'] = sharpe

            # Maximum drawdown
            cumulative_pnl = np.cumsum(pnl_values)
            peak = np.maximum.accumulate(cumulative_pnl)
            drawdown = cumulative_pnl - peak
            self.backtest_results['max_drawdown'] = abs(np.min(drawdown)) if len(drawdown) > 0 else 0

            logger.info("📊 NIFTY BACKTEST STATISTICS CALCULATED")
            logger.info(f"🔍 Total Trades: {self.backtest_results['total_signals']}")
            logger.info(f"💰 Total P&L: ₹{self.backtest_results['total_pnl']:,.2f}")
            logger.info(f"🎯 Win Rate: {self.backtest_results['win_rate']:.1%}")
            logger.info(f"⚡ Profit Factor: {self.backtest_results['profit_factor']:.2f}")
            logger.info(f"📉 Max Drawdown: ₹{self.backtest_results['max_drawdown']:,.2f}")

        except Exception as e:
            logger.error(f"❌ Nifty backtest statistics calculation failed: {e}")

    def get_backtest_report(self) -> str:
        """Generate detailed Nifty backtest report"""
        try:
            report = []
            report.append("📊 NIFTY INTELLIGENCE BACKTEST REPORT")
            report.append("=" * 45)
            report.append(f"Total Signals: {self.backtest_results['total_signals']}")
            report.append(f"Profitable Signals: {self.backtest_results['profitable_signals']}")
            report.append(f"Win Rate: {self.backtest_results['win_rate']:.1%}")
            report.append(f"Total P&L: ₹{self.backtest_results['total_pnl']:,.2f}")
            report.append(f"Average Profit: ₹{self.backtest_results['avg_profit']:.2f}")
            report.append(f"Average Loss: ₹{self.backtest_results['avg_loss']:.2f}")
            report.append(f"Profit Factor: {self.backtest_results['profit_factor']:.2f}")
            report.append(f"Sharpe Ratio: {self.backtest_results['sharpe_ratio']:.2f}")
            report.append(f"Max Drawdown: ₹{self.backtest_results['max_drawdown']:.2f}")

            # Signals by regime
            report.append("\n📈 SIGNALS BY REGIME:")
            for regime, count in self.backtest_results['signals_by_regime'].items():
                report.append(f"  {regime}: {count}")

            return "\n".join(report)

        except Exception as e:
            logger.error(f"❌ Nifty backtest report generation failed: {e}")
            return "Nifty backtest report generation failed"

    # RISK MANAGEMENT METHODS
    def assess_risk_before_trade(self, symbol: str, entry_price: float, stop_loss: float, confidence: float) -> Tuple[bool, str, float]:
        """
        Comprehensive risk assessment for Nifty futures trading
        Returns: (allowed, reason, adjusted_quantity_multiplier)
        """
        try:
            # Emergency stop check
            if self.emergency_stop:
                return False, "EMERGENCY_STOP_ACTIVE", 0.0

            # Daily loss limit check
            if self.daily_pnl <= self.max_daily_loss:
                self.emergency_stop = True
                logger.critical(f"🚨 EMERGENCY STOP: Nifty daily loss limit reached ₹{self.daily_pnl:.2f}")
                return False, "DAILY_LOSS_LIMIT_EXCEEDED", 0.0

            # Daily trade limit check
            if self.daily_trades >= self.max_daily_trades:
                return False, "DAILY_TRADE_LIMIT_EXCEEDED", 0.0

            # Single trade loss limit check (point-based for Nifty)
            potential_loss_points = abs(entry_price - stop_loss)
            potential_loss_value = potential_loss_points * 50  # Nifty futures multiplier
            if potential_loss_value > abs(self.max_single_trade_loss):
                return False, f"TRADE_LOSS_TOO_LARGE_₹{potential_loss_value:.2f}", 0.0

            # Consecutive losses check
            if self.consecutive_losses >= self.max_consecutive_losses:
                return False, f"CONSECUTIVE_LOSSES_LIMIT_{self.consecutive_losses}", 0.0

            # Confidence threshold check (higher for Nifty futures)
            if confidence < 7.5:  # Higher threshold for index futures
                return False, f"LOW_CONFIDENCE_{confidence:.1f}", 0.0

            # Calculate dynamic risk multiplier
            risk_multiplier = self._calculate_dynamic_risk_multiplier()

            logger.info(f"🛡️ Nifty Risk Assessment PASSED for {symbol}: multiplier={risk_multiplier:.2f}")
            return True, "APPROVED", risk_multiplier

        except Exception as e:
            logger.error(f"❌ Nifty risk assessment failed for {symbol}: {e}")
            return False, f"RISK_ASSESSMENT_ERROR_{str(e)}", 0.0

    def _calculate_dynamic_risk_multiplier(self) -> float:
        """Calculate risk multiplier based on current Nifty performance"""
        try:
            base_multiplier = 1.0

            # Reduce risk after losses (more conservative for Nifty)
            if self.daily_pnl < -1000:
                base_multiplier *= 0.7
            elif self.daily_pnl < -2000:
                base_multiplier *= 0.5
            elif self.daily_pnl < -2500:
                base_multiplier *= 0.3

            # Reduce risk after consecutive losses
            if self.consecutive_losses >= 2:
                base_multiplier *= 0.7
            elif self.consecutive_losses >= 3:
                base_multiplier *= 0.5

            # Increase risk slightly after consistent wins (but conservatively)
            if self.consecutive_losses == 0 and self.daily_trades > 5:
                base_multiplier *= 1.1

            return min(base_multiplier, 1.5)  # Conservative cap for Nifty

        except Exception as e:
            logger.error(f"❌ Nifty dynamic risk multiplier calculation failed: {e}")
            return 1.0

    def update_risk_metrics(self, trade_result: float, symbol: str):
        """Update Nifty risk metrics after each trade"""
        try:
            self.daily_pnl += trade_result
            self.daily_trades += 1

            # Track consecutive losses
            if trade_result < 0:
                self.consecutive_losses += 1
                logger.warning(f"⚠️ Nifty consecutive losses: {self.consecutive_losses}")
            else:
                self.consecutive_losses = 0

            # Emergency stop triggers
            if self.daily_pnl <= self.max_daily_loss:
                self.emergency_stop = True
                logger.critical(f"🚨 NIFTY EMERGENCY STOP ACTIVATED: Daily P&L ₹{self.daily_pnl:.2f}")

            if self.consecutive_losses >= self.max_consecutive_losses:
                logger.warning(f"⚠️ MAX CONSECUTIVE LOSSES REACHED: {self.consecutive_losses}")

            logger.info(f"📊 Nifty Risk Update: Daily P&L ₹{self.daily_pnl:.2f}, Trades: {self.daily_trades}, Consecutive Losses: {self.consecutive_losses}")

        except Exception as e:
            logger.error(f"❌ Nifty risk metrics update failed: {e}")

    def reset_daily_risk_metrics(self):
        """Reset daily risk metrics for Nifty strategy"""
        try:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.consecutive_losses = 0
            self.emergency_stop = False

            logger.info("🌅 Nifty daily risk metrics reset - Fresh trading day")

        except Exception as e:
            logger.error(f"❌ Nifty daily risk reset failed: {e}")

    def get_risk_status_report(self) -> str:
        """Generate comprehensive Nifty risk status report"""
        try:
            report = []
            report.append("🛡️ NIFTY INTELLIGENCE RISK REPORT")
            report.append("=" * 40)
            report.append(f"Daily P&L: ₹{self.daily_pnl:.2f}")
            report.append(f"Daily Trades: {self.daily_trades}/{self.max_daily_trades}")
            report.append(f"Consecutive Losses: {self.consecutive_losses}/{self.max_consecutive_losses}")
            report.append(f"Emergency Stop: {'ACTIVE' if self.emergency_stop else 'INACTIVE'}")
            report.append(f"Max Daily Loss Limit: ₹{self.max_daily_loss:.2f}")
            report.append(f"Current Risk Level: {'HIGH' if self.emergency_stop else 'NORMAL'}")
            report.append(f"Current Regime: {self.current_regime}")

            return "\n".join(report)

        except Exception as e:
            logger.error(f"❌ Nifty risk status report failed: {e}")
            return "Nifty risk status report generation failed"

    async def initialize(self):
        """Initialize the strategy"""
        self.is_active = True
        logger.info("✅ Nifty Intelligence Engine loaded successfully")

    async def on_market_data(self, data: Dict):
        """Process market data and generate Nifty signals"""
        if not self.is_active:
            return
            
        try:
            # Generate signals using the existing method
            signals = await self.generate_signals(data)
            
            # Store signals in current_positions for orchestrator to find
            for signal in signals:
                symbol = signal.get('symbol')
                if symbol:
                    self.current_positions[symbol] = signal
                    logger.info(f"🎯 NIFTY INTELLIGENCE: {signal['symbol']} {signal['action']} "
                               f"Confidence: {signal.get('confidence', 0):.1f}/10 "
                               f"Regime: {self.current_regime}")
                
        except Exception as e:
            logger.error(f"Error in Nifty Intelligence Engine: {e}")

    async def generate_signals(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate intelligent Nifty signals with regime awareness"""
        try:
            signals = []
            
            if not market_data:
                return signals
            
            # Update volatility model
            self._update_volatility_model(market_data)
            
            # Detect current market regime
            self._detect_market_regime(market_data)
            
            # Generate signals based on regime
            for symbol in self.nifty_symbols:
                if symbol in market_data:
                    signal = await self._analyze_nifty_opportunity(symbol, market_data)
                    if signal:
                        signals.append(signal)
            
            logger.info(f"📊 Nifty Intelligence Engine generated {len(signals)} signals (Regime: {self.current_regime})")
            return signals
            
        except Exception as e:
            logger.error(f"Error in Nifty Intelligence Engine: {e}")
            return []

    def _update_volatility_model(self, market_data: Dict[str, Any]):
        """Update GARCH-inspired volatility model"""
        try:
            nifty_data = market_data.get('NIFTY-I', {})
            if not nifty_data:
                return
            
            change_percent = nifty_data.get('change_percent', 0)
            self.volatility_history.append(abs(change_percent))
            
            # Keep rolling window
            if len(self.volatility_history) > self.volatility_window:
                self.volatility_history.pop(0)
            
            # Calculate current volatility
            if len(self.volatility_history) >= 5:
                self.current_volatility = np.std(self.volatility_history[-10:]) if len(self.volatility_history) >= 10 else np.std(self.volatility_history)
            else:
                self.current_volatility = 1.0
                
        except Exception as e:
            logger.debug(f"Error updating volatility model: {e}")

    def _detect_market_regime(self, market_data: Dict[str, Any]):
        """Detect current market regime using price action"""
        try:
            nifty_data = market_data.get('NIFTY-I', {})
            if not nifty_data:
                return
            
            change_percent = nifty_data.get('change_percent', 0)
            ltp = nifty_data.get('ltp', 0)
            
            # Simple regime detection logic
            if abs(change_percent) > 1.5:
                if change_percent > 0:
                    self.current_regime = 'trending_up'
                else:
                    self.current_regime = 'trending_down'
            elif hasattr(self, 'current_volatility') and self.current_volatility > 2.0:
                self.current_regime = 'volatile'
            else:
                self.current_regime = 'sideways'
                
        except Exception as e:
            logger.debug(f"Error detecting market regime: {e}")

    async def _analyze_nifty_opportunity(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze Nifty opportunity based on regime and volatility"""
        try:
            data = market_data.get(symbol, {})
            if not data:
                return None
            
            ltp = data.get('ltp', 0)
            change_percent = data.get('change_percent', 0)
            volume = data.get('volume', 0)
            
            if ltp <= 0:
                return None
            
            # Regime-based signal generation
            signal_type = None
            confidence = 5.0
            reasoning = f"Nifty analysis in {self.current_regime} regime"
            
            if self.current_regime == 'trending_up' and change_percent > 0.5:
                signal_type = 'buy'
                confidence += 2.0
                reasoning += f" - Uptrend continuation, change: {change_percent:.1f}%"
                
            elif self.current_regime == 'trending_down' and change_percent < -0.5:
                signal_type = 'sell'
                confidence += 2.0
                reasoning += f" - Downtrend continuation, change: {change_percent:.1f}%"
                
            elif self.current_regime == 'volatile' and abs(change_percent) > 1.0:
                # In volatile regime, trade momentum
                signal_type = 'buy' if change_percent > 0 else 'sell'
                confidence += 1.5
                reasoning += f" - Volatile regime momentum, change: {change_percent:.1f}%"
                
            elif self.current_regime == 'sideways' and abs(change_percent) > 0.3:
                # In sideways, look for mean reversion
                signal_type = 'sell' if change_percent > 0 else 'buy'
                confidence += 1.0
                reasoning += f" - Sideways mean reversion, change: {change_percent:.1f}%"
            
            if not signal_type:
                return None

            # Volume/volatility confirmation
            if volume > 1000000:
                confidence += 1.0
            elif volume > 500000:
                confidence += 0.5

            if hasattr(self, 'current_volatility') and self.current_volatility > 2.0:
                confidence += 0.5

            if confidence < 9.0:
                return None

            # Use standardized signal creation to ensure correct fields
            stop_loss = ltp * (0.99 if signal_type == 'buy' else 1.01)
            target = ltp * (1.02 if signal_type == 'buy' else 0.98)
            action = 'BUY' if signal_type == 'buy' else 'SELL'
            return await self.create_standard_signal(
                symbol=symbol,
                action=action,
                entry_price=ltp,
                stop_loss=stop_loss,
                target=target,
                confidence=confidence,
                metadata={
                    'strategy': self.strategy_name,
                    'signal_type': 'OPTIONS',
                    'reason': reasoning + " | Index regime"
                },
                market_bias=self.market_bias
            )
            
        except Exception as e:
            logger.debug(f"Error analyzing Nifty opportunity for {symbol}: {e}")
            return None

    async def _create_futures_signal(self, symbol: str, signal_type: str, confidence: float, 
                                   reasoning: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Nifty futures signal with point-based targets"""
        try:
            data = market_data.get(symbol, {})
            ltp = data.get('ltp', 0)
            
            # Point-based targets for futures
            if signal_type == 'buy':
                target_price = ltp + self.nifty_target_points
                stop_loss_price = ltp - self.nifty_stop_points
            else:
                target_price = ltp - self.nifty_target_points
                stop_loss_price = ltp + self.nifty_stop_points
            
            # Position sizing for futures (larger lots)
            position_size = 75  # Standard Nifty lot size
            
            return {
                'symbol': symbol,
                'signal_type': signal_type,
                'entry_price': ltp,
                'target_price': target_price,
                'stop_loss_price': stop_loss_price,
                'quantity': position_size,
                'confidence': confidence,
                'strategy': self.strategy_name,
                'reasoning': reasoning + f" | Futures target: {self.nifty_target_points}pts, stop: {self.nifty_stop_points}pts",
                'timestamp': datetime.now().isoformat(),
                'instrument_type': 'futures',
                'trailing_stop_enabled': True,
                'trailing_stop_activation': self.trailing_stop_activation
            }
            
        except Exception as e:
            logger.error(f"Error creating futures signal: {e}")
            return None

    async def _create_index_options_signal(self, symbol: str, signal_type: str, confidence: float,
                                         reasoning: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create index options signal"""
        try:
            # For index options, use the base strategy's options signal creation
            return await self._create_options_signal(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                market_data=market_data,
                reasoning=reasoning + " | Index options strategy",
                position_size=150  # Standard options lot size
            )
            
        except Exception as e:
            logger.error(f"Error creating index options signal: {e}")
            return None

logger.info("✅ Nifty Intelligence Engine loaded successfully")