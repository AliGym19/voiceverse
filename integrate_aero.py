#!/usr/bin/env python3
"""
Integration script for Windows Vista/7 Aero Dashboard
This script will guide you through integrating the Aero interface into your existing TTS app.
"""

import os
import sys
import shutil
from pathlib import Path

def check_files_exist():
    """Check if all required Aero files are present"""
    required_files = [
        'templates/dashboard_aero.html',
        'static/css/aero_theme.css',
        'static/js/aero_player.js',
        'aero_routes.py'
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False

    print("✅ All required Aero files are present")
    return True

def create_directories():
    """Create necessary directories if they don't exist"""
    dirs = ['static/css', 'static/js', 'templates']
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Directory ensured: {dir_path}")

def add_import_to_main():
    """Add the import statement to tts_app19.py"""
    import_line = "from aero_routes import add_aero_routes\n"

    try:
        with open('tts_app19.py', 'r', encoding='utf-8') as f:
            content = f.read()

        if 'from aero_routes import add_aero_routes' in content:
            print("✅ Import already exists in tts_app19.py")
            return True

        # Find a good place to add the import (after other imports)
        lines = content.split('\n')
        import_index = 0

        for i, line in enumerate(lines):
            if line.startswith('from') or line.startswith('import'):
                import_index = i + 1

        lines.insert(import_index, import_line)

        with open('tts_app19.py', 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print("✅ Added import statement to tts_app19.py")
        return True

    except Exception as e:
        print(f"⚠️  Could not automatically add import: {e}")
        return False

def create_simple_integration_route():
    """Create a simple route addition file that can be manually integrated"""
    integration_code = '''
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
'''

    with open('aero_integration_code.py', 'w', encoding='utf-8') as f:
        f.write(integration_code)

    print("✅ Created aero_integration_code.py with route code to add manually")
    return True

def create_launch_script():
    """Create a launch script for easy testing"""
    launch_script = '''#!/usr/bin/env python3
"""
Launch script for VoiceVerse with Aero Dashboard
"""

import os
import subprocess
import sys
import time
import signal

def kill_port_5000():
    """Kill any process using port 5000"""
    try:
        result = subprocess.run(['lsof', '-ti:5000'], capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\\n')
            for pid in pids:
                subprocess.run(['kill', '-9', pid])
            print("✅ Cleared port 5000")
    except:
        pass

def launch_app():
    """Launch the TTS app with Aero dashboard"""
    print("🚀 Launching VoiceVerse with Windows Vista/7 Aero UI...")
    print("-" * 50)

    # Kill any existing process on port 5000
    kill_port_5000()
    time.sleep(1)

    # Launch the app
    try:
        process = subprocess.Popen(
            ['python3', 'tts_app19.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        print("✅ Application started!")
        print("📌 Access the Aero Dashboard at: http://localhost:5000/dashboard")
        print("📌 Access the classic interface at: http://localhost:5000/")
        print("-" * 50)
        print("Press Ctrl+C to stop the server")

        # Wait for the process
        while True:
            line = process.stdout.readline()
            if line:
                print(line.strip())

    except KeyboardInterrupt:
        print("\\n🛑 Shutting down...")
        process.terminate()
        time.sleep(1)
        kill_port_5000()
        print("✅ Server stopped")

if __name__ == "__main__":
    launch_app()
'''

    with open('launch_aero.py', 'w', encoding='utf-8') as f:
        f.write(launch_script)

    # Make it executable
    os.chmod('launch_aero.py', 0o755)

    print("✅ Created launch_aero.py launch script")
    return True

def print_manual_instructions():
    """Print manual integration instructions"""
    print("\n" + "=" * 60)
    print("MANUAL INTEGRATION INSTRUCTIONS")
    print("=" * 60)
    print("""
To complete the integration, add these routes to your tts_app19.py:

1. Open tts_app19.py in your editor

2. Add this import at the top with other imports:
   from flask import render_template

3. Add the routes from aero_integration_code.py to your app
   (The file has been created with the exact code to add)

4. Test the Aero dashboard:
   python3 launch_aero.py

5. Access the new interface at:
   http://localhost:5000/dashboard

6. The original interface remains at:
   http://localhost:5000/

Optional: To make Aero the default, change the main route:
   @app.route('/')
   @login_required
   def index():
       return redirect(url_for('aero_dashboard'))
""")

def main():
    """Main integration function"""
    print("\n🎨 Windows Vista/7 Aero Dashboard Integration")
    print("=" * 50)

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)

    # Create directories
    create_directories()

    # Check if files exist
    if not check_files_exist():
        print("\n⚠️  Please ensure all Aero files are present and try again")
        sys.exit(1)

    # Create integration files
    create_simple_integration_route()
    create_launch_script()

    # Try to add import automatically
    add_import_to_main()

    # Print instructions
    print_manual_instructions()

    print("\n✅ Integration preparation complete!")
    print("Follow the manual instructions above to complete the setup.")

if __name__ == "__main__":
    main()