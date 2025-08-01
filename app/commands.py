# app/commands.py

import click
import unittest
from .models.models import db, User, Portfolio, Account, Asset, Holding, Transaction, Watchlist, WatchlistItem, HistoricalPrice

def register_commands(app):
    """Register custom CLI commands for the Flask app."""

    @app.shell_context_processor
    def make_shell_context():
        """Makes all model objects available in the 'flask shell' context for easy debugging."""
        return dict(
            db=db, User=User, Portfolio=Portfolio, Account=Account, Asset=Asset, 
            Holding=Holding, Transaction=Transaction, Watchlist=Watchlist, 
            WatchlistItem=WatchlistItem, HistoricalPrice=HistoricalPrice
        )

    @app.cli.command()
    @click.argument('test_names', nargs=-1)
    def test(test_names):
        """Run the unit tests."""
        if test_names:
            tests = unittest.TestLoader().loadTestsFromNames(test_names)
        else:
            tests = unittest.TestLoader().discover('tests', pattern='test*.py')
        unittest.TextTestRunner(verbosity=2).run(tests)
