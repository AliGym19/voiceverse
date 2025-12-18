
# ============================================================================
# WINDOWS VISTA/7 AERO DASHBOARD INTEGRATION
# Add this code to your tts_app19.py file after app initialization
# ============================================================================

from flask import render_template

@app.route('/dashboard')
@login_required
def aero_dashboard():
    """Windows Vista/7 Aero themed dashboard"""
    from datetime import datetime

    username = session.get('username', 'User')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Get CSRF token
    if 'csrf_token' not in session:
        import secrets
        session['csrf_token'] = secrets.token_hex(32)

    return render_template('dashboard_aero.html',
        username=username,
        timestamp=timestamp,
        csrf_token=session['csrf_token']
    )

@app.route('/api/audio-files', methods=['GET'])
@login_required
def api_get_audio_files():
    """API endpoint to get user's audio files for Aero dashboard"""
    user_id = session.get('user_id')

    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT filename, voice, speed, text_preview, group_name,
               file_path, created_at
        FROM audio_files
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    """, (user_id,))

    files = []
    for row in cursor.fetchall():
        files.append({
            'filename': row[0],
            'voice': row[1],
            'speed': row[2],
            'text_preview': row[3],
            'group': row[4],
            'file_path': row[5],
            'created_at': row[6] if row[6] else None,
            'display_name': row[0].replace('_', ' ').replace('.mp3', '') if row[0] else 'Audio File'
        })

    conn.close()
    return jsonify(files)

# ============================================================================
# END OF AERO DASHBOARD INTEGRATION
# ============================================================================
