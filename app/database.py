"""
Database - Database operations for Hammy the Hire Tracker

This module handles all database initialization, connection management,
and migrations for the SQLite database.
"""

import sqlite3
import logging
from pathlib import Path
from flask import g

logger = logging.getLogger(__name__)

# Database path (relative to app root)
DB_PATH = Path(__file__).parent.parent / "jobs.db"


def init_db():
    """
    Initialize SQLite database with required tables.

    Creates tables for:
    - jobs: Main job listings with AI analysis and scoring
    - scan_history: Track email scan timestamps to avoid re-processing
    - watchlist: Companies to monitor for future openings
    - followups: Interview and application follow-up tracking
    - external_applications: Track applications made outside the system
    - tracked_companies: Companies to track with career page and job alert email
    - resume_variants: Resume storage and management
    - resume_usage_log: Track resume recommendations
    - custom_email_sources: Custom job alert email sources
    - deleted_jobs: Track deleted jobs to avoid re-importing

    Uses WAL (Write-Ahead Logging) mode for better concurrency.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0)

    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")

    # Create tables if they don't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            url TEXT,
            source TEXT,
            status TEXT DEFAULT 'new',
            score INTEGER DEFAULT 0,
            baseline_score INTEGER DEFAULT 0,
            analysis TEXT,
            cover_letter TEXT,
            notes TEXT,
            raw_text TEXT,
            created_at TEXT,
            updated_at TEXT,
            email_date TEXT,
            is_filtered INTEGER DEFAULT 0,
            viewed INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_scan_date TEXT,
            emails_found INTEGER,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            url TEXT,
            notes TEXT,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS followups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            subject TEXT,
            type TEXT,
            snippet TEXT,
            email_date TEXT,
            job_id TEXT,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS external_applications (
            app_id TEXT PRIMARY KEY,
            job_id TEXT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            url TEXT,
            source TEXT NOT NULL,
            application_method TEXT,
            applied_date TEXT NOT NULL,
            contact_name TEXT,
            contact_email TEXT,
            status TEXT DEFAULT 'applied',
            follow_up_date TEXT,
            notes TEXT,
            created_at TEXT,
            updated_at TEXT,
            is_linked_to_job INTEGER DEFAULT 0,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS resume_variants (
            resume_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            focus_areas TEXT,
            target_roles TEXT,
            file_path TEXT,
            content TEXT,
            content_hash TEXT,
            usage_count INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS resume_usage_log (
            log_id TEXT PRIMARY KEY,
            resume_id TEXT,
            job_id TEXT,
            recommended_at TEXT,
            confidence_score REAL,
            user_selected INTEGER DEFAULT 0,
            reasoning TEXT,
            FOREIGN KEY (resume_id) REFERENCES resume_variants(resume_id),
            FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tracked_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            career_page_url TEXT,
            job_alert_email TEXT,
            notes TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS custom_email_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sender_email TEXT,
            sender_pattern TEXT,
            subject_keywords TEXT,
            enabled INTEGER DEFAULT 1,
            is_builtin INTEGER DEFAULT 0,
            category TEXT DEFAULT 'custom',
            parser_class TEXT,
            sample_email TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS deleted_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_url TEXT NOT NULL UNIQUE,
            title TEXT,
            company TEXT,
            deleted_at TEXT,
            deleted_reason TEXT DEFAULT 'user_deleted'
        )
    """)

    # Processed emails table for deduplication
    conn.execute("""
        CREATE TABLE IF NOT EXISTS processed_emails (
            gmail_message_id TEXT PRIMARY KEY,
            email_type TEXT,
            processed_at TEXT,
            source TEXT
        )
    """)

    # Discovered email sources (auto-detected potential job alert senders)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS discovered_email_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_email TEXT UNIQUE,
            sender_name TEXT,
            email_count INTEGER DEFAULT 1,
            sample_subjects TEXT,
            sample_snippet TEXT,
            sample_email_id TEXT,
            first_seen TEXT,
            last_seen TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            updated_at TEXT
        )
    """)

    # Run migrations
    run_migrations(conn)

    conn.commit()
    conn.close()

    # Seed built-in email sources
    seed_builtin_sources()


def run_migrations(conn):
    """
    Run database migrations to add new columns as needed.

    Uses PRAGMA table_info() to check for missing columns and adds them
    with ALTER TABLE.

    Args:
        conn: SQLite connection
    """
    # Get current columns in jobs table
    jobs_columns = {row[1] for row in conn.execute("PRAGMA table_info(jobs)").fetchall()}

    # Migration: Add job_id column to followups if it doesn't exist
    followups_columns = {row[1] for row in conn.execute("PRAGMA table_info(followups)").fetchall()}
    if "job_id" not in followups_columns:
        logger.info("Migrating database: adding 'job_id' column to followups...")
        conn.execute("ALTER TABLE followups ADD COLUMN job_id TEXT")

    # Migration: Add viewed column if it doesn't exist
    if "viewed" not in jobs_columns:
        logger.info("Migrating database: adding 'viewed' column...")
        conn.execute("ALTER TABLE jobs ADD COLUMN viewed INTEGER DEFAULT 0")

    # Migration: Add job_description column if it doesn't exist
    if "job_description" not in jobs_columns:
        logger.info("Migrating database: adding 'job_description' column...")
        conn.execute("ALTER TABLE jobs ADD COLUMN job_description TEXT")

    # Migration: Add resume-related columns to jobs table
    if "recommended_resume_id" not in jobs_columns:
        logger.info("Migrating database: adding resume-related columns to jobs...")
        conn.execute("ALTER TABLE jobs ADD COLUMN recommended_resume_id TEXT")
        conn.execute("ALTER TABLE jobs ADD COLUMN resume_recommendation TEXT")
        conn.execute("ALTER TABLE jobs ADD COLUMN selected_resume_id TEXT")
        conn.execute("ALTER TABLE jobs ADD COLUMN resume_match_score REAL")

    # Migration: Add email sources columns
    email_sources_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(custom_email_sources)").fetchall()
    }
    if "is_builtin" not in email_sources_columns:
        logger.info("Migrating database: adding email sources columns...")
        conn.execute("ALTER TABLE custom_email_sources ADD COLUMN is_builtin INTEGER DEFAULT 0")
        conn.execute("ALTER TABLE custom_email_sources ADD COLUMN category TEXT DEFAULT 'custom'")
        conn.execute("ALTER TABLE custom_email_sources ADD COLUMN parser_class TEXT")
        conn.execute("ALTER TABLE custom_email_sources ADD COLUMN sample_email TEXT")

    # Migration: Add enrichment columns (Phase 4 - Web Search Enrichment)
    if "salary_estimate" not in jobs_columns:
        logger.info("Migrating database: adding enrichment columns to jobs...")
        # Salary enrichment
        conn.execute("ALTER TABLE jobs ADD COLUMN salary_estimate TEXT")
        conn.execute("ALTER TABLE jobs ADD COLUMN salary_confidence TEXT DEFAULT 'none'")
        # Full description from web search
        conn.execute("ALTER TABLE jobs ADD COLUMN full_description TEXT")
        # Enrichment metadata
        conn.execute("ALTER TABLE jobs ADD COLUMN last_enriched TEXT")
        conn.execute("ALTER TABLE jobs ADD COLUMN enrichment_source TEXT")
        # Aggregator/staffing agency flag
        conn.execute("ALTER TABLE jobs ADD COLUMN is_aggregator INTEGER DEFAULT 0")
        # Company branding
        conn.execute("ALTER TABLE jobs ADD COLUMN logo_url TEXT")

    # Migration: Add applied_date column to jobs for cold applications
    if "applied_date" not in jobs_columns:
        logger.info("Migrating database: adding 'applied_date' column to jobs...")
        conn.execute("ALTER TABLE jobs ADD COLUMN applied_date TEXT")

    # Migration: Add post_scan_action column to email sources
    email_sources_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(custom_email_sources)").fetchall()
    }
    if "post_scan_action" not in email_sources_columns:
        logger.info("Migrating database: adding 'post_scan_action' to custom_email_sources...")
        conn.execute(
            "ALTER TABLE custom_email_sources ADD COLUMN post_scan_action TEXT DEFAULT 'none'"
        )

    # Migration: Add enrichment_status column for enrich-then-score pipeline
    if "enrichment_status" not in jobs_columns:
        logger.info("Migrating database: adding 'enrichment_status' column to jobs...")
        conn.execute("ALTER TABLE jobs ADD COLUMN enrichment_status TEXT DEFAULT 'pending'")

    # Migration: Add expanded followup columns for enhanced tracking
    followups_columns = {row[1] for row in conn.execute("PRAGMA table_info(followups)").fetchall()}
    if "gmail_message_id" not in followups_columns:
        logger.info("Migrating database: adding expanded followup columns...")
        conn.execute("ALTER TABLE followups ADD COLUMN gmail_message_id TEXT")
        conn.execute("ALTER TABLE followups ADD COLUMN full_body TEXT")
        conn.execute("ALTER TABLE followups ADD COLUMN sender_email TEXT")
        conn.execute("ALTER TABLE followups ADD COLUMN confidence REAL DEFAULT 0.8")
        conn.execute("ALTER TABLE followups ADD COLUMN action_required INTEGER DEFAULT 0")
        conn.execute("ALTER TABLE followups ADD COLUMN action_description TEXT")
        conn.execute("ALTER TABLE followups ADD COLUMN action_deadline TEXT")
        conn.execute("ALTER TABLE followups ADD COLUMN is_read INTEGER DEFAULT 0")
        conn.execute("ALTER TABLE followups ADD COLUMN ai_summary TEXT")


def get_db():
    """
    Create and return a database connection with Row factory.

    Establishes a SQLite connection with a 30-second timeout to handle
    concurrent access. The Row factory allows dict-like access to rows.

    Returns:
        sqlite3.Connection: Database connection with Row factory enabled

    Examples:
        >>> conn = get_db()
        >>> job = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (id,)).fetchone()
        >>> print(job['title'])  # Access by column name
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


