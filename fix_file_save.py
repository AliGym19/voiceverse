#!/usr/bin/env python3
"""
Diagnostic and fix script for file saving issue in tts_app19.py
The issue: POST requests return 200 instead of 302, indicating an error is occurring
"""

import re

def add_comprehensive_logging():
    """Add detailed logging to track exactly where the TTS generation is failing"""

    # Read the current file
    with open('/Users/ali/Desktop/Project/tts_app19.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the POST route handler and add logging
    # Pattern to match the TTS generation section
    pattern = r'''(            if request\.method == 'POST' and text and voice:.*?)
(                try:
                    # Get user ID
                    user = db\.get_user\(session\['username'\]\)
                    if not user:
                        error = "User not found"
                        return redirect\(url_for\('login'\)\)

                    # Save file metadata to database
                    db\.create_audio_file\(
                        filename=safe_filename,
                        display_name=file_name,
                        owner_id=user\['id'\],
                        voice=voice,
                        category=group,
                        text=text,
                        character_count=char_count,
                        cost=cost
                    \)

                    # Record usage statistics
                    db\.record_usage\(user\['id'\], char_count, cost\)

                    # Redirect to home page to show the newly created file
                    return redirect\(url_for\('index', success='1', play_file=safe_filename, play_name=file_name\)\))'''

    # Replacement with comprehensive logging and error handling
    replacement = r'''\1
                # Add logging to trace the issue
                print(f"DEBUG: Starting TTS generation - User: {session.get('username')}, Voice: {voice}, Text length: {len(text)}")

                try:
                    # Get user ID with error checking
                    username = session.get('username')
                    if not username:
                        print(f"ERROR: No username in session")
                        error = "Session expired. Please login again."
                        raise Exception("No username in session")

                    print(f"DEBUG: Getting user from database for username: {username}")
                    user = db.get_user(username)

                    if not user:
                        print(f"ERROR: User '{username}' not found in database")
                        error = f"User '{username}' not found. Please login again."
                        return redirect(url_for('login'))

                    print(f"DEBUG: Found user ID: {user['id']}, Username: {user['username']}")

                    # Try to save file metadata to database
                    print(f"DEBUG: Attempting to save file to database - Filename: {safe_filename}, Owner ID: {user['id']}")

                    file_id = db.create_audio_file(
                        filename=safe_filename,
                        display_name=file_name,
                        owner_id=user['id'],
                        voice=voice,
                        category=group,
                        text=text,
                        character_count=char_count,
                        cost=cost
                    )

                    if not file_id:
                        print(f"ERROR: Failed to create audio file in database")
                        error = "Failed to save file to database. Please try again."
                        raise Exception("Database save failed")

                    print(f"DEBUG: Successfully saved file to database with ID: {file_id}")

                    # Record usage statistics
                    print(f"DEBUG: Recording usage stats - User ID: {user['id']}, Chars: {char_count}, Cost: {cost}")
                    db.record_usage(user['id'], char_count, cost)

                    print(f"DEBUG: TTS generation complete, redirecting to index")

                    # Redirect to home page to show the newly created file
                    return redirect(url_for('index', success='1', play_file=safe_filename, play_name=file_name))'''

    # Apply the replacement
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Also add exception handling for the outer try block
    pattern2 = r'''(                except Exception as e:
                    error = f"Generation failed: {str\(e\)}")'''

    replacement2 = r'''                except Exception as e:
                    print(f"ERROR: Exception during TTS generation: {e}")
                    import traceback
                    traceback.print_exc()
                    error = f"Generation failed: {str(e)}")'''

    content = re.sub(pattern2, replacement2, content)

    # Write the updated file
    with open('/Users/ali/Desktop/Project/tts_app19.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ Added comprehensive logging to TTS generation route")

def fix_database_connection():
    """Ensure database connection is properly initialized"""

    with open('/Users/ali/Desktop/Project/tts_app19.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if database is properly initialized
    if 'db = Database(' not in content:
        print("❌ Database initialization not found! Adding it...")

        # Find the right place to add database initialization (after app config)
        pattern = r'(csrf = CSRFProtect\(app\))'
        replacement = r'''\1

# Database: Initialize SQLite database
db = Database('voiceverse.db')
print("✅ Database initialized successfully")'''

        content = re.sub(pattern, replacement, content)

        with open('/Users/ali/Desktop/Project/tts_app19.py', 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Added database initialization")
    else:
        print("✅ Database initialization already present")

def main():
    print("🔧 Fixing file save issue in tts_app19.py...")
    print("-" * 50)

    # First ensure database is initialized
    fix_database_connection()

    # Then add comprehensive logging
    add_comprehensive_logging()

    print("-" * 50)
    print("✅ Fixes applied successfully!")
    print("\n📝 Next steps:")
    print("1. Restart the server")
    print("2. Try generating a new file")
    print("3. Check the terminal output for DEBUG messages")
    print("4. The debug messages will show exactly where the process is failing")

if __name__ == '__main__':
    main()