#!/usr/bin/env python3
"""
Extract embedded HTML templates from tts_app19.py and save them as separate files.
This is a one-time migration script.
"""

import re
import os

def extract_templates():
    with open('tts_app19.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract SETTINGS_TEMPLATE
    settings_match = re.search(r'SETTINGS_TEMPLATE\s*=\s*"""(.*?)"""', content, re.DOTALL)
    if settings_match:
        settings_html = settings_match.group(1).strip()
        os.makedirs('templates', exist_ok=True)
        with open('templates/settings_new.html', 'w', encoding='utf-8') as f:
            f.write(settings_html)
        print(f"✅ Extracted SETTINGS_TEMPLATE ({len(settings_html)} chars) -> templates/settings_new.html")
    else:
        print("❌ Could not find SETTINGS_TEMPLATE")

    # Extract HTML_TEMPLATE
    html_match = re.search(r'HTML_TEMPLATE\s*=\s*"""(.*?)"""', content, re.DOTALL)
    if html_match:
        html_content = html_match.group(1).strip()
        with open('templates/index_new.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Extracted HTML_TEMPLATE ({len(html_content)} chars) -> templates/index_new.html")
    else:
        print("❌ Could not find HTML_TEMPLATE")

    # Extract AUTH_TEMPLATE as well
    auth_match = re.search(r'AUTH_TEMPLATE\s*=\s*"""(.*?)"""', content, re.DOTALL)
    if auth_match:
        auth_html = auth_match.group(1).strip()
        with open('templates/auth_new.html', 'w', encoding='utf-8') as f:
            f.write(auth_html)
        print(f"✅ Extracted AUTH_TEMPLATE ({len(auth_html)} chars) -> templates/auth_new.html")
    else:
        print("❌ Could not find AUTH_TEMPLATE")

    print("\n📁 Templates extracted to templates/ directory")
    print("⚠️  Review the extracted files and rename them:")
    print("    templates/settings_new.html -> templates/settings.html")
    print("    templates/index_new.html -> templates/index.html")
    print("    templates/auth_new.html -> templates/auth.html")

if __name__ == '__main__':
    extract_templates()
