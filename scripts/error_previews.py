"""Render real error templates for browser checks without adding app URLs."""

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "virasat.settings")

import django

django.setup()

from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory


if __name__ == "__main__":
    output = Path("/tmp/opencode/error-previews")
    output.mkdir(exist_ok=True)
    request = RequestFactory().get("/", HTTP_HOST="127.0.0.1:8003")
    request.user = AnonymousUser()
    request.session = {}
    for code in (400, 403, 404, 500):
        html = render_to_string(f"{code}.html", request=request)
        (output / f"{code}.html").write_text(html, encoding="utf-8")
    print(output)
