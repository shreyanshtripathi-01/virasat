"""Optional AI service and artisan catalog workflow tests."""

import json
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import requests
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import Profile
from .ai_service import generate_catalog_content
from .models import Category, CraftTradition, Product
from .views import draft_content_for


FACTS = ("Madhubani", "Bihar", "paper", "hand painting", "Flower patterns on handmade paper.", "hi")


class CatalogAIServiceTests(SimpleTestCase):
    """Prove the provider never makes offline generation unavailable."""

    @override_settings(ANTHROPIC_API_KEY="")
    def test_no_key_gives_deterministic_fallback(self):
        """The same supplied facts always produce the same offline text."""
        first = generate_catalog_content(*FACTS)
        self.assertEqual(first, generate_catalog_content(*FACTS))
        self.assertEqual(first["source"], "fallback")
        self.assertIn("हस्तनिर्मित", first["hindi_description"])

    @override_settings(ANTHROPIC_API_KEY="test-not-a-real-secret")
    @patch("catalog.ai_service.requests.post", side_effect=requests.Timeout)
    def test_timeout_falls_back(self, mocked_post):
        """A network timeout does not stop the artisan from saving a draft."""
        self.assertEqual(generate_catalog_content(*FACTS)["source"], "fallback")
        self.assertEqual(mocked_post.call_args.kwargs["timeout"], 20)

    @override_settings(ANTHROPIC_API_KEY="test-not-a-real-secret")
    @patch("catalog.ai_service.requests.post")
    def test_valid_json_is_parsed(self, mocked_post):
        """A valid provider reply gives editable text marked as AI."""
        data = {
            "title": "Lotus painting", "description": "A handmade painting.",
            "hindi_description": "हाथ से बना चित्र।", "heritage_story": "A craft from Bihar.",
            "care_instructions": "Keep dry.",
            "tags": ["lotus", "painting", "paper", "handmade", "bihar"],
        }
        mocked_post.return_value = Mock(status_code=200)
        mocked_post.return_value.json.return_value = {
            "content": [{"text": "```json\n" + json.dumps(data) + "\n```"}]
        }
        result = generate_catalog_content(*FACTS)
        self.assertEqual(result["source"], "ai")
        self.assertEqual(result["title"], "Lotus painting")

    @override_settings(ANTHROPIC_API_KEY="test-not-a-real-secret")
    @patch("catalog.ai_service.requests.post")
    def test_missing_fields_fall_back(self, mocked_post):
        """Incomplete JSON is not saved as a real AI draft."""
        mocked_post.return_value = Mock(status_code=200)
        mocked_post.return_value.json.return_value = {"content": [{"text": '{"title": "Only"}'}]}
        self.assertEqual(generate_catalog_content(*FACTS)["source"], "fallback")


