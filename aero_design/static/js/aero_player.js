// Windows Vista/7 Aero Player Controls JavaScript

// ==========================================================================
// Global Variables
// ==========================================================================

let audioPlayer = null;
let currentAudioFile = null;
let isPlaying = false;
let audioFiles = [];
let currentIndex = -1;

// ==========================================================================
// Initialize on Page Load
// ==========================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize audio player
    audioPlayer = document.getElementById('audioPlayer');

    // Setup event listeners
    setupEventListeners();

    // Initialize UI components
    initializeUI();

    // Load audio library if on library tab
    if (document.querySelector('.nav-btn[data-tab="library"].active')) {
        loadAudioLibrary();
    }

    // Add window animations
    addWindowAnimations();

    // Handle window resize for responsive behavior
    handleResponsiveResize();
});

// ==========================================================================
// Responsive Resize Handler
// ==========================================================================

function handleResponsiveResize() {
    let resizeTimer;

    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            const contentWrapper = document.querySelector('.content-wrapper');

            // If window is wider than 1024px, remove mobile view class
            if (window.innerWidth > 1024) {
                contentWrapper.classList.remove('show-main');
            }
        }, 250);
    });
}

// ==========================================================================
// Event Listeners Setup
// ==========================================================================

function setupEventListeners() {
    // Tab Navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            switchTab(this.dataset.tab);
        });
    });

    // Voice Selection with Ripple Effect
    document.querySelectorAll('.voice-option').forEach(option => {
        option.addEventListener('click', function(e) {
            createRippleEffect(e, this);
        });
    });

    // Speed Slider
    const speedSlider = document.getElementById('speedSlider');
    if (speedSlider) {
        speedSlider.addEventListener('input', function() {
            document.getElementById('speedValue').textContent = this.value;
        });
    }

    // Character Counter
    const textArea = document.getElementById('text');
    if (textArea) {
        textArea.addEventListener('input', function() {
            const count = this.value.length;
            document.getElementById('charCount').textContent = count.toLocaleString();

            // Change color when approaching limit
            const counter = document.querySelector('.char-counter');
            if (count > 90000) {
                counter.style.color = '#ff6b6b';
            } else if (count > 75000) {
                counter.style.color = '#ffd93d';
            } else {
                counter.style.color = 'rgba(255, 255, 255, 0.6)';
            }
        });
    }

    // File Upload
    const fileUpload = document.getElementById('fileUpload');
    if (fileUpload) {
        fileUpload.addEventListener('change', handleFileUpload);
    }

    // Form Submission
    const ttsForm = document.getElementById('ttsForm');
    if (ttsForm) {
        ttsForm.addEventListener('submit', handleFormSubmit);
    }

    // Player Controls
    setupPlayerControls();

    // Window Controls
    setupWindowControls();

    // Volume Control
    setupVolumeControl();

    // Progress Bar
    setupProgressBar();
}

// ==========================================================================
// Tab Switching
// ==========================================================================

function switchTab(tabName) {
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.style.display = 'none';
    });

    const targetTab = document.getElementById(`${tabName}-tab`);
    if (targetTab) {
        targetTab.style.display = 'block';

        // Load content for specific tabs
        if (tabName === 'library') {
            loadAudioLibrary();
        } else if (tabName === 'agents') {
            loadAgentsInfo();
        } else if (tabName === 'settings') {
            loadSettings();
        }
    }

    // RESPONSIVE: On medium/small screens, show main panel and hide sidebar
    const contentWrapper = document.querySelector('.content-wrapper');
    if (window.innerWidth <= 1024) {
        contentWrapper.classList.add('show-main');
    }
}

// Function to go back to sidebar on mobile/tablet
function backToSidebar() {
    const contentWrapper = document.querySelector('.content-wrapper');
    contentWrapper.classList.remove('show-main');
}

// ==========================================================================
// File Upload Handler
// ==========================================================================

function handleFileUpload(e) {
    const file = e.target.files[0];
    if (file) {
        const fileInfo = document.getElementById('fileInfo');
        fileInfo.innerHTML = `
            <strong>Selected File:</strong> ${file.name}<br>
            <strong>Size:</strong> ${(file.size / 1024).toFixed(2)} KB<br>
            <strong>Type:</strong> ${file.type || 'Unknown'}
        `;
        fileInfo.classList.add('active');

        // Read file content for supported types
        if (file.name.endsWith('.txt')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('text').value = e.target.result;
                updateCharCounter();
            };
            reader.readAsText(file);
        } else if (file.name.endsWith('.pdf') || file.name.endsWith('.docx')) {
            // These will be processed server-side
            showNotification('File uploaded. Content will be extracted during processing.', 'info');
        }
    }
}

