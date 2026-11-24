"""Generate report diagrams and inventories from Django's actual model and URL metadata."""

import html
import inspect
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "virasat.settings")

import django

django.setup()

from django.apps import apps
from django.db import models
from django.urls import URLResolver, get_resolver
from PIL import Image


OUT = ROOT / "docs/report_assets"
DOMAIN = {"accounts", "catalog", "orders", "linkage"}
PALETTE = {"indigo": "#1F2A56", "clay": "#B5482A", "cream": "#FBF5E9", "leaf": "#3E7C4F"}
ASSETS = []


def quote(value):
    return json.dumps(str(value), ensure_ascii=False)


class Graph:
    """Keep DOT source alongside every PNG for a reproducible report."""

    def __init__(self, name, title, direction="TB"):
        self.name = name
        self.lines = ["digraph G {", f"graph [rankdir={direction}, bgcolor=white, dpi=300, pad=.25, nodesep=.35, ranksep=.6, fontname=\"DejaVu Sans\", fontsize=24, labelloc=t, label={quote(title)}];",
                      'node [shape=box, style="rounded,filled", fillcolor="#FBF5E9", color="#1F2A56", fontcolor="#1F2A56", fontname="DejaVu Sans", fontsize=19, margin=".18,.12"];',
                      'edge [color="#615A53", fontcolor="#1F2A56", fontname="DejaVu Sans", fontsize=15, arrowsize=.7];']

    def node(self, key, label, **attrs):
        attributes = {"label": label, **attrs}
        self.lines.append(f"{quote(key)} [" + ",".join(f"{key}={quote(value)}" for key, value in attributes.items()) + "];")

    def edge(self, source, target, label="", **attrs):
        attributes = {"label": label, **attrs}
        self.lines.append(f"{quote(source)} -> {quote(target)} [" + ",".join(f"{key}={quote(value)}" for key, value in attributes.items()) + "];")

    def render(self):
        text = "\n".join(self.lines + ["}"])
        if any(character in text for character in (chr(0x2013), chr(0x2014))):
            raise ValueError("Forbidden punctuation in diagram")
        source = OUT / f"{self.name}.dot"
        source.write_text(text, encoding="utf-8")
        output = OUT / f"{self.name}.png"
        engine = ["-Kneato", "-n2"] if self.name.startswith("05") else []
        subprocess.run(["dot", *engine, "-Tpng", str(source), "-o", str(output)], check=True)
        with Image.open(output) as image:
            width, height = image.size
            image.save(output, dpi=(300, 300))
        with Image.open(output) as image:
            dpi = image.info["dpi"]
        ASSETS.append({"file": output.name, "title": self.name, "width": width, "height": height, "dpi": dpi})


def inventories():
    data = []
    for model in apps.get_models():
        fields = []
        for field in [*model._meta.fields, *model._meta.many_to_many]:
            relation = field.remote_field
            default = field.default
            fields.append({
                "name": field.name, "column": field.column, "type": field.get_internal_type(),
                "primary_key": field.primary_key, "null": field.null, "blank": field.blank,
                "unique": field.unique, "max_length": field.max_length,
                "max_digits": getattr(field, "max_digits", None), "decimal_places": getattr(field, "decimal_places", None),
                "choices": list(field.choices or []),
                "default": None if default is models.NOT_PROVIDED else (default.__name__ if callable(default) else str(default)),
                "related_model": relation.model._meta.label if relation else None,
                "on_delete": getattr(getattr(relation, "on_delete", None), "__name__", None),
                "one_to_one": field.one_to_one, "many_to_many": field.many_to_many,
            })
        data.append({"label": model._meta.label, "table": model._meta.db_table,
                     "project_defined": model._meta.app_label in DOMAIN,
                     "fields": fields, "unique_together": model._meta.unique_together,
                     "permissions": model._meta.permissions})
    (OUT / "data_dictionary.json").write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    routes = []

    def walk(patterns, prefix="", namespace=""):
        for pattern in patterns:
            if isinstance(pattern, URLResolver):
                child_namespace = ":".join(part for part in [namespace, pattern.namespace] if part)
                if child_namespace == "admin":
                    continue
                walk(pattern.url_patterns, prefix + str(pattern.pattern), child_namespace)
            elif pattern.name:
                view = inspect.unwrap(pattern.callback)
                if not view.__module__.split(".")[0] in DOMAIN | {"core"}:
                    continue
                routes.append({"name": f"{namespace}:{pattern.name}", "pattern": prefix + str(pattern.pattern),
                               "view": view.__module__ + "." + view.__name__,
                               "source": str(Path(inspect.getsourcefile(view)).relative_to(ROOT)),
                               "line": inspect.getsourcelines(view)[1]})
    walk(get_resolver().url_patterns)
    (OUT / "routes.json").write_text(json.dumps(routes, indent=2), encoding="utf-8")
    return data


