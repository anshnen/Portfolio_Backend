# app/services/portfolio_service.py

from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import func, case
from ..models.models import db, Portfolio, Account, Holding, Transaction

def get_portfolio_summary(portfolio_id: int):
    """
    Calculates a full summary for a given portfolio, including advanced
    insights like top gainers/losers and sector allocation.
    """
    # --- 1. Fetch Portfolio and its Accounts ---
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        return None, "Portfolio not found"

    # --- 2. Calculate Net Worth, Today's Change, and Performance Insights ---
    net_worth = Decimal('0.0')
    total_todays_change = Decimal('0.0')
    total_yesterday_value = Decimal('0.0')
    investment_value = Decimal('0.0')
    
    daily_movers = []
    sector_allocation = {}

    holdings = Holding.query.join(Account).filter(Account.portfolio_id == portfolio_id).all()

    for holding in holdings:
        market_value = holding.market_value
        net_worth += market_value
        investment_value += market_value

        # Calculate daily change for each holding to find movers
        if holding.asset and holding.asset.last_price and holding.asset.previous_close_price:
            change_for_holding = (holding.asset.last_price - holding.asset.previous_close_price) * holding.quantity
            total_todays_change += change_for_holding
            
            yesterday_holding_value = holding.asset.previous_close_price * holding.quantity
            total_yesterday_value += yesterday_holding_value
            
            percent_change = (change_for_holding / yesterday_holding_value) * 100 if yesterday_holding_value else Decimal('0.0')

            daily_movers.append({
                "ticker": holding.asset.ticker_symbol,
                "name": holding.asset.name,
                "change_amount": float(change_for_holding),
                "percent_change": float(percent_change)
            })

        # Aggregate value by sector for allocation insights
        sector = holding.asset.sector or "Other"
        if sector not in sector_allocation:
            sector_allocation[sector] = Decimal('0.0')
        sector_allocation[sector] += market_value

    # Add cash balances to net worth
    cash_accounts = Account.query.filter_by(portfolio_id=portfolio_id, account_type='CASH').all()
    for account in cash_accounts:
        net_worth += account.balance

    # Finalize daily change percentage
    todays_change_percent = (total_todays_change / total_yesterday_value) * 100 if total_yesterday_value else Decimal('0.0')

    # --- 3. Determine Top 5 Gainers and Losers ---
    daily_movers.sort(key=lambda x: x['change_amount'], reverse=True)
    top_gainers = daily_movers[:5]
    top_losers = sorted([mover for mover in daily_movers if mover['change_amount'] < 0], key=lambda x: x['change_amount'])[:5]

    # --- 4. Finalize Sector Allocation Percentages ---
    sector_allocation_percent = {
        sector: float((value / investment_value) * 100) if investment_value > 0 else 0
        for sector, value in sector_allocation.items()
    }

    # --- 5. Calculate Cash Flow for the Last 30 Days ---
    thirty_days_ago = date.today() - timedelta(days=30)
    cash_flow_query = db.session.query(
        func.sum(case((Transaction.total_amount > 0, Transaction.total_amount), else_=0)).label('income'),
        func.sum(case((Transaction.total_amount < 0, Transaction.total_amount), else_=0)).label('spending')
    ).join(Account).filter(
        Account.portfolio_id == portfolio_id,
        Transaction.transaction_date >= thirty_days_ago
    ).one()
    
    income = cash_flow_query.income or Decimal('0.0')
    spending = cash_flow_query.spending or Decimal('0.0')
    
    # --- 6. Assemble the Complete Summary Object ---
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
                "account_type": acc.account_type,
                "balance": float(acc.balance) if acc.account_type == 'CASH' else float(sum(h.market_value for h in acc.holdings))
            } for acc in portfolio.accounts
        ],
        "insights": {
            "top_gainers": top_gainers,
            "top_losers": top_losers,
            "sector_allocation": sector_allocation_percent
        }
    }

    return summary, None