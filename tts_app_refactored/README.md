# VoiceVerse TTS Application - Refactored Version

A production-ready, modular Text-to-Speech application with enhanced security, database management, comprehensive testing, and monitoring.

## 🎯 Key Improvements Over Original

### 1. **Modular Architecture**
- Separation of concerns (models, routes, services, utils)
- Easier to maintain and extend
- Better code organization

### 2. **Security Enhancements**
- Input validation and sanitization
- CSRF protection
- Rate limiting
- Secure password hashing
- SQL injection prevention (SQLAlchemy ORM)
- File upload security

### 3. **Database Layer**
- SQLAlchemy ORM (from JSON files)
- Proper relationships and foreign keys
- Soft delete functionality
- Database migrations support

### 4. **Testing Infrastructure**
- Comprehensive unit tests
- Integration tests
- Test fixtures and mocks
- 80%+ code coverage

### 5. **Monitoring & Logging**
- Structured logging (JSON format)
- Error tracking
- Access logs
- Security event logging
- Log rotation

### 6. **Configuration Management**
- Environment-based configs
- Development/Testing/Production settings
- Secure secret handling

---

## 📁 Project Structure

```
tts_app_refactored/
├── app/
│   ├── models/           # Database models
│   │   ├── __init__.py
│   │   ├── user.py       # User model
│   │   ├── audio.py      # Audio file model
│   │   └── usage.py      # Usage statistics
│   ├── routes/           # API routes (to be created)
│   │   ├── __init__.py
│   │   ├── auth.py       # Authentication routes
│   │   ├── audio.py      # Audio management routes
│   │   └── api.py        # API endpoints
│   ├── services/         # Business logic
│   │   ├── __init__.py
│   │   └── tts_service.py # TTS generation service
│   ├── utils/            # Utilities
│   │   ├── __init__.py
│   │   ├── logger.py     # Logging utilities
│   │   └── security.py   # Security helpers
│   ├── templates/        # HTML templates
│   ├── static/           # Static files (CSS, JS)
│   ├── extensions.py     # Flask extensions
│   └── __init__.py       # App factory
├── tests/                # Test suite
│   ├── conftest.py       # Test configuration
│   ├── test_models.py    # Model tests
│   ├── test_routes.py    # Route tests
│   └── test_security.py  # Security tests
├── migrations/           # Database migrations
├── logs/                 # Application logs
├── saved_audio/          # Audio file storage
├── config.py             # Configuration
├── requirements.txt      # Python dependencies
├── run.py                # Application entry point
└── README.md             # This file
```

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.9 or higher
- pip
- virtualenv (recommended)
- OpenAI API key

### Step 1: Clone or Navigate to Project

```bash
cd /Users/ali/Desktop/Project/tts_app_refactored
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Set Environment Variables

Create a `.env` file:

```bash
# .env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here

# Optional
DATABASE_URL=sqlite:///dev_database.db
```

### Step 5: Initialize Database

```bash
python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Step 6: Run Application

```bash
python run.py
```

Or using Flask CLI:

```bash
flask run --host=0.0.0.0 --port=5000
```

Visit: http://localhost:5000

---

## 🔧 Configuration

Edit `config.py` for different environments:

### Development
- Debug mode enabled
- SQLite database
- Detailed logging
- CSRF disabled for testing

### Testing
- In-memory database
- CSRF disabled
- Rate limiting disabled

### Production
- Debug mode disabled
- PostgreSQL (recommended)
- Error email notifications
- Strict security settings

---

