# Deploying VoiceVerse TTS to Render

This guide walks you through deploying your TTS application to Render's free tier.

## Prerequisites

- GitHub account
- Render account (free - sign up at render.com)
- Your TTS_App code pushed to a GitHub repository

## Step 1: Push Your Code to GitHub

If you haven't already:

```bash
cd ~/Desktop/Project/TTS_App

# Initialize git if not already done
git init

# Add files
git add .
git commit -m "Prepare for Render deployment"

# Create GitHub repo and push
# (Follow GitHub's instructions for pushing to a new repo)
git remote add origin YOUR_GITHUB_REPO_URL
git branch -M main
git push -u origin main
```

## Step 2: Create Render Account

1. Go to https://render.com
2. Sign up with GitHub (easiest option)
3. Authorize Render to access your repositories

## Step 3: Create New Web Service

1. **From Render Dashboard:**
   - Click "New +" button
   - Select "Web Service"

2. **Connect Repository:**
   - Choose your TTS_App repository
   - Click "Connect"

3. **Configure Service:**
   - **Name:** voiceverse-tts (or your preferred name)
   - **Region:** Frankfurt (EU - closest to London)
   - **Branch:** main
   - **Runtime:** Python 3
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 tts_app19:app`
   - **Instance Type:** Free

## Step 4: Configure Environment Variables

In the Render dashboard, add these environment variables:

### Required Variables

| Variable | Value | Notes |
|----------|-------|-------|
| `PYTHON_VERSION` | `3.11.0` | Python version |
| `SECRET_KEY` | Generate with button → | Click "Generate" |
| `OPENAI_API_KEY` | `your-openai-key` | From platform.openai.com |
| `DEBUG` | `false` | Production mode |
| `HOST` | `0.0.0.0` | Listen on all interfaces |
| `USE_HTTPS` | `true` | Render provides HTTPS |
| `SECURE_COOKIES` | `true` | Required for HTTPS |
| `SESSION_COOKIE_HTTPONLY` | `true` | Security |
| `SESSION_COOKIE_SAMESITE` | `Lax` | CSRF protection |

### Optional Variables

| Variable | Value | Notes |
|----------|-------|-------|
| `SESSION_LIFETIME` | `3600` | 1 hour (default) |
| `IP_HASH_SALT` | Generate random | For security logs |

## Step 5: Add Persistent Disk (Important!)

**This is crucial for SQLite database persistence!**

1. In your service settings, go to "Disks"
2. Click "Add Disk"
3. Configure:
   - **Name:** voiceverse-data
   - **Mount Path:** `/opt/render/project/src/data`
   - **Size:** 1 GB (free tier limit)
4. Click "Create Disk"

5. **Update database location in code** (see below)

### Update Database Path for Persistent Storage

Create a file `config.py` in your TTS_App directory:

```python
import os

# Use Render's persistent disk for production, local file for development
if os.getenv('RENDER'):
    # Production - use persistent disk
    DATABASE_PATH = '/opt/render/project/src/data/voiceverse.db'
    SAVED_AUDIO_PATH = '/opt/render/project/src/data/saved_audio'
    VOICE_SAMPLES_PATH = '/opt/render/project/src/data/voice_samples'
    LOGS_PATH = '/opt/render/project/src/data/logs'
else:
    # Development - use local directories
    DATABASE_PATH = 'voiceverse.db'
    SAVED_AUDIO_PATH = 'saved_audio'
    VOICE_SAMPLES_PATH = 'voice_samples'
    LOGS_PATH = 'logs'
```

Then update `tts_app19.py` to use these paths (you'll need to import and use `DATABASE_PATH` instead of hardcoded `voiceverse.db`).

## Step 6: Deploy

1. Click "Create Web Service"
2. Render will:
   - Clone your repository
   - Run `build.sh` to install dependencies
   - Start your app with gunicorn
   - Provide you with a URL like `https://voiceverse-tts.onrender.com`

3. **First deployment takes 5-10 minutes** (installing torch is slow)

## Step 7: Monitor Deployment

Watch the logs in Render dashboard:
- Look for "✅ Build complete!"
- Check for any errors
- Wait for "Gunicorn is running"

## Step 8: Test Your App

1. Open your Render URL: `https://your-app-name.onrender.com`
2. Test:
   - Registration/login
   - TTS generation
   - Audio playback
   - File downloads

## Render Free Tier Limitations

### What You Get:
✅ 750 hours/month free (enough for one always-on service)
✅ Automatic HTTPS
✅ Custom domains
✅ Auto-deploys from GitHub
✅ 1 GB persistent disk
✅ Unlimited bandwidth

