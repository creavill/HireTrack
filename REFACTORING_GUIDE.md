# Hammy the Hire Tracker - Refactoring Guide

## Overview
This document tracks the refactoring of `local_app.py` (5051 lines) into maintainable, focused modules to improve code organization for open-source contributors.

## ✅ Completed Modules

### 1. constants.py (32 lines)
**Status:** ✅ Complete
- Application directories (APP_DIR, DB_PATH, RESUMES_DIR, etc.)
- Gmail API scopes
- WeWorkRemotely RSS feeds
- Common job title patterns for parsing

### 2. parsers.py (~800 lines)
**Status:** ✅ Complete
**Functions:**
- `clean_text_field()` - Text normalization
- `clean_job_url()` - URL tracking parameter removal
- `generate_job_id()` - Deterministic job ID generation
- `improved_title_company_split()` - Parse combined title/company text
- `parse_linkedin_jobs()` - LinkedIn email parsing
- `parse_indeed_jobs()` - Indeed email parsing
- `parse_greenhouse_jobs()` - Greenhouse ATS parsing
- `parse_wellfound_jobs()` - Wellfound/AngelList parsing
- `fetch_wwr_jobs()` - WeWorkRemotely RSS parsing

### 3. database.py (~215 lines)
**Status:** ✅ Complete
**Functions:**
- `init_db()` - Initialize SQLite database with all tables
- `get_db()` - Get database connection with Row factory

**Tables Created:**
- jobs, scan_history, watchlist, followups
- external_applications, resume_variants, resume_usage_log
- tracked_companies, custom_email_sources, deleted_jobs

### 4. gmail_scanner.py (~680 lines)
**Status:** ✅ Complete
**Functions:**
- `get_gmail_service()` - Gmail API authentication
- `get_email_body()` - Extract HTML from Gmail payload
- `scan_emails()` - Main email scanning function
- `classify_followup_email()` - Classify email type
- `extract_company_from_email()` - Extract company name
- `fuzzy_match_company()` - Match emails to jobs
- `scan_followup_emails()` - Scan for follow-ups (interviews, rejections, offers)

### 5. resume_manager.py (~310 lines)
**Status:** ✅ Complete
**Functions:**
- `load_resumes()` - Load from config.yaml files
- `migrate_file_resumes_to_db()` - Migrate files to database
- `load_resumes_from_db()` - Load from database
- `get_combined_resume_text()` - Combine all resumes for AI
- `recommend_resume_for_job()` - AI-powered resume recommendation

### 6. ai_analyzer.py (~370 lines)
**Status:** ✅ Complete
**Functions:**
- `ai_filter_and_score()` - Initial job filtering and baseline scoring
- `analyze_job()` - Detailed qualification analysis
- `generate_cover_letter()` - AI-generated cover letters
- `generate_interview_answer()` - AI interview prep answers
- `calculate_weighted_score()` - Combine qualification + recency

## 🔄 Remaining Work

### 7. routes.py (~2500 lines)
**Status:** ⏳ Pending
**Required Actions:**
1. Extract ALL @app.route decorated functions from local_app.py
2. Import necessary modules at top of routes.py
3. Accept `app` as parameter or create blueprint
4. Keep DASHBOARD_HTML template in routes or separate file

**Major Routes to Extract:**
- `@app.route('/')` - dashboard()
- `@app.route('/api/jobs')` - get_jobs(), update_job(), delete_job()
- `@app.route('/api/jobs/<job_id>/description')` - update_job_description()
- `@app.route('/api/scan')` - api_scan()
- `@app.route('/api/analyze')` - api_analyze()
- `@app.route('/api/score-jobs')` - api_score_jobs()
- `@app.route('/api/scan-followups')` - api_scan_followups()
- `@app.route('/api/followups')` - api_get_followups()
- `@app.route('/api/jobs/<job_id>/cover-letter')` - api_cover_letter()
- `@app.route('/api/capture')` - api_capture()
- `@app.route('/api/analyze-instant')` - api_analyze_instant()
- `@app.route('/api/wwr')` - api_scan_wwr()
- `@app.route('/api/generate-cover-letter')` - api_generate_cover_letter()
- `@app.route('/api/generate-answer')` - api_generate_answer()
- `@app.route('/api/watchlist')` - watchlist CRUD routes
- `@app.route('/api/tracked-companies')` - tracked companies CRUD
- `@app.route('/api/custom-email-sources')` - custom sources CRUD
- `@app.route('/api/external-applications')` - external apps CRUD
- `@app.route('/api/resumes')` - resume CRUD routes
- `@app.route('/api/resumes/upload')` - upload_resume()
- `@app.route('/api/jobs/<job_id>/recommend-resume')` - get_resume_recommendation()
- `@app.route('/api/jobs/recommend-resumes-batch')` - batch_recommend_resumes()
- `@app.route('/api/research-jobs')` - research_jobs(), research_jobs_for_resume()
- `@app.route('/api/backup/*')` - backup API routes

### 8. local_app.py Refactoring
**Status:** ⏳ Pending
**Target:** ~200 lines (from 5051)

