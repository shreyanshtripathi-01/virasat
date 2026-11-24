# Phase 17: Mobile, accessibility and dash sweep

## Done when checklist

- PASS: public and signed-in routes checked at 360x740, 390x844, 768x1024 and 1366x768.
- PASS: 140 real route/size combinations and 16 rendered error-template combinations without horizontal overflow.
- PASS: WCAG A and AA automated scans at 390px report zero violations on 35 route/role combinations and all four error templates, including text contrast checks.
- PASS: meaningful icon roles, mobile sort name, form error references, image dimensions, 16px inputs, focus, skip link and Hindi document language.
- PASS: keyboard skip link, Bootstrap tabs, Escape to close the drawer, reduced motion and purchase-bar clearance checked in Chrome.
- PASS: larger heart, filter-chip, breadcrumb, role, language and close targets; mobile body clearance added for bottom navigation.
- PASS: obsolete hero, craft-strip and detail rules removed, over 250 lines of legacy CSS. Fonts already use swap and host preconnects.
- PASS: eight presentation tests added. Full suite: 93 passed; check clean; no migrations; global dash scan zero hits.
- PASS: buyer, artisan and verifier state-changing browser flows repeated on disposable data.

## Evidence and limits

`docs/ui_review/phase17/audit.json`, `errors.json`, `keyboard.json` and `role-flows.json` contain reproducible results. The error previews render the actual templates and are intercepted only inside the development browser; no preview routes were added to the application. Error HTTP status codes are tested by Django separately.

Automated checks supplement, but do not replace, a screen-reader or physical-device review. Contrast was checked by axe on the rendered 390px pages, not certified across every possible user-uploaded image. Ordinary inline links inside prose retain the normal inline-text exception; standalone controls use large targets. The offline page is the only cached HTML page and does not promise offline shopping.

The baseline is the committed Phase 15 and Phase 16 capture sets. Phase 17 adds 390px and error captures. Initial scans found generic icons with prohibited aria-label usage and a hidden mobile sort label. Both were corrected and the final scan returned zero violations.

## Commands

```sh
python manage.py runserver 127.0.0.1:8003
NODE_PATH=/tmp/opencode/pw/node_modules node scripts/accessibility_review.cjs
python scripts/error_previews.py
NODE_PATH=/tmp/opencode/pw/node_modules node scripts/error_review.cjs
NODE_PATH=/tmp/opencode/pw/node_modules node scripts/keyboard_review.cjs
python manage.py test -v 2
python scripts/check_dashes.py
```

Playwright Core, axe, system Chrome and the development scripts are not application dependencies. The project remains server-rendered and has no new custom application JavaScript.
