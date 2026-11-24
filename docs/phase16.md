# Phase 16: Logged-in pages redesign

## Done when checklist

- PASS: dashboard stat links, new-piece action, recent orders, matched briefs and delivered/pending CSS earnings bar.
- PASS: three-step catalog presentation, editable language cards, saved card preview, save draft, regeneration and final publish confirmation.
- PASS: responsive products table/cards, session cart quantities, sticky summary, payment radio cards and honest demo label.
- PASS: order badges, item timelines, plain-text invoice, cancellation and artisan next-status controls.
- PASS: request quantities, budgets, deadlines and score-based match labels; proposal decision cards and illustrated empty states.
- PASS: profile, verification and wishlist use the shared design system; messages remain dismissible Bootstrap alerts.
- PASS: all three role flows complete without changing the real demo database.

## Verification

- Django check: no issues. Migration check: no changes.
- Full suite: 85 tests passed. Global dash scan: zero hits.
- Chrome review: 20 signed-in routes across 360x740, 768x1024 and 1366x768, all HTTP 200 without horizontal overflow. Evidence: `docs/ui_review/after-phase16/review.json`.
- Real browser form flow on a disposable SQLite and media copy: artisan upload, offline draft, save and publish; buyer wishlist, cart, UPI demo checkout, invoice and cancellation; artisan confirmation, shipping and delivery; delivered-order review; buyer request, artisan proposal and acceptance; registration and verifier approval. Evidence: `role-flows.json` in the same directory.
- New registration was also checked without external CDN assets. Registration itself has no JavaScript dependency. Bootstrap interactions elsewhere used the normal bundle.
- Baseline captures: `docs/ui_review/before-phase16/`. Its order screenshot used an incorrect test URL and is a debug 404, not an application regression. Correct after captures use `/orders/VR000001/`.

## Scope and honesty

Display context additions provide dashboard previews and earnings percentages, cart quantity options, and deadline counts. The checkout payment widget now renders the original choices as radio cards. No models, migrations, permissions, URL names, save rules or state transitions changed.

The catalog still has one draft-generation endpoint. Manual writing is available by replacing the starter text on the review screen; no separate manual-generation endpoint is claimed. The final confirmation is a Bootstrap collapse in the existing edit form. The card preview deliberately shows saved data, not a live JavaScript preview. Accepting a proposal closes the request but does not create an order or transfer money.

Reproduce with `python scripts/review_server.py`, then `NODE_PATH=/tmp/opencode/pw/node_modules node scripts/role_flows.cjs`. Playwright Core is a development tool only. The isolated server forces an empty AI key and never writes to the source demo database or media.
