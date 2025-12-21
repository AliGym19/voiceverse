#!/usr/bin/env python3
"""
VoiceVerse Database Migration Manager
Manages database schema versioning and migrations

Usage:
    python3 migrations/migration_manager.py status      # Show current migration status
    python3 migrations/migration_manager.py upgrade     # Upgrade to latest version
    python3 migrations/migration_manager.py downgrade   # Downgrade one version
    python3 migrations/migration_manager.py create <name> # Create new migration
"""

import os
import sys
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict


# Color codes for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


class Migration:
    """Represents a single database migration"""

    def __init__(self, version: int, name: str, description: str):
        self.version = version
        self.name = name
        self.description = description

    def up(self, conn: sqlite3.Connection):
        """Apply the migration (override in subclasses)"""
        raise NotImplementedError("Subclasses must implement the up() method")

    def down(self, conn: sqlite3.Connection):
        """Revert the migration (override in subclasses)"""
        raise NotImplementedError("Subclasses must implement the down() method")


class MigrationManager:
    """Manages database migrations for VoiceVerse"""

    def __init__(self, db_path: str = 'voiceverse.db', migrations_dir: Optional[Path] = None):
        """Initialize the migration manager"""
        self.db_path = db_path
        if migrations_dir is None:
            self.migrations_dir = Path(__file__).parent
        else:
            self.migrations_dir = Path(migrations_dir)

        self.migrations: List[Migration] = []
        self._load_migrations()

    def print_success(self, message: str):
        """Print success message in green"""
        print(f"{GREEN}✓ {message}{NC}")

    def print_warning(self, message: str):
        """Print warning message in yellow"""
        print(f"{YELLOW}⚠ {message}{NC}")

    def print_error(self, message: str):
        """Print error message in red"""
        print(f"{RED}✗ {message}{NC}")

    def print_info(self, message: str):
        """Print info message in blue"""
        print(f"{BLUE}ℹ {message}{NC}")

    def _load_migrations(self):
        """Load all available migrations"""
        # For now, we'll define migrations inline
        # In a real system, you might load these from separate files
        self.migrations = [
            InitialSchemaMigration(),
            # Add more migrations here as needed
        ]

        # Sort migrations by version
        self.migrations.sort(key=lambda m: m.version)

    def _ensure_migrations_table(self, conn: sqlite3.Connection):
        """Ensure the migrations tracking table exists"""
        conn.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL,
                description TEXT
            )
        ''')
        conn.commit()

    def get_current_version(self) -> int:
        """Get the current database schema version"""
        try:
            conn = sqlite3.connect(self.db_path)
            self._ensure_migrations_table(conn)

            cursor = conn.execute(
                'SELECT MAX(version) FROM schema_migrations'
            )
            result = cursor.fetchone()
            conn.close()

            return result[0] if result[0] is not None else 0
        except Exception as e:
            self.print_error(f"Failed to get current version: {str(e)}")
            return 0

    def get_applied_migrations(self) -> List[Dict]:
        """Get list of all applied migrations"""
        try:
            conn = sqlite3.connect(self.db_path)
            self._ensure_migrations_table(conn)

            cursor = conn.execute(
                'SELECT version, name, applied_at, description FROM schema_migrations ORDER BY version'
            )
            results = cursor.fetchall()
            conn.close()

            return [
                {
                    'version': row[0],
                    'name': row[1],
                    'applied_at': row[2],
                    'description': row[3]
                }
                for row in results
            ]
        except Exception as e:
            self.print_error(f"Failed to get applied migrations: {str(e)}")
            return []

    def backup_database(self) -> Tuple[bool, str]:
        """
        Create a backup of the database before migration
        Returns: (success, backup_path)
        """
        if not os.path.exists(self.db_path):
            return False, "Database file does not exist"

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = Path(self.db_path).parent / 'backups'
        backup_dir.mkdir(exist_ok=True)

        backup_path = backup_dir / f"voiceverse_backup_{timestamp}.db"

        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return True, str(backup_path)
        except Exception as e:
            return False, f"Backup failed: {str(e)}"

    def apply_migration(self, migration: Migration) -> Tuple[bool, str]:
        """
        Apply a single migration
        Returns: (success, message)
        """
        # Create backup first
        backup_success, backup_path = self.backup_database()
        if not backup_success:
            return False, f"Backup failed: {backup_path}"

        try:
            conn = sqlite3.connect(self.db_path)
            self._ensure_migrations_table(conn)

            # Apply the migration
            migration.up(conn)

            # Record the migration
            conn.execute('''
                INSERT INTO schema_migrations (version, name, applied_at, description)
                VALUES (?, ?, ?, ?)
            ''', (
                migration.version,
                migration.name,
                datetime.utcnow().isoformat() + 'Z',
                migration.description
            ))

            conn.commit()
            conn.close()

            return True, f"Migration {migration.version} applied successfully (backup: {backup_path})"
        except Exception as e:
            # Restore from backup on failure
            self.print_error(f"Migration failed: {str(e)}")
            self.print_warning(f"Restoring from backup: {backup_path}")

            try:
                import shutil
                shutil.copy2(backup_path, self.db_path)
                return False, f"Migration failed and database restored from backup: {str(e)}"
            except Exception as restore_error:
                return False, f"Migration failed AND restore failed: {str(e)} / {str(restore_error)}"

    def revert_migration(self, migration: Migration) -> Tuple[bool, str]:
        """
        Revert a single migration
        Returns: (success, message)
        """
        # Create backup first
        backup_success, backup_path = self.backup_database()
        if not backup_success:
            return False, f"Backup failed: {backup_path}"

        try:
            conn = sqlite3.connect(self.db_path)

            # Revert the migration
            migration.down(conn)

            # Remove the migration record
            conn.execute(
                'DELETE FROM schema_migrations WHERE version = ?',
                (migration.version,)
            )

            conn.commit()
            conn.close()

            return True, f"Migration {migration.version} reverted successfully (backup: {backup_path})"
        except Exception as e:
            return False, f"Revert failed: {str(e)}"

    def upgrade(self, target_version: Optional[int] = None) -> int:
        """
        Upgrade database to target version (or latest if not specified)
        Returns: number of migrations applied
        """
        current_version = self.get_current_version()

        if target_version is None:
            target_version = max([m.version for m in self.migrations]) if self.migrations else 0

        if current_version >= target_version:
            self.print_info(f"Database already at version {current_version}")
            return 0

        migrations_to_apply = [
            m for m in self.migrations
            if current_version < m.version <= target_version
        ]

        if not migrations_to_apply:
            self.print_info("No migrations to apply")
            return 0

        self.print_info(f"Applying {len(migrations_to_apply)} migration(s)...")

        applied_count = 0
        for migration in migrations_to_apply:
            self.print_info(f"Applying migration {migration.version}: {migration.name}")
            success, message = self.apply_migration(migration)

            if success:
                self.print_success(message)
                applied_count += 1
            else:
                self.print_error(message)
                break

        return applied_count

    def downgrade(self, steps: int = 1) -> int:
        """
        Downgrade database by specified number of steps
        Returns: number of migrations reverted
        """
        current_version = self.get_current_version()

        if current_version == 0:
            self.print_info("Database is at initial version (0)")
            return 0

        migrations_to_revert = [
            m for m in reversed(self.migrations)
            if m.version <= current_version
        ][:steps]

        if not migrations_to_revert:
            self.print_info("No migrations to revert")
            return 0

        self.print_info(f"Reverting {len(migrations_to_revert)} migration(s)...")

        reverted_count = 0
        for migration in migrations_to_revert:
            self.print_info(f"Reverting migration {migration.version}: {migration.name}")
            success, message = self.revert_migration(migration)

            if success:
                self.print_success(message)
                reverted_count += 1
            else:
                self.print_error(message)
                break

        return reverted_count

    def status(self):
        """Print current migration status"""
        current_version = self.get_current_version()
        applied_migrations = self.get_applied_migrations()

        print("\n" + "=" * 60)
        print("Database Migration Status")
        print("=" * 60 + "\n")

        print(f"Database: {self.db_path}")
        print(f"Current Version: {current_version}")
        print(f"Latest Available Version: {max([m.version for m in self.migrations]) if self.migrations else 0}")

        if applied_migrations:
            print(f"\nApplied Migrations ({len(applied_migrations)}):")
            print("-" * 60)
            for mig in applied_migrations:
                print(f"  v{mig['version']}: {mig['name']}")
                print(f"      Applied: {mig['applied_at']}")
                if mig['description']:
                    print(f"      {mig['description']}")
        else:
            print("\nNo migrations have been applied yet.")

        pending_migrations = [m for m in self.migrations if m.version > current_version]
        if pending_migrations:
            print(f"\nPending Migrations ({len(pending_migrations)}):")
            print("-" * 60)
            for mig in pending_migrations:
                print(f"  v{mig.version}: {mig.name}")
                print(f"      {mig.description}")

        print("\n" + "=" * 60 + "\n")


# Migration Definitions
class InitialSchemaMigration(Migration):
    """Initial database schema (current state)"""

    def __init__(self):
        super().__init__(
            version=1,
            name="initial_schema",
            description="Initial database schema with users, audio_files, and security_events tables"
        )

    def up(self, conn: sqlite3.Connection):
        """This migration is a no-op since the schema already exists"""
        # The current schema is already in place via database.py
        # This migration just records the baseline
        pass

    def down(self, conn: sqlite3.Connection):
        """Cannot downgrade from initial schema"""
        raise Exception("Cannot downgrade from initial schema")


def main():
    parser = argparse.ArgumentParser(
        description='VoiceVerse Database Migration Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    Show migration status:
        python3 migrations/migration_manager.py status

    Upgrade to latest version:
        python3 migrations/migration_manager.py upgrade

    Downgrade one version:
        python3 migrations/migration_manager.py downgrade

    Downgrade multiple versions:
        python3 migrations/migration_manager.py downgrade --steps 3

    Create new migration:
        python3 migrations/migration_manager.py create add_user_preferences
        """
    )

    parser.add_argument(
        'command',
        choices=['status', 'upgrade', 'downgrade', 'create'],
        help='Command to execute'
    )

    parser.add_argument(
        'name',
        nargs='?',
        help='Migration name (for create command)'
    )

    parser.add_argument(
        '--db',
        type=str,
        default='voiceverse.db',
        help='Database file path (default: voiceverse.db)'
    )

    parser.add_argument(
        '--steps',
        type=int,
        default=1,
        help='Number of steps for downgrade (default: 1)'
    )

    args = parser.parse_args()

    # Initialize manager
    manager = MigrationManager(db_path=args.db)

    if args.command == 'status':
        manager.status()
        return 0

    elif args.command == 'upgrade':
        count = manager.upgrade()
        if count > 0:
            manager.print_success(f"Successfully applied {count} migration(s)")
        return 0

    elif args.command == 'downgrade':
        count = manager.downgrade(steps=args.steps)
        if count > 0:
            manager.print_success(f"Successfully reverted {count} migration(s)")
        return 0

    elif args.command == 'create':
        if not args.name:
            manager.print_error("Migration name is required for create command")
            return 1

        # Get next version number
        current_version = manager.get_current_version()
        next_version = max([m.version for m in manager.migrations]) + 1 if manager.migrations else 1

        template = f'''