def close_db(e=None):
    """Close database connection if it exists in flask g."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def create_job_from_confirmation(
    title: str,
    company: str,
    source: str = "email_confirmation",
    email_date: str = None,
    status: str = "applied",
    applied_date: str = None,
    raw_text: str = "",
    sender_email: str = "",
) -> str:
    """
    Create a minimal job record from an application confirmation email.

    These jobs have limited data (no URL, no location, no score) and should
    be flagged for enrichment to get full descriptions and requirements.

    Args:
        title: Job title extracted from confirmation email
        company: Company name extracted from sender or email content
        source: Source identifier (default: 'email_confirmation')
        email_date: Date the confirmation email was received
        status: Job status (default: 'applied')
        applied_date: Date application was submitted
        raw_text: Raw email text/snippet
        sender_email: Email address of the sender

    Returns:
        job_id: The generated unique job ID
    """
    import uuid
    from datetime import datetime

    job_id = str(uuid.uuid4())[:16]
    now = datetime.now().isoformat()
    email_date = email_date or now
    applied_date = applied_date or email_date

    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO jobs (
                job_id, title, company, source, status,
                applied_date, raw_text, email_date,
                created_at, updated_at, is_filtered
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
            (
                job_id,
                title,
                company,
                source,
                status,
                applied_date,
                raw_text,
                email_date,
                now,
                now,
            ),
        )
        conn.commit()
        logger.info(f"Created job from confirmation: {title} at {company} (id: {job_id})")
    finally:
        conn.close()

    return job_id


def is_email_processed(gmail_message_id: str) -> bool:
    """
    Check if an email has already been processed.

    Args:
        gmail_message_id: Gmail message ID

    Returns:
        True if email was already processed, False otherwise
    """
    conn = get_db()
    try:
        result = conn.execute(
            "SELECT 1 FROM processed_emails WHERE gmail_message_id = ?", (gmail_message_id,)
        ).fetchone()
        return result is not None
    finally:
        conn.close()


def mark_email_processed(
    gmail_message_id: str, email_type: str = "unknown", source: str = ""
) -> None:
    """
    Mark an email as processed to avoid reprocessing.

    Args:
        gmail_message_id: Gmail message ID
        email_type: Type of email (job_alert, confirmation, interview, etc.)
        source: Source that processed the email
    """
    from datetime import datetime

    conn = get_db()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO processed_emails
            (gmail_message_id, email_type, processed_at, source)
            VALUES (?, ?, ?, ?)
        """,
            (gmail_message_id, email_type, datetime.now().isoformat(), source),
        )
        conn.commit()
    finally:
        conn.close()


