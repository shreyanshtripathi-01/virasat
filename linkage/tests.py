"""Market linkage form, matching and ownership tests."""

from datetime import timedelta
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile
from catalog.models import Category, CraftTradition, Product
from .forms import BuyerRequestForm, ProposalForm
from .matching import match_requests_for
from .models import BuyerRequest, Proposal


class LinkageTests(TestCase):
    """Verify scoring, validation and owner-only proposal decisions."""

    @classmethod
    def setUpTestData(cls):
        """Build an artisan with one craft and two buyers with requests."""
        cls.buyer = User.objects.create_user("buyer", password="ExamplePass2026!")
        cls.other_buyer = User.objects.create_user("otherbuyer", password="ExamplePass2026!")
        cls.artisan = User.objects.create_user("artisan", password="ExamplePass2026!")
        cls.other_artisan = User.objects.create_user("otherartisan", password="ExamplePass2026!")
        for user, role, state in [
            (cls.buyer, "buyer", "Delhi"), (cls.other_buyer, "buyer", "Delhi"),
            (cls.artisan, "artisan", "Rajasthan"), (cls.other_artisan, "artisan", "Gujarat"),
        ]:
            Profile.objects.create(user=user, role=role, state=state, city="City", phone="9876543210")
        cls.textiles = Category.objects.create(name="Textiles", slug="textiles")
        cls.paintings = Category.objects.create(name="Paintings", slug="paintings")
        cls.bagru = CraftTradition.objects.create(
            name="Bagru", slug="bagru", state="Rajasthan", description="Block printing."
        )
        cls.madhubani = CraftTradition.objects.create(
            name="Madhubani", slug="madhubani", state="Bihar", description="Painting."
        )
        Product.objects.create(
            artisan=cls.artisan, category=cls.textiles, craft=cls.bagru,
            title="Printed cotton stole", raw_notes="Printed by hand on cotton.",
            materials="cotton", technique="block printing", description="A printed stole.",
            price="400.00", stock=2, image="products/test.jpg", status="published",
        )
        today = timezone.localdate() + timedelta(days=30)
        cls.best = BuyerRequest.objects.create(
            buyer=cls.buyer, title="Best match", description="Cotton cloth.",
            category=cls.textiles, craft=cls.bagru, preferred_state="Rajasthan",
            quantity=2, budget_min="100.00", budget_max="500.00", needed_by=today,
        )
        cls.category_only = BuyerRequest.objects.create(
            buyer=cls.buyer, title="Category match", description="Cotton cloth.",
            category=cls.textiles, craft=cls.madhubani, preferred_state="Gujarat",
            quantity=2, budget_min="100.00", budget_max="500.00", needed_by=today,
        )
        cls.state_only = BuyerRequest.objects.create(
            buyer=cls.buyer, title="State match", description="Small painting.",
            category=cls.paintings, craft=cls.madhubani, preferred_state="Rajasthan",
            quantity=2, budget_min="100.00", budget_max="500.00", needed_by=today,
        )
        BuyerRequest.objects.create(
            buyer=cls.buyer, title="No match", description="Small painting.",
            category=cls.paintings, craft=cls.madhubani, preferred_state="Gujarat",
            quantity=2, budget_min="100.00", budget_max="500.00", needed_by=today,
        )

    def test_matching_order_has_scores_five_two_one(self):
        """Category and craft count twice as much as matching the state."""
        rows = list(match_requests_for(self.artisan).values_list("title", "score"))
        self.assertEqual(rows, [
            ("Best match", 5), ("Category match", 2), ("State match", 1),
        ])

    def test_request_form_rejects_past_date_and_wrong_budget(self):
        """Request validation checks future dates, quantity and budget order."""
        form = BuyerRequestForm({
            "title": "Cotton cloth", "description": "A table runner.",
            "category": self.textiles.pk, "quantity": 0,
            "budget_min": "600.00", "budget_max": "100.00",
            "needed_by": timezone.localdate().isoformat(),
        })
        self.assertFalse(form.is_valid())
        for field in ["quantity", "budget_max", "needed_by"]:
            self.assertIn(field, form.errors)

    def test_proposal_form_rejects_price_and_days(self):
        """An offer cannot be free or require over 90 days."""
        form = ProposalForm({
            "price_per_unit": "0", "delivery_days": 91, "message": "I can make it.",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("price_per_unit", form.errors)
        self.assertIn("delivery_days", form.errors)

    def test_one_artisan_can_propose_only_once(self):
        """Duplicate offers show a friendly form error instead of a server error."""
        self.client.force_login(self.artisan)
        url = reverse("linkage:propose", args=[self.best.pk])
        data = {"message": "I can print the cloth.", "price_per_unit": "350.00", "delivery_days": 12}
        self.assertRedirects(self.client.post(url, data), reverse("linkage:request_detail", args=[self.best.pk]))
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already sent an offer")
        self.assertEqual(Proposal.objects.filter(request=self.best, artisan=self.artisan).count(), 1)

    def test_duplicate_proposals_have_a_database_constraint(self):
        """Even direct ORM inserts cannot bypass one proposal per artisan."""
        Proposal.objects.create(
            request=self.best, artisan=self.artisan, message="First offer.",
            price_per_unit="300.00", delivery_days=10,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Proposal.objects.create(
                    request=self.best, artisan=self.artisan, message="Duplicate offer.",
                    price_per_unit="300.00", delivery_days=10,
                )

    def test_accepting_rejects_other_proposals_and_closes_request(self):
        """One atomic acceptance makes all other pending offers rejected."""
        accepted = Proposal.objects.create(
            request=self.best, artisan=self.artisan, message="I can print it.",
            price_per_unit="300.00", delivery_days=10,
        )
        rejected = Proposal.objects.create(
            request=self.best, artisan=self.other_artisan, message="I can help.",
            price_per_unit="320.00", delivery_days=12,
        )
        self.client.force_login(self.buyer)
        url = reverse("linkage:accept_proposal", args=[accepted.pk])
        self.assertRedirects(self.client.post(url), reverse("linkage:request_detail", args=[self.best.pk]))
        accepted.refresh_from_db()
        rejected.refresh_from_db()
        self.best.refresh_from_db()
        self.assertEqual(accepted.status, "accepted")
        self.assertEqual(rejected.status, "rejected")
        self.assertEqual(self.best.status, "closed")

    def test_other_buyer_cannot_accept_or_close_request(self):
        """Buyer actions filter by the request owner on the server."""
        proposal = Proposal.objects.create(
            request=self.best, artisan=self.artisan, message="I can print it.",
            price_per_unit="300.00", delivery_days=10,
        )
        self.client.force_login(self.other_buyer)
        self.assertEqual(self.client.post(reverse("linkage:accept_proposal", args=[proposal.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("linkage:close_request", args=[self.best.pk])).status_code, 404)

    def test_only_request_owner_sees_other_artisans_offers(self):
        """Artisans cannot inspect competing quotes on a public request."""
        Proposal.objects.create(
            request=self.best, artisan=self.other_artisan, message="Private quote text.",
            price_per_unit="300.00", delivery_days=10,
        )
        self.client.force_login(self.artisan)
        response = self.client.get(reverse("linkage:request_detail", args=[self.best.pk]))
        self.assertNotContains(response, "Private quote text.")
        self.client.force_login(self.buyer)
        response = self.client.get(reverse("linkage:request_detail", args=[self.best.pk]))
        self.assertContains(response, "Private quote text.")
