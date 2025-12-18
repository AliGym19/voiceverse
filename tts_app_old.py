# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, send_file, redirect, url_for, jsonify, Response, stream_with_context
import os
import re
from openai import OpenAI
import io
from datetime import datetime
import json
from collections import defaultdict
from werkzeug.utils import secure_filename
import html
from functools import lru_cache
import secrets
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'saved_audio'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Initialize OpenAI client once
openai_client = None
VALID_VOICES = {'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'}

# Create necessary directories
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

METADATA_FILE = os.path.join(app.config['UPLOAD_FOLDER'], 'metadata.json')
USAGE_FILE = os.path.join(app.config['UPLOAD_FOLDER'], 'usage_stats.json')
HISTORY_FILE = os.path.join(app.config['UPLOAD_FOLDER'], 'playback_history.json')

def get_openai_client():
    """Lazy initialize OpenAI client"""
    global openai_client
    if openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        openai_client = OpenAI(api_key=api_key)
    return openai_client

def load_metadata():
    """Load metadata with error handling"""
    try:
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading metadata: {e}")
    return {}

def save_metadata(metadata):
    """Save metadata with error handling"""
    try:
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving metadata: {e}")

def load_usage():
    """Load usage stats with error handling"""
    try:
        if os.path.exists(USAGE_FILE):
            with open(USAGE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure all required fields exist
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
    """Save usage stats with error handling"""
    try:
        with open(USAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(usage, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving usage: {e}")

def calculate_cost(characters):
    """Calculate cost based on character count"""
    return (characters / 1000) * 0.015

def sanitize_display_name(name):
    """Sanitize user-provided display name"""
    # Remove dangerous characters but allow more than filename
    name = re.sub(r'[<>:"|?*\x00-\x1f]', '', name)
    # Limit length
    name = name.strip()[:100]
    return name or 'audio'

def validate_voice(voice):
    """Validate voice parameter"""
    return voice if voice in VALID_VOICES else 'nova'

def load_history():
    """Load playback history"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading history: {e}")
    return []

def save_history(history):
    """Save playback history"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving history: {e}")

def add_to_history(filename, display_name):
    """Add file play to history"""
    history = load_history()
    entry = {
        'filename': filename,
        'name': display_name,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'datetime_sort': datetime.now().strftime("%Y%m%d%H%M%S")
    }
    history.insert(0, entry)  # Add to beginning
    # Keep only last 50 plays
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
            font-family: 'Circular', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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

        /* Sidebar */
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
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .nav-item {
            padding: 12px 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            color: var(--spotify-text-gray);
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 16px;
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

        /* Main Content */
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

        .header-controls {
            display: flex;
            gap: 12px;
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

        /* Files Grid */
        .section-title {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .sort-select {
            background: var(--spotify-gray);
            color: var(--spotify-text);
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 14px;
            cursor: pointer;
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
            color: white;
        }

        .file-card:hover .file-card-options {
            opacity: 1;
        }

        .file-card-options:hover {
            background: rgba(0, 0, 0, 0.8);
            transform: scale(1.1);
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
        }

        .file-card:hover .play-button {
            opacity: 1;
            transform: translateY(-4px);
        }

        .play-button:hover {
            background: var(--spotify-hover);
            transform: translateY(-4px) scale(1.06);
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
            display: flex;
            justify-content: space-between;
        }

        /* Chart */
        .chart-container {
            background: var(--spotify-gray);
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 40px;
        }

        .chart-title {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 20px;
        }

        .chart-bars {
            display: flex;
            align-items: flex-end;
            gap: 12px;
            height: 200px;
        }

        .chart-bar {
            flex: 1;
            background: var(--spotify-green);
            border-radius: 4px 4px 0 0;
            position: relative;
            transition: all 0.3s;
            min-height: 20px;
        }

        .chart-bar:hover {
            background: var(--spotify-hover);
            transform: scaleY(1.05);
        }

        .chart-bar-label {
            position: absolute;
            bottom: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 11px;
            color: var(--spotify-text-gray);
            white-space: nowrap;
        }

        .chart-bar-value {
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 12px;
            font-weight: 700;
            color: var(--spotify-text);
        }

        /* Bottom Player Bar */
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

        .control-btn.play:hover {
            transform: scale(1.06);
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

        .progress-track:hover .progress-fill {
            background: var(--spotify-green);
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

        /* Modal */
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

        .queue-section {
            background: var(--spotify-gray);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 32px;
        }

        .queue-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .queue-item {
            display: flex;
            align-items: center;
            padding: 8px;
            border-radius: 4px;
            margin-bottom: 4px;
            transition: background 0.2s;
        }

        .queue-item:hover {
            background: var(--spotify-light-gray);
        }

        .queue-number {
            width: 30px;
            text-align: center;
            color: var(--spotify-text-gray);
            font-size: 14px;
        }

        .queue-info {
            flex: 1;
            margin-left: 12px;
        }

        .queue-title {
            font-weight: 600;
            font-size: 14px;
        }

        .queue-meta {
            font-size: 12px;
            color: var(--spotify-text-gray);
        }

        .no-results {
            text-align: center;
            color: var(--spotify-text-gray);
            padding: 40px;
            font-size: 14px;
        }

        .badge {
            background: var(--spotify-green);
            color: var(--spotify-darker);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
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

        /* Voice cards */
        .voice-option {
            cursor: pointer;
        }

        .voice-card {
            background: var(--spotify-gray);
            padding: 16px;
            border-radius: 8px;
            border: 2px solid var(--spotify-gray);
            transition: all 0.2s;
        }

        .voice-option:hover .voice-card {
            border-color: var(--spotify-text-gray);
        }

        .voice-option.selected .voice-card {
            border-color: var(--spotify-green);
            background: rgba(29, 185, 84, 0.1);
        }

        .voice-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .voice-name {
            font-weight: 700;
            font-size: 16px;
        }

        .voice-desc {
            color: var(--spotify-text-gray);
            font-size: 13px;
        }

        .voice-preview-btn {
            background: transparent;
            border: none;
            font-size: 20px;
            cursor: pointer;
            padding: 4px;
            transition: all 0.2s;
        }

        .voice-preview-btn:hover {
            transform: scale(1.2);
        }

        /* Drag & Drop Zone */
        .drag-drop-zone {
            border: 2px dashed var(--spotify-text-gray);
            border-radius: 8px;
            padding: 32px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 16px;
            background: var(--spotify-gray);
        }

        .drag-drop-zone:hover {
            border-color: var(--spotify-green);
            background: rgba(29, 185, 84, 0.05);
        }

        .drag-drop-zone.drag-over {
            border-color: var(--spotify-green);
            background: rgba(29, 185, 84, 0.1);
            transform: scale(1.02);
        }

        .drag-drop-text {
            color: var(--spotify-text-gray);
            font-size: 14px;
        }

        /* Advanced Filter */
        .filter-panel {
            background: var(--spotify-gray);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 24px;
        }

        .filter-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 16px;
        }

        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .filter-group label {
            font-size: 12px;
            color: var(--spotify-text-gray);
            font-weight: 600;
        }

        .filter-group select, .filter-group input {
            background: var(--spotify-light-gray);
            border: 1px solid var(--spotify-text-gray);
            border-radius: 4px;
            padding: 8px 12px;
            color: var(--spotify-text);
            font-size: 14px;
        }

        .filter-actions {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
        }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="sidebar">
            <div class="logo">
                🌌 VoiceVerse
            </div>

            <button class="btn-primary" onclick="openQuickGenerate()" style="width: 100%; margin-bottom: 16px; font-size: 14px;">
                ⚡ Quick Generate
            </button>

            <div class="nav-item active" onclick="showSection('home')">
                🏠 Home
            </div>
            <div class="nav-item" onclick="showSection('create')">
                ➕ Create New
            </div>
            <div class="nav-item" onclick="showSection('podcast')">
                🎙️ Podcast Mode
            </div>
            <div class="nav-item" onclick="showSection('history')">
                🕒 History
            </div>
            <div class="nav-item" onclick="showSection('queue')">
                📋 Queue <span class="badge" id="queueBadge" style="margin-left: auto; display: none;">0</span>
            </div>
            <div class="nav-item" onclick="showSection('analytics')">
                📊 Analytics
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
                    <div class="header-controls">
                        <input type="text" class="search-bar" placeholder="Search your files..." id="searchInput" onkeyup="filterFiles()">
                        <button class="btn-secondary" onclick="openQuickGenerate()">⚡ Quick Generate</button>
                        <button class="btn-primary" onclick="showSection('create')">Create New</button>
                    </div>
                </div>

                {% if recent_files %}
                <div class="section-title">
                    <span>Recent Files</span>
                    <select class="sort-select" id="sortSelect" onchange="sortFiles()">
                        <option value="recent">Recent First</option>
                        <option value="oldest">Oldest First</option>
                        <option value="name-asc">Name (A-Z)</option>
                        <option value="name-desc">Name (Z-A)</option>
                    </select>
                </div>
                <div class="files-grid" id="recentGrid">
                    {% for file in recent_files[:6] %}
                    <div class="file-card" data-filename="{{ file.filename }}" data-name="{{ file.name }}" data-group="{{ file.group }}" oncontextmenu="showContextMenu(event); return false;">
                        <div class="file-card-options" onclick="event.stopPropagation(); showContextMenu(event, '{{ file.filename }}', '{{ file.name }}', '{{ file.group }}')">
                            ⋮
                        </div>
                        <div class="file-card-icon" onclick="playFile('{{ file.filename }}'); event.stopPropagation();">
                            🎵
                            <div class="play-button">▶</div>
                        </div>
                        <div class="file-card-title">{{ file.name }}</div>
                        <div class="file-card-meta">
                            <span>{{ file.chars }} chars</span>
                            <span>${{ "%.3f"|format(file.cost) }}</span>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}

                {% for group, files in grouped_files.items() %}
                <div class="section-title">
                    <span>{{ group }}</span>
                    <span style="font-size: 14px; color: var(--spotify-text-gray);">{{ files|length }} files</span>
                </div>
                <div class="files-grid" data-group="{{ group }}">
                    {% for file in files %}
                    <div class="file-card" data-filename="{{ file.filename }}" data-name="{{ file.name }}" data-group="{{ group }}" oncontextmenu="showContextMenu(event); return false;">
                        <div class="file-card-options" onclick="event.stopPropagation(); showContextMenu(event, '{{ file.filename }}', '{{ file.name }}', '{{ group }}')">
                            ⋮
                        </div>
                        <div class="file-card-icon" onclick="playFile('{{ file.filename }}'); event.stopPropagation();">
                            🎵
                            <div class="play-button">▶</div>
                        </div>
                        <div class="file-card-title">{{ file.name }}</div>
                        <div class="file-card-meta">
                            <span>{{ file.chars }} chars</span>
                            <span>${{ "%.3f"|format(file.cost) }}</span>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endfor %}

                <div class="no-results" id="noResults" style="display: none;">
                    No files found. Try creating a new audio file!
                </div>
            </div>

            <!-- Create Section -->
            <div id="createSection" class="content-section" style="display: none;">
                <div class="header">
                    <h1>Create New Audio</h1>
                    <div class="header-controls">
                        <button class="btn-secondary" onclick="toggleBatchMode()" id="batchToggleBtn">Switch to Batch Mode</button>
                    </div>
                </div>

                {% if error %}
                <div class="error-message">{{ error }}</div>
                {% endif %}

                {% if success %}
                <div class="success-message" id="successMessage">✅ Audio generated successfully! Click play button to listen to {{ file_display_name }}...</div>
                <script>
                    // Auto-play in bottom player after generation
                    (function() {
                        const newFilename = "{{ filename }}";
                        const displayName = "{{ file_display_name }}";
                        if (newFilename) {
                            // Load the audio immediately
                            const audioPlayer = document.getElementById('audioPlayer');
                            audioPlayer.src = `/audio/${encodeURIComponent(newFilename)}`;

                            // Update the player UI
                            document.getElementById('nowPlaying').style.opacity = '1';
                            document.getElementById('currentTrackName').textContent = displayName;
                            document.getElementById('currentTrackInfo').textContent = 'Ready to play';

                            // Try to autoplay, but fallback gracefully
                            setTimeout(() => {
                                audioPlayer.play().then(() => {
                                    document.getElementById('playBtn').textContent = '⏸';
                                    document.getElementById('currentTrackInfo').textContent = 'Playing...';
                                    document.getElementById('successMessage').innerHTML = '✅ Audio generated successfully! Now playing ' + displayName + '...';
                                }).catch(e => {
                                    console.log('Autoplay prevented by browser - user must click play');
                                    document.getElementById('playBtn').textContent = '▶';
                                    // Keep the success message asking user to click play
                                });
                            }, 300);
                        }
                    })();
                </script>
                {% endif %}

                {% if batch_success %}
                <div class="success-message">✅ Batch generation completed! Generated {{ batch_count }} audio files.</div>
                {% endif %}

                <!-- Single Mode Form -->
                <form method="POST" enctype="multipart/form-data" style="max-width: 700px;" id="singleForm">
                    <div class="form-group">
                        <label>File Name</label>
                        <input type="text" name="filename" placeholder="My Awesome Audio" required maxlength="100">
                    </div>

                    <div class="form-group">
                        <label>Group</label>
                        <input type="text" name="group" placeholder="Work, Personal, Projects..." value="Uncategorized" maxlength="50">
                    </div>

                    <div class="form-group">
                        <label>Voice <span style="font-size: 12px; color: var(--spotify-text-gray);">(Click speaker icons to preview)</span></label>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
                            <label class="voice-option" data-voice="alloy">
                                <input type="radio" name="voice" value="alloy" style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Alloy</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('alloy'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">Neutral, balanced</div>
                                </div>
                            </label>
                            <label class="voice-option" data-voice="echo">
                                <input type="radio" name="voice" value="echo" style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Echo</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('echo'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">Male, clear</div>
                                </div>
                            </label>
                            <label class="voice-option" data-voice="fable">
                                <input type="radio" name="voice" value="fable" style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Fable</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('fable'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">British, expressive</div>
                                </div>
                            </label>
                            <label class="voice-option" data-voice="onyx">
                                <input type="radio" name="voice" value="onyx" style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Onyx</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('onyx'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">Deep, authoritative</div>
                                </div>
                            </label>
                            <label class="voice-option selected" data-voice="nova">
                                <input type="radio" name="voice" value="nova" checked style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Nova</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('nova'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">Female, friendly</div>
                                </div>
                            </label>
                            <label class="voice-option" data-voice="shimmer">
                                <input type="radio" name="voice" value="shimmer" style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Shimmer</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('shimmer'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">Soft, warm</div>
                                </div>
                            </label>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Text</label>
                        <div class="drag-drop-zone" id="dragDropZone">
                            <div class="drag-drop-text">
                                📄 Drag & drop a .txt file here or click to browse
                            </div>
                            <input type="file" name="textfile" id="fileInput" accept=".txt" style="display: none;">
                        </div>
                        <textarea name="text" rows="10" placeholder="Enter your text here or drag & drop a .txt file above..." id="textInput" required maxlength="4096"></textarea>
                        <div class="char-info">
                            <span>Characters: <span id="charCount">0</span> / 4,096</span>
                            <span class="cost-estimate">Est. cost: $<span id="costCount">0.000</span></span>
                        </div>
                    </div>

                    <div style="display: flex; gap: 12px; margin-bottom: 12px;">
                        <button type="submit" class="btn-primary" style="flex: 1;" onclick="return handleGenerateSubmit(event, false);">
                            Generate Audio (Streaming)
                        </button>
                        <button type="submit" class="btn-secondary" style="flex: 1;" onclick="return handleGenerateSubmit(event, true);">
                            Generate (Standard)
                        </button>
                    </div>

                    <p style="font-size: 12px; color: var(--spotify-text-gray); text-align: center;">
                        💡 Streaming plays audio as it generates. Standard waits for completion.
                    </p>
                </form>

                <!-- Bookmarklet Instructions -->
                <div style="max-width: 700px; margin-top: 32px; padding: 20px; background: var(--spotify-gray); border-radius: 8px;">
                    <h3 style="margin-bottom: 12px; color: var(--spotify-green);">🔖 Web Text Selection Bookmarklet</h3>
                    <p style="font-size: 14px; color: var(--spotify-text-gray); margin-bottom: 16px;">
                        Drag this button to your bookmarks bar to generate audio from any selected text on any webpage:
                    </p>
                    <a href="javascript:(function(){var text=window.getSelection().toString();if(text){window.open('http://localhost:5000?quick='+encodeURIComponent(text),'_blank');}else{alert('Please select some text first!');}})();"
                       style="display: inline-block; background: var(--spotify-green); color: white; padding: 12px 24px; border-radius: 500px; text-decoration: none; font-weight: 700; margin-bottom: 16px;">
                        ⚡ VoiceVerse Quick TTS
                    </a>
                    <p style="font-size: 12px; color: var(--spotify-text-gray);">
                        <strong>How to use:</strong><br>
                        1. Drag the button above to your bookmarks bar<br>
                        2. On any webpage, select/highlight text<br>
                        3. Click the bookmarklet<br>
                        4. VoiceVerse opens with Quick Generate ready!
                    </p>
                    <p style="font-size: 12px; color: var(--spotify-text-gray); margin-top: 12px;">
                        <strong>Keyboard shortcut:</strong> Press <kbd style="background: var(--spotify-light-gray); padding: 4px 8px; border-radius: 4px;">Ctrl+Shift+V</kbd> anywhere in VoiceVerse to open Quick Generate
                    </p>
                </div>

                <!-- Batch Mode Form -->
                <form method="POST" action="/batch" style="max-width: 700px; display: none;" id="batchForm">
                    <div class="form-group">
                        <label>Group</label>
                        <input type="text" name="group" placeholder="Work, Personal, Projects..." value="Uncategorized" maxlength="50">
                    </div>

                    <div class="form-group">
                        <label>Voice <span style="font-size: 12px; color: var(--spotify-text-gray);">(Click speaker icons to preview)</span></label>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
                            <label class="voice-option" data-voice="alloy">
                                <input type="radio" name="voice" value="alloy" style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Alloy</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('alloy'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">Neutral, balanced</div>
                                </div>
                            </label>
                            <label class="voice-option" data-voice="echo">
                                <input type="radio" name="voice" value="echo" style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Echo</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('echo'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">Male, clear</div>
                                </div>
                            </label>
                            <label class="voice-option" data-voice="fable">
                                <input type="radio" name="voice" value="fable" style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Fable</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('fable'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">British, expressive</div>
                                </div>
                            </label>
                            <label class="voice-option" data-voice="onyx">
                                <input type="radio" name="voice" value="onyx" style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Onyx</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('onyx'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">Deep, authoritative</div>
                                </div>
                            </label>
                            <label class="voice-option selected" data-voice="nova">
                                <input type="radio" name="voice" value="nova" checked style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Nova</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('nova'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">Female, friendly</div>
                                </div>
                            </label>
                            <label class="voice-option" data-voice="shimmer">
                                <input type="radio" name="voice" value="shimmer" style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Shimmer</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('shimmer'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">Soft, warm</div>
                                </div>
                            </label>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Batch Texts (One per line: filename|text)</label>
                        <textarea name="batch_texts" rows="15" placeholder="Example:&#10;Chapter 1|This is the first chapter text...&#10;Chapter 2|This is the second chapter text...&#10;Intro|Welcome to my podcast..." id="batchInput" required></textarea>
                        <div class="char-info">
                            <span>Lines: <span id="batchLineCount">0</span></span>
                            <span class="cost-estimate">Est. cost: $<span id="batchCostCount">0.000</span></span>
                        </div>
                    </div>

                    <button type="submit" class="btn-primary" style="width: 100%;">Generate Batch</button>
                </form>
            </div>

            <!-- Podcast Mode Section -->
            <div id="podcastSection" class="content-section" style="display: none;">
                <div class="header">
                    <h1>Podcast Mode</h1>
                    <p style="color: var(--spotify-text-gray); font-size: 14px; margin-top: 8px;">Combine multiple text segments into one continuous audio file</p>
                </div>

                {% if podcast_success %}
                <div class="success-message">✅ Podcast generated successfully! {{ podcast_filename }}</div>
                {% endif %}

                {% if podcast_error %}
                <div class="error-message">{{ podcast_error }}</div>
                {% endif %}

                <form method="POST" action="/podcast" style="max-width: 700px;">
                    <div class="form-group">
                        <label>Podcast Title</label>
                        <input type="text" name="podcast_title" placeholder="My Podcast Episode" required maxlength="100">
                    </div>

                    <div class="form-group">
                        <label>Group</label>
                        <input type="text" name="group" placeholder="Podcasts, Stories..." value="Podcasts" maxlength="50">
                    </div>

                    <div class="form-group">
                        <label>Voice <span style="font-size: 12px; color: var(--spotify-text-gray);">(Click speaker icons to preview)</span></label>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
                            <label class="voice-option" data-voice="alloy">
                                <input type="radio" name="voice" value="alloy" style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Alloy</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('alloy'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">Neutral, balanced</div>
                                </div>
                            </label>
                            <label class="voice-option" data-voice="echo">
                                <input type="radio" name="voice" value="echo" style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Echo</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('echo'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">Male, clear</div>
                                </div>
                            </label>
                            <label class="voice-option" data-voice="fable">
                                <input type="radio" name="voice" value="fable" style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Fable</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('fable'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">British, expressive</div>
                                </div>
                            </label>
                            <label class="voice-option" data-voice="onyx">
                                <input type="radio" name="voice" value="onyx" style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Onyx</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('onyx'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">Deep, authoritative</div>
                                </div>
                            </label>
                            <label class="voice-option selected" data-voice="nova">
                                <input type="radio" name="voice" value="nova" checked style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Nova</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('nova'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">Female, friendly</div>
                                </div>
                            </label>
                            <label class="voice-option" data-voice="shimmer">
                                <input type="radio" name="voice" value="shimmer" style="display: none;">
                                <div class="voice-card">
                                    <div class="voice-header">
                                        <span class="voice-name">Shimmer</span>
                                        <button type="button" class="voice-preview-btn" onclick="previewVoice('shimmer'); event.stopPropagation();">🔊</button>
                                    </div>
                                    <div class="voice-desc">Soft, warm</div>
                                </div>
                            </label>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Podcast Segments (One per line)</label>
                        <textarea name="podcast_segments" rows="15" placeholder="Example:&#10;Welcome to episode 5 of my podcast. Today we'll discuss AI...&#10;&#10;Segment 2: Let's dive into the topic...&#10;&#10;Conclusion: Thanks for listening!" id="podcastInput" required></textarea>
                        <div class="char-info">
                            <span>Total Characters: <span id="podcastCharCount">0</span></span>
                            <span class="cost-estimate">Est. cost: $<span id="podcastCostCount">0.000</span></span>
                        </div>
                    </div>

                    <button type="submit" class="btn-primary" style="width: 100%;">Generate Podcast</button>
                </form>
            </div>

            <!-- History Section -->
            <div id="historySection" class="content-section" style="display: none;">
                <div class="header">
                    <h1>Playback History</h1>
                    <div class="header-controls">
                        <button class="btn-secondary" onclick="clearHistory()">Clear History</button>
                    </div>
                </div>

                {% if playback_history %}
                <div class="queue-section">
                    <div class="queue-header">
                        <h3>Recently Played</h3>
                        <span style="color: var(--spotify-text-gray); font-size: 14px;">{{ playback_history|length }} plays</span>
                    </div>
                    {% for item in playback_history %}
                    <div class="queue-item" style="cursor: pointer;" onclick="playFile('{{ item.filename }}', '{{ item.name }}')">
                        <div class="queue-number">{{ loop.index }}</div>
                        <div class="queue-info">
                            <div class="queue-title">{{ item.name }}</div>
                            <div class="queue-meta">Played: {{ item.timestamp }}</div>
                        </div>
                        <button class="control-btn" onclick="playFile('{{ item.filename }}', '{{ item.name }}'); event.stopPropagation();">▶</button>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="no-results">
                    No playback history yet. Start listening to audio files to build your history!
                </div>
                {% endif %}
            </div>

            <!-- Queue Section -->
            <div id="queueSection" class="content-section" style="display: none;">
                <div class="header">
                    <h1>Play Queue</h1>
                    <div class="header-controls">
                        <button class="btn-secondary" onclick="clearQueue()">Clear Queue</button>
                        <button class="btn-primary" onclick="playQueue()">Play All</button>
                    </div>
                </div>

                <div class="queue-section">
                    <div class="queue-header">
                        <h3>Up Next</h3>
                        <span id="queueCount" style="color: var(--spotify-text-gray); font-size: 14px;">0 tracks</span>
                    </div>
                    <div id="queueList">
                        <div class="no-results" style="padding: 20px;">
                            Your queue is empty. Add files from your library!
                        </div>
                    </div>
                </div>
            </div>

            <!-- Analytics Section -->
            <div id="analyticsSection" class="content-section" style="display: none;">
                <div class="header">
                    <h1>Analytics</h1>
                </div>

                {% if monthly_chart %}
                <div class="chart-container">
                    <div class="chart-title">Monthly Spending (Last 6 Months)</div>
                    <div class="chart-bars" style="position: relative; padding-bottom: 30px;">
                        {% for month_data in monthly_chart %}
                        <div class="chart-bar" style="height: {{ month_data.percentage }}%;">
                            <div class="chart-bar-value">${{ "%.2f"|format(month_data.cost) }}</div>
                            <div class="chart-bar-label">{{ month_data.month }}</div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% else %}
                <div class="no-results">
                    No analytics data yet. Start creating audio files to see your usage statistics!
                </div>
                {% endif %}

                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
                    <div class="stats-card" style="background: var(--spotify-gray); padding: 24px;">
                        <div style="font-size: 14px; color: var(--spotify-text-gray); margin-bottom: 8px;">Average Cost/File</div>
                        <div style="font-size: 28px; font-weight: 700; color: var(--spotify-green);">
                            ${{ "%.4f"|format(usage.total_cost / usage.files_generated if usage.files_generated > 0 else 0) }}
                        </div>
                    </div>
                    <div class="stats-card" style="background: var(--spotify-gray); padding: 24px;">
                        <div style="font-size: 14px; color: var(--spotify-text-gray); margin-bottom: 8px;">Avg Characters/File</div>
                        <div style="font-size: 28px; font-weight: 700; color: var(--spotify-green);">
                            {{ (usage.total_characters / usage.files_generated)|int if usage.files_generated > 0 else 0 }}
                        </div>
                    </div>
                    <div class="stats-card" style="background: var(--spotify-gray); padding: 24px;">
                        <div style="font-size: 14px; color: var(--spotify-text-gray); margin-bottom: 8px;">Total Files</div>
                        <div style="font-size: 28px; font-weight: 700; color: var(--spotify-green);">
                            {{ usage.files_generated }}
                        </div>
                    </div>
                </div>
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
                <button class="control-btn" onclick="previousTrack()">⏮</button>
                <button class="control-btn play" onclick="togglePlay()" id="playBtn">▶</button>
                <button class="control-btn" onclick="nextTrack()">⏭</button>
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
            <span style="font-size: 14px; color: var(--spotify-text-gray);">
                Speed: <span id="speedDisplay">1.0x</span>
            </span>
            <input type="range" min="0.5" max="2" step="0.1" value="1" 
                   style="width: 80px;" onchange="changeSpeed(this.value)" id="speedSlider">
        </div>
    </div>

    <!-- Modals -->
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

    <div class="modal" id="editModal">
        <div class="modal-content">
            <div class="modal-header">Edit Audio Text</div>
            <p style="color: var(--spotify-text-gray); font-size: 14px; margin-bottom: 16px;">Edit the text and regenerate the audio file</p>
            <textarea class="modal-input" id="editInput" placeholder="Enter new text" rows="8" style="resize: vertical; font-family: inherit;"></textarea>
            <div style="margin-bottom: 16px;">
                <label style="display: block; margin-bottom: 8px; color: var(--spotify-text-gray); font-size: 14px;">Voice</label>
                <select class="modal-input" id="editVoice" style="padding: 12px;">
                    <option value="alloy">Alloy - Neutral, balanced</option>
                    <option value="echo">Echo - Male, clear</option>
                    <option value="fable">Fable - British, expressive</option>
                    <option value="onyx">Onyx - Deep, authoritative</option>
                    <option value="nova" selected>Nova - Female, friendly</option>
                    <option value="shimmer">Shimmer - Soft, warm</option>
                </select>
            </div>
            <div class="modal-buttons">
                <button class="btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn-primary" onclick="confirmEdit()">Regenerate Audio</button>
            </div>
        </div>
    </div>

    <div class="modal" id="pictureModal">
        <div class="modal-content">
            <div class="modal-header">Add Picture</div>
            <p style="color: var(--spotify-text-gray); font-size: 14px; margin-bottom: 16px;">Upload an image to associate with this audio file</p>
            <input type="file" class="modal-input" id="pictureInput" accept="image/*" style="padding: 8px;">
            <div id="picturePreview" style="margin-top: 16px; text-align: center;"></div>
            <div class="modal-buttons">
                <button class="btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn-primary" onclick="confirmPicture()">Upload Picture</button>
            </div>
        </div>
    </div>

    <div class="modal" id="albumModal">
        <div class="modal-content">
            <div class="modal-header">Add to Album</div>
            <p style="color: var(--spotify-text-gray); font-size: 14px; margin-bottom: 16px;">Select an album or create a new one</p>
            <select class="modal-input" id="albumSelect">
                <option value="">-- Select Album --</option>
                <option value="__new__">+ Create New Album</option>
            </select>
            <input type="text" class="modal-input" id="newAlbumInput" placeholder="New album name" style="display: none; margin-top: 12px;" maxlength="100">
            <div class="modal-buttons">
                <button class="btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn-primary" onclick="confirmAlbum()">Add to Album</button>
            </div>
        </div>
    </div>

    <div class="modal" id="mergeModal">
        <div class="modal-content" style="max-width: 700px;">
            <div class="modal-header">Merge Files (Create Audiobook)</div>
            <p style="color: var(--spotify-text-gray); font-size: 14px; margin-bottom: 16px;">Select multiple files to merge into one continuous audio</p>
            <input type="text" class="modal-input" id="mergeTitle" placeholder="Audiobook title" maxlength="100" style="margin-bottom: 16px;">
            <div id="mergeFilesList" style="max-height: 300px; overflow-y: auto; background: var(--spotify-gray); padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                <!-- Files will be populated here -->
            </div>
            <div class="modal-buttons">
                <button class="btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn-primary" onclick="confirmMerge()">Merge Files</button>
            </div>
        </div>
    </div>

    <!-- Quick Generate Modal -->
    <div class="modal" id="quickGenerateModal">
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">⚡ Quick Generate & Play</div>
            <p style="color: var(--spotify-text-gray); font-size: 14px; margin-bottom: 16px;">
                Paste text and instantly play audio without saving
            </p>

            <div style="margin-bottom: 16px;">
                <label style="display: block; margin-bottom: 8px; font-weight: 600;">Select Voice</label>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
                    <label class="voice-option" data-voice="alloy">
                        <input type="radio" name="quick-voice" value="alloy" style="display: none;">
                        <div class="voice-card" style="padding: 8px;">
                            <span class="voice-name" style="font-size: 12px;">Alloy</span>
                        </div>
                    </label>
                    <label class="voice-option" data-voice="echo">
                        <input type="radio" name="quick-voice" value="echo" style="display: none;">
                        <div class="voice-card" style="padding: 8px;">
                            <span class="voice-name" style="font-size: 12px;">Echo</span>
                        </div>
                    </label>
                    <label class="voice-option" data-voice="fable">
                        <input type="radio" name="quick-voice" value="fable" style="display: none;">
                        <div class="voice-card" style="padding: 8px;">
                            <span class="voice-name" style="font-size: 12px;">Fable</span>
                        </div>
                    </label>
                    <label class="voice-option" data-voice="onyx">
                        <input type="radio" name="quick-voice" value="onyx" style="display: none;">
                        <div class="voice-card" style="padding: 8px;">
                            <span class="voice-name" style="font-size: 12px;">Onyx</span>
                        </div>
                    </label>
                    <label class="voice-option selected" data-voice="nova">
                        <input type="radio" name="quick-voice" value="nova" checked style="display: none;">
                        <div class="voice-card" style="padding: 8px;">
                            <span class="voice-name" style="font-size: 12px;">Nova</span>
                        </div>
                    </label>
                    <label class="voice-option" data-voice="shimmer">
                        <input type="radio" name="quick-voice" value="shimmer" style="display: none;">
                        <div class="voice-card" style="padding: 8px;">
                            <span class="voice-name" style="font-size: 12px;">Shimmer</span>
                        </div>
                    </label>
                </div>
            </div>

            <textarea id="quickGenerateText" class="modal-input" rows="8" placeholder="Paste your text here..." maxlength="4096" style="font-family: inherit; resize: vertical;"></textarea>
            <div style="font-size: 12px; color: var(--spotify-text-gray); margin-top: 8px; margin-bottom: 16px;">
                <span id="quickCharCount">0</span> / 4,096 characters
            </div>

            <div class="modal-buttons">
                <button class="btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn-primary" onclick="quickGenerateAndPlay()">⚡ Generate & Play</button>
            </div>
        </div>
    </div>

    <!-- Streaming Progress Modal -->
    <div class="modal" id="streamingModal">
        <div class="modal-content" style="max-width: 500px;">
            <div class="modal-header">Generating Audio...</div>
            <div style="text-align: center; padding: 24px;">
                <div style="font-size: 48px; margin-bottom: 16px;">🎵</div>
                <div id="streamingStatus" style="color: var(--spotify-text-gray); margin-bottom: 16px;">
                    Starting generation...
                </div>
                <div style="background: var(--spotify-gray); border-radius: 8px; height: 8px; overflow: hidden; margin-bottom: 8px;">
                    <div id="streamingProgress" style="background: var(--spotify-green); height: 100%; width: 0%; transition: width 0.3s;"></div>
                </div>
                <div id="streamingProgressText" style="font-size: 12px; color: var(--spotify-text-gray);">
                    0%
                </div>
            </div>
        </div>
    </div>

    <div class="context-menu" id="contextMenu">
        <div class="context-item" onclick="contextPlay()">▶ Play</div>
        <div class="context-item" onclick="contextAddToQueue()">➕ Add to Queue</div>
        <div class="context-item" onclick="contextEdit()">✏️ Edit Text</div>
        <div class="context-item" onclick="contextAddPicture()">🖼️ Add Picture</div>
        <div class="context-item" onclick="contextDuplicate()">📑 Duplicate</div>
        <div class="context-item" onclick="contextAddToAlbum()">📁 Move to Album</div>
        <div class="context-item" onclick="contextMerge()">🔗 Merge Files</div>
        <div class="context-item" onclick="contextShare()">🔗 Share</div>
        <div class="context-item" onclick="contextRename()">✏ Rename</div>
        <div class="context-item" onclick="contextDownload()">⬇ Download</div>
        <div class="context-item danger" onclick="contextDelete()">🗑 Delete</div>
    </div>

    <audio id="audioPlayer" style="display: none;"></audio>

    <script>
        let currentFilename = null;
        let currentFileName = null;
        let playlist = [];
        let currentIndex = 0;
        const audioPlayer = document.getElementById('audioPlayer');

        // Character counter with better handling
        const textInput = document.getElementById('textInput');
        if (textInput) {
            textInput.addEventListener('input', function() {
                const length = this.value.length;
                document.getElementById('charCount').textContent = length.toLocaleString();
                const cost = (length / 1000) * 0.015;
                document.getElementById('costCount').textContent = cost.toFixed(4);

                // Color code based on limit
                if (length > 4096) {
                    this.style.borderColor = '#ff4444';
                } else if (length > 3500) {
                    this.style.borderColor = '#ffaa00';
                } else {
                    this.style.borderColor = '';
                }
            });
        }

        // Batch input counter
        const batchInput = document.getElementById('batchInput');
        if (batchInput) {
            batchInput.addEventListener('input', function() {
                const lines = this.value.split('\n').filter(line => line.trim().length > 0);
                document.getElementById('batchLineCount').textContent = lines.length;

                // Calculate total cost
                let totalChars = 0;
                lines.forEach(line => {
                    const parts = line.split('|');
                    if (parts.length >= 2) {
                        totalChars += parts.slice(1).join('|').length;
                    }
                });
                const cost = (totalChars / 1000) * 0.015;
                document.getElementById('batchCostCount').textContent = cost.toFixed(4);
            });
        }

        // Toggle batch mode
        function toggleBatchMode() {
            const singleForm = document.getElementById('singleForm');
            const batchForm = document.getElementById('batchForm');
            const toggleBtn = document.getElementById('batchToggleBtn');

            if (singleForm.style.display === 'none') {
                singleForm.style.display = 'block';
                batchForm.style.display = 'none';
                toggleBtn.textContent = 'Switch to Batch Mode';
            } else {
                singleForm.style.display = 'none';
                batchForm.style.display = 'block';
                toggleBtn.textContent = 'Switch to Single Mode';
            }
        }

        // Voice selection
        document.querySelectorAll('.voice-option').forEach(option => {
            option.addEventListener('click', function() {
                document.querySelectorAll('.voice-option').forEach(opt => opt.classList.remove('selected'));
                this.classList.add('selected');
                this.querySelector('input[type="radio"]').checked = true;
            });
        });

        // Drag & Drop file upload
        const dragDropZone = document.getElementById('dragDropZone');
        const fileInput = document.getElementById('fileInput');
        const textInput = document.getElementById('textInput');

        if (dragDropZone && fileInput && textInput) {
            // Click to browse
            dragDropZone.addEventListener('click', () => {
                fileInput.click();
            });

            // File selected via browse
            fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    handleFile(file);
                }
            });

            // Drag over
            dragDropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dragDropZone.classList.add('drag-over');
            });

            // Drag leave
            dragDropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dragDropZone.classList.remove('drag-over');
            });

            // Drop
            dragDropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dragDropZone.classList.remove('drag-over');

                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    const file = files[0];
                    if (file.type === 'text/plain' || file.name.endsWith('.txt')) {
                        handleFile(file);
                    } else {
                        alert('Please drop a .txt file');
                    }
                }
            });

            function handleFile(file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const text = e.target.result;
                    if (text.length > 4096) {
                        alert(`File contains ${text.length} characters. Maximum is 4,096. The text will be truncated.`);
                        textInput.value = text.substring(0, 4096);
                    } else {
                        textInput.value = text;
                    }
                    // Trigger input event to update character count
                    textInput.dispatchEvent(new Event('input'));

                    // Show success message
                    const notification = document.createElement('div');
                    notification.className = 'success-message';
                    notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 2000; animation: slideIn 0.3s';
                    notification.textContent = `✅ File "${file.name}" loaded successfully!`;
                    document.body.appendChild(notification);
                    setTimeout(() => notification.remove(), 3000);
                };
                reader.onerror = () => {
                    alert('Failed to read file');
                };
                reader.readAsText(file);
            }
        }

        // Voice preview
        let previewAudio = null;
        function previewVoice(voice) {
            // Stop any currently playing preview
            if (previewAudio) {
                previewAudio.pause();
            }

            // Create preview text
            const previewTexts = {
                'alloy': 'Hello! I am Alloy, a neutral and balanced voice perfect for any content.',
                'echo': 'Hi there! I am Echo, with a clear male voice ideal for professional narration.',
                'fable': 'Greetings! I am Fable, with a British accent bringing expressiveness to your stories.',
                'onyx': 'Good day. I am Onyx, delivering deep and authoritative tones for impactful messages.',
                'nova': 'Hey! I am Nova, a friendly female voice here to make your content engaging.',
                'shimmer': 'Hello! I am Shimmer, offering soft and warm tones for a comforting experience.'
            };

            const text = previewTexts[voice] || 'This is a voice preview sample.';

            // Show loading state
            const notification = document.createElement('div');
            notification.className = 'success-message';
            notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 2000; animation: slideIn 0.3s';
            notification.textContent = `⏳ Generating ${voice} preview...`;
            document.body.appendChild(notification);

            // Generate preview
            fetch('/preview', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({voice: voice, text: text})
            })
            .then(response => {
                if (!response.ok) throw new Error('Preview generation failed');
                return response.blob();
            })
            .then(blob => {
                const url = URL.createObjectURL(blob);
                previewAudio = new Audio(url);
                previewAudio.play().catch(e => {
                    alert('Failed to play preview');
                    console.error(e);
                });
                notification.textContent = `🔊 Playing ${voice} preview...`;
                setTimeout(() => notification.remove(), 3000);
            })
            .catch(error => {
                notification.textContent = `❌ Failed to generate preview`;
                notification.style.background = '#ff4444';
                setTimeout(() => notification.remove(), 3000);
                console.error(error);
            });
        }

        // Podcast input counter
        const podcastInput = document.getElementById('podcastInput');
        if (podcastInput) {
            podcastInput.addEventListener('input', function() {
                const length = this.value.length;
                document.getElementById('podcastCharCount').textContent = length.toLocaleString();
                const cost = (length / 1000) * 0.015;
                document.getElementById('podcastCostCount').textContent = cost.toFixed(4);
            });
        }

        // Navigation
        function showSection(section) {
            document.querySelectorAll('.content-section').forEach(s => s.style.display = 'none');
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

            const sections = {
                'home': 0,
                'create': 1,
                'podcast': 2,
                'history': 3,
                'queue': 4,
                'analytics': 5
            };

            document.getElementById(section + 'Section').style.display = 'block';
            document.querySelectorAll('.nav-item')[sections[section]].classList.add('active');
        }

        // Clear history
        function clearHistory() {
            if (confirm('Clear all playback history?')) {
                fetch('/clear-history', {method: 'POST'})
                    .then(response => {
                        if (response.ok) {
                            window.location.reload();
                        } else {
                            alert('Failed to clear history');
                        }
                    })
                    .catch(err => alert('Error: ' + err));
            }
        }

        // Context Menu
        function showContextMenu(event, filename = null, name = null, group = null) {
            event.preventDefault();
            event.stopPropagation();

            // If parameters are passed directly, use them; otherwise get from element
            if (filename && name) {
                currentFilename = filename;
                currentFileName = name;
            } else {
                const card = event.currentTarget;
                currentFilename = card.dataset.filename;
                currentFileName = card.dataset.name;
            }

            const menu = document.getElementById('contextMenu');
            menu.style.left = event.pageX + 'px';
            menu.style.top = event.pageY + 'px';
            menu.classList.add('active');
        }

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.context-menu')) {
                document.getElementById('contextMenu').classList.remove('active');
            }
        });

        function contextPlay() {
            playFile(currentFilename);
        }

        function contextAddToQueue() {
            addToQueue(currentFilename, currentFileName);
        }

        function contextShare() {
            const shareUrl = `${window.location.origin}/audio/${encodeURIComponent(currentFilename)}`;

            // Try to use the Clipboard API
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(shareUrl).then(() => {
                    const notification = document.createElement('div');
                    notification.className = 'success-message';
                    notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 2000; animation: slideIn 0.3s';
                    notification.textContent = `✅ Share link copied to clipboard!`;
                    document.body.appendChild(notification);
                    setTimeout(() => notification.remove(), 3000);
                }).catch(err => {
                    // Fallback for older browsers
                    prompt('Share this link:', shareUrl);
                });
            } else {
                // Fallback for older browsers
                prompt('Share this link:', shareUrl);
            }
        }

        function contextRename() {
            document.getElementById('renameInput').value = currentFileName;
            document.getElementById('renameModal').classList.add('active');
        }

        function contextDownload() {
            window.location.href = `/download/${encodeURIComponent(currentFilename)}`;
        }

        function contextDuplicate() {
            if (confirm(`Create a duplicate of "${currentFileName}"?`)) {
                fetch(`/duplicate/${encodeURIComponent(currentFilename)}`, {method: 'POST'})
                    .then(response => {
                        if (response.ok) {
                            window.location.reload();
                        } else {
                            alert('Failed to duplicate file');
                        }
                    })
                    .catch(err => alert('Error: ' + err));
            }
        }

        function contextDelete() {
            if (confirm(`Delete "${currentFileName}"?`)) {
                fetch(`/delete/${encodeURIComponent(currentFilename)}`, {method: 'POST'})
                    .then(response => {
                        if (response.ok) {
                            window.location.reload();
                        } else {
                            alert('Failed to delete file');
                        }
                    })
                    .catch(err => alert('Error: ' + err));
            }
        }

        function contextEdit() {
            // Fetch current metadata to get original text if available
            document.getElementById('editInput').value = '';
            document.getElementById('editModal').classList.add('active');
        }

        function confirmEdit() {
            const newText = document.getElementById('editInput').value.trim();
            const voice = document.getElementById('editVoice').value;

            if (!newText) {
                alert('Please enter text');
                return;
            }

            if (newText.length > 4096) {
                alert(`Text exceeds 4,096 character limit (current: ${newText.length} characters)`);
                return;
            }

            // Send edit request
            fetch(`/edit/${encodeURIComponent(currentFilename)}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: newText, voice: voice})
            }).then(response => {
                if (response.ok) {
                    window.location.reload();
                } else {
                    alert('Failed to edit file');
                }
            }).catch(err => alert('Error: ' + err));

            closeModal();
        }

        function contextAddPicture() {
            document.getElementById('pictureInput').value = '';
            document.getElementById('picturePreview').innerHTML = '';
            document.getElementById('pictureModal').classList.add('active');

            // Add preview functionality
            document.getElementById('pictureInput').onchange = function(e) {
                const file = e.target.files[0];
                if (file && file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(event) {
                        document.getElementById('picturePreview').innerHTML =
                            `<img src="${event.target.result}" style="max-width: 100%; max-height: 200px; border-radius: 8px;">`;
                    };
                    reader.readAsDataURL(file);
                }
            };
        }

        function confirmPicture() {
            const fileInput = document.getElementById('pictureInput');
            const file = fileInput.files[0];

            if (!file) {
                alert('Please select an image');
                return;
            }

            const formData = new FormData();
            formData.append('picture', file);
            formData.append('filename', currentFilename);

            fetch(`/add-picture/${encodeURIComponent(currentFilename)}`, {
                method: 'POST',
                body: formData
            }).then(response => {
                if (response.ok) {
                    window.location.reload();
                } else {
                    alert('Failed to upload picture');
                }
            }).catch(err => alert('Error: ' + err));

            closeModal();
        }

        function contextAddToAlbum() {
            // Fetch existing albums
            fetch('/albums')
                .then(response => response.json())
                .then(data => {
                    const select = document.getElementById('albumSelect');
                    // Keep first two options, add albums
                    while (select.options.length > 2) {
                        select.remove(2);
                    }
                    data.albums.forEach(album => {
                        const option = document.createElement('option');
                        option.value = album;
                        option.textContent = album;
                        select.appendChild(option);
                    });
                });

            document.getElementById('albumModal').classList.add('active');

            // Show/hide new album input
            document.getElementById('albumSelect').onchange = function() {
                const newInput = document.getElementById('newAlbumInput');
                if (this.value === '__new__') {
                    newInput.style.display = 'block';
                } else {
                    newInput.style.display = 'none';
                }
            };
        }

        function confirmAlbum() {
            const select = document.getElementById('albumSelect');
            let albumName = select.value;

            if (albumName === '__new__') {
                albumName = document.getElementById('newAlbumInput').value.trim();
                if (!albumName) {
                    alert('Please enter an album name');
                    return;
                }
            } else if (!albumName) {
                alert('Please select an album');
                return;
            }

            fetch(`/add-to-album/${encodeURIComponent(currentFilename)}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({album: albumName})
            }).then(response => {
                if (response.ok) {
                    window.location.reload();
                } else {
                    alert('Failed to add to album');
                }
            }).catch(err => alert('Error: ' + err));

            closeModal();
        }

        function contextMerge() {
            document.getElementById('mergeTitle').value = '';
            const mergeList = document.getElementById('mergeFilesList');
            mergeList.innerHTML = '<p style="color: var(--spotify-text-gray); margin-bottom: 12px;">Select files to merge (in order):</p>';

            // Get all files
            const allCards = document.querySelectorAll('.file-card');
            allCards.forEach((card, index) => {
                const filename = card.dataset.filename;
                const name = card.dataset.name;

                const checkbox = document.createElement('div');
                checkbox.style.cssText = 'padding: 8px; margin-bottom: 4px; background: var(--spotify-light-gray); border-radius: 4px; cursor: pointer; display: flex; align-items: center; gap: 12px;';
                checkbox.innerHTML = `
                    <input type="checkbox" value="${filename}" data-name="${name}" id="merge_${index}" style="width: 20px; height: 20px; cursor: pointer;">
                    <label for="merge_${index}" style="cursor: pointer; flex: 1;">${name}</label>
                `;
                mergeList.appendChild(checkbox);
            });

            document.getElementById('mergeModal').classList.add('active');
        }

        function confirmMerge() {
            const title = document.getElementById('mergeTitle').value.trim();
            if (!title) {
                alert('Please enter a title for the merged audiobook');
                return;
            }

            const selected = Array.from(document.querySelectorAll('#mergeFilesList input[type="checkbox"]:checked'))
                .map(cb => cb.value);

            if (selected.length < 2) {
                alert('Please select at least 2 files to merge');
                return;
            }

            fetch('/merge', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title: title, files: selected})
            }).then(response => {
                if (response.ok) {
                    window.location.reload();
                } else {
                    alert('Failed to merge files');
                }
            }).catch(err => alert('Error: ' + err));

            closeModal();
        }

        function closeModal() {
            document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
        }

        // Quick Generate functions
        function openQuickGenerate(prefilledText = '') {
            document.getElementById('quickGenerateModal').classList.add('active');
            const textarea = document.getElementById('quickGenerateText');
            if (prefilledText) {
                textarea.value = prefilledText;
                textarea.dispatchEvent(new Event('input'));
            }
            textarea.focus();
        }

        function quickGenerateAndPlay() {
            const text = document.getElementById('quickGenerateText').value.trim();
            const voice = document.querySelector('input[name="quick-voice"]:checked')?.value || 'nova';

            if (!text) {
                alert('Please enter some text');
                return;
            }

            if (text.length > 4096) {
                alert(`Text exceeds 4,096 character limit (current: ${text.length} characters)`);
                return;
            }

            closeModal();

            // Show loading notification
            const notification = document.createElement('div');
            notification.className = 'success-message';
            notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 2000; animation: slideIn 0.3s';
            notification.textContent = '⏳ Generating audio...';
            document.body.appendChild(notification);

            fetch('/quick-generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text, voice: voice})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Convert base64 to blob and play
                    const audioData = atob(data.audio);
                    const arrayBuffer = new Uint8Array(audioData.length);
                    for (let i = 0; i < audioData.length; i++) {
                        arrayBuffer[i] = audioData.charCodeAt(i);
                    }
                    const blob = new Blob([arrayBuffer], {type: 'audio/mpeg'});
                    const url = URL.createObjectURL(blob);

                    audioPlayer.src = url;
                    audioPlayer.play().then(() => {
                        document.getElementById('nowPlaying').style.opacity = '1';
                        document.getElementById('currentTrackName').textContent = `Quick Generated (${voice})`;
                        document.getElementById('currentTrackInfo').textContent = 'Playing...';
                        document.getElementById('playBtn').textContent = '⏸';

                        notification.textContent = '✅ Playing audio!';
                        setTimeout(() => notification.remove(), 3000);
                    }).catch(e => {
                        notification.textContent = '❌ Failed to play audio';
                        notification.style.background = '#ff4444';
                        setTimeout(() => notification.remove(), 3000);
                    });
                } else {
                    notification.textContent = `❌ ${data.error}`;
                    notification.style.background = '#ff4444';
                    setTimeout(() => notification.remove(), 3000);
                }
            })
            .catch(error => {
                notification.textContent = '❌ Error generating audio';
                notification.style.background = '#ff4444';
                setTimeout(() => notification.remove(), 3000);
                console.error(error);
            });
        }

        // Character counter for quick generate
        const quickTextInput = document.getElementById('quickGenerateText');
        if (quickTextInput) {
            quickTextInput.addEventListener('input', function() {
                document.getElementById('quickCharCount').textContent = this.value.length.toLocaleString();
            });
        }

        // Keyboard shortcut: Ctrl+Shift+V for Quick Generate
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.shiftKey && e.key === 'V') {
                e.preventDefault();
                openQuickGenerate();
            }
        });

        // Handle URL parameters for bookmarklet
        window.addEventListener('DOMContentLoaded', function() {
            const urlParams = new URLSearchParams(window.location.search);
            const quickText = urlParams.get('quick');
            if (quickText) {
                setTimeout(() => {
                    openQuickGenerate(decodeURIComponent(quickText));
                }, 500);
            }
        });

        // Handle form submission for Generate Audio
        function handleGenerateSubmit(event, useStandard) {
            event.preventDefault();

            const form = document.getElementById('singleForm');
            const text = form.querySelector('[name="text"]').value.trim();
            const voice = form.querySelector('[name="voice"]:checked')?.value || 'nova';
            const filename = form.querySelector('[name="filename"]').value.trim();
            const group = form.querySelector('[name="group"]').value.trim();

            if (!text) {
                alert('Please enter some text');
                return false;
            }

            if (text.length > 4096) {
                alert(`Text exceeds 4,096 character limit (current: ${text.length} characters)`);
                return false;
            }

            if (!filename) {
                alert('Please enter a file name');
                return false;
            }

            if (useStandard) {
                // Use standard form submission
                form.submit();
            } else {
                // Use streaming
                streamingGenerate(text, voice, filename, group);
            }

            return false;
        }

        // Streaming Generate with Progress
        function streamingGenerate(text, voice, filename, group) {
            // Show streaming modal
            document.getElementById('streamingModal').classList.add('active');
            document.getElementById('streamingStatus').textContent = 'Starting generation...';
            document.getElementById('streamingProgress').style.width = '0%';
            document.getElementById('streamingProgressText').textContent = '0%';

            const eventSource = new EventSource('/stream-generate');
            const audioChunks = [];
            let isFirstChunk = true;

            // Send data via POST - we'll use fetch first then EventSource
            fetch('/stream-generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    text: text,
                    voice: voice,
                    filename: filename,
                    group: group
                })
            }).then(response => {
                if (!response.ok) throw new Error('Failed to start streaming');

                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                function readStream() {
                    reader.read().then(({done, value}) => {
                        if (done) {
                            // Close modal and show success
                            closeModal();
                            const notification = document.createElement('div');
                            notification.className = 'success-message';
                            notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 2000; animation: slideIn 0.3s';
                            notification.textContent = '✅ Audio generated and saved!';
                            document.body.appendChild(notification);
                            setTimeout(() => {
                                notification.remove();
                                window.location.reload();
                            }, 2000);
                            return;
                        }

                        const chunk = decoder.decode(value, {stream: true});
                        const lines = chunk.split('\n');

                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const data = JSON.parse(line.substring(6));

                                if (data.error) {
                                    closeModal();
                                    alert(`Error: ${data.error}`);
                                    return;
                                }

                                if (data.progress && data.total) {
                                    const percent = (data.progress / data.total * 100).toFixed(0);
                                    document.getElementById('streamingProgress').style.width = percent + '%';
                                    document.getElementById('streamingProgressText').textContent = percent + '%';
                                    document.getElementById('streamingStatus').textContent = data.status || 'Generating...';
                                }

                                if (data.chunk) {
                                    // Play chunk immediately
                                    if (isFirstChunk) {
                                        const audioData = atob(data.chunk);
                                        const arrayBuffer = new Uint8Array(audioData.length);
                                        for (let i = 0; i < audioData.length; i++) {
                                            arrayBuffer[i] = audioData.charCodeAt(i);
                                        }
                                        const blob = new Blob([arrayBuffer], {type: 'audio/mpeg'});
                                        const url = URL.createObjectURL(blob);

                                        audioPlayer.src = url;
                                        audioPlayer.play().then(() => {
                                            document.getElementById('nowPlaying').style.opacity = '1';
                                            document.getElementById('currentTrackName').textContent = filename;
                                            document.getElementById('currentTrackInfo').textContent = 'Generating & Playing...';
                                            document.getElementById('playBtn').textContent = '⏸';
                                        });
                                        isFirstChunk = false;
                                    }
                                    audioChunks.push(data.chunk);
                                }

                                if (data.complete) {
                                    document.getElementById('streamingProgress').style.width = '100%';
                                    document.getElementById('streamingProgressText').textContent = '100%';
                                    document.getElementById('streamingStatus').textContent = 'Complete!';

                                    // Update player with final filename
                                    setTimeout(() => {
                                        audioPlayer.src = `/audio/${encodeURIComponent(data.filename)}`;
                                        document.getElementById('currentTrackName').textContent = data.display_name;
                                        document.getElementById('currentTrackInfo').textContent = 'Playing...';
                                    }, 500);
                                }
                            }
                        }

                        readStream();
                    });
                }

                readStream();
            }).catch(error => {
                closeModal();
                alert(`Error: ${error.message}`);
                console.error(error);
            });
        }

        function confirmRename() {
            const newName = document.getElementById('renameInput').value.trim();
            if (newName && newName !== currentFileName) {
                fetch(`/rename/${encodeURIComponent(currentFilename)}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: newName})
                }).then(response => {
                    if (response.ok) {
                        window.location.reload();
                    } else {
                        alert('Failed to rename file');
                    }
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
            // Use provided display name or extract from filename
            const trackName = displayName || filename.split('_')[0] || filename;
            document.getElementById('currentTrackName').textContent = trackName;
            document.getElementById('currentTrackInfo').textContent = 'Playing...';
            document.getElementById('playBtn').textContent = '⏸';

            // Track playback in history
            fetch('/track', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({filename: filename, name: trackName})
            }).catch(e => console.log('Failed to track playback:', e));
        }

        function playFileWithName(filename, displayName) {
            if (!filename) return;

            audioPlayer.src = `/audio/${encodeURIComponent(filename)}`;
            audioPlayer.play().catch(e => {
                console.error('Playback error:', e);
                alert('Failed to play audio');
            });

            document.getElementById('nowPlaying').style.opacity = '1';
            document.getElementById('currentTrackName').textContent = displayName;
            document.getElementById('currentTrackInfo').textContent = 'Playing...';
            document.getElementById('playBtn').textContent = '⏸';
        }

        function togglePlay() {
            if (!audioPlayer.src) {
                if (playlist.length > 0) {
                    playQueue();
                }
                return;
            }
            
            if (audioPlayer.paused) {
                audioPlayer.play().catch(e => console.error('Play error:', e));
                document.getElementById('playBtn').textContent = '⏸';
            } else {
                audioPlayer.pause();
                document.getElementById('playBtn').textContent = '▶';
            }
        }

        function changeSpeed(speed) {
            audioPlayer.playbackRate = parseFloat(speed);
            document.getElementById('speedDisplay').textContent = speed + 'x';
        }

        // Queue management
        function addToQueue(filename, name) {
            if (!filename) return;
            
            // Check if already in queue
            if (playlist.some(item => item.filename === filename)) {
                alert('Already in queue!');
                return;
            }
            
            playlist.push({filename, name});
            updateQueueDisplay();
            
            // Show brief notification
            const notification = document.createElement('div');
            notification.className = 'success-message';
            notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 2000; animation: slideIn 0.3s';
            notification.textContent = `✅ Added "${name}" to queue`;
            document.body.appendChild(notification);
            setTimeout(() => notification.remove(), 3000);
        }

        function updateQueueDisplay() {
            const badge = document.getElementById('queueBadge');
            const count = document.getElementById('queueCount');
            const list = document.getElementById('queueList');
            
            if (playlist.length > 0) {
                badge.style.display = 'block';
                badge.textContent = playlist.length;
                count.textContent = `${playlist.length} track${playlist.length !== 1 ? 's' : ''}`;
                
                list.innerHTML = playlist.map((item, i) => `
                    <div class="queue-item">
                        <div class="queue-number">${i + 1}</div>
                        <div class="queue-info">
                            <div class="queue-title">${escapeHtml(item.name)}</div>
                            <div class="queue-meta">${escapeHtml(item.filename)}</div>
                        </div>
                        <button class="control-btn" onclick="removeFromQueue(${i})">✕</button>
                    </div>
                `).join('');
            } else {
                badge.style.display = 'none';
                count.textContent = '0 tracks';
                list.innerHTML = '<div class="no-results" style="padding: 20px;">Your queue is empty. Add files from your library!</div>';
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function playQueue() {
            if (playlist.length > 0) {
                currentIndex = 0;
                playFile(playlist[0].filename);
            }
        }

        function nextTrack() {
            if (playlist.length === 0) return;
            
            if (currentIndex < playlist.length - 1) {
                currentIndex++;
                playFile(playlist[currentIndex].filename);
            }
        }

        function previousTrack() {
            if (playlist.length === 0) return;
            
            if (currentIndex > 0) {
                currentIndex--;
                playFile(playlist[currentIndex].filename);
            }
        }

        function clearQueue() {
            if (playlist.length > 0 && confirm('Clear all items from queue?')) {
                playlist = [];
                currentIndex = 0;
                updateQueueDisplay();
            }
        }

        function removeFromQueue(index) {
            playlist.splice(index, 1);
            if (currentIndex >= index && currentIndex > 0) {
                currentIndex--;
            }
            updateQueueDisplay();
        }

        // Auto-play next in queue
        audioPlayer.addEventListener('ended', () => {
            nextTrack();
        });

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

        // Search functionality
        // Debounce function for search
        let searchTimeout;
        function filterFiles() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const term = document.getElementById('searchInput').value.toLowerCase().trim();
                let found = false;

                document.querySelectorAll('.file-card').forEach(card => {
                    const name = (card.dataset.name || '').toLowerCase();
                    const group = (card.dataset.group || '').toLowerCase();
                    const filename = (card.dataset.filename || '').toLowerCase();

                    if (name.includes(term) || group.includes(term) || filename.includes(term)) {
                        card.style.display = '';
                        found = true;
                    } else {
                        card.style.display = 'none';
                    }
                });

                // Hide empty sections
                document.querySelectorAll('.files-grid').forEach(grid => {
                    const visibleCards = grid.querySelectorAll('.file-card:not([style*="display: none"])');
                    const section = grid.closest('div');
                    if (section && section.previousElementSibling && section.previousElementSibling.classList.contains('section-title')) {
                        section.previousElementSibling.style.display = visibleCards.length > 0 ? '' : 'none';
                    }
                });

                document.getElementById('noResults').style.display = found ? 'none' : 'block';
            }, 300); // Debounce for 300ms
        }

        // Sort functionality
        function sortFiles() {
            const sortBy = document.getElementById('sortSelect').value;
            const grids = document.querySelectorAll('.files-grid');
            
            grids.forEach(grid => {
                const cards = Array.from(grid.querySelectorAll('.file-card'));
                
                cards.sort((a, b) => {
                    const nameA = a.dataset.name || '';
                    const nameB = b.dataset.name || '';
                    const filenameA = a.dataset.filename || '';
                    const filenameB = b.dataset.filename || '';
                    
                    switch(sortBy) {
                        case 'name-asc':
                            return nameA.localeCompare(nameB);
                        case 'name-desc':
                            return nameB.localeCompare(nameA);
                        case 'oldest':
                            return filenameA.localeCompare(filenameB);
                        case 'recent':
                        default:
                            return filenameB.localeCompare(filenameA);
                    }
                });
                
                cards.forEach(card => grid.appendChild(card));
            });
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            
            switch(e.key) {
                case ' ':
                    e.preventDefault();
                    togglePlay();
                    break;
                case 'ArrowRight':
                    nextTrack();
                    break;
                case 'ArrowLeft':
                    previousTrack();
                    break;
                case 'Escape':
                    closeModal();
                    document.getElementById('contextMenu').classList.remove('active');
                    break;
            }
        });

        // Initialize on page load
        window.addEventListener('DOMContentLoaded', function() {
            {% if error or success %}
            showSection('create');
            {% endif %}
            
            // Set initial volume
            audioPlayer.volume = 1.0;
            document.getElementById('volumeFill').style.width = '100%';
        });

        // Add CSS animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
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
        # Check if text file was uploaded
        text = request.form.get('text', '').strip()
        if 'textfile' in request.files:
            file = request.files['textfile']
            if file and file.filename:
                try:
                    text = file.read().decode('utf-8').strip()
                except Exception as e:
                    error = f"Error reading uploaded file: {str(e)}"

        voice = validate_voice(request.form.get('voice', 'nova'))
        file_name = sanitize_display_name(request.form.get('filename', 'audio'))
        group = sanitize_display_name(request.form.get('group', 'Uncategorized'))[:50]

        if not text:
            error = "Please enter some text or upload a text file"
        elif len(text) > 4096:
            error = f"Text exceeds 4,096 character limit (current: {len(text)} characters)"
        elif not file_name:
            error = "Please enter a valid file name"
        else:
            try:
                client = get_openai_client()

                # Make API call with error handling
                try:
                    response = client.audio.speech.create(
                        model="tts-1",
                        voice=voice,
                        input=text,
                        speed=1.0
                    )
                except Exception as api_error:
                    error = f"OpenAI API Error: {str(api_error)}"
                    raise

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = secure_filename(f"{file_name}_{timestamp}.mp3")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)

                # Save audio file
                with open(filepath, 'wb') as f:
                    f.write(response.content)

                char_count = len(text)
                cost = calculate_cost(char_count)

                # Update metadata
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

                # Update usage
                usage = load_usage()
                usage['total_characters'] += char_count
                usage['total_cost'] += cost
                usage['files_generated'] += 1

                # Track monthly
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

                # Redirect to home after successful generation
                return redirect(url_for('index'))

            except ValueError as ve:
                error = str(ve)
            except Exception as e:
                if not error:  # Don't overwrite API error
                    error = f"An error occurred: {str(e)}"
                print(f"Error in audio generation: {e}")
    
    # Load files for display
    metadata = load_metadata()
    usage = load_usage()

    # Build file list with existence check
    all_files = [
        {
            'filename': html.escape(fname),
            'name': html.escape(data.get('name', fname)),
            'group': html.escape(data.get('group', 'Uncategorized')),
            'created': data.get('created', ''),
            'chars': data.get('characters', 0),
            'cost': data.get('cost', 0)
        }
        for fname, data in metadata.items()
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], fname))
    ]

    all_files.sort(key=lambda x: x['created'], reverse=True)
    recent_files = all_files[:10]
    
    # Group files
    grouped_files = defaultdict(list)
    for file in all_files:
        grouped_files[file['group']].append(file)
    
    # Prepare monthly chart data
    monthly_data = usage.get('monthly', {})
    months = sorted(monthly_data.keys(), reverse=True)[:6] if monthly_data else []

    monthly_chart = []
    if months:
        months.reverse()
        max_cost = max((monthly_data.get(m, {}).get('cost', 0) for m in months), default=0.01)

        for month in months:
            month_info = monthly_data.get(month, {})
            cost = month_info.get('cost', 0)
            percentage = min(100, (cost / max_cost * 100) if max_cost > 0 else 0)

            try:
                month_name = datetime.strptime(month, "%Y-%m").strftime("%b")
            except ValueError:
                month_name = month

            monthly_chart.append({
                'month': month_name,
                'cost': cost,
                'percentage': max(10, percentage)  # Minimum height for visibility
            })
    
    # Load playback history
    playback_history = load_history()

    return render_template_string(
        HTML_TEMPLATE,
        error=error,
        success=success,
        filename=filename,
        file_display_name=file_display_name,
        grouped_files=dict(grouped_files),
        recent_files=recent_files,
        usage=usage,
        monthly_chart=monthly_chart,
        batch_success=False,
        batch_count=0,
        podcast_success=False,
        podcast_error=None,
        playback_history=playback_history
    )

@app.route('/audio/<path:filename>')
def audio(filename):
    """Serve audio files with proper error handling and caching"""
    try:
        safe_filename = secure_filename(filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)

        if os.path.exists(filepath):
            response = send_file(filepath, mimetype='audio/mpeg')
            # Add cache headers for better performance
            response.headers['Cache-Control'] = 'public, max-age=31536000'
            return response
        else:
            return "File not found", 404
    except Exception as e:
        print(f"Error serving audio: {e}")
        return "Error serving file", 500

@app.route('/download/<path:filename>')
def download(filename):
    """Download audio files"""
    try:
        safe_filename = secure_filename(filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='audio/mpeg', as_attachment=True, download_name=safe_filename)
        else:
            return "File not found", 404
    except Exception as e:
        print(f"Error downloading: {e}")
        return "Error downloading file", 500

@app.route('/rename/<path:filename>', methods=['POST'])
def rename(filename):
    """Rename audio files"""
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
            else:
                return jsonify({'success': False, 'error': 'File not found'}), 404
        else:
            return jsonify({'success': False, 'error': 'Invalid name'}), 400

    except Exception as e:
        print(f"Error renaming: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete/<path:filename>', methods=['POST'])
def delete(filename):
    """Delete audio files with proper cleanup"""
    try:
        safe_filename = secure_filename(filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)

        # Update usage stats before deletion
        metadata = load_metadata()
        if safe_filename in metadata:
            file_info = metadata[safe_filename]
            usage = load_usage()

            # Safely update usage stats
            usage['total_characters'] = max(0, usage.get('total_characters', 0) - file_info.get('characters', 0))
            usage['total_cost'] = max(0, usage.get('total_cost', 0) - file_info.get('cost', 0))
            usage['files_generated'] = max(0, usage.get('files_generated', 1) - 1)

            # Update monthly stats
            created_timestamp = file_info.get('created', '')
            if created_timestamp:
                try:
                    file_month = datetime.strptime(created_timestamp, "%Y%m%d_%H%M%S").strftime("%Y-%m")
                    if file_month in usage.get('monthly', {}):
                        usage['monthly'][file_month]['cost'] = max(0, usage['monthly'][file_month].get('cost', 0) - file_info.get('cost', 0))
                        usage['monthly'][file_month]['files'] = max(0, usage['monthly'][file_month].get('files', 1) - 1)
                        usage['monthly'][file_month]['characters'] = max(0, usage['monthly'][file_month].get('characters', 0) - file_info.get('characters', 0))
                except ValueError:
                    pass  # Skip if timestamp format is invalid

            save_usage(usage)

            # Remove from metadata
            del metadata[safe_filename]
            save_metadata(metadata)

        # Delete the file if it exists
        if os.path.exists(filepath):
            os.remove(filepath)

        return redirect(url_for('index'))

    except Exception as e:
        print(f"Error deleting: {e}")
        return redirect(url_for('index'))

@app.route('/duplicate/<path:filename>', methods=['POST'])
def duplicate(filename):
    """Duplicate an audio file with all its metadata"""
    try:
        import shutil
        safe_filename = secure_filename(filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)

        if os.path.exists(filepath):
            metadata = load_metadata()
            if safe_filename in metadata:
                # Create new filename
                original_data = metadata[safe_filename]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_name = original_data.get('name', 'audio') + ' (Copy)'
                new_filename = secure_filename(f"{new_name}_{timestamp}.mp3")
                new_filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)

                # Copy the file
                shutil.copy2(filepath, new_filepath)

                # Copy metadata
                metadata[new_filename] = {
                    'name': new_name,
                    'group': original_data.get('group', 'Uncategorized'),
                    'created': timestamp,
                    'voice': original_data.get('voice', 'nova'),
                    'characters': original_data.get('characters', 0),
                    'cost': original_data.get('cost', 0)
                }
                save_metadata(metadata)

                # Update usage
                usage = load_usage()
                usage['total_characters'] += original_data.get('characters', 0)
                usage['total_cost'] += original_data.get('cost', 0)
                usage['files_generated'] += 1

                # Track monthly
                current_month = datetime.now().strftime("%Y-%m")
                if current_month not in usage.get('monthly', {}):
                    usage['monthly'][current_month] = {'cost': 0, 'files': 0, 'characters': 0}
                usage['monthly'][current_month]['cost'] += original_data.get('cost', 0)
                usage['monthly'][current_month]['files'] += 1
                usage['monthly'][current_month]['characters'] += original_data.get('characters', 0)

                save_usage(usage)

        return redirect(url_for('index'))

    except Exception as e:
        print(f"Error duplicating: {e}")
        return redirect(url_for('index'))

@app.route('/track', methods=['POST'])
def track_playback():
    """Track audio playback for history"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        display_name = data.get('name', filename)

        if filename:
            add_to_history(filename, display_name)
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'No filename provided'}), 400
    except Exception as e:
        print(f"Error tracking playback: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/clear-history', methods=['POST'])
def clear_playback_history():
    """Clear all playback history"""
    try:
        save_history([])
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error clearing history: {e}")
        return redirect(url_for('index'))

@app.route('/preview', methods=['POST'])
def voice_preview():
    """Generate voice preview samples"""
    try:
        data = request.get_json()
        voice = validate_voice(data.get('voice', 'nova'))
        text = data.get('text', 'This is a voice preview sample.')[:200]  # Limit preview text

        client = get_openai_client()

        # Generate preview audio
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=1.0
        )

        # Return audio directly as response
        audio_io = io.BytesIO(response.content)
        audio_io.seek(0)
        return send_file(audio_io, mimetype='audio/mpeg')

    except Exception as e:
        print(f"Error generating preview: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/podcast', methods=['POST'])
def podcast_generate():
    """Generate a single continuous podcast audio from multiple text segments"""
    try:
        podcast_title = sanitize_display_name(request.form.get('podcast_title', 'Podcast'))
        voice = validate_voice(request.form.get('voice', 'nova'))
        group = sanitize_display_name(request.form.get('group', 'Podcasts'))[:50]
        podcast_segments = request.form.get('podcast_segments', '').strip()

        if not podcast_segments:
            return render_template_string(
                HTML_TEMPLATE,
                error=None,
                success=False,
                podcast_error="Please enter podcast segments",
                podcast_success=False,
                grouped_files={},
                recent_files=[],
                usage=load_usage(),
                monthly_chart=[],
                batch_success=False,
                batch_count=0,
                playback_history=load_history()
            )

        # Combine all segments with appropriate spacing
        combined_text = podcast_segments.strip()

        # Check total length
        if len(combined_text) > 4096:
            return render_template_string(
                HTML_TEMPLATE,
                error=None,
                success=False,
                podcast_error=f"Total text exceeds 4,096 character limit (current: {len(combined_text)} characters). Please shorten your segments.",
                podcast_success=False,
                grouped_files={},
                recent_files=[],
                usage=load_usage(),
                monthly_chart=[],
                batch_success=False,
                batch_count=0,
                playback_history=load_history()
            )

        try:
            client = get_openai_client()

            # Generate single audio file from combined text
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=combined_text,
                speed=1.0
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = secure_filename(f"{podcast_title}_{timestamp}.mp3")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)

            # Save audio file
            with open(filepath, 'wb') as f:
                f.write(response.content)

            char_count = len(combined_text)
            cost = calculate_cost(char_count)

            # Update metadata
            metadata = load_metadata()
            metadata[safe_filename] = {
                'name': podcast_title,
                'group': group,
                'created': timestamp,
                'voice': voice,
                'characters': char_count,
                'cost': cost
            }
            save_metadata(metadata)

            # Update usage
            usage = load_usage()
            usage['total_characters'] += char_count
            usage['total_cost'] += cost
            usage['files_generated'] += 1

            # Track monthly
            current_month = datetime.now().strftime("%Y-%m")
            if current_month not in usage['monthly']:
                usage['monthly'][current_month] = {'cost': 0, 'files': 0, 'characters': 0}
            usage['monthly'][current_month]['cost'] += cost
            usage['monthly'][current_month]['files'] += 1
            usage['monthly'][current_month]['characters'] += char_count

            save_usage(usage)

            # Load files for display
            all_files = [
                {
                    'filename': html.escape(fname),
                    'name': html.escape(data.get('name', fname)),
                    'group': html.escape(data.get('group', 'Uncategorized')),
                    'created': data.get('created', ''),
                    'chars': data.get('characters', 0),
                    'cost': data.get('cost', 0)
                }
                for fname, data in metadata.items()
                if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            ]

            all_files.sort(key=lambda x: x['created'], reverse=True)
            recent_files = all_files[:10]

            # Group files
            grouped_files = defaultdict(list)
            for file in all_files:
                grouped_files[file['group']].append(file)

            # Prepare monthly chart data
            monthly_data = usage.get('monthly', {})
            months = sorted(monthly_data.keys(), reverse=True)[:6] if monthly_data else []

            monthly_chart = []
            if months:
                months.reverse()
                max_cost = max((monthly_data.get(m, {}).get('cost', 0) for m in months), default=0.01)

                for month in months:
                    month_info = monthly_data.get(month, {})
                    cost_val = month_info.get('cost', 0)
                    percentage = min(100, (cost_val / max_cost * 100) if max_cost > 0 else 0)

                    try:
                        month_name = datetime.strptime(month, "%Y-%m").strftime("%b")
                    except ValueError:
                        month_name = month

                    monthly_chart.append({
                        'month': month_name,
                        'cost': cost_val,
                        'percentage': max(10, percentage)
                    })

            return render_template_string(
                HTML_TEMPLATE,
                error=None,
                success=False,
                podcast_error=None,
                podcast_success=True,
                podcast_filename=podcast_title,
                grouped_files=dict(grouped_files),
                recent_files=recent_files,
                usage=usage,
                monthly_chart=monthly_chart,
                batch_success=False,
                batch_count=0,
                playback_history=load_history()
            )

        except Exception as e:
            print(f"Error generating podcast: {e}")
            return render_template_string(
                HTML_TEMPLATE,
                error=None,
                success=False,
                podcast_error=f"Failed to generate podcast: {str(e)}",
                podcast_success=False,
                grouped_files={},
                recent_files=[],
                usage=load_usage(),
                monthly_chart=[],
                batch_success=False,
                batch_count=0,
                playback_history=load_history()
            )

    except Exception as e:
        print(f"Error in podcast generation: {e}")
        return render_template_string(
            HTML_TEMPLATE,
            error=None,
            success=False,
            podcast_error=f"An error occurred: {str(e)}",
            podcast_success=False,
            grouped_files={},
            recent_files=[],
            usage=load_usage(),
            monthly_chart=[],
            batch_success=False,
            batch_count=0,
            playback_history=load_history()
        )

@app.route('/edit/<path:filename>', methods=['POST'])
def edit_file(filename):
    """Edit and regenerate audio file"""
    try:
        data = request.get_json()
        new_text = data.get('text', '').strip()
        voice = validate_voice(data.get('voice', 'nova'))

        if not new_text or len(new_text) > 4096:
            return jsonify({'success': False, 'error': 'Invalid text'}), 400

        safe_filename = secure_filename(filename)
        metadata = load_metadata()

        if safe_filename not in metadata:
            return jsonify({'success': False, 'error': 'File not found'}), 404

        # Generate new audio
        client = get_openai_client()
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=new_text,
            speed=1.0
        )

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)

        # Update metadata
        char_count = len(new_text)
        cost = calculate_cost(char_count)
        metadata[safe_filename]['voice'] = voice
        metadata[safe_filename]['characters'] = char_count
        metadata[safe_filename]['cost'] = cost
        save_metadata(metadata)

        return jsonify({'success': True})
    except Exception as e:
        print(f"Error editing file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/add-picture/<path:filename>', methods=['POST'])
def add_picture(filename):
    """Add picture to audio file"""
    try:
        safe_filename = secure_filename(filename)
        metadata = load_metadata()

        if safe_filename not in metadata:
            return jsonify({'success': False, 'error': 'File not found'}), 404

        if 'picture' not in request.files:
            return jsonify({'success': False, 'error': 'No picture uploaded'}), 400

        picture = request.files['picture']
        if picture.filename:
            # Save picture
            picture_filename = secure_filename(f"pic_{safe_filename}.{picture.filename.rsplit('.', 1)[1]}")
            picture_path = os.path.join(app.config['UPLOAD_FOLDER'], picture_filename)
            picture.save(picture_path)

            # Update metadata
            metadata[safe_filename]['picture'] = picture_filename
            save_metadata(metadata)

            return jsonify({'success': True})

        return jsonify({'success': False, 'error': 'Invalid picture'}), 400
    except Exception as e:
        print(f"Error adding picture: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/albums', methods=['GET'])
def get_albums():
    """Get list of albums"""
    try:
        metadata = load_metadata()
        albums = set()
        for data in metadata.values():
            if 'album' in data and data['album']:
                albums.add(data['album'])
        return jsonify({'albums': sorted(list(albums))})
    except Exception as e:
        print(f"Error getting albums: {e}")
        return jsonify({'albums': []}), 500

@app.route('/add-to-album/<path:filename>', methods=['POST'])
def add_to_album(filename):
    """Add file to album"""
    try:
        data = request.get_json()
        album = sanitize_display_name(data.get('album', ''))

        if not album:
            return jsonify({'success': False, 'error': 'Invalid album name'}), 400

        safe_filename = secure_filename(filename)
        metadata = load_metadata()

        if safe_filename not in metadata:
            return jsonify({'success': False, 'error': 'File not found'}), 404

        metadata[safe_filename]['album'] = album
        save_metadata(metadata)

        return jsonify({'success': True})
    except Exception as e:
        print(f"Error adding to album: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/merge', methods=['POST'])
def merge_files():
    """Merge multiple audio files into one"""
    try:
        data = request.get_json()
        title = sanitize_display_name(data.get('title', 'Merged Audio'))
        files = data.get('files', [])

        if len(files) < 2:
            return jsonify({'success': False, 'error': 'Need at least 2 files'}), 400

        # This is a simple implementation - for production, you'd use an audio library like pydub
        # For now, we'll just concatenate the MP3 files (works for most MP3s)
        import subprocess

        # Create list of input files
        input_files = []
        for f in files:
            safe_f = secure_filename(f)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_f)
            if os.path.exists(filepath):
                input_files.append(filepath)

        if len(input_files) < 2:
            return jsonify({'success': False, 'error': 'Some files not found'}), 404

        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = secure_filename(f"{title}_{timestamp}.mp3")
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        # Concatenate audio files using ffmpeg (if available)
        try:
            # Create concat file
            concat_file = os.path.join(app.config['UPLOAD_FOLDER'], f'concat_{timestamp}.txt')
            with open(concat_file, 'w') as f:
                for input_file in input_files:
                    f.write(f"file '{input_file}'\n")

            subprocess.run([
                'ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file,
                '-c', 'copy', output_path
            ], check=True, capture_output=True)

            os.remove(concat_file)

            # Calculate metadata
            metadata = load_metadata()
            total_chars = sum(metadata.get(secure_filename(f), {}).get('characters', 0) for f in files)
            total_cost = sum(metadata.get(secure_filename(f), {}).get('cost', 0) for f in files)

            metadata[output_filename] = {
                'name': title,
                'group': 'Merged',
                'created': timestamp,
                'voice': 'merged',
                'characters': total_chars,
                'cost': total_cost
            }
            save_metadata(metadata)

            return jsonify({'success': True})
        except (subprocess.CalledProcessError, FileNotFoundError):
            # If ffmpeg not available, fall back to simple concatenation
            with open(output_path, 'wb') as outfile:
                for input_file in input_files:
                    with open(input_file, 'rb') as infile:
                        outfile.write(infile.read())

            # Calculate metadata
            metadata = load_metadata()
            total_chars = sum(metadata.get(secure_filename(f), {}).get('characters', 0) for f in files)
            total_cost = sum(metadata.get(secure_filename(f), {}).get('cost', 0) for f in files)

            metadata[output_filename] = {
                'name': title,
                'group': 'Merged',
                'created': timestamp,
                'voice': 'merged',
                'characters': total_chars,
                'cost': total_cost
            }
            save_metadata(metadata)

            return jsonify({'success': True})

    except Exception as e:
        print(f"Error merging files: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/batch', methods=['POST'])
def batch_generate():
    """Generate multiple audio files from batch input"""
    try:
        batch_texts = request.form.get('batch_texts', '').strip()
        voice = validate_voice(request.form.get('voice', 'nova'))
        group = sanitize_display_name(request.form.get('group', 'Uncategorized'))[:50]

        if not batch_texts:
            return render_template_string(
                HTML_TEMPLATE,
                error="Please enter batch texts",
                grouped_files={},
                recent_files=[],
                usage=load_usage(),
                monthly_chart=[],
                batch_success=False,
                batch_count=0
            )

        # Parse batch input
        lines = [line.strip() for line in batch_texts.split('\n') if line.strip()]
        if not lines:
            return render_template_string(
                HTML_TEMPLATE,
                error="No valid lines found in batch input",
                grouped_files={},
                recent_files=[],
                usage=load_usage(),
                monthly_chart=[],
                batch_success=False,
                batch_count=0
            )

        generated_count = 0
        client = get_openai_client()
        metadata = load_metadata()
        usage = load_usage()
        current_month = datetime.now().strftime("%Y-%m")

        # Initialize monthly stats if needed
        if current_month not in usage['monthly']:
            usage['monthly'][current_month] = {'cost': 0, 'files': 0, 'characters': 0}

        for line in lines:
            # Parse line: filename|text
            parts = line.split('|', 1)
            if len(parts) < 2:
                continue  # Skip invalid lines

            file_name = sanitize_display_name(parts[0])
            text = parts[1].strip()

            if not text or len(text) > 4096:
                continue  # Skip empty or too long texts

            try:
                # Generate audio
                response = client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=text,
                    speed=1.0
                )

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = secure_filename(f"{file_name}_{timestamp}.mp3")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)

                # Save audio file
                with open(filepath, 'wb') as f:
                    f.write(response.content)

                char_count = len(text)
                cost = calculate_cost(char_count)

                # Update metadata
                metadata[safe_filename] = {
                    'name': file_name,
                    'group': group,
                    'created': timestamp,
                    'voice': voice,
                    'characters': char_count,
                    'cost': cost
                }

                # Update usage
                usage['total_characters'] += char_count
                usage['total_cost'] += cost
                usage['files_generated'] += 1
                usage['monthly'][current_month]['cost'] += cost
                usage['monthly'][current_month]['files'] += 1
                usage['monthly'][current_month]['characters'] += char_count

                generated_count += 1

            except Exception as e:
                print(f"Error generating audio for '{file_name}': {e}")
                continue  # Skip this file and continue with others

        # Save updated metadata and usage
        save_metadata(metadata)
        save_usage(usage)

        # Load files for display
        all_files = [
            {
                'filename': html.escape(fname),
                'name': html.escape(data.get('name', fname)),
                'group': html.escape(data.get('group', 'Uncategorized')),
                'created': data.get('created', ''),
                'chars': data.get('characters', 0),
                'cost': data.get('cost', 0)
            }
            for fname, data in metadata.items()
            if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], fname))
        ]

        all_files.sort(key=lambda x: x['created'], reverse=True)
        recent_files = all_files[:10]

        # Group files
        grouped_files = defaultdict(list)
        for file in all_files:
            grouped_files[file['group']].append(file)

        # Prepare monthly chart data
        monthly_data = usage.get('monthly', {})
        months = sorted(monthly_data.keys(), reverse=True)[:6] if monthly_data else []

        monthly_chart = []
        if months:
            months.reverse()
            max_cost = max((monthly_data.get(m, {}).get('cost', 0) for m in months), default=0.01)

            for month in months:
                month_info = monthly_data.get(month, {})
                cost = month_info.get('cost', 0)
                percentage = min(100, (cost / max_cost * 100) if max_cost > 0 else 0)

                try:
                    month_name = datetime.strptime(month, "%Y-%m").strftime("%b")
                except ValueError:
                    month_name = month

                monthly_chart.append({
                    'month': month_name,
                    'cost': cost,
                    'percentage': max(10, percentage)
                })

        return render_template_string(
            HTML_TEMPLATE,
            error=None,
            success=False,
            filename=None,
            file_display_name=None,
            grouped_files=dict(grouped_files),
            recent_files=recent_files,
            usage=usage,
            monthly_chart=monthly_chart,
            batch_success=True,
            batch_count=generated_count
        )

    except Exception as e:
        print(f"Error in batch generation: {e}")
        return render_template_string(
            HTML_TEMPLATE,
            error=f"Batch generation error: {str(e)}",
            grouped_files={},
            recent_files=[],
            usage=load_usage(),
            monthly_chart=[],
            batch_success=False,
            batch_count=0
        )

@app.route('/stream-generate', methods=['POST'])
def stream_generate():
    """Generate audio with streaming - plays chunks as they're generated"""
    def generate_audio_stream():
        try:
            data = request.get_json()
            text = data.get('text', '').strip()
            voice = validate_voice(data.get('voice', 'nova'))
            file_name = sanitize_display_name(data.get('filename', 'audio'))
            group = sanitize_display_name(data.get('group', 'Uncategorized'))[:50]

            if not text:
                yield f"data: {json.dumps({'error': 'No text provided'})}\n\n"
                return

            if len(text) > 4096:
                yield f"data: {json.dumps({'error': f'Text exceeds 4,096 character limit (current: {len(text)} characters)'})}\n\n"
                return

            client = get_openai_client()

            # Split text into chunks for streaming feel (800-1000 chars)
            chunk_size = 900
            text_chunks = []
            words = text.split()
            current_chunk = []
            current_length = 0

            for word in words:
                word_len = len(word) + 1  # +1 for space
                if current_length + word_len > chunk_size and current_chunk:
                    text_chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                    current_length = word_len
                else:
                    current_chunk.append(word)
                    current_length += word_len

            if current_chunk:
                text_chunks.append(' '.join(current_chunk))

            # Generate audio chunks
            audio_parts = []
            total_chars = 0

            for i, chunk_text in enumerate(text_chunks):
                yield f"data: {json.dumps({'progress': i + 1, 'total': len(text_chunks), 'status': f'Generating part {i+1} of {len(text_chunks)}...'})}\n\n"

                response = client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=chunk_text,
                    speed=1.0
                )

                audio_data = response.content
                audio_parts.append(audio_data)
                total_chars += len(chunk_text)

                # Stream this chunk immediately
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                yield f"data: {json.dumps({'chunk': audio_base64, 'chunk_number': i, 'status': f'Playing part {i+1}...'})}\n\n"

            # Combine all audio parts
            full_audio = b''.join(audio_parts)

            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = secure_filename(f"{file_name}_{timestamp}.mp3")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)

            with open(filepath, 'wb') as f:
                f.write(full_audio)

            # Update metadata and usage
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

            yield f"data: {json.dumps({'complete': True, 'filename': safe_filename, 'display_name': file_name, 'status': 'Complete!'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(stream_with_context(generate_audio_stream()), mimetype='text/event-stream')

@app.route('/quick-generate', methods=['POST'])
def quick_generate():
    """Generate audio instantly without saving - for quick listening"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        voice = validate_voice(data.get('voice', 'nova'))

        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400

        if len(text) > 4096:
            return jsonify({'success': False, 'error': f'Text exceeds 4,096 character limit (current: {len(text)} characters)'}), 400

        client = get_openai_client()

        # Generate audio
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=1.0
        )

        # Return audio as base64 for immediate playback
        audio_data = response.content
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        return jsonify({
            'success': True,
            'audio': audio_base64,
            'voice': voice,
            'characters': len(text)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY environment variable is not set!")
        print("Please set it using: export OPENAI_API_KEY='your-api-key-here'")
        print("")

    print("🌌 Starting VoiceVerse - Text-to-Speech Application")
    print("📍 Open in your browser: http://localhost:5000")
    print("Press Ctrl+C to stop the server\n")

    app.run(debug=True, port=5000, host='0.0.0.0')
