# INT253 syllabus map: Virasat

The paths below are relative to `virasat_project/`. Every example points to working code, not a proposed feature.

| Unit | Topic | Exact file and example |
| --- | --- | --- |
| I | Project, app structure and `manage.py` | `manage.py`; `virasat/settings.py`; five apps in `accounts/`, `catalog/`, `orders/`, `linkage/`, `core/`. Setup commands in `README.md`. |
| I | Django installation and commands | `requirements.txt` pins Django 5.2.8 and Pillow; `README.md` explains `runserver`, `makemigrations`, `migrate`, `createsuperuser`, `shell`, `check`, `test`. |
| II | Function-based views and request/response | `catalog/views.py:product_detail`, `orders/views.py:invoice` (text attachment), `accounts/views.py:logout_view`. No CBVs. |
| II | URL mapping, parameters and regex | `catalog/urls.py` product ID/slug regex; `orders/urls.py` `VR` six-digit routes; `core/urls.py` `language/<en|hi>/` regex. |
| II | Redirects, errors and custom views | `catalog/views.py:product_detail` redirects a wrong slug; `core/views.py:bad_request`, `permission_denied`, `page_not_found`, `server_error`; handlers in `virasat/urls.py`. |
| III | Templates, inheritance and includes | `templates/base.html` blocks `title`, `extra_head`, `content`, `extra_js`; `templates/partials/_product_card.html`, `_pagination.html`, `_form_field.html`. |
| III | Variables, loops and conditions | `templates/core/home.html` loops over products and crafts; `templates/catalog/product_detail.html` selects Hindi from `request.COOKIES.lang`; `templates/orders/order_detail.html` checks item status. |
| III | Debugging and tests | `docs/debugging_notes.md`; `accounts/tests.py`, `catalog/tests.py`, `catalog/tests_ai.py`, `catalog/tests_models.py`, `orders/tests.py`, `orders/tests_forms.py`, `linkage/tests.py`, `core/tests.py`; `docs/test_report.md`. |
| IV | Forms and ModelForms | `catalog/forms.py:ProductRawForm`, `ProductForm`, `ProductFilterForm`; `orders/forms.py:CheckoutForm`; `linkage/forms.py:BuyerRequestForm`, `ProposalForm`. |
| IV | GET vs POST, CSRF, redirect after POST | `catalog/views.py:product_list` reads GET; `orders/views.py:checkout` validates POST and redirects; every app POST template includes `{% csrf_token %}` (for example `templates/orders/checkout.html`). |
| IV | Field and form validation | `accounts/forms.py:ProfileForm.clean_avatar`; `catalog/forms.py:ProductForm.clean_raw_notes` and `clean`; `linkage/forms.py:BuyerRequestForm.clean_needed_by` and `clean`. |
| V | Models and migrations | `accounts/models.py`, `catalog/models.py`, `orders/models.py`, `linkage/models.py`; migrations in each app's `migrations/`. `accounts/migrations/0002_profile_verification_status.py` updates existing approved profiles. |
| V | ORM, foreign keys, joins and aggregation | `linkage/matching.py` scores with `Case`/`When`; `core/views.py:impact` aggregates sales; `catalog/views.py:product_list` uses `select_related`; `catalog/views.py:product_detail` uses `prefetch_related`. |
| V | Admin, groups and permissions | Each app's `admin.py`; `accounts/admin.py:ProfileAdmin.mark_artisans_verified`; `catalog/management/commands/seed_demo.py` creates Artisan, Buyer and Verifier groups and permission. |
| V | SQLite configuration and shell | `virasat/settings.py:DATABASES` with commented PostgreSQL alternative; `docs/shell_demo.md` has run-and-recorded ORM commands. |
| VI | Sessions and cookies | `orders/cart.py` uses `request.session['cart']`; `catalog/views.py:product_detail` saves `recently_viewed`; `core/views.py:change_language` saves `lang`. |
| VI | Login, logout and users | `accounts/views.py:register`, `login_view`, `logout_view`, `artisan_required`, `buyer_required`; role-specific views in `orders/views.py`, `catalog/views.py`, `linkage/views.py`. |

**Extensions outside the syllabus:** `catalog/ai_service.py` is the one permitted plain-Python external API integration. `catalog/views.py:draft_content_for` limits calls and uses its deterministic offline fallback. The Add to Home Screen layer (`core/views.py:manifest`, `service_worker`, `offline`; `templates/pwa/service-worker.js`) is also an optional extension and is not required for any marketplace flow. No Django API framework, signals, custom middleware or JavaScript framework is used, and the only page script is `static/js/pwa-register.js` for service worker registration. Both extensions are labelled in the interface and in `docs/pwa.md`.
