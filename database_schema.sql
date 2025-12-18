-- VoiceVerse TTS Application - SQLite Database Schema
-- Created: October 24, 2025
-- Purpose: Replace JSON file storage with ACID-compliant database

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    CONSTRAINT username_length CHECK (length(username) >= 3)
);

-- Audio files table
CREATE TABLE IF NOT EXISTS audio_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    voice TEXT NOT NULL,
    category TEXT,
    text TEXT,
    character_count INTEGER NOT NULL,
    duration REAL,
    cost REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Usage statistics table
CREATE TABLE IF NOT EXISTS usage_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    characters_used INTEGER NOT NULL,
    cost REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    month TEXT NOT NULL,
    year INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Playback history table
CREATE TABLE IF NOT EXISTS playback_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    file_id INTEGER NOT NULL,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES audio_files(id) ON DELETE CASCADE
);

-- Security logs table
CREATE TABLE IF NOT EXISTS security_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    user_id INTEGER,
    username TEXT,
    ip_address TEXT NOT NULL,
    details TEXT,
    success BOOLEAN NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes for frequent queries
CREATE INDEX IF NOT EXISTS idx_audio_owner ON audio_files(owner_id);
CREATE INDEX IF NOT EXISTS idx_audio_created ON audio_files(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audio_filename ON audio_files(filename);
CREATE INDEX IF NOT EXISTS idx_usage_user_month ON usage_stats(user_id, year, month);
CREATE INDEX IF NOT EXISTS idx_playback_user ON playback_history(user_id);
CREATE INDEX IF NOT EXISTS idx_playback_file ON playback_history(file_id);
CREATE INDEX IF NOT EXISTS idx_playback_timestamp ON playback_history(played_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_timestamp ON security_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_security_type ON security_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_security_user ON security_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Enable foreign key constraints (required for SQLite)
PRAGMA foreign_keys = ON;
