-- 015_simple_fix.sql
-- SIMPLE EMERGENCY FIX: Add broker_user_id column + Clean ALL fake data
-- No complex PostgreSQL blocks - just basic SQL

-- Add missing broker_user_id column
ALTER TABLE users ADD COLUMN IF NOT EXISTS broker_user_id VARCHAR(50);

-- Clean ALL fake data (production starts clean)
DELETE FROM trades;
DELETE FROM orders;

-- Reset sequences to start fresh  
ALTER SEQUENCE IF EXISTS trades_trade_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS orders_order_id_seq RESTART WITH 1; 