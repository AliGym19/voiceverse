# Database Integration Guide for tts_app19.py

**Purpose:** Step-by-step guide to replace JSON file operations with SQLite database operations

---

## Summary

This guide provides exact code changes needed to integrate the SQLite database into your application. Each section shows the current code and the replacement code.

---

## Step 1: Add Database Import (Line ~25)

**Add after other imports:**
```python
from database import Database
```

---

## Step 2: Initialize Database (Line ~40, after app configuration)

**Add after `csrf = CSRFProtect(app)`:**
```python
# Database: Initialize SQLite database
db = Database('voiceverse.db')
```

---

## Step 3: Remove/Replace User Management Functions (Lines 182-240)

### 3.1 Remove `load_users()` function (Lines 182-190)
**DELETE THIS ENTIRE FUNCTION** - No longer needed

### 3.2 Remove `save_users()` function (Lines 191-197)
**DELETE THIS ENTIRE FUNCTION** - No longer needed

### 3.3 Replace `create_user()` function (Lines 198-208)

**FIND (Lines 198-208):**
```python
def create_user(username, password):
    """Create a new user account"""
    users = load_users()

    if username in users:
        return False

    users[username] = {
        'password': generate_password_hash(password),
        'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    save_users(users)
    return True
```

**REPLACE WITH:**
```python
def create_user(username, password):
    """Create a new user account"""
    password_hash = generate_password_hash(password)
    user_id = db.create_user(username, password_hash)
    return user_id is not None
```

### 3.4 Replace `verify_user()` function (Lines 209-240)

**FIND (Lines 209-240):**
```python
def verify_user(username, password):
    """Verify user credentials"""
    users = load_users()

    if username not in users:
        return False

    stored_hash = users[username]['password']

    # Handle both scrypt and sha256 for backwards compatibility
    if stored_hash.startswith('scrypt:'):
        return check_password_hash(stored_hash, password)
    elif stored_hash.startswith('sha256:'):
        return check_password_hash(stored_hash, password)
    else:
        # Legacy plain hash - convert to scrypt
        is_valid = check_password_hash(stored_hash, password)
        if is_valid:
            # Upgrade to scrypt
            users[username]['password'] = generate_password_hash(password)
            save_users(users)
        return is_valid
```

**REPLACE WITH:**
```python
def verify_user(username, password):
    """Verify user credentials"""
    user = db.get_user(username)

    if not user:
        return False

    stored_hash = user['password_hash']

    # Handle both scrypt and sha256 for backwards compatibility
    if stored_hash.startswith('scrypt:'):
        is_valid = check_password_hash(stored_hash, password)
    elif stored_hash.startswith('sha256:'):
        is_valid = check_password_hash(stored_hash, password)
    else:
        # Legacy plain hash
        is_valid = check_password_hash(stored_hash, password)

    # Update last login on successful authentication
    if is_valid:
        db.update_last_login(user['id'])

    return is_valid
```

---

## Step 4: Remove/Replace Metadata Functions (Lines 241-292)

### 4.1 Remove `load_metadata()` function (Lines 241-249)
**DELETE THIS ENTIRE FUNCTION** - No longer needed

### 4.2 Remove `save_metadata()` function (Lines 250-256)
**DELETE THIS ENTIRE FUNCTION** - No longer needed

### 4.3 Replace `verify_file_ownership()` function (Lines 293-320)

**FIND (Lines 293-320):**
```python
def verify_file_ownership(filename, username):
    """Verify that the user owns the file"""
    metadata = load_metadata()

    if filename not in metadata:
        return False

    file_info = metadata[filename]
    owner = file_info.get('owner', '')

    return owner == username
```

**REPLACE WITH:**
```python
def verify_file_ownership(filename, username):
    """Verify that the user owns the file"""
    file_info = db.get_audio_file(filename)

    if not file_info:
        return False

    # Get owner's username from user_id
    owner = db.get_user_by_id(file_info['owner_id'])

    if not owner:
        return False

    return owner['username'] == username
```

