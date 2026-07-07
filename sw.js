// Atlas Copco Intervention Report — Service Worker
// Strategy:
//   - HTML/navigation: stale-while-revalidate (instant load + background update)
//   - Static assets (icons, manifest): cache-first (they rarely change)
//   - Cross-origin: network-first with cache fallback
// The HTML stale-while-revalidate strategy means users always see the cached
// page instantly, AND get the latest version on their NEXT visit — without
// needing a manual cache-version bump for every deploy.

const CACHE_VERSION = 'ac-intervention-v15';
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

  // Cross-origin (e.g. CDN fonts) — network-first with cache fallback
  if (url.origin !== self.location.origin) {
    event.respondWith(
      fetch(req).then((response) => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_VERSION).then((cache) => cache.put(req, clone));
        }
        return response;
      }).catch(() => caches.match(req).then((cached) => cached || new Response('', { status: 504, statusText: 'Offline' })))
    );
    return;
  }

  // Same-origin requests:
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(req));
    return;
  }

  const isHTML = req.mode === 'navigate' ||
    (req.headers.get('accept') || '').includes('text/html');

  // HTML/navigation: stale-while-revalidate
  // Serve cached immediately (instant load), fetch fresh in the background.
  // The fresh copy is cached so the NEXT navigation shows the update —
  // no manual cache-version bump needed for every deploy.
  if (isHTML) {
    event.respondWith(
      caches.open(CACHE_VERSION).then((cache) =>
        cache.match(req).then((cached) => {
          // Fetch fresh in the background regardless
          const fetchPromise = fetch(req).then((response) => {
            if (response && response.status === 200) {
              cache.put(req, response.clone());
            }
            return response;
          }).catch(() => cached); // offline — fall back to whatever we have

          // Return cached immediately if available, otherwise wait for network
          return cached || fetchPromise;
        })
      )
    );
    return;
  }

  // Static assets (icons, manifest, CSS, etc.) — cache-first
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req).then((response) => {
        if (response && response.status === 200 && response.type === 'basic') {
          const clone = response.clone();
          caches.open(CACHE_VERSION).then((cache) => cache.put(req, clone));
        }
        return response;
      }).catch(() => {
        // Offline fallback for navigation requests
        if (req.mode === 'navigate') {
          return caches.match('./index.html');
        }
        return new Response('', { status: 504, statusText: 'Offline' });
      });
    })
  );
});
