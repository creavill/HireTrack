#!/usr/bin/env python3
"""
Hammy the Hire Tracker - New Entry Point

Uses the application factory pattern via app.create_app().
This is the recommended way to run the application.

Usage:
    python run.py
"""

import logging
from pathlib import Path

from app import create_app
from app.config import get_config
from app.database import DB_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
APP_DIR = Path(__file__).parent
CREDENTIALS_FILE = APP_DIR / "credentials.json"


def main():
    """Main entry point for Hammy the Hire Tracker."""
    # Create the Flask app using factory
    app = create_app()

    # Get config for startup info
    config = get_config()

    # Automatic backup on startup
    try:
        from backup_manager import backup_on_startup

        logger.info("Creating automatic backup...")
        backup_on_startup()
        logger.info("Backup created successfully")
    except Exception as e:
        logger.warning(f"Backup skipped: {e}")

    # Resume migration
    try:
        from resume_manager import migrate_file_resumes_to_db

        migrate_file_resumes_to_db()
    except Exception as e:
        logger.warning(f"Resume migration skipped: {e}")

    # Startup banner
    logger.info("\n" + "=" * 60)
    logger.info("Hammy the Hire Tracker - Go HAM on Your Job Search!")
    logger.info("=" * 60)
    logger.info(f"\nUser: {config.user_name}")
    logger.info(f"Email: {config.user_email}")
    logger.info(f"Resumes loaded: {len(config.resume_files)}")
    logger.info(f"\nConfiguration: {APP_DIR / 'config.yaml'}")
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"Gmail credentials: {CREDENTIALS_FILE}")
    logger.info(f"\nHammy's Quick Start Guide:")
    logger.info(f"   1. Click 'Scan Gmail' to import job alerts")
    logger.info(f"   2. Click 'Analyze All' for AI analysis")
    logger.info(f"   3. Click 'Scan Follow-Ups' to track responses")
    logger.info(f"   4. Use the Chrome extension for instant analysis")
    logger.info(f"\nDashboard running at: http://localhost:5000")
    logger.info("=" * 60 + "\n")

    # Run Flask app
    app.run(debug=True, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
