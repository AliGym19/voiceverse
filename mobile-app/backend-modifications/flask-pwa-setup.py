"""
Flask PWA Setup - Add Progressive Web App support to tts_app19.py

This file contains the code modifications needed to enable PWA functionality
in your existing Flask application.

INSTALLATION:
1. Install flask-cors: pip3 install flask-cors
2. Copy the static files to your Flask static directory
3. Add the routes below to tts_app19.py
4. Update your HTML templates to include PWA meta tags and scripts

"""

from flask import send_from_directory, jsonify, request
from flask_cors import CORS
import os

# ==================== CORS SETUP ====================
# Add this near the top of tts_app19.py, after creating the Flask app

def setup_cors(app):
    """
    Enable CORS for mobile app access

    In production, replace '*' with your actual domain:
    CORS(app, origins=['https://yourdomain.com', 'https://app.yourdomain.com'])
    """
    CORS(app,
         origins=['*'],  # Change in production!
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

    return app

# Usage: app = setup_cors(app)


# ==================== PWA ROUTES ====================
# Add these routes to tts_app19.py

def add_pwa_routes(app):
    """Add PWA-specific routes to Flask app"""

    @app.route('/manifest.json')
    def manifest():
        """Serve PWA manifest"""
        return send_from_directory('mobile-app/pwa', 'manifest.json', mimetype='application/json')

    @app.route('/service-worker.js')
    def service_worker():
        """Serve service worker with correct MIME type and no-cache headers"""
        response = send_from_directory('mobile-app/pwa', 'service-worker.js', mimetype='application/javascript')
        response.headers['Service-Worker-Allowed'] = '/'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @app.route('/offline')
    def offline():
        """Offline fallback page"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Offline - VoiceVerse</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background-color: #191414;
                    color: #ffffff;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    margin: 0;
                    padding: 20px;
                    text-align: center;
                }
                .offline-container {
                    max-width: 400px;
                }
                h1 {
                    color: #1DB954;
                    margin-bottom: 1rem;
                }
                p {
                    color: #b3b3b3;
                    line-height: 1.6;
                }
                button {
                    background-color: #1DB954;
                    color: #191414;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 24px;
                    font-weight: 700;
                    cursor: pointer;
                    margin-top: 1rem;
                }
            </style>
        </head>
        <body>
            <div class="offline-container">
                <h1>You're Offline</h1>
                <p>It looks like you've lost your internet connection. Check your connection and try again.</p>
                <button onclick="window.location.reload()">Try Again</button>
            </div>
        </body>
        </html>
        """

    @app.route('/api/analytics/event', methods=['POST'])
    def analytics_event():
        """
        Handle PWA analytics events
        Optional: integrate with your analytics system
        """
        try:
            data = request.get_json()
            event_name = data.get('event')
            event_data = data.get('data', {})
            timestamp = data.get('timestamp')

            # Log to your analytics system here
            print(f"[PWA Analytics] {event_name}: {event_data}")

            # You can store in database, send to Google Analytics, etc.

            return jsonify({'success': True}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/share', methods=['POST'])
    def share_target():
        """
        Handle Web Share Target API
        Allows sharing text to your app from other apps
        """
        try:
            title = request.form.get('title', '')
            text = request.form.get('text', '')
            url = request.form.get('url', '')

            # Pre-fill TTS form with shared text
            shared_content = f"{title}\n\n{text}\n\n{url}".strip()

            # Redirect to main page with pre-filled text
            from urllib.parse import quote
            return redirect(f"/?text={quote(shared_content)}")

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return app

# Usage: app = add_pwa_routes(app)


# ==================== SECURITY HEADERS ====================
# Add these headers for PWA security

def add_pwa_headers(app):
    """Add security and PWA-specific headers"""

    @app.after_request
    def add_security_headers(response):
        # Existing security headers (keep your current ones)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # PWA-specific headers
        # Allow service worker to control all pages
        if request.path == '/service-worker.js':
            response.headers['Service-Worker-Allowed'] = '/'

        # Cache control for static assets
        if '/static/' in request.path:
            response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year

        # No cache for HTML pages
        if response.content_type == 'text/html':
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'

        return response

    return app

# Usage: app = add_pwa_headers(app)


# ==================== HTTPS REDIRECT ====================
# Force HTTPS in production for PWA requirements

def force_https(app):
    """
    Redirect HTTP to HTTPS in production
    PWAs require HTTPS (except localhost)
    """

    @app.before_request
    def redirect_to_https():
        # Skip redirect for localhost
        if request.host.startswith('localhost') or request.host.startswith('127.0.0.1'):
            return None

        # Skip if already HTTPS
        if request.is_secure:
            return None

        # Redirect to HTTPS
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

    return app

# Usage (only in production): app = force_https(app)


# ==================== OFFLINE QUEUE MANAGEMENT ====================
# API endpoints for managing offline queue

def add_offline_queue_routes(app):
    """Add routes for offline queue management"""

    @app.route('/api/queue/add', methods=['POST'])
    def add_to_queue():
        """Add TTS request to offline queue"""
        try:
            data = request.get_json()
            # Store in database or session
            # This will be synced when back online
            return jsonify({'success': True, 'queue_id': 'generated_id'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/queue/list', methods=['GET'])
    def get_queue():
        """Get pending queue items"""
        try:
            # Retrieve from database or session
            queue_items = []  # Get from your storage
            return jsonify({'queue': queue_items}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/queue/remove/<queue_id>', methods=['DELETE'])
    def remove_from_queue(queue_id):
        """Remove item from queue"""
        try:
            # Remove from database or session
            return jsonify({'success': True}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return app

# Usage: app = add_offline_queue_routes(app)


# ==================== COMPLETE INTEGRATION ====================
# Add this to the bottom of tts_app19.py, before if __name__ == '__main__':

def setup_pwa(app):
    """Complete PWA setup - call this function with your Flask app"""

    # Enable CORS
    app = setup_cors(app)

    # Add PWA routes
    app = add_pwa_routes(app)

    # Add security headers
    app = add_pwa_headers(app)

    # Add offline queue routes
    app = add_offline_queue_routes(app)

    # Force HTTPS in production (uncomment when deploying)
    # if not app.debug:
    #     app = force_https(app)

    print("[PWA] Progressive Web App support enabled")

    return app

# Usage in tts_app19.py:
# app = setup_pwa(app)


# ==================== STATIC FILE COPYING ====================
# Run this script to copy PWA files to Flask static directory

if __name__ == '__main__':
    import shutil

    print("Setting up PWA files...")

    # Paths
    pwa_dir = '../pwa'
    static_dir = '../../static'

    # Create directories
    os.makedirs(f'{static_dir}/css', exist_ok=True)
    os.makedirs(f'{static_dir}/js', exist_ok=True)
    os.makedirs(f'{static_dir}/icons', exist_ok=True)

    # Copy files
    try:
        # Copy manifest (serve from root via route)
        print("✓ Manifest will be served via /manifest.json route")

        # Copy service worker (serve from root via route)
        print("✓ Service Worker will be served via /service-worker.js route")

        # Copy mobile styles
        shutil.copy(f'{pwa_dir}/mobile-styles.css', f'{static_dir}/css/mobile-styles.css')
        print("✓ Copied mobile-styles.css")

        # Copy install prompt
        shutil.copy(f'{pwa_dir}/install-prompt.js', f'{static_dir}/js/install-prompt.js')
        print("✓ Copied install-prompt.js")

        print("\nPWA files setup complete!")
        print("\nNext steps:")
        print("1. Add PWA setup to tts_app19.py:")
        print("   from mobile-app.backend-modifications.flask_pwa_setup import setup_pwa")
        print("   app = setup_pwa(app)")
        print("\n2. Update your HTML template to include PWA meta tags")
        print("\n3. Generate app icons (see icon-generator.py)")
        print("\n4. Test on mobile device")

    except Exception as e:
        print(f"Error: {e}")
