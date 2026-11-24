"""Craft traditions, products, reviews and wishlists."""

from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    """Group products by the kind of item they are."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        """Show the category name."""
        return self.name


class CraftTradition(models.Model):
    """Describe a traditional craft and the state it comes from."""

    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(unique=True)
    state = models.CharField(max_length=100)
    description = models.TextField()
    gi_tagged = models.BooleanField(default=False, verbose_name="GI tagged")
    image = models.ImageField(upload_to="crafts/", blank=True)

    class Meta:
        verbose_name = "Craft tradition"
        verbose_name_plural = "Craft traditions"
        ordering = ["name"]

    def __str__(self):
        """Show the craft name and its state."""
        return f"{self.name} ({self.state})"


class Product(models.Model):
    """Store an artisan's listing and its editable catalog description."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]
    AI_SOURCE_CHOICES = [
        ("ai", "AI"),
        ("fallback", "Offline fallback"),
        ("manual", "Manual"),
    ]

    # Syllabus: Unit V - foreign keys connect each listing to its owner and craft.
    artisan = models.ForeignKey(User, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    craft = models.ForeignKey(
        CraftTradition, on_delete=models.PROTECT, related_name="products"
    )
    title = models.CharField(max_length=160)
    raw_notes = models.TextField()
    materials = models.CharField(max_length=255)
    technique = models.CharField(max_length=255)
    description = models.TextField()
    hindi_description = models.TextField(blank=True)
    heritage_story = models.TextField(blank=True)
    care_instructions = models.TextField(blank=True)
    tags = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    stock = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to="products/")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    ai_source = models.CharField(max_length=10, choices=AI_SOURCE_CHOICES, default="manual")
    ai_edited = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"], name="product_status_date_idx"),
            models.Index(fields=["artisan", "status"], name="product_owner_status_idx"),
        ]

    def __str__(self):
        """Show the product title."""
        return self.title

    def get_absolute_url(self):
        """Build the detail URL using the product number and its title slug."""
        return reverse(
            "catalog:product_detail",
            kwargs={"pk": self.pk, "slug": slugify(self.title)},
        )

    def average_rating(self):
        """Return the average review score, or zero without reviews."""
        # Syllabus: Unit V - aggregate a related set of reviews with the ORM.
        result = self.reviews.aggregate(average=Avg("rating"))
        return result["average"] or 0

    def in_stock(self):
        """Return whether at least one item is available."""
        return self.stock > 0


class Review(models.Model):
    """Keep one buyer rating per product."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ["-created_at"]
        unique_together = [("product", "buyer")]

    def __str__(self):
        """Show the product and rating for this review."""
        return f"{self.product.title}: {self.rating}/5"


class Wishlist(models.Model):
    """Remember a product a user wants to find again."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="wishlist_entries"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="wishlist_entries"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Wishlist entry"
        verbose_name_plural = "Wishlist entries"
        ordering = ["-created_at"]
        unique_together = [("user", "product")]

    def __str__(self):
        """Show who saved which product."""
        return f"{self.user.username}: {self.product.title}"
