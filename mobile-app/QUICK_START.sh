#!/bin/bash

###############################################################################
# VoiceVerse Mobile - Quick Start Script
# This script sets up PWA support for your Flask TTS app
###############################################################################

set -e  # Exit on error

echo "=================================="
echo "VoiceVerse Mobile Quick Start"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}Project root: $PROJECT_ROOT${NC}"
echo ""

# Step 1: Check Python dependencies
echo -e "${BLUE}Step 1/6: Checking dependencies...${NC}"
if ! python3 -c "import flask_cors" 2>/dev/null; then
    echo -e "${YELLOW}Installing flask-cors...${NC}"
    pip3 install flask-cors
fi

if ! python3 -c "import PIL" 2>/dev/null; then
    echo -e "${YELLOW}Installing Pillow...${NC}"
    pip3 install Pillow
fi

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 2: Create directories
echo -e "${BLUE}Step 2/6: Creating directories...${NC}"
mkdir -p "$PROJECT_ROOT/static/css"
mkdir -p "$PROJECT_ROOT/static/js"
mkdir -p "$PROJECT_ROOT/static/icons"
mkdir -p "$PROJECT_ROOT/static/splash"

echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Step 3: Copy PWA files
echo -e "${BLUE}Step 3/6: Copying PWA files...${NC}"

# Copy CSS
if [ -f "$SCRIPT_DIR/pwa/mobile-styles.css" ]; then
    cp "$SCRIPT_DIR/pwa/mobile-styles.css" "$PROJECT_ROOT/static/css/"
    echo "  ✓ Copied mobile-styles.css"
fi

# Copy JS
if [ -f "$SCRIPT_DIR/pwa/install-prompt.js" ]; then
    cp "$SCRIPT_DIR/pwa/install-prompt.js" "$PROJECT_ROOT/static/js/"
    echo "  ✓ Copied install-prompt.js"
fi

echo -e "${GREEN}✓ PWA files copied${NC}"
echo ""

# Step 4: Generate icons
echo -e "${BLUE}Step 4/6: Generating PWA icons...${NC}"
cd "$SCRIPT_DIR/pwa"

if [ "$1" != "" ] && [ -f "$1" ]; then
    echo "Using provided icon: $1"
    python3 icon-generator.py "$1"
else
    echo "Generating default VoiceVerse icons..."
    python3 icon-generator.py
fi

echo -e "${GREEN}✓ Icons generated${NC}"
echo ""

# Step 5: Check Flask app
echo -e "${BLUE}Step 5/6: Checking Flask app...${NC}"

FLASK_APP="$PROJECT_ROOT/tts_app19.py"

if [ ! -f "$FLASK_APP" ]; then
    echo -e "${YELLOW}Warning: tts_app19.py not found at $FLASK_APP${NC}"
    echo "Please manually add PWA setup to your Flask app."
else
    # Check if PWA setup is already added
    if grep -q "setup_pwa" "$FLASK_APP"; then
        echo -e "${GREEN}✓ PWA setup already in Flask app${NC}"
    else
        echo -e "${YELLOW}⚠ PWA setup not detected in Flask app${NC}"
        echo ""
        echo "To enable PWA, add this to tts_app19.py:"
        echo ""
        echo "from flask_cors import CORS"
        echo "from mobile_app.backend_modifications.flask_pwa_setup import setup_pwa"
        echo ""
        echo "# After creating Flask app:"
        echo "app = setup_pwa(app)"
        echo ""
    fi
fi

echo ""

# Step 6: Create quick reference
echo -e "${BLUE}Step 6/6: Creating quick reference...${NC}"

cat > "$PROJECT_ROOT/PWA_SETUP_REFERENCE.md" << 'EOF'
# PWA Setup Reference

## Files Added

- ✅ `static/css/mobile-styles.css` - Mobile-responsive styles
- ✅ `static/js/install-prompt.js` - PWA install prompt
- ✅ `static/icons/*` - App icons (all sizes)
- ✅ `static/splash/*` - iOS splash screens

## Next Steps

### 1. Update tts_app19.py

Add these imports at the top:

```python
from flask_cors import CORS
from mobile_app.backend_modifications.flask_pwa_setup import setup_pwa
```

After creating your Flask app, add:

```python
app = setup_pwa(app)
```

### 2. Update HTML Template

Add to `<head>` section:

```html
<!-- PWA Meta Tags -->
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#1DB954">

<!-- Manifest -->
<link rel="manifest" href="/manifest.json">

<!-- Icons -->
<link rel="apple-touch-icon" sizes="180x180" href="/static/icons/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="/static/icons/favicon-32x32.png">

<!-- Styles -->
<link rel="stylesheet" href="/static/css/mobile-styles.css">
```

Add before `</body>`:

```html
<script src="/static/js/install-prompt.js" defer></script>
```

### 3. Enable HTTPS

For local testing:

```bash
openssl req -x509 -newkey rsa:4096 -nodes -keyout key.pem -out cert.pem -days 365
```

Update tts_app19.py to use SSL:

```python
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        ssl_context=('cert.pem', 'key.pem')
    )
```

### 4. Test on Mobile

1. Find your IP: `ifconfig | grep "inet "`
2. Start Flask: `python3 tts_app19.py`
3. On mobile, visit: `https://YOUR_IP:5000`
4. Accept security warning
5. Test "Add to Home Screen"

## Documentation

- Full guide: `mobile-app/DEPLOYMENT_GUIDE.md`
- README: `mobile-app/README.md`

## Troubleshooting

**PWA not installing?**
- Ensure HTTPS is enabled
- Check manifest.json at `/manifest.json`
- Verify service worker at `/service-worker.js`

**Icons not showing?**
- Clear browser cache
- Check `/static/icons/` exists
- Test icon URL directly

**For more help, see:** `mobile-app/DEPLOYMENT_GUIDE.md`
EOF

echo -e "${GREEN}✓ Created PWA_SETUP_REFERENCE.md${NC}"
echo ""

# Final summary
echo "=================================="
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "=================================="
echo ""
echo "Files created:"
echo "  • static/css/mobile-styles.css"
echo "  • static/js/install-prompt.js"
echo "  • static/icons/* (12 icon sizes)"
echo "  • static/splash/* (10 splash screens)"
echo "  • PWA_SETUP_REFERENCE.md (quick reference)"
echo ""
echo "Next steps:"
echo "  1. Review PWA_SETUP_REFERENCE.md"
echo "  2. Add PWA setup to tts_app19.py"
echo "  3. Update your HTML template"
echo "  4. Enable HTTPS"
echo "  5. Test on mobile device"
echo ""
echo "Full documentation:"
echo "  • mobile-app/DEPLOYMENT_GUIDE.md"
echo "  • mobile-app/README.md"
echo ""
echo -e "${BLUE}Ready to test?${NC} Run: python3 tts_app19.py"
echo ""
