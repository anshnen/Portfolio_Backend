# app/services/portfolio_service.py

from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import func, case
from ..models.models import db, Portfolio, Account, Holding, Transaction

def get_portfolio_summary(portfolio_id: int):
    # --- 1. Fetch Portfolio and its Accounts ---
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        return None, "Portfolio not found"

    # --- 2. Calculate Net Worth and Today's Change ---
    net_worth = Decimal('0.0')
    total_todays_change = Decimal('0.0')
    total_yesterday_value = Decimal('0.0')

    # Get all holdings across all investment accounts in the portfolio
    holdings = Holding.query.join(Account).filter(Account.portfolio_id == portfolio_id).all()

    for holding in holdings:
        # Calculate market value for each holding
        market_value = holding.market_value
        net_worth += market_value

        # Calculate today's change for each holding
        if holding.asset and holding.asset.last_price and holding.asset.previous_close_price:
            change_for_holding = (holding.asset.last_price - holding.asset.previous_close_price) * holding.quantity
            total_todays_change += change_for_holding
            total_yesterday_value += holding.asset.previous_close_price * holding.quantity

    # Add cash balances to net worth
    cash_accounts = Account.query.filter_by(portfolio_id=portfolio_id, account_type='CASH').all()
    for account in cash_accounts:
        net_worth += account.balance

    # Calculate today's change percentage
    # Avoid division by zero if the portfolio value was zero yesterday
    todays_change_percent = (total_todays_change / total_yesterday_value) * 100 if total_yesterday_value else Decimal('0.0')

    # --- 3. Calculate Cash Flow for the Last 30 Days ---
    thirty_days_ago = date.today() - timedelta(days=30)
    
    # Use a single query to get income and spending
    cash_flow_query = db.session.query(
        func.sum(case((Transaction.total_amount > 0, Transaction.total_amount), else_=0)).label('income'),
        func.sum(case((Transaction.total_amount < 0, Transaction.total_amount), else_=0)).label('spending')
    ).join(Account).filter(
        Account.portfolio_id == portfolio_id,
        Transaction.transaction_date >= thirty_days_ago
    ).one()
    
    income = cash_flow_query.income or Decimal('0.0')
    spending = cash_flow_query.spending or Decimal('0.0') # Spending is negative, take absolute value for UI
    
    # --- 4. Assemble the Summary Object ---
    summary = {
        "net_worth": float(net_worth),
        "todays_change_amount": float(total_todays_change),
        "todays_change_percent": float(todays_change_percent),
        "cash_flow": {
            "income": float(income),
            "spending": float(abs(spending))
        },
        "accounts": [
            {
                "id": acc.id,
                "name": acc.name,
                "institution": acc.institution,
                "account_type": acc.account_type,
                "balance": float(acc.balance) if acc.account_type == 'CASH' else float(sum(h.market_value for h in acc.holdings))
            } for acc in portfolio.accounts
        ]
    }

    return summary, None