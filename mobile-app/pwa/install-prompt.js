/**
 * VoiceVerse PWA Install Prompt
 * Handles "Add to Home Screen" functionality for iOS and Android
 */

class PWAInstaller {
  constructor() {
    this.deferredPrompt = null;
    this.installed = false;
    this.promptElement = null;

    this.init();
  }

  init() {
    // Check if already installed
    if (this.isInstalled()) {
      this.installed = true;
      return;
    }

    // Listen for beforeinstallprompt event (Android, Chrome)
    window.addEventListener('beforeinstallprompt', (e) => {
      // Prevent the default prompt
      e.preventDefault();

      // Store the event for later use
      this.deferredPrompt = e;

      // Show custom install prompt
      this.showInstallPrompt();
    });

    // Listen for app installed event
    window.addEventListener('appinstalled', () => {
      console.log('[PWA] App installed successfully');
      this.installed = true;
      this.hideInstallPrompt();
      this.showToast('App installed successfully!', 'success');
    });

    // For iOS, check if standalone and show iOS-specific instructions
    if (this.isIOS() && !this.isStandalone()) {
      // Show iOS install instructions after a delay
      setTimeout(() => {
        this.showIOSInstructions();
      }, 3000);
    }
  }

  isInstalled() {
    // Check if running in standalone mode
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone ||
           document.referrer.includes('android-app://');
  }

  isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  }

  isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone;
  }

  showInstallPrompt() {
    // Don't show if already dismissed in this session
    if (sessionStorage.getItem('installPromptDismissed')) {
      return;
    }

    // Create prompt element if it doesn't exist
    if (!this.promptElement) {
      this.createPromptElement();
    }

    // Show the prompt with animation
    setTimeout(() => {
      this.promptElement.classList.add('show');
    }, 100);

    // Log analytics event
    this.logEvent('install_prompt_shown');
  }

  hideInstallPrompt() {
    if (this.promptElement) {
      this.promptElement.classList.remove('show');

      setTimeout(() => {
        if (this.promptElement && this.promptElement.parentNode) {
          this.promptElement.parentNode.removeChild(this.promptElement);
          this.promptElement = null;
        }
      }, 300);
    }
  }

  createPromptElement() {
    const prompt = document.createElement('div');
    prompt.className = 'install-prompt';
    prompt.innerHTML = `
      <div class="install-prompt-header">
        <img src="/static/icons/icon-192x192.png" alt="VoiceVerse" class="install-prompt-icon">
        <div>
          <h3 class="install-prompt-title">Install VoiceVerse</h3>
          <p class="install-prompt-text">Get quick access with one tap on your home screen</p>
        </div>
      </div>
      <div class="install-prompt-actions">
        <button class="install-btn" id="installBtn">Install</button>
        <button class="dismiss-btn" id="dismissBtn">Not Now</button>
      </div>
    `;

    // Add event listeners
    const installBtn = prompt.querySelector('#installBtn');
    const dismissBtn = prompt.querySelector('#dismissBtn');

    installBtn.addEventListener('click', () => this.handleInstall());
    dismissBtn.addEventListener('click', () => this.handleDismiss());

    document.body.appendChild(prompt);
    this.promptElement = prompt;
  }

  async handleInstall() {
    if (!this.deferredPrompt) {
      console.warn('[PWA] No install prompt available');
      return;
    }

    // Show the native install prompt
    this.deferredPrompt.prompt();

    // Wait for the user's response
    const { outcome } = await this.deferredPrompt.userChoice;

    console.log(`[PWA] User ${outcome} the install prompt`);
    this.logEvent('install_prompt_result', { outcome });

    if (outcome === 'accepted') {
      this.showToast('Installing app...', 'success');
    }

    // Clear the deferred prompt
    this.deferredPrompt = null;

    // Hide our custom prompt
    this.hideInstallPrompt();
  }

  handleDismiss() {
    sessionStorage.setItem('installPromptDismissed', 'true');
    this.hideInstallPrompt();
    this.logEvent('install_prompt_dismissed');
  }

  showIOSInstructions() {
    // Don't show if already dismissed
    if (localStorage.getItem('iosInstructionsDismissed')) {
      return;
    }

    const modal = document.createElement('div');
    modal.className = 'install-prompt ios-instructions';
    modal.innerHTML = `
      <div class="install-prompt-header">
        <img src="/static/icons/icon-192x192.png" alt="VoiceVerse" class="install-prompt-icon">
        <div>
          <h3 class="install-prompt-title">Install on iOS</h3>
          <p class="install-prompt-text">Add VoiceVerse to your home screen for quick access</p>
        </div>
      </div>
      <div class="ios-instructions-steps">
        <div class="instruction-step">
          <span class="step-number">1</span>
          <span class="step-text">Tap the Share button <span class="ios-share-icon">⎋</span></span>
        </div>
        <div class="instruction-step">
          <span class="step-number">2</span>
          <span class="step-text">Scroll down and tap "Add to Home Screen"</span>
        </div>
        <div class="instruction-step">
          <span class="step-number">3</span>
          <span class="step-text">Tap "Add" to install</span>
        </div>
      </div>
      <div class="install-prompt-actions">
        <button class="dismiss-btn" id="iosInstructionsDismissBtn">Got It</button>
      </div>
    `;

    const dismissBtn = modal.querySelector('#iosInstructionsDismissBtn');
    dismissBtn.addEventListener('click', () => {
      localStorage.setItem('iosInstructionsDismissed', 'true');
      modal.classList.remove('show');
      setTimeout(() => {
        if (modal.parentNode) {
          modal.parentNode.removeChild(modal);
        }
      }, 300);
      this.logEvent('ios_instructions_dismissed');
    });

    document.body.appendChild(modal);

    setTimeout(() => {
      modal.classList.add('show');
    }, 100);

    this.logEvent('ios_instructions_shown');
  }

  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span>${message}</span>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('show');
    }, 100);

    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 300);
    }, 3000);
  }

  logEvent(eventName, data = {}) {
    // Log to console in development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      console.log(`[PWA Event] ${eventName}`, data);
    }

    // Send to analytics in production
    if (typeof gtag !== 'undefined') {
      gtag('event', eventName, {
        event_category: 'PWA',
        ...data
      });
    }

    // Send to your own analytics endpoint
    if (typeof fetch !== 'undefined') {
      fetch('/api/analytics/event', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          event: eventName,
          data: data,
          timestamp: new Date().toISOString()
        })
      }).catch(err => {
        // Silent fail
        console.debug('Analytics error:', err);
      });
    }
  }

  // Public method to manually trigger install prompt
  triggerInstall() {
    if (this.isIOS()) {
      this.showIOSInstructions();
    } else {
      this.showInstallPrompt();
    }
  }

  // Check if updates are available
  async checkForUpdates() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.getRegistration();
        if (registration) {
          await registration.update();
          console.log('[PWA] Checked for updates');
        }
      } catch (error) {
        console.error('[PWA] Update check failed:', error);
      }
    }
  }
}

