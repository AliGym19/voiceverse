# VoiceVerse TTS Application - Claude Context

## Project Overview

**VoiceVerse** is a production-grade text-to-speech web application built with Flask and OpenAI's TTS API. It features AI-powered text processing agents, user authentication, audio library management, and enterprise security.

**Key Stats:**
- 85+ project files
- 6 premium voices (alloy, echo, fable, onyx, nova, shimmer)
- 5 AI agents for text optimization
- 9 automation scripts for DevOps
- SQLite database with user authentication

## Architecture

### Tech Stack
- **Backend:** Python 3.8+, Flask 2.3+
- **Database:** SQLite (voiceverse.db) with bcrypt password hashing
- **TTS API:** OpenAI TTS-1 and TTS-1-HD models
- **AI Agents:** OpenAI GPT-4o-mini for text processing
- **Security:** HTTPS/TLS support, session-based auth, rate limiting
- **Frontend:** Vanilla JavaScript, Spotify-inspired dark UI

### File Structure
```
TTS_App/
├── tts_app19.py              # Main Flask application (68K+ tokens - large file!)
├── tts_agents.py             # AI agent system (preprocessing, chunking, analysis)
├── voiceverse.db             # SQLite database
├── scripts/                  # 9 automation scripts
│   ├── app_manager.sh        # Start/stop/restart/monitor
│   ├── health_check.sh       # System diagnostics
│   ├── backup_db.sh          # Database backups
│   ├── restore_db.sh         # Database restoration
│   ├── quick_deploy.sh       # Rapid deployment
│   ├── cleanup.sh            # Maintenance tasks
│   ├── setup_dev.sh          # Dev environment setup
│   ├── aliases.sh            # Command shortcuts (20+)
│   └── install_aliases.sh    # Alias installer
├── saved_audio/              # Generated TTS audio files
├── certs/                    # SSL certificates
├── logs/                     # Application and security logs
└── .env                      # Environment configuration (GITIGNORED!)
```

### Database Schema (voiceverse.db)
- **users table:** id, username, password (bcrypt hashed), created_at, is_admin
- **audio_files table:** id, user_id, filename, voice, speed, text_preview, group_name, file_path, created_at
- **security_audit_log table:** Comprehensive security event logging with PII protection

### Important Admin User
- **Username:** ali.admin
- Created by previous AI assistant
- Admin role exists in database

## Critical Constraints

### Performance Targets
- **Latency:** Aim for sub-300ms response time (not achieved yet)
- **Streaming:** WebSocket streaming planned but not implemented
- **TTS Processing:** Depends on OpenAI API speed (typically 2-5 seconds)

### Cost Optimization
- **TTS-1 Model:** $0.015 per 1K characters (~$0.0075/min audio)
- **TTS-1-HD Model:** $0.030 per 1K characters (~$0.015/min audio)
- **AI Agents:** $0.001-0.003 per request (GPT-4o-mini)
- **Typical Cost:** $0.015-0.025 per generation
- **Redis Caching:** Planned but NOT implemented (would save 40-60% costs)

### Quality Standards
- AI preprocessing improves quality by 30-40%
- Smart chunking maintains narrative flow
- Quality analysis detects problematic text patterns
- Voice recommendations match content type

## Code Patterns & Conventions

### Key Patterns to Follow

1. **Always Use Async/Await for OpenAI Calls**
   ```python
   # Good - Uses async client
   response = await client.audio.speech.create(
       model="tts-1",
       voice=voice,
       input=text
   )

   # Bad - Blocking synchronous call
   response = client.audio.speech.create(...)
   ```

2. **Require Authentication on All Routes**
   ```python
   @app.route('/api/generate')
   @login_required
   def generate_audio():
       user_id = session['user_id']
       # ... rest of code
   ```

3. **Verify File Ownership Before Operations**
   ```python
   # Always check user_id matches
   file = get_audio_file(file_id)
   if file['user_id'] != session['user_id']:
       return jsonify({'error': 'Unauthorized'}), 403
   ```

