"""
Database - Database operations

This module handles all database initialization and connection management
for the Hammy the Hire Tracker SQLite database.
"""

import sqlite3
import logging

from constants import DB_PATH

logger = logging.getLogger(__name__)


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

    Uses WAL (Write-Ahead Logging) mode for better concurrency when
    multiple processes/threads access the database.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0)

    # Enable WAL mode for better concurrency (allows simultaneous reads during writes)
    conn.execute("PRAGMA journal_mode=WAL")

    # Create tables if they don't exist
    conn.execute('''
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
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_scan_date TEXT,
            emails_found INTEGER,
            created_at TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            url TEXT,
            notes TEXT,
            created_at TEXT
        )
    ''')
    conn.execute('''
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
    ''')
    conn.execute('''
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
    ''')

    # Resume management tables
    conn.execute('''
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
    ''')

    conn.execute('''
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
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS tracked_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            career_page_url TEXT,
            job_alert_email TEXT,
            notes TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS custom_email_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sender_email TEXT,
            sender_pattern TEXT,
            subject_keywords TEXT,
            enabled INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS deleted_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_url TEXT NOT NULL UNIQUE,
            title TEXT,
            company TEXT,
            deleted_at TEXT,
            deleted_reason TEXT DEFAULT 'user_deleted'
        )
    ''')

    # Migration: Add job_id column if it doesn't exist
    try:
        conn.execute("SELECT job_id FROM followups LIMIT 1")
    except sqlite3.OperationalError:
        logger.info("🔄 Migrating database: adding 'job_id' column to followups...")
        conn.execute("ALTER TABLE followups ADD COLUMN job_id TEXT")

    # Migration: Add viewed column if it doesn't exist
    try:
        conn.execute("SELECT viewed FROM jobs LIMIT 1")
    except sqlite3.OperationalError:
        logger.info("🔄 Migrating database: adding 'viewed' column...")
        conn.execute("ALTER TABLE jobs ADD COLUMN viewed INTEGER DEFAULT 0")

    # Migration: Add job_description column if it doesn't exist
    try:
        conn.execute("SELECT job_description FROM jobs LIMIT 1")
    except sqlite3.OperationalError:
        logger.info("🔄 Migrating database: adding 'job_description' column...")
        conn.execute("ALTER TABLE jobs ADD COLUMN job_description TEXT")

    # Migration: Add resume-related columns to jobs table
    try:
        conn.execute("SELECT recommended_resume_id FROM jobs LIMIT 1")
    except sqlite3.OperationalError:
        logger.info("🔄 Migrating database: adding resume-related columns to jobs...")
        conn.execute("ALTER TABLE jobs ADD COLUMN recommended_resume_id TEXT")
        conn.execute("ALTER TABLE jobs ADD COLUMN resume_recommendation TEXT")
        conn.execute("ALTER TABLE jobs ADD COLUMN selected_resume_id TEXT")
        conn.execute("ALTER TABLE jobs ADD COLUMN resume_match_score REAL")

    conn.commit()
    conn.close()


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
    conn = sqlite3.connect(DB_PATH, timeout=30.0)  # Wait up to 30s for lock
    conn.row_factory = sqlite3.Row
    return conn
