#!/usr/bin/env python3
"""
Hammy the Hire Tracker - Main Application Entry Point

AI-powered job tracking system with Gmail integration.
Go HAM on your job search! 🐷
"""

import os
import logging
from pathlib import Path
from flask import Flask
from flask_cors import CORS

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
from config_loader import get_config
from constants import APP_DIR, DB_PATH, CREDENTIALS_FILE
from database import init_db
from resume_manager import migrate_file_resumes_to_db
from backup_manager import backup_on_startup
from routes import register_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
try:
    CONFIG = get_config()
except FileNotFoundError as e:
    print(f"\n❌ Configuration Error: {e}")
    print("📝 Copy config.example.yaml to config.yaml and fill in your information.\n")
    exit(1)

# Validate API key
if not os.getenv("ANTHROPIC_API_KEY"):
    logger.error("❌ ANTHROPIC_API_KEY not set in environment")
    logger.error("Set it in your .env file or environment variables")
    exit(1)

# Initialize Flask app
app = Flask(__name__, static_folder='dist/assets', static_url_path='/assets')
CORS(app)

# Initialize database
init_db()

# Register all routes
app = register_routes(app)

if __name__ == '__main__':
    # Automatic backup on startup
    try:
        logger.info("🔄 Creating automatic backup...")
        backup_on_startup()
        logger.info("✅ Backup created successfully")
    except Exception as e:
        logger.warning(f"⚠️  Backup skipped: {e}")

    # Resume migration
    try:
        migrate_file_resumes_to_db()
    except Exception as e:
        logger.warning(f"⚠️  Resume migration skipped: {e}")

    # Startup banner
    logger.info("\n" + "="*60)
    logger.info("🐷 Hammy the Hire Tracker - Go HAM on Your Job Search!")
    logger.info("="*60)
    logger.info(f"\n👤 User: {CONFIG.user_name}")
    logger.info(f"📧 Email: {CONFIG.user_email}")
    logger.info(f"📄 Resumes loaded: {len(CONFIG.resume_files)}")
    logger.info(f"\n📁 Configuration: {APP_DIR / 'config.yaml'}")
    logger.info(f"📁 Database: {DB_PATH}")
    logger.info(f"📁 Gmail credentials: {CREDENTIALS_FILE}")
    logger.info(f"\n💡 Hammy's Quick Start Guide:")
    logger.info(f"   1. Click '📧 Scan Gmail' to import job alerts")
    logger.info(f"   2. Click '🤖 Analyze All' for AI analysis")
    logger.info(f"   3. Click '📬 Scan Follow-Ups' to track responses")
    logger.info(f"   4. Use the Chrome extension for instant analysis")
    logger.info(f"\n🚀 Dashboard running at: http://localhost:5000")
    logger.info("="*60 + "\n")

    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
