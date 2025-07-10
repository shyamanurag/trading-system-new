-- Create symbols table for search functionality
-- This was lost during git rollback and needs to be recreated

BEGIN;

-- Create symbols table if it doesn't exist
CREATE TABLE IF NOT EXISTS symbols (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    exchange VARCHAR(20),
    symbol_type VARCHAR(20), -- EQUITY, OPTION, FUTURE
    lot_size INTEGER DEFAULT 1,
    tick_size DECIMAL(10,4) DEFAULT 0.01,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for search functionality
CREATE INDEX IF NOT EXISTS idx_symbols_search ON symbols(symbol, name);
CREATE INDEX IF NOT EXISTS idx_symbols_active ON symbols(is_active);
CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(symbol_type);

-- Insert sample symbols for search functionality
INSERT INTO symbols (symbol, name, exchange, symbol_type, lot_size) VALUES
('NIFTY', 'Nifty 50 Index', 'NSE', 'INDEX', 25),
('BANKNIFTY', 'Bank Nifty Index', 'NSE', 'INDEX', 25),
('SENSEX', 'BSE Sensex', 'BSE', 'INDEX', 10),
('RELIANCE', 'Reliance Industries Ltd', 'NSE', 'EQUITY', 1),
('TCS', 'Tata Consultancy Services Ltd', 'NSE', 'EQUITY', 1),
('HDFCBANK', 'HDFC Bank Ltd', 'NSE', 'EQUITY', 1),
('INFY', 'Infosys Ltd', 'NSE', 'EQUITY', 1),
('ICICIBANK', 'ICICI Bank Ltd', 'NSE', 'EQUITY', 1),
('HINDUNILVR', 'Hindustan Unilever Ltd', 'NSE', 'EQUITY', 1),
('ITC', 'ITC Ltd', 'NSE', 'EQUITY', 1),
('SBIN', 'State Bank of India', 'NSE', 'EQUITY', 1),
('BHARTIARTL', 'Bharti Airtel Ltd', 'NSE', 'EQUITY', 1),
('ASIANPAINT', 'Asian Paints Ltd', 'NSE', 'EQUITY', 1),
('MARUTI', 'Maruti Suzuki India Ltd', 'NSE', 'EQUITY', 1),
('BAJFINANCE', 'Bajaj Finance Ltd', 'NSE', 'EQUITY', 1),
('LT', 'Larsen & Toubro Ltd', 'NSE', 'EQUITY', 1),
('TECHM', 'Tech Mahindra Ltd', 'NSE', 'EQUITY', 1),
('SUNPHARMA', 'Sun Pharmaceutical Industries Ltd', 'NSE', 'EQUITY', 1),
('TITAN', 'Titan Company Ltd', 'NSE', 'EQUITY', 1),
('ULTRACEMCO', 'UltraTech Cement Ltd', 'NSE', 'EQUITY', 1),
('ONGC', 'Oil & Natural Gas Corporation Ltd', 'NSE', 'EQUITY', 1),
('NTPC', 'NTPC Ltd', 'NSE', 'EQUITY', 1),
('AXISBANK', 'Axis Bank Ltd', 'NSE', 'EQUITY', 1),
('WIPRO', 'Wipro Ltd', 'NSE', 'EQUITY', 1),
('POWERGRID', 'Power Grid Corporation of India Ltd', 'NSE', 'EQUITY', 1)
ON CONFLICT (symbol) DO NOTHING;

COMMIT;

-- Verify table creation
SELECT COUNT(*) as symbol_count FROM symbols;
SELECT 'Symbols table created successfully with ' || COUNT(*) || ' symbols' as status FROM symbols; 