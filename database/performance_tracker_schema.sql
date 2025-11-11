-- Performance Tracking Database Schema
-- Tracks every trade, daily performance, and system analytics

-- Table 1: Trade History (Every single trade executed)
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    trade_id VARCHAR(100) UNIQUE NOT NULL,  -- Unique trade identifier
    symbol VARCHAR(50) NOT NULL,
    underlying_symbol VARCHAR(50),  -- For options: BHARTIARTL from BHARTIARTL25OCT2000CE
    instrument_type VARCHAR(20) NOT NULL,  -- 'EQUITY' or 'OPTIONS'
    option_type VARCHAR(10),  -- 'CE', 'PE', or NULL for equity
    strike_price DECIMAL(10, 2),
    expiry_date DATE,
    
    -- Entry Details
    entry_time TIMESTAMP NOT NULL,
    entry_price DECIMAL(10, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    side VARCHAR(10) NOT NULL,  -- 'long' or 'short'
    entry_order_id VARCHAR(100),
    
    -- Exit Details
    exit_time TIMESTAMP,
    exit_price DECIMAL(10, 2),
    exit_order_id VARCHAR(100),
    exit_reason VARCHAR(100),  -- 'target', 'stop_loss', 'trailing_stop', 'time_based', 'manual'
    
    -- P&L Calculation
    gross_pnl DECIMAL(12, 2),
    commission DECIMAL(10, 2) DEFAULT 0,
    taxes DECIMAL(10, 2) DEFAULT 0,
    net_pnl DECIMAL(12, 2),
    pnl_percent DECIMAL(8, 4),
    
    -- Risk Metrics
    risk_amount DECIMAL(12, 2),  -- Initial risk (entry - stop_loss) * qty
    reward_amount DECIMAL(12, 2),  -- Initial reward (target - entry) * qty
    risk_reward_ratio DECIMAL(8, 2),
    max_adverse_excursion DECIMAL(12, 2),  -- MAE: Worst drawdown during trade
    max_favorable_excursion DECIMAL(12, 2),  -- MFE: Best profit during trade
    
    -- Strategy Info
    strategy_name VARCHAR(100) NOT NULL,
    signal_confidence DECIMAL(4, 2),
    market_bias VARCHAR(20),  -- 'bullish', 'bearish', 'neutral', 'choppy'
    market_regime VARCHAR(20),  -- 'trending', 'ranging', 'volatile'
    
    -- Trade Context
    capital_at_entry DECIMAL(15, 2),
    position_size_pct DECIMAL(6, 4),  -- Position size as % of capital
    daily_pnl_at_entry DECIMAL(12, 2),  -- Daily P&L when this trade was entered
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'open',  -- 'open', 'closed', 'cancelled'
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for fast queries
    INDEX idx_symbol (symbol),
    INDEX idx_underlying (underlying_symbol),
    INDEX idx_entry_time (entry_time),
    INDEX idx_status (status),
    INDEX idx_strategy (strategy_name),
    INDEX idx_instrument (instrument_type)
);

-- Table 2: Daily Performance Summary
CREATE TABLE IF NOT EXISTS daily_performance (
    id SERIAL PRIMARY KEY,
    trading_date DATE UNIQUE NOT NULL,
    
    -- Capital
    starting_capital DECIMAL(15, 2) NOT NULL,
    ending_capital DECIMAL(15, 2) NOT NULL,
    
    -- Trading Activity
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    breakeven_trades INTEGER DEFAULT 0,
    
    -- Options vs Equity
    options_trades INTEGER DEFAULT 0,
    equity_trades INTEGER DEFAULT 0,
    options_pnl DECIMAL(12, 2) DEFAULT 0,
    equity_pnl DECIMAL(12, 2) DEFAULT 0,
    
    -- P&L Metrics
    gross_pnl DECIMAL(12, 2) NOT NULL,
    total_commission DECIMAL(10, 2) DEFAULT 0,
    total_taxes DECIMAL(10, 2) DEFAULT 0,
    net_pnl DECIMAL(12, 2) NOT NULL,
    pnl_percent DECIMAL(8, 4) NOT NULL,
    
    -- Performance Metrics
    win_rate DECIMAL(6, 4),  -- Winning trades / Total trades
    avg_win DECIMAL(12, 2),
    avg_loss DECIMAL(12, 2),
    largest_win DECIMAL(12, 2),
    largest_loss DECIMAL(12, 2),
    profit_factor DECIMAL(8, 2),  -- Gross profit / Gross loss
    
    -- Risk Metrics
    max_drawdown DECIMAL(12, 2),
    max_drawdown_pct DECIMAL(8, 4),
    sharpe_ratio DECIMAL(8, 4),
    
    -- Exposure Tracking
    max_portfolio_exposure DECIMAL(8, 4),  -- Max % of capital in trades
    max_options_exposure DECIMAL(8, 4),
    avg_position_size_pct DECIMAL(6, 4),
    
    -- Loss Limit Tracking
    daily_loss_limit_pct DECIMAL(6, 4) DEFAULT 0.02,  -- 2%
    loss_limit_breached BOOLEAN DEFAULT FALSE,
    breach_time TIMESTAMP,
    trades_after_breach INTEGER DEFAULT 0,
    
    -- Market Conditions
    nifty_open DECIMAL(10, 2),
    nifty_close DECIMAL(10, 2),
    nifty_change_pct DECIMAL(8, 4),
    market_regime VARCHAR(20),  -- Overall regime for the day
    
    -- Strategy Performance
    best_strategy VARCHAR(100),
    worst_strategy VARCHAR(100),
    
    -- Notes
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_trading_date (trading_date),
    INDEX idx_pnl (net_pnl)
);

