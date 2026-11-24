"""Admin screens for user profiles and verification."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Profile


class ProfileInline(admin.StackedInline):
    """Show the marketplace profile next to its Django user."""

    model = Profile
    fk_name = "user"
    can_delete = False
    extra = 0
    max_num = 1
    readonly_fields = ("is_verified", "verification_status", "verified_by", "verified_at")


# Syllabus: Unit V - extend Django Admin and its built-in User screen.
admin.site.unregister(User)


@admin.register(User)
class VirasatUserAdmin(UserAdmin):
    """Keep Django's user tools and add the related profile inline."""

    inlines = [ProfileInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Find and verify artisan profiles in the admin."""

    list_display = (
        "user", "role", "city", "state", "verification_status", "is_verified", "created_at"
    )
    list_filter = ("role", "verification_status", "is_verified", "state", "created_at")
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone", "city")
    date_hierarchy = "created_at"
    readonly_fields = (
        "created_at", "is_verified", "verification_status", "verified_by", "verified_at"
    )
    list_select_related = ("user",)
    actions = ["mark_artisans_verified"]

    @admin.action(description="Mark selected artisans as verified")
    def mark_artisans_verified(self, request, queryset):
        """Verify only selected artisan profiles and record who did it."""
        count = queryset.filter(role="artisan", verification_status="pending").update(
            is_verified=True,
            verification_status="approved",
            verified_by=request.user,
            verified_at=timezone.now(),
        )
        self.message_user(request, f"Verified {count} artisan profile(s).")


admin.site.site_header = "Virasat Administration"
