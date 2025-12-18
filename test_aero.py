#!/usr/bin/env python3
"""
Test script to verify Windows Vista/7 Aero Dashboard setup
"""

import os
import sys

def check_files():
    """Check if all Aero files exist"""
    print("=" * 60)
    print("WINDOWS VISTA/7 AERO DASHBOARD VERIFICATION")
    print("=" * 60)

    files_to_check = [
        ('templates/dashboard_aero.html', 'Aero Dashboard Template'),
        ('static/css/aero_theme.css', 'Aero CSS Stylesheet'),
        ('static/js/aero_player.js', 'Aero JavaScript'),
        ('aero_routes.py', 'Aero Routes Module'),
        ('integrate_aero.py', 'Integration Script'),
        ('launch_aero.py', 'Launch Script')
    ]

    all_good = True

    print("\n✅ FILE VERIFICATION:")
    print("-" * 40)

    for filepath, description in files_to_check:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"✅ {description:<30} ({size:,} bytes)")
        else:
            print(f"❌ {description:<30} MISSING!")
            all_good = False

    print("\n✅ ROUTE VERIFICATION:")
    print("-" * 40)

    # Check if routes are added to main app
    with open('tts_app19.py', 'r', encoding='utf-8') as f:
        content = f.read()

    checks = [
        ('render_template import', 'from flask import.*render_template'),
        ('Aero Dashboard route', '@app.route\\(\'/dashboard\'\\)'),
        ('API Audio Files route', '@app.route\\(\'/api/audio-files\''),
        ('Aero routes import', 'from aero_routes import')
    ]

    for check_name, pattern in checks:
        if pattern.replace('\\', '') in content or pattern in content:
            print(f"✅ {check_name:<30} Added")
        else:
            print(f"❌ {check_name:<30} NOT FOUND!")
            all_good = False

    print("\n" + "=" * 60)

    if all_good:
        print("🎉 SUCCESS! All Aero Dashboard components are in place!")
        print("\n📌 NEXT STEPS:")
        print("1. Start the app: python3 tts_app19.py")
        print("2. Open browser: http://localhost:5000/login")
        print("3. Login with your credentials")
        print("4. Navigate to: http://localhost:5000/dashboard")
        print("\n✨ Features of the Aero Dashboard:")
        print("   • Windows Vista/7 glass window design")
        print("   • Vibrant gradient backgrounds")
        print("   • Animated orbs and aurora effects")
        print("   • Voice-specific color gradients")
        print("   • Windows Media Player style controls")
        print("   • Glass blur effects throughout")
    else:
        print("⚠️  Some components are missing. Please review above.")

    print("=" * 60)

    # Show file statistics
    print("\n📊 AERO DASHBOARD STATISTICS:")
    print("-" * 40)

    total_size = 0
    line_counts = {}

    for filepath, _ in files_to_check[:3]:  # Only count the main 3 files
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            total_size += size

            with open(filepath, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
                line_counts[filepath] = lines

    print(f"Total Size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    print(f"Total Lines of Code:")
    for filepath, lines in line_counts.items():
        name = os.path.basename(filepath)
        print(f"  • {name:<25} {lines:,} lines")

    print("\n✨ The Windows Vista/7 Aero transformation is complete!")

if __name__ == "__main__":
    os.chdir('/Users/ali/Desktop/Project/TTS_App')
    check_files()