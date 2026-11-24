"""Simple forms for signing in and updating a Virasat profile."""

from pathlib import Path

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from .models import Profile, phone_validator


def style_fields(form):
    """Give ordinary Django form fields consistent styles and error links."""
    for name, field in form.fields.items():
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs["class"] = "form-check-input"
        elif isinstance(field.widget, forms.RadioSelect):
            field.widget.attrs["class"] = "btn-check role-radio-input"
        elif isinstance(field.widget, forms.Select):
            field.widget.attrs["class"] = "form-select"
        else:
            field.widget.attrs["class"] = "form-control"
        described_by = [f"id_{name}_error"]
        if field.help_text:
            described_by.insert(0, f"id_{name}_helptext")
        if name == "password1":
            described_by.append("password-tips")
        field.widget.attrs["aria-describedby"] = " ".join(described_by)


class RegisterForm(UserCreationForm):
    """Collect the minimum details needed to join as an artisan or buyer."""

    role = forms.ChoiceField(
        choices=[("artisan", "Artisan"), ("buyer", "Buyer")],
        label="I am a",
        widget=forms.RadioSelect(attrs={"class": "role-radio-input"}),
    )
    phone = forms.CharField(
        max_length=10,
        validators=[phone_validator],
        help_text="10 digits, starting 6 to 9.",
    )
    state = forms.CharField(max_length=100)
    city = forms.CharField(max_length=100)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "password1", "password2", "role", "phone", "state", "city")

    def __init__(self, *args, **kwargs):
        """Apply shared styles and keep long username and password rules out of the form."""
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = ""
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""
        self.fields["username"].widget.attrs.setdefault("autofocus", "autofocus")
        style_fields(self)


class LoginForm(AuthenticationForm):
    """Check credentials and offer a two-week sign-in on this device."""

    remember_me = forms.BooleanField(required=False, label="Keep me signed in")

    def __init__(self, *args, **kwargs):
        """Style the fields without repeating obvious sign-in help."""
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.setdefault("autofocus", "autofocus")
        style_fields(self)


class ProfileForm(forms.ModelForm):
    """Edit contact details and an optional artisan photo."""

    class Meta:
        model = Profile
        fields = (
            "phone", "state", "city", "preferred_language", "bio",
            "craft_speciality", "years_of_experience", "avatar",
        )
        widgets = {"bio": forms.Textarea(attrs={"rows": 3})}
        help_texts = {
            "phone": "10 digits, starting 6 to 9.",
            "avatar": "JPG, PNG or WebP, up to 2 MB.",
        }

    def __init__(self, *args, **kwargs):
        """Hide artisan-only details from buyer and verifier profiles."""
        super().__init__(*args, **kwargs)
        if self.instance.role != "artisan":
            self.fields.pop("craft_speciality")
            self.fields.pop("years_of_experience")
        style_fields(self)

    def clean_avatar(self):
        """Accept only small, valid JPG, PNG or WebP uploads."""
        # Syllabus: Unit IV - validate an uploaded form field on the server.
        avatar = self.cleaned_data.get("avatar")
        if not avatar or not isinstance(avatar, UploadedFile):
            return avatar
        extension = Path(avatar.name).suffix.lower()
        if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise ValidationError("Choose a JPG, PNG or WebP image.")
        if avatar.size > 2 * 1024 * 1024:
            raise ValidationError("Choose an image smaller than 2 MB.")
        if avatar.image.format not in {"JPEG", "PNG", "WEBP"}:
            raise ValidationError("Choose a valid JPG, PNG or WebP image.")
        return avatar
