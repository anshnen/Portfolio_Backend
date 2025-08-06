# tests/test_api/test_portfolio_routes.py

from decimal import Decimal
from app.models.models import User, Portfolio, Account, Asset, Holding, AssetType

def test_get_portfolio_summary_api(client, db):
    """
    GIVEN a portfolio with a single account and holdings
    WHEN the GET /api/v1/portfolio/<id>/summary endpoint is called
    THEN it should return a 200 OK with the correctly calculated summary
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    # FIX: Create only a single account for the portfolio
    account = Account(name="Primary Account", balance=Decimal("5000.00"), portfolio=portfolio)
    # FIX: Added the required 'asset_type' field.
    asset = Asset(ticker_symbol="AAPL", name="Apple Inc", asset_type=AssetType.STOCK, last_price=Decimal("200.00"), previous_close_price=Decimal("190.00"))
    holding = Holding(account=account, asset=asset, quantity=100, cost_basis=15000) # 100 shares
    db.session.add_all([user, portfolio, account, asset, holding])
    db.session.commit()

    # ACT
    response = client.get(f'/api/v1/portfolio/{portfolio.id}/summary')
    json_data = response.get_json()

    # ASSERT
    assert response.status_code == 200
    
    # Check the main performance metrics
    # Net Worth = Cash Balance + Market Value of Holdings = 5000 + (100 * 200) = 25000
    assert json_data['net_worth'] == 25000.00
    
    # Today's Change = (Current Price - Prev Close) * Quantity = (200 - 190) * 100 = 1000
    performance_data = json_data.get('performance', {})
    assert performance_data.get('todays_change_amount') == 1000.00
    
    # Check that the single account is represented correctly
    account_data = json_data.get('account', {})
    assert account_data is not None
    assert account_data.get('name') == "Primary Account"