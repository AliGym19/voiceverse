@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per 15 minutes")  # Security: Prevent brute force attacks
def login():
    error = None
    if request.method == 'POST':
        # Security: Get and hash IP address for privacy-preserving lockout tracking
        user_ip = request.remote_addr
        hashed_ip = hash_ip(user_ip)

        # Security: Check lockout status before processing login
        lockout_status = lockout.check_and_record(hashed_ip)

        if lockout_status['locked']:
            # Account is locked - show lockout message
            remaining = lockout_status['remaining_seconds']
            error = f"Too many failed login attempts. Account locked for {remaining} seconds. Please try again later."
            log_security_event('LOGIN_BLOCKED', f'Account locked, {remaining}s remaining', success=False)

            # Send email alert if this is a new lockout
            if lockout_status['should_alert']:
                try:
                    alerts.send_lockout_alert(
                        identifier_hash=hashed_ip,
                        attempt_count=lockout_status['attempt_count'],
                        lockout_duration=60
                    )
                    log_security_event('ALERT_SENT', f'Lockout email alert sent for {hashed_ip[:8]}...', success=True)
                except Exception as e:
                    log_security_event('ALERT_FAILED', f'Failed to send lockout alert: {str(e)}', success=False)

            return render_template_string(AUTH_TEMPLATE, error=error, mode='login')

        # Process login credentials
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            error = "Please enter both username and password"
            log_security_event('LOGIN_ATTEMPT', f'Empty credentials', username=username, success=False)
        elif verify_user(username, password):
            # Successful login - clear lockout attempts
            lockout.clear_attempts(hashed_ip)
            session['username'] = username
            log_security_event('LOGIN', f'User logged in', username=username, success=True)
            return redirect(url_for('index'))
        else:
            error = "Invalid username or password"
            log_security_event('LOGIN_ATTEMPT', f'Invalid credentials (attempt {lockout_status["attempt_count"]})', username=username, success=False)

    return render_template_string(AUTH_TEMPLATE, error=error, mode='login')

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per 15 minutes")  # Security: Prevent account creation spam
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if not username or not password:
            error = "Please enter both username and password"
            log_security_event('REGISTER_ATTEMPT', 'Empty credentials', username=username, success=False)
        elif len(username) < 3:
            error = "Username must be at least 3 characters"
            log_security_event('REGISTER_ATTEMPT', 'Username too short', username=username, success=False)
        elif password != confirm:
            error = "Passwords do not match"
            log_security_event('REGISTER_ATTEMPT', 'Password mismatch', username=username, success=False)
        else:
            # Security: Validate password strength
            is_valid, validation_error = validate_password(password)
            if not is_valid:
                error = validation_error
                log_security_event('REGISTER_ATTEMPT', f'Weak password: {validation_error}', username=username, success=False)
            elif create_user(username, password):
                session['username'] = username
                log_security_event('REGISTER', 'New user account created', username=username, success=True)
                return redirect(url_for('index'))
            else:
                error = "Username already exists"
                log_security_event('REGISTER_ATTEMPT', 'Username already exists', username=username, success=False)

    return render_template_string(AUTH_TEMPLATE, error=error, mode='register')

@app.route('/switch-account/<username>')
@login_required
def switch_account(username):
    """Switch to a different user account without requiring password"""
    # Verify the target user exists
    user = db.get_user(username)
    if user:
        session['username'] = username
        db.update_last_login(user['id'])
        return redirect(url_for('index'))
    return redirect(url_for('login'))

