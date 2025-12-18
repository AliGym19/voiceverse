# -*- coding: utf-8 -*-
"""
VoiceVerse - AI Text-to-Speech Application
Clean, fully functional version
"""

from flask import Flask, render_template_string, request, send_file, redirect, url_for, jsonify
import os
import re
from openai import OpenAI
import io
import sys
from datetime import datetime
import json
from collections import defaultdict
from werkzeug.utils import secure_filename
import html
import secrets

# Ensure UTF-8 output for Flask
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['UPLOAD_FOLDER'] = 'saved_audio'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))

VALID_VOICES = {'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

METADATA_FILE = os.path.join(app.config['UPLOAD_FOLDER'], 'metadata.json')
USAGE_FILE = os.path.join(app.config['UPLOAD_FOLDER'], 'usage_stats.json')
HISTORY_FILE = os.path.join(app.config['UPLOAD_FOLDER'], 'playback_history.json')

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)

def load_metadata():
    try:
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading metadata: {e}")
    return {}

def save_metadata(metadata):
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)


def load_usage():
    try:
        if os.path.exists(USAGE_FILE):
            with open(USAGE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'total_characters' not in data:
                    data['total_characters'] = 0
                if 'total_cost' not in data:
                    data['total_cost'] = 0
                if 'files_generated' not in data:
                    data['files_generated'] = 0
                if 'monthly' not in data:
                    data['monthly'] = {}
                return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading usage: {e}")
    return {'total_characters': 0, 'total_cost': 0, 'files_generated': 0, 'monthly': {}}

def save_usage(usage):
    try:
        with open(USAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(usage, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving usage: {e}")
    try:
        with open(USAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(usage, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving usage: {e}")

def calculate_cost(characters):
    return (characters / 1000) * 0.015

def sanitize_display_name(name):
    name = re.sub(r'[<>:"|?*\x00-\x1f]', '', name)
    name = name.strip()[:100]
    return name or 'audio'

def validate_voice(voice):
    return voice if voice in VALID_VOICES else 'nova'

def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading history: {e}")
    return []

def save_history(history):
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving history: {e}")

def add_to_history(filename, display_name):
    history = load_history()
    entry = {
        'filename': filename,
        'name': display_name,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'datetime_sort': datetime.now().strftime("%Y%m%d%H%M%S")
    }
    history.insert(0, entry)
    history = history[:50]
    save_history(history)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    success = False
    filename = None
    file_display_name = None

    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        # normalize text as UTF-8 safely
        text = text.encode('utf-8', 'ignore').decode('utf-8').strip()
        voice = validate_voice(request.form.get('voice', 'nova'))
        file_name = sanitize_display_name(request.form.get('filename', 'audio'))
        group = sanitize_display_name(request.form.get('group', 'Uncategorized'))[:50]

        if not text:
            error = "Please enter some text"
        elif len(text) > 4096:
            error = f"Text exceeds 4,096 character limit (current: {len(text)} characters)"
        elif not file_name:
            error = "Please enter a valid file name"
        else:
            try:
                client = get_openai_client()

                response = client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=text,
                    speed=1.0
                )

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = secure_filename(f"{file_name}_{timestamp}.mp3")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)

                try:
                    if hasattr(response, 'stream_to_file'):
                        response.stream_to_file(filepath)
                        print(f'✅ Saved using stream_to_file at: {filepath}')
                    else:
                        audio_bytes = getattr(response, 'content', None)
                        if audio_bytes is None and hasattr(response, 'read'):
                            audio_bytes = response.read()
                        if audio_bytes:
                            with open(filepath, 'wb') as f:
                                f.write(audio_bytes)
                            print(f'✅ Saved audio file at: {filepath}')
                        else:
                            raise RuntimeError('No audio bytes found in OpenAI response.')
                except Exception as e:
                    error = f'Error saving file: {e}'
                    print(error)

                if not error:
                    char_count = len(text)
                    cost = calculate_cost(char_count)

                    metadata = load_metadata()
                    metadata[safe_filename] = {
                        'name': file_name,
                        'group': group,
                        'created': timestamp,
                        'voice': voice,
                        'characters': char_count,
                        'cost': cost
                    }
                    save_metadata(metadata)

                    usage = load_usage()
                    usage['total_characters'] += char_count
                    usage['total_cost'] += cost
                    usage['files_generated'] += 1

                    current_month = datetime.now().strftime("%Y-%m")
                    if current_month not in usage['monthly']:
                        usage['monthly'][current_month] = {'cost': 0, 'files': 0, 'characters': 0}
                    usage['monthly'][current_month]['cost'] += cost
                    usage['monthly'][current_month]['files'] += 1
                    usage['monthly'][current_month]['characters'] += char_count

                    save_usage(usage)
                    success = True
                    filename = safe_filename
                    file_display_name = file_name

            except ValueError as ve:
                error = str(ve)
            except Exception as e:
                error = f"An error occurred: {str(e)}"
                print(f"Error in audio generation: {e}")

    metadata = load_metadata()
    usage = load_usage()

    # Avoid repeatedly hitting the filesystem for each metadata entry
    existing_files = set(os.listdir(app.config['UPLOAD_FOLDER']))
    all_files = [
        {
            'filename': fname,
            'name': data.get('name', fname),
            'group': data.get('group', 'Uncategorized'),
            'created': data.get('created', ''),
            'chars': data.get('characters', 0),
            'cost': data.get('cost', 0)
        }
        for fname, data in metadata.items()
        if fname in existing_files
    ]

    all_files.sort(key=lambda x: x['created'], reverse=True)
    recent_files = all_files[:12]

    return render_template(
        "index.html",
        error=error,
        success=success,
        filename=filename,
        file_display_name=file_display_name,
        recent_files=recent_files,
        usage=usage
    )

@app.route('/download/<path:filename>')
def download(filename):
    try:
        safe_filename = secure_filename(filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='audio/mpeg', as_attachment=True, download_name=safe_filename)
        return "File not found", 404
    except Exception as e:
        print(f"Error downloading: {e}")
        return "Error downloading file", 500

@app.route('/rename/<path:filename>', methods=['POST'])
def rename(filename):
    try:
        data = request.get_json() or {}
        new_name = sanitize_display_name(data.get('name', ''))

        if new_name:
            safe_filename = secure_filename(filename)
            metadata = load_metadata()

            if safe_filename in metadata:
                metadata[safe_filename]['name'] = new_name
                save_metadata(metadata)
                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'File not found'}), 404
        return jsonify({'success': False, 'error': 'Invalid name'}), 400

    except Exception as e:
        print(f"Error renaming: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete/<path:filename>', methods=['POST'])
def delete(filename):
    try:
        safe_filename = secure_filename(filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)

        metadata = load_metadata()
        if safe_filename in metadata:
            file_info = metadata[safe_filename]
            usage = load_usage()

            usage['total_characters'] = max(0, usage.get('total_characters', 0) - file_info.get('characters', 0))
            usage['total_cost'] = max(0, usage.get('total_cost', 0) - file_info.get('cost', 0))
            usage['files_generated'] = max(0, usage.get('files_generated', 1) - 1)

            save_usage(usage)
            del metadata[safe_filename]
            save_metadata(metadata)

        if os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error deleting: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/preview/<voice>')
def preview(voice):
    try:
        voice = validate_voice(voice)
        preview_text = f"Hello, I am {voice.capitalize()}. This is how I sound."

        client = get_openai_client()
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=preview_text,
            speed=1.0
        )

        audio_buffer = io.BytesIO(getattr(response, 'content', b''))
        audio_buffer.seek(0)

        return send_file(audio_buffer, mimetype='audio/mpeg')

    except Exception as e:
        print(f"Error generating preview: {e}")
        return f"Error: {str(e)}", 500

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY environment variable is not set!")
        print("Please set it using: export OPENAI_API_KEY='your-api-key-here'")
        print("")
    
    print("🌌 Starting VoiceVerse - Text-to-Speech Application")
    print("📍 Open in your browser: http://localhost:5000")
    print("Press Ctrl+C to stop the server\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
