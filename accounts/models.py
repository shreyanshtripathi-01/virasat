"""User profiles and contact details for the marketplace."""

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models


phone_validator = RegexValidator(
    regex=r"^[6-9][0-9]{9}$",
    message="Enter a 10-digit Indian mobile number starting with 6, 7, 8 or 9.",
)


class Profile(models.Model):
    """Store a user's role and public artisan information."""

    ROLE_CHOICES = [
        ("artisan", "Artisan"),
        ("buyer", "Buyer"),
        ("verifier", "Verifier"),
    ]
    LANGUAGE_CHOICES = [("en", "English"), ("hi", "Hindi")]
    VERIFICATION_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    # Syllabus: Unit V - one-to-one and foreign-key relationships.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=10, validators=[phone_validator])
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    preferred_language = models.CharField(
        max_length=2, choices=LANGUAGE_CHOICES, default="en"
    )
    bio = models.TextField(blank=True)
    craft_speciality = models.CharField(max_length=150, blank=True)
    years_of_experience = models.PositiveSmallIntegerField(null=True, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    is_verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=10, choices=VERIFICATION_CHOICES, default="pending"
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_profiles",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        ordering = ["-created_at"]
        permissions = [("can_verify_artisan", "Can verify artisan profiles")]

    def __str__(self):
        """Identify the profile by its username and role."""
        return f"{self.user.username} ({self.get_role_display()})"

    def is_artisan(self):
        """Return whether this user has the artisan role."""
        return self.role == "artisan"

    def is_buyer(self):
        """Return whether this user has the buyer role."""
        return self.role == "buyer"