"""
Migration: {args.name}
Version: {next_version}
Created: {datetime.now().isoformat()}
"""

from migration_manager import Migration
import sqlite3


class {args.name.title().replace('_', '')}Migration(Migration):
    """TODO: Add migration description"""

    def __init__(self):
        super().__init__(
            version={next_version},
            name="{args.name}",
            description="TODO: Add description"
        )

    def up(self, conn: sqlite3.Connection):
        """Apply the migration"""
        # TODO: Add migration code here
        # Example:
        # conn.execute("""
        #     ALTER TABLE users ADD COLUMN new_column TEXT
        # """)
        # conn.commit()
        pass

    def down(self, conn: sqlite3.Connection):
        """Revert the migration"""
        # TODO: Add rollback code here
        # Example:
        # conn.execute("""
        #     ALTER TABLE users DROP COLUMN new_column
        # """)
        # conn.commit()
        pass
'''

        migration_file = manager.migrations_dir / f"migration_{next_version:03d}_{args.name}.py"

        with open(migration_file, 'w') as f:
            f.write(template.strip() + '\n')

        manager.print_success(f"Created migration file: {migration_file}")
        manager.print_info(f"Edit the file and add it to migration_manager.py's _load_migrations() method")
        return 0

    return 0


if __name__ == '__main__':
    sys.exit(main())
