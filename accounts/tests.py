"""Focused tests for registration, roles and the verification queue."""

from io import BytesIO

from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from PIL import Image

from catalog.models import Category, CraftTradition, Product

from .forms import ProfileForm, RegisterForm
from .models import Profile
from .views import artisan_required, buyer_required


def protected_page(request):
    """Return a small response when a role decorator admits a user."""
    return HttpResponse("Allowed")


class AccountTests(TestCase):
    """Check the real account pages and their role boundaries."""

    @classmethod
    def setUpTestData(cls):
        """Create one account for each role and grant verification access."""
        cls.artisan = User.objects.create_user("maker", password="ExamplePass2026!")
        cls.buyer = User.objects.create_user("shopper", password="ExamplePass2026!")
        cls.verifier = User.objects.create_user("checker", password="ExamplePass2026!")
        cls.artisan_profile = Profile.objects.create(
            user=cls.artisan, role="artisan", phone="9876543210",
            state="Bihar", city="Patna",
        )
        Profile.objects.create(
            user=cls.buyer, role="buyer", phone="9876543211",
            state="Delhi", city="Delhi",
        )
        Profile.objects.create(
            user=cls.verifier, role="verifier", phone="9876543212",
            state="Delhi", city="Delhi",
        )
        verifier_group = Group.objects.create(name="Verifier")
        verifier_group.permissions.add(Permission.objects.get(codename="can_verify_artisan"))
        cls.verifier.groups.add(verifier_group)

    def test_registration_creates_buyer_profile_and_group(self):
        """A valid POST saves a buyer and redirects after login."""
        response = self.client.post(reverse("accounts:register"), {
            "username": "newbuyer", "password1": "AnotherPass2026!",
            "password2": "AnotherPass2026!", "role": "buyer",
            "phone": "9876543213", "state": "Goa", "city": "Panaji",
        })
        self.assertRedirects(response, "/")
        new_user = User.objects.get(username="newbuyer")
        self.assertTrue(new_user.profile.is_buyer())
        self.assertTrue(new_user.groups.filter(name="Buyer").exists())
        self.assertEqual(int(self.client.session["_auth_user_id"]), new_user.pk)

    def test_registration_rejects_verifier_and_invalid_phone(self):
        """Visitors cannot choose the verifier role or an invalid phone."""
        data = {
            "username": "unexpected", "password1": "AnotherPass2026!",
            "password2": "AnotherPass2026!", "role": "verifier",
            "phone": "1234567890", "state": "Goa", "city": "Panaji",
        }
        form = RegisterForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("role", form.errors)
        self.assertIn("phone", form.errors)

    def test_registration_creates_pending_artisan(self):
        """A new artisan starts unverified in the Artisan group."""
        response = self.client.post(reverse("accounts:register"), {
            "username": "newmaker", "password1": "AnotherPass2026!",
            "password2": "AnotherPass2026!", "role": "artisan",
            "phone": "9876543214", "state": "Odisha", "city": "Puri",
        })
        self.assertRedirects(response, "/")
        profile = User.objects.get(username="newmaker").profile
        self.assertTrue(profile.is_artisan())
        self.assertEqual(profile.verification_status, "pending")
        self.assertTrue(profile.user.groups.filter(name="Artisan").exists())

    def test_login_honours_only_local_next_urls(self):
        """Sign-in never redirects to an outside host."""
        url = reverse("accounts:login")
        response = self.client.post(url, {
            "username": "shopper", "password": "ExamplePass2026!",
            "next": "https://untrusted.example/path",
        })
        self.assertRedirects(response, "/")
        self.client.post(reverse("accounts:logout"))
        response = self.client.post(url, {
            "username": "shopper", "password": "ExamplePass2026!",
            "next": reverse("accounts:profile"),
        })
        self.assertRedirects(response, reverse("accounts:profile"))

    def test_login_uses_browser_or_two_week_session(self):
        """The remember-me checkbox controls the session lifetime."""
        url = reverse("accounts:login")
        self.client.post(url, {
            "username": "shopper", "password": "ExamplePass2026!",
        })
        self.assertTrue(self.client.session.get_expire_at_browser_close())
        self.client.post(reverse("accounts:logout"))
        self.client.post(url, {
            "username": "shopper", "password": "ExamplePass2026!", "remember_me": "on",
        })
        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertGreater(self.client.session.get_expiry_age(), 60 * 60 * 24 * 13)

    def test_logout_is_post_only(self):
        """A GET cannot sign someone out, but a POST can."""
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_csrf_token(self):
        """A forged POST without a CSRF token cannot sign out a user."""
        secure_client = Client(enforce_csrf_checks=True)
        secure_client.force_login(self.buyer)
        response = secure_client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"This form expired", response.content)
        self.assertIn("_auth_user_id", secure_client.session)

    def test_invalid_login_does_not_create_a_session(self):
        """Wrong passwords display form errors instead of signing in."""
        response = self.client.post(reverse("accounts:login"), {
            "username": "shopper", "password": "wrong password",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_profile_edit_changes_only_current_profile(self):
        """A buyer can update their own contact information."""
        self.client.force_login(self.buyer)
        response = self.client.post(reverse("accounts:profile_edit"), {
            "phone": "9876543219", "state": "Delhi", "city": "New Delhi",
            "preferred_language": "hi", "bio": "I love handmade textiles.",
        })
        self.assertRedirects(response, reverse("accounts:profile"))
        self.buyer.profile.refresh_from_db()
        self.assertEqual(self.buyer.profile.phone, "9876543219")
        self.artisan_profile.refresh_from_db()
        self.assertEqual(self.artisan_profile.phone, "9876543210")

    def test_profile_avatar_rejects_other_image_types(self):
        """A real GIF image with a GIF filename is not accepted."""
        output = BytesIO()
        Image.new("RGB", (8, 8), "white").save(output, format="GIF")
        avatar = SimpleUploadedFile("picture.gif", output.getvalue(), content_type="image/gif")
        form = ProfileForm(data={
            "phone": "9876543210", "state": "Bihar", "city": "Patna",
            "preferred_language": "en",
        }, files={"avatar": avatar}, instance=self.artisan_profile)
        self.assertFalse(form.is_valid())
        self.assertIn("avatar", form.errors)

    def test_profile_avatar_rejects_files_over_two_megabytes(self):
        """A valid PNG still fails if its upload exceeds the size limit."""
        output = BytesIO()
        Image.new("RGB", (8, 8), "white").save(output, format="PNG")
        contents = output.getvalue() + b"0" * (2 * 1024 * 1024)
        avatar = SimpleUploadedFile("large.png", contents, content_type="image/png")
        form = ProfileForm(data={
            "phone": "9876543210", "state": "Bihar", "city": "Patna",
            "preferred_language": "en",
        }, files={"avatar": avatar}, instance=self.artisan_profile)
        self.assertFalse(form.is_valid())
        self.assertIn("smaller than 2 MB", str(form.errors["avatar"]))

    def test_role_decorators_redirect_visitors_and_block_other_roles(self):
        """Guests go to login and signed-in users get the correct role gate."""
        factory = RequestFactory()
        request = factory.get("/private/")
        request.user = AnonymousUser()
        response = artisan_required(protected_page)(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/?next=/private/", response["Location"])
        request.user = self.buyer
        with self.assertRaises(PermissionDenied):
            artisan_required(protected_page)(request)
        request.user = self.artisan
        with self.assertRaises(PermissionDenied):
            buyer_required(protected_page)(request)
        self.assertEqual(artisan_required(protected_page)(request).status_code, 200)

    def test_public_artisan_page_only_shows_artisans(self):
        """Visitors can view a maker but cannot treat a buyer as a maker."""
        response = self.client.get(reverse("accounts:artisan_detail", args=[self.artisan.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/artisan_detail.html")
        response = self.client.get(reverse("accounts:artisan_detail", args=[self.buyer.pk]))
        self.assertEqual(response.status_code, 404)

    def test_public_artisan_page_hides_drafts(self):
        """The public page never reveals a maker's unpublished listings."""
        category = Category.objects.create(name="Paintings", slug="paintings")
        craft = CraftTradition.objects.create(
            name="Madhubani", slug="madhubani", state="Bihar", description="Folk art."
        )
        for title, status in [("Public painting", "published"), ("Private draft", "draft")]:
            Product.objects.create(
                artisan=self.artisan, category=category, craft=craft,
                title=title, raw_notes="Flowers on paper.", materials="paper",
                technique="painting", description="A painted piece.",
                price="200.00", stock=2, image="products/test.jpg", status=status,
            )
        response = self.client.get(reverse("accounts:artisan_detail", args=[self.artisan.pk]))
        self.assertContains(response, "Public painting")
        self.assertNotContains(response, "Private draft")

    def test_verification_queue_requires_permission(self):
        """Visitors log in, buyers see 403 and verifiers see the queue."""
        url = reverse("accounts:verification_queue")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("next=", response["Location"])
        self.client.force_login(self.buyer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")
        self.client.force_login(self.verifier)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "maker")

    def test_approval_records_verifier_and_rejects_second_post(self):
        """Only a pending artisan can be approved once."""
        self.client.force_login(self.verifier)
        url = reverse("accounts:approve", args=[self.artisan_profile.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), reverse("accounts:verification_queue"))
        self.artisan_profile.refresh_from_db()
        self.assertTrue(self.artisan_profile.is_verified)
        self.assertEqual(self.artisan_profile.verification_status, "approved")
        self.assertEqual(self.artisan_profile.verified_by, self.verifier)
        self.assertIsNotNone(self.artisan_profile.verified_at)
        self.assertEqual(self.client.post(url).status_code, 404)

    def test_rejection_removes_artisan_from_queue_but_keeps_account(self):
        """A declined artisan remains a user but leaves the pending list."""
        self.client.force_login(self.verifier)
        url = reverse("accounts:reject", args=[self.artisan_profile.pk])
        self.assertRedirects(self.client.post(url), reverse("accounts:verification_queue"))
        self.artisan_profile.refresh_from_db()
        self.assertEqual(self.artisan_profile.verification_status, "rejected")
        self.assertFalse(self.artisan_profile.is_verified)
        self.assertTrue(User.objects.get(pk=self.artisan.pk).is_active)
        response = self.client.get(reverse("accounts:verification_queue"))
        self.assertNotContains(response, "maker")

    def test_buyer_cannot_approve_an_artisan(self):
        """The permission gate prevents forged approval requests."""
        self.client.force_login(self.buyer)
        response = self.client.post(reverse("accounts:approve", args=[self.artisan_profile.pk]))
        self.assertEqual(response.status_code, 403)
        self.artisan_profile.refresh_from_db()
        self.assertFalse(self.artisan_profile.is_verified)