def context_and_dfd():
    graph = Graph("01_system_context", "Virasat: system context", "LR")
    graph.node("app", "Virasat\nDjango marketplace", fillcolor=PALETTE["indigo"], fontcolor="white")
    for key, text in [("visitor", "Visitor"), ("buyer", "Buyer"), ("artisan", "Artisan"), ("verifier", "Verifier"), ("admin", "Administrator")]:
        graph.node(key, text, fillcolor="#ECEEF5")
    graph.edge("visitor", "app", "Browse and install")
    graph.edge("buyer", "app", "Shop and request")
    graph.edge("artisan", "app", "Sell and fulfil")
    graph.edge("verifier", "app", "Verify profiles")
    graph.edge("admin", "app", "Maintain records")
    graph.node("ai", "Anthropic API\nOptional extension", fillcolor="#FBEFEB")
    graph.node("data", "SQLite database\nand uploaded media", shape="cylinder")
    graph.edge("app", "ai", "Draft JSON\nover HTTPS", dir="both")
    graph.edge("app", "data", "Read and write", dir="both")
    graph.render()

    graph = Graph("02_dfd_level0", "Data flow diagram: Level 0", "LR")
    graph.node("system", "0\nVirasat marketplace", shape="ellipse", fillcolor=PALETTE["indigo"], fontcolor="white")
    flows = [
        ("visitor", "Visitor", "Search,\nlanguage", "Pages,\ninstall files"),
        ("buyer", "Buyer", "Order data,\nreviews, briefs", "Orders, invoices,\noffers"),
        ("artisan", "Artisan", "Product facts,\nstatus updates", "Drafts, orders,\nmatched briefs"),
        ("verifier", "Verifier", "Approve\nor reject", "Pending profiles,\nresult"),
        ("admin", "Administrator", "Maintenance\nchanges", "Admin records,\nresults"),
        ("ai", "AI Service", "Draft JSON\nor error", "Craft facts\nand notes"),
    ]
    for key, label, incoming, outgoing in flows:
        graph.node(key, label)
        left = key in {"visitor", "buyer", "artisan"}
        graph.edge(key, "system", incoming, constraint="true" if left else "false")
        graph.edge("system", key, outgoing, color=PALETTE["clay"], constraint="false" if left else "true")
    graph.render()

    graph = Graph("03_dfd_level1", "Data flow diagram: Level 1", "LR")
    graph.node("people", "Marketplace\nusers", fillcolor="#ECEEF5")
    processes = {"p1": "1 Account\nmanagement", "p2": "2 Catalog\nmanagement", "p3": "3 AI\ncataloging",
                 "p4": "4 Cart\nand orders", "p5": "5 Market\nlinkage", "p6": "6 Artisan\nverification", "p7": "7 Impact\nreporting"}
    for key, label in processes.items():
        graph.node(key, label, shape="ellipse", fillcolor="#FBEFEB")
    graph.lines.append("{rank=same; p1;p2;p3;p4;p5;p6;p7;}")
    stores = {"d1": "D1 Users\nand Profiles", "d2": "D2 Products, Crafts,\nCategories", "d3": "D3 Orders\nand Items", "d4": "D4 Requests\nand Proposals", "d5": "D5 Reviews\nand Wishlist"}
    for key, label in stores.items():
        graph.node(key, label, shape="cylinder")
    graph.node("ai", "AI Service\nOptional HTTPS API", fillcolor="#ECEEF5")
    graph.node("session", "Session cart\nand cookies", shape="note")
    for process, label in [("p1", "Credentials"), ("p2", "Search / edits"), ("p3", "Craft facts"), ("p4", "Checkout"), ("p5", "Briefs / offers"), ("p6", "Decision"), ("p7", "Impact")]:
        graph.edge("people", process, label, dir="both")
    for process, store, label in [("p1", "d1", "Accounts"), ("p2", "d2", "Catalog"), ("p2", "d5", "Reviews, saves"), ("p3", "d2", "Draft text"), ("p4", "d2", "Stock"), ("p4", "d3", "Orders"), ("p5", "d4", "Briefs, offers"), ("p6", "d1", "Verified status")]:
        graph.edge(process, store, label, dir="both")
    graph.edge("p3", "ai", "Facts / JSON", dir="both")
    graph.edge("p4", "session", "Quantities", dir="both")
    graph.edge("d2", "p7", "Published", constraint="false")
    graph.edge("d3", "p7", "Delivered", constraint="false")
    graph.edge("d1", "p7", "Verified", constraint="false")
    graph.edge("d5", "p7", "Ratings", constraint="false")
    graph.render()