**Keep in local_app.py:**
```python
#!/usr/bin/env python3
"""
Hammy the Hire Tracker - Local Application Entry Point
"""

import logging
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Import configuration
from config_loader import get_config
from constants import APP_DIR, DB_PATH, RESUMES_DIR
from database import init_db
from resume_manager import migrate_file_resumes_to_db
from backup_manager import backup_on_startup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load config
try:
    CONFIG = get_config()
except FileNotFoundError as e:
    print(f"\n❌ Configuration Error: {e}")
    print("📝 Copy config.example.yaml to config.yaml and fill in your information.\n")
    exit(1)

# Create Flask app
app = Flask(__name__, static_folder='dist/assets', static_url_path='/assets')
CORS(app)

# Import and register routes
from routes import register_routes
register_routes(app)

if __name__ == '__main__':
    # Initialize database
    init_db()
    RESUMES_DIR.mkdir(exist_ok=True)

    # Create backup
    logger.info("🔄 Creating automatic backup...")
    if backup_on_startup(DB_PATH, max_backups=10):
        logger.info("✅ Backup created successfully")

    # Migrate resumes
    try:
        migrate_file_resumes_to_db()
    except Exception as e:
        logger.warning(f"⚠️  Resume migration skipped: {e}")

    # Display startup banner
    logger.info("\n" + "="*60)
    logger.info("🐷 Hammy the Hire Tracker - Go HAM on Your Job Search!")
    logger.info("="*60)
    logger.info(f"\n👤 User: {CONFIG.user_name}")
    logger.info(f"📧 Email: {CONFIG.user_email}")
    logger.info(f"📄 Resumes loaded: {len(CONFIG.resume_files)}")
    logger.info(f"\n🚀 Dashboard running at: http://localhost:5000")
    logger.info("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
```

## 📋 Module Import Structure

### Dependency Graph (No Circular Dependencies)
```
local_app.py
  ↓
routes.py
  ↓
├─ ai_analyzer.py
│    ↓
│  config_loader (external)
│
├─ resume_manager.py
│    ↓
│  ├─ database.py
│  │    ↓
│  │  constants.py
│  └─ config_loader
│
├─ gmail_scanner.py
│    ↓
│  ├─ parsers.py
│  │    ↓
│  │  constants.py
│  ├─ database.py
│  └─ constants.py
│
└─ database.py
     ↓
   constants.py
```

## 🧪 Testing Checklist

### 1. Import Testing
```bash
cd /home/user/Hammy-the-Hire-Tracker
python3 -c "import constants; print('✅ constants.py')"
python3 -c "import database; print('✅ database.py')"
python3 -c "import parsers; print('✅ parsers.py')"
python3 -c "import gmail_scanner; print('✅ gmail_scanner.py')"
python3 -c "import resume_manager; print('✅ resume_manager.py')"
python3 -c "import ai_analyzer; print('✅ ai_analyzer.py')"
```

### 2. Functional Testing
- [ ] Database initialization works
- [ ] Gmail scanning works
- [ ] Email parsing (LinkedIn, Indeed, Greenhouse, Wellfound, WWR)
- [ ] AI filtering and scoring
- [ ] Resume loading from database
- [ ] Resume recommendation for jobs
- [ ] Cover letter generation
- [ ] Interview answer generation
- [ ] All Flask routes respond correctly
- [ ] Chrome extension integration
- [ ] Backup/restore functionality

### 3. Integration Testing
```bash
# Start the app
python3 local_app.py

# Test endpoints
curl http://localhost:5000/
curl http://localhost:5000/api/jobs
curl -X POST http://localhost:5000/api/scan
```

## 📁 File Summary

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| constants.py | 32 | Shared constants | ✅ Complete |
| parsers.py | ~800 | Email parsing | ✅ Complete |
| database.py | ~215 | Database operations | ✅ Complete |
| gmail_scanner.py | ~680 | Gmail integration | ✅ Complete |
| resume_manager.py | ~310 | Resume management | ✅ Complete |
| ai_analyzer.py | ~370 | AI analysis | ✅ Complete |
| routes.py | ~2500 | Flask routes | ⏳ Pending |
| local_app.py | ~200 | Entry point | ⏳ Pending |
| **Original** | **5051** | **Monolithic** | **→ 8 modules** |

## 🎯 Benefits of Refactoring

1. **Modularity**: Each module has single responsibility
2. **Maintainability**: Easy to find and fix bugs
3. **Testability**: Can unit test each module independently
4. **Collaboration**: Multiple devs can work on different modules
5. **Reusability**: Modules can be imported by other projects
6. **Documentation**: Clear module docstrings explain purpose
7. **No Circular Dependencies**: Clean import hierarchy

## 🚀 Next Steps

1. **Create routes.py** - Extract all @app.route functions
2. **Update local_app.py** - Slim down to entry point only
3. **Test imports** - Verify no circular dependencies
4. **Functional testing** - Ensure all features work
5. **Update documentation** - README, API docs, contributor guides
6. **Create CONTRIBUTING.md** - Guide for new contributors
7. **Add module tests** - Unit tests for each module

## ⚠️ Important Notes

- **Preserve all functionality** - Nothing should break
- **Keep function signatures identical** - No API changes
- **Maintain error handling** - Keep all try/except blocks
- **Preserve logging** - Keep logger.info/error calls
- **Keep comments** - All docstrings and inline comments
- **Test thoroughly** - Before committing changes

## 📞 Support

If you encounter issues during refactoring:
1. Check import statements are correct
2. Verify no circular dependencies (use import graph above)
3. Test each module individually
4. Check Flask app initialization
5. Verify environment variables are loaded correctly
