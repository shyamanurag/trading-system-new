-- Migration: Add PnL columns to trades table
-- Version: 008  
-- Date: 2025-07-15
-- Description: Add pnl and pnl_percent columns to trades table for frontend display

BEGIN;

-- Add PnL columns to trades table
ALTER TABLE trades 
ADD COLUMN IF NOT EXISTS pnl DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS pnl_percent DECIMAL(6,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'EXECUTED';

-- Update existing trades to have default values
UPDATE trades 
SET pnl = 0, pnl_percent = 0, status = 'EXECUTED' 
WHERE pnl IS NULL OR pnl_percent IS NULL OR status IS NULL;

-- Add index for performance on pnl queries
CREATE INDEX IF NOT EXISTS idx_trades_pnl ON trades(pnl);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);

COMMIT;
