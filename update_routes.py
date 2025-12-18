#!/usr/bin/env python3
"""
Script to update tts_app19.py routes to use database instead of JSON files.
This script makes surgical replacements to avoid breaking the application.
"""

import re

def update_file_listing_route(content):
    """Update the main index route to use database for file listing"""

    # Pattern 1: Replace metadata loading and file listing in index route (around line 4195-4210)
    pattern1 = r'''    metadata = load_metadata\(\)
    usage = load_usage\(\)

    all_files = \[
        \{
            'filename': fname,
            'name': data\.get\('name', fname\),
            'group': data\.get\('group', 'Uncategorized'\),
            'created': data\.get\('created', ''\),
            'chars': data\.get\('characters', 0\),
            'cost': data\.get\('cost', 0\)
        \}
        for fname, data in metadata\.items\(\)
        if os\.path\.exists\(os\.path\.join\(app\.config\['UPLOAD_FOLDER'\], fname\)\)
    \]'''

    replacement1 = '''    # Get user ID
    user = db.get_user(session['username'])
    if not user:
        return redirect(url_for('login'))

    # Get files for this user from database
    audio_files_db = db.get_audio_files_by_owner(user['id'])

    all_files = [
        {
            'filename': file_info['filename'],
            'name': file_info['display_name'],
            'group': file_info['category'] or 'Uncategorized',
            'created': file_info['created_at'],
            'chars': file_info['character_count'],
            'cost': file_info['cost']
        }
        for file_info in audio_files_db
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], file_info['filename']))
    ]

    # Get usage stats
    usage = db.get_all_time_usage(user['id'])'''

    content = re.sub(pattern1, replacement1, content)

    return content

def update_file_creation_route(content):
    """Update TTS generation route to save to database"""

    # Pattern 2: Replace metadata and usage saving after TTS generation (around line 4160-4184)
    pattern2 = r'''                metadata = load_metadata\(\)
                metadata\[safe_filename\] = \{
                    'name': file_name,
                    'group': group,
                    'created': timestamp,
                    'voice': voice,
                    'characters': char_count,
                    'cost': cost,
                    'owner': session\['username'\]  # Security: Track file ownership
                \}
                save_metadata\(metadata\)

                usage = load_usage\(\)
                usage\['total_characters'\] \+= char_count
                usage\['total_cost'\] \+= cost
                usage\['files_generated'\] \+= 1

                current_month = datetime\.now\(\)\.strftime\("%Y-%m"\)
                if current_month not in usage\['monthly'\]:
                    usage\['monthly'\]\[current_month\] = \{'cost': 0, 'files': 0, 'characters': 0\}
                usage\['monthly'\]\[current_month\]\['cost'\] \+= cost
                usage\['monthly'\]\[current_month\]\['files'\] \+= 1
                usage\['monthly'\]\[current_month\]\['characters'\] \+= char_count

                save_usage\(usage\)'''

    replacement2 = '''                # Get user ID
                user = db.get_user(session['username'])
                if not user:
                    error = "User not found"
                    return redirect(url_for('login'))

                # Save file metadata to database
                db.create_audio_file(
                    filename=safe_filename,
                    display_name=file_name,
                    owner_id=user['id'],
                    voice=voice,
                    category=group,
                    text=text,
                    character_count=char_count,
                    cost=cost
                )

                # Record usage statistics
                db.record_usage(user['id'], char_count, cost)'''

    content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)

    return content

def update_delete_route(content):
    """Update delete route to use database"""

    # Pattern 3: Replace metadata deletion in delete route
    pattern3 = r'''        metadata = load_metadata\(\)
        if filename in metadata:
            del metadata\[filename\]
            save_metadata\(metadata\)'''

    replacement3 = '''        file_info = db.get_audio_file(filename)
        if file_info:
            db.delete_audio_file(file_info['id'])'''

    content = re.sub(pattern3, replacement3, content)

    return content

def update_edit_route(content):
    """Update edit route to use database"""

    # Pattern 4: Replace metadata update in edit route
    pattern4 = r'''        metadata = load_metadata\(\)
        if safe_filename in metadata:
            metadata\[safe_filename\]\['name'\] = new_name
            if new_group:
                metadata\[safe_filename\]\['group'\] = new_group
            save_metadata\(metadata\)'''

    replacement4 = '''        file_info = db.get_audio_file(safe_filename)
        if file_info:
            update_data = {'display_name': new_name}
            if new_group:
                update_data['category'] = new_group
            db.update_audio_file(file_info['id'], **update_data)'''

    content = re.sub(pattern4, replacement4, content)

    return content

def update_export_routes(content):
    """Update export routes to use database"""

    # Pattern 5: Replace metadata/usage loading in export routes
    pattern5 = r'''        metadata = load_metadata\(\)
        usage = load_usage\(\)'''

    replacement5 = '''        # Get user ID
        user = db.get_user(session['username'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get files and usage from database
        audio_files_db = db.get_audio_files_by_owner(user['id'])
        usage = db.get_all_time_usage(user['id'])

        # Build metadata dict for compatibility
        metadata = {
            f['filename']: {
                'name': f['display_name'],
                'group': f['category'] or 'Uncategorized',
                'created': f['created_at'],
                'voice': f['voice'],
                'characters': f['character_count'],
                'cost': f['cost']
            }
            for f in audio_files_db
        }'''

    content = re.sub(pattern5, replacement5, content)

    return content

def main():
    print("Reading tts_app19.py...")
    with open('/Users/ali/Desktop/Project/tts_app19.py', 'r', encoding='utf-8') as f:
        content = f.read()

    print("Updating file listing route...")
    content = update_file_listing_route(content)

    print("Updating file creation route...")
    content = update_file_creation_route(content)

    print("Updating delete route...")
    content = update_delete_route(content)

    print("Updating edit route...")
    content = update_edit_route(content)

    print("Updating export routes...")
    content = update_export_routes(content)

    print("Writing updated file...")
    with open('/Users/ali/Desktop/Project/tts_app19.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ Route updates complete!")

if __name__ == '__main__':
    main()
