-- Migration: Deployment Cleanup - Remove All Fake/Simulated Trades  
-- Version: 013
-- Date: 2025-07-17
-- Description: CRITICAL CLEANUP - Remove all fake/mock/simulated trades that have contaminated the database

BEGIN;

-- SAFETY: Log what we're about to delete
DO $$
DECLARE
    trade_count INTEGER;
    position_count INTEGER;
    order_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO trade_count FROM trades;
    SELECT COUNT(*) INTO position_count FROM positions;
    SELECT COUNT(*) INTO order_count FROM orders;
    
    RAISE NOTICE 'CLEANUP: Found % trades, % positions, % orders - DELETING ALL FAKE DATA', trade_count, position_count, order_count;
END $$;

-- CRITICAL: Delete all fake/simulated trades and related data
DELETE FROM trades WHERE 1=1;
DELETE FROM positions WHERE 1=1;  
DELETE FROM orders WHERE 1=1;
DELETE FROM paper_trades WHERE 1=1;

-- Clear any trade-related cache or session data
DELETE FROM user_metrics WHERE 1=1;
DELETE FROM audit_logs WHERE entity_type IN ('TRADE', 'ORDER', 'POSITION');

-- Reset auto-increment sequences to start fresh
ALTER SEQUENCE trades_trade_id_seq RESTART WITH 1;
ALTER SEQUENCE positions_position_id_seq RESTART WITH 1;

-- Ensure clean user state for paper trading
UPDATE users 
SET 
    current_balance = initial_capital,
    updated_at = NOW()
WHERE username = 'PAPER_TRADER_001';

-- Log cleanup completion
DO $$
DECLARE
    trade_count INTEGER;
    position_count INTEGER;
    order_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO trade_count FROM trades;
    SELECT COUNT(*) INTO position_count FROM positions;
    SELECT COUNT(*) INTO order_count FROM orders;
    
    RAISE NOTICE 'CLEANUP COMPLETE: Database now has % trades, % positions, % orders (should all be 0)', trade_count, position_count, order_count;
    
    IF trade_count > 0 OR position_count > 0 OR order_count > 0 THEN
        RAISE EXCEPTION 'CLEANUP FAILED: Still have fake data in database';
    END IF;
    
    RAISE NOTICE 'SUCCESS: Database is now clean - ready for REAL trading only';
END $$;

COMMIT; 