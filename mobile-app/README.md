# VoiceVerse Mobile Applications

Complete mobile solution for VoiceVerse TTS, including Progressive Web App (PWA) and React Native native apps.

## 📱 Overview

This directory contains everything needed to convert your Flask TTS application into mobile apps:

- **PWA (Progressive Web App)**: Works on any device, installable, offline-capable
- **React Native App**: Native iOS and Android apps for app store distribution

## 🗂️ Directory Structure

```
mobile-app/
├── pwa/                          # Progressive Web App files
│   ├── manifest.json            # PWA configuration
│   ├── service-worker.js        # Offline caching & background sync
│   ├── mobile-styles.css        # Mobile-responsive styles
│   ├── install-prompt.js        # Install prompt handler
│   ├── icon-generator.py        # Generate all required icons
│   └── pwa-template-additions.html  # HTML snippets to add
│
├── react-native/                # React Native mobile app
│   ├── App.js                   # Main app entry point
│   ├── package.json             # Dependencies
│   ├── services/
│   │   └── api.js               # Flask backend integration
│   ├── screens/
│   │   ├── TTSScreen.js         # TTS generation screen
│   │   ├── LibraryScreen.js     # Audio library
│   │   ├── LoginScreen.js       # Authentication
│   │   └── SettingsScreen.js    # App settings
│   ├── components/
│   │   ├── AudioPlayer.js       # Audio playback component
│   │   └── LoadingScreen.js     # Loading state
│   └── navigation/              # Navigation config
│
├── backend-modifications/        # Flask backend changes
│   └── flask-pwa-setup.py       # PWA support for Flask
│
├── DEPLOYMENT_GUIDE.md          # Complete deployment instructions
└── README.md                    # This file
```

## 🚀 Quick Start

### Phase 1: PWA (Get Mobile App in 1-2 weeks)

```bash
# 1. Generate icons
cd pwa
python3 icon-generator.py

# 2. Copy files to Flask app
cp mobile-styles.css ../../static/css/
cp install-prompt.js ../../static/js/

# 3. Update tts_app19.py
# Add PWA setup code (see DEPLOYMENT_GUIDE.md)

# 4. Test on mobile
python3 ../../tts_app19.py
# Visit https://YOUR_IP:5000 on your phone
```

### Phase 2: React Native (Native Apps in 4-8 weeks)

```bash
# 1. Install dependencies
cd react-native
npm install

# 2. Configure API URL in services/api.js

# 3. Start development
npm start

# 4. Test on device with Expo Go app
# Scan QR code to load app
```

## ✨ Features

### PWA Features

- ✅ Install on home screen (iOS & Android)
- ✅ Offline functionality with service worker
- ✅ Background sync for queued TTS requests
- ✅ Push notifications support
- ✅ Fast loading with aggressive caching
- ✅ Responsive design for all screen sizes
- ✅ Share target integration
- ✅ Spotify-inspired dark theme

### React Native Features

- ✅ Native iOS and Android apps
- ✅ All 6 OpenAI voices (alloy, echo, fable, onyx, nova, shimmer)
- ✅ Speed control (0.5x to 2.0x)
- ✅ AI text preprocessing
- ✅ PDF/DOCX file upload
- ✅ Audio library with offline storage
- ✅ Background audio playback
- ✅ Share audio files
- ✅ Camera OCR (extract text from photos)
- ✅ Voice recommendations
- ✅ Authentication with secure token storage

## 📋 Requirements

### PWA Requirements

- Python 3.8+
- Flask 2.3+
- flask-cors
- Pillow (for icon generation)
- HTTPS (required for PWA)

### React Native Requirements

- Node.js 16+
- Expo CLI
- iOS: macOS + Xcode (for building)
- Android: Android Studio (for building)
- Physical device or emulator for testing

## 🔧 Technology Stack

### PWA Stack

- **Frontend**: Vanilla JavaScript (ES6+)
- **Caching**: Service Worker API
- **Storage**: IndexedDB for offline queue
- **Notifications**: Push API
- **Styling**: CSS3 with CSS Variables

### React Native Stack

- **Framework**: React Native 0.73 + Expo
- **Navigation**: React Navigation 6
- **HTTP Client**: Axios
- **Storage**: AsyncStorage
- **Audio**: expo-av
- **File System**: expo-file-system
- **Sharing**: expo-sharing
- **Camera**: expo-camera

## 🎨 Design

Both apps follow the Spotify-inspired dark theme:

- **Primary Color**: #1DB954 (Spotify Green)
- **Background**: #191414 (Dark Black)
- **Surface**: #282828 (Card Background)
- **Text**: #FFFFFF (White)
- **Secondary Text**: #B3B3B3 (Gray)

