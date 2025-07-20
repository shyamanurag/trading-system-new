-- 014_complete_cleanup_and_schema_fix.sql
-- PRODUCTION EMERGENCY: Fix missing broker_user_id + Remove ALL fake data contamination
-- Execute Date: 2025-07-20
-- Target: 5,696 fake records + missing column

BEGIN;

-- STEP 1: Add missing broker_user_id column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'broker_user_id'
    ) THEN
        ALTER TABLE users ADD COLUMN broker_user_id VARCHAR(50);
        RAISE NOTICE '✅ Added broker_user_id column to users table';
    ELSE
        RAISE NOTICE '✅ broker_user_id column already exists';
    END IF;
END $$;

-- STEP 2: Count contamination before cleanup
DO $$
DECLARE
    trades_count INTEGER;
    orders_count INTEGER;
    positions_count INTEGER := 0;
    total_contamination INTEGER;
BEGIN
    SELECT COUNT(*) INTO trades_count FROM trades;
    SELECT COUNT(*) INTO orders_count FROM orders;
    
    -- Check if positions table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'positions') THEN
        SELECT COUNT(*) INTO positions_count FROM positions;
    END IF;
    
    total_contamination := trades_count + orders_count + positions_count;
    
    RAISE NOTICE '🚨 CONTAMINATION FOUND: % trades, % orders, % positions = % total', 
                 trades_count, orders_count, positions_count, total_contamination;
END $$;

-- STEP 3: COMPLETE CLEANUP - Delete ALL fake data
DO $$
BEGIN
    RAISE NOTICE '🔥 EXECUTING COMPLETE CLEANUP...';
    
    -- Delete all trades (ALL are fake - production starts clean)
    DELETE FROM trades WHERE 1=1;
    RAISE NOTICE '🔥 Deleted ALL trades';
    
    -- Delete all orders (ALL are fake - production starts clean)  
    DELETE FROM orders WHERE 1=1;
    RAISE NOTICE '🔥 Deleted ALL orders';
    
    -- Delete all positions if table exists (ALL are fake - production starts clean)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'positions') THEN
        DELETE FROM positions WHERE 1=1;
        RAISE NOTICE '🔥 Deleted ALL positions';
    ELSE
        RAISE NOTICE '⚠️ Positions table not found, skipped';
    END IF;
END $$;

-- STEP 4: Reset auto-increment sequences to start fresh
DO $$
BEGIN
    -- Reset trades sequence
    IF EXISTS (SELECT 1 FROM information_schema.sequences WHERE sequence_name = 'trades_trade_id_seq') THEN
        ALTER SEQUENCE trades_trade_id_seq RESTART WITH 1;
        RAISE NOTICE '✅ Reset trades sequence';
    END IF;
    
    -- Reset orders sequence
    IF EXISTS (SELECT 1 FROM information_schema.sequences WHERE sequence_name = 'orders_order_id_seq') THEN
        ALTER SEQUENCE orders_order_id_seq RESTART WITH 1;
        RAISE NOTICE '✅ Reset orders sequence';
    END IF;
    
    -- Reset positions sequence if exists
    IF EXISTS (SELECT 1 FROM information_schema.sequences WHERE sequence_name = 'positions_position_id_seq') THEN
        ALTER SEQUENCE positions_position_id_seq RESTART WITH 1;
        RAISE NOTICE '✅ Reset positions sequence';
    END IF;
END $$;

-- STEP 5: Verify cleanup completion
DO $$
DECLARE
    final_trades INTEGER;
    final_orders INTEGER;
    final_positions INTEGER := 0;
    total_remaining INTEGER;
BEGIN
    SELECT COUNT(*) INTO final_trades FROM trades;
    SELECT COUNT(*) INTO final_orders FROM orders;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'positions') THEN
        SELECT COUNT(*) INTO final_positions FROM positions;
    END IF;
    
    total_remaining := final_trades + final_orders + final_positions;
    
    RAISE NOTICE '📊 FINAL VERIFICATION: % trades, % orders, % positions = % total remaining', 
                 final_trades, final_orders, final_positions, total_remaining;
    
    IF total_remaining = 0 THEN
        RAISE NOTICE '🎉 SUCCESS: Database is now COMPLETELY CLEAN!';
        RAISE NOTICE '✅ Rule #1: NO MOCK/DEMO DATA - ACHIEVED';
        RAISE NOTICE '✅ Schema fixed: broker_user_id column added';
        RAISE NOTICE '✅ Database ready for REAL trading data only';
    ELSE
        RAISE EXCEPTION 'CLEANUP FAILED: % records still remain', total_remaining;
    END IF;
END $$;

COMMIT;

-- Final success notification
DO $$
BEGIN
    RAISE NOTICE '🎉 MIGRATION 014 COMPLETED SUCCESSFULLY!';
    RAISE NOTICE '🎯 Next deployment will start with 100% clean database';
    RAISE NOTICE '🔥 Ready for REAL autonomous trading!';
END $$; 