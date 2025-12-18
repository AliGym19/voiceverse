"""
Aero Dashboard Routes for VoiceVerse TTS Application
Add these routes to your tts_app19.py file to enable the Windows Vista/7 Aero interface
"""

from flask import render_template, request, jsonify, session, send_file, redirect, url_for
from functools import wraps
import os
import json
from datetime import datetime

def add_aero_routes(app, db, security_log, lockout, get_agent_system, client, login_required):
    """
    Add Windows Vista/7 Aero themed routes to the Flask app.

    Call this function in your main tts_app19.py file after app initialization:
    add_aero_routes(app, db, security_log, lockout, get_agent_system, client, login_required)
    """

    @app.route('/dashboard')
    @login_required
    def aero_dashboard():
        """Windows Vista/7 Aero themed dashboard"""
        try:
            user_id = session.get('user_id')
            username = session.get('username', 'User')

            # Get timestamp for filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            return render_template('dashboard_aero.html',
                username=username,
                timestamp=timestamp,
                csrf_token=generate_csrf_token()
            )
        except Exception as e:
            print(f"Error loading Aero dashboard: {e}")
            return redirect(url_for('index'))

    @app.route('/api/audio-files', methods=['GET'])
    @login_required
    def get_audio_files():
        """API endpoint to get user's audio files"""
        try:
            user_id = session.get('user_id')
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT filename, voice, speed, text_preview, group_name,
                       file_path, created_at
                FROM audio_files
                WHERE user_id = ?
                ORDER BY created_at DESC
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
                    'created_at': row[6],
                    'display_name': row[0].replace('_', ' ').replace('.mp3', '')
                })

            conn.close()
            return jsonify(files)

        except Exception as e:
            print(f"Error getting audio files: {e}")
            return jsonify([]), 500

    @app.route('/api/agent/recommend-voice', methods=['POST'])
    @login_required
    def recommend_voice():
        """API endpoint for voice recommendation agent"""
        try:
            data = request.get_json()
            text = data.get('text', '')

            if not text:
                return jsonify({'error': 'No text provided'}), 400

            agents = get_agent_system()
            recommendation = agents.recommend_voice(text)

            return jsonify(recommendation)

        except Exception as e:
            print(f"Error recommending voice: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/generate-aero', methods=['POST'])
    @login_required
    def generate_audio_aero():
        """Aero-specific audio generation endpoint with enhanced feedback"""
        try:
            user_id = session.get('user_id')
            username = session.get('username')

            # Get form data
            text = request.form.get('text', '').strip()
            voice = request.form.get('voice', 'nova')
            filename = request.form.get('filename', f'audio_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            group = request.form.get('group', 'Uncategorized')
            speed = float(request.form.get('speed', 1.0))

            # AI features
            use_preprocessing = request.form.get('use_preprocessing') == 'on'
            use_chunking = request.form.get('use_chunking') == 'on'
            model = 'tts-1-hd' if request.form.get('model') == 'tts-1-hd' else 'tts-1'

            # Validate input
            if not text:
                return jsonify({'error': 'No text provided'}), 400

            if len(text) > 100000:
                return jsonify({'error': 'Text too long (max 100,000 characters)'}), 400

            # Apply AI preprocessing if enabled
            if use_preprocessing:
                try:
                    agents = get_agent_system()
                    text = agents.preprocess_text(text)
                except Exception as e:
                    print(f"Preprocessing failed: {e}")

            # Handle long text with chunking
            if len(text) > 4096 and use_chunking:
                try:
                    agents = get_agent_system()
                    chunks = agents.smart_chunk_text(text)
                    # For now, just use the first chunk
                    text = chunks[0] if chunks else text[:4096]
                except Exception as e:
                    print(f"Chunking failed: {e}")
                    text = text[:4096]
            elif len(text) > 4096:
                text = text[:4096]

            # Generate audio
            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=speed
            )

            # Save audio file
            safe_filename = f"{filename}_{user_id}_{int(datetime.now().timestamp())}.mp3"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)

            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            with open(file_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

            # Save to database
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO audio_files (user_id, filename, voice, speed,
                                        text_preview, group_name, file_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, safe_filename, voice, speed,
                text[:100], group, file_path, datetime.now()
            ))

            conn.commit()
            conn.close()

            # Log successful generation
            security_log.log_event('audio_generated', user_id, request)

            return jsonify({
                'success': True,
                'filename': safe_filename,
                'display_name': filename
            })

        except Exception as e:
            print(f"Error generating audio: {e}")
            return jsonify({'error': str(e)}), 500

def generate_csrf_token():
    """Generate a CSRF token for the session"""
    import secrets
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

# Instructions for integration:
"""
To integrate the Aero dashboard into your existing tts_app19.py:

1. Add this import at the top of your tts_app19.py file:
   from aero_routes import add_aero_routes

2. After your app initialization and login_required decorator definition, add:
   add_aero_routes(app, db, security_log, lockout, get_agent_system, client, login_required)

3. Ensure the static files are in place:
   - /static/css/aero_theme.css
   - /static/js/aero_player.js
   - /templates/dashboard_aero.html

4. Access the new dashboard at: http://localhost:5000/dashboard

5. Optional: Redirect the main route to the Aero dashboard:
   @app.route('/')
   @login_required
   def index():
       return redirect(url_for('aero_dashboard'))
"""