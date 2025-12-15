"""
Strategy Coordination Layer
============================
Eliminates conflicts between multiple trading strategies by:
1. Assigning strategy priority based on market regime
2. Detecting and resolving contradictory signals
3. Ensuring only appropriate strategies activate for current conditions
4. Preventing strategy overlap in same symbols
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class StrategyCoordinator:
    """Coordinates multiple strategies to prevent conflicts"""
    
    def __init__(self):
        # Strategy priority by market regime (higher = more priority)
        self.regime_priority = {
            'STRONG_TRENDING': {
                'momentum_surfer': 10,           # Hodrick-Prescott trend following
                'optimized_volume_scalper': 5,   # Only order flow momentum
                'news_impact_scalper': 3,        # Options momentum
                'regime_adaptive_controller': 1   # Meta strategy (lowest priority)
            },
            'TRENDING': {
                'momentum_surfer': 10,
                'optimized_volume_scalper': 5,
                'news_impact_scalper': 3,
                'regime_adaptive_controller': 1
            },
            'RANGING': {
                'optimized_volume_scalper': 10,  # Mean reversion + liquidity gaps
                'news_impact_scalper': 5,        # Options strategies
                'momentum_surfer': 3,            # Range trading sub-strategies
                'regime_adaptive_controller': 1
            },
            'CHOPPY': {
                'optimized_volume_scalper': 10,  # Microstructure edges
                'news_impact_scalper': 5,
                'momentum_surfer': 2,            # Reduced slots in choppy (was 0 - too restrictive)
                'regime_adaptive_controller': 1
            },
            'VOLATILE': {
                'news_impact_scalper': 10,       # Options shine in volatility
                'optimized_volume_scalper': 8,   # Volatility clustering
                'momentum_surfer': 5,            # High vol momentum
                'regime_adaptive_controller': 1
            },
            'NEUTRAL': {
                'optimized_volume_scalper': 8,
                'momentum_surfer': 8,
                'news_impact_scalper': 8,
                'regime_adaptive_controller': 1
            }
        }
        
        # Track which strategy "owns" each symbol
        self.symbol_ownership = {}  # symbol -> strategy_name
        self.ownership_timestamp = {}  # symbol -> timestamp
        self.ownership_timeout = 300  # 5 minutes
        
        # Conflict resolution rules
        self.allowed_strategy_combos = {
            # Strategies that can coexist for same symbol
            ('news_impact_scalper', 'momentum_surfer'): False,  # Options vs equity conflict
            ('optimized_volume_scalper', 'momentum_surfer'): False,  # Scalper vs momentum time conflict
        }
        
        logger.info("✅ Strategy Coordinator initialized - conflict prevention active")
    
    async def coordinate_signals(self, all_signals: List[Dict], market_regime: str) -> List[Dict]:
        """
        Coordinate signals from multiple strategies to eliminate conflicts
        
        Args:
            all_signals: Raw signals from all strategies
            market_regime: Current market regime (TRENDING, RANGING, etc.)
            
        Returns:
            Coordinated signals with conflicts resolved
        """
        if not all_signals:
            return []
        
        logger.info(f"🎯 COORDINATING {len(all_signals)} signals in {market_regime} regime")
        
        # Step 1: Group signals by strategy
        signals_by_strategy = self._group_by_strategy(all_signals)
        
        # Step 2: Filter strategies by market regime appropriateness
        appropriate_signals = self._filter_by_regime(signals_by_strategy, market_regime)
        
        # Step 3: Detect and resolve conflicts
        conflict_free_signals = self._resolve_conflicts(appropriate_signals, market_regime)
        
        # Step 4: Enforce symbol ownership
        final_signals = self._enforce_symbol_ownership(conflict_free_signals)
        
        logger.info(f"📊 COORDINATION RESULT: {len(all_signals)} → {len(final_signals)} signals after conflict resolution")
        
        return final_signals
    
    def _group_by_strategy(self, signals: List[Dict]) -> Dict[str, List[Dict]]:
        """Group signals by originating strategy"""
        grouped = defaultdict(list)
        
        for signal in signals:
            # 🔥 FIX: Check both top-level 'strategy' and 'metadata.strategy'
            # Signals have 'strategy' at top level, not in metadata
            strategy = signal.get('strategy') or signal.get('metadata', {}).get('strategy', 'unknown')
            
            # Map strategy names to standardized keys
            if 'microstructure' in strategy.lower() or 'volume_scalper' in strategy.lower():
                strategy_key = 'optimized_volume_scalper'
            elif 'momentum' in strategy.lower():
                strategy_key = 'momentum_surfer'
            elif 'options' in strategy.lower() or 'news' in strategy.lower():
                strategy_key = 'news_impact_scalper'
            elif 'regime' in strategy.lower() or 'adaptive' in strategy.lower():
                strategy_key = 'regime_adaptive_controller'
            else:
                strategy_key = strategy
            
            signal['_strategy_key'] = strategy_key
            grouped[strategy_key].append(signal)
        
        logger.info(f"📋 Signals by strategy: {dict((k, len(v)) for k, v in grouped.items())}")
        return dict(grouped)
    
    def _filter_by_regime(self, signals_by_strategy: Dict[str, List[Dict]], regime: str) -> Dict[str, List[Dict]]:
        """Filter out strategies that shouldn't run in current market regime"""
        regime = regime.upper()
        if regime not in self.regime_priority:
            regime = 'NEUTRAL'
        
        priorities = self.regime_priority[regime]
        filtered = {}
        
        # High confidence threshold for regime override
        # 🎯 LOWERED: 8.5 → 8.0 to allow more quality signals through choppy regimes
        # HDFCBANK 8.17 was blocked - that was a valid signal
        HIGH_CONFIDENCE_OVERRIDE = 8.0  # Signals >= 8.0 can bypass regime restrictions
        
        for strategy, signals in signals_by_strategy.items():
            priority = priorities.get(strategy, 0)
            
            if priority == 0:
                # Check for high-confidence signals that should bypass regime restriction
                high_conf_signals = [
                    s for s in signals 
                    if s.get('confidence', 0) >= HIGH_CONFIDENCE_OVERRIDE
                ]
                
                if high_conf_signals:
                    logger.info(f"🎯 HIGH CONFIDENCE OVERRIDE: {len(high_conf_signals)} {strategy} signals "
                               f"(>={HIGH_CONFIDENCE_OVERRIDE}) bypassing {regime} regime block")
                    filtered[strategy] = high_conf_signals
                    for s in high_conf_signals:
                        logger.info(f"   ✅ {s.get('symbol')} {s.get('action')} @ {s.get('confidence'):.1f}/10")
                else:
                    logger.info(f"❌ BLOCKED: {strategy} disabled in {regime} regime ({len(signals)} signals dropped)")
                continue
            
            # Filter signals within strategy based on regime
            regime_appropriate_signals = []
            for signal in signals:
                if self._is_signal_regime_appropriate(signal, regime):
                    regime_appropriate_signals.append(signal)
                else:
                    # Allow high-confidence signals to bypass regime appropriateness check
                    if signal.get('confidence', 0) >= HIGH_CONFIDENCE_OVERRIDE:
                        regime_appropriate_signals.append(signal)
                        logger.info(f"🎯 HIGH CONF OVERRIDE: {signal.get('symbol')} bypassing regime filter")
                    else:
                        logger.debug(f"⏭️ FILTERED: {signal.get('symbol')} from {strategy} - not regime-appropriate")
            
            if regime_appropriate_signals:
                filtered[strategy] = regime_appropriate_signals
                logger.info(f"✅ APPROVED: {strategy} priority={priority} ({len(regime_appropriate_signals)} signals)")
        
        return filtered
    
    def _is_signal_regime_appropriate(self, signal: Dict, regime: str) -> bool:
        """Check if individual signal is appropriate for regime"""
        metadata = signal.get('metadata', {})
        edge_source = metadata.get('edge_source', '')
        
        # Block counter-trend strategies in trending markets
        if regime in ['STRONG_TRENDING', 'TRENDING']:
            counter_trend_edges = ['MEAN_REVERSION', 'LIQUIDITY_GAP', 'RANGE_TRADING']
            if any(ct in edge_source for ct in counter_trend_edges):
                logger.debug(f"⏭️ Blocking counter-trend signal {signal.get('symbol')} in {regime}")
                return False
            
            # Also check signal_type metadata
            signal_type = metadata.get('signal_type', '')
            if 'reversal' in signal_type.lower() or 'sideways' in signal_type.lower():
                return False
        
        # Block trend-following in ranging markets
        if regime in ['RANGING', 'CHOPPY']:
            trend_edges = ['MOMENTUM_UP', 'MOMENTUM_DOWN', 'BREAKOUT']
            if any(te in edge_source for te in trend_edges):
                logger.debug(f"⏭️ Blocking trend signal {signal.get('symbol')} in {regime}")
                return False
            
            # Also check signal_type
            signal_type = metadata.get('signal_type', '')
            if 'breakout' in signal_type.lower() or 'trending' in signal_type.lower():
                return False
        
        return True
    
    def _resolve_conflicts(self, signals_by_strategy: Dict[str, List[Dict]], regime: str) -> List[Dict]:
        """Detect and resolve contradictory signals from different strategies"""
        # Group signals by symbol
        signals_by_symbol = defaultdict(list)
        for strategy, signals in signals_by_strategy.items():
            for signal in signals:
                symbol = signal.get('symbol')
                signals_by_symbol[symbol].append((strategy, signal))
        
        resolved_signals = []
        
        for symbol, strategy_signals in signals_by_symbol.items():
            if len(strategy_signals) == 1:
                # No conflict - single strategy for this symbol
                _, signal = strategy_signals[0]
                resolved_signals.append(signal)
                continue
            
            # Multiple strategies want to trade same symbol - resolve conflict
            logger.info(f"⚠️ CONFLICT DETECTED: {len(strategy_signals)} strategies want {symbol}")
            
            # Check for direction conflicts (BUY vs SELL)
            directions = set(signal.get('action') for _, signal in strategy_signals)
            if len(directions) > 1:
                logger.warning(f"🚫 CRITICAL CONFLICT: {symbol} has opposing directions {directions}")
                # Use regime priority to pick winner
                winner = self._pick_winner_by_priority(strategy_signals, regime)
                if winner:
                    resolved_signals.append(winner)
                    logger.info(f"✅ WINNER: {winner.get('_strategy_key')} for {symbol} {winner.get('action')}")
            else:
                # Same direction but multiple strategies - pick highest priority
                winner = self._pick_winner_by_priority(strategy_signals, regime)
                if winner:
                    resolved_signals.append(winner)
        
        return resolved_signals
    
    def _pick_winner_by_priority(self, strategy_signals: List[tuple], regime: str) -> Optional[Dict]:
        """Pick winning signal based on strategy priority for current regime"""
        priorities = self.regime_priority.get(regime, {})
        
        best_signal = None
        best_priority = -1
        
        for strategy, signal in strategy_signals:
            priority = priorities.get(strategy, 0)
            
            if priority > best_priority:
                best_priority = priority
                best_signal = signal
            elif priority == best_priority and best_signal:
                # Tie-break by confidence
                if signal.get('confidence', 0) > best_signal.get('confidence', 0):
                    best_signal = signal
        
        if best_signal:
            logger.info(f"🏆 Winner: {best_signal.get('_strategy_key')} (priority={best_priority})")
        
        return best_signal
    
    def _enforce_symbol_ownership(self, signals: List[Dict]) -> List[Dict]:
        """Prevent strategies from stepping on each other's active positions"""
        current_time = datetime.now()
        final_signals = []
        
        for signal in signals:
            symbol = signal.get('symbol')
            strategy = signal.get('_strategy_key')
            
            # Check if another strategy owns this symbol
            if symbol in self.symbol_ownership:
                owner = self.symbol_ownership[symbol]
                owner_time = self.ownership_timestamp[symbol]
                
                # Check if ownership has expired
                age = (current_time - owner_time).total_seconds()
                if age > self.ownership_timeout:
                    # Ownership expired - allow new strategy
                    logger.info(f"⏰ Ownership expired for {symbol} (was: {owner}, now: {strategy})")
                    self.symbol_ownership[symbol] = strategy
                    self.ownership_timestamp[symbol] = current_time
                    final_signals.append(signal)
                elif owner == strategy:
                    # Same strategy - allow
                    self.ownership_timestamp[symbol] = current_time  # Refresh
                    final_signals.append(signal)
                else:
                    # Different strategy owns it - block
                    logger.info(f"🔒 BLOCKED: {symbol} owned by {owner}, {strategy} cannot trade")
                    continue
            else:
                # No ownership - claim it
                self.symbol_ownership[symbol] = strategy
                self.ownership_timestamp[symbol] = current_time
                final_signals.append(signal)
        
        return final_signals
    
    def release_symbol(self, symbol: str):
        """Release ownership of a symbol (called when position closed)"""
        if symbol in self.symbol_ownership:
            owner = self.symbol_ownership[symbol]
            del self.symbol_ownership[symbol]
            del self.ownership_timestamp[symbol]
            logger.info(f"🔓 Released {symbol} from {owner}")
    
    def get_coordination_stats(self) -> Dict:
        """Get statistics about strategy coordination"""
        return {
            'owned_symbols': len(self.symbol_ownership),
            'symbol_owners': dict(self.symbol_ownership),
            'regime_priorities': self.regime_priority
        }

# Global instance
strategy_coordinator = StrategyCoordinator()

