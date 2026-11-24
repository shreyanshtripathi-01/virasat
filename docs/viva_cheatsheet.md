# Virasat viva: 40 short questions and answers

All paths are relative to `virasat_project/`. AI is an isolated extra, not a Django syllabus unit.

## Unit I: setup and structure

1. **What is this project?** Virasat is a responsive Django website connecting buyers to handmade Indian craft and its makers; it is not a native mobile app.
2. **What does `manage.py` do?** It sets `DJANGO_SETTINGS_MODULE` and runs Django management commands; see `manage.py`.
3. **Why five apps?** `accounts`, `catalog`, `orders`, `linkage` and `core` group related models, views and URLs so each part is explainable.
4. **What does `runserver` do?** It starts Django's local development server, not a production deployment server.
5. **What is in `settings.py`?** `virasat/settings.py` configures apps, SQLite, templates, timezone, media/static paths, sessions and optional environment settings.

## Unit II: requests, URLs and responses

6. **What is a function-based view?** A Python function taking `request` and returning an `HttpResponse`; `core/views.py:home` is an example.
7. **Why `re_path` for products?** `catalog/urls.py` matches a numeric ID and the title slug; the view redirects an incorrect slug to the canonical URL.
8. **What does the VR regex do?** `orders/urls.py` matches paths such as `orders/VR000123/`, with exactly six digits following `VR`.
9. **How are routes named?** Each app defines `app_name` and route names; `reverse('orders:cart')` builds `/cart/` without hardcoding it.
10. **Why redirect after writing?** A redirect after successful POST prevents a refresh from resubmitting checkout or a proposal; see `orders/views.py:checkout`.
11. **When is `Http404` useful?** `catalog/views.py:submit_review` hides review submission for a buyer without a delivered purchase; owner-filtered `get_object_or_404` also protects private orders.
12. **Where do custom error pages live?** `templates/400.html`, `403.html`, `404.html`, `500.html`, with handlers in `virasat/urls.py` and views in `core/views.py`.

## Unit III: templates, debugging, testing

13. **Why use template inheritance?** `templates/base.html` provides a shared header, footer, CSS and blocks so pages change only their content.
14. **What does `{% include %}` do?** It reuses a fragment, for example `templates/partials/_product_card.html` on home and catalog pages.
15. **How does a template loop work here?** `templates/core/home.html` loops through craft traditions and featured Products; its `{% empty %}` branch handles no data.
16. **Why avoid `|safe`?** Product text and reviews are user-controlled; Django's default escaping stops injected HTML from executing.
17. **How does Hindi display work?** `templates/catalog/product_detail.html` checks `request.COOKIES.lang == 'hi'` and uses `hindi_description` when present.
18. **How do you debug a URL mistake?** Check the traceback and route order; Phase 4 fixed the review path being caught by the product slug regex. See `docs/debugging_notes.md`.
19. **How are views tested?** `django.test.TestCase` and the test Client issue GET/POST requests against a disposable database; see `docs/test_report.md`.

## Unit IV: forms, validation and POST

20. **Why GET for search and POST for checkout?** GET filters are repeatable URLs without private data; POST creates orders and includes a CSRF token.
21. **How does CSRF protection work?** Middleware checks a form token tied to a cookie for unsafe requests; templates add `{% csrf_token %}`. A missing token shows a styled 403.
22. **What is a ModelForm?** A form mapped to model fields; `orders/forms.py:CheckoutForm` validates fields before saving an `Order`.
23. **What is `clean_<field>()`?** One field's validation method; `linkage/forms.py:BuyerRequestForm.clean_needed_by` requires a future date.
24. **What is `clean()`?** Cross-field validation; `BuyerRequestForm.clean` rejects a minimum budget larger than the maximum.
25. **How are images validated?** `catalog/forms.py:validate_product_image` checks file size, extension and actual Pillow-checked image format; `accounts/forms.py:ProfileForm.clean_avatar` limits avatars to 2 MB.
26. **What happens after a successful POST?** Views redirect to a GET page and show a friendly Django message instead of rendering the POST response again.

## Unit V: models, database and permissions

27. **What is a model?** A class representing stored records; `catalog/models.py:Product` has artisan, craft, descriptions, price and status.
28. **What does a migration do?** It records a database schema change; `accounts/migrations/0002_profile_verification_status.py` also updated existing approved profiles.
29. **What is a foreign key?** A link to another row; `OrderItem.product` links a purchase snapshot to a Product, and `related_name='order_items'` lets you query back.
30. **Why save `unit_price`?** The current Product price might change later; `OrderItem.unit_price` keeps the purchase price used in invoices and payout math.
31. **What is `select_related`?** It joins one-to-one or foreign-key objects in the same query; `catalog/views.py:product_list` loads maker, craft and category.
32. **What is `prefetch_related`?** It loads collections in a separate query and attaches them; `catalog/views.py:product_detail` prefetched reviews of other products.
33. **What do `annotate` and `aggregate` do?** `linkage/matching.py` annotates each request's match score; `core/views.py:impact` sums delivered sales by craft.
34. **Why use `transaction.atomic()`?** `orders/views.py:place_order` rolls back all stock updates and order rows if any checkout step fails.
35. **How are roles and verifier permissions stored?** `Profile.role` identifies artisan/buyer/verifier; Groups are seeded in `seed_demo.py`; the Verifier group receives `accounts.can_verify_artisan`.

## Unit VI: users, cookies and sessions

36. **How do users sign in?** `accounts/views.py:login_view` validates `AuthenticationForm`, authenticates the credentials and calls `login()` to start a session.
37. **Why is logout POST-only?** Signing out changes session state; `logout_view` uses `@require_POST` and the navbar includes CSRF.
38. **Where is the cart stored?** `orders/cart.py` stores a dictionary of product IDs and quantities in `request.session['cart']`; it rechecks live Product stock.
39. **How are cookies different from sessions here?** Cookies store client-side language/recent IDs; Django sessions keep server-side login, cart and AI-call counter, with a session ID cookie.
40. **Why an AI fallback and call cap?** `catalog/ai_service.py` returns deterministic offline text on missing key or error; `catalog/views.py:draft_content_for` limits paid calls to 15 per session per day. Generated text never publishes automatically.
