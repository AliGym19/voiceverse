# Knowledge Graph Usage Guide for TTS_App

## Overview

This guide shows how to populate and use the knowledge graph MCP server for the VoiceVerse TTS Application. The knowledge graph helps Claude remember project context, relationships, and important information across sessions.

## Quick Start After Restart

After restarting Claude Code, the MCP servers will be available. You can:

1. **Check server status:**
   ```bash
   claude mcp list
   ```

2. **Approve the servers** (first time only - Claude will prompt)

3. **Start using** - Just tell Claude to remember things naturally!

---

## Example 1: Core Application Architecture

### Creating Entity: Main Application File

**You say:**
> "Remember that tts_app19.py is the main Flask application file. It's 68K+ tokens which is too large to read at once, so always use offset/limit when reading it."

**Claude will create:**
- **Entity:** `tts_app19.py`
- **Type:** `file`
- **Observations:**
  - "Main Flask application for VoiceVerse"
  - "68K+ tokens - too large to read at once"
  - "Always use offset/limit when reading"
  - "Contains API endpoints, authentication, and TTS generation logic"

### Creating Relations Between Files

**You say:**
> "tts_app19.py imports and uses tts_agents.py for AI-powered text preprocessing"

**Claude will create:**
- **Relation:** `tts_app19.py` → `uses` → `tts_agents.py`

---

## Example 2: AI Agents System

### Entity: AI Agent System

**You say:**
> "Remember that we have 5 AI agents: Smart Text Preprocessing, Smart Chunking, Metadata Suggestion, Quality Analysis, and Voice Recommendation. They all use GPT-4o-mini and cost $0.001-0.003 per request."

**Claude will create:**
- **Entity:** `AI Agents System`
- **Type:** `system`
- **Observations:**
  - "5 integrated AI agents"
  - "Uses GPT-4o-mini model"
  - "Cost: $0.001-0.003 per request"
  - "Agents: Text Preprocessing, Chunking, Metadata, Quality Analysis, Voice Recommendation"

### Relations

**You say:**
> "The AI Agents System is implemented in tts_agents.py and used by tts_app19.py"

**Claude will create:**
- `AI Agents System` → `implemented_in` → `tts_agents.py`
- `tts_app19.py` → `uses` → `AI Agents System`

---

## Example 3: Database Schema

### Entity: Database

**You say:**
> "Remember the voiceverse.db has three tables: users (with bcrypt hashed passwords), audio_files (with user_id foreign key), and security_audit_log. Admin user is ali.admin."

**Claude will create:**
- **Entity:** `voiceverse.db`
- **Type:** `database`
- **Observations:**
  - "SQLite database"
  - "Three tables: users, audio_files, security_audit_log"
  - "Users table: bcrypt hashed passwords"
  - "Audio_files table: has user_id foreign key"
  - "Admin user: ali.admin"

---

## Example 4: Performance Targets & Gotchas

### Entity: Performance Requirements

**You say:**
> "Remember our performance target is sub-300ms response time, but we haven't achieved it yet. TTS processing takes 2-5 seconds depending on OpenAI API."

**Claude will create:**
- **Entity:** `Performance Requirements`
- **Type:** `requirement`
- **Observations:**
  - "Target: sub-300ms response time"
  - "Current status: not achieved"
  - "TTS processing: 2-5 seconds (OpenAI API dependent)"

### Entity: Common Issues

**You say:**
> "Remember that port 5000 often conflicts with macOS AirPlay. Always use 'lsof -ti:5000 | xargs kill -9' before starting the app."

**Claude will create:**
- **Entity:** `Port 5000 Conflict`
- **Type:** `issue`
- **Observations:**
  - "macOS AirPlay uses port 5000"
  - "Solution: lsof -ti:5000 | xargs kill -9"
  - "Must run before starting app"

---

## Example 5: Cost Optimization Strategies

### Entity: Cost Information

**You say:**
> "Remember TTS-1 costs $0.015 per 1K characters and TTS-1-HD costs $0.030. Typical generation costs $0.015-0.025. Redis caching is planned but NOT implemented - it would save 40-60% costs."

