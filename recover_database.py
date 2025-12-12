#!/usr/bin/env python3
"""
Recover database from WAL files.
This script creates an empty database structure and lets SQLite merge the WAL files.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'jobs.db'
print(f"Attempting to recover database at: {DB_PATH}")

# Create connection - this will create the file and auto-apply WAL files if they exist
conn = sqlite3.connect(str(DB_PATH), timeout=30.0)

# Enable WAL mode
conn.execute("PRAGMA journal_mode=WAL")

# Create all tables (matches local_app.py schema)
print("Creating database schema...")

# Jobs table
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

# External applications table
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

# Resume usage log table
conn.execute('''
    CREATE TABLE IF NOT EXISTS resume_usage_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT,
        resume_variant TEXT,
        resume_file TEXT,
        used_at TEXT,
        FOREIGN KEY (job_id) REFERENCES jobs(job_id)
    )
''')

# Scan history table
conn.execute('''
    CREATE TABLE IF NOT EXISTS scan_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        last_scan_date TEXT,
        emails_found INTEGER,
        created_at TEXT
    )
''')

# Watchlist table
conn.execute('''
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT NOT NULL,
        url TEXT,
        notes TEXT,
        created_at TEXT
    )
''')

# Followups table
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

# Tracked companies table (from add-tracked-companies branch)
conn.execute('''
    CREATE TABLE IF NOT EXISTS tracked_companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT NOT NULL UNIQUE,
        website TEXT,
        careers_page TEXT,
        notes TEXT,
        last_checked TEXT,
        status TEXT DEFAULT 'watching',
        created_at TEXT,
        updated_at TEXT
    )
''')

conn.commit()

# Try to checkpoint WAL to merge data
print("Attempting to merge WAL files...")
try:
    conn.execute("PRAGMA wal_checkpoint(FULL)")
    print("✅ WAL checkpoint successful")
except Exception as e:
    print(f"⚠️  WAL checkpoint warning: {e}")

# Check what data we have
cursor = conn.cursor()

# Count jobs
cursor.execute("SELECT COUNT(*) FROM jobs")
job_count = cursor.fetchone()[0]
print(f"\n📊 Database Recovery Results:")
print(f"  Jobs: {job_count}")

# Count external applications
cursor.execute("SELECT COUNT(*) FROM external_applications")
app_count = cursor.fetchone()[0]
print(f"  External Applications: {app_count}")

# Count tracked companies
try:
    cursor.execute("SELECT COUNT(*) FROM tracked_companies")
    company_count = cursor.fetchone()[0]
    print(f"  Tracked Companies: {company_count}")
except:
    print(f"  Tracked Companies: 0 (table doesn't exist yet)")

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()
print(f"\n✅ Database tables:")
for table in tables:
    print(f"  ✓ {table[0]}")

conn.close()
print(f"\n✅ Database recovery complete!")
print(f"📁 Database location: {DB_PATH}")