class ArtisanCatalogTests(TestCase):
    """Check owner-only draft generation, review and publication."""

    @classmethod
    def setUpTestData(cls):
        """Create one maker, a second maker and one buyer."""
        cls.artisan = User.objects.create_user("maker", password="ExamplePass2026!")
        cls.other = User.objects.create_user("other", password="ExamplePass2026!")
        cls.buyer = User.objects.create_user("buyer", password="ExamplePass2026!")
        for user, role in [(cls.artisan, "artisan"), (cls.other, "artisan"), (cls.buyer, "buyer")]:
            Profile.objects.create(
                user=user, role=role, phone="9876543210", state="Bihar", city="Patna"
            )
        cls.category = Category.objects.create(name="Paintings", slug="paintings")
        cls.craft = CraftTradition.objects.create(
            name="Madhubani", slug="madhubani", state="Bihar", description="Folk painting."
        )

    def setUp(self):
        """Keep uploaded test images outside the project tree."""
        folder = TemporaryDirectory(dir="/tmp/opencode")
        self.addCleanup(folder.cleanup)
        settings_change = override_settings(MEDIA_ROOT=folder.name, ANTHROPIC_API_KEY="")
        settings_change.enable()
        self.addCleanup(settings_change.disable)

    def create_draft(self):
        """Post a real image and the minimum notes for an offline draft."""
        self.client.force_login(self.artisan)
        output = BytesIO()
        Image.new("RGB", (12, 12), "red").save(output, format="PNG")
        response = self.client.post(reverse("catalog:product_generate"), {
            "craft": self.craft.pk, "category": self.category.pk,
            "title_hint": "Lotus painting", "materials": "paper",
            "technique": "hand painting", "notes": "Painted lotus flowers on paper.",
            "price": "350.00", "stock": "2",
            "image": SimpleUploadedFile("lotus.png", output.getvalue(), content_type="image/png"),
        })
        self.assertEqual(response.status_code, 302)
        return Product.objects.get(title="Lotus painting")

    def test_offline_generation_saves_only_a_draft(self):
        """No API key is needed and the draft remains unpublished."""
        product = self.create_draft()
        self.assertEqual(product.status, "draft")
        self.assertEqual(product.ai_source, "fallback")
        self.assertIn("handmade", product.description.lower())
        self.client.logout()
        self.assertEqual(self.client.get(product.get_absolute_url()).status_code, 404)

    def test_artisan_can_edit_generated_text_then_publish(self):
        """Changing generated wording records the edit before publishing."""
        product = self.create_draft()
        response = self.client.post(reverse("catalog:product_edit", args=[product.pk]), {
            "category": self.category.pk, "craft": self.craft.pk,
            "title": product.title, "raw_notes": product.raw_notes,
            "materials": product.materials, "technique": product.technique,
            "description": "This is my own description of a painted lotus.",
            "hindi_description": product.hindi_description,
            "heritage_story": product.heritage_story,
            "care_instructions": product.care_instructions, "tags": product.tags,
            "price": "350.00", "stock": "2", "action": "publish",
        })
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.status, "published")
        self.assertTrue(product.ai_edited)

    def test_other_artisan_cannot_edit_or_regenerate(self):
        """Every management action filters by the signed-in owner."""
        product = self.create_draft()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("catalog:product_edit", args=[product.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("catalog:product_regenerate", args=[product.pk]), {"confirm": "yes"}).status_code, 404)

    def test_buyer_cannot_open_dashboard(self):
        """Buyer role access to artisan pages is a styled 403."""
        self.client.force_login(self.buyer)
        response = self.client.get(reverse("catalog:dashboard"))
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")

    def test_raw_form_rejects_only_symbols_and_zero_price(self):
        """Poor notes and free products cannot produce a draft."""
        self.client.force_login(self.artisan)
        response = self.client.post(reverse("catalog:product_generate"), {
            "craft": self.craft.pk, "category": self.category.pk,
            "title_hint": "12345", "materials": "paper", "technique": "painting",
            "notes": "123456789012345", "price": "0", "stock": "-1",
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Product.objects.count(), 0)

    def test_daily_session_cap_uses_offline_draft(self):
        """The sixteenth AI request in a session makes no network call."""
        request = RequestFactory().post("/dashboard/products/generate/")
        request.user = self.artisan
        request.session = SessionStore()
        request.session["ai_calls_date"] = timezone.localdate().isoformat()
        request.session["ai_calls_count"] = 15
        request._messages = FallbackStorage(request)
        with override_settings(ANTHROPIC_API_KEY="fake-key"):
            with patch("catalog.views.generate_catalog_content") as generator:
                content = draft_content_for(request, self.craft, "paper", "painting", "Painted lotus flowers.")
        self.assertEqual(content["source"], "fallback")
        generator.assert_not_called()

    def test_regenerate_requires_confirmation_and_returns_to_draft(self):
        """Regeneration cannot silently replace a published description."""
        product = self.create_draft()
        product.status = "published"
        product.save(update_fields=["status"])
        url = reverse("catalog:product_regenerate", args=[product.pk])
        self.assertEqual(self.client.post(url).status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.status, "published")
        self.assertEqual(self.client.post(url, {"confirm": "yes"}).status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.status, "draft")
        self.assertFalse(product.ai_edited)

    def test_status_publish_requires_explicit_draft_review(self):
        """A generated draft cannot publish through an unconfirmed status POST."""
        product = self.create_draft()
        url = reverse("catalog:product_status", args=[product.pk])
        response = self.client.post(url, {"status": "published"})
        self.assertRedirects(response, reverse("catalog:product_edit", args=[product.pk]))
        product.refresh_from_db()
        self.assertEqual(product.status, "draft")
        self.client.post(url, {"status": "published", "reviewed": "yes"})
        product.refresh_from_db()
        self.assertEqual(product.status, "published")
