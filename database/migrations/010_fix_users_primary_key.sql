-- Migration: Fix Users Table Primary Key
-- Version: 010
-- Date: 2025-07-15
-- Description: Add PRIMARY KEY constraint to existing users.id column safely

BEGIN;

-- Check and fix users table primary key
DO $$
DECLARE
    has_id_column BOOLEAN;
    has_primary_key BOOLEAN;
    existing_primary_key TEXT;
BEGIN
    -- Check if users table has id column
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'id'
    ) INTO has_id_column;
    
    -- Check if users table has any primary key
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'users' AND constraint_type = 'PRIMARY KEY'
    ) INTO has_primary_key;
    
    -- Get existing primary key constraint name if any
    SELECT constraint_name INTO existing_primary_key
    FROM information_schema.table_constraints 
    WHERE table_name = 'users' AND constraint_type = 'PRIMARY KEY'
    LIMIT 1;
    
    RAISE NOTICE 'Users table analysis: has_id_column=%, has_primary_key=%, existing_pk=%', 
                 has_id_column, has_primary_key, existing_primary_key;
    
    IF NOT has_id_column THEN
        -- Add id column if missing
        ALTER TABLE users ADD COLUMN id SERIAL PRIMARY KEY;
        RAISE NOTICE 'Added missing id column as primary key';
        
    ELSIF NOT has_primary_key THEN
        -- Make existing id column the primary key
        ALTER TABLE users ADD CONSTRAINT users_pkey PRIMARY KEY (id);
        RAISE NOTICE 'Added primary key constraint to existing id column';
        
    ELSE
        -- Check if primary key is on id column
        IF EXISTS (
            SELECT 1 FROM information_schema.key_column_usage k
            JOIN information_schema.table_constraints t ON k.constraint_name = t.constraint_name
            WHERE t.table_name = 'users' 
            AND t.constraint_type = 'PRIMARY KEY' 
            AND k.column_name = 'id'
        ) THEN
            RAISE NOTICE 'Users table already has correct primary key on id column';
        ELSE
            RAISE NOTICE 'Users table has primary key but not on id column - manual intervention needed';
        END IF;
    END IF;
    
    -- Ensure at least one user exists for paper trading
    IF NOT EXISTS (SELECT 1 FROM users LIMIT 1) THEN
        -- Insert paper trading user
        INSERT INTO users (
            username, 
            email, 
            password_hash, 
            full_name, 
            initial_capital, 
            current_balance, 
            risk_tolerance, 
            is_active, 
            zerodha_client_id,
            trading_enabled,
            max_daily_trades,
            max_position_size
        ) VALUES (
            'PAPER_TRADER_001',
            'paper.trader@algoauto.com',
            '$2b$12$dummy.hash.for.paper.trading.user.not.used.for.login',
            'AlgoAuto Paper Trading Master',
            100000.00,
            100000.00,
            'medium',
            true,
            'PAPER_API_KEY',
            true,
            1000,
            500000.00
        );
        
        RAISE NOTICE 'Created paper trading user';
    ELSE
        RAISE NOTICE 'Paper trading user already exists';
    END IF;
    
END $$;

-- Verify the fix works
DO $$
DECLARE
    test_result INTEGER;
BEGIN
    -- Test that the problematic query now works
    SELECT id INTO test_result FROM users LIMIT 1;
    RAISE NOTICE 'SUCCESS: SELECT id FROM users query works correctly, first user id=%', test_result;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'FAILED: SELECT id FROM users still failing: %', SQLERRM;
END $$;

COMMIT; 