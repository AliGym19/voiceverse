# Automatic Session Coordination - Claude Code Integration

**CRITICAL**: This file defines automatic session coordination behavior for Claude Code.
Claude Code should read and follow these instructions automatically at session start.

## Auto-Activation Rules

### Session Start (ALWAYS RUN)

When ANY Claude Code session starts in `/Users/ali/Desktop/Project/TTS_App/`, automatically:

1. **Detect Session Markers**
   ```bash
   Check for: ~/.claude/session-markers/Session_*
   ```

2. **Register This Session**
   ```javascript
   const sessionId = process.env.CLAUDE_SESSION_ID || `Session_${hostname}_${pid}_${timestamp}`;

   await mcp__knowledge-graph__aim_create_entities({
     context: "tts_app_coordination",
     location: "project",
     entities: [{
       name: sessionId,
       entityType: "active_session",
       observations: [
         `Started: ${new Date().toISOString()}`,
         `PID: ${process.pid}`,
         `Working directory: ${process.cwd()}`,
         `Status: active`,
         `Last heartbeat: ${new Date().toISOString()}`
       ]
     }]
   });
   ```

3. **Check Other Active Sessions**
   ```javascript
   const sessions = await mcp__knowledge-graph__aim_search_nodes({
     context: "tts_app_coordination",
     location: "project",
     query: "active_session"
   });

   // Display to user
   if (sessions.length > 1) {
     console.log(`\n🔗 ${sessions.length} active sessions detected`);
     console.log(`This is ${sessionId}\n`);

     // Show what others are doing
     for (const session of sessions) {
       if (session.name !== sessionId) {
         console.log(`- ${session.name}`);
         // Extract work info from observations
       }
     }
   }
   ```

4. **Display Coordination Status**
   ```
   ✓ Session registered and coordinating
   ✓ Monitoring for file conflicts
   ✓ Ready to work!
   ```

### Pre-File Operation (ALWAYS CHECK)

Before **EVERY** Edit or Write operation, automatically:

1. **Extract Filename**
   ```javascript
   const filename = path.basename(filePath);
   const lockName = `lock_${filename.replace(/[^a-zA-Z0-9]/g, '_')}`;
   ```

2. **Check for Existing Lock**
   ```javascript
   const existingLock = await mcp__knowledge-graph__aim_search_nodes({
     context: "tts_app_coordination",
     location: "project",
     query: lockName
   });

   if (existingLock && existingLock.length > 0) {
     // File is locked by another session
     const lock = existingLock[0];
     const lockedBy = lock.observations.find(obs => obs.includes("Locked by"));

     // BLOCK the operation
     throw new Error(`
⚠️  FILE CONFLICT DETECTED

File: ${filePath}
Status: Locked by another session
${lockedBy}

Suggestion: Work on a different file or wait for lock release.
Check status: /sc:session-status
     `);
   }
   ```

3. **Acquire Lock If Available**
   ```javascript
   await mcp__knowledge-graph__aim_create_entities({
     context: "tts_app_coordination",
     location: "project",
     entities: [{
       name: lockName,
       entityType: "file_lock",
       observations: [
         `File: ${filePath}`,
         `Locked by: ${sessionId}`,
         `Acquired: ${new Date().toISOString()}`,
         `Timeout: ${new Date(Date.now() + 3600000).toISOString()}` // 1 hour
       ]
     }]
   });

   // Create relation
   await mcp__knowledge-graph__aim_create_relations({
     context: "tts_app_coordination",
     location: "project",
     relations: [{
       from: sessionId,
       to: lockName,
       relationType: "holds_lock"
     }]
   });
   ```

4. **Proceed with Operation**
   Operation continues normally after lock is acquired.

### During Work (PERIODIC UPDATE)

Every 5 minutes during active work:

1. **Update Heartbeat**
   ```javascript
   setInterval(async () => {
     await mcp__knowledge-graph__aim_add_observations({
       context: "tts_app_coordination",
       location: "project",
       observations: [{
         entityName: sessionId,
         contents: [`Last heartbeat: ${new Date().toISOString()}`]
       }]
     });
   }, 300000); // 5 minutes
   ```

2. **Check for Stale Locks**
   ```javascript
   const locks = await mcp__knowledge-graph__aim_search_nodes({
     context: "tts_app_coordination",
     location: "project",
     query: "file_lock"
   });

   for (const lock of locks) {
     const timeout = lock.observations.find(obs => obs.includes("Timeout:"));
     if (timeout) {
       const timeoutDate = new Date(timeout.split(": ")[1]);
       if (timeoutDate < new Date()) {
         // Lock expired, release it
         await mcp__knowledge-graph__aim_delete_entities({
           context: "tts_app_coordination",
           location: "project",
           entityNames: [lock.name]
         });
       }
     }
   }
   ```

### Session End (ALWAYS CLEANUP)

When session ends or exits:

1. **Release All Locks**
   ```javascript
   const locks = await mcp__knowledge-graph__aim_search_nodes({
     context: "tts_app_coordination",
     location: "project",
     query: `holds_lock`
   });

   const myLocks = locks.filter(lock =>
     lock.observations.some(obs => obs.includes(`Locked by: ${sessionId}`))
   );

   for (const lock of myLocks) {
     await mcp__knowledge-graph__aim_delete_entities({
       context: "tts_app_coordination",
       location: "project",
       entityNames: [lock.name]
     });
   }
   ```

2. **Update Session Status**
   ```javascript
   await mcp__knowledge-graph__aim_add_observations({
     context: "tts_app_coordination",
     location: "project",
     observations: [{
       entityName: sessionId,
       contents: [
         `Status: completed`,
         `Ended: ${new Date().toISOString()}`
       ]
     }]
   });
   ```

