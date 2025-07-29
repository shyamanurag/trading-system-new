-- Fix trades table issues for production deployment
-- 1. Add missing updated_at column
-- 2. Add missing status column

BEGIN;

-- Add updated_at column if it doesn't exist
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add status column if it doesn't exist  
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'EXECUTED';

-- Update all existing rows to have updated_at
UPDATE trades 
SET updated_at = COALESCE(updated_at, executed_at, created_at, NOW())
WHERE updated_at IS NULL;

COMMIT; 