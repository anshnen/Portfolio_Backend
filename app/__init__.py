# app/__init__.py

from flask import Flask
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from flask_migrate import Migrate
from .core.config import config
from .models.models import db
from .commands import register_commands

# Initialize extensions globally but do not bind them to an app yet
migrate = Migrate()

def create_app(config_name='default'):
    """
    Application Factory Function: Creates and configures the Flask app.
    """
    app = Flask(__name__, static_folder='static')
    app.config.from_object(config[config_name])

    # Initialize extensions with the app instance
    db.init_app(app)
    migrate.init_app(app, db)
    # Allow requests specifically from your frontend's origin for all API routes
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:8501"]}})

    # Register custom CLI commands (e.g., 'flask test') and shell context
    register_commands(app)

    # --- Register API Blueprints ---
    from .api.portfolio_routes import portfolio_bp
    from .api.transaction_routes import transaction_bp
    from .api.watchlist_routes import watchlist_bp
    from .api.market_data_routes import market_data_bp
    from .api.order_routes import order_bp
    # FIX: Added the missing account blueprint to support account-related endpoints
    from .api.account_routes import account_bp 

    app.register_blueprint(portfolio_bp, url_prefix='/api/v1/portfolio')
    app.register_blueprint(transaction_bp, url_prefix='/api/v1/transactions')
    app.register_blueprint(watchlist_bp, url_prefix='/api/v1/watchlists')
    app.register_blueprint(market_data_bp, url_prefix='/api/v1/market')
    app.register_blueprint(order_bp, url_prefix='/api/v1/orders')
    # FIX: Registered the new account blueprint
    app.register_blueprint(account_bp, url_prefix='/api/v1/accounts')

    # --- Swagger UI Configuration ---
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "Portfolio API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    @app.route('/')
    def index():
        return "Portfolio API is running. Visit /api/docs for documentation."

    return app