def use_cases():
    for name, title, roles in [
        ("04a_use_cases_buyers", "Use cases: visitors and buyers", {
            "Visitor": ["Browse and filter catalog", "Read product and maker pages", "Read about and impact", "Choose language; install PWA"],
            "Buyer": ["Register, sign in, edit profile", "Save pieces; manage cart", "Checkout; track or cancel items", "Download invoice; review delivery", "Post briefs; decide on proposals"],
        }),
        ("04b_use_cases_artisans_staff", "Use cases: artisans and staff", {
            "Artisan": ["Describe, generate and review draft", "Publish, edit or archive pieces", "Fulfil orders; view earnings", "Find matches; send proposals", "Edit profile; view public page"],
            "Verifier": ["Review pending artisan profiles", "Approve or reject artisan"],
            "Administrator": ["Maintain records in Django Admin", "Manage groups and permissions"],
        }),
    ]:
        graph = Graph(name, title, "LR")
        for index, (actor, cases) in enumerate(roles.items()):
            graph.lines.append(f"subgraph cluster_{index} {{ color=\"#E4D7C5\";")
            graph.node(actor, actor, shape="box", fillcolor="#ECEEF5")
            for number, case in enumerate(cases):
                key = f"case_{index}_{number}"
                graph.node(key, case, shape="ellipse")
                graph.edge(actor, key, arrowhead="none")
            graph.lines.append("}")
        graph.render()


