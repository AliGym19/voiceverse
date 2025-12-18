# Global Session Coordination Usage Guide

## Quick Start

### For ANY Claude Code Terminal (Any Project)

Tell Claude Code:

```
Register this session in the global coordination system.
- Context: session_coordination
- Location: global
- Project: [your project name, e.g., kcgboxing, EHN, Miscellaneous]
- Status: Working on [your task]
```

Or manually:
```javascript
await mcp__knowledge-graph__aim_create_entities({
  context: "session_coordination",
  location: "global",
  entities: [{
    name: "Session_20251108_Other",
    entityType: "active_session",
    observations: [
      "Session started: 2025-11-08",
      "Working directory: /Users/ali/Desktop/Project/kcgboxing",
      "Project: kcgboxing",
      "Last heartbeat: " + new Date().toISOString(),
      "Status: Active - working on [your task]"
    ]
  }]
})
```

---

## Safe Editing Workflow

### Before Editing ANY File

**Step 1: Check for locks**
```javascript
const locks = await mcp__knowledge-graph__aim_search_nodes({
  context: "session_coordination",
  location: "global",
  query: "lock_app.py"  // Change to your filename
})

if (locks.entities.length > 0) {
  console.log("⚠️ LOCKED by another session!");
  console.log(locks.entities[0].observations);
  // STOP - Don't edit!
}
```

**Step 2: Create lock (if safe)**
```javascript
await mcp__knowledge-graph__aim_create_entities({
  context: "session_coordination",
  location: "global",
  entities: [{
    name: "lock_app.py",  // Change to your filename
    entityType: "file_lock",
    observations: [
      "Locked by: Session_20251108_Other",
      "Project: kcgboxing",
      "Locked at: " + new Date().toISOString(),
      "Timeout: " + new Date(Date.now() + 7200000).toISOString(),
      "Operation: Refactoring authentication"
    ]
  }]
})

await mcp__knowledge-graph__aim_create_relations({
  context: "session_coordination",
  location: "global",
  relations: [{
    from: "Session_20251108_Other",
    to: "lock_app.py",
    relationType: "holds_lock"
  }]
})
```

**Step 3: Edit the file**
```javascript
// Now it's safe to edit
await Edit({ file_path: "app.py", ... })
```

**Step 4: Release lock**
```javascript
await mcp__knowledge-graph__aim_delete_entities({
  context: "session_coordination",
  location: "global",
  entityNames: ["lock_app.py"]
})
```

---

## Simple Commands for Claude Code

### Register Session
```
Register this session in the global coordination system:
- Name: Session_[unique_id]
- Context: session_coordination
- Location: global
- Project: [kcgboxing, EHN, Miscellaneous, etc.]
- Status: Working on [describe your task]
```

### Before Editing File
```
Check if [filename] is locked in the coordination system.
If not locked, create a lock before I edit it.
```

### After Editing File
```
Release the lock on [filename] in the coordination system.
```

### Check What Other Sessions Are Doing
```
Show me all active sessions and their current work from the coordination system.
```

### List All Locked Files
```
Show me all file locks in the coordination system.
```

### Clean Up at Session End
```
Remove my session and all my locks from the coordination system.
```

---

## Using the Helper Script

### Python CLI Tool

```bash
# Register session (global, any project)
python3 scripts/session_coordinator.py register \
  --working-dir /Users/ali/Desktop/Project/kcgboxing \
  --project kcgboxing

# Check if file is locked (works across all projects)
python3 scripts/session_coordinator.py check --file app.py

# Create lock
python3 scripts/session_coordinator.py lock \
  --file app.py \
  --operation "Refactoring auth"

# Release lock
python3 scripts/session_coordinator.py unlock --file app.py

# List all sessions (across ALL projects)
python3 scripts/session_coordinator.py list-sessions

# List all locks (across ALL projects)
python3 scripts/session_coordinator.py list-locks

# Get safe edit workflow
python3 scripts/session_coordinator.py safe-edit \
  --file app.py \
  --operation "Adding feature"

# Cleanup at end
python3 scripts/session_coordinator.py cleanup
```

---

## Example: Coordinated Editing Session

**Session 1 (Terminal 1):**
```
1. Register session
2. "Check if database.py is locked"
3. "Create lock on database.py for migration work"
4. Edit database.py
5. "Release lock on database.py"
```

**Session 2 (Terminal 2):**
```
1. Register session
2. "Check if database.py is locked"
   → ⚠️ LOCKED by Session 1 - migration work
3. Work on different file instead
4. Wait for Session 1 to release lock
```

---

## Current Status Check

### See All Active Coordination (Across ALL Projects)
```javascript
await mcp__knowledge-graph__aim_read_graph({
  context: "session_coordination",
  location: "global"
})
```

This shows:
- All active sessions (any project: kcgboxing, EHN, TTS_App, etc.)
- All file locks (across all projects)
- Who's working on what and where

---

## Best Practices

1. **Always check for locks before editing**
2. **Release locks promptly after editing**
3. **Update session status regularly** (heartbeat every 30 min)
4. **Clean up session at end** (remove session entity)
5. **Use descriptive operation names** in locks
6. **Set reasonable timeouts** (2 hours default)

---

## Troubleshooting

### Stale Locks
If a lock exists but the session died:
```javascript
// Clean up stale locks (manually check timeout)
await mcp__knowledge-graph__aim_delete_entities({
  context: "session_coordination",
  location: "global",
  entityNames: ["lock_filename"]
})
```

### Lost Session
If you forgot to register:
```javascript
// Register retroactively
await mcp__knowledge-graph__aim_create_entities({
  context: "session_coordination",
  location: "global",
  entities: [{
    name: "Session_Recovery",
    entityType: "active_session",
    observations: [
      "Recovered session",
      "Project: kcgboxing",
      "Status: Active"
    ]
  }]
})
```

---

## Quick Reference Card

| Action | Command |
|--------|---------|
| Register | `aim_create_entities` with active_session |
| Check lock | `aim_search_nodes` with "lock_filename" |
| Create lock | `aim_create_entities` with file_lock |
| Release lock | `aim_delete_entities` with lock name |
| Update status | `aim_add_observations` to session |
| List sessions | `aim_search_nodes` with "active_session" |
| List locks | `aim_search_nodes` with "file_lock" |
| Cleanup | `aim_delete_entities` with session name |