---

## Step 5: Replace Usage Stats Functions (Lines 257-291)

### 5.1 Remove `load_usage()` function (Lines 257-274)
**DELETE THIS ENTIRE FUNCTION** - No longer needed

### 5.2 Remove `save_usage()` function (Lines 275-291)
**DELETE THIS ENTIRE FUNCTION** - No longer needed

---

## Step 6: Replace Playback History Functions (Lines 346-360)

### 6.1 Remove `load_history()` function (Lines 346-354)
**DELETE THIS ENTIRE FUNCTION** - No longer needed

### 6.2 Remove `save_history()` function (Lines 355-360)
**DELETE THIS ENTIRE FUNCTION** - No longer needed

---

## Step 7: Update Routes to Use Database

### 7.1 Update Index Route (Lines ~4000-4090)

**FIND the section that loads metadata for file listing:**
```python
metadata = load_metadata()
files = []
for filename, info in metadata.items():
    if info.get('owner') == username:
        files.append({
            'filename': filename,
            'name': info['name'],
            ...
        })
```

**REPLACE WITH:**
```python
# Get user ID first
user = db.get_user(username)
if not user:
    return redirect(url_for('login'))

# Get files for this user
audio_files = db.get_audio_files_by_owner(user['id'])
files = []
for file_info in audio_files:
    files.append({
        'filename': file_info['filename'],
        'name': file_info['display_name'],
        'voice': file_info['voice'],
        'group': file_info['category'],
        'created': file_info['created_at'],
        'characters': file_info['character_count'],
        'cost': file_info['cost']
    })
```

### 7.2 Update TTS Generation Route (POST /)

**FIND the section that saves file metadata (after TTS generation):**
```python
metadata = load_metadata()
metadata[full_filename] = {
    'name': name,
    'group': group,
    'created': timestamp,
    'voice': voice,
    'characters': len(text),
    'cost': cost,
    'owner': username
}
save_metadata(metadata)
```

**REPLACE WITH:**
```python
# Get user ID
user = db.get_user(username)
if not user:
    error = "User not found"
    # Handle error...

# Save file metadata to database
db.create_audio_file(
    filename=full_filename,
    display_name=name,
    owner_id=user['id'],
    voice=voice,
    category=group,
    text=text,
    character_count=len(text),
    cost=cost
)
```

### 7.3 Update Usage Stats Tracking

**FIND where usage is recorded:**
```python
usage = load_usage()
# ... update usage dict ...
save_usage(usage)
```

**REPLACE WITH:**
```python
user = db.get_user(username)
if user:
    db.record_usage(user['id'], len(text), cost)
```

### 7.4 Update Playback History

**FIND where playback is recorded:**
```python
history = load_history()
# ... update history ...
save_history(history)
```

**REPLACE WITH:**
```python
user = db.get_user(username)
file_info = db.get_audio_file(filename)
if user and file_info:
    db.record_playback(user['id'], file_info['id'])
```

---

## Step 8: Update API Routes

### 8.1 Update `/api/history` route

**FIND:**
```python
@app.route('/api/history')
@login_required
def get_history():
    username = session.get('username')
    history = load_history()
    user_history = history.get(username, [])
    return jsonify(user_history)
```

**REPLACE WITH:**
```python
@app.route('/api/history')
@login_required
def get_history():
    username = session.get('username')
    user = db.get_user(username)

    if not user:
        return jsonify([])

    history = db.get_playback_history(user['id'], limit=50)
    return jsonify(history)
```

### 8.2 Update `/api/delete/<filename>` route

**FIND where metadata is updated after file deletion:**
```python
metadata = load_metadata()
if filename in metadata:
    del metadata[filename]
    save_metadata(metadata)
```