**Claude will create:**
- **Entity:** `TTS API Costs`
- **Type:** `pricing`
- **Observations:**
  - "TTS-1: $0.015 per 1K characters"
  - "TTS-1-HD: $0.030 per 1K characters"
  - "Typical cost: $0.015-0.025 per generation"
  - "Redis caching: NOT implemented (would save 40-60%)"

---

## Example 6: Security Patterns

### Entity: Security Best Practices

**You say:**
> "Remember: always use parameterized queries (never string formatting), require @login_required on all routes, verify file ownership before operations, and log security events with SecurityLogger."

**Claude will create:**
- **Entity:** `Security Patterns`
- **Type:** `best_practice`
- **Observations:**
  - "Use parameterized queries (SQL injection prevention)"
  - "All routes need @login_required decorator"
  - "Verify file ownership: check user_id matches session"
  - "Log security events with SecurityLogger"

---

## Example 7: Automation Scripts

### Entity: DevOps Scripts

**You say:**
> "Remember we have 9 automation scripts in ./scripts/: app_manager.sh (start/stop/restart/status), health_check.sh, backup_db.sh, restore_db.sh, quick_deploy.sh, cleanup.sh, setup_dev.sh, aliases.sh, and install_aliases.sh. They save 21 minutes per day."

**Claude will create:**
- **Entity:** `Automation Scripts`
- **Type:** `tooling`
- **Observations:**
  - "Location: ./scripts/ directory"
  - "9 scripts total"
  - "app_manager.sh: start/stop/restart/status"
  - "Time saved: 21 minutes/day, 10.5 hours/month"
  - "All pre-approved in settings.json"

---

## Example 8: Voice Characteristics

### Entity: Voice Options

**You say:**
> "Remember we have 6 premium voices: alloy (neutral, tutorials), echo (male, technical), fable (British male, storytelling), onyx (deep male, formal), nova (female warm, guides), shimmer (soft female, meditation)."

**Claude will create:**
- **Entity:** `TTS Voices`
- **Type:** `configuration`
- **Observations:**
  - "6 premium voices available"
  - "alloy: neutral, versatile, tutorials"
  - "echo: male, clear, technical content"
  - "fable: British male, storytelling"
  - "onyx: deep male, authority, news"
  - "nova: female warm, friendly guides"
  - "shimmer: soft female, meditation"

---

## Example 9: Project Decisions & Future Plans

### Entity: Redis Caching Plan

**You say:**
> "Remember: Redis caching is the #1 priority feature. It's NOT implemented yet but would save 40-60% on costs. It's in the high-priority roadmap."

**Claude will create:**
- **Entity:** `Redis Caching Feature`
- **Type:** `feature`
- **Observations:**
  - "Status: NOT implemented"
  - "Priority: High (#1 in roadmap)"
  - "Expected savings: 40-60% cost reduction"
  - "Would cache repeated TTS content"

### Entity: Code Refactoring Need

**You say:**
> "Remember: tts_app19.py needs to be split into modules. It's too large at 68K tokens. This is in the high-priority roadmap."

**Claude will create:**
- **Entity:** `Code Refactoring Task`
- **Type:** `technical_debt`
- **Observations:**
  - "Target: tts_app19.py"
  - "Problem: 68K tokens - too large"
  - "Solution: split into modules"
  - "Priority: High"

---

## Example 10: Testing Standards

### Entity: Testing Requirements

**You say:**
> "Remember: always run test_agents.py after changing agents, ./scripts/health_check.sh before commits, and check logs/security_audit.log for security issues."

**Claude will create:**
- **Entity:** `Testing Protocol`
- **Type:** `process`
- **Observations:**
  - "After agent changes: python3 test_agents.py"
  - "Before commits: ./scripts/health_check.sh"
  - "Security check: tail -f logs/security_audit.log"

---

## Using Named Databases (Context Separation)

The fork supports multiple named databases for organization:

### Personal Context

**You say:**
> "Remember in my personal context: I prefer working late evenings, I like detailed comments in code, and I'm learning about async/await patterns in Python."

**Claude stores in:** `memory-personal.jsonl`

### Work Context

**You say:**
> "Remember in work context: VoiceVerse TTS app is for client Ali, deadline is end of month, they want focus on cost optimization and performance."

**Claude stores in:** `memory-work.jsonl`

---

## Querying the Knowledge Graph

Once populated, Claude can answer questions like:

