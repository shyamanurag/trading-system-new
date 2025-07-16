"""
User Analytics Service
Provides comprehensive analytics and reporting for individual users
Integrates with database and real-time data for complete user insights
"""

import logging
import asyncio
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import create_engine, text, func, and_, or_, desc, distinct
from sqlalchemy.orm import sessionmaker, Session
import pandas as pd
import numpy as np
from decimal import Decimal
import json
import redis.asyncio as redis
import os

from ..models.trading_models import User, Trade, Position, Order
from ..config.database import DatabaseConfig

logger = logging.getLogger(__name__)

@dataclass
class UserPerformanceMetrics:
    """Comprehensive user performance metrics"""
    user_id: int
    username: str
    
    # Trading Statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win_amount: float
    avg_loss_amount: float
    profit_factor: float
    
    # P&L Metrics
    total_pnl: float
    daily_pnl: float
    weekly_pnl: float
    monthly_pnl: float
    yearly_pnl: float
    
    # Risk Metrics
    max_profit: float
    max_loss: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Trading Behavior
    avg_trade_duration_hours: float
    avg_position_size: float
    most_traded_symbol: str
    most_profitable_strategy: str
    
    # Capital Metrics
    initial_capital: float
    current_balance: float
    peak_balance: float
    total_invested: float
    available_capital: float
    margin_used: float
    
    # Activity Metrics
    active_positions: int
    pending_orders: int
    last_trade_date: Optional[datetime]
    trading_days: int
    avg_trades_per_day: float

@dataclass
class UserTradingReport:
    """Detailed trading report for a user"""
    user_id: int
    username: str
    report_period: str
    generated_at: datetime
    
    performance_metrics: UserPerformanceMetrics
    daily_pnl_chart: List[Dict]
    symbol_performance: List[Dict]
    strategy_performance: List[Dict]
    monthly_summary: List[Dict]
    risk_analysis: Dict
    recommendations: List[str]

router = APIRouter(prefix="/api/v1/analytics", tags=["user-analytics"])

