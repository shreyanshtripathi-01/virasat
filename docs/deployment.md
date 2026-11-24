# Deploy Virasat to PythonAnywhere (free-tier-compatible path)

Virasat is a WSGI Django website with SQLite, local media and optional AI. This guide describes the code in this repository. PythonAnywhere's available Python versions and free-tier limits can change: check the [supported versions](https://help.pythonanywhere.com/pages/PythonVersions) and your Web tab before creating a site. **Use Python 3.12** to match this project if your chosen system image offers it. If 3.12 is unavailable, change the system image if supported or choose another host; do not silently deploy under an untested Python version.

1. **Put the project on your account.** Upload `virasat_project/` (without `.venv/`, `db.sqlite3`, `.git/`, `media/` and secrets) using the Files tab, or push to your own private Git remote and clone it in a Bash console. Ensure `/home/USERNAME/virasat_project/manage.py` exists. Replace `USERNAME` below with your actual PythonAnywhere username.
2. **Create a matching virtual environment.** In a Bash console, run:

   ```bash
   python3.12 -m venv /home/USERNAME/.virtualenvs/virasat
   source /home/USERNAME/.virtualenvs/virasat/bin/activate
   cd /home/USERNAME/virasat_project
   python -m pip install -r requirements.txt
   ```

   If PythonAnywhere offers a different 3.12 binary path, use its documented path; the Web tab must use the same Python minor version as the virtual environment. Do not deploy a public database seeded with the documented demo password.
3. **Make a private environment file outside Git.** Generate a random key using `python -c 'import secrets; print(secrets.token_urlsafe(48))'`. Put this text in `/home/USERNAME/virasat_project/.env` (which `.gitignore` excludes), replacing the example key with your generated value:

   ```text
   SECRET_KEY=PASTE_YOUR_OWN_GENERATED_RANDOM_KEY_HERE
   DEBUG=False
   ALLOWED_HOSTS=USERNAME.pythonanywhere.com
   PLATFORM_FEE_PERCENT=5
   AI_MODEL=claude-haiku-5-5
   ```

   Run `chmod 600 /home/USERNAME/virasat_project/.env`. Leave `ANTHROPIC_API_KEY` **unset**: all artisan catalog flows work offline. Free PythonAnywhere accounts restrict outbound HTTP to an [allowlist](https://www.pythonanywhere.com/whitelist/), so the Anthropic endpoint may be inaccessible even if you have a key. Never assume it can be reached or expose a key in logs.
4. **Use the same settings in the console.** In the activated environment from step 2:

   ```bash
   set -a
   source /home/USERNAME/virasat_project/.env
   set +a
   python manage.py check
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic --noinput
   python manage.py test
   python manage.py check --deploy
   ```

   `createsuperuser` asks for your **own private password**. The local `seed_demo` command intentionally refuses `DEBUG=False`: its public demo credentials are unsafe on a public website. Create any public data with your own secure accounts in admin. Keep backups of `db.sqlite3` and `media/`.
5. **Create a web app.** On the Web tab choose **Add a new web app → Manual configuration → Python 3.12** (if available). Set its virtualenv to `/home/USERNAME/.virtualenvs/virasat`. Open its WSGI file from the Web tab. Replace the example WSGI application configuration with the following, adjusting `USERNAME`. This uses only Python's standard library, not `python-dotenv`:

   ```python
   import os
   import sys
   from pathlib import Path

   project = Path("/home/USERNAME/virasat_project")
   sys.path.insert(0, str(project))
   for raw_line in (project / ".env").read_text().splitlines():
       line = raw_line.strip()
       if line and not line.startswith("#"):
           name, value = line.split("=", 1)
           os.environ[name] = value
   os.environ.setdefault("DJANGO_SETTINGS_MODULE", "virasat.settings")

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

   The `.env` example uses unquoted `NAME=value` lines and an URL-safe random key. The WSGI file sets variables **before** loading Django; the Bash console sources the same file before running commands. The `.env` file is private server configuration, not a tracked source file.
6. **Map CSS and uploaded media.** Under **Static files** in the Web tab, add URL `/static/` → directory `/home/USERNAME/virasat_project/staticfiles/` (output of `collectstatic`) and URL `/media/` → directory `/home/USERNAME/virasat_project/media/`. Django serves media itself only in development (`DEBUG=True` in `virasat/urls.py`). New uploaded images live in `media/`; seed-generated demo images are not copied to a production site by Git.
7. **Force HTTPS in the Web tab, then reload.** Use PythonAnywhere's [Force HTTPS setting](https://help.pythonanywhere.com/pages/ForcingHTTPS) and click **Reload**. With `DEBUG=False`, `virasat/settings.py` marks session and CSRF cookies secure. Test `/`, `/products/`, `/accounts/login/`, `/admin/`, a POST login/logout and an uploaded media image at `https://USERNAME.pythonanywhere.com/`. Review your Web-tab error log and ignored `logs/app.log` if anything fails. With a custom domain, set up its HTTPS certificate before forcing HTTPS.

## Real deployment check from this project

The following is the actual local result using `DEBUG=False`, a long throwaway key, and `ALLOWED_HOSTS=example.pythonanywhere.com`. The key shown in the command was for a **check only**, not a deployment secret:

```text
System check identified some issues:

WARNINGS:
?: (security.W004) You have not set a value for the SECURE_HSTS_SECONDS setting. If your entire site is served only over SSL, you may want to consider setting a value and enabling HTTP Strict Transport Security. Be sure to read the documentation first; enabling HSTS carelessly can cause serious, irreversible problems.
?: (security.W008) Your SECURE_SSL_REDIRECT setting is not set to True. Unless your site should be available over both SSL and non-SSL connections, you may want to either set this setting True or configure a load balancer or reverse-proxy server to redirect all connections to HTTPS.

System check identified 2 issues (0 silenced).
```

**Why two warnings remain:** use the host's Force HTTPS slider to redirect at its front-end proxy, rather than assuming Django detects the original protocol (an in-app redirect behind a proxy can loop). HSTS is deliberately left off until HTTPS for the final domain has been verified; setting it too early can lock users into a broken HTTPS site. Do not claim the deployment check is warning-free. Re-run it on the live configuration and reconsider HSTS only after HTTPS is reliably enforced.

Source checked for the hosting steps: [PythonAnywhere existing Django project](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject), [static/media mapping](https://help.pythonanywhere.com/pages/DjangoStaticFiles), [environment variables](https://help.pythonanywhere.com/pages/EnvironmentVariables), [forcing HTTPS](https://help.pythonanywhere.com/pages/ForcingHTTPS), [outbound allowlist](https://help.pythonanywhere.com/pages/RequestingAllowlistAdditions). No external site was deployed during this project build.
