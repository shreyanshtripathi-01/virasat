"""Buyer craft requests and the artisans' proposals."""

from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from catalog.models import Category, CraftTradition


class BuyerRequest(models.Model):
    """Describe a handmade item a buyer would like an artisan to make."""

    STATUS_CHOICES = [("open", "Open"), ("closed", "Closed")]

    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="buyer_requests"
    )
    title = models.CharField(max_length=160)
    description = models.TextField()
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="buyer_requests"
    )
    craft = models.ForeignKey(
        CraftTradition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="buyer_requests",
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    budget_min = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    budget_max = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    needed_by = models.DateField()
    preferred_state = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Buyer request"
        verbose_name_plural = "Buyer requests"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"], name="request_status_date_idx")]

    def __str__(self):
        """Show the request title."""
        return self.title


class Proposal(models.Model):
    """Record an artisan's offer for a buyer request."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    request = models.ForeignKey(
        BuyerRequest, on_delete=models.CASCADE, related_name="proposals"
    )
    artisan = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="proposals"
    )
    message = models.TextField()
    price_per_unit = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    delivery_days = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(90)]
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proposal"
        verbose_name_plural = "Proposals"
        ordering = ["-created_at"]
        unique_together = [("request", "artisan")]

    def __str__(self):
        """Show which artisan made this offer for which request."""
        return f"{self.artisan.username}: {self.request.title}"
