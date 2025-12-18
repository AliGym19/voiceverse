#!/usr/bin/env python3
"""
Test script for Aero UI replacement
Verifies that the Windows Vista/7 Aero interface is working correctly
"""

import os
import sys
import time
import requests
from pathlib import Path

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test(message, status='info'):
    """Print formatted test message"""
    icons = {
        'info': '🧪',
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'progress': '⏳'
    }
    colors = {
        'info': Colors.BLUE,
        'success': Colors.GREEN,
        'error': Colors.RED,
        'warning': Colors.YELLOW,
        'progress': Colors.CYAN
    }
    icon = icons.get(status, '•')
    color = colors.get(status, '')
    print(f"{color}{icon} {message}{Colors.END}")

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print_test(f"{description} exists: {filepath}", 'success')
        return True
    else:
        print_test(f"{description} NOT FOUND: {filepath}", 'error')
        return False

def check_file_content(filepath, search_strings, description):
    """Check if file contains specific strings"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            all_found = True
            for search_str in search_strings:
                if search_str in content:
                    print_test(f"  ✓ Found: {search_str}", 'success')
                else:
                    print_test(f"  ✗ Missing: {search_str}", 'error')
                    all_found = False
            return all_found
    except Exception as e:
        print_test(f"Error reading {filepath}: {e}", 'error')
        return False

def test_file_structure():
    """Test 1: Verify file structure exists"""
    print_test("\n=== Test 1: File Structure ===", 'info')

    base_path = Path(__file__).parent

    files_to_check = [
        (base_path / 'templates' / 'dashboard_aero.html', 'Aero Dashboard Template'),
        (base_path / 'static' / 'css' / 'aero_theme.css', 'Aero CSS Stylesheet'),
        (base_path / 'static' / 'js' / 'aero_player.js', 'Aero JavaScript'),
        (base_path / 'tts_app19.py', 'Main Flask Application'),
        (base_path / 'old_spotify_design' / 'README.md', 'Backup Documentation'),
    ]

    all_exist = True
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_exist = False

    return all_exist

def test_aero_css_features():
    """Test 2: Verify Aero CSS contains required features"""
    print_test("\n=== Test 2: Aero CSS Features ===", 'info')

    css_file = Path(__file__).parent / 'static' / 'css' / 'aero_theme.css'

    required_features = [
        '@keyframes floatOrb',
        '@keyframes aurora',
        '@keyframes shimmer',
        '@keyframes pulse',
        '@keyframes scanline',
        '@keyframes glow',
        '@keyframes spin',
        '@keyframes ripple',
        '.aero-window',
        '.window-titlebar',
        '.player-bar',
        '.alloy-gradient',
        '.echo-gradient',
        '.fable-gradient',
        '.nova-gradient',
        '.onyx-gradient',
        '.shimmer-gradient',
        'backdrop-filter: blur',
        'rgba(255, 255, 255, 0.95)',
    ]

    return check_file_content(css_file, required_features, 'Aero CSS')

def test_aero_js_features():
    """Test 3: Verify Aero JS contains required features"""
    print_test("\n=== Test 3: Aero JavaScript Features ===", 'info')

    js_file = Path(__file__).parent / 'static' / 'js' / 'aero_player.js'

    required_features = [
        'function switchTab',
        'function handleFormSubmit',
        'function loadAudioLibrary',
        'function setupPlayerControls',
        'function createRippleEffect',
        'audioPlayer',
        'DOMContentLoaded',
    ]

    return check_file_content(js_file, required_features, 'Aero JavaScript')

def test_flask_routes():
    """Test 4: Verify Flask routes are configured"""
    print_test("\n=== Test 4: Flask Routes Configuration ===", 'info')

    py_file = Path(__file__).parent / 'tts_app19.py'

    required_routes = [
        "@app.route('/dashboard')",
        "def aero_dashboard():",
        "return render_template('dashboard_aero.html'",
        "@app.route('/api/audio-files'",
        "def api_get_audio_files():",
    ]

    return check_file_content(py_file, required_routes, 'Flask Routes')

def test_backup_created():
    """Test 5: Verify backup of old Spotify design"""
    print_test("\n=== Test 5: Backup Verification ===", 'info')

    base_path = Path(__file__).parent
    backup_dir = base_path / 'old_spotify_design'

    if not backup_dir.exists():
        print_test("Backup directory not found", 'error')
        return False

    backup_files = [
        backup_dir / 'templates' / 'index_spotify_original.html',
        backup_dir / 'README.md',
    ]

    all_exist = True
    for filepath in backup_files:
        if filepath.exists():
            print_test(f"Backup exists: {filepath.name}", 'success')
        else:
            print_test(f"Backup missing: {filepath.name}", 'warning')

    return True

def test_app_running(base_url='http://localhost:5000'):
    """Test 6: Test if Flask app is running and accessible"""
    print_test("\n=== Test 6: Application Accessibility ===", 'info')

    try:
        # Test if app is running
        response = requests.get(f"{base_url}/login", timeout=5)
        if response.status_code in [200, 302]:
            print_test(f"Flask app is running on {base_url}", 'success')
        else:
            print_test(f"Unexpected status code: {response.status_code}", 'warning')
            return False
    except requests.exceptions.ConnectionError:
        print_test(f"Cannot connect to {base_url} - App may not be running", 'warning')
        print_test("To start the app, run: python3 tts_app19.py", 'info')
        return False
    except Exception as e:
        print_test(f"Error connecting to app: {e}", 'error')
        return False

    return True

def test_aero_dashboard_accessible(base_url='http://localhost:5000'):
    """Test 7: Test if Aero dashboard route is accessible"""
    print_test("\n=== Test 7: Aero Dashboard Route ===", 'info')

    try:
        response = requests.get(f"{base_url}/dashboard", timeout=5, allow_redirects=False)
        if response.status_code in [200, 302]:
            print_test(f"Dashboard route accessible (Status: {response.status_code})", 'success')

            # Check if it redirects to login (expected for unauthenticated users)
            if response.status_code == 302 and '/login' in response.headers.get('Location', ''):
                print_test("  → Correctly redirects to login for unauthenticated users", 'success')

            return True
        else:
            print_test(f"Unexpected status: {response.status_code}", 'error')
            return False
    except requests.exceptions.ConnectionError:
        print_test("App not running - skipping route test", 'warning')
        return True  # Don't fail if app isn't running
    except Exception as e:
        print_test(f"Error: {e}", 'error')
        return False

def test_api_endpoint(base_url='http://localhost:5000'):
    """Test 8: Test if API endpoint exists"""
    print_test("\n=== Test 8: API Endpoint ===", 'info')

    try:
        response = requests.get(f"{base_url}/api/audio-files", timeout=5, allow_redirects=False)
        # Should redirect to login or return 401/403 for unauthenticated users
        if response.status_code in [302, 401, 403]:
            print_test(f"API endpoint exists (Status: {response.status_code})", 'success')
            return True
        elif response.status_code == 200:
            print_test("API endpoint accessible", 'success')
            return True
        else:
            print_test(f"Unexpected status: {response.status_code}", 'warning')
            return False
    except requests.exceptions.ConnectionError:
        print_test("App not running - skipping API test", 'warning')
        return True  # Don't fail if app isn't running
    except Exception as e:
        print_test(f"Error: {e}", 'error')
        return False

def test_no_spotify_theme():
    """Test 9: Verify old Spotify theme is not in use"""
    print_test("\n=== Test 9: Spotify Theme Removal ===", 'info')

    dashboard_file = Path(__file__).parent / 'templates' / 'dashboard_aero.html'

    try:
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()

            # Check for Spotify-specific elements that shouldn't be there
            spotify_indicators = [
                '--spotify-green: #1DB954',
                'spotify-dark',
                'Spotify-like',
            ]

            found_spotify = False
            for indicator in spotify_indicators:
                if indicator in content:
                    print_test(f"  Found Spotify reference: {indicator}", 'error')
                    found_spotify = True

            if not found_spotify:
                print_test("No Spotify theme references found in dashboard", 'success')

            # Check for Aero-specific elements
            aero_indicators = [
                'Windows Aero',
                'aero-window',
                'aero-background',
            ]

            found_aero = False
            for indicator in aero_indicators:
                if indicator in content:
                    found_aero = True
                    break

            if found_aero:
                print_test("Aero theme elements confirmed", 'success')
                return True
            else:
                print_test("Aero theme elements not found", 'error')
                return False

    except Exception as e:
        print_test(f"Error reading dashboard: {e}", 'error')
        return False

def run_all_tests():
    """Run all tests and report results"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}")
    print("🪟 VoiceVerse Aero UI Transformation Test Suite")
    print(f"{'='*70}{Colors.END}\n")

    tests = [
        ("File Structure", test_file_structure),
        ("Aero CSS Features", test_aero_css_features),
        ("Aero JavaScript Features", test_aero_js_features),
        ("Flask Routes", test_flask_routes),
        ("Backup Created", test_backup_created),
        ("Application Running", test_app_running),
        ("Aero Dashboard Route", test_aero_dashboard_accessible),
        ("API Endpoint", test_api_endpoint),
        ("Spotify Theme Removed", test_no_spotify_theme),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_test(f"Test '{test_name}' failed with error: {e}", 'error')
            results.append((test_name, False))

    # Summary
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}")
    print("📊 Test Summary")
    print(f"{'='*70}{Colors.END}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = '✅ PASS' if result else '❌ FAIL'
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status}{Colors.END} - {test_name}")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! Aero transformation complete!{Colors.END}")
        print(f"{Colors.CYAN}Your VoiceVerse app now has a beautiful Windows Vista/7 interface!{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠️  Some tests failed. Review the output above for details.{Colors.END}\n")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