// ==========================================================================
// Form Submission
// ==========================================================================

async function handleFormSubmit(e) {
    e.preventDefault();

    const formData = new FormData(e.target);

    // Add voice selection
    const selectedVoice = document.querySelector('input[name="voice"]:checked');
    if (selectedVoice) {
        formData.append('voice', selectedVoice.value);
    }

    // Add speed value
    formData.append('speed', document.getElementById('speedSlider').value);

    // Add AI features
    formData.append('use_preprocessing',
        document.getElementById('preprocessToggle').checked ? 'on' : 'off');
    formData.append('use_chunking',
        document.getElementById('chunkingToggle').checked ? 'on' : 'off');
    formData.append('model',
        document.getElementById('qualityToggle').checked ? 'tts-1-hd' : 'tts-1');

    // Show loading overlay
    showLoading(true);

    try {
        const response = await fetch('/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        if (response.ok) {
            // Handle success
            showNotification('Audio generated successfully!', 'success');

            // Refresh library
            if (document.querySelector('.nav-btn[data-tab="library"]')) {
                loadAudioLibrary();
            }

            // Play the generated audio
            const result = await response.json();
            if (result.filename) {
                playAudio(result.filename, result.display_name);
            }
        } else {
            const error = await response.text();
            showNotification(`Error: ${error}`, 'error');
        }
    } catch (error) {
        console.error('Form submission error:', error);
        showNotification('An error occurred. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

// ==========================================================================
// Player Controls
// ==========================================================================

function setupPlayerControls() {
    const playPauseBtn = document.getElementById('playPauseBtn');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const downloadBtn = document.getElementById('downloadBtn');

    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', togglePlayPause);
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', playPrevious);
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', playNext);
    }

    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadCurrentAudio);
    }

    // Audio player events
    if (audioPlayer) {
        audioPlayer.addEventListener('play', onAudioPlay);
        audioPlayer.addEventListener('pause', onAudioPause);
        audioPlayer.addEventListener('ended', onAudioEnded);
        audioPlayer.addEventListener('timeupdate', updateProgress);
        audioPlayer.addEventListener('loadedmetadata', updateDuration);
    }
}

function togglePlayPause() {
    if (!audioPlayer.src) {
        showNotification('No audio file selected', 'info');
        return;
    }

    if (isPlaying) {
        audioPlayer.pause();
    } else {
        audioPlayer.play();
    }
}

function onAudioPlay() {
    isPlaying = true;
    const playPauseBtn = document.getElementById('playPauseBtn');
    playPauseBtn.querySelector('.play-icon').style.display = 'none';
    playPauseBtn.querySelector('.pause-icon').style.display = 'block';

    // Add pulsing animation
    playPauseBtn.classList.add('playing');
}

function onAudioPause() {
    isPlaying = false;
    const playPauseBtn = document.getElementById('playPauseBtn');
    playPauseBtn.querySelector('.play-icon').style.display = 'block';
    playPauseBtn.querySelector('.pause-icon').style.display = 'none';

    // Remove pulsing animation
    playPauseBtn.classList.remove('playing');
}

function onAudioEnded() {
    isPlaying = false;
    onAudioPause();

    // Auto-play next if available
    if (currentIndex < audioFiles.length - 1) {
        playNext();
    }
}

function playPrevious() {
    if (currentIndex > 0) {
        currentIndex--;
        const file = audioFiles[currentIndex];
        playAudio(file.filename, file.display_name);
    }
}

function playNext() {
    if (currentIndex < audioFiles.length - 1) {
        currentIndex++;
        const file = audioFiles[currentIndex];
        playAudio(file.filename, file.display_name);
    }
}

function playAudio(filename, displayName) {
    currentAudioFile = filename;
    audioPlayer.src = `/audio/${filename}`;
    audioPlayer.play();

    // Update player info
    document.getElementById('trackName').textContent = displayName || filename;
    document.getElementById('trackArtist').textContent = 'VoiceVerse AI';

    // Update navigation buttons
    updateNavigationButtons();
}

