from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from decimal import Decimal

db = SQLAlchemy()

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    accounts = db.relationship('Account', back_populates='portfolio', lazy='dynamic', cascade="all, delete-orphan")

class Asset(db.Model):
    __tablename__ = 'assets'
    id = db.Column(db.Integer, primary_key=True)
    ticker_symbol = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    asset_type = db.Column(db.Enum('STOCK', 'BOND', 'ETF', 'MUTUAL_FUND', 'CRYPTO', 'CASH'), nullable=False)
    region = db.Column(db.String(100))
    last_price = db.Column(db.Numeric(19, 4), default=0.0)
    previous_close_price = db.Column(db.Numeric(19, 4), default=0.0)
    price_updated_at = db.Column(db.TIMESTAMP)

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    institution = db.Column(db.String(255))
    account_type = db.Column(db.Enum('CASH', 'INVESTMENT', 'RETIREMENT'), nullable=False)
    balance = db.Column(db.Numeric(19, 4), nullable=False, default=0.00)
    
    portfolio = db.relationship('Portfolio', back_populates='accounts')
    holdings = db.relationship('Holding', back_populates='account', cascade="all, delete-orphan")
    transactions = db.relationship('Transaction', back_populates='account', cascade="all, delete-orphan")

class Holding(db.Model):
    __tablename__ = 'holdings'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    quantity = db.Column(db.Numeric(19, 8), nullable=False)
    cost_basis = db.Column(db.Numeric(19, 4), nullable=False)

    account = db.relationship('Account', back_populates='holdings')
    asset = db.relationship('Asset', backref=backref('holdings', lazy=True))

    @property
    def market_value(self):
        if self.asset and self.asset.last_price:
            return self.quantity * self.asset.last_price
        return Decimal('0')
    
    @property
    def previous_day_market_value(self):
        if self.asset and self.asset.previous_close_price:
            return self.quantity * self.asset.previous_close_price
        return self.market_value 

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=True)
    transaction_type = db.Column(db.Enum('BUY', 'SELL', 'DEPOSIT', 'WITHDRAWAL', 'DIVIDEND', 'INTEREST', 'FEE'), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False, index=True)
    quantity = db.Column(db.Numeric(19, 8))
    price_per_unit = db.Column(db.Numeric(19, 4))
    total_amount = db.Column(db.Numeric(19, 4), nullable=False)
    description = db.Column(db.String(255))

    account = db.relationship('Account', back_populates='transactions')
    asset = db.relationship('Asset', backref=backref('transactions', lazy=True))
