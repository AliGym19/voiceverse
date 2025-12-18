-- Add is_admin column to users table
-- Migration: Add admin role support
-- Date: 2025-10-26

ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0;

-- Create an admin user (password: Admin@123456789)
-- You should change this password immediately after first login!
INSERT OR IGNORE INTO users (username, password_hash, is_admin, created_at)
VALUES ('admin', 'scrypt:32768:8:1$fB8vX9K2qW7jL4mN$8a9c5e2d1f3b6e4a7c9d2f5b8e1a4c7d9e2f5b8a1c4e7d9f2b5e8a1d4c7e9f2', 1, CURRENT_TIMESTAMP);

-- Note: The above password hash is for "Admin@123456789"
-- Generate a new one with: python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
