"""Run browser checks against disposable copies of demo data and media."""

import os
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "virasat.settings")

from django.conf import settings
from django.core.management import execute_from_command_line


if __name__ == "__main__":
    sandbox = Path(tempfile.mkdtemp(prefix="virasat-review-", dir="/tmp/opencode"))
    shutil.copy2(ROOT / "db.sqlite3", sandbox / "db.sqlite3")
    shutil.copytree(ROOT / "media", sandbox / "media")
    settings.DATABASES["default"]["NAME"] = sandbox / "db.sqlite3"
    settings.MEDIA_ROOT = sandbox / "media"
    settings.DEBUG = True
    settings.SESSION_COOKIE_SECURE = False
    settings.CSRF_COOKIE_SECURE = False
    settings.ANTHROPIC_API_KEY = ""
    print(f"Isolated review data: {sandbox}", flush=True)
    execute_from_command_line([
        "manage.py", "runserver", sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:8004",
        "--noreload",
    ])
