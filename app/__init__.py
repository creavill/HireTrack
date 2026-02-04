"""
Hammy the Hire Tracker - Application Factory

AI-powered job tracking system with Gmail integration.
Go HAM on your job search!
"""

import os
import logging
from flask import Flask
from flask_cors import CORS

from app.config import get_config
from app.database import init_db

logger = logging.getLogger(__name__)


def create_app(config_path=None):
    """
    Application factory for creating Flask app instances.

    Args:
        config_path: Optional path to config.yaml file

    Returns:
        Configured Flask application instance
    """
    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    # Load configuration
    try:
        config = get_config(config_path)
    except FileNotFoundError as e:
        logger.error(f"Configuration Error: {e}")
        raise

    # Validate at least one AI provider API key is set
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_google = bool(os.getenv("GOOGLE_API_KEY"))

    if not (has_anthropic or has_openai or has_google):
        logger.error("No AI provider API key set in environment")
        raise ValueError(
            "No AI provider API key found. "
            "Set at least one of: ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY in your .env file."
        )

    # Create Flask app
    app = Flask(__name__, static_folder="../dist/assets", static_url_path="/assets")

    # Enable CORS
    CORS(app)

    # Store config in app
    app.config["HAMMY_CONFIG"] = config

    # Initialize database
    init_db()

    # Register blueprints/routes
    # Note: routes.py handles frontend serving
    register_blueprints(app)

    return app


def register_blueprints(app):
    """Register all Flask blueprints."""
    from app.routes import register_all_blueprints

    register_all_blueprints(app)
