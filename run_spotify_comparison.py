#!/usr/bin/env python3
"""
Run Old Spotify Theme on Port 5001 for Comparison
"""

from flask import Flask, render_template, session, redirect, url_for, request
import secrets
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Simple login check
def is_logged_in():
    return 'spotify_user' in session

@app.route('/')
def index():
    if not is_logged_in():
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Simple login - just set session
        session['spotify_user'] = 'demo'
        return redirect(url_for('dashboard'))

    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Spotify Theme - Login</title>
        <style>
            body {
                background: #121212;
                color: white;
                font-family: 'Segoe UI', sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
            }
            .login-box {
                background: #282828;
                padding: 40px;
                border-radius: 8px;
                text-align: center;
            }
            h1 {
                color: #1DB954;
                margin-bottom: 30px;
            }
            button {
                background: #1DB954;
                color: white;
                border: none;
                padding: 15px 40px;
                border-radius: 25px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }
            button:hover {
                background: #1ed760;
            }
            .note {
                margin-top: 20px;
                color: #b3b3b3;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>🎵 OLD SPOTIFY THEME</h1>
            <p>This is the original Spotify dark theme (Port 5001)</p>
            <form method="POST">
                <button type="submit">Enter Demo</button>
            </form>
            <div class="note">
                Compare with new Aero theme on:<br>
                <strong>http://localhost:5000/dashboard</strong>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect(url_for('login'))

    # Prepare all template variables needed by spotify_demo.html
    username = session.get('spotify_user', 'Demo User')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Mock usage data for demo
    usage_data = {
        'files_generated': 42,
        'total_characters': 12500,
        'total_cost': 0.18
    }

    # CSRF token
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)

    # Use the spotify_demo.html template with all required variables
    try:
        return render_template('spotify_demo.html',
            username=username,
            timestamp=timestamp,
            error=None,
            success=None,
            usage=usage_data,
            csrf_token=session['csrf_token']
        )
    except Exception as e:
        # If template fails, show a simple message
        return f'''
        <html>
        <head><title>Spotify Demo - Error</title></head>
        <body style="background: #121212; color: white; font-family: sans-serif; padding: 40px;">
            <h1>Template Error</h1>
            <p>Error loading Spotify template: {str(e)}</p>
            <p><a href="/" style="color: #1DB954;">Back to Login</a></p>
            <hr>
            <p><strong>Instead, visit the Aero theme:</strong></p>
            <p><a href="http://localhost:5000/dashboard" style="color: #1DB954;">Aero Dashboard (Port 5000)</a></p>
        </body>
        </html>
        '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    print()
    print("=" * 70)
    print("🎵 OLD SPOTIFY THEME - Comparison Server")
    print("=" * 70)
    print()
    print("  OLD Spotify Theme: http://localhost:5001/")
    print("  NEW Aero Theme:    http://localhost:5000/dashboard")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    app.run(
        host='127.0.0.1',
        port=5001,
        debug=False
    )
