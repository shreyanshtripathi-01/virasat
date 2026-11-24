# Report assets and source trace

These are assets, not the final report. The final report is deferred until its configuration and sample template are supplied.

## Diagram index

| File | Meaning | Actual implementation sources |
| --- | --- | --- |
| `01_system_context.png` | Roles, marketplace, optional API, database and media | App `urls.py`, `views.py`, `virasat/settings.py`, `catalog/ai_service.py` |
| `02_dfd_level0.png` | One process and all six specified external entities | Account, catalog, order and linkage views; AI request and parser |
| `03_dfd_level1.png` | Main processes and five domain data stores | `accounts/views.py`, `catalog/views.py`, `orders/views.py`, `linkage/views.py`, `core/views.py`, `orders/cart.py` |
| `04a_use_cases_buyers.png` | Visitor and buyer use cases | Public routes, buyer decorators, order ownership and review delivery checks |
| `04b_use_cases_artisans_staff.png` | Artisan, verifier and administrator use cases | Artisan decorators, verification permission and app `admin.py` registrations |
| `05_er_all_models.png` | All 16 registered concrete models | Django `_meta` for all installed apps |
| `05a_er_marketplace.png` | Ten project models and the built-in User | Four app `models.py` files and `auth.User` |
| `05b_er_framework.png` | Authentication, content types, admin logs and sessions | Built-in Django model metadata |
| `06_ai_sequence.png` | Draft request, conditional provider call, fallback, review and publish | `catalog/views.py:draft_content_for`, `generate_product`, `edit_product`; `catalog/ai_service.py` |

The Level 1 diagram groups people under "Marketplace users"; Level 0 names Visitor, Buyer, Artisan, Verifier, Administrator and AI Service separately. Django Admin maintenance is represented in the context and staff use-case diagrams rather than repeated as an eighth process connected to every Level 1 store.

## ER notation

- PK is the primary key. FK names use the actual database column names.
- A bracket after an FK gives the number of parent records that one child may reference: `[1]` is required and `[0..1]` is nullable.
- A crow foot at the child end means zero to many child records for a parent. A tee at a UNIQUE foreign key means zero or one child. Two crow feet denote many-to-many.
- Profile.user is UNIQUE. Profile.verified_by is a separate nullable link to User.
- Review has a unique product/buyer pair. Wishlist has a unique user/product pair. Proposal has a unique request/artisan pair. These constraints are also recorded in `data_dictionary.json`.
- Django's automatically created many-to-many join tables are represented as associations, not additional model nodes. There are 16 registered models, of which 10 are project-defined.
- Session has no relational foreign key to User. Django serializes authentication and cart data in session_data, so the diagram does not invent a Session-to-User FK.

## AI sequence interpretation

The provider is called only when a key is configured and the session's daily allowance is available. The views enforce the allowance. The draft service prepares a local fallback, validates provider JSON and cleans returned strings. A timeout, provider failure or invalid response selects the fallback. No key or an exhausted allowance bypasses the provider. The stored product remains a draft until the owner reviews and publishes it. The sequence's Draft service participant represents the plain-Python service functions, not a separate deployed server or background worker.

## Real screenshots

`screenshots/screenshots.json` records the route, role, viewport, scale and scroll offset for each capture. There are 12 desktop screens at 1366x1000 and three mobile screens at 390x844, all captured at device scale two. PNG metadata is set to 300 DPI without changing the rendered pixels.

The screens cover home, browse, detail, register, login, artisan dashboard, catalog description, bilingual catalog review, cart, checkout, order detail and requests. Mobile captures cover home, browse and checkout. These captures predate the Selvedge redesign and must be regenerated with `scripts/report_screenshots.cjs` before the final report is built. The review screen shows saved seeded offline content; it is not evidence of a live paid API call. Cart and checkout screenshots use a real session and do not submit an order. The earlier browser flow evidence does submit and fulfil orders, but only on disposable copies.

## Quality and reproducibility

DOT source is committed beside each diagram. All nine diagrams are rendered with Graphviz at 300 DPI in the project palette. Labels were wrapped and the ER diagrams separated into domain and framework views so they can be read at 6.5 inches wide. The all-model view provides coverage; use the two focused ER views for detailed report discussion. PNG files and the English/Hindi editor capture were visually inspected. `validation.json` records dimensions, physical resolution and inventory checks for all 24 PNGs.

```sh
python scripts/build_report_assets.py
python manage.py runserver 127.0.0.1:8003
NODE_PATH=/tmp/opencode/pw/node_modules node scripts/report_screenshots.cjs
python scripts/validate_report_assets.py
python scripts/check_dashes.py
```

Development prerequisites: Graphviz `dot`, system Chrome, Pillow, Node and Playwright Core. Report document tooling is listed in `requirements-dev.txt`, not the application requirements. `data_dictionary.json` captures every field, type, key, choice, relation and declared uniqueness constraint from the current models. `routes.json` captures named app routes with view names and source line numbers.
