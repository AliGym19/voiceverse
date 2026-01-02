#!/usr/bin/env bash
# Render build script for VoiceVerse TTS

set -o errexit  # Exit on error

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "📁 Creating required directories..."

# Check if running on Render with persistent disk
if [ -d "/opt/render/project/src/data" ]; then
    echo "🔧 Detected Render environment - using persistent storage..."
    mkdir -p /opt/render/project/src/data/saved_audio
    mkdir -p /opt/render/project/src/data/voice_samples
    mkdir -p /opt/render/project/src/data/logs
else
    echo "🔧 Local environment - using local directories..."
    mkdir -p saved_audio
    mkdir -p voice_samples
    mkdir -p logs
    mkdir -p certs
fi

echo "🗄️ Setting up database..."
# Database will be created automatically on first run
# SQLite file will persist in Render's disk storage

echo "✅ Build complete!"