4. **Use Parameterized Queries (SQL Injection Prevention)**
   ```python
   # Good - Safe from SQL injection
   cursor.execute("SELECT * FROM users WHERE username = ?", (username,))

   # Bad - NEVER use string formatting
   cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
   ```

5. **Implement Retry Logic with Exponential Backoff**
   ```python
   for attempt in range(max_retries):
       try:
           response = await openai_call()
           break
       except Exception as e:
           if attempt < max_retries - 1:
               wait_time = (2 ** attempt) * base_delay
               await asyncio.sleep(wait_time)
   ```

6. **Log Security Events**
   ```python
   from logger import SecurityLogger
   security_logger = SecurityLogger()
   security_logger.log_event('login_success', user_id, request)
   ```

### Common Gotchas

1. **Port 5000 Conflicts:** macOS AirPlay uses port 5000
   ```bash
   # Kill existing process
   lsof -ti:5000 | xargs kill -9
   ```

2. **Large File Warning:** `tts_app19.py` is 68K+ tokens
   - Use offset/limit when reading
   - Use Grep for specific searches
   - Consider code splitting in future refactor

3. **Database Lock Issues:** SQLite can lock with concurrent writes
   - Implement connection pooling
   - Use WAL mode (Write-Ahead Logging)

4. **API Key Security:** NEVER commit .env files
   - Always in .gitignore
   - Use environment variables in production

## Common Commands

### Quick Start
```bash
# Start the app (with timeout to prevent hanging)
timeout 5 python3 tts_app19.py

# Start in background
python3 tts_app19.py &

# View in browser
open http://localhost:5000
```

### Using Automation Scripts
```bash
# App management
./scripts/app_manager.sh start      # Start application
./scripts/app_manager.sh stop       # Stop application
./scripts/app_manager.sh restart    # Restart application
./scripts/app_manager.sh status     # Check status

# Health checks
./scripts/health_check.sh           # Full system diagnostics

# Database operations
./scripts/backup_db.sh              # Backup database
./scripts/restore_db.sh backup.db   # Restore from backup

# Deployment
./scripts/quick_deploy.sh           # Git pull + restart

# Maintenance
./scripts/cleanup.sh                # Clean old files and logs

# Development setup
./scripts/setup_dev.sh              # One-command dev environment

# Install command aliases
./scripts/install_aliases.sh        # Add 20+ shortcuts to shell
```

### Git Workflow
```bash
# Check status and differences
git status && git diff

# Create commit (already in main branch)
git add .
git commit -m "Your message"

# View commit history
git log --oneline -10
```

### Testing
```bash
# Test AI agents
python3 test_agents.py

# Check dependencies
pip3 list | grep -E "(Flask|openai|PyPDF2|python-docx)"

# Verify API key
echo $OPENAI_API_KEY
```

## AI Agent Features

### 5 Integrated AI Agents

1. **Smart Text Preprocessing Agent**
   - Cleans formatting artifacts from PDF/DOCX
   - Expands URLs to readable format
   - Expands acronyms for better pronunciation
   - Converts numbers to words when appropriate
   - **Cost:** ~$0.001-0.002 per request

2. **Smart Chunking Agent**
   - Splits text > 4,096 chars at natural boundaries
   - Maintains narrative flow between chunks
   - Prevents mid-sentence cuts
   - **Cost:** ~$0.001-0.003 per request

3. **Metadata Suggestion Agent**
   - Auto-generates filename, category, summary
   - Suggests optimal voice for content type
   - Identifies content type (narration, dialogue, technical)
   - **Cost:** ~$0.0005-0.001 per request

4. **Quality Analysis Agent**
   - Analyzes TTS suitability
   - Detects problematic patterns (code, URLs, long numbers)
   - Estimates duration and cost
   - Provides quality score and warnings
   - **Cost:** ~$0.0002-0.0005 per request

5. **Voice Recommendation Agent**
   - Analyzes content tone and style
   - Recommends best voice from 6 options
   - Provides reasoning for recommendation

