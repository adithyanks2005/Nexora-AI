const CACHE_NAME = "nexora-ai-v6";

// Assets that never change — cache forever
const IMMUTABLE = [
  "/manifest.webmanifest",
  "/static/icons/icon.svg",
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(IMMUTABLE))
  );
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", event => {
  const { request } = event;
  const url = new URL(request.url);

  // Never intercept API calls or non-GET
  if (request.method !== "GET" || url.pathname.startsWith("/api/")) return;

  // Navigation: always go to network (fresh HTML), fall back to cache
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() => caches.match("/") || Response.error())
    );
    return;
  }

  // External CDN resources (Chart.js, Google Fonts, GSI) — cache on first load
  if (url.origin !== self.location.origin) {
    event.respondWith(
      caches.match(request).then(cached => {
        if (cached) return cached;
        return fetch(request).then(res => {
          const copy = res.clone();
          caches.open(CACHE_NAME).then(c => c.put(request, copy));
          return res;
        });
      })
    );
    return;
  }

  // Static assets (/static/*, /manifest.webmanifest) — cache-first
  if (url.pathname.startsWith("/static/") || url.pathname === "/manifest.webmanifest") {
    event.respondWith(
      caches.match(request).then(cached => {
        if (cached) return cached;
        return fetch(request).then(res => {
          const copy = res.clone();
          caches.open(CACHE_NAME).then(c => c.put(request, copy));
          return res;
        });
      })
    );
    return;
  }

  // Everything else — network only
  event.respondWith(fetch(request));
});