# AI Discovery & Documentation Routes
@app.route('/robots.txt')
def robots_txt():
    """Serve robots.txt for AI crawler guidance"""
    return send_file('static/robots.txt', mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap_xml():
    """Serve XML sitemap for search engines and AI crawlers"""
    return send_file('static/sitemap.xml', mimetype='application/xml')

@app.route('/openapi.json')
def openapi_spec():
    """Serve OpenAPI 3.1.0 specification for API documentation"""
    return send_file('static/openapi.json', mimetype='application/json')

@app.route('/api-docs')
def api_docs():
    """Serve human-readable API documentation"""
    return jsonify({
        "name": "VoiceVerse API",
        "version": "1.0.0",
        "description": "AI-powered text-to-speech API",
        "documentation": {
            "openapi_spec": "/openapi.json",
            "base_url": request.url_root,
            "authentication": "Session-based (login required for web interface)"
        },
        "endpoints": {
            "audio_generation": {
                "POST /": "Generate audio from text",
                "parameters": {
                    "text": "Text to convert (max 50,000 chars)",
                    "voice": "alloy|echo|fable|onyx|nova|shimmer",
                    "speed": "0.25-4.0 (default: 1.0)",
                    "filename": "Custom filename",
                    "group": "Category/group name",
                    "use_preprocessing": "Enable AI text preprocessing",
                    "use_chunking": "Enable smart chunking for long text"
                }
            },
            "file_management": {
                "GET /api/history": "Get playback history",
                "GET /api/groups": "Get file groups",
                "POST /api/clear-history": "Clear playback history",
                "POST /api/move-to-group": "Move files to a group"
            },
            "document_parsing": {
                "POST /api/parse-docx": "Extract text from DOCX files",
                "POST /api/parse-pdf": "Extract text from PDF files"
            },
            "ai_features": {
                "POST /api/agent/preprocess": "AI text preprocessing",
                "POST /api/agent/suggest-metadata": "AI metadata suggestions",
                "POST /api/agent/analyze": "AI text quality analysis",
                "POST /api/agent/smart-chunk": "Smart text chunking"
            }
        },
        "voices": {
            "alloy": "Neutral, balanced tone - ideal for tutorials and general content",
            "echo": "Male voice, clear - suitable for technical and professional content",
            "fable": "British accent, expressive - perfect for storytelling and audiobooks",
            "onyx": "Deep, authoritative - great for news and formal content",
            "nova": "Female voice, friendly - excellent for guides and conversational content",
            "shimmer": "Soft, warm tone - best for soothing and calm narration"
        },
        "features": [
            "Multiple AI voices with distinct characteristics",
            "Adjustable speech speed (0.25x - 4.0x)",
            "Smart text preprocessing for better speech quality",
            "Intelligent chunking for texts over 4,096 characters",
            "Document upload support (TXT, DOCX, PDF)",
            "Audio file organization with groups",
            "Usage tracking and cost estimation",
            "Voice comparison tool",
            "Playback history"
        ]
    })

@app.route('/capabilities')
def capabilities():
    """Machine-readable endpoint for AI agents to understand app capabilities"""
    return jsonify({
        "application": {
            "name": "VoiceVerse",
            "type": "text-to-speech",
            "version": "1.0.0",
            "api_version": "1.0.0"
        },
        "capabilities": {
            "text_to_speech": {
                "enabled": True,
                "max_characters": 50000,
                "chunk_size": 4096,
                "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                "speed_range": {"min": 0.25, "max": 4.0},
                "formats": ["mp3"]
            },
            "ai_features": {
                "text_preprocessing": True,
                "smart_chunking": True,
                "metadata_suggestions": True,
                "text_analysis": True
            },
            "document_parsing": {
                "formats": ["txt", "docx", "pdf"],
                "max_file_size": 16777216
            },
            "file_management": {
                "groups": True,
                "history": True,
                "search": True,
                "bulk_operations": True
            },
            "api_access": {
                "rest_api": True,
                "websocket": False,
                "graphql": False
            }
        },
        "limits": {
            "max_text_length": 50000,
            "max_filename_length": 100,
            "max_group_name_length": 50,
            "max_file_size": 16777216,
            "rate_limit": "50 requests per hour per user"
        },
        "authentication": {
            "methods": ["session"],
            "required": True
        },
        "documentation": {
            "openapi": "/openapi.json",
            "api_docs": "/api-docs",
            "ai_info": "/ai-info"
        }
    })

@app.route('/ai-info')
def ai_info():
    """Comprehensive AI-friendly information about the application"""
    return jsonify({
        "application": {
            "name": "VoiceVerse",
            "description": "An AI-powered text-to-speech application that converts text into natural, high-quality audio using advanced voice synthesis technology from OpenAI.",
            "tagline": "Convert Text to Natural Speech with AI",
            "category": "Multimedia/Text-to-Speech",
            "version": "1.0.0",
            "url": request.url_root
        },
        "for_ai_agents": {
            "what_this_app_does": "VoiceVerse allows you to convert text into spoken audio using AI-generated voices. It provides features for managing audio files, organizing them into groups, and enhancing text quality before conversion.",
            "primary_use_cases": [
                "Converting articles or blog posts to audio for accessibility",
                "Creating audiobook narrations",
                "Generating voice-overs for presentations",
                "Converting study materials to audio format",
                "Creating podcast content from written scripts",
                "Accessibility for visually impaired users"
            ],
            "how_to_use": {
                "step_1": "Create an account and log in",
                "step_2": "Navigate to 'Create New' section",
                "step_3": "Enter or upload your text (supports TXT, DOCX, PDF)",
                "step_4": "Choose a voice that matches your content style",
                "step_5": "Optionally enable AI preprocessing or smart chunking",
                "step_6": "Click 'Generate Audio' to create your audio file",
                "step_7": "Play, download, or organize your audio files into groups"
            },
            "api_integration": {
                "authentication": "Session-based (requires login)",
                "content_type": "application/x-www-form-urlencoded or application/json",
                "response_format": "HTML for web interface, JSON for API endpoints",
                "error_handling": "Returns appropriate HTTP status codes with descriptive messages"
            }
        },
        "features": {
            "voice_options": {
                "count": 6,
                "voices": {
                    "alloy": {
                        "type": "neutral",
                        "best_for": ["tutorials", "general content", "balanced narration"],
                        "characteristics": "Neutral, balanced tone"
                    },
                    "echo": {
                        "type": "male",
                        "best_for": ["technical content", "professional presentations", "corporate"],
                        "characteristics": "Clear, professional male voice"
                    },
                    "fable": {
                        "type": "british_expressive",
                        "best_for": ["storytelling", "audiobooks", "creative content"],
                        "characteristics": "British accent, expressive, engaging"
                    },
                    "onyx": {
                        "type": "authoritative",
                        "best_for": ["news", "formal announcements", "documentary"],
                        "characteristics": "Deep, authoritative, commanding"
                    },
                    "nova": {
                        "type": "female_friendly",
                        "best_for": ["guides", "tutorials", "conversational content"],
                        "characteristics": "Friendly female voice, approachable"
                    },
                    "shimmer": {
                        "type": "soothing",
                        "best_for": ["meditation", "calm narration", "relaxation"],
                        "characteristics": "Soft, warm, soothing"
                    }
                }
            },
            "ai_enhancements": {
                "preprocessing": "Cleans text, fixes formatting, expands URLs and acronyms for better speech quality",
                "smart_chunking": "Intelligently splits long text at natural boundaries instead of arbitrary character limits",
                "metadata_suggestions": "AI analyzes your text and suggests appropriate filename, category, and voice",
                "text_analysis": "Identifies potential issues in text that may affect speech quality"
            },
            "file_management": {
                "organization": "Group files by category (work, personal, projects, etc.)",
                "search": "Search through your audio library",
                "bulk_operations": "Select and manage multiple files at once",
                "playback_history": "Track recently played audio files"
            }
        },
        "technical_details": {
            "powered_by": "OpenAI Text-to-Speech API",
            "audio_format": "MP3",
            "max_input_length": "50,000 characters",
            "single_request_limit": "4,096 characters (use smart chunking for longer texts)",
            "supported_upload_formats": ["TXT", "DOCX", "PDF"],
            "max_upload_size": "16 MB",
            "pricing_model": "Pay-per-character usage (OpenAI API costs apply)"
        },
        "accessibility": {
            "aria_labels": True,
            "semantic_html": True,
            "keyboard_navigation": True,
            "screen_reader_compatible": True,
            "wcag_compliance": "Designed with WCAG 2.1 guidelines in mind"
        },
        "schema_org_data": True,
        "open_graph_tags": True,
        "sitemap": "/sitemap.xml",
        "robots_txt": "/robots.txt",
        "openapi_spec": "/openapi.json"
    })

@app.route('/logout')
def logout():
    # Security: Log logout event before clearing session
    username = session.get('username', 'anonymous')
    log_security_event('LOGOUT', 'User logged out', username=username)

    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    error = None
    success = request.args.get('success') == '1'
    filename = request.args.get('play_file')
    file_display_name = request.args.get('play_name')

    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        text = text.encode('utf-8', 'ignore').decode('utf-8').strip()
        voice = validate_voice(request.form.get('voice', 'nova'))
        file_name = sanitize_display_name(request.form.get('filename', 'audio'))
        group_input = request.form.get('group', '').strip()
        group = sanitize_display_name(group_input) if group_input else 'Uncategorized'
        group = group[:50] if group else 'Uncategorized'

        # Get speed parameter (default 1.0)
        try:
            speed = float(request.form.get('speed', 1.0))
            speed = max(0.25, min(4.0, speed))  # Clamp between 0.25 and 4.0
        except:
            speed = 1.0

        # Security: Validate input length (prevent DoS attacks)
        if len(text) > 100000:
            error = "Text is too long. Maximum 100,000 characters allowed."
        elif not text:
            error = "Please enter some text"
        elif not file_name:
            error = "Please enter a valid file name"
        else:
            try:
                # AI Agent: Preprocess text for better TTS quality
                use_ai_preprocessing = request.form.get('use_preprocessing', 'off') == 'on'
                if use_ai_preprocessing:
                    try:
                        agents = get_agent_system()
                        text = agents.preprocess_text(text)
                        print(f"✅ Text preprocessed by AI agent")
                    except Exception as e:
                        print(f"⚠️ AI preprocessing failed, using original text: {e}")

                # Handle long text with smart chunking or simple truncation
                original_length = len(text)
                use_smart_chunking = request.form.get('use_chunking', 'off') == 'on'

                if original_length > 4096:
                    if use_smart_chunking:
                        # AI Agent: Smart chunking for multi-part audio
                        try:
                            agents = get_agent_system()
                            chunks = agents.smart_chunk(text, 4000)
                            print(f"✅ Text split into {len(chunks)} chunks by AI agent")
                            # For now, use first chunk (future: generate multiple files)
                            text = chunks[0]['text']
                            print(f"📝 Using chunk 1/{len(chunks)} ({len(text)} chars)")
                        except Exception as e:
                            print(f"⚠️ Smart chunking failed, truncating: {e}")
                            text = text[:4096]
                    else:
                        # Simple truncation (original behavior)
                        text = text[:4096]
                        print(f"⚠️ Text truncated from {original_length} to 4,096 characters for TTS generation")

                client = get_openai_client()

                response = client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=text,
                    speed=speed
                )

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = secure_filename(f"{file_name}_{timestamp}.mp3")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)

                try:
                    if hasattr(response, 'stream_to_file'):
                        response.stream_to_file(filepath)
                        print(f'✅ Saved using stream_to_file at: {filepath}')
                    else:
                        audio_bytes = getattr(response, 'content', None)
                        if audio_bytes is None and hasattr(response, 'read'):
                            audio_bytes = response.read()
                        if audio_bytes:
                            with open(filepath, 'wb') as f:
                                f.write(audio_bytes)
                            print(f'✅ Saved audio file at: {filepath}')
                        else:
                            print('⚠️ No audio bytes found in OpenAI response.')
                except Exception as e:
                    print(f'❌ Error saving file: {e}')

                char_count = len(text)
                cost = calculate_cost(char_count)

                # Get user ID for database operations
                user = db.get_user(session['username'])
                if not user:
                    error = "User not found"
                else:
                    # Save file metadata to database
                    db.create_audio_file(
                        filename=safe_filename,
                        display_name=file_name,
                        owner_id=user['id'],
                        voice=voice,
                        category=group,
                        text=text,
                        character_count=char_count,
                        cost=cost
                    )

                    # Record usage statistics
                    db.record_usage(user['id'], char_count, cost)

                    # Redirect to home page to show the newly created file
                    return redirect(url_for('index', success='1', play_file=safe_filename, play_name=file_name))

            except ValueError as ve:
                error = str(ve)
            except Exception as e:
                error = f"An error occurred: {str(e)}"
                print(f"Error in audio generation: {e}")
    
    # Get user ID for database queries
    user = db.get_user(session['username'])
    if not user:
        return redirect(url_for('login'))

    # Get files for this user from database
    audio_files_db = db.get_audio_files_by_owner(user['id'])

    all_files = [
        {
            'filename': file_info['filename'],
            'name': file_info['display_name'],
            'group': file_info['category'] or 'Uncategorized',
            'created': file_info['created_at'],
            'chars': file_info['character_count'],
            'cost': file_info['cost']
        }
        for file_info in audio_files_db
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], file_info['filename']))
    ]

    all_files.sort(key=lambda x: x['created'], reverse=True)
    recent_files = all_files[:12]

    # Calculate groups and their counts
    groups = defaultdict(int)
    for file_data in all_files:
        group_name = file_data.get('group', 'Uncategorized')
        groups[group_name] += 1

    # Get usage stats from database
    usage_stats = db.get_all_time_usage(user['id'])
    usage = {
        'total_characters': usage_stats.get('total_characters', 0),
        'total_cost': usage_stats.get('total_cost', 0.0),
        'files_generated': len(audio_files_db),
        'monthly': {}  # Monthly stats can be added later if needed
    }

    # Get all users for account switcher
    all_users = db.list_users()

    return render_template_string(
        HTML_TEMPLATE,
        error=error,
        success=success,
        filename=filename,
        file_display_name=file_display_name,
        recent_files=recent_files,
        usage=usage,
        groups=dict(groups),
        all_users=all_users
    )

@app.route('/audio/<path:filename>')
@login_required  # Security: Require authentication to access audio files
def audio(filename):
    try:
        safe_filename = secure_filename(filename)

        # Security: Verify file ownership
        if not verify_file_ownership(safe_filename, session['username']):
            return "Unauthorized access", 403

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='audio/mpeg')
        return "File not found", 404
    except Exception as e:
        print(f"Error serving audio: {e}")
        return "Error serving file", 500

@app.route('/download/<path:filename>')
@login_required  # Security: Require authentication to download files
def download(filename):
    try:
        safe_filename = secure_filename(filename)
        username = session.get('username', 'anonymous')

        # Security: Verify file ownership
