#!/usr/bin/env python3
"""
Migration script to create job entries for existing external applications.

This script:
1. Finds all external applications that don't have a linked job (is_linked_to_job = 0 or job_id is NULL)
2. Creates a corresponding job entry for each one
3. Links the external application to the job

Run this ONCE if you have existing external applications that aren't showing up in the job list.
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "jobs.db"

def migrate_external_apps():
    """Create job entries for external applications that don't have them."""

    if not DB_PATH.exists():
        print("❌ Database file not found. No migration needed.")
        return

    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row

    # Find external applications without linked jobs
    unlinked_apps = conn.execute('''
        SELECT * FROM external_applications
        WHERE is_linked_to_job = 0 OR job_id IS NULL OR job_id = ''
    ''').fetchall()

    if not unlinked_apps:
        print("✅ No unlinked external applications found. Migration not needed.")
        conn.close()
        return

    print(f"📋 Found {len(unlinked_apps)} external applications without linked jobs.")
    print("🔄 Creating job entries...")

    migrated_count = 0
    now = datetime.now().isoformat()

    for app in unlinked_apps:
        app_dict = dict(app)

        # Generate a new job_id
        job_id = str(uuid.uuid4())[:16]

        try:
            # Create job entry
            conn.execute('''
                INSERT INTO jobs (
                    job_id, title, company, location, url, source,
                    status, score, baseline_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id,
                app_dict['title'],
                app_dict['company'],
                app_dict.get('location', ''),
                app_dict.get('url', ''),
                f"external_{app_dict['source']}",
                'applied',  # External apps are already applied
                0,  # Default score
                0,  # Default baseline score
                app_dict.get('created_at', now),
                now
            ))

            # Update external application to link to the job
            conn.execute('''
                UPDATE external_applications
                SET job_id = ?, is_linked_to_job = 1, updated_at = ?
                WHERE app_id = ?
            ''', (job_id, now, app_dict['app_id']))

            migrated_count += 1
            print(f"  ✓ Created job for: {app_dict['title']} at {app_dict['company']}")

        except Exception as e:
            print(f"  ✗ Failed to migrate {app_dict['title']}: {e}")
            continue

    conn.commit()
    conn.close()

    print(f"\n✅ Migration complete! Created {migrated_count} job entries.")
    print("🎉 Your external applications should now appear in the main job list!")

if __name__ == '__main__':
    print("=" * 60)
    print("External Applications Migration Script")
    print("=" * 60)
    migrate_external_apps()
