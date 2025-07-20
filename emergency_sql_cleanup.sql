-- EMERGENCY CLEANUP: Remove ALL FAKE DATA CONTAMINATION
-- PostgreSQL version of 005_clean_fake_data.sql
-- Removes all mock/fake data contamination for REAL money trading ONLY

BEGIN;

-- Log what we're about to delete
DO $$
DECLARE
    trade_count INTEGER;
    position_count INTEGER;
    order_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO trade_count FROM trades;
    SELECT COUNT(*) INTO order_count FROM orders;
    
    -- Try positions table if it exists
    BEGIN
        SELECT COUNT(*) INTO position_count FROM positions;
    EXCEPTION
        WHEN undefined_table THEN position_count := 0;
    END;
    
    RAISE NOTICE 'EMERGENCY CLEANUP: Deleting % trades, % positions, % orders - ALL FAKE DATA REMOVAL', trade_count, position_count, order_count;
END $$;

-- CRITICAL: Delete ALL fake/contaminated data
DELETE FROM trades WHERE 1=1;
DELETE FROM orders WHERE 1=1;

-- Delete positions if table exists
DO $$
BEGIN
    DELETE FROM positions WHERE 1=1;
EXCEPTION
    WHEN undefined_table THEN
        RAISE NOTICE 'Positions table does not exist, skipping...';
END $$;

-- Delete other fake data if tables exist
DO $$
BEGIN
    DELETE FROM daily_pnl WHERE 1=1;
EXCEPTION
    WHEN undefined_table THEN
        RAISE NOTICE 'daily_pnl table does not exist, skipping...';
END $$;

DO $$
BEGIN
    DELETE FROM trading_sessions WHERE 1=1;
EXCEPTION
    WHEN undefined_table THEN
        RAISE NOTICE 'trading_sessions table does not exist, skipping...';
END $$;

-- Reset auto-increment sequences for PostgreSQL
ALTER SEQUENCE IF EXISTS trades_trade_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS orders_order_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS positions_position_id_seq RESTART WITH 1;

-- Verify cleanup
DO $$
DECLARE
    final_trades INTEGER;
    final_orders INTEGER;
    final_positions INTEGER;
BEGIN
    SELECT COUNT(*) INTO final_trades FROM trades;
    SELECT COUNT(*) INTO final_orders FROM orders;
    
    -- Try positions
    BEGIN
        SELECT COUNT(*) INTO final_positions FROM positions;
    EXCEPTION
        WHEN undefined_table THEN final_positions := 0;
    END;
    
    RAISE NOTICE 'CLEANUP COMPLETE: Database now has % trades, % orders, % positions (should all be 0)', final_trades, final_orders, final_positions;
    
    IF final_trades > 0 OR final_orders > 0 OR final_positions > 0 THEN
        RAISE EXCEPTION 'CLEANUP FAILED: Still have fake data in database - % trades, % orders, % positions', final_trades, final_orders, final_positions;
    END IF;
    
    RAISE NOTICE 'SUCCESS: Database is CLEAN - ready for REAL trading data only!';
END $$;

COMMIT;

SELECT 'EMERGENCY CLEANUP COMPLETED - Database purged of ALL fake data' as status; 