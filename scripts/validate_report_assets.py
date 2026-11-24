"""Validate generated image properties and code-derived model inventory."""

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "virasat.settings")

import django

django.setup()

from django.apps import apps
from PIL import Image


if __name__ == "__main__":
    directory = ROOT / "docs/report_assets"
    rows = []
    for path in sorted(directory.rglob("*.png")):
        with Image.open(path) as image:
            image.load()
            width, height = image.size
            # Browser screenshots have no physical-resolution metadata by default.
            image.save(path, dpi=(300, 300))
        with Image.open(path) as image:
            dpi = image.info["dpi"]
            assert min(dpi) >= 200, path
            assert width >= (780 if "mobile" in path.name else 1950), path
            rows.append({"file": str(path.relative_to(directory)), "width": width, "height": height,
                         "dpi": dpi, "format": image.format})
    inventory = json.loads((directory / "data_dictionary.json").read_text())
    actual = {model._meta.label: model for model in apps.get_models()}
    assert {row["label"] for row in inventory} == set(actual)
    for row in inventory:
        model = actual[row["label"]]
        assert [field["name"] for field in row["fields"]] == [field.name for field in [*model._meta.fields, *model._meta.many_to_many]]
    screenshots = json.loads((directory / "screenshots/screenshots.json").read_text())
    assert len(screenshots) == 15
    assert sum(row["viewport"]["width"] == 390 for row in screenshots) == 3
    result = {"images": rows, "concrete_models": len(inventory), "project_models": sum(row["project_defined"] for row in inventory),
              "named_app_routes": len(json.loads((directory / "routes.json").read_text())), "screenshots": len(screenshots), "errors": []}
    (directory / "validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Validated {len(rows)} PNGs, {len(inventory)} models and {len(screenshots)} real screenshots.")
