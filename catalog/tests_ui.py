"""Regression checks for server-rendered presentation and buyer controls."""

from html.parser import HTMLParser
from urllib.parse import parse_qs

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from .models import Category, CraftTradition, Product


class Controls(HTMLParser):
    """Read form actions and select options without a third-party parser."""

    def __init__(self, text):
        super().__init__()
        self.forms = []
        self.selects = {}
        self.current_select = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.forms.append(attrs)
        elif tag == "select":
            self.current_select = attrs.get("id")
            self.selects[self.current_select] = []
        elif tag == "option" and self.current_select:
            self.selects[self.current_select].append(attrs.get("value"))

    def handle_endtag(self, tag):
        if tag == "select":
            self.current_select = None


class PresentationTests(TestCase):
    """The redesign must not expose buyer POST actions to other roles."""

    @classmethod
    def setUpTestData(cls):
        cls.artisan = User.objects.create_user("ui_maker", first_name="Asha", last_name="Devi")
        cls.buyer = User.objects.create_user("ui_buyer")
        for user, role in [(cls.artisan, "artisan"), (cls.buyer, "buyer")]:
            Profile.objects.create(user=user, role=role, phone="9876543210", state="Bihar", city="Patna")
        cls.category = Category.objects.create(name="Paintings", slug="paintings")
        cls.craft = CraftTradition.objects.create(name="Madhubani", slug="madhubani", state="Bihar", description="Folk painting.")
        cls.product = Product.objects.create(
            artisan=cls.artisan, category=cls.category, craft=cls.craft,
            title="Lotus panel", raw_notes="Painted carefully on cotton paper.",
            materials="Cotton paper", technique="Hand painting", description="A painted lotus.",
            hindi_description="कमल की हस्तनिर्मित कलाकृति।", price="200.00", stock=3,
            image="products/test.jpg", status="published", ai_source="manual",
        )

    def controls(self, url):
        return Controls(self.client.get(url).content.decode())

    def test_product_card_names_the_artisan_without_ai_note(self):
        response = self.client.get(reverse("catalog:product_list"))
        self.assertContains(response, "Asha Devi")
        self.assertContains(response, "Lotus panel")
        self.assertNotContains(response, "Description drafted with AI")

    def test_cart_form_is_only_rendered_for_buyers(self):
        action = reverse("orders:cart_add", args=[self.product.pk])
        url = reverse("catalog:product_list")
        self.assertFalse(any(form.get("action") == action for form in self.controls(url).forms))
        self.client.force_login(self.artisan)
        self.assertFalse(any(form.get("action") == action for form in self.controls(url).forms))
        self.client.force_login(self.buyer)
        self.assertTrue(any(form.get("action") == action and form.get("method") == "post" for form in self.controls(url).forms))

    def test_filter_chips_keep_other_parameters_and_remove_page(self):
        response = self.client.get(reverse("catalog:product_list"), {
            "q": "lotus", "craft": self.craft.pk, "verified_only": "on", "sort": "price_asc", "page": "2",
        })
        chips = response.context["active_filters"]
        search_chip = next(chip for chip in chips if chip["label"] == "Search")
        query = parse_qs(search_chip["query"])
        self.assertNotIn("q", query)
        self.assertNotIn("page", query)
        self.assertEqual(query["craft"], [str(self.craft.pk)])
        self.assertEqual(query["sort"], ["price_asc"])
        self.assertEqual(query["verified_only"], ["on"])

    def test_quantity_select_respects_stock(self):
        self.client.force_login(self.buyer)
        controls = self.controls(self.product.get_absolute_url())
        self.assertEqual(controls.selects["quantity-desktop"], ["1", "2", "3"])
        self.assertEqual(controls.selects["quantity-mobile"], ["1", "2", "3"])

    def test_quantity_select_caps_at_ten(self):
        Product.objects.filter(pk=self.product.pk).update(stock=20)
        self.client.force_login(self.buyer)
        self.assertEqual(self.controls(self.product.get_absolute_url()).selects["quantity-desktop"], [str(n) for n in range(1, 11)])

    def test_sold_out_product_has_no_purchase_select(self):
        Product.objects.filter(pk=self.product.pk).update(stock=0)
        self.client.force_login(self.buyer)
        self.assertNotIn("quantity-desktop", self.controls(self.product.get_absolute_url()).selects)

    def test_hindi_cookie_sets_document_language_and_description(self):
        self.client.cookies["lang"] = "hi"
        response = self.client.get(self.product.get_absolute_url())
        self.assertContains(response, '<html lang="hi">')
        self.assertContains(response, self.product.hindi_description)
        self.client.cookies["lang"] = "en"
        self.assertContains(self.client.get(reverse("core:home")), '<html lang="en">')

    def test_recent_section_only_appears_for_a_valid_cookie(self):
        self.assertNotContains(self.client.get(reverse("core:home")), 'id="recent-heading"')
        self.client.cookies["recently_viewed"] = str(self.product.pk)
        self.assertContains(self.client.get(reverse("core:home")), 'id="recent-heading"')
