"""Function-based views for registration, profiles and verification."""

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST

from catalog.models import CraftTradition
from .forms import LoginForm, ProfileForm, RegisterForm
from .models import Profile


logger = logging.getLogger(__name__)


def is_artisan_or_forbidden(user):
    """Allow an artisan, or raise a 403 error for another signed-in user."""
    if not Profile.objects.filter(user=user, role="artisan").exists():
        raise PermissionDenied("This page is for artisans.")
    return True


def is_buyer_or_forbidden(user):
    """Allow a buyer, or raise a 403 error for another signed-in user."""
    if not Profile.objects.filter(user=user, role="buyer").exists():
        raise PermissionDenied("This page is for buyers.")
    return True


def artisan_required(view_function):
    """Redirect visitors to login and show a 403 to non-artisans."""
    # Syllabus: Unit VI - use login_required and user_passes_test for roles.
    return login_required(user_passes_test(is_artisan_or_forbidden)(view_function))


def buyer_required(view_function):
    """Redirect visitors to login and show a 403 to non-buyers."""
    return login_required(user_passes_test(is_buyer_or_forbidden)(view_function))


def safe_next_url(request):
    """Return a local redirect target, or the home page for unsafe links."""
    destination = request.POST.get("next") or request.GET.get("next", "")
    if url_has_allowed_host_and_scheme(
        destination, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return destination
    return "/"


@transaction.atomic
def register(request):
    """Create an artisan or buyer with a profile and sign them in."""
    if request.user.is_authenticated:
        return redirect("/")
    form = RegisterForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        # Syllabus: Unit V - save related objects and join a user group.
        user = form.save()
        Profile.objects.create(
            user=user,
            role=form.cleaned_data["role"],
            phone=form.cleaned_data["phone"],
            state=form.cleaned_data["state"],
            city=form.cleaned_data["city"],
        )
        group, _ = Group.objects.get_or_create(name=form.cleaned_data["role"].title())
        user.groups.add(group)
        login(request, user)
        messages.success(request, "Welcome to Virasat!")
        return redirect("/")
    return render(request, "accounts/register.html", {
        "form": form, "auth_crafts": CraftTradition.objects.exclude(image="").order_by("name")[:3],
    })


def login_view(request):
    """Sign in and honour a safe local next URL."""
    if request.user.is_authenticated:
        return redirect(safe_next_url(request))
    form = LoginForm(request, data=request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        # Syllabus: Unit VI - authenticate, login and set session expiry.
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user is not None:
            login(request, user)
            expiry = settings.SESSION_COOKIE_AGE if form.cleaned_data["remember_me"] else 0
            request.session.set_expiry(expiry)
            messages.success(request, "You are signed in.")
            return redirect(safe_next_url(request))
    if request.method == "POST":
        username = request.POST.get("username", "")
        clean_username = "".join(character for character in username if character.isalnum() or character in "._-")[:50]
        logger.info("Failed sign-in for username %s", clean_username)
    return render(request, "accounts/login.html", {
        "form": form, "next": safe_next_url(request),
        "auth_crafts": CraftTradition.objects.exclude(image="").order_by("name")[:3],
    })


@require_POST
def logout_view(request):
    """Sign out only after a CSRF-protected POST request."""
    logout(request)
    messages.success(request, "You are signed out.")
    return redirect("accounts:login")


@login_required
@require_GET
def profile(request):
    """Show the signed-in user's own profile."""
    user_profile = get_object_or_404(Profile, user=request.user)
    return render(request, "accounts/profile.html", {"profile": user_profile})


@login_required
def edit_profile(request):
    """Save contact or artisan details and redirect back to the profile."""
    user_profile = get_object_or_404(Profile, user=request.user)
    form = ProfileForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        instance=user_profile,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile_edit.html", {"form": form})


@require_GET
def artisan_detail(request, pk):
    """Show an artisan's public profile and published products."""
    artisan = get_object_or_404(
        User.objects.select_related("profile"), pk=pk, profile__role="artisan"
    )
    products = artisan.products.filter(status="published").select_related("craft", "category")
    return render(request, "accounts/artisan_detail.html", {
        "artisan": artisan, "products": products
    })


@login_required
@permission_required("accounts.can_verify_artisan", raise_exception=True)
@require_GET
def verification_queue(request):
    """List pending artisans for a user with verification permission."""
    # Syllabus: Unit V - check a group permission before querying the queue.
    artisans = Profile.objects.filter(
        role="artisan", verification_status="pending", is_verified=False
    ).select_related("user").order_by("created_at")
    return render(request, "accounts/verification_queue.html", {"artisans": artisans})


@login_required
@permission_required("accounts.can_verify_artisan", raise_exception=True)
@require_POST
def approve_artisan(request, pk):
    """Approve a pending artisan and record the verifier and time."""
    artisan = get_object_or_404(
        Profile, pk=pk, role="artisan", verification_status="pending", is_verified=False
    )
    artisan.is_verified = True
    artisan.verification_status = "approved"
    artisan.verified_by = request.user
    artisan.verified_at = timezone.now()
    artisan.save(update_fields=[
        "is_verified", "verification_status", "verified_by", "verified_at"
    ])
    messages.success(request, "Artisan approved.")
    return redirect("accounts:verification_queue")


@login_required
@permission_required("accounts.can_verify_artisan", raise_exception=True)
@require_POST
def reject_artisan(request, pk):
    """Mark a pending artisan rejected without disabling their account."""
    artisan = get_object_or_404(
        Profile, pk=pk, role="artisan", verification_status="pending", is_verified=False
    )
    artisan.verification_status = "rejected"
    artisan.save(update_fields=["verification_status"])
    messages.info(request, "Artisan not approved. Their account stays active.")
    return redirect("accounts:verification_queue")
