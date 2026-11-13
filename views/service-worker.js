const CACHE_NAME = "felipe-tracker-saiyan-v7";
const APP_SHELL = [
  "/views/dashboard.html",
  "/views/manifest.json",
  "/views/icons/icon-192.png",
  "/views/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName.startsWith("felipe-tracker-") && cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
          return Promise.resolve();
        }),
      ))
      .then(() => self.clients.claim()),
  );
});

async function fetchAndCache(request) {
  const response = await fetch(request);
  if (response.ok || response.type === "opaque") {
    try {
      const cache = await caches.open(CACHE_NAME);
      await cache.put(request, response.clone());
    } catch (error) {
      console.warn("No se pudo guardar la respuesta en caché:", error);
    }
  }
  return response;
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const requestUrl = new URL(request.url);

  if (requestUrl.pathname.includes("/api/")) {
    event.respondWith(fetch(request));
    return;
  }

  if (request.method !== "GET") {
    return;
  }

  const networkUpdate = fetchAndCache(request);
  event.waitUntil(networkUpdate.then(() => undefined).catch(() => undefined));
  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    try {
      return await networkUpdate;
    } catch {
      if (request.mode === "navigate") {
        const appShell = await cache.match("/views/dashboard.html");
        if (appShell) {
          return appShell;
        }
      }
      return Response.error();
    }
  })());
});
