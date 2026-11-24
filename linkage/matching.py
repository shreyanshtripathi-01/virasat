"""Simple ORM-only matching for open handmade buyer requests."""

from django.db.models import Case, F, IntegerField, Value, When

from catalog.models import Product
from .models import BuyerRequest


def match_requests_for(artisan):
    """Score category and craft matches twice as much as a state match."""
    # Syllabus: Unit V - use ORM annotations to score and order related rows.
    products = Product.objects.filter(artisan=artisan)
    category_ids = products.values_list("category_id", flat=True).distinct()
    craft_ids = products.values_list("craft_id", flat=True).distinct()
    state = artisan.profile.state
    return BuyerRequest.objects.filter(status="open").annotate(
        category_points=Case(
            When(category_id__in=category_ids, then=Value(2)),
            default=Value(0), output_field=IntegerField(),
        ),
        craft_points=Case(
            When(craft_id__in=craft_ids, then=Value(2)),
            default=Value(0), output_field=IntegerField(),
        ),
        state_points=Case(
            When(preferred_state__iexact=state, then=Value(1)),
            default=Value(0), output_field=IntegerField(),
        ),
    ).annotate(
        score=F("category_points") + F("craft_points") + F("state_points")
    ).filter(score__gt=0).select_related("buyer", "category", "craft").order_by(
        "-score", "-created_at"
    )