# Built-in email sources with their parser configurations
BUILTIN_EMAIL_SOURCES = [
    {
        "name": "LinkedIn Job Alerts",
        "sender_pattern": "@linkedin.com",
        "subject_keywords": "job,jobs,hiring,opportunity",
        "category": "job_board",
        "parser_class": "app.parsers.linkedin.LinkedInParser",
    },
    {
        "name": "Indeed Job Alerts",
        "sender_pattern": "@indeed.com,@indeedemail.com,@match.indeed.com",
        "subject_keywords": "job,jobs,hiring,new jobs",
        "category": "job_board",
        "parser_class": "app.parsers.indeed.IndeedParser",
    },
    {
        "name": "Greenhouse ATS",
        "sender_pattern": "@greenhouse.io",
        "subject_keywords": "job,opportunity,career",
        "category": "ats",
        "parser_class": "app.parsers.greenhouse.GreenhouseParser",
    },
    {
        "name": "Wellfound (AngelList)",
        "sender_pattern": "@wellfound.com,@angel.co",
        "subject_keywords": "job,jobs,startup,opportunity",
        "category": "job_board",
        "parser_class": "app.parsers.wellfound.WellfoundParser",
    },
    {
        "name": "Glassdoor",
        "sender_pattern": "@glassdoor.com",
        "subject_keywords": "job,jobs,hiring",
        "category": "job_board",
        "parser_class": None,  # Uses generic AI parser
    },
    {
        "name": "ZipRecruiter",
        "sender_pattern": "@ziprecruiter.com",
        "subject_keywords": "job,jobs,hiring,match",
        "category": "job_board",
        "parser_class": None,  # Uses generic AI parser
    },
    {
        "name": "Dice",
        "sender_pattern": "@dice.com",
        "subject_keywords": "job,jobs,tech,hiring",
        "category": "job_board",
        "parser_class": None,  # Uses generic AI parser
    },
    {
        "name": "ServiceNow Careers",
        "sender_pattern": "@servicenow.com",
        "subject_keywords": "job,career,opportunity,application",
        "category": "company",
        "parser_class": None,  # Uses generic AI parser
    },
    {
        "name": "WayUp",
        "sender_pattern": "@wayup.com",
        "subject_keywords": "job,jobs,opportunity,career",
        "category": "job_board",
        "parser_class": None,  # Uses generic AI parser
    },
]


