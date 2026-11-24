"""Catalog browsing, cookie, wishlist and review tests."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from orders.models import Order, OrderItem

from .models import Category, CraftTradition, Product, Review, Wishlist


class CatalogTests(TestCase):
    """Exercise public browsing and buyer-only product actions."""

    @classmethod
    def setUpTestData(cls):
        """Make thirteen products so pagination has two pages."""
        cls.artisan = User.objects.create_user("maker", password="ExamplePass2026!")
        cls.buyer = User.objects.create_user("buyer", password="ExamplePass2026!")
        Profile.objects.create(
            user=cls.artisan, role="artisan", phone="9876543210",
            city="Patna", state="Bihar", is_verified=True, verification_status="approved",
        )
        Profile.objects.create(
            user=cls.buyer, role="buyer", phone="9876543211", city="Delhi", state="Delhi",
        )
        cls.category = Category.objects.create(name="Paintings", slug="paintings")
        cls.craft = CraftTradition.objects.create(
            name="Madhubani", slug="madhubani", state="Bihar", description="Hand-painted art."
        )
        cls.products = []
        for number in range(13):
            cls.products.append(Product.objects.create(
                artisan=cls.artisan, category=cls.category, craft=cls.craft,
                title=f"Cotton Art {number}", raw_notes="Drawn on cotton paper.",
                materials="cotton paper", technique="hand painting", description="A handmade painting.",
                price=f"{200 + number}.00", stock=3,
                image="products/test.jpg", status="published",
            ))

    def test_filters_and_pagination_keep_query_string(self):
        """Search and page work together without losing the search term."""
        response = self.client.get(reverse("catalog:product_list"), {"q": "cotton", "page": "2"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page_obj"]), 1)
        self.assertEqual(response.context["page_obj"].paginator.count, 13)
        self.assertEqual(response.context["query_string"], "q=cotton")

    def test_filters_can_limit_price_state_and_verified_artisans(self):
        """Several GET filters combine into one ORM query."""
        response = self.client.get(reverse("catalog:product_list"), {
            "category": self.category.pk, "craft": self.craft.pk, "state": "Bihar",
            "min_price": "205", "max_price": "206", "verified_only": "on",
            "sort": "price_desc",
        })
        self.assertEqual(response.context["page_obj"].paginator.count, 2)
        self.assertEqual(response.context["page_obj"][0].title, "Cotton Art 6")

    def test_invalid_price_range_displays_error(self):
        """A maximum below the minimum does not break browsing."""
        response = self.client.get(reverse("catalog:product_list"), {
            "min_price": "500", "max_price": "100",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("max_price", response.context["form"].errors)

    def test_top_rated_sort_uses_review_average(self):
        """Reviewed pieces rise above items with no reviews."""
        Review.objects.create(product=self.products[0], buyer=self.buyer, rating=5)
        response = self.client.get(reverse("catalog:product_list"), {"sort": "rated"})
        self.assertEqual(response.context["page_obj"][0].pk, self.products[0].pk)

    def test_wrong_slug_permanently_redirects_before_view_count(self):
        """Only visits to the canonical detail URL count as views."""
        product = self.products[0]
        response = self.client.get(reverse("catalog:product_detail", args=[product.pk, "wrong"]))
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], product.get_absolute_url())
        product.refresh_from_db()
        self.assertEqual(product.view_count, 0)
        self.assertEqual(self.client.get(product.get_absolute_url()).status_code, 200)
        product.refresh_from_db()
        self.assertEqual(product.view_count, 1)

    def test_recent_cookie_shows_products_on_home(self):
        """Detail visits leave a small cookie read by the home page."""
        product = self.products[0]
        response = self.client.get(product.get_absolute_url())
        self.assertEqual(response.cookies["recently_viewed"].value, str(product.pk))
        home = self.client.get(reverse("core:home"))
        self.assertEqual(home.context["recent_products"][0].pk, product.pk)

    def test_draft_can_only_be_previewed_by_its_owner(self):
        """Visitors and buyers cannot open a draft detail URL."""
        draft = self.products[0]
        draft.status = "draft"
        draft.save(update_fields=["status"])
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)
        self.client.force_login(self.artisan)
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 200)

    def test_wishlist_is_buyer_only_and_uses_post(self):
        """The buyer saves and removes a published product with POSTs."""
        product = self.products[0]
        url = reverse("catalog:wishlist_toggle", args=[product.pk])
        self.client.force_login(self.artisan)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), product.get_absolute_url())
        self.assertTrue(Wishlist.objects.filter(user=self.buyer, product=product).exists())
        self.assertRedirects(self.client.post(url), product.get_absolute_url())
        self.assertFalse(Wishlist.objects.filter(user=self.buyer, product=product).exists())

    def test_review_requires_delivered_purchase_and_is_unique(self):
        """Only a buyer with a delivered item can review it once."""
        product = self.products[0]
        url = reverse("catalog:review", args=[product.pk])
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.post(url, {"rating": 5, "comment": "Lovely."}).status_code, 404)
        order = Order.objects.create(
            buyer=self.buyer, full_name="Buyer", phone="9876543211", address="12 Main Road",
            city="Delhi", state="Delhi", pincode="110001", payment_method="cod", total="200.00",
        )
        OrderItem.objects.create(
            order=order, product=product, quantity=1, unit_price="200.00", status="delivered",
        )
        self.assertRedirects(self.client.post(url, {"rating": 5, "comment": "Lovely."}), product.get_absolute_url())
        self.assertRedirects(self.client.post(url, {"rating": 4}), product.get_absolute_url())
        self.assertEqual(Review.objects.filter(product=product, buyer=self.buyer).count(), 1)

    def test_craft_and_category_show_published_products(self):
        """Craft and category links render their named templates."""
        craft = self.client.get(reverse("catalog:craft_detail", args=[self.craft.slug]))
        category = self.client.get(reverse("catalog:category_detail", args=[self.category.slug]))
        self.assertTemplateUsed(craft, "catalog/craft_detail.html")
        self.assertTemplateUsed(category, "catalog/category_detail.html")
        self.assertContains(craft, "Cotton Art 0")
