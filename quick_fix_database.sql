-- Quick Database Fix for Paper Trading
-- Run this directly in your database to fix the users table

-- 1. Add id column if missing
ALTER TABLE users ADD COLUMN IF NOT EXISTS id SERIAL PRIMARY KEY;

-- 2. Create user with id=1 for paper trading
INSERT INTO users (
    id, username, email, password_hash, full_name, 
    initial_capital, current_balance, risk_tolerance, 
    is_active, zerodha_client_id, trading_enabled,
    max_daily_trades, max_position_size, created_at, updated_at
) VALUES (
    1, 'PAPER_TRADER_001', 'paper@algoauto.com', 
    '$2b$12$dummy', 'Paper Trading Account',
    100000, 100000, 'medium',
    true, 'PAPER', true,
    1000, 500000, NOW(), NOW()
) ON CONFLICT (id) DO UPDATE SET
    trading_enabled = true,
    is_active = true,
    updated_at = NOW();

-- 3. Verify the fix
SELECT id, username, email, trading_enabled FROM users WHERE id = 1;

-- 4. Check if trades can now be inserted
-- This should work without foreign key errors
INSERT INTO trades (
    order_id, user_id, symbol, trade_type, quantity,
    price, commission, strategy, executed_at, created_at
) VALUES (
    'TEST_' || EXTRACT(EPOCH FROM NOW())::TEXT, 
    1, 'TEST', 'BUY', 1,
    100, 0, 'PAPER_TEST', NOW(), NOW()
);

-- 5. View recent trades
SELECT * FROM trades WHERE created_at > NOW() - INTERVAL '1 hour' ORDER BY created_at DESC; 