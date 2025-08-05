# app/services/portfolio_service.py

from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import func, case
from ..models.models import db, Portfolio, Account, Holding, Transaction, AccountType
from .market_data_service import MarketDataService # Import the service

def get_detailed_holdings(portfolio_id: int):
    """
    Retrieves a detailed list of all individual holdings for a portfolio,
    including calculated metrics like market value and unrealized P&L.
    """
    holdings = Holding.query.join(Account).filter(Account.portfolio_id == portfolio_id).all()
    if not holdings:
        return [], None

    detailed_holdings = []
    for holding in holdings:
        market_value = holding.market_value
        unrealized_pnl = market_value - holding.cost_basis
        
        detailed_holdings.append({
            "holding_id": holding.id,
            "account_name": holding.account.name,
            "ticker_symbol": holding.asset.ticker_symbol,
            "asset_name": holding.asset.name,
            "quantity": float(holding.quantity),
            "average_buy_price": float(holding.average_price),
            "cost_basis": float(holding.cost_basis),
            "market_value": float(market_value),
            "unrealized_pnl": float(unrealized_pnl),
            "current_price": float(holding.asset.last_price) if holding.asset.last_price else None
        })
        
    return detailed_holdings, None

def get_total_holdings_value(portfolio_id: int):
    """Calculates the total market value of all assets held in a portfolio."""
    holdings = Holding.query.join(Account).filter(Account.portfolio_id == portfolio_id).all()
    total_value = sum(holding.market_value for holding in holdings)
    return {"total_holdings_value": float(total_value)}, None

def get_portfolio_summary(portfolio_id: int):
    """
    Calculates a full summary for a given portfolio, including P&L,
    market indices, a detailed holdings breakdown, and other advanced insights.
    """
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        return None, "Portfolio not found"

    # --- Initialize metrics ---
    net_worth = Decimal('0.0')
    total_todays_change = Decimal('0.0')
    total_yesterday_value = Decimal('0.0')
    total_initial_investment = Decimal('0.0')
    total_holdings_value = Decimal('0.0')
    
    holdings_details = []
    daily_movers = []
    sector_allocation = {}

    holdings = Holding.query.join(Account).filter(Account.portfolio_id == portfolio_id).all()

    for holding in holdings:
        market_value = holding.market_value
        total_holdings_value += market_value
        total_initial_investment += holding.cost_basis
        net_worth += market_value

        # --- Calculate individual P&L for each holding ---
        unrealized_pnl = market_value - holding.cost_basis
        
        holdings_details.append({
            "ticker_symbol": holding.asset.ticker_symbol,
            "asset_name": holding.asset.name,
            "quantity": float(holding.quantity),
            "average_buy_price": float(holding.average_price),
            "current_price": float(holding.asset.last_price) if holding.asset.last_price else None,
            "market_value": float(market_value),
            "unrealized_pnl": float(unrealized_pnl)
        })

        if holding.asset and holding.asset.last_price and holding.asset.previous_close_price:
            change_for_holding = (holding.asset.last_price - holding.asset.previous_close_price) * holding.quantity
            total_todays_change += change_for_holding
            yesterday_holding_value = holding.asset.previous_close_price * holding.quantity
            total_yesterday_value += yesterday_holding_value
            
            percent_change = (change_for_holding / yesterday_holding_value) * 100 if yesterday_holding_value > 0 else Decimal('0.0')
            daily_movers.append({
                "ticker": holding.asset.ticker_symbol,
                "name": holding.asset.name,
                "change_amount": float(change_for_holding),
                "percent_change": float(percent_change)
            })

        sector = holding.asset.sector or "Other"
        sector_allocation.setdefault(sector, Decimal('0.0'))
        sector_allocation[sector] += market_value

    # Add cash balances to net worth
    cash_accounts = Account.query.filter_by(portfolio_id=portfolio_id, account_type=AccountType.CASH).all()
    for account in cash_accounts:
        net_worth += account.balance

    # --- Calculate Overall P&L Metrics ---
    overall_pl = total_holdings_value - total_initial_investment
    overall_pl_percent = (overall_pl / total_initial_investment) * 100 if total_initial_investment > 0 else Decimal('0.0')

    # --- Fetch Market Index Data ---
    market_indices = MarketDataService.get_index_data()

    # --- Determine Top 5 Gainers and Losers ---
    daily_movers.sort(key=lambda x: x['change_amount'], reverse=True)
    top_gainers = daily_movers[:5]
    top_losers = sorted([mover for mover in daily_movers if mover['change_amount'] < 0], key=lambda x: x['change_amount'])[:5]

    # --- Finalize Sector Allocation Percentages ---
    sector_allocation_percent = {
        sector: float((value / total_holdings_value) * 100) if total_holdings_value > 0 else 0
        for sector, value in sector_allocation.items()
    }

    # --- Calculate Cash Flow for the Last 30 Days ---
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
    
    # --- Assemble the Complete Summary Object ---
    summary = {
        "net_worth": float(net_worth),
        "performance": {
            "total_initial_investment": float(total_initial_investment),
            "current_holdings_worth": float(total_holdings_value),
            "overall_pl": float(overall_pl),
            "overall_pl_percent": float(overall_pl_percent),
            "todays_change_amount": float(total_todays_change),
        },
        "market_indices": market_indices,
        "detailed_holdings": holdings_details,
        "accounts": [
            {
                "id": acc.id,
                "name": acc.name,
                "account_type": acc.account_type.value,
                "balance": float(acc.balance + acc.holdings_market_value)
            } for acc in portfolio.accounts
        ],
        "insights": {
            "top_gainers": top_gainers,
            "top_losers": top_losers,
            "sector_allocation": sector_allocation_percent
        }
    }

    return summary, None