// Initialize PWA installer when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.pwaInstaller = new PWAInstaller();
  });
} else {
  window.pwaInstaller = new PWAInstaller();
}

// Register service worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    try {
      const registration = await navigator.serviceWorker.register('/service-worker.js', {
        scope: '/'
      });

      console.log('[PWA] Service Worker registered:', registration.scope);

      // Check for updates every hour
      setInterval(() => {
        registration.update();
      }, 60 * 60 * 1000);

      // Handle service worker updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;

        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // New service worker available
            console.log('[PWA] New version available');

            // Show update notification
            if (window.pwaInstaller) {
              window.pwaInstaller.showToast(
                'New version available! Refresh to update.',
                'info'
              );
            }

            // Auto-update after 5 seconds
            setTimeout(() => {
              newWorker.postMessage({ type: 'SKIP_WAITING' });
              window.location.reload();
            }, 5000);
          }
        });
      });

    } catch (error) {
      console.error('[PWA] Service Worker registration failed:', error);
    }
  });

  // Handle service worker controller change (update applied)
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    console.log('[PWA] Service Worker controller changed');
  });
}

// Offline/Online detection
window.addEventListener('online', () => {
  console.log('[PWA] Back online');
  if (window.pwaInstaller) {
    window.pwaInstaller.showToast('Back online!', 'success');
  }

  // Trigger background sync for queued TTS requests
  if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
    navigator.serviceWorker.ready.then((registration) => {
      return registration.sync.register('sync-tts-queue');
    }).catch((err) => {
      console.error('[PWA] Background sync registration failed:', err);
    });
  }
});

window.addEventListener('offline', () => {
  console.log('[PWA] Gone offline');
  if (window.pwaInstaller) {
    window.pwaInstaller.showToast('You are offline. Some features may be limited.', 'warning');
  }
});

// Expose global function for manual install trigger
window.triggerPWAInstall = function() {
  if (window.pwaInstaller) {
    window.pwaInstaller.triggerInstall();
  }
};

// iOS-specific instructions styling
const style = document.createElement('style');
style.textContent = `
  .ios-instructions {
    max-width: 400px;
  }

  .ios-instructions-steps {
    margin: var(--spacing-lg) 0;
  }

  .instruction-step {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    background-color: var(--spotify-darker);
    border-radius: var(--radius-md);
    margin-bottom: var(--spacing-sm);
  }

  .step-number {
    width: 32px;
    height: 32px;
    background-color: var(--primary-color);
    color: var(--spotify-darker);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    flex-shrink: 0;
  }

  .step-text {
    flex: 1;
    font-size: 0.9rem;
  }

  .ios-share-icon {
    display: inline-block;
    font-size: 1.2rem;
    vertical-align: middle;
  }
`;
document.head.appendChild(style);
