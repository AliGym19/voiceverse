# Knowledge Graph Best Practices for Long-Term Success

## Core Philosophy

The knowledge graph is **not a dump** - it's a **structured memory system**. Quality over quantity.

---

## 1. Entity Design Patterns

### ✅ Good Entity Design

```
Entity: "tts_app19.py"
Type: "file"
Observations:
  - "Main Flask application (1,500 lines)"
  - "68K+ tokens - use offset/limit for reading"
  - "Contains: API endpoints, auth, TTS generation"
  - "Port: 5000 (conflicts with macOS AirPlay)"
```

**Why good:** Specific, actionable, focused

### ❌ Poor Entity Design

```
Entity: "main file"
Type: "thing"
Observations:
  - "important"
  - "has code"
```

**Why bad:** Vague, no context, not searchable

---

## 2. Relationship Best Practices

### Use Clear, Active Voice Relations

| ✅ Good | ❌ Avoid |
|---------|----------|
| `tts_app19.py` → `imports` → `tts_agents.py` | `tts_app19.py` → `related_to` → `tts_agents.py` |
| `Flask` → `provides_framework_for` → `TTS_App` | `Flask` → `used_by` → `TTS_App` |
| `OpenAI API` → `powers` → `TTS Generation` | `OpenAI API` → `connected` → `TTS Generation` |

**Principle:** Relations should read like natural sentences when traversed.

---

## 3. Observation Guidelines

### Atomic & Independent

Each observation should be:
- **Self-contained** - Understandable alone
- **Atomic** - One fact per observation
- **Timestamped mentally** - Update when outdated

### ✅ Good Observations

```
- "Cost: $0.015 per 1K characters (TTS-1 model)"
- "Admin user: ali.admin (created 2025-10-30)"
- "Testing: Run test_agents.py after agent changes"
- "Performance target: sub-300ms (not yet achieved)"
```

### ❌ Poor Observations

```
- "costs money"
- "has admin"
- "need to test"
- "performance"
```

---

## 4. Entity Type Taxonomy

Use consistent types for easier querying:

### Standard Types

| Type | Use For | Examples |
|------|---------|----------|
| `file` | Source code files | `tts_app19.py`, `tts_agents.py` |
| `directory` | Folders | `scripts/`, `saved_audio/` |
| `database` | DB instances | `voiceverse.db` |
| `table` | DB tables | `users`, `audio_files` |
| `api` | External APIs | `OpenAI TTS API`, `GPT-4o-mini` |
| `person` | Team members | `ali.admin`, `Cole (contractor)` |
| `feature` | App features | `AI Agents System`, `Authentication` |
| `issue` | Known problems | `Port 5000 Conflict`, `Large file read` |
| `best_practice` | Coding patterns | `Parameterized Queries`, `Retry Logic` |
| `configuration` | Settings | `Voice Options`, `Environment Variables` |
| `technical_debt` | Future work | `Code Refactoring Task`, `Redis Caching` |
| `process` | Workflows | `Testing Protocol`, `Deployment Process` |
| `requirement` | Specs | `Performance Requirements`, `Security Standards` |
| `cost` | Pricing info | `TTS API Costs`, `Agent Costs` |
| `library` | Dependencies | `Flask`, `OpenAI`, `bcrypt` |

---

## 5. When to Create Entities

### DO Create Entities For:

✅ **Files you reference often**
   - `tts_app19.py`, `tts_agents.py`, `voiceverse.db`

✅ **Persistent gotchas**
   - Port conflicts, large file issues, API quirks

✅ **Core concepts**
   - Authentication system, AI agents, TTS generation

✅ **People & roles**
   - Team members, admin users, stakeholders

✅ **External dependencies**
   - OpenAI API, Flask framework, bcrypt

✅ **Architectural decisions**
   - "Why we chose Flask", "Why SQLite not PostgreSQL"

### DON'T Create Entities For:

❌ **Temporary debugging info**
   - "Bug in line 42" (will be fixed)

❌ **Obvious facts**
   - "Python uses indentation" (general knowledge)

❌ **One-time tasks**
   - "Install package X today" (transient)

❌ **Personal notes unrelated to code**
   - "Buy milk" (use personal todo list)

---

## 6. Maintenance Schedule

### After Each Major Change

🔄 **Update entities** when:
- Completing a feature → Add observations about implementation
- Fixing a bug → Update the issue entity or remove if resolved
- Refactoring → Update file descriptions and relationships
- Adding dependencies → Create library entities and relations

### Weekly Review

