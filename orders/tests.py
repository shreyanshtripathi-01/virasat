"""Session cart, stock, ownership and order status tests."""

from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from catalog.models import Category, CraftTradition, Product

from .models import Order, OrderItem


class OrderFlowTests(TestCase):
    """Exercise checkout, buyers' orders and artisans' delivery steps."""

    @classmethod
    def setUpTestData(cls):
        """Create two buyers, two artisans and two published products."""
        cls.buyer = User.objects.create_user("buyer", password="ExamplePass2026!")
        cls.other_buyer = User.objects.create_user("otherbuyer", password="ExamplePass2026!")
        cls.artisan = User.objects.create_user("maker", password="ExamplePass2026!")
        cls.other_artisan = User.objects.create_user("othermaker", password="ExamplePass2026!")
        for user, role in [(cls.buyer, "buyer"), (cls.other_buyer, "buyer"),
                           (cls.artisan, "artisan"), (cls.other_artisan, "artisan")]:
            Profile.objects.create(user=user, role=role, phone="9876543210", city="Delhi", state="Delhi")
        category = Category.objects.create(name="Textiles", slug="textiles")
        craft = CraftTradition.objects.create(name="Bagru", slug="bagru", state="Rajasthan", description="Block printing.")
        cls.product = Product.objects.create(
            artisan=cls.artisan, category=category, craft=craft, title="Cotton stole",
            raw_notes="Printed by hand on cotton.", materials="cotton", technique="block printing",
            description="A soft cotton stole.", price=Decimal("200.00"), stock=3,
            image="products/test.jpg", status="published",
        )
        cls.other_product = Product.objects.create(
            artisan=cls.other_artisan, category=category, craft=craft, title="Cotton bag",
            raw_notes="Printed by hand on cotton.", materials="cotton", technique="block printing",
            description="A printed cotton bag.", price=Decimal("100.00"), stock=2,
            image="products/test.jpg", status="published",
        )

    def checkout_data(self):
        """Return valid delivery details for the test buyer."""
        return {
            "full_name": "Test Buyer", "phone": "9876543210", "address": "10 Market Road",
            "city": "Delhi", "state": "Delhi", "pincode": "110001", "payment_method": "upi_demo",
        }

    def add_product(self, product=None, quantity=1):
        """Sign in as the buyer and add a published product to the session."""
        self.client.force_login(self.buyer)
        product = product or self.product
        return self.client.post(reverse("orders:cart_add", args=[product.pk]), {"quantity": quantity})

    def test_cart_add_update_remove_and_session_persistence(self):
        """The session stores a capped quantity across different pages."""
        self.assertRedirects(self.add_product(quantity=20), reverse("orders:cart"))
        self.assertEqual(self.client.session["cart"][str(self.product.pk)], 3)
        self.client.get(reverse("core:home"))
        self.assertEqual(self.client.session["cart"][str(self.product.pk)], 3)
        self.client.post(reverse("orders:cart_update", args=[self.product.pk]), {"quantity": 2})
        self.assertEqual(self.client.session["cart"][str(self.product.pk)], 2)
        self.client.post(reverse("orders:cart_remove", args=[self.product.pk]))
        self.assertEqual(self.client.session["cart"], {})

    def test_cart_requires_buyer_and_post(self):
        """An artisan gets 403 and a GET cannot add an item."""
        self.client.force_login(self.artisan)
        self.assertEqual(self.client.get(reverse("orders:cart")).status_code, 403)
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(reverse("orders:cart_add", args=[self.product.pk])).status_code, 405)

    def test_invalid_quantity_has_styled_bad_request_page(self):
        """A malformed quantity returns 400 without touching the session."""
        self.client.force_login(self.buyer)
        response = self.client.post(reverse("orders:cart_add", args=[self.product.pk]), {
            "quantity": "many",
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Check your request", response.content)

    def test_checkout_decrements_stock_and_keeps_price_snapshot(self):
        """The order and its item use the price at checkout."""
        self.add_product(quantity=2)
        response = self.client.post(reverse("orders:checkout"), self.checkout_data())
        order = Order.objects.get(buyer=self.buyer)
        self.assertRedirects(response, reverse("orders:order_detail", args=[f"{order.pk:06d}"]))
        self.assertEqual(order.order_number, "VR000001")
        self.assertEqual(order.total, Decimal("400.00"))
        self.assertEqual(order.items.get().unit_price, Decimal("200.00"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
        self.assertEqual(self.client.session["cart"], {})

    def test_insufficient_stock_never_creates_partial_order(self):
        """A stock change before checkout keeps the cart but makes no order."""
        self.add_product(quantity=2)
        self.client.post(reverse("orders:cart_add", args=[self.other_product.pk]))
        Product.objects.filter(pk=self.product.pk).update(stock=1)
        response = self.client.post(reverse("orders:checkout"), self.checkout_data())
        self.assertRedirects(response, reverse("orders:cart"))
        self.assertEqual(Order.objects.count(), 0)
        self.other_product.refresh_from_db()
        self.assertEqual(self.other_product.stock, 2)

    def test_transaction_rolls_back_when_item_creation_fails(self):
        """If item creation fails after stock updates, nothing is charged or decremented."""
        self.add_product(quantity=1)
        with patch("orders.views.OrderItem.objects.create", side_effect=RuntimeError("test failure")):
            with self.assertRaises(RuntimeError):
                self.client.post(reverse("orders:checkout"), self.checkout_data())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(self.client.session["cart"][str(self.product.pk)], 1)

    def test_cancellation_restores_stock_and_reduces_total(self):
        """A placed item can be cancelled once with an exact stock refund."""
        self.add_product(quantity=2)
        self.client.post(reverse("orders:checkout"), self.checkout_data())
        item = OrderItem.objects.get()
        url = reverse("orders:cancel_item", args=[item.pk])
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.product.refresh_from_db()
        item.refresh_from_db()
        item.order.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(item.status, "cancelled")
        self.assertEqual(item.order.total, Decimal("0.00"))

    def test_order_and_invoice_hide_from_another_buyer(self):
        """An order number is not permission to view another buyer's details."""
        self.add_product()
        self.client.post(reverse("orders:checkout"), self.checkout_data())
        order = Order.objects.get()
        self.client.force_login(self.other_buyer)
        number = f"{order.pk:06d}"
        self.assertEqual(self.client.get(reverse("orders:order_detail", args=[number])).status_code, 404)
        self.assertEqual(self.client.get(reverse("orders:invoice", args=[number])).status_code, 404)

    def test_invoice_is_plain_text_attachment(self):
        """The buyer can download a readable VR-numbered invoice."""
        self.add_product()
        self.client.post(reverse("orders:checkout"), self.checkout_data())
        order = Order.objects.get()
        response = self.client.get(reverse("orders:invoice", args=[f"{order.pk:06d}"]))
        self.assertIn("text/plain", response["Content-Type"])
        self.assertIn("VR000001.txt", response["Content-Disposition"])

    def test_artisan_cannot_update_someone_elses_item(self):
        """Fulfillment status changes require owning the sold product."""
        self.add_product()
        self.client.post(reverse("orders:checkout"), self.checkout_data())
        item = OrderItem.objects.get()
        self.client.force_login(self.other_artisan)
        url = reverse("orders:item_status", args=[item.pk])
        self.assertEqual(self.client.post(url, {"status": "confirmed"}).status_code, 404)
        self.client.force_login(self.artisan)
        self.assertEqual(self.client.post(url, {"status": "shipped"}).status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.status, "placed")
        self.client.post(url, {"status": "confirmed"})
        item.refresh_from_db()
        self.assertEqual(item.status, "confirmed")

    def test_delivery_address_only_shows_to_the_selling_artisan(self):
        """Only the maker handling this item sees its buyer's address."""
        self.add_product()
        self.client.post(reverse("orders:checkout"), self.checkout_data())
        self.client.force_login(self.other_artisan)
        response = self.client.get(reverse("orders:artisan_orders"))
        self.assertNotContains(response, "10 Market Road")
        self.client.force_login(self.artisan)
        response = self.client.get(reverse("orders:artisan_orders"))
        self.assertContains(response, "10 Market Road")

    def test_artisan_fee_math(self):
        """The configured five percent fee leaves 95 percent for the maker."""
        self.add_product()
        self.client.post(reverse("orders:checkout"), self.checkout_data())
        item = OrderItem.objects.get()
        self.assertEqual(item.platform_fee(), Decimal("10.00"))
        self.assertEqual(item.artisan_amount(), Decimal("190.00"))
