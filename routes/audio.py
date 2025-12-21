"""Audio management routes - Download, Delete, Rename, Groups"""

from flask import Blueprint, send_file, request, jsonify, session
import os
from functools import wraps
from collections import defaultdict
from utils import verify_file_ownership as _verify_file_ownership, sanitize_display_name

audio_bp = Blueprint('audio', __name__)

# Dependencies (will be set by main app)
db = None
security_log = None
app_config = None

def init_audio(database, security_logger, config):
    """Initialize audio blueprint with dependencies"""
    global db, security_log, app_config
    db = database
    security_log = security_logger
    app_config = config

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            from flask import redirect, url_for
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def verify_file_ownership(filename, username):
    """Verify that the user owns the file"""
    return _verify_file_ownership(db, filename, username)

@audio_bp.route('/audio/<path:filename>')
@login_required
def audio(filename):
    """Serve audio files with ownership verification"""
    username = session.get('username')

    # Security: Verify file ownership
    if not verify_file_ownership(filename, username):
        return "Unauthorized", 403

    file_path = os.path.join(app_config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='audio/mpeg')
    return "File not found", 404

@audio_bp.route('/download/<path:filename>')
@login_required
def download(filename):
    """Download audio file with ownership verification"""
    username = session.get('username')

    # Security: Verify file ownership
    if not verify_file_ownership(filename, username):
        return "Unauthorized", 403

    file_path = os.path.join(app_config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        # Use the sanitized display name for the download
        display_name = sanitize_display_name(filename)
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"{display_name}.mp3",
            mimetype='audio/mpeg'
        )
    return "File not found", 404

@audio_bp.route('/rename/<path:filename>', methods=['POST'])
@login_required
def rename(filename):
    """Rename an audio file"""
    username = session.get('username')
    user = db.get_user(username)

    # Security: Verify file ownership
    if not verify_file_ownership(filename, username):
        return jsonify({'error': 'Unauthorized'}), 403

    new_name = request.form.get('new_name', '').strip()
    if not new_name:
        return jsonify({'error': 'Name cannot be empty'}), 400

    # Update filename in database
    success = db.rename_audio_file(filename, new_name, user['id'])

    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to rename file'}), 500

@audio_bp.route('/delete/<path:filename>', methods=['POST'])
@login_required
def delete(filename):
    """Delete an audio file"""
    username = session.get('username')
    user = db.get_user(username)

    # Security: Verify file ownership
    if not verify_file_ownership(filename, username):
        return jsonify({'error': 'Unauthorized'}), 403

    # Delete from database
    db.delete_audio_file(filename, user['id'])

    # Delete physical file
    file_path = os.path.join(app_config['UPLOAD_FOLDER'], filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@audio_bp.route('/delete-group/<path:group_name>', methods=['POST'])
def delete_group(group_name):
    """Delete all files in a group"""
    username = session.get('username')
    user = db.get_user(username)

    # Get all files in the group
    files = db.get_audio_files_by_group(group_name, user['id'])

    # Delete each file
    for file_info in files:
        filename = file_info['filename']
        db.delete_audio_file(filename, user['id'])

        # Delete physical file
        file_path = os.path.join(app_config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file {filename}: {e}")

    return jsonify({'success': True})

@audio_bp.route('/rename-group/<path:old_name>', methods=['POST'])
def rename_group(old_name):
    """Rename a group"""
    username = session.get('username')
    user = db.get_user(username)

    new_name = request.form.get('new_name', '').strip()
    if not new_name:
        return jsonify({'error': 'Name cannot be empty'}), 400

    # Update all files in the group
    success = db.rename_group(old_name, new_name, user['id'])

    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to rename group'}), 500

@audio_bp.route('/api/groups', methods=['GET'])
@login_required
def get_groups():
    """Get all groups with file counts"""
    username = session.get('username')
    user = db.get_user(username)

    files = db.get_audio_files_by_owner(user['id'])

    # Group files by group_name
    groups = defaultdict(int)
    for file in files:
        group = file.get('group_name', 'Ungrouped')
        groups[group] += 1

    return jsonify(dict(groups))

@audio_bp.route('/api/move-to-group', methods=['POST'])
@login_required
def move_to_group():
    """Move a file to a different group"""
    username = session.get('username')
    user = db.get_user(username)

    data = request.get_json()
    filename = data.get('filename')
    new_group = data.get('group', '').strip()

    # Security: Verify file ownership
    if not verify_file_ownership(filename, username):
        return jsonify({'error': 'Unauthorized'}), 403

    # Update group in database
    success = db.update_audio_file_group(filename, new_group, user['id'])

    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to move file'}), 500

@audio_bp.route('/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    """Delete multiple files at once"""
    username = session.get('username')
    user = db.get_user(username)

    data = request.get_json()
    filenames = data.get('files', [])

    deleted_count = 0
    for filename in filenames:
        # Security: Verify file ownership
        if verify_file_ownership(filename, username):
            db.delete_audio_file(filename, user['id'])

            # Delete physical file
            file_path = os.path.join(app_config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting file {filename}: {e}")

    return jsonify({'success': True, 'deleted_count': deleted_count})

@audio_bp.route('/bulk-move', methods=['POST'])
@login_required
def bulk_move():
    """Move multiple files to a group"""
    username = session.get('username')
    user = db.get_user(username)

    data = request.get_json()
    filenames = data.get('files', [])
    new_group = data.get('group', '').strip()

    moved_count = 0
    for filename in filenames:
        # Security: Verify file ownership
        if verify_file_ownership(filename, username):
            if db.update_audio_file_group(filename, new_group, user['id']):
                moved_count += 1

    return jsonify({'success': True, 'moved_count': moved_count})

@audio_bp.route('/api/history', methods=['GET'])
@login_required
def get_history():
    """Get recently played audio files"""
    # This could be enhanced to track actual play history
    # For now, return recent files
    username = session.get('username')
    user = db.get_user(username)

    files = db.get_audio_files_by_owner(user['id'])
    # Return only the 10 most recent
    recent_files = sorted(files, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
    return jsonify([{'filename': f['filename'], 'created_at': f['created_at']} for f in recent_files])

@audio_bp.route('/api/clear-history', methods=['POST'])
@login_required
def clear_history_endpoint():
    """Clear play history"""
    # Placeholder for future implementation
    return jsonify({'success': True})

@audio_bp.route('/api/add-to-history', methods=['POST'])
@login_required
def add_to_history_endpoint():
    """Add file to play history"""
    # Placeholder for future implementation
    data = request.get_json()
    filename = data.get('filename')
    return jsonify({'success': True})
