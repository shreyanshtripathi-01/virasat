# Virasat

**Heritage in every handmade piece.** Virasat is a mobile-first, responsive Django marketplace for Indian artisans. It is a website, not a native mobile app. Python 3.12, Django 5.2, SQLite and Pillow are the core stack; `requests` is used only by the isolated optional AI service. All application views are function-based, and ordinary HTML forms work without custom JavaScript.

## Features at a glance

- **Visitors:** browse craft traditions, maker pages, products and real impact figures; switch between English and available Hindi descriptions.
- **Buyers:** save products, manage a session cart, order with COD or demo UPI, see their own invoices, review delivered pieces and post custom craft requests.
- **Artisans:** create and review AI-assisted or offline catalog drafts, publish their own products, fulfil orders, see net earnings and send offers to matching requests.
- **Verifiers and administrators:** approve or reject artisan verification; administrators maintain data using Django Admin.

## Local setup (Python 3.12)

From the `virasat_project` directory:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py runserver
```

If Python 3.12 is not installed, install it first. On a computer with `uv`, you can run `uv python install 3.12` and `uv venv --python 3.12 .venv`, then activate the environment and install the requirements as above. Visit <http://127.0.0.1:8000/> for the marketplace home page. Run `python manage.py seed_demo` for a local demonstration after migrating.

SQLite is the default database; the database file is created locally and is not committed. Uploaded images go in `media/`, and application logs go in `logs/app.log`. Both are ignored by Git.

### Settings

Development works without environment variables. Production must set a strong private key, `DEBUG=False` and its real hostnames. `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` become true when `DEBUG=False`. Never put production secrets in source control.

| Variable | Default for development | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | Development-only key when `DEBUG=True`; required otherwise | Django signing, sessions and CSRF |
| `DEBUG` | `True` | Set `False` on a public website |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1]` | Comma-separated public hostnames |
| `ANTHROPIC_API_KEY` | Empty | Optional AI provider; if absent, offline catalog drafts still work |
| `AI_MODEL` | `claude-haiku-5-5` | Provider model identifier; invalid or unavailable IDs trigger the fallback |
| `PLATFORM_FEE_PERCENT` | `5` | Percentage used by artisan payout calculations |

### Useful Django commands

Run these inside the activated virtual environment, from `virasat_project`:

| Command | What it does |
| --- | --- |
| `python manage.py runserver` | Starts the local development web server. |
| `python manage.py makemigrations` | Generates migration files after model changes. |
| `python manage.py migrate` | Applies pending migrations to the database. |
| `python manage.py createsuperuser` | Creates an administrator for the Django admin site. |
| `python manage.py shell` | Opens a Python shell with the Django project loaded. |
| `python manage.py check` | Checks project configuration for common problems. |
| `python manage.py test` | Runs the Django test suite. |
| `python manage.py seed_demo` | Creates or completes the local demo without overwriting existing records or images. |
| `python manage.py seed_demo --refresh-images` | Rebuilds all generated product images and craft covers. |

## Demo data (local development only)

After `migrate`, run:

```bash
python manage.py seed_demo
```

This creates 12 users, seven categories, nine craft traditions, 20 products with original 1200 x 1500 Pillow artwork, nine 800 x 800 craft covers, three orders, three buyer requests and four proposals. It is safe to run twice: existing demo records, passwords and images are not overwritten. It refuses to run when `DEBUG=False`, because the demo password is public. No images are downloaded.

To rebuild every product image and craft cover, including existing files, run `python manage.py seed_demo --refresh-images`. To use an owned photograph for a product, place it at `media/seed_photos/<product-slug>.jpg` (`.jpeg`, `.png` and `.webp` also work) and refresh. The command crops it to 4:5, resizes it to 1200 x 1500, keeps it under 250 KB and uses it instead of the generated art. See [`docs/imagery.md`](docs/imagery.md) for the craft palettes, product slugs and ownership notes.

**Demo password for newly created accounts:** `VirasatDemo2026!` (development use only).

| Role | Usernames |
| --- | --- |
| Admin | `admin` |
| Verifier | `verifier` |
| Artisans | `anita`, `sulekha`, `shabnam`, `fatima`, `jaspreet`, `lakshmi` |
| Buyers | `neha`, `rohan`, `tara`, `imran` |

Four artisans are marked verified; two remain in the pending queue. The Verifier group has the `can_verify_artisan` permission. Seeded AI-source labels illustrate catalog states; actual AI drafts use `catalog/ai_service.py` and always require maker review. Log in to the admin at <http://127.0.0.1:8000/admin/> with the admin demo account.

## Accounts (Phase 3)

Visit `/accounts/register/` to join as an artisan or buyer, or `/accounts/login/` to sign in. The login form offers a two-week "keep me signed in" option; without it the session ends when the browser closes. Artisans have public pages at `/artisans/<user-id>/`. Verifiers can approve or reject pending artisans at `/accounts/verify/`; rejected accounts stay active but leave the pending queue. Only the admin or seed command creates verifier accounts.

## Browse crafts (Phase 4)

The home page shows featured work, craft traditions and live counts. `/products/` searches, filters and sorts published pieces using GET parameters and paginates 12 per page. Product pages show the maker, craft story, buyer reviews and care instructions. Recently viewed products are remembered in a cookie; the footer switches descriptions between English and Hindi. Buyers can save products and review only items delivered to them. Images in the seeded demo are original illustrations, not photos of actual products.

All business-record changes (cart, orders, products, verification, reviews and proposals) use POST. The explicitly requested GET language switch and product-detail view also set preference/recent-item cookies and increment a view counter; they do not alter purchases or ownership.

## Artisan catalog (Phase 5)

