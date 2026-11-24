{% load static %}// Virasat service worker. Extension: offline support outside the INT253 syllabus.
const CACHE_NAME = "virasat-v1";
const OFFLINE_URL = "{% url 'core:offline' %}";
const PRECACHE_URLS = [
  OFFLINE_URL,
  "{% static 'css/theme.css' %}",
  "{% static 'img/icons/icon-192.png' %}",
  "{% static 'img/icons/icon-512.png' %}",
  "{% static 'img/icons/icon-512-maskable.png' %}",
  "{% static 'img/icons/apple-touch-icon-180.png' %}"
];
const BYPASS_PREFIXES = ["/admin/", "/accounts/", "/orders/checkout/", "/cart/"];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(PRECACHE_URLS);
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (names) {
      return Promise.all(names.map(function (name) {
        if (name.indexOf("virasat-") === 0 && name !== CACHE_NAME) {
          return caches.delete(name);
        }
        return Promise.resolve();
      }));
    }).then(function () {
      return self.clients.claim();
    })
  );
});

function isBypassed(pathname) {
  return BYPASS_PREFIXES.some(function (prefix) {
    return pathname.indexOf(prefix) === 0;
  });
}

function canCache(response) {
  if (!response || !response.ok || response.type !== "basic") {
    return false;
  }
  const type = response.headers.get("content-type") || "";
  return type.indexOf("text/html") === -1;
}

self.addEventListener("fetch", function (event) {
  const request = event.request;
  if (request.method !== "GET") {
    return;
  }
  const url = new URL(request.url);
  if (url.origin !== self.location.origin || isBypassed(url.pathname)) {
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request, {cache: "no-store"}).catch(function () {
        return caches.match(OFFLINE_URL).then(function (cached) {
          return cached || new Response("You are offline.", {
            status: 503,
            headers: {"Content-Type": "text/plain; charset=utf-8"}
          });
        });
      })
    );
    return;
  }

  if (url.pathname.indexOf("/static/") === 0) {
    const refresh = fetch(request, {cache: "no-store"}).then(function (response) {
      if (canCache(response)) {
        return caches.open(CACHE_NAME).then(function (cache) {
          return cache.put(request, response.clone()).then(function () {
            return response;
          });
        });
      }
      return response;
    }).catch(function () {
      return null;
    });
    event.waitUntil(refresh);
    event.respondWith(
      caches.match(request).then(function (cached) {
        return cached || refresh.then(function (response) {
          return response || new Response("", {status: 503});
        });
      })
    );
  }
});