## 📱 Supported Devices

### PWA

- **iOS**: Safari 11.1+ (iOS 11.3+)
- **Android**: Chrome 67+
- **Desktop**: Chrome, Firefox, Edge, Safari

### React Native

- **iOS**: iOS 13.0+
- **Android**: Android 6.0+ (API 23+)

## 🔐 Security

### PWA Security

- HTTPS required (via Let's Encrypt or self-signed)
- CORS configured for mobile access
- Service worker HTTPS requirement
- Secure session management

### React Native Security

- Secure token storage (expo-secure-store)
- HTTPS API communication
- Token expiration handling
- Biometric authentication support (optional)

## 📊 Performance

### PWA Performance

- **First Load**: < 3s
- **Repeat Load**: < 1s (cached)
- **Lighthouse Score**: > 90
- **Cache Strategy**: Aggressive caching for static assets

### React Native Performance

- **App Start**: < 2s
- **TTS Generation**: Depends on OpenAI API (2-5s typical)
- **Audio Playback**: Instant (native player)
- **Hermes Engine**: Enabled for faster performance

## 💰 Cost Estimates

### Development Costs

| Phase | DIY | Freelance | Time |
|-------|-----|-----------|------|
| PWA | $0 | $500-1,500 | 1-2 weeks |
| React Native | $0 | $5,000-15,000 | 4-8 weeks |
| App Store Fees | $99/year (iOS) + $25 (Android one-time) | Same | - |

### Operating Costs

- **OpenAI TTS**: $0.015-0.030 per 1K characters (same as web app)
- **Hosting**: $5-50/month (VPS or cloud)
- **SSL Certificate**: Free (Let's Encrypt) or $10-50/year
- **Push Notifications**: Free (up to limits)

## 📖 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**: Complete deployment instructions
- **pwa/pwa-template-additions.html**: HTML snippets for PWA
- **backend-modifications/flask-pwa-setup.py**: Flask integration code

## 🧪 Testing

### PWA Testing Tools

```bash
# Lighthouse audit
lighthouse https://yourdomain.com --view

# Test PWA criteria
npx pwa-asset-generator
```

### React Native Testing

```bash
# Unit tests
npm test

# E2E tests (if configured)
npx detox test
```

## 🚢 Deployment Targets

### PWA Deployment

- ✅ Any web hosting (VPS, Heroku, AWS, etc.)
- ✅ Cloudflare Pages
- ✅ Netlify
- ✅ Vercel

### React Native Deployment

- ✅ Apple App Store
- ✅ Google Play Store
- ✅ Expo managed workflow
- ✅ Bare workflow (ejected)

## 🛠️ Development Workflow

### PWA Development

1. Modify PWA files in `pwa/`
2. Test in browser with DevTools
3. Test on physical device
4. Deploy to server

### React Native Development

1. Modify files in `react-native/`
2. Test with Expo Go on device
3. Build standalone app
4. Submit to app stores

## 📈 Roadmap

### Current Features (v1.0)

- ✅ TTS generation
- ✅ 6 voices
- ✅ Speed control
- ✅ AI preprocessing
- ✅ File upload
- ✅ Audio library
- ✅ Offline support (PWA)

### Planned Features (v1.1)

- 🔄 Camera OCR for text extraction
- 🔄 Voice cloning
- 🔄 Batch processing
- 🔄 Playlist creation
- 🔄 Cloud sync
- 🔄 Multi-language support

### Future Features (v2.0)

- 🔮 Real-time streaming
- 🔮 Collaborative features
- 🔮 Advanced audio editing
- 🔮 Custom voice training
- 🔮 Integration with other services

## 🐛 Troubleshooting

### Common Issues

**PWA not installing:**
- Ensure HTTPS is enabled
- Check manifest.json is accessible
- Verify service worker is registered

**React Native can't connect to backend:**
- Use computer's IP, not localhost
- Ensure Flask runs on 0.0.0.0
- Check firewall settings

**Audio playback fails:**
- Verify audio URL is accessible
- Check CORS headers
- Test expo-av permissions

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed solutions.

## 📞 Support

For issues or questions:

1. Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. Review the code comments
3. Test API endpoints directly
4. Check Flask/React Native documentation

## 📄 License

Same license as main VoiceVerse TTS application.

## 🙏 Credits

- **Design Inspiration**: Spotify
- **TTS Provider**: OpenAI
- **Framework**: Flask + React Native
- **Icons**: Generated with icon-generator.py

---

Built with ❤️ for VoiceVerse TTS

**Ready to deploy?** Start with Phase 1 (PWA) and see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for step-by-step instructions!