### Agent API Endpoints
- `POST /api/agent/preprocess` - Preprocess text
- `POST /api/agent/suggest-metadata` - Get metadata suggestions
- `POST /api/agent/analyze` - Analyze text quality
- `POST /api/agent/smart-chunk` - Smart chunking

## Testing Standards

### What to Test
1. **Latency Tests:** Measure TTS generation time
2. **Quality Tests:** Use Word Error Rate (WER) for accuracy
3. **Error Handling:** Test API failures, network issues, invalid inputs
4. **Security Tests:** SQL injection, XSS, CSRF, rate limiting
5. **Agent Tests:** Run `test_agents.py` after agent changes

### Test Commands
```bash
# Run agent tests
python3 test_agents.py

# Check app health
./scripts/health_check.sh

# Test API endpoint (example)
curl -X POST http://localhost:5000/api/agent/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Test content here"}'
```

## Development Workflow

### Starting New Feature
1. Read relevant code sections (use offset/limit for large files)
2. Check existing patterns in codebase
3. Review security implications
4. Update tests if needed
5. Test with automation scripts

### Making Changes to tts_app19.py
- **File is 68K+ tokens** - Too large to read in one go
- Use Grep to find specific functions
- Use offset/limit to read sections
- Consider refactoring into modules (future task)

### Before Committing
1. Test with `./scripts/health_check.sh`
2. Run `python3 test_agents.py` if agents changed
3. Check no secrets in code
4. Verify .env not staged: `git status`

### Debugging Issues
1. Check logs: `tail -f logs/security_audit.log`
2. Run health check: `./scripts/health_check.sh`
3. Check database: `sqlite3 voiceverse.db`
4. Kill port conflicts: `lsof -ti:5000 | xargs kill -9`

## MCP Server Usage

### Available MCP Servers

This project is configured with three MCP (Model Context Protocol) servers that enhance Claude Code's capabilities:

#### 1. Knowledge Graph MCP
- **Purpose:** Store and retrieve persistent memories across sessions
- **Use for:** Tracking project context, user preferences, technical decisions
- **Tools:** `aim_create_entities`, `aim_search_nodes`, `aim_read_graph`, etc.

#### 2. Context7 MCP
- **Purpose:** Fetch up-to-date documentation for programming languages and frameworks
- **Use for:** Getting correct API docs, latest syntax, best practices
- **Important:** ALWAYS use Context7 to pull documentation for the language/framework you're writing in
- **Example usage:**
  - When writing Python code: Fetch Flask, SQLAlchemy, or OpenAI SDK documentation
  - When writing JavaScript: Fetch latest Node.js, npm, or browser API documentation
  - When debugging: Look up error messages and solutions

#### 3. Puppeteer MCP
- **Purpose:** Browser automation for testing frontend interfaces
- **Use for:** Testing UI layouts, interactions, form submissions, responsive design
- **Important:** Use Puppeteer MCP to test the frontend after making layout changes
- **Example usage:**
  - Navigate to http://localhost:5000 and verify three-column layout
  - Test "Create New" page renders correctly
  - Verify form submissions work end-to-end
  - Take screenshots of UI for visual verification

### When to Use MCP Servers

**Context7 Documentation Fetching:**
```
When writing code in ANY language:
1. Before implementing a feature, fetch current documentation
2. Check for deprecated methods or updated APIs
3. Verify correct import statements and usage patterns
4. Look up error codes and troubleshooting guides

Example: "Fetch Flask render_template_string documentation from Context7"
```

**Puppeteer Frontend Testing:**
```
After ANY frontend changes:
1. Use Puppeteer to navigate to the page
2. Verify layout renders correctly
3. Test interactive elements (buttons, forms, dropdowns)
4. Capture screenshots for visual confirmation
5. Test responsive behavior at different screen sizes

Example: "Use Puppeteer MCP to test the Create New Audio page layout at http://localhost:5000"
```