📅 **Every week:**
1. Search for outdated observations
2. Remove resolved issues
3. Update cost information (if changed)
4. Add newly discovered gotchas

### Monthly Audit

📊 **Every month:**
1. Review all entities for relevance
2. Consolidate duplicate entities
3. Ensure relations are bidirectional where needed
4. Archive/delete obsolete entities

---

## 7. Context Separation Strategies

### Use Named Databases

```
memory.jsonl          → General TTS_App knowledge
memory-personal.jsonl → Your preferences, learning notes
memory-work.jsonl     → Client requirements, deadlines
memory-research.jsonl → Experimental features, POCs
```

**When to use:**
- Personal: Learning notes, preferences, shortcuts
- Work: Client info, deadlines, priorities
- Research: Experimental ideas not yet in main code

---

## 8. Project-Specific Memory (.aim)

### What Belongs in Project Memory

✅ **Project-specific:**
- File structures specific to this project
- Local gotchas (port conflicts, environment issues)
- Project team members
- Architecture decisions for this project

❌ **Should be global:**
- General programming knowledge
- Universal best practices (DRY, SOLID)
- Personal preferences across all projects

---

## 9. Querying Patterns

### Effective Questions

| ✅ Specific | ❌ Vague |
|------------|----------|
| "What files import tts_agents.py?" | "What uses agents?" |
| "What's the cost of TTS-1-HD model?" | "How much does it cost?" |
| "What's our admin username?" | "Who's the admin?" |
| "What should I check before deploying?" | "Deployment stuff?" |

### Relationship Queries

- "What depends on OpenAI API?"
- "What implements the Authentication feature?"
- "What issues are related to performance?"

---

## 10. Migration from CLAUDE.md

### Phase 1: Core Infrastructure (Week 1)

```
Priority entities:
- tts_app19.py (main file)
- tts_agents.py (AI system)
- voiceverse.db (database)
- scripts/ automation
```

### Phase 2: Relationships (Week 2)

```
Key relations:
- File imports
- Feature implementations
- API dependencies
```

### Phase 3: Knowledge (Week 3)

```
Soft knowledge:
- Best practices
- Gotchas
- Performance targets
- Cost information
```

### Phase 4: Maintenance (Ongoing)

```
Keep CLAUDE.md for:
- Quick reference
- File structure overview

Use knowledge graph for:
- Relationships
- Historical decisions
- Contextual queries
```

---

## 11. Collaboration with Knowledge Graph

### For Solo Developers

- **Document decisions** as you make them
- **Track technical debt** for future you
- **Remember "why"** not just "what"

### For Teams (Future)

