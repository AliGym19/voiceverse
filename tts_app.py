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
from datetime import datetime
import json
from collections import defaultdict
from werkzeug.utils import secure_filename
import html
import secrets

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'saved_audio'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))

openai_client = None
VALID_VOICES = {'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

METADATA_FILE = os.path.join(app.config['UPLOAD_FOLDER'], 'metadata.json')
USAGE_FILE = os.path.join(app.config['UPLOAD_FOLDER'], 'usage_stats.json')
HISTORY_FILE = os.path.join(app.config['UPLOAD_FOLDER'], 'playback_history.json')

def get_openai_client():
    global openai_client
    if openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        openai_client = OpenAI(api_key=api_key)
    return openai_client

def load_metadata():
    try:
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading metadata: {e}")
    return {}

def save_metadata(metadata):
    try:
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving metadata: {e}")

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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>VoiceVerse - AI Text-to-Speech</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --spotify-green: #1DB954;
            --spotify-dark: #121212;
            --spotify-darker: #000000;
            --spotify-gray: #181818;
            --spotify-light-gray: #282828;
            --spotify-text: #FFFFFF;
            --spotify-text-gray: #B3B3B3;
            --spotify-hover: #1ed760;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--spotify-darker);
            color: var(--spotify-text);
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .main-container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        .sidebar {
            width: 280px;
            background-color: var(--spotify-darker);
            padding: 24px 16px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .logo {
            font-size: 28px;
            font-weight: 700;
            color: var(--spotify-text);
            margin-bottom: 20px;
        }

        .nav-item {
            padding: 12px 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            color: var(--spotify-text-gray);
            font-weight: 600;
        }

        .nav-item:hover, .nav-item.active {
            color: var(--spotify-text);
            background-color: var(--spotify-light-gray);
        }

        .stats-card {
            background: linear-gradient(135deg, var(--spotify-gray), var(--spotify-light-gray));
            padding: 20px;
            border-radius: 8px;
            margin-top: auto;
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
            font-size: 13px;
        }

        .stat-label {
            color: var(--spotify-text-gray);
        }

        .stat-value {
            color: var(--spotify-green);
            font-weight: 700;
        }

        .main-content {
            flex: 1;
            background-color: var(--spotify-dark);
            overflow-y: auto;
            padding: 24px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
        }

        .header h1 {
            font-size: 32px;
            font-weight: 700;
        }

        .search-bar {
            background: var(--spotify-gray);
            border: none;
            padding: 12px 20px;
            border-radius: 500px;
            color: var(--spotify-text);
            width: 300px;
            font-size: 14px;
        }

        .btn-primary {
            background: var(--spotify-green);
            color: var(--spotify-text);
            border: none;
            padding: 12px 32px;
            border-radius: 500px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-primary:hover {
            background: var(--spotify-hover);
            transform: scale(1.04);
        }

        .btn-secondary {
            background: transparent;
            color: var(--spotify-text);
            border: 1px solid var(--spotify-text-gray);
            padding: 10px 28px;
            border-radius: 500px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-secondary:hover {
            border-color: var(--spotify-text);
            transform: scale(1.04);
        }

        .section-title {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 20px;
        }

        .files-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .file-card {
            background: var(--spotify-gray);
            padding: 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            position: relative;
        }

        .file-card:hover {
            background: var(--spotify-light-gray);
            transform: translateY(-4px);
        }

        .file-card-icon {
            width: 100%;
            aspect-ratio: 1;
            background: linear-gradient(135deg, var(--spotify-green), #1ed760);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 48px;
            margin-bottom: 12px;
            position: relative;
        }

        .play-button {
            position: absolute;
            bottom: 8px;
            right: 8px;
            width: 48px;
            height: 48px;
            background: var(--spotify-green);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: all 0.3s;
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
            font-size: 20px;
        }

        .file-card:hover .play-button {
            opacity: 1;
            transform: translateY(-4px);
        }

        .file-card-title {
            font-weight: 700;
            margin-bottom: 4px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .file-card-meta {
            font-size: 13px;
            color: var(--spotify-text-gray);
        }

        .file-card-options {
            position: absolute;
            top: 12px;
            right: 12px;
            width: 32px;
            height: 32px;
            background: rgba(0, 0, 0, 0.6);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            opacity: 0;
            transition: all 0.2s;
            z-index: 10;
            font-size: 20px;
        }

        .file-card:hover .file-card-options {
            opacity: 1;
        }

        .player-bar {
            height: 90px;
            background-color: var(--spotify-gray);
            border-top: 1px solid var(--spotify-darker);
            display: flex;
            align-items: center;
            padding: 0 16px;
            gap: 16px;
        }

        .now-playing {
            min-width: 300px;
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .now-playing-art {
            width: 56px;
            height: 56px;
            background: linear-gradient(135deg, var(--spotify-green), #1ed760);
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }

        .now-playing-info h4 {
            font-size: 14px;
            margin-bottom: 4px;
        }

        .now-playing-info p {
            font-size: 12px;
            color: var(--spotify-text-gray);
        }

        .player-controls {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }

        .control-buttons {
            display: flex;
            gap: 16px;
            align-items: center;
        }

        .control-btn {
            background: none;
            border: none;
            color: var(--spotify-text-gray);
            cursor: pointer;
            font-size: 20px;
            transition: all 0.2s;
        }

        .control-btn:hover {
            color: var(--spotify-text);
            transform: scale(1.1);
        }

        .control-btn.play {
            width: 36px;
            height: 36px;
            background: var(--spotify-text);
            color: var(--spotify-darker);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .progress-bar {
            width: 100%;
            max-width: 600px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            color: var(--spotify-text-gray);
        }

        .progress-track {
            flex: 1;
            height: 4px;
            background: var(--spotify-light-gray);
            border-radius: 2px;
            cursor: pointer;
            position: relative;
        }

        .progress-fill {
            height: 100%;
            background: var(--spotify-text);
            border-radius: 2px;
            width: 0%;
            transition: width 0.1s;
        }

        .volume-controls {
            min-width: 200px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .volume-slider {
            flex: 1;
            height: 4px;
            background: var(--spotify-light-gray);
            border-radius: 2px;
            cursor: pointer;
        }

        .volume-fill {
            height: 100%;
            background: var(--spotify-text);
            border-radius: 2px;
            width: 100%;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: var(--spotify-text-gray);
        }

        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 12px;
            background: var(--spotify-gray);
            border: 1px solid var(--spotify-light-gray);
            border-radius: 4px;
            color: var(--spotify-text);
            font-size: 14px;
        }

        .form-group textarea {
            resize: vertical;
            font-family: inherit;
        }

        .char-info {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: var(--spotify-text-gray);
            margin-top: 8px;
        }

        .cost-estimate {
            color: var(--spotify-green);
        }

        .voice-card {
            background: var(--spotify-gray);
            padding: 16px;
            border-radius: 8px;
            border: 2px solid var(--spotify-gray);
            transition: all 0.2s;
            cursor: pointer;
        }

        .voice-card:hover {
            border-color: var(--spotify-text-gray);
        }

        .voice-card.selected {
            border-color: var(--spotify-green);
            background: rgba(29, 185, 84, 0.1);
        }

        .voice-name {
            font-weight: 700;
            font-size: 16px;
            margin-bottom: 4px;
        }

        .voice-desc {
            color: var(--spotify-text-gray);
            font-size: 13px;
        }

        .success-message {
            background: var(--spotify-green);
            color: var(--spotify-darker);
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-weight: 600;
        }

        .error-message {
            background: #ff4444;
            color: white;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-weight: 600;
        }

        .context-menu {
            position: fixed;
            background: var(--spotify-light-gray);
            border-radius: 4px;
            padding: 4px 0;
            box-shadow: 0 16px 24px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            display: none;
            min-width: 160px;
        }

        .context-menu.active {
            display: block;
        }

        .context-item {
            padding: 12px 16px;
            cursor: pointer;
            transition: background 0.2s;
            font-size: 14px;
        }

        .context-item:hover {
            background: var(--spotify-gray);
        }

        .context-item.danger:hover {
            color: #ff4444;
        }

        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }

        .modal.active {
            display: flex;
        }

        .modal-content {
            background: var(--spotify-light-gray);
            padding: 32px;
            border-radius: 12px;
            max-width: 500px;
            width: 90%;
        }

        .modal-header {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 24px;
        }

        .modal-input {
            width: 100%;
            padding: 12px;
            background: var(--spotify-gray);
            border: 1px solid var(--spotify-text-gray);
            border-radius: 4px;
            color: var(--spotify-text);
            font-size: 16px;
            margin-bottom: 24px;
        }

        .modal-buttons {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
        }

        .no-results {
            text-align: center;
            color: var(--spotify-text-gray);
            padding: 40px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="sidebar">
            <div class="logo">🌌 VoiceVerse</div>
            
            <div class="nav-item active" onclick="showSection('home')">
                🏠 Home
            </div>
            <div class="nav-item" onclick="showSection('create')">
                ➕ Create New
            </div>
            
            <div class="stats-card">
                <div class="stat-row">
                    <span class="stat-label">Total Files</span>
                    <span class="stat-value">{{ usage.files_generated }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Characters</span>
                    <span class="stat-value">{{ "{:,}".format(usage.total_characters) }}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Total Cost</span>
                    <span class="stat-value">${{ "%.2f"|format(usage.total_cost) }}</span>
                </div>
            </div>
        </div>

        <div class="main-content">
            <!-- Home Section -->
            <div id="homeSection" class="content-section">
                <div class="header">
                    <h1>Your Audio Library</h1>
                    <div style="display: flex; gap: 12px;">
                        <input type="text" class="search-bar" placeholder="Search your files..." id="searchInput" onkeyup="filterFiles()">
                        <button class="btn-primary" onclick="showSection('create')">Create New</button>
                    </div>
                </div>

                {% if recent_files %}
                <div class="section-title">Recent Files</div>
                <div class="files-grid">
                    {% for file in recent_files[:12] %}
                    <div class="file-card" data-filename="{{ file.filename }}" data-name="{{ file.name }}">
                        <div class="file-card-options" onclick="event.stopPropagation(); showContextMenu(event, '{{ file.filename }}', '{{ file.name }}')">
                            ⋮
                        </div>
                        <div class="file-card-icon" onclick="playFile('{{ file.filename }}', '{{ file.name }}')">
                            🎵
                            <div class="play-button">▶</div>
                        </div>
                        <div class="file-card-title">{{ file.name }}</div>
                        <div class="file-card-meta">
                            {{ file.chars }} chars • ${{ "%.3f"|format(file.cost) }}
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="no-results">
                    No audio files yet. Click "Create New" to get started!
                </div>
                {% endif %}
            </div>

            <!-- Create Section -->
            <div id="createSection" class="content-section" style="display: none;">
                <div class="header">
                    <h1>Create New Audio</h1>
                </div>

                {% if error %}
                <div class="error-message">{{ error }}</div>
                {% endif %}

                {% if success %}
                <div class="success-message">✅ Audio generated successfully!</div>
                {% endif %}

                <form method="POST" action="/" style="max-width: 700px;">
                    <div class="form-group">
                        <label>File Name</label>
                        <input type="text" name="filename" placeholder="My Awesome Audio" required maxlength="100">
                    </div>

                    <div class="form-group">
                        <label>Group</label>
                        <input type="text" name="group" placeholder="Work, Personal, Projects..." value="Uncategorized" maxlength="50">
                    </div>

                    <div class="form-group">
                        <label>Voice</label>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
                            <div class="voice-card" onclick="selectVoice('alloy', this)">
                                <input type="radio" name="voice" value="alloy" style="display: none;">
                                <div class="voice-name">Alloy</div>
                                <div class="voice-desc">Neutral, balanced</div>
                            </div>
                            <div class="voice-card" onclick="selectVoice('echo', this)">
                                <input type="radio" name="voice" value="echo" style="display: none;">
                                <div class="voice-name">Echo</div>
                                <div class="voice-desc">Male, clear</div>
                            </div>
                            <div class="voice-card" onclick="selectVoice('fable', this)">
                                <input type="radio" name="voice" value="fable" style="display: none;">
                                <div class="voice-name">Fable</div>
                                <div class="voice-desc">British, expressive</div>
                            </div>
                            <div class="voice-card" onclick="selectVoice('onyx', this)">
                                <input type="radio" name="voice" value="onyx" style="display: none;">
                                <div class="voice-name">Onyx</div>
                                <div class="voice-desc">Deep, authoritative</div>
                            </div>
                            <div class="voice-card selected" onclick="selectVoice('nova', this)">
                                <input type="radio" name="voice" value="nova" checked style="display: none;">
                                <div class="voice-name">Nova</div>
                                <div class="voice-desc">Female, friendly</div>
                            </div>
                            <div class="voice-card" onclick="selectVoice('shimmer', this)">
                                <input type="radio" name="voice" value="shimmer" style="display: none;">
                                <div class="voice-name">Shimmer</div>
                                <div class="voice-desc">Soft, warm</div>
                            </div>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Text</label>
                        <textarea name="text" rows="10" placeholder="Enter your text here..." id="textInput" required maxlength="4096"></textarea>
                        <div class="char-info">
                            <span>Characters: <span id="charCount">0</span> / 4,096</span>
                            <span class="cost-estimate">Est. cost: $<span id="costCount">0.000</span></span>
                        </div>
                    </div>

                    <button type="submit" class="btn-primary" style="width: 100%;">Generate Audio</button>
                </form>
            </div>
        </div>
    </div>

    <!-- Player Bar -->
    <div class="player-bar">
        <div class="now-playing" id="nowPlaying" style="opacity: 0.5;">
            <div class="now-playing-art">🎵</div>
            <div class="now-playing-info">
                <h4 id="currentTrackName">No track playing</h4>
                <p id="currentTrackInfo">Select a file to play</p>
            </div>
        </div>

        <div class="player-controls">
            <div class="control-buttons">
                <button class="control-btn play" onclick="togglePlay()" id="playBtn">▶</button>
            </div>
            <div class="progress-bar">
                <span id="currentTime">0:00</span>
                <div class="progress-track" onclick="seekTo(event)">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <span id="totalTime">0:00</span>
            </div>
        </div>

        <div class="volume-controls">
            <span>🔊</span>
            <div class="volume-slider" onclick="setVolume(event)">
                <div class="volume-fill" id="volumeFill"></div>
            </div>
        </div>
    </div>

    <!-- Context Menu -->
    <div class="context-menu" id="contextMenu">
        <div class="context-item" onclick="contextPlay()">▶ Play</div>
        <div class="context-item" onclick="contextRename()">✏ Rename</div>
        <div class="context-item" onclick="contextDownload()">⬇ Download</div>
        <div class="context-item danger" onclick="contextDelete()">🗑 Delete</div>
    </div>

    <!-- Rename Modal -->
    <div class="modal" id="renameModal">
        <div class="modal-content">
            <div class="modal-header">Rename File</div>
            <input type="text" class="modal-input" id="renameInput" placeholder="New file name" maxlength="100">
            <div class="modal-buttons">
                <button class="btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn-primary" onclick="confirmRename()">Rename</button>
            </div>
        </div>
    </div>

    <audio id="audioPlayer" style="display: none;"></audio>

    <script>
        let currentFilename = null;
        let currentFileName = null;
        const audioPlayer = document.getElementById('audioPlayer');

        // Character counter
        const textInput = document.getElementById('textInput');
        if (textInput) {
            textInput.addEventListener('input', function() {
                const length = this.value.length;
                document.getElementById('charCount').textContent = length.toLocaleString();
                const cost = (length / 1000) * 0.015;
                document.getElementById('costCount').textContent = cost.toFixed(4);
            });
        }

        // Voice selection
        function selectVoice(voice, element) {
            document.querySelectorAll('.voice-card').forEach(card => card.classList.remove('selected'));
            element.classList.add('selected');
            element.querySelector('input[type="radio"]').checked = true;
        }

        // Navigation
        function showSection(section) {
            document.querySelectorAll('.content-section').forEach(s => s.style.display = 'none');
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

            const sections = {
                'home': 0,
                'create': 1
            };

            document.getElementById(section + 'Section').style.display = 'block';
            document.querySelectorAll('.nav-item')[sections[section]].classList.add('active');
        }

        // Context Menu
        function showContextMenu(event, filename, name) {
            event.preventDefault();
            event.stopPropagation();

            currentFilename = filename;
            currentFileName = name;

            const menu = document.getElementById('contextMenu');
            menu.style.left = event.pageX + 'px';
            menu.style.top = event.pageY + 'px';
            menu.classList.add('active');
        }

        document.addEventListener('click', () => {
            document.getElementById('contextMenu').classList.remove('active');
        });

        function contextPlay() {
            playFile(currentFilename, currentFileName);
        }

        function contextRename() {
            document.getElementById('renameInput').value = currentFileName;
            document.getElementById('renameModal').classList.add('active');
        }

        function contextDownload() {
            window.location.href = `/download/${encodeURIComponent(currentFilename)}`;
        }

        function contextDelete() {
            if (confirm(`Delete "${currentFileName}"?`)) {
                fetch(`/delete/${encodeURIComponent(currentFilename)}`, {method: 'POST'})
                    .then(response => {
                        if (response.ok) window.location.reload();
                        else alert('Failed to delete file');
                    })
                    .catch(err => alert('Error: ' + err));
            }
        }

        function closeModal() {
            document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
        }

        function confirmRename() {
            const newName = document.getElementById('renameInput').value.trim();
            if (newName && newName !== currentFileName) {
                fetch(`/rename/${encodeURIComponent(currentFilename)}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: newName})
                }).then(response => {
                    if (response.ok) window.location.reload();
                    else alert('Failed to rename file');
                }).catch(err => alert('Error: ' + err));
            }
            closeModal();
        }

        // Player functions
        function playFile(filename, displayName) {
            if (!filename) return;

            audioPlayer.src = `/audio/${encodeURIComponent(filename)}`;
            audioPlayer.play().catch(e => {
                console.error('Playback error:', e);
                alert('Failed to play audio');
            });

            document.getElementById('nowPlaying').style.opacity = '1';
            document.getElementById('currentTrackName').textContent = displayName || filename;
            document.getElementById('currentTrackInfo').textContent = 'Playing...';
            document.getElementById('playBtn').textContent = '⏸';
        }

        function togglePlay() {
            if (!audioPlayer.src) return;
            
            if (audioPlayer.paused) {
                audioPlayer.play().catch(e => console.error('Play error:', e));
                document.getElementById('playBtn').textContent = '⏸';
            } else {
                audioPlayer.pause();
                document.getElementById('playBtn').textContent = '▶';
            }
        }

        // Progress bar
        audioPlayer.addEventListener('timeupdate', () => {
            if (!isNaN(audioPlayer.duration)) {
                const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
                document.getElementById('progressFill').style.width = progress + '%';
                document.getElementById('currentTime').textContent = formatTime(audioPlayer.currentTime);
                document.getElementById('totalTime').textContent = formatTime(audioPlayer.duration);
            }
        });

        function formatTime(seconds) {
            if (isNaN(seconds) || !isFinite(seconds)) return '0:00';
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }

        function seekTo(event) {
            if (!audioPlayer.duration) return;
            const rect = event.currentTarget.getBoundingClientRect();
            const percent = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
            audioPlayer.currentTime = audioPlayer.duration * percent;
        }

        function setVolume(event) {
            const rect = event.currentTarget.getBoundingClientRect();
            const percent = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
            audioPlayer.volume = percent;
            document.getElementById('volumeFill').style.width = (percent * 100) + '%';
        }

        // Search
        function filterFiles() {
            const term = document.getElementById('searchInput').value.toLowerCase().trim();
            let found = false;

            document.querySelectorAll('.file-card').forEach(card => {
                const name = (card.dataset.name || '').toLowerCase();
                const filename = (card.dataset.filename || '').toLowerCase();

                if (name.includes(term) || filename.includes(term)) {
                    card.style.display = '';
                    found = true;
                } else {
                    card.style.display = 'none';
                }
            });
        }

        // Initialize
        audioPlayer.volume = 1.0;
        document.getElementById('volumeFill').style.width = '100%';

        {% if success and filename %}
        setTimeout(() => {
            playFile('{{ filename }}', '{{ file_display_name }}');
        }, 500);
        {% endif %}
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    success = False
    filename = None
    file_display_name = None

    if request.method == 'POST':
        text = request.form.get('text', '').strip()
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

                with open(filepath, 'wb') as f:
                    f.write(response.content)

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
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], fname))
    ]

    all_files.sort(key=lambda x: x['created'], reverse=True)
    recent_files = all_files[:12]

    return render_template_string(
        HTML_TEMPLATE,
        error=error,
        success=success,
        filename=filename,
        file_display_name=file_display_name,
        recent_files=recent_files,
        usage=usage
    )

@app.route('/audio/<path:filename>')
def audio(filename):
    try:
        safe_filename = secure_filename(filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='audio/mpeg')
        return "File not found", 404
    except Exception as e:
        print(f"Error serving audio: {e}")
        return "Error serving file", 500

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
        data = request.get_json()
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

if __name__ == '__main__':
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY environment variable is not set!")
        print("Please set it using: export OPENAI_API_KEY='your-api-key-here'")
        print("")
    
    print("🌌 Starting VoiceVerse - Text-to-Speech Application")
    print("📍 Open in your browser: http://localhost:5000")
    print("Press Ctrl+C to stop the server\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
