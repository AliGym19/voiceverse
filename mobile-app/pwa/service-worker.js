/**
 * VoiceVerse Service Worker
 * Handles offline caching, background sync, and push notifications
 */

const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `voiceverse-${CACHE_VERSION}`;

// Assets to cache immediately on install
const STATIC_ASSETS = [
  '/',
  '/static/css/style.css',
  '/static/css/mobile-styles.css',
  '/static/js/main.js',
  '/static/js/install-prompt.js',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  '/manifest.json'
];

// API routes that should be cached
const API_CACHE_ROUTES = [
  '/api/voices',
  '/api/audio/list'
];

// Dynamic content cache
const DYNAMIC_CACHE = `voiceverse-dynamic-${CACHE_VERSION}`;

// Audio file cache (large files)
const AUDIO_CACHE = `voiceverse-audio-${CACHE_VERSION}`;

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name.startsWith('voiceverse-') && name !== CACHE_NAME && name !== DYNAMIC_CACHE && name !== AUDIO_CACHE)
            .map((name) => {
              console.log('[Service Worker] Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests and chrome-extension requests
  if (request.method !== 'GET' || url.protocol === 'chrome-extension:') {
    return;
  }

  // Handle different types of requests with appropriate strategies
  if (isStaticAsset(url)) {
    event.respondWith(cacheFirst(request, CACHE_NAME));
  } else if (isAudioFile(url)) {
    event.respondWith(cacheFirst(request, AUDIO_CACHE));
  } else if (isAPIRequest(url)) {
    event.respondWith(networkFirst(request, DYNAMIC_CACHE));
  } else {
    event.respondWith(staleWhileRevalidate(request, DYNAMIC_CACHE));
  }
});

// Cache strategies

/**
 * Cache First - Try cache, fallback to network
 * Good for: Static assets, audio files
 */
async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  if (cached) {
    return cached;
  }

  try {
    const response = await fetch(request);

    if (response.ok) {
      cache.put(request, response.clone());
    }

    return response;
  } catch (error) {
    console.error('[Service Worker] Fetch failed:', error);
    return new Response('Offline - Resource not available', {
      status: 503,
      statusText: 'Service Unavailable'
    });
  }
}

/**
 * Network First - Try network, fallback to cache
 * Good for: API requests, dynamic content
 */
async function networkFirst(request, cacheName) {
  const cache = await caches.open(cacheName);

  try {
    const response = await fetch(request);

    if (response.ok) {
      cache.put(request, response.clone());
    }

    return response;
  } catch (error) {
    console.log('[Service Worker] Network failed, trying cache');
    const cached = await cache.match(request);

    if (cached) {
      return cached;
    }

    return new Response(JSON.stringify({
      error: 'offline',
      message: 'Network unavailable and no cached data'
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

/**
 * Stale While Revalidate - Return cache immediately, update in background
 * Good for: Frequently changing content that's okay to be slightly stale
 */
async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  const fetchPromise = fetch(request).then((response) => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  });

  return cached || fetchPromise;
}

// Helper functions

function isStaticAsset(url) {
  return url.pathname.startsWith('/static/') ||
         url.pathname === '/manifest.json';
}

function isAudioFile(url) {
  return url.pathname.startsWith('/saved_audio/') ||
         url.pathname.endsWith('.mp3') ||
         url.pathname.endsWith('.wav');
}

function isAPIRequest(url) {
  return url.pathname.startsWith('/api/');
}

// Background Sync - Queue TTS requests when offline
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background sync:', event.tag);

  if (event.tag === 'sync-tts-queue') {
    event.waitUntil(syncTTSQueue());
  }
});

async function syncTTSQueue() {
  console.log('[Service Worker] Syncing TTS queue');

  try {
    // Get queued TTS requests from IndexedDB
    const queue = await getTTSQueue();

    for (const item of queue) {
      try {
        const response = await fetch('/api/tts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(item.data)
        });

        if (response.ok) {
          await removeFromQueue(item.id);

          // Notify user of success
          self.registration.showNotification('TTS Generated', {
            body: `"${item.data.text.substring(0, 50)}..." is ready`,
            icon: '/static/icons/icon-192x192.png',
            badge: '/static/icons/badge-72x72.png',
            tag: 'tts-complete',
            requireInteraction: false
          });
        }
      } catch (error) {
        console.error('[Service Worker] Failed to sync TTS request:', error);
      }
    }
  } catch (error) {
    console.error('[Service Worker] Background sync failed:', error);
  }
}

// Push notifications
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push notification received');

  const data = event.data ? event.data.json() : {};
  const title = data.title || 'VoiceVerse';
  const options = {
    body: data.body || 'New notification',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: data.url || '/',
    actions: [
      {
        action: 'open',
        title: 'Open'
      },
      {
        action: 'close',
        title: 'Dismiss'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'open' || !event.action) {
    const urlToOpen = event.notification.data || '/';

    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then((clientList) => {
          // Check if there's already a window open
          for (const client of clientList) {
            if (client.url === urlToOpen && 'focus' in client) {
              return client.focus();
            }
          }

          // Open new window
          if (clients.openWindow) {
            return clients.openWindow(urlToOpen);
          }
        })
    );
  }
});

// Message handler for communication with main thread
self.addEventListener('message', (event) => {
  console.log('[Service Worker] Message received:', event.data);

  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data.type === 'CACHE_AUDIO') {
    cacheAudioFile(event.data.url);
  }

  if (event.data.type === 'CLEAR_CACHE') {
    clearAllCaches();
  }
});

async function cacheAudioFile(url) {
  const cache = await caches.open(AUDIO_CACHE);
  try {
    const response = await fetch(url);
    await cache.put(url, response);
    console.log('[Service Worker] Audio file cached:', url);
  } catch (error) {
    console.error('[Service Worker] Failed to cache audio:', error);
  }
}

async function clearAllCaches() {
  const cacheNames = await caches.keys();
  await Promise.all(
    cacheNames
      .filter(name => name.startsWith('voiceverse-'))
      .map(name => caches.delete(name))
  );
  console.log('[Service Worker] All caches cleared');
}

// Helper functions for IndexedDB queue management
async function getTTSQueue() {
  // TODO: Implement IndexedDB queue retrieval
  return [];
}

async function removeFromQueue(id) {
  // TODO: Implement IndexedDB queue item removal
  return true;
}
