-- Fix Dashboard Issues - Missing Database Columns
-- Date: 2025-07-29
-- Issue: column "updated_at" of relation "trades" does not exist

BEGIN;

-- Add missing updated_at column to trades table
DO $$ 
BEGIN
    -- Check if updated_at column exists, if not add it
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trades' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE trades ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        RAISE NOTICE 'Added updated_at column to trades table';
    ELSE
        RAISE NOTICE 'updated_at column already exists in trades table';
    END IF;
END $$;

-- Update existing trades with current timestamp for updated_at
UPDATE trades 
SET updated_at = created_at 
WHERE updated_at IS NULL;

-- Create index on updated_at for better performance
CREATE INDEX IF NOT EXISTS idx_trades_updated_at ON trades(updated_at);

COMMIT;

-- Verify the fix
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'trades' 
AND column_name IN ('created_at', 'executed_at', 'updated_at')
ORDER BY column_name; 