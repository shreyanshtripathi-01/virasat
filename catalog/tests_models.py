"""Model behaviour, form validation and regex URL tests."""

from io import BytesIO

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import resolve, reverse
from PIL import Image

from accounts.models import Profile
from orders.models import Order, OrderItem
from .forms import ProductRawForm
from .models import Category, CraftTradition, Product, Review, Wishlist


class ModelAndFormTests(TestCase):
    """Keep the catalog's constraints and important calculations reliable."""

    @classmethod
    def setUpTestData(cls):
        """Create one artisan, one buyer and a real published catalog record."""
        cls.artisan = User.objects.create_user("maker", password="ExamplePass2026!")
        cls.buyer = User.objects.create_user("buyer", password="ExamplePass2026!")
        Profile.objects.create(
            user=cls.artisan, role="artisan", phone="9876543210",
            city="Patna", state="Bihar",
        )
        cls.category = Category.objects.create(name="Paintings", slug="paintings")
        cls.craft = CraftTradition.objects.create(
            name="Madhubani", slug="madhubani", state="Bihar", description="Folk painting."
        )
        cls.product = Product.objects.create(
            artisan=cls.artisan, category=cls.category, craft=cls.craft,
            title="Lotus painting", raw_notes="Flowers painted on cotton paper.",
            materials="paper", technique="hand painting", description="A painted lotus.",
            price="100.00", stock=2, image="products/test.jpg", status="published",
        )

    def test_model_names_rating_stock_and_url(self):
        """Model display helpers return truthful, readable values."""
        self.assertEqual(str(self.category), "Paintings")
        self.assertEqual(str(self.craft), "Madhubani (Bihar)")
        self.assertEqual(str(self.product), "Lotus painting")
        self.assertEqual(str(self.artisan.profile), "maker (Artisan)")
        self.assertTrue(self.product.in_stock())
        self.assertEqual(self.product.average_rating(), 0)
        Review.objects.create(product=self.product, buyer=self.buyer, rating=5)
        self.assertEqual(self.product.average_rating(), 5.0)
        self.assertEqual(self.product.get_absolute_url(), f"/product/{self.product.pk}/lotus-painting/")

    def test_wishlist_and_review_database_uniqueness(self):
        """The database stops duplicate buyer-product entries."""
        Wishlist.objects.create(user=self.buyer, product=self.product)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Wishlist.objects.create(user=self.buyer, product=self.product)
        Review.objects.create(product=self.product, buyer=self.buyer, rating=4)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(product=self.product, buyer=self.buyer, rating=5)

    def test_price_and_stock_model_validators(self):
        """A listed product cannot be free or have negative stock."""
        self.product.price = 0
        self.product.stock = -1
        with self.assertRaises(ValidationError) as caught:
            self.product.full_clean()
        self.assertIn("price", caught.exception.message_dict)
        self.assertIn("stock", caught.exception.message_dict)

    def test_product_image_extension_and_size(self):
        """A valid image with an unsupported extension or excess size fails."""
        output = BytesIO()
        Image.new("RGB", (8, 8), "white").save(output, format="PNG")
        data = {
            "category": self.category.pk, "craft": self.craft.pk,
            "materials": "paper", "technique": "painting",
            "notes": "Flowers painted on cotton paper.",
            "price": "100.00", "stock": "2",
        }
        bad_extension = SimpleUploadedFile("picture.gif", output.getvalue(), content_type="image/png")
        form = ProductRawForm(data, files={"image": bad_extension})
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)
        large = SimpleUploadedFile(
            "picture.png", output.getvalue() + b"0" * (5 * 1024 * 1024),
            content_type="image/png",
        )
        form = ProductRawForm(data, files={"image": large})
        self.assertFalse(form.is_valid())
        self.assertIn("smaller than 5 MB", str(form.errors["image"]))

    def test_regex_routes_reverse_and_resolve(self):
        """Product and VR invoice paths resolve to their app namespaces."""
        product_path = reverse("catalog:product_detail", args=[self.product.pk, "lotus-painting"])
        order_path = reverse("orders:order_detail", args=["000123"])
        invoice_path = reverse("orders:invoice", args=["000123"])
        self.assertEqual(resolve(product_path).view_name, "catalog:product_detail")
        self.assertEqual(resolve(order_path).view_name, "orders:order_detail")
        self.assertEqual(resolve(invoice_path).view_name, "orders:invoice")
        self.assertEqual(resolve("/language/hi/").view_name, "core:language")