### Limitations:
⚠️ **Spins down after 15 minutes of inactivity**
- First request after spin-down takes 30-60 seconds
- Subsequent requests are fast

⚠️ **512 MB RAM**
- Coqui TTS voice cloning may not work (requires ~2GB)
- Consider disabling TTS voice cloning for free tier

⚠️ **Shared CPU**
- Performance varies
- TTS generation might be slightly slower

## Optimizations for Free Tier

### 1. Disable Voice Cloning (Optional)

In `tts_app19.py`, you can disable Coqui TTS to reduce memory usage:

```python
# Comment out this line
# TTS_XTTS = TTS_API
TTS_XTTS = None  # Disable voice cloning on free tier
```

### 2. Keep Service Awake

Use a free uptime monitor like:
- **UptimeRobot** (uptimerobot.com)
- **Cronitor** (cronitor.io)
- **BetterUptime** (betteruptime.com)

Configure to ping your app every 10-14 minutes to prevent spin-down.

### 3. Reduce Workers

Already optimized in `render.yaml` - using 2 workers to stay within RAM limits.

## Environment-Specific Database Setup

Update your `build.sh` to create the data directory:

```bash
# In build.sh
if [ -d "/opt/render/project/src/data" ]; then
    echo "📁 Setting up persistent storage..."
    mkdir -p /opt/render/project/src/data/saved_audio
    mkdir -p /opt/render/project/src/data/voice_samples
    mkdir -p /opt/render/project/src/data/logs
fi
```

## Troubleshooting

### Build Fails

**Error: `torch` installation timeout**
- Solution: Torch is large (~2GB). First build may time out. Click "Retry Deploy"

**Error: Missing environment variable**
- Solution: Check all required env vars are set in Render dashboard

### App Won't Start

**Error: `ModuleNotFoundError`**
- Solution: Ensure all dependencies in `requirements.txt`
- Check build logs for pip errors

**Error: Database not found**
- Solution: Ensure persistent disk is mounted at `/opt/render/project/src/data`
- Check `config.py` is imported correctly

### App is Slow

**Symptom: First request takes 60+ seconds**
- This is normal after spin-down
- Use uptime monitor to prevent spin-down

**Symptom: All requests are slow**
- Check Render logs for errors
- Verify you're using gunicorn (not Flask dev server)
- Consider upgrading to paid tier for better performance

## Updating Your App

After pushing changes to GitHub:

1. **Automatic Deployment** (if enabled):
   - Render detects changes
   - Rebuilds and redeploys automatically

2. **Manual Deployment**:
   - Go to Render dashboard
   - Click "Manual Deploy" → "Deploy latest commit"

## Custom Domain (Optional)

1. In Render dashboard, go to "Settings" → "Custom Domains"
2. Add your domain (e.g., `voiceverse.com`)
3. Update DNS records as instructed
4. Render provides free SSL certificate

## Monitoring & Logs

### View Logs
- Render dashboard → "Logs" tab
- Real-time streaming
- Search and filter

### Metrics
- CPU usage
- Memory usage
- Request counts
- Response times

### Alerts
- Set up email notifications for:
  - Deploy failures
  - Service down
  - High error rates

## Backup Strategy

### Database Backups

Since you have a persistent disk, set up automated backups:

**Option 1: Manual Download**
- Use Render's "Shell" feature
- Download `voiceverse.db` periodically

**Option 2: Automated Backup Script**
- Create a cron job to backup to cloud storage
- Use Render's persistent disk for backups

**Option 3: Git-based Backups**
- Add a backup endpoint
- Trigger it to commit DB to a private repo

## Cost Estimate

### Free Tier (Current)
- **Hosting:** $0/month
- **OpenAI TTS:** Pay-per-use
  - ~$0.015-0.030 per generation
  - Depends on usage

### Paid Tier (If You Upgrade Later)
- **Starter:** $7/month
  - 1 GB RAM (can handle voice cloning)
  - No spin-down
  - Better performance

## Next Steps

1. ✅ Deploy to Render
2. ✅ Test all features
3. ⏩ Set up uptime monitoring
4. ⏩ Configure custom domain (optional)
5. ⏩ Set up database backups
6. ⏩ Monitor usage and costs

## Support

- **Render Docs:** https://render.com/docs
- **Render Community:** https://community.render.com
- **Your TTS App Docs:** See README.md and DEPLOYMENT.md

---

**Deployment Checklist:**

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] Web service created
- [ ] All environment variables set
- [ ] Persistent disk added and mounted
- [ ] Database path updated for production
- [ ] First deployment successful
- [ ] App tested and working
- [ ] Uptime monitor configured (optional)
- [ ] Custom domain added (optional)

**Estimated Time:** 30-45 minutes for first deployment

Good luck! 🚀