function updateNavigationButtons() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');

    prevBtn.disabled = currentIndex <= 0;
    nextBtn.disabled = currentIndex >= audioFiles.length - 1;
}

function downloadCurrentAudio() {
    if (currentAudioFile) {
        window.location.href = `/download/${currentAudioFile}`;
    } else {
        showNotification('No audio file selected', 'info');
    }
}

// ==========================================================================
// Volume Control
// ==========================================================================

function setupVolumeControl() {
    const volumeSlider = document.getElementById('volumeSlider');
    const volumeFill = document.getElementById('volumeFill');

    if (volumeSlider) {
        volumeSlider.addEventListener('input', function() {
            const value = this.value;
            audioPlayer.volume = value / 100;

            // Update fill
            if (volumeFill) {
                volumeFill.style.width = `${value}%`;
            }

            // Update icon
            updateVolumeIcon(value);
        });

        // Set initial volume
        volumeSlider.value = 70;
        audioPlayer.volume = 0.7;
        if (volumeFill) {
            volumeFill.style.width = '70%';
        }
    }
}

function updateVolumeIcon(value) {
    const volumeBtn = document.getElementById('volumeBtn');
    if (!volumeBtn) return;

    let iconPath;
    if (value == 0) {
        iconPath = 'M3 9v6h4l5 5V4L7 9H3z M16.5 12l-3.5-3.5v7z';
    } else if (value < 50) {
        iconPath = 'M3 9v6h4l5 5V4L7 9H3z M16.5 12A4.5 4.5 0 0014 7.5v9a4.5 4.5 0 002.5-4.5z';
    } else {
        iconPath = 'M3 9v6h4l5 5V4L7 9H3z M16.5 12A4.5 4.5 0 0014 7.5v9a4.5 4.5 0 002.5-4.5z M19 12c0 4.5-2 7-2 7s2-2.5 2-7-2-7-2-7 2 2.5 2 7z';
    }

    volumeBtn.querySelector('path').setAttribute('d', iconPath);
}

// ==========================================================================
// Progress Bar
// ==========================================================================

function setupProgressBar() {
    const progressBar = document.getElementById('progressBar');

    if (progressBar) {
        progressBar.addEventListener('click', function(e) {
            if (!audioPlayer.src) return;

            const rect = this.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            audioPlayer.currentTime = percent * audioPlayer.duration;
        });
    }
}

function updateProgress() {
    if (!audioPlayer.duration) return;

    const percent = (audioPlayer.currentTime / audioPlayer.duration) * 100;
    const progressFill = document.getElementById('progressFill');
    const progressHandle = document.getElementById('progressHandle');

    if (progressFill) {
        progressFill.style.width = `${percent}%`;
    }

    if (progressHandle) {
        progressHandle.style.left = `${percent}%`;
    }

    // Update time displays
    document.getElementById('currentTime').textContent = formatTime(audioPlayer.currentTime);
}

function updateDuration() {
    document.getElementById('totalTime').textContent = formatTime(audioPlayer.duration);
}

function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '0:00';

    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// ==========================================================================
// Window Controls
// ==========================================================================

function setupWindowControls() {
    // These are decorative in the web version
    window.minimizeWindow = function() {
        const aeroWindow = document.querySelector('.aero-window');
        aeroWindow.style.transform = 'scale(0.9)';
        setTimeout(() => {
            aeroWindow.style.transform = 'scale(1)';
        }, 300);
    };

    window.maximizeWindow = function() {
        const aeroWindow = document.querySelector('.aero-window');
        aeroWindow.classList.toggle('maximized');
    };

    window.closeWindow = function() {
        if (confirm('Are you sure you want to close VoiceVerse?')) {
            window.location.href = '/logout';
        }
    };
}

// ==========================================================================
// Library Management
// ==========================================================================

