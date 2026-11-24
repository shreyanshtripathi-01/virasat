"""Admin screens for buyer requests and artisan proposals."""

from django.contrib import admin

from .models import BuyerRequest, Proposal


@admin.register(BuyerRequest)
class BuyerRequestAdmin(admin.ModelAdmin):
    """Browse buyers' craft requests by status and category."""

    list_display = ("title", "buyer", "category", "quantity", "status", "needed_by", "created_at")
    list_filter = ("status", "category", "craft", "needed_by")
    search_fields = ("title", "buyer__username", "description", "preferred_state")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
    list_select_related = ("buyer", "category", "craft")


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    """Find artisan offers by request and response status."""

    list_display = ("request", "artisan", "price_per_unit", "delivery_days", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("request__title", "artisan__username", "message")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
    list_select_related = ("request", "artisan")
