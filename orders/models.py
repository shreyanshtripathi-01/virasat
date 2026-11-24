"""Buyer orders and individual items sold by artisans."""

from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from accounts.models import phone_validator
from catalog.models import Product


pincode_validator = RegexValidator(
    regex=r"^[1-9][0-9]{5}$", message="Enter a valid six-digit Indian pincode."
)


class Order(models.Model):
    """Save a buyer's delivery details and total at checkout."""

    PAYMENT_CHOICES = [("cod", "Cash on delivery"), ("upi_demo", "UPI (demo)")]

    buyer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=10, validators=[phone_validator])
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6, validators=[pincode_validator])
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    total = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self):
        """Show the readable order number."""
        return self.order_number

    @property
    def order_number(self):
        """Return the order number with the Virasat prefix."""
        return f"VR{self.pk:06d}"

    @property
    def overall_status(self):
        """Show the earliest unfinished stage among active order items."""
        # Syllabus: Unit V - read related order items using the ORM.
        statuses = list(self.items.values_list("status", flat=True))
        active_statuses = [status for status in statuses if status != "cancelled"]
        if not active_statuses:
            return "cancelled" if statuses else "placed"
        for stage in ["placed", "confirmed", "shipped", "delivered"]:
            if stage in active_statuses:
                return stage
        return "placed"


class OrderItem(models.Model):
    """Record a purchased product, its original price and delivery stage."""

    STATUS_CHOICES = [
        ("placed", "Placed"),
        ("confirmed", "Confirmed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="placed")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order item"
        verbose_name_plural = "Order items"
        ordering = ["order_id", "pk"]
        indexes = [models.Index(fields=["product", "status"], name="item_product_status_idx")]

    def __str__(self):
        """Show the product and the order it belongs to."""
        return f"{self.product.title} in {self.order.order_number}"

    def line_total(self):
        """Multiply the price at checkout by the quantity purchased."""
        return self.unit_price * self.quantity

    def platform_fee(self):
        """Calculate the platform's share rounded to two decimal places."""
        percentage = settings.PLATFORM_FEE_PERCENT / Decimal("100")
        return (self.line_total() * percentage).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def artisan_amount(self):
        """Calculate the artisan's earnings after the platform fee."""
        return self.line_total() - self.platform_fee()