class UserAnalyticsService:
    """Comprehensive user analytics service"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.engine = create_engine(self.db_config.database_url)  # Fixed: use attribute instead of method
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.redis_client = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the analytics service"""
        try:
            # Initialize Redis connection
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self.redis_client = await redis.from_url(redis_url)
            
            self.is_initialized = True
            logger.info("✅ UserAnalyticsService initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ UserAnalyticsService initialization failed: {e}")
            return False
    
    def get_db_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    async def get_user_performance_metrics(self, user_id: int, days: int = 30) -> UserPerformanceMetrics:
        """Calculate comprehensive performance metrics for a user"""
        db = self.get_db_session()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Calculate date ranges
            now = datetime.utcnow()
            start_date = now - timedelta(days=days)
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = now - timedelta(days=7)
            month_start = now - timedelta(days=30)
            year_start = now - timedelta(days=365)
            
            # Get all trades for the period
            trades = db.query(Trade).filter(
                and_(Trade.user_id == user_id, Trade.created_at >= start_date)
            ).all()
            
            # Basic trading statistics
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.pnl and t.pnl > 0])
            losing_trades = len([t for t in trades if t.pnl and t.pnl < 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
            
            # P&L calculations
            all_pnl = [float(t.pnl) for t in trades if t.pnl is not None]
            total_pnl = sum(all_pnl)
            
            daily_trades = [t for t in trades if t.created_at >= day_start]
            daily_pnl = sum(float(t.pnl) for t in daily_trades if t.pnl)
            
            weekly_trades = [t for t in trades if t.created_at >= week_start]
            weekly_pnl = sum(float(t.pnl) for t in weekly_trades if t.pnl)
            
            monthly_trades = [t for t in trades if t.created_at >= month_start]
            monthly_pnl = sum(float(t.pnl) for t in monthly_trades if t.pnl)
            
            yearly_trades = [t for t in trades if t.created_at >= year_start]
            yearly_pnl = sum(float(t.pnl) for t in yearly_trades if t.pnl)
            
            # Win/Loss analysis
            wins = [float(t.pnl) for t in trades if t.pnl and t.pnl > 0]
            losses = [float(t.pnl) for t in trades if t.pnl and t.pnl < 0]
            
            avg_win_amount = sum(wins) / len(wins) if wins else 0.0
            avg_loss_amount = sum(losses) / len(losses) if losses else 0.0
            
            # Profit factor
            total_wins = sum(wins) if wins else 0.0
            total_losses = abs(sum(losses)) if losses else 0.0
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf') if total_wins > 0 else 0.0
            
            # Risk metrics
            max_profit = max(wins) if wins else 0.0
            max_loss = min(losses) if losses else 0.0
            
            # Calculate max drawdown
            cumulative_pnl = []
            running_total = 0
            for trade in sorted(trades, key=lambda x: x.created_at):
                if trade.pnl:
                    running_total += float(trade.pnl)
                    cumulative_pnl.append(running_total)
            
            max_drawdown = 0.0
            if cumulative_pnl:
                peak = cumulative_pnl[0]
                for value in cumulative_pnl:
                    if value > peak:
                        peak = value
                    drawdown = peak - value
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
            
            # Sharpe ratio calculation
            sharpe_ratio = self._calculate_sharpe_ratio(all_pnl)
            sortino_ratio = self._calculate_sortino_ratio(all_pnl)
            calmar_ratio = self._calculate_calmar_ratio(total_pnl, max_drawdown)
            
            # Trading behavior analysis
            avg_trade_duration = self._calculate_avg_trade_duration(trades)
            avg_position_size = self._calculate_avg_position_size(trades)
            most_traded_symbol = self._get_most_traded_symbol(trades)
            most_profitable_strategy = self._get_most_profitable_strategy(trades)
            
            # Position and order analysis
            active_positions = db.query(Position).filter(
                and_(Position.user_id == user_id, Position.is_active == True)
            ).count()
            
            pending_orders = db.query(Order).filter(
                and_(Order.user_id == user_id, Order.status == 'PENDING')
            ).count()
            
            # Capital calculations
            total_invested = sum(float(p.current_value) for p in db.query(Position).filter(
                and_(Position.user_id == user_id, Position.is_active == True)
            ).all() if p.current_value)
            
            margin_used = total_invested * 0.2  # Assuming 20% margin requirement
            available_capital = float(user.current_balance) - margin_used
            
            # Peak balance calculation
            peak_balance = await self._get_peak_balance(user_id)
            
            # Activity metrics
            last_trade = db.query(Trade).filter(Trade.user_id == user_id).order_by(desc(Trade.created_at)).first()
            last_trade_date = last_trade.created_at if last_trade else None
            
            # Calculate trading days
            if trades:
                first_trade_date = min(t.created_at for t in trades)
                trading_days = (now - first_trade_date).days
            else:
                trading_days = 0
            
            avg_trades_per_day = total_trades / trading_days if trading_days > 0 else 0.0
            
            return UserPerformanceMetrics(
                user_id=user_id,
                username=user.username,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                avg_win_amount=avg_win_amount,
                avg_loss_amount=avg_loss_amount,
                profit_factor=profit_factor,
                total_pnl=total_pnl,
                daily_pnl=daily_pnl,
                weekly_pnl=weekly_pnl,
                monthly_pnl=monthly_pnl,
                yearly_pnl=yearly_pnl,
                max_profit=max_profit,
                max_loss=max_loss,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                avg_trade_duration_hours=avg_trade_duration,
                avg_position_size=avg_position_size,
                most_traded_symbol=most_traded_symbol,
                most_profitable_strategy=most_profitable_strategy,
                initial_capital=float(user.initial_capital),
                current_balance=float(user.current_balance),
                peak_balance=peak_balance,
                total_invested=total_invested,
                available_capital=available_capital,
                margin_used=margin_used,
                active_positions=active_positions,
                pending_orders=pending_orders,
                last_trade_date=last_trade_date,
                trading_days=trading_days,
                avg_trades_per_day=avg_trades_per_day
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error calculating performance metrics for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to calculate performance metrics")
        finally:
            db.close()
    
    async def generate_user_trading_report(self, user_id: int, days: int = 30) -> UserTradingReport:
        """Generate comprehensive trading report for a user"""
        db = self.get_db_session()
        try:
            # Get performance metrics
            performance_metrics = await self.get_user_performance_metrics(user_id, days)
            
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            
            # Generate daily P&L chart
            daily_pnl_chart = await self._generate_daily_pnl_chart(user_id, days, db)
            
            # Generate symbol performance analysis
            symbol_performance = await self._generate_symbol_performance(user_id, days, db)
            
            # Generate strategy performance analysis
            strategy_performance = await self._generate_strategy_performance(user_id, days, db)
            
            # Generate monthly summary
            monthly_summary = await self._generate_monthly_summary(user_id, days, db)
            
            # Generate risk analysis
            risk_analysis = await self._generate_risk_analysis(user_id, days, db)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(performance_metrics, db)
            
            return UserTradingReport(
                user_id=user_id,
                username=user.username,
                report_period=f"Last {days} days",
                generated_at=datetime.utcnow(),
                performance_metrics=performance_metrics,
                daily_pnl_chart=daily_pnl_chart,
                symbol_performance=symbol_performance,
                strategy_performance=strategy_performance,
                monthly_summary=monthly_summary,
                risk_analysis=risk_analysis,
                recommendations=recommendations
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error generating trading report for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate trading report")
        finally:
            db.close()
    
    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        if not returns or len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        return mean_return / std_return if std_return > 0 else 0.0
    
    def _calculate_sortino_ratio(self, returns: List[float]) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        if not returns or len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        negative_returns = [r for r in returns if r < 0]
        
        if not negative_returns:
            return float('inf') if mean_return > 0 else 0.0
        
        downside_deviation = np.std(negative_returns)
        return mean_return / downside_deviation if downside_deviation > 0 else 0.0
    
    def _calculate_calmar_ratio(self, total_return: float, max_drawdown: float) -> float:
        """Calculate Calmar ratio"""
        return total_return / max_drawdown if max_drawdown > 0 else 0.0
    
    def _calculate_avg_trade_duration(self, trades: List[Trade]) -> float:
        """Calculate average trade duration in hours"""
        durations = []
        for trade in trades:
            if trade.entry_time and trade.exit_time:
                duration = (trade.exit_time - trade.entry_time).total_seconds() / 3600
                durations.append(duration)
        
        return sum(durations) / len(durations) if durations else 0.0
    
    def _calculate_avg_position_size(self, trades: List[Trade]) -> float:
        """Calculate average position size"""
        sizes = [float(trade.quantity) * float(trade.entry_price) for trade in trades 
                if trade.quantity and trade.entry_price]
        
        return sum(sizes) / len(sizes) if sizes else 0.0
    
    def _get_most_traded_symbol(self, trades: List[Trade]) -> str:
        """Get most frequently traded symbol"""
        if not trades:
            return "N/A"
        
        symbol_counts = {}
        for trade in trades:
            symbol = trade.symbol
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        return max(symbol_counts, key=symbol_counts.get) if symbol_counts else "N/A"
    
    def _get_most_profitable_strategy(self, trades: List[Trade]) -> str:
        """Get most profitable trading strategy"""
        if not trades:
            return "N/A"
        
        strategy_pnl = {}
        for trade in trades:
            if trade.strategy and trade.pnl:
                strategy = trade.strategy
                strategy_pnl[strategy] = strategy_pnl.get(strategy, 0) + float(trade.pnl)
        
        return max(strategy_pnl, key=strategy_pnl.get) if strategy_pnl else "N/A"
    
    async def _get_peak_balance(self, user_id: int) -> float:
        """Get peak balance from Redis cache or calculate"""
        try:
            if self.redis_client:
                peak = await self.redis_client.get(f"user:peak_balance:{user_id}")
                if peak:
                    return float(peak)
            
            # Calculate from database if not cached
            db = self.get_db_session()
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    # For now, use current balance as peak
                    # In a real system, you'd track this over time
                    peak_balance = float(user.current_balance)
                    
                    # Cache the result
                    if self.redis_client:
                        await self.redis_client.set(f"user:peak_balance:{user_id}", peak_balance, ex=3600)
                    
                    return peak_balance
                
                return 0.0
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error getting peak balance for user {user_id}: {e}")
            return 0.0
    
    async def _generate_daily_pnl_chart(self, user_id: int, days: int, db: Session) -> List[Dict]:
        """Generate daily P&L chart data"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            # Get trades grouped by date
            daily_data = []
            current_date = start_date
            
            while current_date <= end_date:
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())
                
                trades = db.query(Trade).filter(
                    and_(
                        Trade.user_id == user_id,
                        Trade.created_at >= day_start,
                        Trade.created_at <= day_end
                    )
                ).all()
                
                daily_pnl = sum(float(t.pnl) for t in trades if t.pnl)
                trade_count = len(trades)
                
                daily_data.append({
                    'date': current_date.isoformat(),
                    'pnl': daily_pnl,
                    'trades': trade_count,
                    'cumulative_pnl': 0  # Will be calculated below
                })
                
                current_date += timedelta(days=1)
            
            # Calculate cumulative P&L
            cumulative = 0
            for day in daily_data:
                cumulative += day['pnl']
                day['cumulative_pnl'] = cumulative
            
            return daily_data
            
        except Exception as e:
            logger.error(f"❌ Error generating daily P&L chart: {e}")
            return []
    
    async def _generate_symbol_performance(self, user_id: int, days: int, db: Session) -> List[Dict]:
        """Generate symbol performance analysis"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get trades grouped by symbol
            result = db.query(
                Trade.symbol,
                func.count(Trade.id).label('trade_count'),
                func.sum(Trade.pnl).label('total_pnl'),
                func.avg(Trade.pnl).label('avg_pnl'),
                func.sum(func.case([(Trade.pnl > 0, 1)], else_=0)).label('winning_trades')
            ).filter(
                and_(Trade.user_id == user_id, Trade.created_at >= start_date)
            ).group_by(Trade.symbol).all()
            
            symbol_data = []
            for row in result:
                win_rate = (row.winning_trades / row.trade_count * 100) if row.trade_count > 0 else 0
                
                symbol_data.append({
                    'symbol': row.symbol,
                    'trades': row.trade_count,
                    'total_pnl': float(row.total_pnl) if row.total_pnl else 0.0,
                    'avg_pnl': float(row.avg_pnl) if row.avg_pnl else 0.0,
                    'win_rate': win_rate,
                    'winning_trades': row.winning_trades
                })
            
            # Sort by total P&L descending
            symbol_data.sort(key=lambda x: x['total_pnl'], reverse=True)
            
            return symbol_data
            
        except Exception as e:
            logger.error(f"❌ Error generating symbol performance: {e}")
            return []
    
    async def _generate_strategy_performance(self, user_id: int, days: int, db: Session) -> List[Dict]:
        """Generate strategy performance analysis"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get trades grouped by strategy
            result = db.query(
                Trade.strategy,
                func.count(Trade.id).label('trade_count'),
                func.sum(Trade.pnl).label('total_pnl'),
                func.avg(Trade.pnl).label('avg_pnl'),
                func.sum(func.case([(Trade.pnl > 0, 1)], else_=0)).label('winning_trades')
            ).filter(
                and_(Trade.user_id == user_id, Trade.created_at >= start_date, Trade.strategy.isnot(None))
            ).group_by(Trade.strategy).all()
            
            strategy_data = []
            for row in result:
                win_rate = (row.winning_trades / row.trade_count * 100) if row.trade_count > 0 else 0
                
                strategy_data.append({
                    'strategy': row.strategy,
                    'trades': row.trade_count,
                    'total_pnl': float(row.total_pnl) if row.total_pnl else 0.0,
                    'avg_pnl': float(row.avg_pnl) if row.avg_pnl else 0.0,
                    'win_rate': win_rate,
                    'winning_trades': row.winning_trades
                })
            
            # Sort by total P&L descending
            strategy_data.sort(key=lambda x: x['total_pnl'], reverse=True)
            
            return strategy_data
            
        except Exception as e:
            logger.error(f"❌ Error generating strategy performance: {e}")
            return []
    
    async def _generate_monthly_summary(self, user_id: int, days: int, db: Session) -> List[Dict]:
        """Generate monthly summary"""
        try:
            # Get last 12 months or specified days, whichever is less
            months_to_analyze = min(12, days // 30 + 1)
            
            monthly_data = []
            current_date = datetime.utcnow()
            
            for i in range(months_to_analyze):
                month_start = current_date.replace(day=1) - timedelta(days=30*i)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                trades = db.query(Trade).filter(
                    and_(
                        Trade.user_id == user_id,
                        Trade.created_at >= month_start,
                        Trade.created_at <= month_end
                    )
                ).all()
                
                total_pnl = sum(float(t.pnl) for t in trades if t.pnl)
                trade_count = len(trades)
                winning_trades = len([t for t in trades if t.pnl and t.pnl > 0])
                win_rate = (winning_trades / trade_count * 100) if trade_count > 0 else 0
                
                monthly_data.append({
                    'month': month_start.strftime('%Y-%m'),
                    'trades': trade_count,
                    'total_pnl': total_pnl,
                    'win_rate': win_rate,
                    'winning_trades': winning_trades
                })
            
            return monthly_data
            
        except Exception as e:
            logger.error(f"❌ Error generating monthly summary: {e}")
            return []
    
    async def _generate_risk_analysis(self, user_id: int, days: int, db: Session) -> Dict:
        """Generate risk analysis"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            trades = db.query(Trade).filter(
                and_(Trade.user_id == user_id, Trade.created_at >= start_date)
            ).all()
            
            if not trades:
                return {'risk_level': 'No Data', 'analysis': 'Insufficient trading data'}
            
            # Calculate risk metrics
            pnl_values = [float(t.pnl) for t in trades if t.pnl]
            
            if not pnl_values:
                return {'risk_level': 'No Data', 'analysis': 'No P&L data available'}
            
            # Value at Risk (95th percentile)
            var_95 = np.percentile(pnl_values, 5) if len(pnl_values) > 1 else 0
            
            # Maximum consecutive losses
            max_consecutive_losses = self._calculate_max_consecutive_losses(trades)
            
            # Risk assessment
            risk_level = 'Low'
            if abs(var_95) > 1000 or max_consecutive_losses > 5:
                risk_level = 'High'
            elif abs(var_95) > 500 or max_consecutive_losses > 3:
                risk_level = 'Medium'
            
            return {
                'risk_level': risk_level,
                'var_95': var_95,
                'max_consecutive_losses': max_consecutive_losses,
                'volatility': float(np.std(pnl_values)) if len(pnl_values) > 1 else 0,
                'analysis': f'Risk level assessed as {risk_level} based on trading patterns'
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating risk analysis: {e}")
            return {'risk_level': 'Error', 'analysis': 'Unable to calculate risk metrics'}
    
    def _calculate_max_consecutive_losses(self, trades: List[Trade]) -> int:
        """Calculate maximum consecutive losses"""
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in sorted(trades, key=lambda x: x.created_at):
            if trade.pnl and trade.pnl < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    async def _generate_recommendations(self, metrics: UserPerformanceMetrics, db: Session) -> List[str]:
        """Generate trading recommendations based on performance"""
        recommendations = []
        
        try:
            # Win rate recommendations
            if metrics.win_rate < 40:
                recommendations.append("Consider reviewing your trading strategy - win rate is below 40%")
            elif metrics.win_rate > 70:
                recommendations.append("Excellent win rate! Continue with current strategy")
            
            # Risk management recommendations
            if metrics.max_drawdown > metrics.initial_capital * 0.2:
                recommendations.append("High drawdown detected - consider reducing position sizes")
            
            # Profit factor recommendations
            if metrics.profit_factor < 1.0:
                recommendations.append("Profit factor is below 1 - review risk/reward ratios")
            elif metrics.profit_factor > 2.0:
                recommendations.append("Strong profit factor - consider scaling up positions carefully")
            
            # Diversification recommendations
            if metrics.most_traded_symbol and metrics.total_trades > 10:
                # Check if too concentrated in one symbol
                recommendations.append("Consider diversifying across more symbols for better risk management")
            
            # Capital utilization
            if metrics.available_capital / metrics.initial_capital > 0.8:
                recommendations.append("High available capital - consider increasing position sizes gradually")
            elif metrics.available_capital / metrics.initial_capital < 0.2:
                recommendations.append("Low available capital - consider reducing exposure")
            
            # Activity recommendations
            if metrics.avg_trades_per_day < 1 and metrics.trading_days > 7:
                recommendations.append("Low trading frequency - consider more active trading or review strategy signals")
            elif metrics.avg_trades_per_day > 10:
                recommendations.append("High trading frequency - ensure you're not overtrading")
            
            if not recommendations:
                recommendations.append("Trading performance looks balanced - continue monitoring key metrics")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error generating recommendations: {e}")
            return ["Unable to generate recommendations due to calculation error"]

# Global instance
analytics_service = UserAnalyticsService()

# Dependency
async def get_analytics_service() -> UserAnalyticsService:
    if not analytics_service.is_initialized:
        await analytics_service.initialize()
    return analytics_service

# API Routes
@router.get("/user/{user_id}/performance")
async def get_user_performance(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    service: UserAnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive performance metrics for a user"""
    metrics = await service.get_user_performance_metrics(user_id, days)
    
    return {
        'user_id': metrics.user_id,
        'username': metrics.username,
        'period_days': days,
        'trading_statistics': {
            'total_trades': metrics.total_trades,
            'winning_trades': metrics.winning_trades,
            'losing_trades': metrics.losing_trades,
            'win_rate': metrics.win_rate,
            'avg_win_amount': metrics.avg_win_amount,
            'avg_loss_amount': metrics.avg_loss_amount,
            'profit_factor': metrics.profit_factor
        },
        'pnl_metrics': {
            'total_pnl': metrics.total_pnl,
            'daily_pnl': metrics.daily_pnl,
            'weekly_pnl': metrics.weekly_pnl,
            'monthly_pnl': metrics.monthly_pnl,
            'yearly_pnl': metrics.yearly_pnl
        },
        'risk_metrics': {
            'max_profit': metrics.max_profit,
            'max_loss': metrics.max_loss,
            'max_drawdown': metrics.max_drawdown,
            'sharpe_ratio': metrics.sharpe_ratio,
            'sortino_ratio': metrics.sortino_ratio,
            'calmar_ratio': metrics.calmar_ratio
        },
        'trading_behavior': {
            'avg_trade_duration_hours': metrics.avg_trade_duration_hours,
            'avg_position_size': metrics.avg_position_size,
            'most_traded_symbol': metrics.most_traded_symbol,
            'most_profitable_strategy': metrics.most_profitable_strategy
        },
        'capital_metrics': {
            'initial_capital': metrics.initial_capital,
            'current_balance': metrics.current_balance,
            'peak_balance': metrics.peak_balance,
            'total_invested': metrics.total_invested,
            'available_capital': metrics.available_capital,
            'margin_used': metrics.margin_used
        },
        'activity_metrics': {
            'active_positions': metrics.active_positions,
            'pending_orders': metrics.pending_orders,
            'last_trade_date': metrics.last_trade_date,
            'trading_days': metrics.trading_days,
            'avg_trades_per_day': metrics.avg_trades_per_day
        }
    }

@router.get("/user/{user_id}/report")
async def get_user_trading_report(
    user_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    service: UserAnalyticsService = Depends(get_analytics_service)
):
    """Generate comprehensive trading report for a user"""
    report = await service.generate_user_trading_report(user_id, days)
    
    return {
        'user_id': report.user_id,
        'username': report.username,
        'report_period': report.report_period,
        'generated_at': report.generated_at,
        'performance_summary': {
            'total_trades': report.performance_metrics.total_trades,
            'win_rate': report.performance_metrics.win_rate,
            'total_pnl': report.performance_metrics.total_pnl,
            'sharpe_ratio': report.performance_metrics.sharpe_ratio
        },
        'daily_pnl_chart': report.daily_pnl_chart,
        'symbol_performance': report.symbol_performance,
        'strategy_performance': report.strategy_performance,
        'monthly_summary': report.monthly_summary,
        'risk_analysis': report.risk_analysis,
        'recommendations': report.recommendations
    }

@router.get("/user/{user_id}/dashboard")
async def get_user_dashboard_data(
    user_id: int,
    service: UserAnalyticsService = Depends(get_analytics_service)
):
    """Get dashboard data for a specific user"""
    try:
        # Get 7-day and 30-day metrics
        metrics_7d = await service.get_user_performance_metrics(user_id, 7)
        metrics_30d = await service.get_user_performance_metrics(user_id, 30)
        
        return {
            'user_id': user_id,
            'username': metrics_30d.username,
            'current_status': {
                'current_balance': metrics_30d.current_balance,
                'available_capital': metrics_30d.available_capital,
                'active_positions': metrics_30d.active_positions,
                'pending_orders': metrics_30d.pending_orders
            },
            'performance_7d': {
                'total_trades': metrics_7d.total_trades,
                'win_rate': metrics_7d.win_rate,
                'total_pnl': metrics_7d.total_pnl,
                'daily_pnl': metrics_7d.daily_pnl
            },
            'performance_30d': {
                'total_trades': metrics_30d.total_trades,
                'win_rate': metrics_30d.win_rate,
                'total_pnl': metrics_30d.total_pnl,
                'max_drawdown': metrics_30d.max_drawdown
            },
            'last_activity': metrics_30d.last_trade_date
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting dashboard data for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")

@router.get("/users/leaderboard")
async def get_users_leaderboard(
    metric: str = Query("total_pnl", description="Metric to rank by: total_pnl, win_rate, sharpe_ratio"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(10, ge=1, le=50, description="Number of users to return"),
    service: UserAnalyticsService = Depends(get_analytics_service)
):
    """Get leaderboard of top performing users"""
    try:
        db = service.get_db_session()
        
        # Get all active users
        users = db.query(User).filter(User.is_active == True).all()
        
        # Calculate metrics for each user
        user_metrics = []
        for user in users:
            try:
                metrics = await service.get_user_performance_metrics(user.id, days)
                user_metrics.append({
                    'user_id': user.id,
                    'username': user.username,
                    'total_pnl': metrics.total_pnl,
                    'win_rate': metrics.win_rate,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'total_trades': metrics.total_trades,
                    'current_balance': metrics.current_balance
                })
            except Exception as e:
                logger.warning(f"⚠️ Error calculating metrics for user {user.id}: {e}")
                continue
        
        # Sort by specified metric
        if metric == "total_pnl":
            user_metrics.sort(key=lambda x: x['total_pnl'], reverse=True)
        elif metric == "win_rate":
            user_metrics.sort(key=lambda x: x['win_rate'], reverse=True)
        elif metric == "sharpe_ratio":
            user_metrics.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        else:
            # Default to total P&L
            user_metrics.sort(key=lambda x: x['total_pnl'], reverse=True)
        
        # Add ranking
        for i, user_data in enumerate(user_metrics[:limit]):
            user_data['rank'] = i + 1
        
        return {
            'leaderboard': user_metrics[:limit],
            'metric': metric,
            'period_days': days,
            'total_users': len(user_metrics)
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating leaderboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate leaderboard")
    finally:
        db.close() 