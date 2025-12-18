# 🌌 VoiceVerse - AI-Powered Text-to-Speech Application

A beautiful, feature-rich web application for converting text to speech using OpenAI's TTS API. Built with Flask, featuring AI agents for intelligent text processing, and a Spotify-inspired dark interface.

![VoiceVerse](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## ✨ Features

### Core Features
- 🎙️ **6 Premium Voices** - Choose from alloy, echo, fable, onyx, nova, and shimmer
- 📝 **Smart Text Input** - Paste, type, or upload PDF/DOCX files
- 🎵 **Built-in Audio Player** - Spotify-style player with volume control, seek, and playlist
- 📚 **Audio Library** - Organize your audio files by groups/categories
- 🔄 **Playback History** - Recently played tracks
- 🌙 **Dark Mode UI** - Beautiful, modern interface

### AI Agent Features
- 🤖 **Smart Text Preprocessing** - Automatically cleans and optimizes text for TTS
- ✂️ **Intelligent Chunking** - Splits long texts at natural boundaries
- 💡 **AI Suggestions** - Auto-generates filenames, categories, and voice recommendations
- 📊 **Quality Analysis** - Checks text quality and estimates duration/cost
- 🎯 **Voice Recommendations** - AI suggests the best voice for your content

### Advanced Features
- 🔐 **User Authentication** - Secure login system with bcrypt password hashing
- 🔒 **HTTPS/TLS Support** - Encrypted connections with self-signed or Let's Encrypt certificates
- 🛡️ **Security Logging** - Comprehensive audit trails with PII protection
- 💾 **Persistent Storage** - SQLite database with transaction safety
- 📱 **Responsive Design** - Works on desktop and mobile
- ⚡ **Real-time Generation** - Fast audio synthesis
- 🔄 **Auto-save** - Never lose your audio files
- 🌍 **Production Ready** - Full deployment guides with Nginx reverse proxy

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/voiceverse.git
   cd voiceverse
   ```

2. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Configure environment variables**

   Create a `.env` file or set environment variables:

   **Option A: Using .env file (Recommended)**
   ```bash
   # Copy development template
   cp .env.development .env

   # Edit .env with your values
   nano .env
   ```

   Add your API key and generate secrets:
   ```bash
   # Generate SECRET_KEY
   python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env

   # Add your OpenAI API key
   echo "OPENAI_API_KEY=your-api-key-here" >> .env
   ```

   **Option B: Environment Variables**
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   export SECRET_KEY='your-secret-key-here'
   ```

4. **Run the application**
   ```bash
   python3 tts_app19.py
   ```

5. **Open in your browser**
   ```
   http://localhost:5000
   ```

   Or with HTTPS (self-signed certificate):
   ```bash
   # Generate development certificate
   bash scripts/generate_dev_cert.sh

   # Enable HTTPS in .env
   USE_HTTPS=true

   # Access via HTTPS
   https://localhost:5000
   ```

6. **Create an account**
   - Click "Sign Up"
   - Enter username and password
   - Start generating audio!

## 📋 Requirements

Create a `requirements.txt` file with:

```txt
Flask>=2.3.0
openai>=1.0.0
Werkzeug>=2.3.0
PyPDF2>=3.0.0
python-docx>=0.8.11
```

## 🎯 Usage

### Basic Text-to-Speech
1. Enter or paste your text
2. Choose a voice (or let AI suggest one)
3. Set speed (0.25x - 4.0x)
4. Click "Generate Audio"

### Using AI Features
1. **Get AI Suggestions**
   - Click the "Get AI Suggestions" button
   - Review suggested filename, category, and voice
   - Accept or modify suggestions

2. **Smart Text Preprocessing**
   - Enable "Smart Text Preprocessing" toggle
   - AI automatically cleans formatting issues
   - Expands URLs and acronyms
   - Removes PDF artifacts

3. **Smart Chunking** (for long texts)
   - Enable "Smart Chunking" toggle
   - AI splits text at natural boundaries
   - Maintains narrative flow
   - No mid-sentence cuts

4. **Quality Analysis**
   - Click "Analyze Text Quality"
   - See character/word count
   - Estimated duration and cost
   - Quality score and warnings

### File Upload
- Drag and drop PDF or DOCX files
- Text is automatically extracted
- Use AI preprocessing for best results

### Library Management
- Create groups/categories
- Rename, download, or delete files
- Search and filter your library
- Click files to play instantly

## 📁 Project Structure

```
voiceverse/
├── tts_app19.py              # Main Flask application
├── tts_agents.py             # AI agents module
├── database.py               # Database abstraction layer
├── logger.py                 # Security logging module
├── test_agents.py            # Agent tests
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── DEPLOYMENT.md             # Production deployment guide
├── SECURITY.md               # Security documentation
├── IMPLEMENTATION_ROADMAP.md # Development roadmap
├── .env.development          # Development environment template
├── .env.production           # Production environment template
├── .env                      # Active environment config (gitignored)
├── .gitignore               # Git ignore rules
├── nginx.conf.example        # Nginx reverse proxy config
├── scripts/                  # Utility scripts
│   └── generate_dev_cert.sh # SSL certificate generator
├── certs/                    # SSL certificates (gitignored)
│   ├── dev-cert.pem         # Development certificate
│   └── dev-key.pem          # Development private key
├── data/                     # Application data
│   └── voiceverse.db        # SQLite database
├── logs/                     # Application logs
│   └── security_audit.log   # Security events log
└── saved_audio/             # Generated audio storage
```

## 🔧 Configuration

### Environment Variables

Configure via `.env` file:

```bash
# Flask Security
SECRET_KEY=your-secret-key-here
IP_HASH_SALT=your-salt-here

# OpenAI API
OPENAI_API_KEY=your-api-key-here

# Application Settings
DEBUG=true                    # Set to false in production
HOST=127.0.0.1               # Use 0.0.0.0 to allow external access
PORT=5000

# HTTPS/TLS Configuration
USE_HTTPS=false              # Enable for encrypted connections
SSL_CERT_PATH=certs/dev-cert.pem
SSL_KEY_PATH=certs/dev-key.pem

# Session Security
SESSION_LIFETIME=3600        # Session timeout in seconds
SECURE_COOKIES=false         # Set to true when using HTTPS
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
```

### Change Port
Edit `.env`:
```bash
PORT=8080  # Change from 5000 to 8080
```

### Adjust Audio Settings
Default settings in `tts_app19.py`:
```python
# TTS model
model = "tts-1"  # or "tts-1-hd" for higher quality

# Default speed
speed = 1.0  # Range: 0.25 to 4.0

# Default voice
voice = "nova"  # Options: alloy, echo, fable, onyx, nova, shimmer
```

### Production Configuration

For production deployments, see [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive guides on:
- HTTPS/SSL setup with Let's Encrypt
- Nginx reverse proxy configuration
- Systemd service setup
- Security hardening
- Monitoring and backups

## 💰 Cost Information

OpenAI TTS Pricing (as of 2024):
- **TTS-1**: $0.015 per 1,000 characters (~$0.0075 per minute of audio)
- **TTS-1-HD**: $0.030 per 1,000 characters (~$0.015 per minute of audio)

AI Agent costs (GPT-4o-mini):
- Preprocessing: ~$0.001-0.002 per request
- Suggestions: ~$0.0005-0.001 per request
- Analysis: ~$0.0002-0.0005 per request
- Chunking: ~$0.001-0.003 per request

**Total typical cost per generation: $0.015 - $0.025**

## 🎨 Available Voices

| Voice | Description | Best For |
|-------|-------------|----------|
| **alloy** | Neutral, versatile | Tutorials, documentation |
| **echo** | Male, clear | Technical content, professional |
| **fable** | British male | Storytelling, audiobooks |
| **onyx** | Deep male | Authority, news, formal |
| **nova** | Female, warm | Friendly content, guides |
| **shimmer** | Soft female | Meditation, calm narration |

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find and kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use a different port (see Configuration section)
```

### API Key Issues
```bash
# Verify your key is set
echo $OPENAI_API_KEY

# Test API access
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Module Not Found
```bash
# Reinstall dependencies
pip3 install -r requirements.txt --upgrade
```

### Database Locked
```bash
# Stop all running instances
lsof -ti:5000 | xargs kill -9

# Remove lock (only if app is not running)
rm tts_users.db-journal
```

## 🔒 Security Features

VoiceVerse implements enterprise-grade security:

### Authentication & Authorization
- ✅ Bcrypt password hashing (14 rounds)
- ✅ Session-based authentication with secure cookies
- ✅ File ownership verification on all operations
- ✅ Rate limiting on login attempts (5 per 15 minutes)

### Encryption
- ✅ HTTPS/TLS support with Let's Encrypt or self-signed certificates
- ✅ Secure session cookies (HttpOnly, Secure, SameSite)
- ✅ Environment-based configuration management

### Security Logging
- ✅ Comprehensive audit trails for all security events
- ✅ PII protection (hashed IPs, redacted emails)
- ✅ Dual logging (file + database)
- ✅ Automated log rotation

### Protection
- ✅ SQL injection protection (parameterized queries)
- ✅ CSRF protection
- ✅ XSS protection (Content Security Policy)
- ✅ Rate limiting on all sensitive endpoints
- ✅ Input validation and sanitization

**For detailed security information, see [SECURITY.md](SECURITY.md)**

### Security Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `DEBUG=false`
- [ ] Enable `SECURE_COOKIES=true`
- [ ] Configure HTTPS with valid SSL certificate
- [ ] Set up Fail2ban for brute-force protection
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Review security audit logs regularly

**Never commit `.env` files or API keys to version control!**

## 📚 Documentation

### Project Documentation
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete production deployment guide
- **[SECURITY.md](SECURITY.md)** - Security features and best practices
- **[IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)** - Development phases and features
- **[AI_AGENTS_README.md](AI_AGENTS_README.md)** - AI agents documentation
- **[QUICK_START.md](QUICK_START.md)** - Quick start guide

### External Documentation
- [OpenAI TTS API Docs](https://platform.openai.com/docs/guides/text-to-speech)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Let's Encrypt](https://letsencrypt.org/) - Free SSL certificates

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Clone your fork
git clone https://github.com/yourusername/voiceverse.git

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python3 test_agents.py
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for the TTS API
- Flask community
- All contributors and users

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/voiceverse/issues)
- **Documentation**: See `AI_AGENTS_README.md` and `QUICK_START.md`

## 🗺️ Roadmap

- [ ] Voice cloning support
- [ ] Batch processing
- [ ] Cloud storage integration
- [ ] Mobile app
- [ ] SSML support
- [ ] Multi-language support
- [ ] Custom pronunciation dictionary
- [ ] Audio enhancement filters
- [ ] Collaborative features
- [ ] Analytics dashboard

---

**Made with ❤️ using OpenAI TTS**

*Star ⭐ this repo if you find it useful!*