def seed_builtin_sources():
    """
    Seed the database with built-in email sources.

    This function is called on app startup to ensure all built-in sources
    are in the database. It only inserts sources that don't already exist.

    Built-in sources have is_builtin=1 and cannot be deleted by users.
    """
    from datetime import datetime

    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    now = datetime.utcnow().isoformat()

    for source in BUILTIN_EMAIL_SOURCES:
        # Check if source already exists by name
        existing = conn.execute(
            "SELECT id FROM custom_email_sources WHERE name = ? AND is_builtin = 1",
            (source["name"],),
        ).fetchone()

        if existing:
            # Update existing source in case parser changed
            conn.execute(
                """
                UPDATE custom_email_sources
                SET sender_pattern = ?, subject_keywords = ?, category = ?,
                    parser_class = ?, updated_at = ?
                WHERE id = ?
            """,
                (
                    source["sender_pattern"],
                    source["subject_keywords"],
                    source["category"],
                    source["parser_class"],
                    now,
                    existing[0],
                ),
            )
        else:
            # Insert new built-in source
            conn.execute(
                """
                INSERT INTO custom_email_sources
                (name, sender_pattern, subject_keywords, category, parser_class,
                 is_builtin, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?)
            """,
                (
                    source["name"],
                    source["sender_pattern"],
                    source["subject_keywords"],
                    source["category"],
                    source["parser_class"],
                    now,
                    now,
                ),
            )

    conn.commit()
    conn.close()
    logger.info(f"Seeded {len(BUILTIN_EMAIL_SOURCES)} built-in email sources")


def detect_parser_type(sender_email: str) -> str:
    """Guess the best parser for a sender based on domain patterns."""
    domain = sender_email.split("@")[-1].lower()

    if "linkedin" in domain:
        return "linkedin"
    if "indeed" in domain:
        return "indeed"
    if "greenhouse" in domain:
        return "greenhouse"
    if "lever" in domain:
        return "greenhouse"
    if "wellfound" in domain or "angel" in domain:
        return "wellfound"

    return "generic"