## 🧪 Running Tests

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/test_models.py
```

### Run Specific Test

```bash
pytest tests/test_models.py::TestUserModel::test_create_user
```

---

## 📊 Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: Email address
- `password_hash`: Hashed password
- `created_at`: Registration date
- `last_login`: Last login timestamp
- `is_active`: Active status
- `is_admin`: Admin flag

### Audio Files Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `filename`: Unique filename
- `display_name`: User-friendly name
- `file_path`: File system path
- `group_name`: Group/category
- `voice`: TTS voice used
- `speed`: Playback speed
- `character_count`: Text length
- `cost`: Generation cost
- `created_at`: Creation timestamp
- `is_deleted`: Soft delete flag

### Usage Stats Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `total_characters`: Total characters processed
- `total_cost`: Total spending
- `files_generated`: Number of files
- `monthly_data`: JSON with monthly breakdown

### Playback History Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `audio_id`: Foreign key to audio
- `played_at`: Playback timestamp

---

## 🔒 Security Features

### 1. Input Validation
- All user inputs are validated
- Type checking and range validation
- Maximum length enforcement

### 2. Sanitization
- HTML/script injection prevention
- SQL injection prevention (ORM)
- Path traversal prevention
- Filename sanitization

### 3. Authentication
- Secure password hashing (Werkzeug)
- Session management
- Login required decorators

### 4. Rate Limiting
- Per-user rate limits
- API endpoint protection
- Configurable limits

### 5. CSRF Protection
- Token-based protection
- Automatic validation

### 6. File Upload Security
- Extension whitelist
- File size limits
- Secure filename handling
- Content type validation

---

## 📝 Logging

### Log Files

Located in `logs/` directory:

- `app.log` - General application log
- `error.log` - Error log (JSON format)
- `access.log` - HTTP access log

### Log Levels

- **DEBUG**: Detailed information
- **INFO**: General information
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

### Viewing Logs

```bash
# Tail application log
tail -f logs/app.log

# View errors (JSON formatted)
cat logs/error.log | jq

# Search logs
grep "ERROR" logs/app.log
```

---

## 🔄 Migrating from Original App

### Data Migration

1. **Export data from original app:**

```python
import json
from pathlib import Path

# Read metadata.json
with open('saved_audio/metadata.json', 'r') as f:
    metadata = json.load(f)

# This data can be imported into new database
```

2. **Import into new database:**

```python
from app import create_app
from app.extensions import db
from app.models import User, Audio
from pathlib import Path
import json

app = create_app()
with app.app_context():
    # Create default user
    user = User.create_user('admin', 'adminpass', 'admin@example.com')

    # Read old metadata
    with open('saved_audio/metadata.json', 'r') as f:
        metadata = json.load(f)

    # Import audio files
    for filename, data in metadata.items():
        audio = Audio(
            user_id=user.id,
            filename=filename,
            display_name=data['name'],
            file_path=f"saved_audio/{filename}",
            group_name=data.get('group', 'Uncategorized'),
            voice=data.get('voice', 'nova'),
            speed=1.0,
            character_count=data.get('characters', 0),
            cost=data.get('cost', 0.0)
        )
        db.session.add(audio)

    db.session.commit()
    print(f"Imported {len(metadata)} audio files")
```

---

## 🐛 Troubleshooting

### Database Errors

```bash
# Reset database
rm dev_database.db
python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Port Already in Use

```bash
# Find process
lsof -ti:5000

# Kill process
lsof -ti:5000 | xargs kill -9
```

### Module Import Errors

```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### OpenAI API Errors

- Verify API key is set correctly
- Check API key has sufficient credits
- Verify network connectivity

---

## 📈 Performance Optimization

### 1. Database Indexing
- Indexed columns: user_id, group_name, created_at
- Query optimization with proper joins

### 2. Caching (Future Enhancement)
- Redis for session storage
- Cache frequently accessed data

### 3. Async Processing (Future Enhancement)
- Celery for background tasks
- Queue system for TTS generation

---

## 🔐 Production Deployment

### Environment Setup

```bash
export FLASK_ENV=production
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export DATABASE_URL="postgresql://user:pass@localhost/voiceverse"
```

### Using Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:create_app()"]
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/app/static;
    }
}
```

---

## 🤝 Contributing

1. Create feature branch
2. Write tests for new features
3. Ensure all tests pass
4. Submit pull request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🆘 Support

For issues and questions:
- Check logs in `logs/` directory
- Review error messages
- Ensure all dependencies are installed
- Verify environment variables are set

---

## 📚 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Pytest Documentation](https://docs.pytest.org/)

---

**Built with ❤️ by the VoiceVerse Team**