Artisans can add a product at `/dashboard/products/new/`, describe it in their own words and upload a photo. An optional Anthropic request drafts editable catalog text; without a key, when the provider fails or after 15 AI requests per session per day, a deterministic offline draft is used. Every new or regenerated product stays a draft until the artisan reviews and publishes it. Artisans can edit, preview, archive or delete only their own listings. A product with past orders cannot be deleted; archive it instead. Do not put your API key in source code.

## Cart and orders (Phase 6)

Buyers add published products to a session cart, update quantities and check out with cash on delivery or UPI (demo). UPI is a demonstration; no payment is taken. Checkout rechecks stock in a database transaction and saves the unit price with each purchased item. Buyers can download a text invoice and cancel an item only while it is placed; stock is returned. Artisans can confirm, ship and mark their own order items delivered and see their share after the platform fee.

## Buyer requests and artisan offers (Phase 7)

Buyers post requests at `/requests/new/` with a future date, quantity and budget. Artisans browse `/requests/` or find ranked matches at `/requests/matches/`; category and craft matches each add two points, and a state match adds one. Each artisan can make one offer per request. The buyer can accept an offer, automatically decline other pending offers, or close the request. Private quotes are shown only to the request owner and the proposing artisan.

## Public impact (Phase 8)

Visit `/impact/` for live counts, leading crafts by delivered sales, top-rated products and the total artisan payout after the fee. The artisan dashboard separates earnings from delivered items and not-yet-delivered items. Cancelled orders are not counted as paid earnings.

## Errors and logs (Phase 9)

Virasat has custom 400, 403, 404 and 500 pages. With `DEBUG=False`, visitors do not see tracebacks. A missing or expired CSRF token shows the same styled access-denied page. Application events go to the terminal and the ignored `logs/app.log`; passwords and API keys are never logged. See [`docs/debugging_notes.md`](docs/debugging_notes.md) for examples from this project.

## Add to Home Screen (Phase 12, optional extension)

Virasat can be installed from Chrome on localhost or an HTTPS deployment. The manifest is at `/manifest.webmanifest`, the service worker is at `/sw.js`, and the offline fallback is at `/offline/`. When the network fails, a page reload shows the branded offline page. The worker caches only the offline page, the site stylesheet and the app icons; it never caches HTML pages, POST requests or private areas such as the cart and checkout. This feature is outside the INT253 syllabus and is not required for any marketplace flow. See [`docs/pwa.md`](docs/pwa.md) for the DevTools test steps and limits. The icon generator is `scripts/make_icons.py`.

## Tests (Phase 10)

Run `python manage.py test -v 2` from the activated virtual environment. The suite uses its own temporary database and does not change the demo data. The passing full output and coverage summary are in [`docs/test_report.md`](docs/test_report.md).

## Folder structure and project report

```text
virasat_project/
├── manage.py, requirements.txt, README.md
├── virasat/                 # settings, root URLs, WSGI and ASGI
├── accounts/                # registration, profiles and verification
├── catalog/                 # crafts, products, art generator, AI drafts and seed_demo
├── orders/                  # session cart, checkout and fulfilment
├── linkage/                 # requests, offers and ORM matching
├── core/                    # home, impact and error handlers
├── templates/               # pages and reusable partials
├── static/css/, static/img/ # responsive styles and original SVGs
├── media/, logs/            # local images and logs; ignored by Git
└── docs/                    # viva, SRS, model, URL, test and deployment notes
```

For the project report and viva, see [`docs/syllabus_mapping.md`](docs/syllabus_mapping.md), [`docs/model_summary.md`](docs/model_summary.md), [`docs/url_map.md`](docs/url_map.md), [`docs/feature_list.md`](docs/feature_list.md), [`docs/data_flows.md`](docs/data_flows.md), [`docs/imagery.md`](docs/imagery.md), [`docs/viva_cheatsheet.md`](docs/viva_cheatsheet.md) and [`docs/deployment.md`](docs/deployment.md). [`docs/shell_demo.md`](docs/shell_demo.md) has real ORM outputs. The optional AI feature falls back automatically; no API key is needed for a complete local demo.

## Redesigned interface and report assets

The public and signed-in interfaces use the Selvedge design system: forest ink and sage fields on linen, Manrope typography, a circular maker seal, a sticky pill header and editorial commerce layouts. [`DESIGN.md`](DESIGN.md) records the visual system, [`PRODUCT.md`](PRODUCT.md) records the product truth, and [`docs/skill_review.md`](docs/skill_review.md) records the final design review. The final verification suite contains 93 passing tests. Browser evidence and phase notes are in `docs/ui_review/` and `docs/phase15.md` through `docs/phase18.md`. The Phase 17 review covers four viewport sizes and all three roles.

Report diagrams and real screen captures are in [`docs/report_assets/`](docs/report_assets/README.md). Rebuild the code-derived diagrams with `python scripts/build_report_assets.py`, recapture screens with `NODE_PATH=/tmp/opencode/pw/node_modules node scripts/report_screenshots.cjs` against the server on port 8003 after the interface is frozen, then run `python scripts/validate_report_assets.py`. Refresh test evidence with `python scripts/test_report.py`; run the punctuation guard with `python scripts/check_dashes.py`.

Browser and document tools are development-only. Install Playwright Core and axe separately with `npm install --prefix /tmp/opencode/pw --no-save playwright-core @axe-core/playwright`; use `requirements-dev.txt` for optional document tooling. The application `requirements.txt` is unchanged.

The final SRS Word document and PDF are not generated yet. Student and assessment details are confirmed. Phase 19 is blocked on the repository and deployment links and the supplied `docs/Project_Report_Format.docx`. The final report builder and its rebuild command will be added after those inputs are confirmed, rather than publishing a report with invented details.
