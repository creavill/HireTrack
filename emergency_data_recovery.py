#!/usr/bin/env python3
"""
Emergency Data Recovery for Corrupted SQLite Database
Attempts multiple recovery methods to salvage job application data.
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'jobs.db'
OUTPUT_DIR = Path(__file__).parent / 'recovered_data'

def create_output_dir():
    """Create directory for recovered data."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"📁 Recovery output directory: {OUTPUT_DIR}")

def attempt_1_read_only_mode():
    """Try opening database in read-only mode."""
    print("\n" + "="*60)
    print("ATTEMPT 1: Read-Only Mode")
    print("="*60)

    try:
        # Open in read-only mode with URI
        uri = f"file:{DB_PATH}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row

        # Try to read jobs table
        cursor = conn.execute("SELECT * FROM jobs")
        jobs = [dict(row) for row in cursor.fetchall()]

        if jobs:
            output_file = OUTPUT_DIR / f'jobs_readonly_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w') as f:
                json.dump(jobs, f, indent=2)

            print(f"✅ SUCCESS! Recovered {len(jobs)} jobs")
            print(f"📄 Saved to: {output_file}")
            conn.close()
            return True
        else:
            print("⚠️  Database opened but no jobs found")
            conn.close()
            return False

    except Exception as e:
        print(f"❌ Read-only mode failed: {e}")
        return False

def attempt_2_ignore_corruption():
    """Try reading with corruption checks disabled."""
    print("\n" + "="*60)
    print("ATTEMPT 2: Ignore Corruption Flags")
    print("="*60)

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        # Disable integrity checks
        conn.execute("PRAGMA ignore_check_constraints = ON")
        conn.execute("PRAGMA defer_foreign_keys = ON")

        # Try to read each table
        tables = ['jobs', 'external_applications', 'resume_variants', 'tracked_companies']
        all_data = {}

        for table in tables:
            try:
                cursor = conn.execute(f"SELECT * FROM {table}")
                rows = [dict(row) for row in cursor.fetchall()]
                all_data[table] = rows
                print(f"  ✓ {table}: {len(rows)} records")
            except Exception as e:
                print(f"  ✗ {table}: {e}")
                all_data[table] = []

        conn.close()

        # Save if we got anything
        if any(len(records) > 0 for records in all_data.values()):
            output_file = OUTPUT_DIR / f'all_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w') as f:
                json.dump(all_data, f, indent=2)

            total_records = sum(len(records) for records in all_data.values())
            print(f"\n✅ SUCCESS! Recovered {total_records} total records")
            print(f"📄 Saved to: {output_file}")
            return True
        else:
            print("⚠️  No data recovered")
            return False

    except Exception as e:
        print(f"❌ Ignore corruption mode failed: {e}")
        return False

def attempt_3_partial_read():
    """Try to read individual pages of the database."""
    print("\n" + "="*60)
    print("ATTEMPT 3: Partial Page Reading")
    print("="*60)

    try:
        # Try reading with smaller page size
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA page_size = 512")

        # Try LIMIT queries to read in chunks
        jobs = []
        offset = 0
        chunk_size = 10

        while True:
            try:
                cursor = conn.execute(f"SELECT * FROM jobs LIMIT {chunk_size} OFFSET {offset}")
                chunk = [dict(row) for row in cursor.fetchall()]

                if not chunk:
                    break

                jobs.extend(chunk)
                print(f"  ✓ Read chunk at offset {offset}: {len(chunk)} records")
                offset += chunk_size

            except Exception as e:
                print(f"  ✗ Chunk at offset {offset} failed: {e}")
                break

        conn.close()

        if jobs:
            output_file = OUTPUT_DIR / f'jobs_partial_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w') as f:
                json.dump(jobs, f, indent=2)

            print(f"\n✅ SUCCESS! Recovered {len(jobs)} jobs via partial reading")
            print(f"📄 Saved to: {output_file}")
            return True
        else:
            print("⚠️  No data recovered via partial reading")
            return False

    except Exception as e:
        print(f"❌ Partial reading failed: {e}")
        return False

def attempt_4_wal_file_reading():
    """Try to read data directly from WAL file."""
    print("\n" + "="*60)
    print("ATTEMPT 4: Read WAL File Directly")
    print("="*60)

    wal_path = Path(__file__).parent / 'jobs.db-wal'

    if not wal_path.exists():
        print("⚠️  No WAL file found")
        return False

    try:
        # Read WAL file as binary and search for text patterns
        with open(wal_path, 'rb') as f:
            wal_content = f.read()

        # Look for common job-related strings
        text_content = wal_content.decode('utf-8', errors='ignore')

        # Search for job titles, companies, URLs
        indicators = ['http://', 'https://', '.com', 'linkedin', 'indeed', 'greenhouse']
        found_data = []

        for line in text_content.split('\n'):
            if any(indicator in line.lower() for indicator in indicators):
                found_data.append(line.strip())

        if found_data:
            output_file = OUTPUT_DIR / f'wal_extracted_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(found_data))

            print(f"✅ Found {len(found_data)} potential data fragments in WAL file")
            print(f"📄 Saved to: {output_file}")
            print("⚠️  Note: This is raw data, may need manual parsing")
            return True
        else:
            print("⚠️  No recognizable data in WAL file")
            return False

    except Exception as e:
        print(f"❌ WAL file reading failed: {e}")
        return False

def attempt_5_dump_schema():
    """Try to at least dump the database schema."""
    print("\n" + "="*60)
    print("ATTEMPT 5: Dump Schema (Last Resort)")
    print("="*60)

    try:
        conn = sqlite3.connect(DB_PATH)

        # Try to get table schema
        cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table'")
        schema = [row[0] for row in cursor.fetchall() if row[0]]

        conn.close()

        if schema:
            output_file = OUTPUT_DIR / f'schema_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sql'
            with open(output_file, 'w') as f:
                f.write('\n\n'.join(schema))

            print(f"✅ Schema recovered (structure only, no data)")
            print(f"📄 Saved to: {output_file}")
            return True
        else:
            print("⚠️  Could not recover schema")
            return False

    except Exception as e:
        print(f"❌ Schema dump failed: {e}")
        return False

def main():
    """Run all recovery attempts."""
    print("\n" + "="*60)
    print("🚨 EMERGENCY DATABASE RECOVERY")
    print("="*60)
    print(f"Database: {DB_PATH}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nAttempting all recovery methods...")

    if not DB_PATH.exists():
        print(f"\n❌ Database file not found: {DB_PATH}")
        return

    create_output_dir()

    # Try all recovery methods
    success = False
    success |= attempt_1_read_only_mode()
    success |= attempt_2_ignore_corruption()
    success |= attempt_3_partial_read()
    success |= attempt_4_wal_file_reading()
    success |= attempt_5_dump_schema()

    print("\n" + "="*60)
    if success:
        print("✅ RECOVERY COMPLETE")
        print("="*60)
        print(f"\n📁 Check the '{OUTPUT_DIR}' folder for recovered data")
        print("\nNext steps:")
        print("1. Review the recovered JSON/TXT files")
        print("2. If you found your jobs data, you can manually import it")
        print("3. If recovery worked, you may not need to delete the database!")
    else:
        print("❌ RECOVERY FAILED")
        print("="*60)
        print("\nNo data could be recovered. The database is truly corrupted.")
        print("You can safely delete jobs.db, jobs.db-shm, and jobs.db-wal")
        print("The app will create a fresh database on next startup.")

    print("\n")

if __name__ == '__main__':
    main()
