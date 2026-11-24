# Add to Home Screen

Virasat includes a small Progressive Web App layer. The core marketplace does not depend on it. This feature is an optional extension and is outside the INT253 syllabus.

## What it does

- `/manifest.webmanifest` describes the app name, colours, icons, start route and three shortcuts.
- `/sw.js` is served from the site root with `Service-Worker-Allowed: /`, so it can control every page.
- The service worker precaches the offline fallback, the site stylesheet and the app icons.
- A page navigation is loaded from the network first. If the network fails, the worker returns `/offline/`.
- Same-origin requests under `/static/` use stale-while-revalidate. Cached files load immediately while a fresh copy is fetched.
- The worker never caches HTML pages, POST requests, or responses under `/admin/`, `/accounts/`, `/orders/checkout/` or `/cart/`.
- Old `virasat-` caches are deleted when a new worker activates.
- `static/js/pwa-register.js` registers the worker only when the browser supports service workers.
- `scripts/make_icons.py` rebuilds the PNG icons with Pillow.

The offline page deliberately has no home link. Virasat never caches ordinary HTML pages, so a cached home route never exists. Offering a home link while offline would be misleading. The page offers a retry button instead.

## Test in Chrome DevTools

1. Start the project on `http://127.0.0.1:8000/`.
2. Open Chrome DevTools, then **Application**.
3. Open **Manifest**. Confirm the name, colours, icons and shortcuts.
4. Open **Service Workers**. Confirm `/sw.js` is activated and running.
5. Reload once so the worker controls the page.
6. Tick **Offline** under **Service Workers** or in the **Network** tab.
7. Reload. The Virasat offline page should appear.
8. Untick **Offline** and use **Try again**.

Chrome shows an install icon in the address bar only on `localhost` or an HTTPS origin. A plain HTTP address on another machine is not a secure context, so installation will not be offered there.

## Honest scope

This is not a native mobile app. It does not work fully offline, does not store product or account pages, and does not provide background sync or push notifications. The marketplace itself remains a Django website built with function-based views and normal HTML forms. The PWA layer is optional presentation support, clearly marked as an extension in `docs/syllabus_mapping.md`.

## Relevant files

| File | Purpose |
| --- | --- |
| `core/views.py` | Manifest, service worker and offline function views |
| `core/urls.py` | Routes `/manifest.webmanifest`, `/sw.js`, `/offline/` |
| `templates/pwa/service-worker.js` | Cache policy |
| `templates/core/offline.html` | Offline fallback |
| `static/js/pwa-register.js` | Service worker registration |
| `scripts/make_icons.py` | Pillow icon generator |
| `static/img/icons/` | Committed PNG icons |
| `core/tests.py` | Manifest, worker, offline and dash tests |
