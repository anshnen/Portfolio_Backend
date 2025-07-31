-- schema.sql
CREATE DATABASE portfolio_db;

USE portfolio_db;
-- Drop tables in reverse order of dependency to avoid foreign key errors
DROP TABLE IF EXISTS watchlist_items, watchlists, transactions, holdings, assets, accounts, portfolios, users;

-- Users table to support multiple users
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Portfolios are now linked to a user
CREATE TABLE portfolios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Accounts table remains largely the same but is linked to a portfolio
CREATE TABLE accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    account_type ENUM('CASH', 'INVESTMENT', 'RETIREMENT') NOT NULL,
    institution VARCHAR(100),
    balance DECIMAL(15, 2) DEFAULT 0.00,
    portfolio_id INT NOT NULL,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
);

-- Assets table now includes market-specific info and a type for indices
CREATE TABLE assets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker_symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    asset_type ENUM('STOCK', 'ETF', 'INDEX', 'CASH') NOT NULL,
    market_cap BIGINT,
    sector VARCHAR(100),
    last_price DECIMAL(15, 4),
    previous_close_price DECIMAL(15, 4),
    price_updated_at TIMESTAMP
);

-- Holdings table remains the same
CREATE TABLE holdings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quantity DECIMAL(15, 4) NOT NULL,
    cost_basis DECIMAL(15, 2) NOT NULL,
    account_id INT NOT NULL,
    asset_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);

-- Orders table to track buy and sell orders
CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_type ENUM('BUY', 'SELL', 'DEPOSIT', 'WITHDRAWAL', 'DIVIDEND', 'INTEREST', 'FEE') NOT NULL,
    status ENUM('PENDING', 'COMPLETED', 'FAILED', 'CANCELLED') NOT NULL DEFAULT 'COMPLETED',
    transaction_date DATE NOT NULL,
    quantity DECIMAL(15, 4),
    price_per_unit DECIMAL(15, 4),
    total_amount DECIMAL(15, 2) NOT NULL,
    description VARCHAR(255),
    account_id INT NOT NULL,
    asset_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

-- Watchlists are now linked to a user's portfolio
CREATE TABLE watchlists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    portfolio_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
    UNIQUE KEY (portfolio_id, name)
);

CREATE TABLE watchlist_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    watchlist_id INT NOT NULL,
    asset_id INT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (watchlist_id) REFERENCES watchlists(id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    UNIQUE KEY (watchlist_id, asset_id)
);

-- New table to store historical price data for charts
CREATE TABLE historical_prices (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    price_date DATE NOT NULL,
    open_price DECIMAL(15, 4),
    high_price DECIMAL(15, 4),
    low_price DECIMAL(15, 4),
    close_price DECIMAL(15, 4) NOT NULL,
    volume BIGINT,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    UNIQUE KEY (asset_id, price_date)
);