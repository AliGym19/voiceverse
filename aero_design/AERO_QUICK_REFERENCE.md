# 🪟 Aero UI Quick Reference Guide

## Quick Commands

### Start/Stop App
```bash
# Start the app
python3 tts_app19.py

# With timeout (prevents hanging)
timeout 10 python3 tts_app19.py

# Kill running app
lsof -ti:5000 | xargs kill -9
```

### Access Points
- **Main Page**: http://localhost:5000/ → redirects to dashboard
- **Dashboard**: http://localhost:5000/dashboard
- **Login**: http://localhost:5000/login
- **API**: http://localhost:5000/api/audio-files

### Run Tests
```bash
# Run full test suite
python3 test_aero_ui.py

# Should show: 9/9 tests passed ✅
```

## File Locations

### Templates
- **Aero Dashboard**: `templates/dashboard_aero.html`
- **Auth Page**: `templates/auth.html`
- **Old Spotify Backup**: `old_spotify_design/templates/`

### Styles & Scripts
- **Aero CSS**: `static/css/aero_theme.css` (1,454 lines)
- **Aero JS**: `static/js/aero_player.js` (1,116 lines)

### Main Application
- **Flask App**: `tts_app19.py` (69K+ tokens)
- **Test Suite**: `test_aero_ui.py`

## Key Features

### Navigation Tabs
1. **Generate** 🎙️ - Create TTS audio
2. **Library** 📚 - Manage audio files
3. **AI Agents** 🤖 - Agent dashboard
4. **Settings** ⚙️ - User preferences

### Voice Options (with unique gradients)
1. **Alloy** 🎭 - Pink gradient - Neutral & Versatile
2. **Echo** 🎤 - Purple gradient - Male & Clear
3. **Fable** 📖 - Yellow gradient - British Storyteller
4. **Nova** ✨ - Blue gradient - Warm & Friendly
5. **Onyx** 🎩 - Gray gradient - Deep & Authoritative
6. **Shimmer** 💫 - Magenta gradient - Soft & Calming

### AI Features (Toggle Switches)
- **Smart Preprocessing** - Clean and optimize text
- **Smart Chunking** - Split long text intelligently
- **HD Quality** - Use TTS-1-HD model (2x cost)

### Speed Control
- Range: 0.25x to 4.0x
- Default: 1.0x
- Step: 0.25x increments

## Customization Points

### Change Color Scheme
Edit `static/css/aero_theme.css`:

```css
:root {
    /* Primary green colors */
    --aero-green-vivid: #7fff00;
    --aero-green-bright: #00ff00;
    --aero-green-medium: #33ff33;

    /* Background blues */
    --aero-blue-dark: #0a1929;
    --aero-blue-bright: #56a5eb;
}
```

### Modify Window Title
Edit `templates/dashboard_aero.html` line 31:

```html
<span class="window-title">VoiceVerse - AI Text-to-Speech Studio</span>
```

### Adjust Glass Blur Intensity
Edit `static/css/aero_theme.css`:

```css
.aero-window {
    backdrop-filter: blur(20px);  /* Change 20px to desired value */
}
```

### Animation Speeds
Edit animation durations in `static/css/aero_theme.css`:

```css
.orb-1 {
    animation-duration: 25s;  /* Change speed */
}

@keyframes shimmer {
    /* Adjust timing */
}
```

## Common Tasks

### Add New Voice Gradient
1. Edit `static/css/aero_theme.css`
2. Add new CSS variable in `:root`:
   ```css
   --voice-newvoice-from: #colorA;
   --voice-newvoice-to: #colorB;
   ```
3. Add gradient class:
   ```css
   .newvoice-gradient {
       background: linear-gradient(135deg,
           var(--voice-newvoice-from) 0%,
           var(--voice-newvoice-to) 100%);
   }
   ```
4. Update `templates/dashboard_aero.html` voice options

### Modify Player Bar Style
Edit `static/css/aero_theme.css` section starting ~line 900:

```css
.player-bar {
    height: 90px;
    background: linear-gradient(135deg, ...);
    /* Customize appearance */
}
```