3. **Archive Session (After 5 Minutes)**
   ```javascript
   setTimeout(async () => {
     await mcp__knowledge-graph__aim_delete_entities({
       context: "tts_app_coordination",
       location: "project",
       entityNames: [sessionId]
     });
   }, 300000); // 5 minutes
   ```

## Commands Available to User

### `/sc:session-status`
Show all active sessions and their work.

```javascript
const sessions = await mcp__knowledge-graph__aim_search_nodes({
  context: "tts_app_coordination",
  location: "project",
  query: "active_session"
});

// Display formatted status
for (const session of sessions) {
  console.log(`Session: ${session.name}`);
  for (const obs of session.observations) {
    console.log(`  ${obs}`);
  }
}
```

### `/sc:session-locks`
Show all file locks.

```javascript
const locks = await mcp__knowledge-graph__aim_search_nodes({
  context: "tts_app_coordination",
  location: "project",
  query: "file_lock"
});

// Display formatted locks
for (const lock of locks) {
  console.log(`Lock: ${lock.name}`);
  for (const obs of lock.observations) {
    console.log(`  ${obs}`);
  }
}
```

### `/sc:session-unlock <file> [--force]`
Force release a file lock (emergency use only).

```javascript
const filename = args.file;
const lockName = `lock_${filename.replace(/[^a-zA-Z0-9]/g, '_')}`;

if (args.force) {
  await mcp__knowledge-graph__aim_delete_entities({
    context: "tts_app_coordination",
    location: "project",
    entityNames: [lockName]
  });
  console.log(`✓ Force released lock on ${filename}`);
} else {
  console.log("Use --force to confirm unlock");
}
```

### `/sc:session-refresh`
Clean up stale sessions and locks.

```javascript
// Clean up stale sessions (>2 hours inactive)
const sessions = await mcp__knowledge-graph__aim_search_nodes({
  context: "tts_app_coordination",
  location: "project",
  query: "active_session"
});

for (const session of sessions) {
  const lastHeartbeat = session.observations.find(obs => obs.includes("Last heartbeat"));
  if (lastHeartbeat) {
    const heartbeatTime = new Date(lastHeartbeat.split(": ")[1]);
    const twoHoursAgo = new Date(Date.now() - 7200000);

    if (heartbeatTime < twoHoursAgo) {
      // Stale session, clean up
      await mcp__knowledge-graph__aim_delete_entities({
        context: "tts_app_coordination",
        location: "project",
        entityNames: [session.name]
      });
    }
  }
}

// Clean up expired locks
const locks = await mcp__knowledge-graph__aim_search_nodes({
  context: "tts_app_coordination",
  location: "project",
  query: "file_lock"
});

for (const lock of locks) {
  const timeout = lock.observations.find(obs => obs.includes("Timeout:"));
  if (timeout) {
    const timeoutDate = new Date(timeout.split(": ")[1]);
    if (timeoutDate < new Date()) {
      await mcp__knowledge-graph__aim_delete_entities({
        context: "tts_app_coordination",
        location: "project",
        entityNames: [lock.name]
      });
    }
  }
}

console.log("✓ Coordination state refreshed");
```

## Configuration

Load configuration from: `skills/session-coordinator/config/coordination.yaml`

```javascript
const config = yaml.parse(fs.readFileSync(
  path.join(process.cwd(), 'skills/session-coordinator/config/coordination.yaml'),
  'utf8'
));

// Use config values:
const lockTimeout = config.session_coordination.lock_timeout;
const heartbeatInterval = config.session_coordination.heartbeat_interval;
const conflictAction = config.session_coordination.conflict_action;
```

## Error Handling

### If Knowledge Graph is unavailable:
```javascript
try {
  // Coordination operation
} catch (error) {
  console.log("⚠️  Session coordination unavailable (Knowledge Graph offline)");
  console.log("Proceeding without coordination - manual coordination required");
  // Continue without coordination
}
```

### If conflict detected but config says "warn":
```javascript
if (conflictAction === "warn") {
  console.log("⚠️  File locked by another session, but proceeding per config");
  // Continue with operation
}
```

### If conflict detected and config says "block":
```javascript
if (conflictAction === "block") {
  throw new Error("Operation blocked due to file lock");
}
```

## Performance Optimization

- Session registration: Run once at startup (~500ms)
- Lock checks: Run before each file operation (~100ms)
- Heartbeat updates: Run every 5 minutes (negligible)
- Total overhead: <1% of session time

## Security Considerations

- Locks are advisory only (cannot physically prevent file access)
- Trust-based system for coordinated development
- File locks timeout after 1 hour automatically
- Stale sessions cleaned up after 2 hours automatically
- All coordination data stored in project-local Knowledge Graph

## Integration with Other Skills

Other skills can check coordination status:

```javascript
// Check if file is locked before working on it
const isLocked = await checkFileLock(filename);
if (isLocked) {
  // Suggest alternative work
}

// Register work area
await mcp__knowledge-graph__aim_add_observations({
  context: "tts_app_coordination",
  location: "project",
  observations: [{
    entityName: sessionId,
    contents: [`Working on: ${workArea}`]
  }]
});
```

---

**Important**: This coordination is **mandatory** when multiple sessions are detected.
Claude Code must implement these checks automatically without user intervention.

**Exception**: User can disable with `--no-coordination` flag (not recommended).

---

**Version**: 1.0.0
**Status**: Production Ready
**Auto-Activate**: YES - Always active in TTS_App directory