**Knowledge Graph Memory:**
```
For persistent project context:
1. Store important technical decisions
2. Remember user preferences and settings
3. Track known bugs and their solutions
4. Document architectural patterns used

Example: "Store in knowledge graph: User prefers Frutiger Aero design aesthetic"
```

### MCP Configuration

Configuration file: `~/.mcp.json`

```json
{
  "mcpServers": {
    "knowledge-graph": {
      "command": "npx",
      "args": ["-y", "mcp-knowledge-graph", "--memory-path", "/Users/ali/.knowledge-graph/"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    }
  }
}
```

## Environment Configuration

### Required Environment Variables (.env)
```bash
# Generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-secret-key-here

# From OpenAI platform
OPENAI_API_KEY=your-api-key-here

# App settings
DEBUG=true                    # false in production
HOST=127.0.0.1               # 0.0.0.0 for external access
PORT=5000

# Security
USE_HTTPS=false              # true in production
SECURE_COOKIES=false         # true with HTTPS
SESSION_LIFETIME=3600        # 1 hour
```

### Pre-Approved Commands
These commands can run without approval:
- `python3 tts_app19.py` (with timeout)
- `lsof -ti:5000 | xargs kill -9`
- All `./scripts/*` automation scripts
- `git status`, `git log`, `git diff`
- `pip3 install` commands

## Future Enhancements (Roadmap)

### High Priority (Not Implemented Yet)
- [ ] **Redis Caching:** 40-60% cost savings on repeated content
- [ ] **WebSocket Streaming:** Sub-300ms latency for real-time TTS
- [ ] **Code Refactoring:** Split tts_app19.py into modules

### Medium Priority
- [ ] Voice cloning support
- [ ] Batch processing for multiple files
- [ ] SSML support for advanced control
- [ ] Multi-language support

### Low Priority
- [ ] Cloud storage integration
- [ ] Mobile app
- [ ] Analytics dashboard
- [ ] Collaborative features

## Key Documentation Files

- **README.md** - Project overview and quick start
- **DEPLOYMENT.md** - Production deployment guide
- **SECURITY.md** - Security features and best practices
- **AI_AGENTS_README.md** - AI agents documentation
- **IMPLEMENTATION_ROADMAP.md** - Development phases

## Quick Reference

### Voice Options
| Voice | Description | Best For |
|-------|-------------|----------|
| alloy | Neutral, versatile | Tutorials, documentation |
| echo | Male, clear | Technical content, professional |
| fable | British male | Storytelling, audiobooks |
| onyx | Deep male | Authority, news, formal |
| nova | Female, warm | Friendly content, guides |
| shimmer | Soft female | Meditation, calm narration |

### Time Savings with Automation Scripts
- **21 minutes saved per day**
- **10.5 hours saved per month**
- **126 hours saved per year**

### Security Checklist for Production
- [ ] Change SECRET_KEY to strong random value
- [ ] Set DEBUG=false
- [ ] Enable SECURE_COOKIES=true
- [ ] Configure HTTPS with valid SSL certificate
- [ ] Set up Fail2ban for brute-force protection
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Review security audit logs regularly

## Working with Claude Code

### When Reading Large Files
```bash
# tts_app19.py is too large - use these strategies:
# 1. Use Grep to find specific functions
# 2. Use Read with offset/limit for sections
# 3. Ask Claude to use Explore agent for code understanding
```

### Preferred Development Flow
1. Use Plan Mode (Shift+Tab) for complex features
2. Read relevant files first
3. Make incremental changes
4. Test with automation scripts
5. **After finishing a new feature, call the expert-code-reviewer agent and implement its suggestions**
6. Commit with descriptive messages

### Custom Commands (To Be Created)
Future custom commands to consider:
- `/test-audio` - Quick TTS generation test
- `/optimize-latency` - Profile and optimize slow endpoints
- `/check-costs` - Estimate API costs for content
- `/backup-now` - Quick database backup

---

**Last Updated:** 2025-10-30
**Maintained by:** Ali (ali.admin)
**Claude Version:** Sonnet 4.5