- **"What do you know about tts_app19.py?"**
  - Claude retrieves the entity and all observations

- **"What files use the AI Agents System?"**
  - Claude traverses relations to find connected entities

- **"What are our performance requirements?"**
  - Claude searches for entities related to performance

- **"What's our biggest technical debt?"**
  - Claude searches entities of type "technical_debt"

---

## Project-Specific Memory (Auto-Detection)

When you're in the TTS_App directory, the `tts-memory` MCP server automatically uses the `.aim/` folder:

- **Memories specific to TTS_App** stay in this project
- **Won't pollute other projects** you work on
- **Can be backed up** with the project

---

## Best Practices

### 1. **Be Specific with Entities**
   ❌ Bad: "Remember the file"
   ✅ Good: "Remember tts_app19.py is the main Flask app"

### 2. **Use Active Voice for Relations**
   ❌ Bad: "tts_agents.py and tts_app19.py are related"
   ✅ Good: "tts_app19.py imports tts_agents.py"

### 3. **Add Context to Observations**
   ❌ Bad: "Large file"
   ✅ Good: "68K tokens - too large to read at once, use offset/limit"

### 4. **Create Relations for Understanding**
   - File imports: `file_a` → `imports` → `file_b`
   - Dependencies: `feature_x` → `depends_on` → `library_y`
   - Implementations: `concept_a` → `implemented_in` → `file_c`

### 5. **Tag by Type**
   - Files: `file`
   - Features: `feature`
   - Issues: `issue`
   - Best practices: `best_practice`
   - Configuration: `configuration`
   - People: `person`
   - Technical debt: `technical_debt`

### 6. **Update Regularly**
   - After completing features
   - When discovering gotchas
   - When making architectural decisions
   - When adding new modules/files

---

## Maintenance Commands

### View All Memory
> "Show me what's in the knowledge graph"

### Search
> "Search the knowledge graph for anything related to security"

### Update
> "Update the tts_app19.py entity to note that we added caching"

### Delete
> "Delete the outdated entity about the old authentication system"

---

## Example: Full Session Building Knowledge

```
You: Remember that tts_app19.py is the main app file, it's 68K tokens.

Claude: [Creates entity tts_app19.py with observation]

You: It uses tts_agents.py for AI preprocessing.

Claude: [Creates relation tts_app19.py → uses → tts_agents.py]

You: tts_agents.py has 5 AI agents that cost $0.001-0.003 each.

Claude: [Creates entity tts_agents.py with observations about agents and cost]

You: Port 5000 often conflicts with AirPlay on macOS.

Claude: [Creates entity "Port 5000 Conflict" with solution]

You: What files use AI preprocessing?

Claude: Based on the knowledge graph, tts_app19.py uses tts_agents.py for AI preprocessing.

You: What should I watch out for when starting the app?

Claude: The knowledge graph shows that port 5000 often conflicts with macOS AirPlay.
       You should run 'lsof -ti:5000 | xargs kill -9' before starting the app.
```

---

## Migration: Importing from CLAUDE.md

The existing `CLAUDE.md` file contains valuable context. You can gradually migrate this to the knowledge graph:

### Strategy:
1. **Core entities first**: Files, databases, APIs
2. **Relationships**: Imports, dependencies, usage
3. **Gotchas & patterns**: Common issues, best practices
4. **Future plans**: Roadmap items, technical debt

This allows Claude to query relationships rather than re-reading large context files.

---

## Troubleshooting

### MCP Server Not Available
```bash
# Check if servers are configured
claude mcp list

# If not listed, check config files
cat ~/.mcp.json
cat .mcp.json

# Restart Claude Code
```

### Memory Not Persisting
- Check that memory files exist:
  ```bash
  ls -la ~/.knowledge-graph/
  ls -la .aim/
  ```

### Wrong Database Being Used
- Verify you're in the project directory for project-specific memory
- Check memory path in MCP config

---

## Summary

The knowledge graph transforms Claude from stateless to stateful:

- ✅ **Persistent memory** across sessions
- ✅ **Relationship tracking** between concepts
- ✅ **Context-aware** responses
- ✅ **Project isolation** with `.aim` folders
- ✅ **Reduced token usage** (don't re-explain every time)

Start using it naturally - just tell Claude to "remember" things!
