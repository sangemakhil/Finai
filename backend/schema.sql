PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

-- Funds table
CREATE TABLE IF NOT EXISTS funds (
    fund_id INTEGER PRIMARY KEY,
    fund_name TEXT NOT NULL,
    fund_type TEXT,
    risk_level TEXT,
    expense_ratio REAL
);

-- SIP records table
CREATE TABLE IF NOT EXISTS sip_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fund_id INTEGER NOT NULL,
    date TEXT NOT NULL,                -- stored as 'YYYY-MM-DD'
    amount REAL NOT NULL,
    nav_at_purchase REAL,
    units_purchased REAL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(fund_id) REFERENCES funds(fund_id)
);

-- NAV history table
CREATE TABLE IF NOT EXISTS nav_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    nav_value REAL NOT NULL,
    FOREIGN KEY(fund_id) REFERENCES funds(fund_id)
);