### Change Window Size
Edit `static/css/aero_theme.css` `.aero-window`:

```css
.aero-window {
    max-width: 1400px;    /* Maximum width */
    min-width: 1000px;    /* Minimum width */
    height: 85vh;         /* Height */
    max-height: 800px;    /* Maximum height */
}
```

## Troubleshooting

### Issue: App won't start (port conflict)
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Then restart
python3 tts_app19.py
```

### Issue: CSS not loading
1. Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+F5` (Windows)
2. Check file exists: `ls static/css/aero_theme.css`
3. Check Flask is serving static files correctly

### Issue: Animations not smooth
1. Close other browser tabs
2. Check CPU usage: System is under heavy load
3. Reduce blur intensity in CSS
4. Reduce number of orbs (comment out in HTML)

### Issue: Glass effect not showing
1. Check browser supports backdrop-filter
2. Update browser to latest version
3. Try Chrome/Edge for best compatibility
4. Fallback: Edit CSS to increase background opacity

### Issue: Login redirects not working
1. Check session is enabled in Flask
2. Verify `SECRET_KEY` is set in environment
3. Check database connection
4. Verify user credentials in database

### Issue: Audio generation fails
1. Check `OPENAI_API_KEY` is set
2. Verify API key is valid
3. Check internet connection
4. Review Flask console for error messages

## Performance Tips

### Optimize for Low-End Devices
1. Reduce blur amount (20px → 10px)
2. Reduce number of orbs (4 → 2)
3. Disable some animations
4. Simplify gradients (fewer color stops)

### Optimize for Battery Life
1. Reduce animation durations
2. Use `will-change: transform` sparingly
3. Limit simultaneous animations
4. Reduce shadow complexity

### Speed Up Page Load
1. Minimize CSS/JS (production build)
2. Enable browser caching
3. Compress static assets
4. Use CDN for libraries (if any)

## Keyboard Shortcuts (Browser)

- `Cmd+R` / `Ctrl+R` - Refresh page
- `Cmd+Shift+R` / `Ctrl+F5` - Hard refresh (clear cache)
- `Cmd+Option+I` / `F12` - Open developer tools
- `Cmd+Option+J` / `Ctrl+Shift+J` - Open console

## Testing Checklist

Before deploying changes:

- [ ] Run `python3 test_aero_ui.py` - All 9 tests pass
- [ ] Test login/logout flow
- [ ] Generate a test audio file
- [ ] Verify audio playback works
- [ ] Test file upload (PDF/DOCX/TXT)
- [ ] Check all tabs load correctly
- [ ] Verify responsive on different window sizes
- [ ] Test on multiple browsers
- [ ] Check console for JavaScript errors
- [ ] Verify all animations are smooth

## Useful Links

- **OpenAI TTS Docs**: https://platform.openai.com/docs/guides/text-to-speech
- **CSS Backdrop Filter**: https://developer.mozilla.org/en-US/docs/Web/CSS/backdrop-filter
- **Flask Documentation**: https://flask.palletsprojects.com/
- **Frutiger Aero Design**: https://frutiger-aero.org/

## Support

### Getting Help
1. Check Flask console for errors
2. Check browser console (F12) for JavaScript errors
3. Review test output: `python3 test_aero_ui.py`
4. Check backup files in `old_spotify_design/`
5. Consult `AERO_TRANSFORMATION_SUMMARY.md`

### Reporting Issues
Include this information:
- Error message (if any)
- Browser and version
- Operating system
- Steps to reproduce
- Screenshot (if UI issue)

## Quick Rollback

If something goes wrong:

```bash
# Restore old Spotify theme
cp old_spotify_design/templates/index_spotify_original.html templates/index.html

# Or use the backup
cp templates/index.html.backup templates/index.html

# Then restart app
python3 tts_app19.py
```

## Version Info

- **Aero Version**: 1.0
- **Transformation Date**: November 4, 2025
- **Base App**: VoiceVerse TTS v19
- **Flask Version**: Check with `pip3 show Flask`
- **Python Version**: Check with `python3 --version`

---

**🪟 Windows Vista/7 Aero Theme - Fully Operational! ✨**