- **Shared .mcp.json** in repo (committed)
- **Separate .aim/** for shared project memory
- **Personal context** in your own memory-personal.jsonl
- **Document onboarding info** for new team members

---

## 12. Anti-Patterns to Avoid

### ❌ The "Everything Entity"

```
Entity: "TTS_App"
Observations:
  - "Flask app with AI agents and OpenAI API..."
  - "Has database with users and audio files..."
  - "Ports are 5000..."
  - [100 more observations]
```

**Problem:** Too broad, hard to maintain, not granular

**Solution:** Break into separate entities (app, agents, DB, config)

### ❌ The "Duplicate Forest"

```
Entity: "tts_app19.py"
Entity: "tts_app19"
Entity: "main file"
Entity: "Flask app"
```

**Problem:** Same concept, multiple entities

**Solution:** One canonical entity, use search to find

### ❌ The "Dead Relations"

```
old_file.py → imports → deleted_file.py
```

**Problem:** Relations to non-existent entities

**Solution:** Delete relations when deleting entities

### ❌ The "Observation Novel"

```
Observation: "This file is 68K tokens which is really large
              and so you should use offset and limit when reading
              it because otherwise you'll hit token limits and
              it was created on Oct 30th and has Flask and OpenAI..."
```

**Problem:** Multiple facts in one observation

**Solution:** Split into atomic observations

---

## 13. Performance Optimization

### Token Efficiency

Knowledge graph **reduces token usage** by:
- Avoiding re-reading large context files
- Querying specific information
- Traversing relationships instead of text search

### When Knowledge Graph > File Reading

| Scenario | Use Graph | Use File |
|----------|-----------|----------|
| "What's the admin username?" | ✅ Fast query | ❌ Grep + read |
| "What files use OpenAI?" | ✅ Relation traversal | ❌ Grep all files |
| "Show me the login function code" | ❌ Need actual code | ✅ Read file |
| "What's our performance target?" | ✅ Fast observation | ❌ Search docs |

---

## 14. Security Considerations

### What NOT to Store

🚫 **Never store in knowledge graph:**
- API keys (use .env)
- Passwords (use password manager)
- Private user data (use encrypted DB)
- Session tokens (ephemeral)

### What's Safe to Store

✅ **Safe to store:**
- File structures
- Architecture decisions
- Best practices
- Non-sensitive configuration
- Public user IDs (like "ali.admin")

---

## 15. Versioning & History

### Track Changes Over Time

```
Entity: "Authentication System"
Observations:
  - "v1: Basic auth with plaintext passwords (deprecated)"
  - "v2: bcrypt hashing implemented 2025-10-15"
  - "v3: Planning session tokens + JWT (roadmap)"
```

**Benefit:** Understand evolution of the system

---

## 16. Testing Your Knowledge Graph

### Validation Questions

Test your graph by asking:

1. **Completeness**: "What files make up the core app?"
2. **Relationships**: "What depends on OpenAI API?"
3. **Gotchas**: "What should I watch out for?"
4. **History**: "Why did we choose Flask?"
5. **Roadmap**: "What's in the high-priority backlog?"

If Claude can't answer, add those entities!

---

## 17. Recovery & Backup

### Backup Strategy

```bash
# Backup global knowledge graph
cp -r ~/.knowledge-graph/ ~/backups/kg-$(date +%Y%m%d)/

# Backup project memory
cp -r .aim/ .aim.backup-$(date +%Y%m%d)/

# Version control .mcp.json (auto-backed up with git)
git add .mcp.json
git commit -m "Update MCP configuration"
```

### Disaster Recovery

If memory files are corrupted:
1. Restore from backup
2. Rebuild from CLAUDE.md (use migration guide)
3. Ask Claude to read git history for context

---

## 18. Advanced: Cross-Project Knowledge

### Global Entities (in ~/.knowledge-graph/)

Store cross-project knowledge:

```
Entity: "My Coding Preferences"
Type: "personal"
Observations:
  - "Prefer async/await over callbacks"
  - "Add detailed comments for complex logic"
  - "Use type hints in Python"

Entity: "macOS Port Conflicts"
Type: "issue"
Observations:
  - "Port 5000: AirPlay"
  - "Port 3000: Common Node.js dev servers"
  - "Always check: lsof -i :PORT"
```

### Project-Specific (in .aim/)

Keep project-unique knowledge:

```
Entity: "VoiceVerse Architecture"
Type: "architecture"
Observations:
  - "Monolithic Flask app (for now)"
  - "SQLite for simplicity (< 10k users)"
  - "OpenAI TTS API (no alternatives evaluated)"
```

---

## 19. Success Metrics

Track knowledge graph effectiveness:

### Qualitative Signals

✅ Claude remembers context across sessions
✅ Fewer "I don't see that in the codebase" responses
✅ More accurate suggestions based on project patterns
✅ Less time explaining the same concepts

### Quantitative Metrics

📊 **Count:**
- Entities created per week
- Relations established
- Queries answered without file reads

---

## 20. Future-Proofing

### As Project Grows

- **Split by module**: Create sub-contexts for major features
- **Use more named DBs**: Separate concerns (api, frontend, backend)
- **Archive old entities**: Keep historical context without clutter

### As Team Grows

- **Shared .mcp.json**: Team-wide knowledge in VCS
- **Personal contexts**: Keep your preferences separate
- **Documentation sync**: Keep CLAUDE.md and graph aligned

---

## Quick Reference Card

### When to Use Knowledge Graph

| Situation | Action |
|-----------|--------|
| Discovered a gotcha | Create `issue` entity |
| Made architectural decision | Create `architecture` entity with reasoning |
| Added new file | Create `file` entity + relations |
| Found external dependency | Create `library` entity + `depends_on` relation |
| Changed cost structure | Update `cost` entity observations |
| Fixed a bug | Update or remove `issue` entity |
| Completed feature | Add observations to `feature` entity |
| Found best practice | Create `best_practice` entity |

---

## Summary: The Path to Knowledge Graph Mastery

1. **Week 1**: Start small - core files and relationships
2. **Week 2**: Add gotchas and best practices as you find them
3. **Week 3**: Populate cost, configuration, and architecture info
4. **Week 4**: Review and refine - delete obsolete, consolidate duplicates
5. **Month 2+**: Maintenance mode - update as you code

The knowledge graph becomes **more valuable over time** as it accumulates project wisdom.

**Remember:** Quality beats quantity. 20 well-structured entities > 100 vague ones.