def er_diagram(name, title, selected):
    graph = Graph(name, title)
    graph.lines.append('graph [splines=polyline, nodesep=.8, ranksep=1.2];')
    order = ["auth.User", "catalog.Category", "catalog.CraftTradition", "accounts.Profile", "catalog.Product", "linkage.BuyerRequest", "orders.Order", "catalog.Review", "linkage.Proposal", "orders.OrderItem", "catalog.Wishlist", "auth.Group", "auth.Permission", "contenttypes.ContentType", "admin.LogEntry", "sessions.Session"]
    selected = sorted(selected, key=lambda model: order.index(model._meta.label))
    labels = {model._meta.label for model in selected}
    for index, model in enumerate(selected):
        rows = []
        for field in model._meta.fields:
            if field.primary_key or field.is_relation:
                kind = "PK" if field.primary_key else ("FK, UNIQUE" if field.one_to_one else "FK")
                count = "" if field.primary_key else (" [0..1]" if field.null else " [1]")
                rows.append(f'<TR><TD PORT="{field.name}" ALIGN="LEFT" BGCOLOR="#FBF5E9">{html.escape(kind + " " + field.column + count)}</TD></TR>')
        label = f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4"><TR><TD BGCOLOR="#1F2A56"><FONT COLOR="white"><B>{html.escape(model.__name__)}</B></FONT></TD></TR>{"".join(rows)}</TABLE>>'
        x, y = (index % 3) * 245, (len(selected) // 3 - index // 3) * 185
        graph.lines.append(f'{quote(model._meta.label)} [shape=plain, style="", fontsize=18, pos="{x},{y}!", label={label}];')
    for model in selected:
        for field in [*model._meta.fields, *model._meta.many_to_many]:
            if not field.is_relation or field.remote_field.model._meta.label not in labels:
                continue
            parent = field.remote_field.model._meta.label
            child = model._meta.label
            if field.many_to_many:
                graph.edge(parent, child, field.name, dir="both", arrowhead="crow", arrowtail="crow", constraint="false")
            else:
                attributes = {"dir": "both", "arrowtail": "tee", "arrowhead": "tee" if field.one_to_one else "crow", "constraint": "false"}
                graph.lines.append(f'{quote(parent)}:{field.remote_field.model._meta.pk.name} -> {quote(child)}:{field.name} [' + ",".join(f"{key}={quote(value)}" for key, value in attributes.items()) + "];")
    graph.render()


def sequence():
    graph = Graph("06_ai_sequence", "AI smart catalog\nRequest, fallback and artisan review")
    graph.lines.append('graph [ranksep=.7, nodesep=.4]; node [fontsize=18]; edge [fontsize=16];')
    actors = ["Artisan\nbrowser", "Django\nviews", "Draft\nservice", "AI\nService", "SQLite"]
    for index, actor in enumerate(actors):
        graph.node(f"h{index}", actor, group=f"c{index}", fillcolor="#ECEEF5")
    graph.lines.append("{rank=same; " + ";".join(f"h{n}" for n in range(5)) + ";}")
    for n in range(4):
        graph.edge(f"h{n}", f"h{n+1}", style="invis", weight="100")
    steps = [
        (0, 1, "1 POST notes\nand image"),
        (1, 2, "2 Key / quota\nDraft or fallback"),
        (2, 2, "3 Prepare clean\nlocal fallback"),
        (2, 3, "4 [allowed] facts\nHTTPS, 20 s timeout"),
        (3, 2, "5 JSON or error"),
        (2, 2, "6 ALT valid: clean JSON\nELSE: local fallback"),
        (2, 1, "7 Draft + source"),
        (1, 4, "8 Save draft Product"),
        (1, 0, "9 Redirect to review"),
        (0, 1, "10 POST edited fields\nSave or publish"),
        (1, 4, "11 Owner-checked status update"),
        (1, 0, "12 Saved status"),
    ]
    for row, (source, target, message) in enumerate(steps):
        for col in range(5):
            graph.node(f"r{row}c{col}", "", shape="point", width=".03", group=f"c{col}")
            previous = f"h{col}" if row == 0 else f"r{row-1}c{col}"
            graph.edge(previous, f"r{row}c{col}", style="dashed", arrowhead="none", color="#B5BDD5", weight="100")
        graph.lines.append("{rank=same; " + ";".join(f"r{row}c{n}" for n in range(5)) + ";}")
        graph.edge(f"r{row}c{source}", f"r{row}c{target}", message, constraint="false", color=PALETTE["clay"] if source == target else PALETTE["indigo"])
    graph.render()


if __name__ == "__main__":
    if not shutil.which("dot"):
        raise SystemExit("Install the Graphviz development tool to rebuild these diagrams.")
    OUT.mkdir(parents=True, exist_ok=True)
    data = inventories()
    context_and_dfd()
    use_cases()
    all_models = list(apps.get_models())
    er_diagram("05_er_all_models", "ER diagram: all concrete models", all_models)
    er_diagram("05a_er_marketplace", "ER diagram: marketplace and User", [model for model in all_models if model._meta.app_label in DOMAIN or model._meta.label == "auth.User"])
    er_diagram("05b_er_framework", "ER diagram: Django infrastructure", [model for model in all_models if model._meta.app_label not in DOMAIN])
    sequence()
    (OUT / "diagrams.json").write_text(json.dumps(ASSETS, indent=2), encoding="utf-8")
    print(f"Generated {len(ASSETS)} diagrams and inventories for {len(data)} concrete models.")
