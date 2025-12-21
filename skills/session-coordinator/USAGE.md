# Session Coordinator - Usage Guide

## Quick Start

### One-Time Setup (5 minutes)

```bash
# 1. Navigate to skill directory
cd /Users/ali/Desktop/Project/TTS_App/skills/session-coordinator

# 2. Install automatic coordination
./hooks/install-hooks.sh

# 3. Verify installation
./scripts/session-manager.sh --test

# 4. Done! All future sessions auto-coordinate
```

## Daily Usage

### Zero Configuration Mode (Recommended)

Just open Claude Code sessions normally - coordination is **completely automatic**:

```bash
# Terminal 1
cd ~/Desktop/Project/TTS_App
claude
# Session auto-registers and starts working

# Terminal 2
cd ~/Desktop/Project/TTS_App
claude
# Session sees Terminal 1's work, coordinates automatically

# Terminal 3
cd ~/Desktop/Project/TTS_App
claude
# Session coordinates with both, suggests available work
```

That's it! No commands needed.

## What Happens Automatically

### When You Start a Session

```
✓ Session registered: Session_MacBook_24157_20251107103045
✓ Checking active sessions... Found 2 active sessions
✓ Coordination status:
  - Session_1: Working on frontend (index.html, app.js)
  - Session_2: Working on backend (tts_engine.py)
✓ Available areas: Testing, Documentation, Audio Processing
→ Ready to work!
```

### When You Edit Files

**Scenario A: File Available**
```
You: Edit auth.py
System: ✓ auth.py available, acquiring lock...
System: ✓ Lock acquired, proceeding with edit
[Edit happens normally]
```

**Scenario B: File Locked**
```
You: Edit auth.py
System: ⚠️ CONFLICT DETECTED
System: auth.py is locked by Session_2
System: Reason: Refactoring authentication logic
System: Estimated completion: 15 minutes
System:
System: Available alternatives:
  - tests/test_auth.py (write tests for changes)
  - docs/auth_design.md (update documentation)
  - Wait 15 minutes

[Edit is blocked until file unlocks]
```

### When You Work Normally

**Background activity (invisible to you):**
```
Every 5 minutes:
- Session heartbeat updated in Knowledge Graph
- Progress status refreshed
- Stale session cleanup checked
- File lock timeouts verified
```

### When You Exit

```
Session ending...
✓ Releasing 3 file locks
✓ Updating session status to completed
✓ Archiving work log
✓ Session cleanup complete
Goodbye!
```

## Manual Commands (Optional)

Use these only when you need manual control:

### Check Session Status
```bash
/sc:session-status

# Output:
# Active Sessions (3):
# 1. Session_MacBook_24157 - Frontend UI (30 min)
#    Files: index.html, app.js, style.css
#
# 2. Session_MacBook_24158 - Backend API (15 min)
#    Files: tts_engine.py, audio_processor.py
#
# 3. Session_MacBook_24159 - Testing (5 min)
#    Files: tests/test_integration.py
```

### View File Locks
```bash
/sc:session-locks

# Output:
# Active File Locks (5):
# 1. auth.py - Session_24157 (15 min remaining)
# 2. tts_engine.py - Session_24158 (45 min remaining)
# 3. index.html - Session_24157 (30 min remaining)
```

### Force Unlock (Emergency)
```bash
/sc:session-unlock auth.py --force

# Output:
# ⚠️ Forcing unlock of auth.py
# Previous lock held by: Session_24157
# Lock released. Proceed with caution.
```

### Refresh Coordination
```bash
/sc:session-refresh

# Output:
# ✓ Refreshing coordination state...
# ✓ Cleaned up 2 stale sessions
# ✓ Released 1 expired lock
# ✓ Updated heartbeats
# ✓ Coordination refreshed
```

### View History
```bash
/sc:session-history --last 24h

# Output:
# Session History (Last 24 hours):
#
# Session_MacBook_24155 (Completed)
#   Duration: 45 minutes
#   Work: Voice selection feature
#   Files edited: 7
#
# Session_MacBook_24156 (Completed)
#   Duration: 30 minutes
#   Work: Audio format export
#   Files edited: 4
```

## Common Scenarios

### Scenario 1: Working on Different Features

