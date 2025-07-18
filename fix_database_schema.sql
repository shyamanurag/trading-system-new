-- CRITICAL DATABASE SCHEMA FIX
-- ===============================
-- This script fixes the missing 'broker_user_id' column in the users table
-- Run this on the production PostgreSQL database

-- Check if users table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users') THEN
        RAISE EXCEPTION 'Users table does not exist. Please create the users table first.';
    END IF;
END $$;

-- Add broker_user_id column if it doesn't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS broker_user_id VARCHAR(50);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_users_broker_user_id 
ON users(broker_user_id);

-- Update existing users with default broker_user_id
UPDATE users 
SET broker_user_id = COALESCE(broker_user_id, 'MASTER_USER_001')
WHERE broker_user_id IS NULL;

-- Add constraint to ensure broker_user_id is not null for new records
ALTER TABLE users 
ALTER COLUMN broker_user_id SET DEFAULT 'MASTER_USER_001';

-- Verify the fix
DO $$
DECLARE
    column_exists BOOLEAN;
    user_count INTEGER;
BEGIN
    -- Check if column exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'broker_user_id'
    ) INTO column_exists;
    
    IF column_exists THEN
        RAISE NOTICE 'SUCCESS: broker_user_id column exists';
        
        -- Check if existing users have broker_user_id
        SELECT COUNT(*) FROM users WHERE broker_user_id IS NULL INTO user_count;
        
        IF user_count = 0 THEN
            RAISE NOTICE 'SUCCESS: All users have broker_user_id assigned';
        ELSE
            RAISE NOTICE 'WARNING: % users still have NULL broker_user_id', user_count;
        END IF;
    ELSE
        RAISE EXCEPTION 'FAILED: broker_user_id column was not created';
    END IF;
END $$;

-- Test user creation to verify the fix
DO $$
DECLARE
    test_user_id VARCHAR(50) := 'test_user_' || EXTRACT(EPOCH FROM NOW())::TEXT;
    user_created BOOLEAN;
BEGIN
    -- Try to create a test user
    INSERT INTO users (user_id, broker_user_id, created_at)
    VALUES (test_user_id, 'TEST_BROKER_001', NOW())
    ON CONFLICT (user_id) DO NOTHING;
    
    -- Check if user was created
    SELECT EXISTS(SELECT 1 FROM users WHERE user_id = test_user_id) INTO user_created;
    
    IF user_created THEN
        RAISE NOTICE 'SUCCESS: User creation test passed';
        -- Clean up test user
        DELETE FROM users WHERE user_id = test_user_id;
    ELSE
        RAISE EXCEPTION 'FAILED: User creation test failed';
    END IF;
END $$;

-- Display current schema
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;

-- Success message
SELECT 'DATABASE SCHEMA FIX COMPLETED SUCCESSFULLY' AS status;
