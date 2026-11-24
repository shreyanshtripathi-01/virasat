"""Admin screens for buyer orders and their purchased items."""

from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Show the purchased products on their parent order."""

    model = OrderItem
    extra = 0
    readonly_fields = ("updated_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Find orders by buyer, date, delivery address and payment method."""

    list_display = ("order_number", "buyer", "full_name", "total", "payment_method", "created_at")
    list_filter = ("payment_method", "state", "created_at")
    search_fields = ("buyer__username", "full_name", "phone", "city", "pincode")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
    list_select_related = ("buyer",)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Inspect order-item delivery states and purchase prices."""

    list_display = ("order", "product", "quantity", "unit_price", "status", "updated_at")
    list_filter = ("status", "updated_at")
    search_fields = ("order__buyer__username", "product__title")
    date_hierarchy = "updated_at"
    readonly_fields = ("updated_at",)
    list_select_related = ("order", "product")
