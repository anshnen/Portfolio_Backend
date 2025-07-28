import os
import click
import unittest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

from .core.config import config
from .models.models import db, Portfolio, Account, Asset, Holding, Transaction

# Initialize extensions but do not bind them to an app yet
migrate = Migrate()

def create_app(config_name='default'):
    """
    Application Factory Function: Creates and configures the Flask app.
    This is the central place for all application setup.
    """
    app = Flask(__name__, static_folder='static')
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app) # Enable Cross-Origin Resource Sharing

    from .api.portfolio_routes import portfolio_bp
    from .api.transaction_routes import transaction_bp
    
    app.register_blueprint(portfolio_bp, url_prefix='/api/v1/portfolio')
    app.register_blueprint(transaction_bp, url_prefix='/api/v1/transactions')

    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.json'

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "Portfolio Management API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, Portfolio=Portfolio, Account=Account, Asset=Asset, Holding=Holding, Transaction=Transaction)


    @app.cli.command()
    @click.argument('test_names', nargs=-1)
    def test(test_names):
        """Run the unit tests."""
        if test_names:
            tests = unittest.TestLoader().loadTestsFromNames(test_names)
        else:
            tests = unittest.TestLoader().discover('tests', pattern='test*.py')
        unittest.TextTestRunner(verbosity=2).run(tests)

    @app.route('/')
    def index():
        return "Portfolio Management API is running. Visit /api/docs for documentation."

    return app