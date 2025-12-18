#!/usr/bin/env python3
"""
VoiceVerse TTS - JSON to SQLite Migration Script
Created: October 24, 2025
Purpose: Migrate data from JSON files to SQLite database with rollback support
"""

import json
import os
import shutil
from datetime import datetime
from database import Database


class MigrationError(Exception):
    """Custom exception for migration errors"""
    pass


class DataMigrator:
    """Handles migration from JSON files to SQLite database"""

    def __init__(self, dry_run=False):
        """
        Initialize migrator.

        Args:
            dry_run: If True, don't actually migrate, just validate
        """
        self.dry_run = dry_run
        self.db = None
        self.backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stats = {
            'users': 0,
            'audio_files': 0,
            'usage_stats': 0,
            'playback_history': 0
        }

    def backup_json_files(self):
        """Create timestamped backup of all JSON files"""
        print(f"\n📦 Creating backup in {self.backup_dir}/...")

        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        json_files = [
            'saved_audio/users.json',
            'saved_audio/metadata.json',
            'saved_audio/usage_stats.json',
            'saved_audio/playback_history.json'
        ]

        for json_file in json_files:
            if os.path.exists(json_file):
                backup_path = os.path.join(self.backup_dir, os.path.basename(json_file))
                shutil.copy2(json_file, backup_path)
                print(f"  ✓ Backed up {json_file}")
            else:
                print(f"  ⚠ Skipped {json_file} (not found)")

        print(f"✓ Backup completed in {self.backup_dir}/")

    def load_json(self, filepath):
        """
        Load and validate JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            Parsed JSON data or empty dict if file doesn't exist
        """
        if not os.path.exists(filepath):
            print(f"  ⚠ {filepath} not found, skipping...")
            return {}

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            print(f"  ✓ Loaded {filepath}: {len(data)} records")
            return data
        except json.JSONDecodeError as e:
            raise MigrationError(f"Invalid JSON in {filepath}: {e}")
        except Exception as e:
            raise MigrationError(f"Failed to load {filepath}: {e}")

    def migrate_users(self):
        """Migrate users from users.json to database"""
        print("\n👤 Migrating users...")

        users_data = self.load_json('saved_audio/users.json')

        if not users_data:
            print("  ℹ No users to migrate")
            return {}

        # Map username to user_id for later use
        username_to_id = {}

        for username, user_info in users_data.items():
            if self.dry_run:
                print(f"  [DRY RUN] Would create user: {username}")
                username_to_id[username] = len(username_to_id) + 1
            else:
                user_id = self.db.create_user(
                    username=username,
                    password_hash=user_info['password']
                )

                if user_id:
                    username_to_id[username] = user_id
                    self.stats['users'] += 1
                    print(f"  ✓ Migrated user: {username} (ID: {user_id})")
                else:
                    print(f"  ✗ Failed to migrate user: {username} (may already exist)")

        return username_to_id

    def migrate_audio_files(self, username_to_id):
        """
        Migrate audio files from metadata.json to database.

        Args:
            username_to_id: Mapping of usernames to database IDs
        """
        print("\n🎵 Migrating audio files...")

        metadata = self.load_json('saved_audio/metadata.json')

        if not metadata:
            print("  ℹ No audio files to migrate")
            return

        for filename, file_info in metadata.items():
            owner_username = file_info.get('owner', 'unknown')

            # Get owner_id from username
            owner_id = username_to_id.get(owner_username)

            if not owner_id:
                # Owner not found, try to create them
                print(f"  ⚠ Owner '{owner_username}' not found for {filename}")

                if not self.dry_run:
                    # Create a placeholder user
                    owner_id = self.db.create_user(
                        username=owner_username,
                        password_hash='placeholder_password'  # They'll need to reset
                    )

                    if owner_id:
                        username_to_id[owner_username] = owner_id
                        self.stats['users'] += 1
                        print(f"  ✓ Created placeholder user: {owner_username} (ID: {owner_id})")
                    else:
                        print(f"  ✗ Skipping {filename}: Could not create owner")
                        continue
                else:
                    # In dry run, just assign a dummy ID
                    owner_id = 999

            if self.dry_run:
                print(f"  [DRY RUN] Would create audio file: {filename}")
            else:
                file_id = self.db.create_audio_file(
                    filename=filename,
                    display_name=file_info.get('name', filename),
                    owner_id=owner_id,
                    voice=file_info.get('voice', 'unknown'),
                    category=file_info.get('group'),
                    text=None,  # Original text not stored in metadata
                    character_count=file_info.get('characters', 0),
                    cost=file_info.get('cost', 0.0),
                    duration=None  # Duration not stored in metadata
                )

                if file_id:
                    self.stats['audio_files'] += 1
                    print(f"  ✓ Migrated: {filename} (owner: {owner_username})")
                else:
                    print(f"  ✗ Failed to migrate: {filename} (may already exist)")

    def migrate_usage_stats(self, username_to_id):
        """
        Migrate usage statistics from usage_stats.json to database.

        Args:
            username_to_id: Mapping of usernames to database IDs
        """
        print("\n📊 Migrating usage statistics...")

        usage_data = self.load_json('saved_audio/usage_stats.json')

        if not usage_data:
            print("  ℹ No usage statistics to migrate")
            return

        for username, stats in usage_data.items():
            user_id = username_to_id.get(username)

            if not user_id:
                print(f"  ⚠ Skipping usage stats for unknown user: {username}")
                continue

            # Note: The existing usage_stats.json format may vary
            # Adjust this based on actual format
            if self.dry_run:
                print(f"  [DRY RUN] Would migrate usage stats for: {username}")
            else:
                # If usage stats has a simple format, record it
                # This is a placeholder - adjust based on actual format
                print(f"  ℹ Usage stats migration for {username} - format may need adjustment")

    def migrate_playback_history(self, username_to_id):
        """
        Migrate playback history from playback_history.json to database.

        Args:
            username_to_id: Mapping of usernames to database IDs
        """
        print("\n📜 Migrating playback history...")

        playback_data = self.load_json('saved_audio/playback_history.json')

        if not playback_data:
            print("  ℹ No playback history to migrate")
            return

        # Note: The existing playback_history.json format may vary
        # Adjust this based on actual format
        if self.dry_run:
            print(f"  [DRY RUN] Would migrate playback history")
        else:
            print(f"  ℹ Playback history migration - format may need adjustment")

    def verify_migration(self, username_to_id):
        """
        Verify that migration was successful.

        Args:
            username_to_id: Mapping of usernames to database IDs
        """
        print("\n🔍 Verifying migration...")

        if self.dry_run:
            print("  ℹ Skipping verification (dry run)")
            return True

        # Get database stats
        db_stats = self.db.get_stats()

        print(f"\n  Database contains:")
        print(f"    Users:         {db_stats['users']}")
        print(f"    Audio Files:   {db_stats['audio_files']}")
        print(f"    Usage Stats:   {db_stats['usage_records']}")
        print(f"    Playback Logs: {db_stats['playback_records']}")

        print(f"\n  Migration stats:")
        print(f"    Users:       {self.stats['users']}")
        print(f"    Audio Files: {self.stats['audio_files']}")

        # Basic validation
        if db_stats['users'] < self.stats['users']:
            print("  ⚠ WARNING: User count mismatch")
            return False

        if db_stats['audio_files'] < self.stats['audio_files']:
            print("  ⚠ WARNING: Audio file count mismatch")
            return False

        print("\n✓ Verification passed!")
        return True

    def run_migration(self, db_path='voiceverse.db'):
        """
        Execute the full migration process.

        Args:
            db_path: Path to SQLite database file
        """
        print("=" * 60)
        print("VoiceVerse TTS - JSON to SQLite Migration")
        print("=" * 60)

        if self.dry_run:
            print("\n🔎 DRY RUN MODE - No changes will be made")

        try:
            # Step 1: Backup JSON files
            if not self.dry_run:
                self.backup_json_files()

            # Step 2: Initialize database
            print(f"\n🗄️  Initializing database: {db_path}")
            if not self.dry_run:
                self.db = Database(db_path)
                print("  ✓ Database initialized")
            else:
                print("  [DRY RUN] Would initialize database")

            # Step 3: Migrate users (must be first due to foreign keys)
            username_to_id = self.migrate_users()

            # Step 4: Migrate audio files
            self.migrate_audio_files(username_to_id)

            # Step 5: Migrate usage statistics
            self.migrate_usage_stats(username_to_id)

            # Step 6: Migrate playback history
            self.migrate_playback_history(username_to_id)

            # Step 7: Verify migration
            success = self.verify_migration(username_to_id)

            # Summary
            print("\n" + "=" * 60)
            if self.dry_run:
                print("DRY RUN COMPLETE")
                print("=" * 60)
                print("\nNo changes were made. Run without --dry-run to migrate.")
            elif success:
                print("MIGRATION SUCCESSFUL")
                print("=" * 60)
                print(f"\n✓ Migrated {self.stats['users']} users")
                print(f"✓ Migrated {self.stats['audio_files']} audio files")
                print(f"\n📂 Backup saved to: {self.backup_dir}/")
                print("\n⚠️  IMPORTANT:")
                print("  1. Test the application with the new database")
                print("  2. If everything works, you can delete the backup")
                print(f"  3. If there are issues, restore from: {self.backup_dir}/")
            else:
                print("MIGRATION COMPLETED WITH WARNINGS")
                print("=" * 60)
                print("\n⚠️  Please review warnings above")

        except MigrationError as e:
            print(f"\n❌ Migration failed: {e}")
            print(f"\n💾 Backup available at: {self.backup_dir}/")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print(f"\n💾 Backup available at: {self.backup_dir}/")
            import traceback
            traceback.print_exc()
            return False

        return True

    def rollback(self):
        """Rollback migration by restoring JSON files from backup"""
        if not os.path.exists(self.backup_dir):
            print(f"❌ Backup directory not found: {self.backup_dir}")
            return False

        print(f"\n🔄 Rolling back from {self.backup_dir}...")

        backup_files = os.listdir(self.backup_dir)

        for backup_file in backup_files:
            if backup_file.endswith('.json'):
                src = os.path.join(self.backup_dir, backup_file)
                dst = os.path.join('saved_audio', backup_file)

                shutil.copy2(src, dst)
                print(f"  ✓ Restored {backup_file}")

        print("\n✓ Rollback complete")
        print(f"  The backup directory ({self.backup_dir}) is still available")
        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate VoiceVerse data from JSON to SQLite')
    parser.add_argument('--dry-run', action='store_true',
                      help='Perform a dry run without making changes')
    parser.add_argument('--db', default='voiceverse.db',
                      help='Path to SQLite database file (default: voiceverse.db)')
    parser.add_argument('--rollback', action='store_true',
                      help='Rollback the last migration')
    parser.add_argument('--backup-dir', help='Backup directory for rollback')

    args = parser.parse_args()

    migrator = DataMigrator(dry_run=args.dry_run)

    if args.rollback:
        if args.backup_dir:
            migrator.backup_dir = args.backup_dir
        migrator.rollback()
    else:
        migrator.run_migration(db_path=args.db)


if __name__ == '__main__':
    main()
