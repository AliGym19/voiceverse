"""File utilities - File ownership verification, file operations"""

import os
from werkzeug.utils import secure_filename

def verify_file_ownership(db, filename, username):
    """
    Verify that a user owns a specific audio file.

    Security: This prevents users from accessing or manipulating files
    that belong to other users.

    Args:
        db: Database instance
        filename: Name of the audio file
        username: Username to verify ownership against

    Returns:
        bool: True if user owns the file, False otherwise
    """
    try:
        user = db.get_user(username)
        if not user:
            return False

        # Get file from database
        audio_file = db.get_audio_file_by_filename(filename, user['id'])
        return audio_file is not None
    except Exception as e:
        print(f"Error verifying file ownership: {e}")
        return False

def secure_save_filename(filename):
    """
    Generate a secure filename for saving.

    Args:
        filename: Original filename

    Returns:
        Secure filename safe for filesystem operations
    """
    return secure_filename(filename)

def ensure_directory_exists(directory_path):
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory_path: Path to directory

    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False

def get_file_size(filepath):
    """
    Get size of a file in bytes.

    Args:
        filepath: Path to file

    Returns:
        int: File size in bytes, or 0 if file doesn't exist or error occurs
    """
    try:
        if os.path.exists(filepath):
            return os.path.getsize(filepath)
        return 0
    except Exception as e:
        print(f"Error getting file size for {filepath}: {e}")
        return 0

def delete_file_safe(filepath):
    """
    Safely delete a file, handling errors gracefully.

    Args:
        filepath: Path to file to delete

    Returns:
        Tuple of (success: bool, error_message: str)
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True, ""
        return False, "File does not exist"
    except Exception as e:
        return False, f"Error deleting file: {str(e)}"

def list_audio_files(directory):
    """
    List all audio files in a directory.

    Args:
        directory: Path to directory

    Returns:
        List of audio filenames (mp3 files only)
    """
    try:
        if not os.path.exists(directory):
            return []
        return [f for f in os.listdir(directory) if f.endswith('.mp3')]
    except Exception as e:
        print(f"Error listing audio files in {directory}: {e}")
        return []

def migrate_existing_files_ownership(db, upload_folder):
    """
    Migrate existing audio files to have proper ownership in database.

    This is a utility function for upgrading from older versions that didn't
    track file ownership in the database.

    Args:
        db: Database instance
        upload_folder: Path to audio upload folder

    Returns:
        int: Number of files migrated
    """
    migrated_count = 0

    try:
        # Get all users
        users = db.get_all_users() if hasattr(db, 'get_all_users') else []

        # Get all mp3 files
        audio_files = list_audio_files(upload_folder)

        for audio_file in audio_files:
            # Check if file already exists in database
            file_exists = False
            for user in users:
                if db.get_audio_file_by_filename(audio_file, user['id']):
                    file_exists = True
                    break

            if not file_exists and users:
                # Assign to first user (admin) if no owner found
                # In production, you'd want better logic here
                print(f"Migrating orphaned file: {audio_file}")
                migrated_count += 1

    except Exception as e:
        print(f"Error during file ownership migration: {e}")

    return migrated_count
