# Windows Aero Design Theme

This directory contains the complete Windows Vista/7 Aero glass theme implementation for VoiceVerse TTS Application.

## Contents

- `templates/dashboard_aero.html` - Main Aero dashboard template
- `static/css/aero_theme.css` - Complete Aero styling with glass effects and animations
- `static/js/aero_player.js` - JavaScript for Aero UI interactions
- `AERO_*.md` - Documentation files for the Aero theme

## Features

- Windows Vista/7 glass morphism design
- 8 custom CSS animations (floatOrb, aurora, shimmer, pulse, scanline, glow, spin, ripple)
- 6 unique voice gradients
- Floating orbs background with aurora effects
- Windows Media Player style bottom bar
- Responsive design with mobile-style navigation
- Green gradient titlebar with window controls

## How to Switch to Aero Theme

If you want to enable the Aero theme instead of the Spotify theme:

1. **Copy files to active directories:**
   ```bash
   cp aero_design/templates/dashboard_aero.html templates/
   cp aero_design/static/css/aero_theme.css static/css/
   cp aero_design/static/js/aero_player.js static/js/
   ```

2. **Update Flask routes in `tts_app19.py`:**

   Add the Aero dashboard route (around line 5250):
   ```python
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
   ```

   Change the main index route to redirect to Aero:
   ```python
   @app.route('/', methods=['GET', 'POST'])
   @login_required
   def index():
       """Redirect to the new Aero dashboard by default"""
       return redirect(url_for('aero_dashboard'))
   ```

3. **Restart the Flask application:**
   ```bash
   lsof -ti:5000 | xargs kill -9
   python3 tts_app19.py &
   ```

4. **Access the Aero theme:**
   Open http://localhost:5000/dashboard

## Reverting to Spotify Theme

To go back to the Spotify theme, simply remove the redirect in the index route and restore the original Spotify template rendering.

## Notes

- All Aero files are preserved here for future use
- The Aero theme is fully functional and tested
- Responsive design works on all screen sizes
- No changes to backend functionality or database structure