**What You Do:**
```
Terminal 1: "Help me add voice selection dropdown"
Terminal 2: "Optimize the audio processing speed"
Terminal 3: "Write tests for the export feature"
```

**What Happens:**
- Session 1: Locks frontend files (index.html, app.js)
- Session 2: Locks backend files (audio_processor.py)
- Session 3: Locks test files (tests/test_export.py)
- **No conflicts** - everyone works in parallel

### Scenario 2: Working on Same Feature

**What You Do:**
```
Terminal 1: "Refactor the authentication system"
Terminal 2: "Add 2FA to authentication"
```

**What Happens:**
- Session 1: Starts first, locks auth.py
- Session 2: Tries to edit auth.py → **BLOCKED**
- Session 2 sees: "Auth.py locked by Session 1 (refactoring)"
- Session 2 suggests: "Write tests for 2FA instead?"
- You: "Yes, write tests"
- Session 2: Works on tests/test_2fa.py (no conflict)

### Scenario 3: Dependent Work

**What You Do:**
```
Terminal 1: "Change the API endpoint structure"
Terminal 2: "Update the frontend to use the new API"
```

**What Happens:**
- Session 1: Locks backend API files
- Session 2: Checks dependencies, sees Session 1 changing API
- Session 2 suggests: "Session 1 is changing APIs. Wait or work on UI styling?"
- You: "Wait"
- Session 2: Monitors Session 1, notifies when API changes complete
- Session 2: "API changes complete! Ready to update frontend"

### Scenario 4: Emergency Override

**What You Do:**
```
Terminal 1: Session crashed/frozen with file locks
Terminal 2: Need to edit those files urgently
```

**What Happens:**
- Terminal 2: Tries to edit → Blocked by stale lock
- You: `/sc:session-unlock auth.py --force`
- System: Releases lock with warning
- Terminal 2: Proceeds with edit

## Configuration

### Adjusting Lock Timeout

Edit `config/coordination.yaml`:

```yaml
session_coordination:
  lock_timeout: 3600  # 1 hour (default)
  # Increase for long operations: 7200 (2 hours)
  # Decrease for quick edits: 1800 (30 minutes)
```

### Changing Conflict Behavior

```yaml
session_coordination:
  conflict_action: "block"  # Options:
  # block - Stop operation, show warning (recommended)
  # warn - Show warning, allow proceed (risky)
  # proceed - Silent, no checks (dangerous)
```

### File Lock Patterns

Edit `config/file-patterns.yaml`:

```yaml
# Always lock these files
critical_files:
  - "*.py"        # Python source
  - "*.js"        # JavaScript
  - "*.yaml"      # Config files
  - "*.json"      # Config files
  - "*.sql"       # Database migrations

# Never lock these files
ignore_files:
  - "*.log"       # Log files
  - "*.tmp"       # Temporary files
  - "*.cache"     # Cache files
  - "*.md"        # Documentation (usually safe)

# Lock timeout by file type
timeouts:
  "*.py": 3600       # 1 hour for Python
  "*.js": 3600       # 1 hour for JavaScript
  "*.sql": 7200      # 2 hours for migrations
  "*.yaml": 1800     # 30 minutes for configs
```

### Notification Settings

```yaml
session_coordination:
  show_notifications: true
  notification_types:
    - "session_start"      # Show when sessions start
    - "conflict_detected"  # Show on conflicts
    - "lock_acquired"      # Show when locks acquired
    - "session_complete"   # Show when sessions end
```

## Advanced Usage

### Custom Work Areas

Define work areas for better coordination:

```yaml
work_areas:
  frontend:
    files: ["templates/", "static/"]
    dependencies: []

  backend:
    files: ["*.py", "!tests/"]
    dependencies: []

  testing:
    files: ["tests/"]
    dependencies: ["backend", "frontend"]

  documentation:
    files: ["docs/", "*.md"]
    dependencies: []
```

Now sessions can register work areas:

```bash
# Session 1
You: "Work on frontend"
System: ✓ Registered work area: frontend
System: ✓ Locked: templates/, static/

# Session 2
You: "Work on testing"
System: ✓ Registered work area: testing
System: ℹ️ Dependencies: frontend (Session 1), backend (available)
System: Suggestion: Wait for frontend changes or start backend tests?
```

