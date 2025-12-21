#!/usr/bin/env python3
"""
TTS App - Old Spotify Theme Version (Port 5001)
This is a minimal version to run the old Spotify UI for comparison
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main app
from tts_app19 import app, HTML_TEMPLATE

# Monkey-patch the routes to use old template
from flask import render_template_string, session, redirect, url_for
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Override the index route to use old Spotify template
@app.route('/spotify')
@login_required
def spotify_dashboard():
    """Old Spotify-themed dashboard"""
    from datetime import datetime

    username = session.get('username', 'User')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Get CSRF token
    if 'csrf_token' not in session:
        import secrets
        session['csrf_token'] = secrets.token_hex(32)

    return render_template_string(
        HTML_TEMPLATE,
        username=username,
        timestamp=timestamp,
        error=None,
        success=None,
        csrf_token=session['csrf_token']
    )

if __name__ == '__main__':
    print("=" * 70)
    print("🎵 VoiceVerse - OLD SPOTIFY THEME")
    print("=" * 70)
    print(f"Running on: http://localhost:5001")
    print(f"Spotify UI: http://localhost:5001/spotify")
    print(f"")
    print(f"Compare with Aero UI on port 5000:")
    print(f"  Aero UI: http://localhost:5000/dashboard")
    print(f"")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    app.run(
        host='127.0.0.1',
        port=5001,
        debug=True,
        use_reloader=False
    )
