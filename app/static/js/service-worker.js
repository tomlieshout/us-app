// "Us" service worker: caches the app shell for offline/instant loads.
// API responses are NEVER cached - answers are privacy-sensitive and must
// always come fresh from the server (see build brief section 34).

const CACHE_NAME = 'us-app-shell-v1';
const SHELL_ASSETS = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/js/api.js',
  '/static/js/utils.js',
  '/static/js/state.js',
  '/static/js/views/onboarding.js',
  '/static/js/views/home.js',
  '/static/js/views/questions.js',
  '/static/js/views/memories.js',
  '/static/js/views/stats.js',
  '/static/js/views/settings.js',
  '/static/js/views/round.js',
  '/static/manifest.json',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(SHELL_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Never intercept API calls - always hit the network so answer data is
  // never served from a cache, and so privacy state is always current.
  if (url.pathname.startsWith('/api/')) return;
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      const networkFetch = fetch(event.request)
        .then((response) => {
          if (response && response.status === 200 && response.type === 'basic') {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => cached);
      return cached || networkFetch;
    })
  );
});
