# Phase 15: Public pages redesign

## Implemented

- Home: searchable hero, three product-art cards, five craft chips, buyer and artisan actions, trust rail, craft covers, four maker cards, two numbered journeys, request band and live figures.
- Browse: one responsive Bootstrap filter form, compact prices, verified switch, removable query-preserving chips, sorting and illustrated empty state.
- Detail: balanced sticky gallery, real fee split, buyer quantity choices capped at stock or ten, purchase and wishlist actions, four Bootstrap tabs, related work and a mobile purchase bar.
- Login and registration: craft-art panel on desktop, compact forms, collapsed password rules and two role cards using the original Django role field.
- Craft, category, maker, about, impact, error and offline pages use the shared shell and surfaces. Error pages have an inline SVG and a home action.

## Scope

Small context additions only: craft and maker counts, hero imagery, filter chips, related products, saved state, quantity choices and the configured platform fee. No models, migrations, permissions, URL names or POST behaviours changed. Registration uses a RadioSelect instead of a select for the same choices. All interactive components use the existing Bootstrap bundle; no custom application JavaScript was added.

## Verification

- Django check: no issues.
- Existing suite: 85 tests passed.
- Migration check: no changes.
- Global text and report XML dash scan: zero hits.
- Chrome: 13 public routes at 360x740, 768x1024 and 1366x768, with no overflow, duplicate IDs, broken loaded images or page errors. Filter opening and closing, mobile menu navigation, Care and Reviews tabs passed.
- Screenshots: `docs/ui_review/after-phase15/`; baseline public captures are in `after-phase14/` and `before-phase13/`.
- Browser command: `UI_BASE=http://127.0.0.1:8003 NODE_PATH=/tmp/opencode/pw/node_modules node scripts/ui_review.cjs`.
- The scanner is `python scripts/check_dashes.py`. Browser tooling is development-only.

## Done when checklist

- PASS: home, browse, cards, detail, auth and other public templates updated.
- PASS: required mobile filter drawer and product information tabs work.
- PASS: no horizontal overlap at 360px; hero text does not sit on patterned art.
- PASS: before and after evidence exists and shows distinct craft imagery and stronger hierarchy.
- PASS: existing functionality tests pass and no schema changes are needed.

The full authenticated responsive and role-flow sweep remains in Phases 16 and 17. Error handler templates are also exercised by the existing server-side tests; debug-mode missing URLs show Django's debug page instead of the custom 404.