**REPLACE WITH:**
```python
file_info = db.get_audio_file(filename)
if file_info:
    db.delete_audio_file(file_info['id'])
```

---

## Step 9: Update Security Migration (Lines ~160-180)

**FIND the `migrate_file_ownership()` function:**
```python
def migrate_file_ownership():
    """One-time migration: Add owner field to existing files"""
    metadata_file = os.path.join(AUDIO_DIR, 'metadata.json')

    if not os.path.exists(metadata_file):
        return

    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    modified = False
    for filename, info in metadata.items():
        if 'owner' not in info:
            info['owner'] = 'admin'  # Default owner
            modified = True

    if modified:
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
```

**REPLACE WITH:**
```python
def migrate_file_ownership():
    """
    Migration is now handled by migrate_to_sqlite.py
    This function is kept for backward compatibility but does nothing.
    """
    pass
```

---

## Step 10: Remove JSON File Constants (Optional)

**FIND (around lines 160-170):**
```python
USERS_FILE = os.path.join(AUDIO_DIR, 'users.json')
METADATA_FILE = os.path.join(AUDIO_DIR, 'metadata.json')
USAGE_FILE = os.path.join(AUDIO_DIR, 'usage_stats.json')
HISTORY_FILE = os.path.join(AUDIO_DIR, 'playback_history.json')
```

**COMMENT OUT or DELETE** - These are no longer used

---

## Testing Checklist

After making all changes:

1. **Syntax Check:**
   ```bash
   python3 -m py_compile tts_app19.py
   ```

2. **Run Migration:**
   ```bash
   python3 migrate_to_sqlite.py
   ```

3. **Start Application:**
   ```bash
   python3 tts_app19.py
   ```

4. **Test User Operations:**
   - [ ] Register new user
   - [ ] Login with existing user
   - [ ] Logout

5. **Test File Operations:**
   - [ ] Generate new TTS audio
   - [ ] View file list
   - [ ] Play audio file
   - [ ] Delete audio file

6. **Test Ownership:**
   - [ ] User can only see their own files
   - [ ] User cannot access other users' files

7. **Test Stats:**
   - [ ] Usage stats are recorded
   - [ ] Monthly totals are calculated

---

## Rollback Plan

If there are issues after integration:

1. **Restore JSON files from backup:**
   ```bash
   python3 migrate_to_sqlite.py --rollback --backup-dir backup_YYYYMMDD_HHMMSS
   ```

2. **Revert code changes:**
   ```bash
   git checkout tts_app19.py
   ```

3. **Or use your version control to restore previous version**

---

## Performance Notes

**Expected Improvements:**
- File listing: 10-50x faster (indexed query vs loading all JSON)
- User lookup: 5-10x faster (indexed username vs dictionary lookup)
- Concurrent access: Much more reliable (SQLite locking vs file locking)
- Data integrity: Guaranteed (ACID compliance)

**Database Maintenance:**
```python
# Vacuum database (reclaim space) - run monthly
db.vacuum()

# Backup database
db.backup('voiceverse_backup.db')

# Get statistics
stats = db.get_stats()
print(stats)
```

---

## Common Issues and Solutions

### Issue: "Table already exists" error
**Solution:** Database already initialized. This is normal if you ran migration script.

### Issue: "No such table" error
**Solution:** Run `python3 migrate_to_sqlite.py` to create tables and migrate data.

### Issue: Files not showing up
**Solution:** Check that migration completed successfully. Verify with:
```python
python3 -c "from database import Database; db = Database(); print(db.get_stats())"
```

### Issue: "User not found" after migration
**Solution:** The migration creates "ali.admin" user automatically. Set password:
```python
python3 -c "from database import Database; from werkzeug.security import generate_password_hash; db = Database(); print('TODO: Add password reset function')"
```

---

**Document Version:** 1.0
**Created:** October 24, 2025
**For Application:** tts_app19.py (SQLite Integration)