async function loadAudioLibrary() {
    try {
        const response = await fetch('/api/audio-files', {
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        if (response.ok) {
            audioFiles = await response.json();
            displayAudioLibrary(audioFiles);
            updateCategoryFilter(audioFiles);
        }
    } catch (error) {
        console.error('Error loading library:', error);
    }
}

function displayAudioLibrary(files) {
    const library = document.getElementById('audioLibrary');
    if (!library) return;

    if (files.length === 0) {
        library.innerHTML = '<p style="color: rgba(255,255,255,0.6); text-align: center;">No audio files yet. Generate your first audio above!</p>';
        return;
    }

    library.innerHTML = files.map((file, index) => `
        <div class="audio-card" data-index="${index}" onclick="selectAudioFile(${index})">
            <div class="audio-card-icon">🎵</div>
            <div class="audio-card-title">${file.display_name || file.filename}</div>
            <div class="audio-card-info">
                <span class="audio-voice">${file.voice || 'Unknown'}</span>
                <span class="audio-date">${formatDate(file.created_at)}</span>
            </div>
            <div class="audio-card-actions">
                <button onclick="event.stopPropagation(); playAudioFile(${index})">Play</button>
                <button onclick="event.stopPropagation(); downloadAudioFile('${file.filename}')">Download</button>
                <button onclick="event.stopPropagation(); deleteAudioFile('${file.filename}')">Delete</button>
            </div>
        </div>
    `).join('');
}

function selectAudioFile(index) {
    currentIndex = index;
    const file = audioFiles[index];
    playAudio(file.filename, file.display_name);
}

function playAudioFile(index) {
    selectAudioFile(index);
}

function downloadAudioFile(filename) {
    window.location.href = `/download/${filename}`;
}

async function deleteAudioFile(filename) {
    if (!confirm('Are you sure you want to delete this audio file?')) {
        return;
    }

    try {
        const response = await fetch(`/delete/${filename}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        if (response.ok) {
            showNotification('File deleted successfully', 'success');
            loadAudioLibrary();
        } else {
            showNotification('Error deleting file', 'error');
        }
    } catch (error) {
        console.error('Error deleting file:', error);
        showNotification('Error deleting file', 'error');
    }
}

function updateCategoryFilter(files) {
    const categories = [...new Set(files.map(f => f.group || 'Uncategorized'))];
    const filter = document.getElementById('categoryFilter');

    if (filter) {
        filter.innerHTML = '<option value="">All Categories</option>' +
            categories.map(cat => `<option value="${cat}">${cat}</option>`).join('');

        filter.addEventListener('change', function() {
            filterAudioLibrary();
        });
    }
}

function filterAudioLibrary() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const category = document.getElementById('categoryFilter').value;

    const filtered = audioFiles.filter(file => {
        const matchesSearch = !searchTerm ||
            (file.display_name && file.display_name.toLowerCase().includes(searchTerm)) ||
            file.filename.toLowerCase().includes(searchTerm);
        const matchesCategory = !category || file.group === category;

        return matchesSearch && matchesCategory;
    });

    displayAudioLibrary(filtered);
}

// ==========================================================================
// AI Agents
// ==========================================================================

async function loadAgentsInfo() {
    const agentsGrid = document.querySelector('.agents-grid');
    if (!agentsGrid) return;

    const agents = [
        {
            name: 'Smart Preprocessing',
            icon: '🧹',
            description: 'Cleans and optimizes text for better TTS quality',
            endpoint: '/api/agent/preprocess'
        },
        {
            name: 'Smart Chunking',
            icon: '✂️',
            description: 'Splits long text at natural boundaries',
            endpoint: '/api/agent/smart-chunk'
        },
        {
            name: 'Metadata Suggestion',
            icon: '📝',
            description: 'Auto-generates filename and category',
            endpoint: '/api/agent/suggest-metadata'
        },
        {
            name: 'Quality Analysis',
            icon: '📊',
            description: 'Analyzes text for TTS suitability',
            endpoint: '/api/agent/analyze'
        },
        {
            name: 'Voice Recommendation',
            icon: '🎤',
            description: 'Suggests the best voice for your content',
            endpoint: '/api/agent/recommend-voice'
        }
    ];

    agentsGrid.innerHTML = agents.map(agent => `
        <div class="agent-card">
            <div class="agent-icon">${agent.icon}</div>
            <h3 class="agent-name">${agent.name}</h3>
            <p class="agent-description">${agent.description}</p>
            <button class="aero-btn secondary" onclick="testAgent('${agent.endpoint}')">
                Test Agent
            </button>
        </div>
    `).join('');
}

async function testAgent(endpoint) {
    const text = prompt('Enter text to test the agent:');
    if (!text) return;

    showLoading(true);

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ text })
        });

        if (response.ok) {
            const result = await response.json();
            showAgentResult(result);
        } else {
            showNotification('Error testing agent', 'error');
        }
    } catch (error) {
        console.error('Error testing agent:', error);
        showNotification('Error testing agent', 'error');
    } finally {
        showLoading(false);
    }
}

function showAgentResult(result) {
    const modal = document.createElement('div');
    modal.className = 'agent-result-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>Agent Result</h3>
            <pre>${JSON.stringify(result, null, 2)}</pre>
            <button onclick="this.parentElement.parentElement.remove()">Close</button>
        </div>
    `;
    document.body.appendChild(modal);
}

// ==========================================================================
// Settings
// ==========================================================================

async function loadSettings() {
    const settingsContent = document.querySelector('.settings-content');
    if (!settingsContent) return;

    settingsContent.innerHTML = `
        <div class="settings-section">
            <h3>Account Settings</h3>
            <div class="setting-item">
                <label>Username:</label>
                <span>${document.querySelector('.user-name').textContent}</span>
            </div>
            <div class="setting-item">
                <button class="aero-btn secondary" onclick="window.location.href='/logout'">
                    Sign Out
                </button>
            </div>
        </div>

        <div class="settings-section">
            <h3>Audio Settings</h3>
            <div class="setting-item">
                <label>Default Voice:</label>
                <select class="aero-select" id="defaultVoice">
                    <option value="alloy">Alloy</option>
                    <option value="echo">Echo</option>
                    <option value="fable">Fable</option>
                    <option value="nova" selected>Nova</option>
                    <option value="onyx">Onyx</option>
                    <option value="shimmer">Shimmer</option>
                </select>
            </div>
            <div class="setting-item">
                <label>Default Speed:</label>
                <input type="range" min="0.25" max="4" step="0.25" value="1" id="defaultSpeed">
                <span id="defaultSpeedValue">1.0x</span>
            </div>
        </div>

        <div class="settings-section">
            <h3>AI Features</h3>
            <div class="setting-item">
                <label class="aero-toggle">
                    <input type="checkbox" id="defaultPreprocessing">
                    <span class="toggle-slider"></span>
                    <span class="toggle-label">Enable preprocessing by default</span>
                </label>
            </div>
            <div class="setting-item">
                <label class="aero-toggle">
                    <input type="checkbox" id="defaultChunking">
                    <span class="toggle-slider"></span>
                    <span class="toggle-label">Enable smart chunking by default</span>
                </label>
            </div>
        </div>

        <div class="settings-section">
            <button class="aero-btn primary" onclick="saveSettings()">
                Save Settings
            </button>
        </div>
    `;

    // Setup settings listeners
    document.getElementById('defaultSpeed').addEventListener('input', function() {
        document.getElementById('defaultSpeedValue').textContent = this.value + 'x';
    });
}

function saveSettings() {
    // In a real implementation, this would save to the backend
    showNotification('Settings saved successfully', 'success');
}

// ==========================================================================
// Text Analysis
// ==========================================================================

async function analyzeText() {
    const text = document.getElementById('text').value;
    if (!text) {
        showNotification('Please enter some text first', 'info');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch('/api/agent/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ text })
        });

        if (response.ok) {
            const result = await response.json();
            displayAnalysisResults(result);
        } else {
            showNotification('Error analyzing text', 'error');
        }
    } catch (error) {
        console.error('Error analyzing text:', error);
        showNotification('Error analyzing text', 'error');
    } finally {
        showLoading(false);
    }
}

function displayAnalysisResults(result) {
    const panel = document.getElementById('analysisPanel');
    const content = document.getElementById('analysisContent');

    if (panel && content) {
        content.innerHTML = `
            <div class="analysis-item">
                <strong>Quality Score:</strong> ${result.quality_score || 'N/A'}/10
            </div>
            <div class="analysis-item">
                <strong>Estimated Duration:</strong> ${result.estimated_duration || 'N/A'} seconds
            </div>
            <div class="analysis-item">
                <strong>Recommended Voice:</strong> ${result.recommended_voice || 'Nova'}
            </div>
            <div class="analysis-item">
                <strong>Content Type:</strong> ${result.content_type || 'General'}
            </div>
            ${result.warnings ? `
            <div class="analysis-item warnings">
                <strong>Warnings:</strong>
                <ul>${result.warnings.map(w => `<li>${w}</li>`).join('')}</ul>
            </div>
            ` : ''}
            ${result.suggestions ? `
            <div class="analysis-item suggestions">
                <strong>Suggestions:</strong>
                <ul>${result.suggestions.map(s => `<li>${s}</li>`).join('')}</ul>
            </div>
            ` : ''}
        `;

        panel.style.display = 'block';
    }
}

// ==========================================================================
// UI Utilities
// ==========================================================================

function initializeUI() {
    // Add current timestamp to filename
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
    const filenameInput = document.getElementById('filename');
    if (filenameInput && !filenameInput.value) {
        filenameInput.value = `audio_${timestamp}`;
    }

    // Initialize search listener
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', filterAudioLibrary);
    }

    // Update character counter
    updateCharCounter();
}

function updateCharCounter() {
    const textArea = document.getElementById('text');
    if (textArea) {
        const count = textArea.value.length;
        document.getElementById('charCount').textContent = count.toLocaleString();
    }
}

function createRippleEffect(e, element) {
    const ripple = document.createElement('span');
    ripple.className = 'ripple';

    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;

    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';

    element.appendChild(ripple);

    setTimeout(() => {
        ripple.remove();
    }, 600);
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = show ? 'flex' : 'none';
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `aero-notification ${type}`;
    notification.innerHTML = `
        <div class="notification-icon">
            ${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}
        </div>
        <div class="notification-message">${message}</div>
    `;

    // Add to body
    document.body.appendChild(notification);

    // Trigger animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    // Remove after delay
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

// ==========================================================================
// Window Animations
// ==========================================================================

function addWindowAnimations() {
    const aeroWindow = document.querySelector('.aero-window');

    // Add entrance animation
    aeroWindow.style.opacity = '0';
    aeroWindow.style.transform = 'scale(0.9) translateY(20px)';

    setTimeout(() => {
        aeroWindow.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
        aeroWindow.style.opacity = '1';
        aeroWindow.style.transform = 'scale(1) translateY(0)';
    }, 100);

    // Add glass shimmer effect on hover
    aeroWindow.addEventListener('mousemove', function(e) {
        const rect = this.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;

        this.style.setProperty('--mouse-x', `${x}%`);
        this.style.setProperty('--mouse-y', `${y}%`);
    });
}

// ==========================================================================
// Notification Styles (Add to CSS)
// ==========================================================================

const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
.aero-notification {
    position: fixed;
    top: 20px;
    right: -400px;
    max-width: 350px;
    padding: 15px 20px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 8px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    display: flex;
    align-items: center;
    gap: 12px;
    transition: right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 10000;
}

.aero-notification.show {
    right: 20px;
}

.notification-icon {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}

.aero-notification.success .notification-icon {
    background: linear-gradient(135deg, #00ff00 0%, #4fcf00 100%);
    color: white;
}

.aero-notification.error .notification-icon {
    background: linear-gradient(135deg, #ff6b6b 0%, #ff0000 100%);
    color: white;
}

.aero-notification.info .notification-icon {
    background: linear-gradient(135deg, #56a5eb 0%, #3d7eaa 100%);
    color: white;
}

.notification-message {
    color: #333;
    font-size: 14px;
}

.ripple {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.6);
    transform: scale(0);
    animation: ripple-animation 0.6s ease-out;
    pointer-events: none;
}

@keyframes ripple-animation {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

.agent-card {
    background: linear-gradient(135deg,
        rgba(255, 255, 255, 0.1) 0%,
        rgba(255, 255, 255, 0.05) 100%);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    transition: all 0.3s;
}

.agent-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(0, 255, 0, 0.3);
}

.agent-icon {
    font-size: 48px;
    margin-bottom: 15px;
}

.agent-name {
    color: var(--aero-green-bright);
    font-size: 18px;
    margin-bottom: 10px;
}

.agent-description {
    color: rgba(255, 255, 255, 0.8);
    font-size: 14px;
    margin-bottom: 20px;
}

.agents-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 20px;
}

.settings-section {
    margin-bottom: 30px;
    padding: 20px;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
}

.settings-section h3 {
    color: var(--aero-green-bright);
    margin-bottom: 15px;
}

.setting-item {
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 15px;
}

.setting-item label {
    color: rgba(255, 255, 255, 0.9);
    min-width: 150px;
}

.aero-window.maximized {
    width: 100vw !important;
    max-width: 100vw !important;
    height: 100vh !important;
    max-height: 100vh !important;
    border-radius: 0 !important;
}
`;

document.head.appendChild(notificationStyles);