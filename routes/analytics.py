"""Analytics routes - Usage statistics and activity tracking"""

from flask import Blueprint, jsonify, session
from functools import wraps

analytics_bp = Blueprint('analytics', __name__)

# Dependencies
db = None

def init_analytics(database):
    """Initialize analytics blueprint with dependencies"""
    global db
    db = database

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@analytics_bp.route('/api/analytics/stats', methods=['GET'])
@login_required
def analytics_stats():
    """Get user analytics statistics"""
    try:
        username = session.get('username')
        user = db.get_user(username)

        # Get usage statistics
        usage = db.get_all_time_usage(user['id'])
        files = db.get_audio_files_by_owner(user['id'])

        return jsonify({
            'success': True,
            'stats': {
                'total_files': usage.get('files_generated', 0),
                'total_cost': usage.get('total_cost', 0.0),
                'total_characters': usage.get('total_characters', 0),
                'file_count_by_voice': {},  # Could be enhanced
                'recent_activity_count': len(files[:10]) if files else 0
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/recent-activity', methods=['GET'])
@login_required
def analytics_recent_activity():
    """Get recent activity"""
    try:
        username = session.get('username')
        user = db.get_user(username)

        # Get recent files
        files = db.get_recent_audio_files(user['id'], limit=20)

        activity = [{
            'filename': f['filename'],
            'voice': f.get('voice', 'unknown'),
            'created_at': f.get('created_at', ''),
            'group': f.get('group_name', 'Ungrouped')
        } for f in files]

        return jsonify({
            'success': True,
            'activity': activity
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
