"""GET filters and a short buyer review form."""

from decimal import Decimal
from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from accounts.forms import style_fields
from .models import Category, CraftTradition, Product, Review


def validate_product_image(image):
    """Accept a real JPG, PNG or WebP image no larger than five megabytes."""
    if not image or not isinstance(image, UploadedFile):
        return image
    if image.size > 5 * 1024 * 1024:
        raise ValidationError("Choose an image smaller than 5 MB.")
    if Path(image.name).suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValidationError("Choose a JPG, PNG or WebP image.")
    if image.image.format not in {"JPEG", "PNG", "WEBP"}:
        raise ValidationError("Choose a valid JPG, PNG or WebP image.")
    return image


def check_written_fields(form, names):
    """Reject titles or notes that have no letters at all."""
    for name in names:
        value = form.cleaned_data.get(name, "")
        if value and not any(character.isalpha() for character in value):
            form.add_error(name, "Please use words to describe your work.")


class ProductRawForm(forms.Form):
    """Collect a maker's simple notes before drafting catalog text."""

    craft = forms.ModelChoiceField(CraftTradition.objects.all())
    category = forms.ModelChoiceField(Category.objects.all())
    title_hint = forms.CharField(
        required=False, min_length=4, max_length=160, label="Name your piece",
        widget=forms.TextInput(attrs={"placeholder": "Indigo cotton table runner"}),
    )
    materials = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Hand spun cotton and natural indigo"}),
    )
    technique = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Hand-block printed with natural indigo dye"}),
    )
    notes = forms.CharField(
        min_length=15, widget=forms.Textarea(attrs={"rows": 4, "placeholder": "I printed this cotton runner by hand. It has small flower motifs and a stitched border."}),
        help_text="15 characters or more.",
    )
    price = forms.DecimalField(
        min_value=Decimal("0.01"), max_digits=10, decimal_places=2, label="Price (₹)"
    )
    stock = forms.IntegerField(min_value=0)
    image = forms.ImageField(help_text="JPG, PNG or WebP, up to 5 MB.")

    def __init__(self, *args, **kwargs):
        """Make the simple notes form easy to use on a phone."""
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_image(self):
        """Validate the image extension, format and file size."""
        return validate_product_image(self.cleaned_data.get("image"))

    def clean(self):
        """Make sure a proposed title and the notes contain words."""
        cleaned = super().clean()
        check_written_fields(self, ("title_hint", "notes"))
        return cleaned


class ProductForm(forms.ModelForm):
    """Let the artisan review and edit every generated catalog field."""

    title = forms.CharField(min_length=4, max_length=160)

    class Meta:
        model = Product
        fields = (
            "category", "craft", "title", "raw_notes", "materials", "technique",
            "description", "hindi_description", "heritage_story", "care_instructions",
            "tags", "price", "stock", "image",
        )
        widgets = {
            "raw_notes": forms.Textarea(attrs={"rows": 3}),
            "description": forms.Textarea(attrs={"rows": 5}),
            "hindi_description": forms.Textarea(attrs={"rows": 5}),
            "heritage_story": forms.Textarea(attrs={"rows": 3}),
            "care_instructions": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "raw_notes": "15 characters or more.",
            "heritage_story": "Use only facts you know about your craft.",
            "stock": "Zero means sold out.",
            "image": "JPG, PNG or WebP, up to 5 MB.",
        }

    def __init__(self, *args, **kwargs):
        """Style the editable catalog fields."""
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_raw_notes(self):
        """Require enough notes for a helpful generated description."""
        notes = self.cleaned_data["raw_notes"].strip()
        if len(notes) < 15:
            raise ValidationError("Write at least 15 characters about your work.")
        return notes

    def clean_image(self):
        """Validate new uploads without rejecting an existing saved image."""
        return validate_product_image(self.cleaned_data.get("image"))

    def clean(self):
        """Reject a title or notes that contain only numbers or symbols."""
        cleaned = super().clean()
        check_written_fields(self, ("title", "raw_notes"))
        return cleaned


class ProductFilterForm(forms.Form):
    """Filter published listings using ordinary GET query parameters."""

    SORT_CHOICES = [
        ("newest", "Newest"), ("price_asc", "Price: low to high"),
        ("price_desc", "Price: high to low"), ("rated", "Top rated"),
    ]
    q = forms.CharField(
        required=False, max_length=100, label="Search",
        widget=forms.TextInput(attrs={"placeholder": "Craft, item or material"}),
    )
    category = forms.ModelChoiceField(
        Category.objects.all(), required=False, empty_label="All categories"
    )
    craft = forms.ModelChoiceField(
        CraftTradition.objects.all(), required=False, empty_label="All crafts"
    )
    state = forms.ChoiceField(required=False)
    min_price = forms.DecimalField(
        required=False, min_value=0, decimal_places=2, label="From ₹"
    )
    max_price = forms.DecimalField(
        required=False, min_value=0, decimal_places=2, label="To ₹"
    )
    verified_only = forms.BooleanField(required=False, label="Verified artisans only")
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        """Build state options from real traditions and style the inputs."""
        super().__init__(*args, **kwargs)
        states = CraftTradition.objects.order_by("state").values_list("state", flat=True).distinct()
        self.fields["state"].choices = [("", "All states")] + [(state, state) for state in states]
        style_fields(self)

    def clean(self):
        """Keep the upper price at or above the lower price."""
        cleaned = super().clean()
        minimum = cleaned.get("min_price")
        maximum = cleaned.get("max_price")
        if minimum is not None and maximum is not None and minimum > maximum:
            self.add_error("max_price", "Choose a price above the minimum.")
        return cleaned


class ReviewForm(forms.ModelForm):
    """Collect a buyer's rating and optional comment."""

    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "rating": forms.Select(choices=[(number, str(number)) for number in range(1, 6)]),
            "comment": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        """Style rating and comment like the other site forms."""
        super().__init__(*args, **kwargs)
        style_fields(self)
