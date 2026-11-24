"""Buyer delivery and demo payment fields."""

from django import forms

from accounts.forms import style_fields
from .models import Order


class CheckoutForm(forms.ModelForm):
    """Collect validated delivery details for one order."""

    class Meta:
        model = Order
        fields = (
            "full_name", "phone", "address", "city", "state", "pincode", "payment_method",
        )
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "payment_method": forms.RadioSelect(),
        }
        help_texts = {
            "phone": "10-digit mobile number.",
            "pincode": "6 digits.",
        }

    def __init__(self, *args, **kwargs):
        """Style the checkout fields for clear phone-friendly entry."""
        super().__init__(*args, **kwargs)
        style_fields(self)