-- Table 3: Strategy Performance Tracking
CREATE TABLE IF NOT EXISTS strategy_performance (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) NOT NULL,
    trading_date DATE NOT NULL,
    
    -- Trading Activity
    total_signals INTEGER DEFAULT 0,
    signals_executed INTEGER DEFAULT 0,
    signals_rejected INTEGER DEFAULT 0,
    execution_rate DECIMAL(6, 4),
    
    -- Trades
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    
    -- P&L
    gross_pnl DECIMAL(12, 2) DEFAULT 0,
    net_pnl DECIMAL(12, 2) DEFAULT 0,
    pnl_contribution_pct DECIMAL(6, 4),  -- % of daily P&L from this strategy
    
    -- Performance Metrics
    win_rate DECIMAL(6, 4),
    avg_win DECIMAL(12, 2),
    avg_loss DECIMAL(12, 2),
    profit_factor DECIMAL(8, 2),
    avg_confidence DECIMAL(4, 2),
    
    -- Risk Metrics
    total_risk_taken DECIMAL(15, 2),
    max_single_loss DECIMAL(12, 2),
    avg_risk_reward DECIMAL(8, 2),
    
    -- Market Conditions
    best_market_regime VARCHAR(20),  -- Which regime this strategy performs best in
    worst_market_regime VARCHAR(20),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_strategy_date (strategy_name, trading_date),
    INDEX idx_strategy_date (strategy_name, trading_date),
    INDEX idx_pnl (net_pnl)
);

