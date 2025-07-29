-- Migration 017: Add missing updated_at column to trades table
-- This fixes the "column updated_at does not exist" error during trade sync

ALTER TABLE trades ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Update existing rows to have updated_at timestamp
UPDATE trades SET updated_at = created_at WHERE updated_at IS NULL;

-- Add comment for clarity
COMMENT ON COLUMN trades.updated_at IS 'Timestamp when trade record was last updated'; 