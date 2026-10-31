#!/usr/bin/env python3
"""
CIVILENS — Clean Presentation Database Maintenance Script
Phase 12: Academic Viva Presentation Preparation

This script safely wipes and reinitializes ONLY the configured presentation database
(default: data/civilens_presentation.db) and the presentation upload staging directory
(default: uploads_presentation).

SAFETY CONSTRAINTS:
- NEVER deletes or modifies data/civic_issues.db or existing user records.
- Strictly guards against running against non-presentation databases.
- Retains database schema, routing configurations, and default auth roles (citizen, inspector, admin).
"""

import sys
import os
import shutil
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Force presentation mode for this script
os.environ["CIVILENS_PRESENTATION_MODE"] = "true"

from app.config import settings
from app.db.database import init_db, build_engine, get_session_factory
from app.db.repository import SqliteIssueRepository


def clean_presentation_environment() -> None:
    print("=" * 70)
    print("CIVILENS — CLEAN PRESENTATION ENVIRONMENT RESET")
    print("=" * 70)

    target_db_path = settings.resolved_db_path.resolve()
    print(f"Target Presentation Database: {target_db_path}")

    # Safety Guard: Ensure we never touch the primary production/dev database
    if "presentation" not in target_db_path.name.lower():
        print(f"FATAL SAFETY ABORT: Target database '{target_db_path.name}' is NOT a presentation database!")
        print("This cleanup script is strictly restricted to presentation databases (*presentation*.db).")
        sys.exit(1)

    # 1. Initialize schema
    print("\n1. Initializing presentation database schema...")
    engine = build_engine(target_db_path)
    init_db(target_engine=engine)
    session_factory = get_session_factory(engine)
    repo = SqliteIssueRepository(session_factory=session_factory)

    # 2. Ensure default auth accounts (citizen, inspector, admin)
    print("2. Ensuring default authentication accounts (citizen, inspector, admin)...")
    repo.seed_default_users_if_empty()

    # 3. Wipe all complaint records, audit logs, and lifecycle events
    print("3. Wiping all complaint records, audit logs, and lifecycle events...")
    cleared = repo.clear_issues()
    print(f"   Cleared {cleared} issue records.")

    # 4. Clean uploads_presentation directory
    upload_dir = settings.resolved_upload_dir.resolve()
    print(f"\n4. Cleaning presentation upload directory: {upload_dir}")
    if "presentation" not in str(upload_dir).lower():
        print(f"   WARNING: Upload dir '{upload_dir}' does not contain 'presentation'. Skipping file wipe.")
    else:
        if upload_dir.exists():
            deleted_files = 0
            for item in upload_dir.iterdir():
                if item.is_file():
                    item.unlink()
                    deleted_files += 1
                elif item.is_dir() and item.name != "__pycache__":
                    shutil.rmtree(item)
            print(f"   Removed {deleted_files} disposable uploaded presentation files.")
        else:
            upload_dir.mkdir(parents=True, exist_ok=True)
            print("   Created empty presentation upload directory.")

    # 5. Verification
    print("\n5. Verifying clean presentation state...")
    issues = repo.list_issues()
    print(f"   Pre-existing issues in presentation database: {len(issues)}")
    if len(issues) != 0:
        print("   ERROR: Presentation database is not empty!")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("SUCCESS: Clean presentation environment ready for live demonstration!")
    print(f"Database Path: {target_db_path}")
    print(f"Upload Path:   {upload_dir}")
    print("Complaint Count: 0 (Pure clean empty state)")
    print("=" * 70)


if __name__ == "__main__":
    clean_presentation_environment()
