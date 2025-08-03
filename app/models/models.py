# app/models/models.py

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from decimal import Decimal
from datetime import datetime
import enum

# --- Enums for Data Integrity ---
# Using enums ensures that type and status fields can only contain predefined values.

class AccountType(enum.Enum):
    CASH = "CASH"
    INVESTMENT = "INVESTMENT"
    RETIREMENT = "RETIREMENT"

class AssetType(enum.Enum):
    STOCK = "STOCK"
    ETF = "ETF"
    CASH = "CASH"
    INDEX = "INDEX"

class TransactionType(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    DIVIDEND = "DIVIDEND"
    INTEREST = "INTEREST"
    FEE = "FEE"

class TransactionStatus(enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    portfolios = relationship('Portfolio', back_populates='user', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship('User', back_populates='portfolios')
    accounts = relationship('Account', back_populates='portfolio', cascade="all, delete-orphan")
    watchlists = relationship('Watchlist', back_populates='portfolio', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Portfolio(id={self.id}, name='{self.name}')>"

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.Enum(AccountType), nullable=False)
    institution = db.Column(db.String(100))
    balance = db.Column(db.Numeric(15, 2), default=0.00) # For CASH accounts, this is the total. For others, it's the cash portion.
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    portfolio = relationship('Portfolio', back_populates='accounts')
    holdings = relationship('Holding', back_populates='account', cascade="all, delete-orphan")
    transactions = relationship('Transaction', back_populates='account', cascade="all, delete-orphan")

    @property
    def holdings_market_value(self):
        """Calculates the total market value of all assets held in this account."""
        return sum(holding.market_value for holding in self.holdings)

    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', type='{self.account_type.value}')>"

class Asset(db.Model):
    __tablename__ = 'assets'
    id = db.Column(db.Integer, primary_key=True)
    ticker_symbol = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    asset_type = db.Column(db.Enum(AssetType), nullable=False)
    
    last_price = db.Column(db.Numeric(15, 4))
    previous_close_price = db.Column(db.Numeric(15, 4))
    price_updated_at = db.Column(db.DateTime)
    
    market_cap = db.Column(db.BigInteger)
    sector = db.Column(db.String(100))
    pe_ratio = db.Column(db.Numeric(10, 2))
    eps = db.Column(db.Numeric(10, 2))
    dividend_yield = db.Column(db.Numeric(10, 4))
    beta = db.Column(db.Numeric(10, 4))
    
    fifty_day_average = db.Column(db.Numeric(15, 4))
    two_hundred_day_average = db.Column(db.Numeric(15, 4))

    historical_prices = relationship('HistoricalPrice', back_populates='asset', cascade="all, delete-orphan")
    watchlist_items = relationship('WatchlistItem', back_populates='asset', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Asset(id={self.id}, ticker='{self.ticker_symbol}')>"

class Holding(db.Model):
    __tablename__ = 'holdings'
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Numeric(15, 4), nullable=False)
    cost_basis = db.Column(db.Numeric(15, 2), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    account = relationship('Account', back_populates='holdings')
    asset = relationship('Asset')
    
    @property
    def market_value(self):
        if self.asset and self.asset.last_price:
            return self.quantity * self.asset.last_price
        return Decimal('0.0')

    @property
    def average_price(self):
        return self.cost_basis / self.quantity if self.quantity > 0 else Decimal('0')

    def __repr__(self):
        return f"<Holding(account_id={self.account_id}, asset_id={self.asset_id}, quantity={self.quantity})>"

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.Enum(TransactionType), nullable=False)
    status = db.Column(db.Enum(TransactionStatus), nullable=False, default=TransactionStatus.COMPLETED)
    order_type = db.Column(db.String(50))
    trigger_price = db.Column(db.Numeric(15, 4))
    transaction_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Numeric(15, 4))
    price_per_unit = db.Column(db.Numeric(15, 4))
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    commission_fee = db.Column(db.Numeric(10, 2), default=0.00)
    realized_pnl = db.Column(db.Numeric(15, 2))
    description = db.Column(db.String(255))
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'))
    account = relationship('Account', back_populates='transactions')
    asset = relationship('Asset')

    def __repr__(self):
        return f"<Transaction(id={self.id}, type='{self.transaction_type.value}', amount={self.total_amount})>"

class Watchlist(db.Model):
    __tablename__ = 'watchlists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    portfolio = relationship('Portfolio', back_populates='watchlists')
    items = relationship('WatchlistItem', back_populates='watchlist', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Watchlist(id={self.id}, name='{self.name}')>"

class WatchlistItem(db.Model):
    __tablename__ = 'watchlist_items'
    id = db.Column(db.Integer, primary_key=True)
    watchlist_id = db.Column(db.Integer, db.ForeignKey('watchlists.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    watchlist = relationship('Watchlist', back_populates='items')
    asset = relationship('Asset', back_populates='watchlist_items')

    def __repr__(self):
        return f"<WatchlistItem(watchlist_id={self.watchlist_id}, asset_id={self.asset_id})>"

class HistoricalPrice(db.Model):
    __tablename__ = 'historical_prices'
    id = db.Column(db.BigInteger, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    price_date = db.Column(db.Date, nullable=False)
    open_price = db.Column(db.Numeric(15, 4))
    high_price = db.Column(db.Numeric(15, 4))
    low_price = db.Column(db.Numeric(15, 4))
    close_price = db.Column(db.Numeric(15, 4), nullable=False)
    volume = db.Column(db.BigInteger)
    asset = relationship('Asset', back_populates='historical_prices')

    def __repr__(self):
        return f"<HistoricalPrice(asset_id={self.asset_id}, date='{self.price_date}', close={self.close_price})>"