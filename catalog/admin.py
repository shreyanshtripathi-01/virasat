"""Admin screens for crafts and product listings."""

from django.contrib import admin

from .models import Category, CraftTradition, Product, Review, Wishlist


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Maintain product categories."""

    list_display = ("name", "slug")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(CraftTradition)
class CraftTraditionAdmin(admin.ModelAdmin):
    """Maintain the heritage craft directory."""

    list_display = ("name", "state", "gi_tagged", "slug")
    list_filter = ("state", "gi_tagged")
    search_fields = ("name", "state", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Inspect and edit an artisan's product and catalog text."""

    list_display = ("title", "artisan", "category", "price", "stock", "status", "created_at")
    list_filter = ("status", "ai_source", "category", "craft", "created_at")
    search_fields = ("title", "materials", "tags", "artisan__username", "craft__name")
    date_hierarchy = "created_at"
    readonly_fields = ("view_count", "created_at", "updated_at")
    list_select_related = ("artisan", "category", "craft")
    fieldsets = (
        ("Product", {"fields": ("artisan", "category", "craft", "title", "image", "price", "stock", "status")}),
        ("Artisan notes", {"fields": ("raw_notes", "materials", "technique")}),
        ("Catalog text", {"fields": ("description", "hindi_description", "heritage_story", "care_instructions", "tags")}),
        ("Catalog source", {"fields": ("ai_source", "ai_edited")}),
        ("Activity", {"fields": ("view_count", "created_at", "updated_at")}),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Find buyer reviews by rating, product or buyer."""

    list_display = ("product", "buyer", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("product__title", "buyer__username", "comment")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
    list_select_related = ("product", "buyer")


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """Inspect saved products without editing their creation dates."""

    list_display = ("user", "product", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "product__title")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
    list_select_related = ("user", "product")
