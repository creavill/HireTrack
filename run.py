#!/usr/bin/env python3
"""
Hammy the Hire Tracker - Main Entry Point

Uses the application factory pattern via app.create_app().
This is the recommended way to run the application.

Usage:
    python run.py

Environment Variables:
    FLASK_ENV: development (default), production, testing
    LOG_LEVEL: DEBUG, INFO, WARNING, ERROR (optional)
"""

import os
import sys
from pathlib import Path

# Ensure app directory is in path
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv(APP_DIR / ".env")

# Initialize logging first
from app.logging_config import setup_logging, get_logger

# Setup logging based on environment
flask_env = os.environ.get("FLASK_ENV", "development")
log_level = os.environ.get("LOG_LEVEL")
json_logs = flask_env == "production"

setup_logging(level=log_level, json_logs=json_logs)
logger = get_logger(__name__)


def main():
    """Main entry point for Hammy the Hire Tracker."""

    logger.info("=" * 60)
    logger.info("Hammy the Hire Tracker - Starting Up")
    logger.info("=" * 60)

    # Run startup validation
    from app.startup import run_startup_validation

    logger.info("Running startup validation...")
    validation_passed, results = run_startup_validation(
        strict=False, log_results=True  # Allow warnings in development
    )

    if not validation_passed:
        logger.error("Startup validation failed. Please fix the errors above.")
        sys.exit(1)

    # Create the Flask app using factory
    from app import create_app

    app = create_app()

    # Get config for startup info
    try:
        from app.config import get_config

        config = get_config()
        user_name = config.user_name
        user_email = config.user_email
        resume_count = len(config.resume_files) if config.resume_files else 0
    except Exception as e:
        logger.warning(f"Could not load config: {e}")
        user_name = "Unknown"
        user_email = "Not configured"
        resume_count = 0

    # Automatic backup on startup (non-blocking)
    try:
        from backup_manager import backup_on_startup

        logger.info("Creating automatic backup...")
        backup_on_startup()
        logger.info("Backup created successfully")
    except Exception as e:
        logger.warning(f"Backup skipped: {e}")

    # Resume migration (non-blocking)
    try:
        from resume_manager import migrate_file_resumes_to_db

        migrate_file_resumes_to_db()
    except Exception as e:
        logger.debug(f"Resume migration skipped: {e}")

    # Startup banner
    from app.database import DB_PATH

    credentials_file = APP_DIR / "credentials.json"

    logger.info("")
    logger.info("=" * 60)
    logger.info("  Hammy the Hire Tracker - Go HAM on Your Job Search!")
    logger.info("=" * 60)
    logger.info(f"  Environment: {flask_env}")
    logger.info(f"  User: {user_name}")
    logger.info(f"  Email: {user_email}")
    logger.info(f"  Config Resumes: {resume_count}")
    logger.info("")
    logger.info(f"  Configuration: {APP_DIR / 'config.yaml'}")
    logger.info(f"  Database: {DB_PATH}")
    logger.info(f"  Gmail credentials: {credentials_file}")
    logger.info("")
    logger.info("  Quick Start:")
    logger.info("    1. Click 'Scan Gmail' to import job alerts")
    logger.info("    2. Click 'Analyze All' for AI analysis")
    logger.info("    3. Click 'Scan Follow-Ups' to track responses")
    logger.info("    4. Use the Chrome extension for instant analysis")
    logger.info("")
    logger.info("  Dashboard: http://localhost:5000")
    logger.info("  Health Check: http://localhost:5000/api/health")
    logger.info("=" * 60)
    logger.info("")

    # Run Flask app
    debug_mode = flask_env != "production"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
