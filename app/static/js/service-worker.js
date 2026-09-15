// "Us" service worker: caches the app shell for offline/instant loads.
// API responses are NEVER cached - answers are privacy-sensitive and must
// always come fresh from the server (see build brief section 34).
//
// The HTML document itself (`/`) is treated differently from the other
// shell assets: it embeds a CSRF token tied to the current server-side
// session at render time. Serving a stale cached copy of it can leave a
// user stuck with a token that no longer matches their live session -
// surfacing as "your session expired" on every submit, especially on
// mobile where session/cookie state resets more readily than desktop.
// So the HTML page is network-first (always try fresh, fall back to
// cache only when genuinely offline); everything else stays cache-first
// for instant loads, since CSS/JS aren't session-sensitive.

const CACHE_NAME = 'us-app-shell-v3';
const SHELL_ASSETS = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/js/api.js',
  '/static/js/utils.js',
  '/static/js/state.js',
  '/static/js/views/onboarding.js',
  '/static/js/views/home.js',
  '/static/js/views/games.js',
  '/static/js/views/wyr.js',
  '/static/js/views/know_each_other.js',
  '/static/js/views/emoji_story.js',
  '/static/js/views/twenty_questions.js',
  '/static/js/views/who_would.js',
  '/static/js/views/challenges.js',
  '/static/js/views/appreciation.js',
  '/static/js/views/questions.js',
  '/static/js/views/memories.js',
  '/static/js/views/history.js',
  '/static/js/views/stats.js',
  '/static/js/views/settings.js',
  '/static/js/views/round.js',
  '/static/js/views/past_answers.js',
  '/static/js/views/game_screen.js',
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

  // The HTML document (navigation requests, and "/" specifically) always
  // needs a fresh CSRF token tied to the current session - network-first,
  // only falling back to the cached shell when there's no connectivity.
  const isDocumentRequest = event.request.mode === 'navigate' || url.pathname === '/';
  if (isDocumentRequest) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.status === 200 && response.type === 'basic') {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Everything else (CSS/JS/manifest): cache-first for instant loads,
  // with a background refresh for next time. Not session-sensitive, so
  // staleness here doesn't cause the CSRF problem the HTML page can.
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
