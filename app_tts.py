from flask import Flask, render_template_string, request, send_file, redirect, url_for, jsonify
import os
from openai import OpenAI
import io
from datetime import datetime
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'saved_audio'

# Create folder for saved files
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Metadata file for file organization
METADATA_FILE = os.path.join(app.config['UPLOAD_FOLDER'], 'metadata.json')
USAGE_FILE = os.path.join(app.config['UPLOAD_FOLDER'], 'usage_stats.json')

def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_metadata(metadata):
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def load_usage():
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, 'r') as f:
            return json.load(f)
    return {'total_characters': 0, 'total_cost': 0, 'files_generated': 0}

def save_usage(usage):
    with open(USAGE_FILE, 'w') as f:
        json.dump(usage, f, indent=2)

def calculate_cost(characters):
    # OpenAI TTS pricing: $0.015 per 1000 characters
    return (characters / 1000) * 0.015

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Text-to-Speech Pro</title>
    <style>
        :root {
            --bg-primary: #f5f5f5;
            --bg-secondary: white;
            --text-primary: #333;
            --text-secondary: #666;
            --border-color: #ddd;
            --button-bg: #007bff;
            --button-hover: #0056b3;
            --success-bg: #e8f5e9;
            --success-border: #4caf50;
            --error-bg: #ffebee;
            --error-border: #f44336;
            --shadow: rgba(0,0,0,0.1);
            --sidebar-bg: white;
            --accent: #007bff;
        }

        body.dark-theme {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --text-primary: #e0e0e0;
            --text-secondary: #b0b0b0;
            --border-color: #444;
            --button-bg: #0d6efd;
            --button-hover: #0b5ed7;
            --success-bg: #1b5e20;
            --success-border: #4caf50;
            --error-bg: #b71c1c;
            --error-border: #f44336;
            --shadow: rgba(0,0,0,0.3);
            --sidebar-bg: #2d2d2d;
            --accent: #0d6efd;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            transition: background 0.3s, color 0.3s;
            display: flex;
            height: 100vh;
        }

        .sidebar {
            width: 300px;
            background: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }

        .sidebar h2 {
            margin-bottom: 15px;
            font-size: 18px;
            color: var(--text-primary);
        }

        .stats-panel {
            background: var(--bg-primary);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        .stat-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 13px;
        }

        .stat-label {
            color: var(--text-secondary);
        }

        .stat-value {
            font-weight: 600;
            color: var(--accent);
        }

        .search-box {
            margin-bottom: 15px;
        }

        .search-box input {
            width: 100%;
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            font-size: 14px;
        }

        .sort-box {
            margin-bottom: 15px;
        }

        .sort-box select {
            width: 100%;
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            font-size: 14px;
        }

        .new-file-btn {
            background: var(--button-bg);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            margin-bottom: 20px;
            transition: background 0.3s;
        }

        .new-file-btn:hover {
            background: var(--button-hover);
        }

        .file-list {
            flex: 1;
        }

        .file-group {
            margin-bottom: 20px;
        }

        .group-header {
            font-weight: 600;
            color: var(--text-secondary);
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 8px;
            padding: 4px 0;
            display: flex;
            justify-content: space-between;
        }

        .file-count {
            color: var(--text-secondary);
            font-weight: normal;
        }

        .file-item {
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 4px;
            cursor: pointer;
            transition: background 0.2s;
        }

        .file-item:hover {
            background: var(--bg-primary);
        }

        .file-item.active {
            background: var(--button-bg);
            color: white;
        }

        .file-item.recent {
            border-left: 3px solid var(--accent);
        }

        .file-name {
            font-size: 14px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin-bottom: 4px;
        }

        .file-meta {
            font-size: 11px;
            color: var(--text-secondary);
            display: flex;
            justify-content: space-between;
        }

        .context-menu {
            position: fixed;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            box-shadow: 0 4px 12px var(--shadow);
            padding: 4px 0;
            z-index: 1000;
            display: none;
        }

        .context-menu.active {
            display: block;
        }

        .context-menu-item {
            padding: 10px 20px;
            cursor: pointer;
            color: var(--text-primary);
            transition: background 0.2s;
            white-space: nowrap;
        }

        .context-menu-item:hover {
            background: var(--bg-primary);
        }

        .context-menu-item.danger:hover {
            background: var(--error-bg);
            color: var(--error-border);
        }

        .main-content {
            flex: 1;
            padding: 40px;
            overflow-y: auto;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: var(--bg-secondary);
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 2px 10px var(--shadow);
            position: relative;
        }

        .theme-toggle {
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--border-color);
            border: none;
            border-radius: 12px;
            width: 48px;
            height: 24px;
            cursor: pointer;
            transition: all 0.3s;
            padding: 0;
            z-index: 1001;
        }

        .theme-toggle::after {
            content: '';
            position: absolute;
            top: 2px;
            left: 2px;
            width: 20px;
            height: 20px;
            background: white;
            border-radius: 50%;
            transition: all 0.3s;
        }

        body.dark-theme .theme-toggle {
            background: var(--button-bg);
        }

        body.dark-theme .theme-toggle::after {
            transform: translateX(24px);
        }

        .theme-toggle:hover {
            opacity: 0.8;
        }

        h1 {
            color: var(--text-primary);
            margin-bottom: 10px;
        }

        .subtitle {
            color: var(--text-secondary);
            margin-bottom: 30px;
        }

        label {
            display: block;
            margin-top: 20px;
            margin-bottom: 8px;
            font-weight: 600;
            color: var(--text-primary);
        }

        input[type="text"], select, textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            font-size: 14px;
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        textarea {
            resize: vertical;
            font-family: inherit;
        }

        .char-count {
            text-align: right;
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 5px;
            display: flex;
            justify-content: space-between;
        }

        .cost-estimate {
            color: var(--accent);
        }

        .warning {
            color: #ff6b6b;
            font-weight: 600;
        }

        button[type="submit"] {
            margin-top: 20px;
            padding: 14px 28px;
            background: var(--button-bg);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
        }

        button[type="submit"]:hover {
            background: var(--button-hover);
        }

        button[type="submit"]:disabled {
            background: #ccc;
            cursor: not-allowed;
        }

        .result {
            margin-top: 30px;
            padding: 20px;
            background: var(--success-bg);
            border-radius: 6px;
            border-left: 4px solid var(--success-border);
        }

        .error {
            background: var(--error-bg);
            border-left-color: var(--error-border);
        }

        .audio-player {
            margin-top: 15px;
        }

        audio {
            width: 100%;
            margin-bottom: 10px;
        }

        .speed-control {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 10px;
        }

        .speed-control label {
            margin: 0;
            font-size: 13px;
            min-width: 80px;
        }

        .speed-control input[type="range"] {
            flex: 1;
            padding: 0;
        }

        .speed-value {
            min-width: 40px;
            text-align: right;
            font-weight: 600;
            font-size: 13px;
        }

        .no-results {
            text-align: center;
            color: var(--text-secondary);
            padding: 20px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>📁 My Audio Files</h2>
        
        <div class="stats-panel">
            <div class="stat-item">
                <span class="stat-label">Total Files:</span>
                <span class="stat-value">{{ usage.files_generated }}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Characters Used:</span>
                <span class="stat-value">{{ "{:,}".format(usage.total_characters) }}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Total Cost:</span>
                <span class="stat-value">${{ "%.4f"|format(usage.total_cost) }}</span>
            </div>
        </div>
        
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 Search files..." onkeyup="filterFiles()">
        </div>
        
        <div class="sort-box">
            <select id="sortSelect" onchange="sortFiles()">
                <option value="recent">Sort by: Recent First</option>
                <option value="oldest">Sort by: Oldest First</option>
                <option value="name-asc">Sort by: Name (A-Z)</option>
                <option value="name-desc">Sort by: Name (Z-A)</option>
                <option value="group">Sort by: Group</option>
            </select>
        </div>
        
        <button class="new-file-btn" onclick="window.location.href='/'">➕ New File</button>
        
        <div class="file-list" id="fileList">
            {% if recent_files %}
            <div class="file-group">
                <div class="group-header">
                    <span>⭐ Recent</span>
                    <span class="file-count">({{ recent_files|length }})</span>
                </div>
                {% for file in recent_files %}
                <div class="file-item recent" data-filename="{{ file.filename }}" data-name="{{ file.name }}" data-group="{{ file.group }}" data-date="{{ file.created }}" oncontextmenu="showContextMenu(event, '{{ file.filename }}')">
                    <div class="file-name">{{ file.name }}</div>
                    <div class="file-meta">
                        <span>{{ file.chars }} chars</span>
                        <span>${{ "%.4f"|format(file.cost) }}</span>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% for group, files in grouped_files.items() %}
            <div class="file-group" data-group="{{ group }}">
                <div class="group-header">
                    <span>{{ group }}</span>
                    <span class="file-count">({{ files|length }})</span>
                </div>
                {% for file in files %}
                <div class="file-item" data-filename="{{ file.filename }}" data-name="{{ file.name }}" data-group="{{ group }}" data-date="{{ file.created }}" oncontextmenu="showContextMenu(event, '{{ file.filename }}')">
                    <div class="file-name">{{ file.name }}</div>
                    <div class="file-meta">
                        <span>{{ file.chars }} chars</span>
                        <span>${{ "%.4f"|format(file.cost) }}</span>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endfor %}
            
            <div class="no-results" id="noResults" style="display: none;">
                No files found
            </div>
        </div>
    </div>

    <div class="context-menu" id="contextMenu">
        <div class="context-menu-item" onclick="contextPlay()">Play</div>
        <div class="context-menu-item" onclick="contextDownload()">Download</div>
        <div class="context-menu-item danger" onclick="contextDelete()">Delete</div>
    </div>

    <button class="theme-toggle" id="themeToggle" onclick="toggleTheme()" aria-label="Toggle theme"></button>

    <div class="main-content">
        <div class="container">
            <h1>🎙️ AI Text-to-Speech Pro</h1>
            <p class="subtitle">Convert your text to high-quality speech using OpenAI's voices</p>
            
            <form method="POST" id="ttsForm">
                <label for="filename">File Name:</label>
                <input type="text" name="filename" id="filename" placeholder="My Audio File" required>
                
                <label for="group">Group:</label>
                <input type="text" name="group" id="group" placeholder="e.g., Work, Personal, Projects" value="Uncategorized">
                
                <label for="voice">Select a voice:</label>
                <select name="voice" id="voice" required>
                    <option value="alloy">Alloy (Neutral, balanced)</option>
                    <option value="echo">Echo (Male, clear)</option>
                    <option value="fable">Fable (British, expressive)</option>
                    <option value="onyx">Onyx (Deep, authoritative)</option>
                    <option value="nova" selected>Nova (Female, friendly)</option>
                    <option value="shimmer">Shimmer (Soft, warm)</option>
                </select>
                
                <label for="text">Enter your text:</label>
                <textarea name="text" id="text" rows="8" placeholder="Type or paste your text here..." required></textarea>
                <div class="char-count" id="charCount">
                    <span>Characters: <span id="charNum">0</span> / 4,096</span>
                    <span class="cost-estimate">Estimated cost: $<span id="costNum">0.0000</span></span>
                </div>
                
                <button type="submit" id="submitBtn">🎤 Generate Speech</button>
            </form>
            
            {% if error %}
            <div class="result error">
                <strong>❌ Error:</strong> {{ error }}
            </div>
            {% endif %}
            
            {% if success %}
            <div class="result">
                <strong>✓ Speech generated and saved successfully!</strong>
                <div class="audio-player">
                    <audio id="audioPlayer" controls src="/audio/{{ filename }}" preload="auto"></audio>
                    <div class="speed-control">
                        <label>Playback Speed:</label>
                        <input type="range" id="speedSlider" min="0.5" max="2" step="0.1" value="1" oninput="updateSpeed()">
                        <span class="speed-value" id="speedValue">1.0x</span>
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
    </div>
    
    <script>
        let currentFilename = null;
        let allFiles = [];
        
        // Collect all files on page load
        window.addEventListener('DOMContentLoaded', function() {
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'dark') {
                document.body.classList.add('dark-theme');
            }
            
            // Collect file data
            document.querySelectorAll('.file-item').forEach(item => {
                allFiles.push({
                    element: item,
                    filename: item.dataset.filename,
                    name: item.dataset.name,
                    group: item.dataset.group,
                    date: item.dataset.date
                });
            });
        });
        
        // Theme toggle
        function toggleTheme() {
            document.body.classList.toggle('dark-theme');
            const isDark = document.body.classList.contains('dark-theme');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        }
        
        // Search functionality
        function filterFiles() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            let visibleCount = 0;
            
            document.querySelectorAll('.file-group').forEach(group => {
                let groupHasVisible = false;
                group.querySelectorAll('.file-item').forEach(item => {
                    const name = item.dataset.name.toLowerCase();
                    if (name.includes(searchTerm)) {
                        item.style.display = 'block';
                        groupHasVisible = true;
                        visibleCount++;
                    } else {
                        item.style.display = 'none';
                    }
                });
                group.style.display = groupHasVisible ? 'block' : 'none';
            });
            
            document.getElementById('noResults').style.display = visibleCount === 0 ? 'block' : 'none';
        }
        
        // Sort functionality
        function sortFiles() {
            const sortBy = document.getElementById('sortSelect').value;
            const fileList = document.getElementById('fileList');
            const groups = Array.from(document.querySelectorAll('.file-group')).filter(g => !g.querySelector('.recent'));
            
            if (sortBy === 'recent' || sortBy === 'oldest') {
                const items = Array.from(document.querySelectorAll('.file-item')).filter(i => !i.classList.contains('recent'));
                items.sort((a, b) => {
                    const dateA = a.dataset.date;
                    const dateB = b.dataset.date;
                    return sortBy === 'recent' ? dateB.localeCompare(dateA) : dateA.localeCompare(dateB);
                });
                
                // Clear groups except recent
                groups.forEach(g => g.remove());
                
                // Create single "All Files" group
                const allGroup = document.createElement('div');
                allGroup.className = 'file-group';
                allGroup.innerHTML = '<div class="group-header"><span>All Files</span><span class="file-count">(' + items.length + ')</span></div>';
                items.forEach(item => allGroup.appendChild(item));
                fileList.appendChild(allGroup);
                
            } else if (sortBy === 'name-asc' || sortBy === 'name-desc') {
                groups.forEach(group => {
                    const items = Array.from(group.querySelectorAll('.file-item'));
                    items.sort((a, b) => {
                        const nameA = a.dataset.name.toLowerCase();
                        const nameB = b.dataset.name.toLowerCase();
                        return sortBy === 'name-asc' ? nameA.localeCompare(nameB) : nameB.localeCompare(nameA);
                    });
                    items.forEach(item => group.appendChild(item));
                });
            }
        }
        
        // Context menu
        function showContextMenu(event, filename) {
            event.preventDefault();
            currentFilename = filename;
            
            const contextMenu = document.getElementById('contextMenu');
            contextMenu.style.left = event.pageX + 'px';
            contextMenu.style.top = event.pageY + 'px';
            contextMenu.classList.add('active');
        }
        
        document.addEventListener('click', function() {
            document.getElementById('contextMenu').classList.remove('active');
        });
        
        function contextPlay() {
            if (currentFilename) {
                const audio = new Audio(`/audio/${currentFilename}`);
                audio.play();
            }
        }
        
        function contextDownload() {
            if (currentFilename) {
                window.location.href = `/download/${currentFilename}`;
            }
        }
        
        function contextDelete() {
            if (currentFilename && confirm('Are you sure you want to delete this file?')) {
                fetch(`/delete/${currentFilename}`, {method: 'POST'})
                    .then(() => window.location.reload());
            }
        }
        
        // Character counter with cost estimate
        const textarea = document.getElementById('text');
        const charNum = document.getElementById('charNum');
        const costNum = document.getElementById('costNum');
        const submitBtn = document.getElementById('submitBtn');
        
        textarea.addEventListener('input', function() {
            const length = this.value.length;
            charNum.textContent = length;
            
            // Calculate cost
            const cost = (length / 1000) * 0.015;
            costNum.textContent = cost.toFixed(4);
            
            if (length > 4096) {
                charNum.parentElement.classList.add('warning');
                submitBtn.disabled = true;
            } else {
                charNum.parentElement.classList.remove('warning');
                submitBtn.disabled = false;
            }
        });
        
        // Speed control
        function updateSpeed() {
            const slider = document.getElementById('speedSlider');
            const speedValue = document.getElementById('speedValue');
            const audio = document.getElementById('audioPlayer');
            
            if (audio) {
                audio.playbackRate = slider.value;
                speedValue.textContent = slider.value + 'x';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    success = False
    filename = None
    
    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        voice = request.form.get('voice', 'nova')
        file_name = request.form.get('filename', 'audio').strip()
        group = request.form.get('group', 'Uncategorized').strip()
        
        if not text:
            error = "Please enter some text"
        elif len(text) > 4096:
            error = "Text exceeds 4,096 character limit"
        elif not file_name:
            error = "Please enter a file name"
        else:
            try:
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    error = "OPENAI_API_KEY not set in environment"
                else:
                    client = OpenAI(api_key=api_key)
                    response = client.audio.speech.create(
                        model="tts-1",
                        voice=voice,
                        input=text,
                        speed=1.0
                    )
                    
                    # Save file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{file_name}_{timestamp}.mp3"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    # Calculate cost
                    char_count = len(text)
                    cost = calculate_cost(char_count)
                    
                    # Update metadata
                    metadata = load_metadata()
                    metadata[filename] = {
                        'name': file_name,
                        'group': group,
                        'created': timestamp,
                        'voice': voice,
                        'characters': char_count,
                        'cost': cost
                    }
                    save_metadata(metadata)
                    
                    # Update usage stats
                    usage = load_usage()
                    usage['total_characters'] += char_count
                    usage['total_cost'] += cost
                    usage['files_generated'] += 1
                    save_usage(usage)
                    
                    success = True
                    
            except Exception as e:
                error = str(e)
    
    # Load files and organize
    metadata = load_metadata()
    usage = load_usage()
    
    # Get recent files (last 10)
    all_files = []
    for fname, data in metadata.items():
        all_files.append({
            'filename': fname,
            'name': data.get('name', fname),
            'group': data.get('group', 'Uncategorized'),
            'created': data.get('created', ''),
            'chars': data.get('characters', 0),
            'cost': data.get('cost', 0)
        })
    
    # Sort by date and get recent
    all_files.sort(key=lambda x: x['created'], reverse=True)
    recent_files = all_files[:10]
    
    # Group remaining files
    grouped_files = {}
    for file in all_files:
        group = file['group']
        if group not in grouped_files:
            grouped_files[group] = []
        grouped_files[group].append(file)
    
    return render_template_string(HTML_TEMPLATE, 
                                   error=error, 
                                   success=success, 
                                   filename=filename, 
                                   grouped_files=grouped_files,
                                   recent_files=recent_files,
                                   usage=usage)

@app.route('/audio/<filename>')
def audio(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='audio/mpeg')
    return "File not found", 404

@app.route('/download/<filename>')
def download(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='audio/mpeg', as_attachment=True, download_name=filename)
    return "File not found", 404

@app.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        
        # Update metadata and recalculate usage
        metadata = load_metadata()
        if filename in metadata:
            # Subtract from usage stats
            usage = load_usage()
            usage['total_characters'] -= metadata[filename].get('characters', 0)
            usage['total_cost'] -= metadata[filename].get('cost', 0)
            usage['files_generated'] -= 1
            save_usage(usage)
            
            del metadata[filename]
            save_metadata(metadata)
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("\n🚀 Starting TTS Web App Pro...")
    print("📱 Open your browser and go to: http://localhost:5000\n")
    app.run(debug=True, port=5000)
