// Atlas Copco Intervention Report — Service Worker
// Strategy: cache-first for app shell (so the app works fully offline once installed),
// network-first with cache fallback for everything else.

const CACHE_VERSION = 'ac-intervention-v12';
const APP_SHELL = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png',
  './icons/favicon-32.png'
];

self.addEventListener('install', (event) => {
  // Pre-cache the app shell so the first offline launch works
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => {
      // addAll is atomic — if any URL fails, the whole install fails
      // Use individual put() so a single 404 doesn't break everything
      return Promise.all(
        APP_SHELL.map((url) =>
          cache.add(new Request(url, { cache: 'reload' })).catch((err) => {
            console.warn('SW: failed to pre-cache', url, err);
          })
        )
      );
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  // Take over any open clients immediately and prune old caches
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  // Only handle GET requests; let everything else (POST, etc.) pass through
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Cache-first for same-origin (the app shell — HTML, JS, CSS, icons)
  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(req).then((cached) => {
        if (cached) return cached;
        return fetch(req).then((response) => {
          // Only cache successful, basic responses
          if (response && response.status === 200 && response.type === 'basic') {
            const clone = response.clone();
            caches.open(CACHE_VERSION).then((cache) => cache.put(req, clone));
          }
          return response;
        }).catch(() => {
          // Offline + not in cache — fall back to index.html for navigation
          if (req.mode === 'navigate') {
            return caches.match('./index.html');
          }
        });
      })
    );
    return;
  }

  // Network-first for cross-origin (e.g. CDN fonts) with cache fallback
  event.respondWith(
    fetch(req).then((response) => {
      if (response && response.status === 200) {
        const clone = response.clone();
        caches.open(CACHE_VERSION).then((cache) => cache.put(req, clone));
      }
      return response;
    }).catch(() => caches.match(req))
  );
});