### Session Priority

Set session priorities for conflict resolution:

```yaml
# In coordination.yaml
priority_rules:
  - match: "production"
    priority: 100  # Highest
  - match: "hotfix"
    priority: 90
  - match: "feature"
    priority: 50   # Normal
  - match: "refactor"
    priority: 30
  - match: "experiment"
    priority: 10   # Lowest
```

Usage:
```bash
# Terminal 1 (normal priority)
You: "Add new feature"

# Terminal 2 (high priority)
You: "[HOTFIX] Fix critical bug"
System: ✓ High priority session detected
System: ✓ Can override lower priority locks if needed
```

### Cross-Project Coordination

Coordinate across multiple projects:

```yaml
# Use global coordination database
session_coordination:
  kg_context: "global_coordination"
  kg_location: "global"

  # Track work across projects
  multi_project: true
  projects:
    - "/Users/ali/Desktop/Project/TTS_App"
    - "/Users/ali/Desktop/Project/EHN"
    - "/Users/ali/Desktop/Project/kcgboxing"
```

## Troubleshooting

### Problem: Sessions not seeing each other

**Solution:**
```bash
# Check Knowledge Graph connection
aim_list_databases

# Should see: tts_app_coordination database

# If not, reinstall:
cd skills/session-coordinator
./hooks/install-hooks.sh --force
```

### Problem: False conflicts (file not actually locked)

**Solution:**
```bash
# Check actual locks
aim_search_nodes("lock_")

# Clean stale locks
/sc:session-refresh

# Or manual cleanup
aim_delete_entities(["lock_filename"])
```

### Problem: Session crashes leave locks

**Solution:**
Automatic cleanup happens every 30 minutes. Manual:
```bash
/sc:session-cleanup --stale --force
```

### Problem: Too many notifications

**Solution:**
```yaml
# Edit config/coordination.yaml
show_notifications: false  # Disable all

# Or selective:
notification_types:
  - "conflict_detected"  # Only conflicts
```

## Best Practices

### ✅ Do This

1. **Trust the system** - Let automatic coordination work
2. **Use descriptive work descriptions** - "Refactoring auth" not "Working"
3. **Check session status** if unsure - `/sc:session-status`
4. **Clean up completed work** - System does this, but you can help
5. **Use work areas** - Clearer coordination

### ❌ Avoid This

1. **Don't force unlock** unless emergency - Causes conflicts
2. **Don't disable coordination** - That's why it exists
3. **Don't work on same files** - Defeats the purpose
4. **Don't ignore conflict warnings** - They're there for a reason
5. **Don't run too many sessions** - 3-4 is optimal

## Performance Tips

### Optimize for Many Sessions

```yaml
# Reduce monitoring frequency
heartbeat_interval: 600  # 10 minutes instead of 5

# Increase lock timeout (fewer checks)
lock_timeout: 7200  # 2 hours

# Disable less important notifications
notification_types:
  - "conflict_detected"  # Keep only critical
```

### Optimize for Fast Operations

```yaml
# Increase monitoring frequency
heartbeat_interval: 180  # 3 minutes

# Decrease lock timeout (faster release)
lock_timeout: 1800  # 30 minutes

# Enable all notifications
show_notifications: true
```

## Integration with Other Skills

Session Coordinator works with other TTS App skills:

```bash
# TTS Quality Skill uses coordination
/sc:tts-quality analyze
→ Registers work area: "audio_quality_analysis"
→ Locks: audio files for testing
→ Other sessions see and avoid

# TTS Performance Skill uses coordination
/sc:tts-performance optimize
→ Registers work area: "performance_optimization"
→ Locks: tts_engine.py, audio_processor.py
→ Other sessions work on tests/docs instead
```

## Support

- **Documentation**: `skills/session-coordinator/README.md`
- **Logs**: `~/Desktop/Project/TTS_App/.logs/coordination/`
- **Knowledge Graph**: `aim_read_graph({context: "tts_app_coordination"})`
- **Re-install**: `./hooks/install-hooks.sh --force`

---

**Remember**: Once installed, coordination is **100% automatic**. You should rarely need manual commands!
