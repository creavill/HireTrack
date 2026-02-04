"""
Routes Package - Flask Blueprints for Hammy the Hire Tracker

This module registers all Flask blueprints with the application.

Blueprint structure:
- main_bp: Frontend serving (/, static files)
- API routes: Currently via legacy routes.py wrapper

Future structure will split API routes into:
- jobs_bp: Job CRUD operations
- scan_bp: Email scanning
- analysis_bp: AI analysis
- resumes_bp: Resume management
- settings_bp: Watchlist, companies, email sources
- backup_bp: Backup operations
"""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Add parent directory to path to import existing routes module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def register_all_blueprints(app):
    """
    Register all Flask blueprints with the application.

    Args:
        app: Flask application instance
    """
    # Register main blueprint for frontend
    from .main import main_bp

    app.register_blueprint(main_bp)
    logger.info("Registered main blueprint (frontend routes)")

    # Register API routes via legacy wrapper
    # Note: These can be converted to proper blueprints incrementally
    _register_api_routes(app)
    logger.info("Registered API routes")


def _register_api_routes(app):
    """
    Register API routes from the legacy routes module.

    This is a transitional function that wraps the existing routes.py
    The routes inside register_routes() use @app.route decorators,
    so they need the app instance directly.
    """
    # Import the legacy routes module
    import routes as legacy_routes

    # Get the register_routes function which adds @app.route decorators
    # We need to call it but skip the frontend routes since main_bp handles those
    _register_api_routes_only(app, legacy_routes)


def _register_api_routes_only(app, legacy_routes):
    """
    Register only API routes from legacy routes module.

    This calls the register_routes function but the main_bp
    will handle the frontend routes with higher priority.
    """
    # The legacy register_routes adds routes to app
    # Our main_bp already handles '/' and '/<path:path>'
    # The API routes (/api/*) will be added by legacy register_routes
    legacy_routes.register_routes(app)


# Export blueprints for direct import
from .main import main_bp

__all__ = [
    "register_all_blueprints",
    "main_bp",
]
