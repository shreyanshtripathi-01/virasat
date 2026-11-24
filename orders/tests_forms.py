"""Checkout form validation and order method tests."""

from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from catalog.models import Category, CraftTradition, Product
from .forms import CheckoutForm
from .models import Order, OrderItem


class CheckoutAndOrderTests(TestCase):
    """Check delivery validators and saved-price arithmetic."""

    def test_checkout_rejects_invalid_phone_and_pincode(self):
        """Contact and delivery validators reject malformed Indian numbers."""
        form = CheckoutForm({
            "full_name": "Buyer", "phone": "1234567890", "address": "1 Market Road",
            "city": "Patna", "state": "Bihar", "pincode": "000001",
            "payment_method": "cod",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)
        self.assertIn("pincode", form.errors)

    def test_order_number_fee_rounding_and_overall_status(self):
        """Small-price fees round fairly and item states determine order state."""
        buyer = User.objects.create_user("buyer", password="ExamplePass2026!")
        artisan = User.objects.create_user("maker", password="ExamplePass2026!")
        category = Category.objects.create(name="Art", slug="art")
        craft = CraftTradition.objects.create(
            name="Madhubani", slug="madhubani", state="Bihar", description="Painting."
        )
        product = Product.objects.create(
            artisan=artisan, category=category, craft=craft, title="Small print",
            raw_notes="Painted on paper by hand.", materials="paper", technique="painting",
            description="A small print.", price="0.10", stock=2,
            image="products/test.jpg", status="published",
        )
        order = Order.objects.create(
            buyer=buyer, full_name="Buyer", phone="9876543210", address="1 Market Road",
            city="Patna", state="Bihar", pincode="800001", payment_method="cod", total="0.20",
        )
        first = OrderItem.objects.create(
            order=order, product=product, quantity=1, unit_price=Decimal("0.10"), status="delivered"
        )
        second = OrderItem.objects.create(
            order=order, product=product, quantity=1, unit_price=Decimal("0.10"), status="placed"
        )
        self.assertEqual(order.order_number, "VR000001")
        self.assertEqual(first.line_total(), Decimal("0.10"))
        self.assertEqual(first.platform_fee(), Decimal("0.01"))
        self.assertEqual(first.artisan_amount(), Decimal("0.09"))
        self.assertEqual(order.overall_status, "placed")
        second.status = "cancelled"
        second.save(update_fields=["status"])
        self.assertEqual(order.overall_status, "delivered")
