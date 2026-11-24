"""Buyer request and artisan proposal forms."""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.forms import style_fields
from .models import BuyerRequest, Proposal


class BuyerRequestForm(forms.ModelForm):
    """Ask for a handmade item with a sensible date and budget."""

    class Meta:
        model = BuyerRequest
        fields = (
            "title", "description", "category", "craft", "quantity",
            "budget_min", "budget_max", "needed_by", "preferred_state",
        )
        widgets = {
            "description": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "For a wedding, 30 cotton pouches in indigo block print.",
            }),
            "needed_by": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        """Use clear phone-friendly controls."""
        super().__init__(*args, **kwargs)
        self.fields["needed_by"].input_formats = ["%Y-%m-%d"]
        style_fields(self)

    def clean_needed_by(self):
        """Reject delivery dates that have already passed or are today."""
        day = self.cleaned_data["needed_by"]
        if day <= timezone.localdate():
            raise ValidationError("Choose a date after today.")
        return day

    def clean(self):
        """Keep the minimum budget no higher than the maximum."""
        cleaned = super().clean()
        minimum = cleaned.get("budget_min")
        maximum = cleaned.get("budget_max")
        if minimum is not None and maximum is not None and minimum > maximum:
            self.add_error("budget_max", "The maximum must be at least the minimum.")
        return cleaned


class ProposalForm(forms.ModelForm):
    """Let one artisan quote a price, days and a short message."""

    class Meta:
        model = Proposal
        fields = ("price_per_unit", "delivery_days", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        """Keep the quote fields easy to read and tap."""
        super().__init__(*args, **kwargs)
        style_fields(self)
