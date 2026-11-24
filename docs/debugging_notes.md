# Debugging Virasat (INT253 Unit III)

## Safe local debugging

- `DEBUG=True` is for local development only. It shows Django's yellow error page and the traceback (the chain of calls that led to an error). Never leave it enabled on a public site: a traceback can expose settings and private details. With `DEBUG=False`, Virasat's 400, 403, 404 and 500 pages show short messages instead.
- Read the **last** traceback line first for the exception and the file/line above it for the cause. During Phase 1, `manage.py check` reported `admin.E202`: `Profile` links to `User` through both `user` and `verified_by`, so `ProfileInline` needed `fk_name = "user"`.
- During Phase 4, a review POST returned 301 instead of 404 in a test. The regex `product/<pk>/<slug>/` caught `product/<pk>/review/` before the review URL. Moving the specific review route above the regex route fixed it.
- `print()` is useful in `manage.py shell` for one-off checks; remove debugging prints from production views. Use `logging.getLogger(__name__)` for persistent events instead. `logs/app.log` records AI fallback errors, failed sign-ins (never passwords) and successful order numbers.

## Commands to use from `virasat_project/`

```bash
python manage.py check
python manage.py showmigrations
python manage.py sqlmigrate accounts 0002
python manage.py shell
python manage.py dbshell
python manage.py test -v 2
```

- `check` detects model/admin/URL configuration problems. It reported no issues after the admin fix.
- `showmigrations` uses `[X]` for applied migrations; `accounts.0002_profile_verification_status` is applied in the demo database.
- `sqlmigrate accounts 0002` prints the SQL Django plans to run, without applying it. SQLite may recreate a table to alter a column.
- `shell` lets you inspect actual ORM values. On the seeded data, `OrderItem.objects.filter(status="delivered").count()` is `3`; the impact page's artisan payout is `3505.50` rupees. See `docs/shell_demo.md` for runnable queries and recorded outputs.
- `dbshell` opens the database's own command-line tool. SQLite requires the `sqlite3` executable on your computer; if it is unavailable, use `manage.py shell` instead.
- `test -v 2` reports each test and creates a disposable test database. Expected 403 and 404 cases are logged as warnings; a passing test still shows `OK`.

## Template debugging

If a page loads but a value is missing, check the view's `render()` context and the exact template variable, then inspect the model relationship. The bottom cart count reads `request.session.cart|length`; no custom context processor is needed. The product detail checks `request.COOKIES.lang` before choosing Hindi text. Django escapes product notes and reviews automatically: never add `|safe` to silence a display issue. Check mobile layouts at 360px and ensure links and form buttons remain tappable.

## Try error pages safely

With a real `SECRET_KEY` and `DEBUG=False`, request a non-existent URL for the custom 404. A buyer visiting `/dashboard/` gets the custom 403. Sending an invalid quantity to `/cart/add/<id>/` as a buyer shows the styled 400. Test `DEBUG=False` locally; do not deliberately raise an uncaught error on a live site just to see the 500 page.
