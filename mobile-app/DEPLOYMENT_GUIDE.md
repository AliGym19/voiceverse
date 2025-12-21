# VoiceVerse Mobile Deployment Guide

Complete guide for deploying the PWA (Progressive Web App) and React Native mobile applications.

---

## Table of Contents

1. [Phase 1: PWA Deployment (1-2 weeks)](#phase-1-pwa-deployment)
2. [Phase 2: React Native Deployment (4-8 weeks)](#phase-2-react-native-deployment)
3. [Testing Checklist](#testing-checklist)
4. [Troubleshooting](#troubleshooting)

---

## Phase 1: PWA Deployment

### Step 1: Install Dependencies

```bash
cd /Users/ali/Desktop/Project/TTS_App
pip3 install flask-cors Pillow
```

### Step 2: Generate PWA Icons

```bash
cd mobile-app/pwa
python3 icon-generator.py

# Or with your own icon:
python3 icon-generator.py path/to/your-icon.png
```

This will generate:
- 12 icon sizes (16x16 to 512x512)
- 10 iOS splash screens
- Favicon files

### Step 3: Copy PWA Files

```bash
# Copy manifest and service worker (they'll be served via routes)
# Copy static assets
cp mobile-app/pwa/mobile-styles.css static/css/
cp mobile-app/pwa/install-prompt.js static/js/
```

### Step 4: Update tts_app19.py

Add this code to your `tts_app19.py`:

```python
# At the top, add imports
from flask_cors import CORS

# After creating Flask app, add PWA setup
from mobile_app.backend_modifications.flask_pwa_setup import setup_pwa

# Enable PWA support
app = setup_pwa(app)
```

### Step 5: Update Your HTML Template

Add to the `<head>` section of your base template:

```html
<!-- PWA Meta Tags -->
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#1DB954">

<!-- Manifest -->
<link rel="manifest" href="/manifest.json">

<!-- Icons -->
<link rel="apple-touch-icon" sizes="180x180" href="/static/icons/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="/static/icons/favicon-32x32.png">

<!-- Styles -->
<link rel="stylesheet" href="/static/css/mobile-styles.css">
```

Add before closing `</body>`:

```html
<!-- PWA Scripts -->
<script src="/static/js/install-prompt.js" defer></script>
```

### Step 6: Enable HTTPS (Required for PWA)

#### For Local Testing:

```bash
# Generate self-signed certificate
cd scripts
./generate_dev_cert.sh

# Or manually:
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.pem -days 365
```

Update `tts_app19.py`:

```python
if __name__ == '__main__':
    if os.path.exists('cert.pem') and os.path.exists('key.pem'):
        app.run(
            host='0.0.0.0',
            port=5000,
            ssl_context=('cert.pem', 'key.pem')
        )
    else:
        app.run(host='0.0.0.0', port=5000)
```

#### For Production:

Use Let's Encrypt:

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com
```

Or use Cloudflare for free SSL.

### Step 7: Test PWA Locally

```bash
# Start your Flask app with HTTPS
python3 tts_app19.py

# Test on mobile:
# 1. Find your computer's IP: ifconfig (Mac/Linux) or ipconfig (Windows)
# 2. On your phone, visit: https://YOUR_IP:5000
# 3. Accept the security warning (self-signed cert)
# 4. Test "Add to Home Screen"
```

### Step 8: Deploy to Production

#### Option A: Simple VPS Deployment

```bash
# On your server:
git clone your-repo
cd TTS_App
pip3 install -r requirements.txt

# Use gunicorn for production
pip3 install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 tts_app19:app \
  --certfile=cert.pem --keyfile=key.pem
```

#### Option B: Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "tts_app19:app"]
```

Deploy:

```bash
docker build -t voiceverse .
docker run -p 5000:5000 -e OPENAI_API_KEY=$OPENAI_API_KEY voiceverse
```

#### Option C: Heroku Deployment

```bash
# Install Heroku CLI
heroku login

# Create app
heroku create voiceverse-tts

# Set environment variables
heroku config:set OPENAI_API_KEY=your-key
heroku config:set SECRET_KEY=your-secret

# Deploy
git push heroku main
```

### Step 9: Configure PWA Manifest

Edit `mobile-app/pwa/manifest.json`:

```json
{
  "start_url": "https://yourdomain.com/",
  "scope": "https://yourdomain.com/"
}
```

### Step 10: Verify PWA Quality

Use Lighthouse in Chrome DevTools:

```bash
# Open Chrome DevTools
# Go to Lighthouse tab
# Run audit
# Score should be >90 for PWA
```

---

## Phase 2: React Native Deployment

### Step 1: Install Expo CLI

```bash
npm install -g expo-cli
```

### Step 2: Create New Expo Project

```bash
cd mobile-app/react-native

# Initialize expo project (if not done)
expo init .

# Choose "blank" template when prompted
```

### Step 3: Copy Project Files

The files are already created in `mobile-app/react-native/`:
- `package.json` - Dependencies
- `App.js` - Main app entry
- `services/api.js` - API layer
- `screens/*.js` - App screens
- `components/*.js` - Reusable components

### Step 4: Install Dependencies

```bash
cd mobile-app/react-native
npm install

# Or with yarn:
yarn install
```

### Step 5: Configure API Base URL

Edit `services/api.js`:

```javascript
const API_CONFIG = {
  baseURL: __DEV__
    ? 'http://YOUR_COMPUTER_IP:5000'  // Change this!
    : 'https://your-production-url.com',
};
```

To find your IP:

```bash
# macOS/Linux:
ifconfig | grep "inet "

# Windows:
ipconfig
```

### Step 6: Start Development Server

```bash
# Start Expo
npm start

# Or
expo start
```

This will open Expo DevTools in your browser.

### Step 7: Test on Physical Device

#### iOS:

1. Install "Expo Go" from App Store
2. Scan QR code from Expo DevTools
3. App will load on your iPhone

#### Android:

1. Install "Expo Go" from Play Store
2. Scan QR code from Expo DevTools
3. App will load on your Android

### Step 8: Create Stub Screens (Temporarily)

Create placeholder files for screens not yet implemented:

```bash
# LibraryScreen.js
touch screens/LibraryScreen.js

# SettingsScreen.js
touch screens/SettingsScreen.js

# LoginScreen.js
touch screens/LoginScreen.js

# RegisterScreen.js
touch screens/RegisterScreen.js

# LoadingScreen.js (in components)
touch components/LoadingScreen.js
```

Add basic placeholder content:

```javascript
// Example: LibraryScreen.js
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function LibraryScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Library Screen - Coming Soon</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#191414',
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    color: '#ffffff',
    fontSize: 18,
  },
});
```

### Step 9: Build Standalone Apps

#### For iOS (requires macOS and Apple Developer Account):

```bash
# Configure app.json
expo build:ios

# Follow prompts to create build
# Download IPA file when ready
# Submit to App Store Connect
```

#### For Android:

```bash
# Generate keystore (first time only)
keytool -genkeypair -v -keystore voiceverse.keystore \
  -alias voiceverse -keyalg RSA -keysize 2048 -validity 10000

# Build APK
expo build:android -t apk

# Or build AAB for Play Store
expo build:android -t app-bundle

# Download and install APK on device
```

### Step 10: Submit to App Stores

#### iOS App Store:

1. Create App ID in Apple Developer Portal
2. Upload app via App Store Connect
3. Fill in app metadata
4. Submit for review (7-14 days)

#### Google Play Store:

1. Create app in Play Console
2. Upload AAB file
3. Fill in app metadata
4. Submit for review (1-3 days)

---

## Testing Checklist

### PWA Testing

- [ ] Install on iOS (Safari)
- [ ] Install on Android (Chrome)
- [ ] Test offline functionality
- [ ] Test "Add to Home Screen" prompt
- [ ] Test service worker caching
- [ ] Test background sync
- [ ] Test push notifications (if implemented)
- [ ] Lighthouse score >90
- [ ] Works on iPhone SE (smallest screen)
- [ ] Works on iPad
- [ ] HTTPS enabled

### React Native Testing

- [ ] Test on iPhone (physical device)
- [ ] Test on Android (physical device)
- [ ] Test authentication flow
- [ ] Test TTS generation
- [ ] Test audio playback
- [ ] Test file upload (PDF/DOCX)
- [ ] Test AI preprocessing
- [ ] Test voice selection
- [ ] Test speed control
- [ ] Test offline mode
- [ ] Test background audio playback
- [ ] Test sharing functionality

### Backend Testing

- [ ] CORS enabled for mobile origin
- [ ] API endpoints return correct data
- [ ] Authentication tokens work
- [ ] File uploads work
- [ ] Rate limiting works
- [ ] Error handling works
- [ ] Logs working properly

---

## Troubleshooting

### PWA Issues

**Problem: "Add to Home Screen" not appearing**

Solution:
- Ensure HTTPS is enabled
- Check manifest.json is accessible at /manifest.json
- Verify service worker is registered
- Test in Incognito mode
- Check Chrome DevTools > Application > Manifest

**Problem: Service Worker not updating**

Solution:
```javascript
// In install-prompt.js, force update:
navigator.serviceWorker.getRegistration().then(reg => {
  reg.update();
});
```

**Problem: Icons not showing**

Solution:
- Verify icon paths in manifest.json
- Check icons exist in /static/icons/
- Clear browser cache
- Test icon URLs directly

### React Native Issues

**Problem: Cannot connect to Flask backend**

Solution:
1. Use computer's IP, not localhost
2. Ensure Flask is running on 0.0.0.0, not 127.0.0.1
3. Check firewall allows port 5000
4. Test API URL in browser first

```python
# In tts_app19.py:
app.run(host='0.0.0.0', port=5000)  # Not localhost!
```

**Problem: Expo build fails**

Solution:
```bash
# Clear cache
expo start -c

# Update Expo
npm install -g expo-cli@latest

# Check for errors
expo doctor
```

**Problem: Audio playback fails**

Solution:
- Check audio URL is accessible
- Verify CORS headers allow mobile origin
- Test audio URL in browser
- Check expo-av permissions

### API Issues

**Problem: CORS errors**

Solution:
```python
# In tts_app19.py:
CORS(app, origins=['*'], supports_credentials=True)
```

**Problem: 401 Unauthorized**

Solution:
- Check auth token is being sent
- Verify token hasn't expired
- Check AsyncStorage has token:

```javascript
AsyncStorage.getItem('authToken').then(console.log);
```

---

## Performance Optimization

### PWA

1. **Enable Compression**:
```python
from flask_compress import Compress
Compress(app)
```

2. **Cache Static Assets**:
```python
@app.after_request
def add_cache_header(response):
    if '/static/' in request.path:
        response.cache_control.max_age = 31536000  # 1 year
    return response
```

3. **Minify Assets**:
```bash
# Install minifiers
npm install -g uglify-js clean-css-cli

# Minify JS
uglifyjs static/js/install-prompt.js -o static/js/install-prompt.min.js

# Minify CSS
cleancss -o static/css/mobile-styles.min.css static/css/mobile-styles.css
```

### React Native

1. **Optimize Images**:
```bash
# Use optimized image formats
npm install react-native-fast-image
```

2. **Enable Hermes**:
```json
// In app.json:
{
  "expo": {
    "jsEngine": "hermes"
  }
}
```

3. **Code Splitting**:
```javascript
// Lazy load screens
const TTSScreen = React.lazy(() => import('./screens/TTSScreen'));
```

---

## Security Checklist

- [ ] HTTPS enabled in production
- [ ] API keys in environment variables
- [ ] CORS restricted to your domains
- [ ] Rate limiting enabled
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitize inputs)
- [ ] CSRF protection enabled
- [ ] Session tokens expire
- [ ] Passwords hashed with bcrypt
- [ ] File upload validation
- [ ] Error messages don't leak sensitive info

---

## Monitoring & Analytics

### Add Analytics

```javascript
// In React Native app
import * as Analytics from 'expo-firebase-analytics';

// Track events
Analytics.logEvent('tts_generated', {
  voice: 'alloy',
  text_length: 100
});
```

### Monitor Backend

```python
# Add request logging
@app.before_request
def log_request():
    app.logger.info(f'{request.method} {request.path}')
```

### Error Tracking

```bash
# Install Sentry
pip install sentry-sdk[flask]
npm install @sentry/react-native
```

---

## Next Steps

### After PWA Launch

1. Gather user feedback
2. Monitor analytics
3. Fix bugs
4. Add requested features
5. Start React Native development

### After React Native Launch

1. Submit to app stores
2. Monitor reviews
3. Update regularly
4. Add premium features
5. Scale backend as needed

---

## Support

For issues:
1. Check this guide
2. Review Flask/React Native docs
3. Check GitHub issues
4. Test API endpoints directly

Good luck with your deployment! 🚀
