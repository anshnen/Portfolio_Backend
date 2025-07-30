from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from decimal import Decimal
from datetime import datetime

db = SQLAlchemy()

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    accounts = relationship('Account', back_populates='portfolio', cascade="all, delete-orphan")
    watchlists = relationship('Watchlist', back_populates='portfolio', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Portfolio(id={self.id}, name='{self.name}')>"

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50), nullable=False) # CASH, INVESTMENT, RETIREMENT
    institution = db.Column(db.String(100))
    balance = db.Column(db.Numeric(15, 2), default=0.00)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    
    portfolio = relationship('Portfolio', back_populates='accounts')
    holdings = relationship('Holding', back_populates='account', cascade="all, delete-orphan")
    transactions = relationship('Transaction', back_populates='account', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', type='{self.account_type}')>"

class Asset(db.Model):
    __tablename__ = 'assets'
    id = db.Column(db.Integer, primary_key=True)
    ticker_symbol = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    asset_type = db.Column(db.String(50), nullable=False) # STOCK, ETF, CASH
    last_price = db.Column(db.Numeric(15, 4))
    previous_close_price = db.Column(db.Numeric(15, 4))
    price_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    account = relationship('Account', back_populates='holdings')
    asset = relationship('Asset')
    
    @property
    def market_value(self):
        if self.asset and self.asset.last_price:
            return self.quantity * self.asset.last_price
        return Decimal('0.0')

    def __repr__(self):
        return f"<Holding(account_id={self.account_id}, asset_id={self.asset_id}, quantity={self.quantity})>"

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(50), nullable=False) # BUY, SELL, DEPOSIT, WITHDRAWAL, DIVIDEND
    transaction_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Numeric(15, 4))
    price_per_unit = db.Column(db.Numeric(15, 4))
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.String(255))
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    account = relationship('Account', back_populates='transactions')
    asset = relationship('Asset')

    def __repr__(self):
        return f"<Transaction(id={self.id}, type='{self.transaction_type}', amount={self.total_amount})>"

class Watchlist(db.Model):
    __tablename__ = 'watchlists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    portfolio = relationship('Portfolio', back_populates='watchlists')
    items = relationship('WatchlistItem', back_populates='watchlist', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Watchlist(id={self.id}, name='{self.name}')>"

class WatchlistItem(db.Model):
    __tablename__ = 'watchlist_items'
    id = db.Column(db.Integer, primary_key=True)
    watchlist_id = db.Column(db.Integer, db.ForeignKey('watchlists.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    watchlist = relationship('Watchlist', back_populates='items')
    asset = relationship('Asset', back_populates='watchlist_items')

    def __repr__(self):
        return f"<WatchlistItem(watchlist_id={self.watchlist_id}, asset_id={self.asset_id})>"