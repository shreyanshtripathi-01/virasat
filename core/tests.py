"""Core home, language-cookie, PWA and punctuation-guard tests."""

import json
import os
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from accounts.models import Profile
from catalog.ai_service import clean_dashes, fallback_content
from catalog.models import Category, CraftTradition, Product, Review
from catalog.views import artisan_earnings
from orders.models import Order, OrderItem
from .views import server_error


class PublicPageTests(TestCase):
    """Check that public information pages need no account."""

    def test_home_and_about_work_without_seed_data(self):
        """Empty project pages have friendly, usable content."""
        self.assertEqual(self.client.get(reverse("core:home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("core:about")).status_code, 200)

    def test_language_cookie_and_safe_redirect(self):
        """The switch stores hi and never redirects to another host."""
        url = reverse("core:language", args=["hi"])
        response = self.client.get(url, HTTP_REFERER="https://untrusted.example/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")
        self.assertEqual(response.cookies["lang"].value, "hi")
        self.assertEqual(self.client.get("/language/fr/").status_code, 404)

    @override_settings(DEBUG=False)
    def test_custom_404_renders_with_debug_off(self):
        """Production-style unknown URLs render the Virasat error page."""
        response = self.client.get("/there-is-no-page/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertContains(response, "Go home", status_code=404)

    @override_settings(DEBUG=False)
    def test_custom_403_renders_with_debug_off(self):
        """A buyer cannot open the artisan dashboard in production mode."""
        buyer = User.objects.create_user("buyer", password="ExamplePass2026!")
        Profile.objects.create(
            user=buyer, role="buyer", phone="9876543210", city="Delhi", state="Delhi"
        )
        self.client.force_login(buyer)
        response = self.client.get(reverse("catalog:dashboard"))
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")
        self.assertContains(response, "Go home", status_code=403)

    def test_custom_500_view_hides_internal_details(self):
        """The server-error page has no traceback or sensitive text."""
        from django.contrib.auth.models import AnonymousUser

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        response = server_error(request)
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Please try again", response.content)
        self.assertNotIn(b"Traceback", response.content)

    def test_impact_counts_only_delivered_artisan_amounts(self):
        """Impact and earnings reflect actual delivered item price snapshots."""
        artisan = User.objects.create_user("maker", password="ExamplePass2026!")
        buyer = User.objects.create_user("buyer", password="ExamplePass2026!")
        Profile.objects.create(
            user=artisan, role="artisan", phone="9876543210", city="Patna",
            state="Bihar", is_verified=True, verification_status="approved",
        )
        category = Category.objects.create(name="Paintings", slug="paintings")
        craft = CraftTradition.objects.create(
            name="Madhubani", slug="madhubani", state="Bihar", description="Folk painting."
        )
        product = Product.objects.create(
            artisan=artisan, category=category, craft=craft, title="Lotus painting",
            raw_notes="Painted by hand on paper.", materials="paper", technique="painting",
            description="A painted lotus.", price="100.00", stock=3,
            image="products/test.jpg", status="published",
        )
        order = Order.objects.create(
            buyer=buyer, full_name="Buyer", phone="9876543211", address="1 Lane",
            city="Patna", state="Bihar", pincode="800001", payment_method="cod", total="200.00",
        )
        for status in ["delivered", "placed"]:
            OrderItem.objects.create(order=order, product=product, quantity=1, unit_price="100.00", status=status)
        Review.objects.create(product=product, buyer=buyer, rating=5)
        response = self.client.get(reverse("core:impact"))
        self.assertEqual(response.context["verified_artisans"], 1)
        self.assertEqual(response.context["published_count"], 1)
        self.assertEqual(response.context["state_count"], 1)
        self.assertEqual(response.context["craft_count"], 1)
        self.assertEqual(response.context["artisan_paid"], Decimal("95.00"))
        self.assertEqual(response.context["top_crafts"][0].sales, Decimal("100.00"))
        self.assertEqual(artisan_earnings(artisan), {
            "delivered": Decimal("95.00"), "pending": Decimal("95.00"),
        })


class PWATests(TestCase):
    """The installable web app files are served with the promised headers."""

    def test_manifest_is_valid_json_with_required_fields(self):
        """The manifest names the app, its start route and its icons."""
        response = self.client.get(reverse("core:manifest"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/manifest+json")
        data = json.loads(response.content)
        self.assertEqual(data["name"], "Virasat")
        self.assertEqual(data["start_url"], "/?source=pwa")
        self.assertEqual(data["display"], "standalone")
        self.assertEqual(data["theme_color"], "#1F2A56")
        self.assertEqual(len(data["icons"]), 3)
        self.assertEqual(
            [shortcut["name"] for shortcut in data["shortcuts"]],
            ["Browse", "My orders", "Requests"],
        )

    def test_service_worker_has_root_scope_header(self):
        """The worker is served from the root with JavaScript content type."""
        response = self.client.get(reverse("core:service_worker"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/javascript")
        self.assertEqual(response["Service-Worker-Allowed"], "/")
        self.assertContains(response, "virasat-v1")

    def test_offline_page_renders(self):
        """The cached offline fallback is a friendly branded page."""
        response = self.client.get(reverse("core:offline"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/offline.html")
        self.assertContains(response, "You are offline")


class DashGuardTests(TestCase):
    """Em and en dashes stay out of every project text file."""

    def test_project_text_contains_no_em_or_en_dashes(self):
        """Walk the repository and fail on the first forbidden character."""
        skip_dirs = {
            ".git", ".venv", "venv", "media", "node_modules", "logs",
            "staticfiles", "__pycache__",
        }
        suffixes = {
            ".py", ".html", ".css", ".js", ".md", ".txt", ".svg", ".json",
            ".webmanifest", ".csv", ".yml", ".yaml", ".xml", ".toml", ".ini", ".cjs", ".dot",
        }
        offenders = []
        for root, dirs, files in os.walk(settings.BASE_DIR):
            dirs[:] = [name for name in dirs if name not in skip_dirs]
            for name in files:
                path = Path(root) / name
                if path.suffix.lower() not in suffixes:
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                if "\u2014" in text or "\u2013" in text:
                    offenders.append(str(path.relative_to(settings.BASE_DIR)))
        self.assertEqual(offenders, [], "Forbidden dash found in: " + ", ".join(offenders))

    def test_clean_dashes_replaces_symbols_and_spaces(self):
        """The generated-text guard handles prose ranges and repeated spaces."""
        self.assertEqual(clean_dashes("One\u2014two"), "One, two")
        self.assertEqual(clean_dashes("1\u20135 pieces"), "1-5 pieces")
        self.assertEqual(clean_dashes("a  b"), "a b")
        self.assertNotIn("\u2014", clean_dashes("a\u2014b"))
        self.assertNotIn("\u2013", clean_dashes("a\u2013b"))

    def test_fallback_text_is_clean(self):
        """Offline AI fallback prose passes through the same guard."""
        draft = fallback_content(
            "Madhubani", "Bihar", "cotton\u2014hand spun", "brush work",
            "A careful note\u2014with a dash.", "en",
        )
        for value in draft.values():
            if isinstance(value, str):
                self.assertNotIn("\u2014", value)
                self.assertNotIn("\u2013", value)