-- Table 4: Real-time Position Tracking (Active positions)
CREATE TABLE IF NOT EXISTS active_positions (
    id SERIAL PRIMARY KEY,
    trade_id VARCHAR(100) UNIQUE NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    
    -- Position Details
    entry_time TIMESTAMP NOT NULL,
    entry_price DECIMAL(10, 2) NOT NULL,
    current_price DECIMAL(10, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    side VARCHAR(10) NOT NULL,
    
    -- Risk Management
    stop_loss DECIMAL(10, 2) NOT NULL,
    target DECIMAL(10, 2) NOT NULL,
    trailing_stop DECIMAL(10, 2),
    
    -- P&L Tracking
    unrealized_pnl DECIMAL(12, 2) NOT NULL,
    unrealized_pnl_pct DECIMAL(8, 4) NOT NULL,
    max_profit DECIMAL(12, 2) DEFAULT 0,  -- Peak profit seen
    max_loss DECIMAL(12, 2) DEFAULT 0,  -- Worst loss seen
    
    -- Partial Exit Tracking
    partial_exit_done BOOLEAN DEFAULT FALSE,
    original_quantity INTEGER,
    partial_exit_quantity INTEGER,
    partial_exit_pnl DECIMAL(12, 2),
    
    -- Strategy Info
    strategy_name VARCHAR(100) NOT NULL,
    signal_confidence DECIMAL(4, 2),
    
    -- Timestamps
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_symbol (symbol),
    INDEX idx_strategy (strategy_name),
    INDEX idx_entry_time (entry_time)
);

-- Table 5: System Events Log (Critical events, errors, breaches)
CREATE TABLE IF NOT EXISTS system_events (
    id SERIAL PRIMARY KEY,
    event_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(50) NOT NULL,  -- 'loss_limit_breach', 'connection_error', 'token_refresh', 'manual_override'
    severity VARCHAR(20) NOT NULL,  -- 'info', 'warning', 'error', 'critical'
    component VARCHAR(100),  -- 'orchestrator', 'trade_engine', 'position_monitor', etc.
    
    -- Event Details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    affected_symbols TEXT,  -- JSON array of affected symbols
    
    -- Context
    capital_at_event DECIMAL(15, 2),
    daily_pnl_at_event DECIMAL(12, 2),
    open_positions_count INTEGER,
    
    -- Resolution
    resolved BOOLEAN DEFAULT FALSE,
    resolution_time TIMESTAMP,
    resolution_notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_event_time (event_time),
    INDEX idx_event_type (event_type),
    INDEX idx_severity (severity),
    INDEX idx_resolved (resolved)
);

-- Table 6: Market Data Snapshots (Periodic snapshots for backtesting and analysis)
CREATE TABLE IF NOT EXISTS market_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_time TIMESTAMP NOT NULL,
    
    -- NIFTY Data
    nifty_price DECIMAL(10, 2),
    nifty_change_pct DECIMAL(8, 4),
    nifty_volatility DECIMAL(8, 4),
    
    -- Market Metrics
    market_bias VARCHAR(20),  -- 'bullish', 'bearish', 'neutral'
    market_regime VARCHAR(20),  -- 'trending', 'choppy', 'volatile'
    regime_confidence DECIMAL(4, 2),
    
    -- VIX Data (if available)
    vix_level DECIMAL(8, 2),
    
    -- Portfolio State
    total_capital DECIMAL(15, 2),
    open_positions INTEGER,
    portfolio_exposure DECIMAL(8, 4),
    daily_pnl DECIMAL(12, 2),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_snapshot_time (snapshot_time)
);

-- Trigger: Update updated_at on trades table
CREATE OR REPLACE FUNCTION update_trades_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_trades_timestamp
BEFORE UPDATE ON trades
FOR EACH ROW
EXECUTE FUNCTION update_trades_timestamp();

-- Trigger: Update updated_at on daily_performance table
CREATE TRIGGER trigger_update_daily_performance_timestamp
BEFORE UPDATE ON daily_performance
FOR EACH ROW
EXECUTE FUNCTION update_trades_timestamp();

-- Trigger: Update updated_at on strategy_performance table
CREATE TRIGGER trigger_update_strategy_performance_timestamp
BEFORE UPDATE ON strategy_performance
FOR EACH ROW
EXECUTE FUNCTION update_trades_timestamp();

-- Views for Quick Analytics

-- View 1: Today's Active Trades
CREATE OR REPLACE VIEW todays_trades AS
SELECT 
    t.trade_id,
    t.symbol,
    t.instrument_type,
    t.entry_time,
    t.entry_price,
    t.exit_time,
    t.exit_price,
    t.net_pnl,
    t.pnl_percent,
    t.exit_reason,
    t.strategy_name,
    t.status
FROM trades t
WHERE DATE(t.entry_time) = CURRENT_DATE
ORDER BY t.entry_time DESC;

-- View 2: Current Performance Summary
CREATE OR REPLACE VIEW current_performance AS
SELECT 
    COUNT(*) as total_trades,
    SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(CASE WHEN net_pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
    SUM(net_pnl) as total_pnl,
    AVG(CASE WHEN net_pnl > 0 THEN net_pnl ELSE NULL END) as avg_win,
    AVG(CASE WHEN net_pnl < 0 THEN net_pnl ELSE NULL END) as avg_loss,
    MAX(net_pnl) as largest_win,
    MIN(net_pnl) as largest_loss
FROM trades
WHERE DATE(entry_time) = CURRENT_DATE
AND status = 'closed';

-- View 3: Strategy Leaderboard (Last 7 days)
CREATE OR REPLACE VIEW strategy_leaderboard AS
SELECT 
    strategy_name,
    COUNT(*) as total_trades,
    SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as wins,
    SUM(net_pnl) as total_pnl,
    AVG(pnl_percent) as avg_return_pct,
    AVG(signal_confidence) as avg_confidence
FROM trades
WHERE entry_time >= CURRENT_DATE - INTERVAL '7 days'
AND status = 'closed'
GROUP BY strategy_name
ORDER BY total_pnl DESC;

-- Initial Data Verification
SELECT 'Performance tracking database schema created successfully!' as status;


