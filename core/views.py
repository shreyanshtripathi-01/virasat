"""The marketplace home page, about page, language switch and PWA files."""

import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import Avg, Count, DecimalField, F, Q, Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET

from accounts.models import Profile
from catalog.models import CraftTradition, Product
from catalog.views import recent_products
from orders.models import Order, OrderItem


@require_GET
def home(request):
    """Introduce crafts, makers and real figures from the database."""
    products = list(Product.objects.filter(status="published").select_related(
        "artisan__profile", "craft", "category"
    ).prefetch_related("reviews")[:8])
    crafts = list(CraftTradition.objects.annotate(
        published_count=Count("products", filter=Q(products__status="published"))
    ).order_by("name"))
    featured_artisans = (
        User.objects.filter(profile__role="artisan", profile__is_verified=True)
        .select_related("profile")
        .annotate(live_products=Count("products", filter=Q(products__status="published")))
        .order_by("-live_products", "first_name", "username")[:4]
    )
    hero_product = Product.objects.filter(
        status="published", craft__slug="madhubani", artisan__profile__is_verified=True,
    ).select_related("artisan__profile", "craft").order_by("pk").first()
    if hero_product is None:
        hero_product = products[0] if products else None
    return render(request, "core/home.html", {
        "crafts": crafts,
        "hero_product": hero_product,
        "featured_products": products,
        "featured_artisans": featured_artisans,
        "recent_products": recent_products(request),
        "artisan_count": Profile.objects.filter(role="artisan", is_verified=True).count(),
        "product_count": Product.objects.filter(status="published").count(),
        "craft_count": len(crafts),
        "state_count": len({craft.state for craft in crafts}),
    })


@require_GET
def about(request):
    """Explain what Virasat does without making unverifiable claims."""
    return render(request, "core/about.html")


@require_GET
def impact(request):
    """Show honest figures calculated from published work and delivered items."""
    # Syllabus: Unit V - aggregate and annotate marketplace data with the ORM.
    published = Product.objects.filter(status="published")
    delivered = OrderItem.objects.filter(status="delivered").select_related("product")
    artisan_paid = sum((item.artisan_amount() for item in delivered), Decimal("0.00"))
    top_crafts = CraftTradition.objects.filter(
        products__order_items__status="delivered"
    ).annotate(sales=Sum(
        F("products__order_items__quantity") * F("products__order_items__unit_price"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )).order_by("-sales")[:5]
    top_products = published.annotate(
        rating=Avg("reviews__rating"), review_count=Count("reviews")
    ).filter(review_count__gt=0).select_related("craft").order_by("-rating", "-review_count")[:5]
    return render(request, "core/impact.html", {
        "verified_artisans": Profile.objects.filter(role="artisan", is_verified=True).count(),
        "published_count": published.count(),
        "state_count": published.values("craft__state").distinct().count(),
        "craft_count": published.values("craft_id").distinct().count(),
        "order_count": Order.objects.count(),
        "artisan_paid": artisan_paid,
        "top_crafts": top_crafts, "top_products": top_products,
    })


@require_GET
def change_language(request, language):
    """Remember English or Hindi in a cookie and return to a local page."""
    # Syllabus: Unit VI - set a cookie in the response to a request.
    previous = request.META.get("HTTP_REFERER", "")
    if not url_has_allowed_host_and_scheme(
        previous, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        previous = "/"
    response = redirect(previous)
    response.set_cookie(
        "lang", language, max_age=60 * 60 * 24 * 365,
        samesite="Lax", secure=request.is_secure(),
    )
    return response


@require_GET
def manifest(request):
    """Serve the installable web app manifest as JSON."""
    # Extension: this manifest supports Add to Home Screen, outside the INT253 syllabus.
    data = {
        "name": "Virasat",
        "short_name": "Virasat",
        "description": "Virasat, a Django marketplace for Indian handmade craft",
        "start_url": "/?source=pwa",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#FBF5E9",
        "theme_color": "#1F2A56",
        "lang": "en-IN",
        "icons": [
            {
                "src": static("img/icons/icon-192.png"),
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": static("img/icons/icon-512.png"),
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": static("img/icons/icon-512-maskable.png"),
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable",
            },
        ],
        "shortcuts": [
            {"name": "Browse", "url": reverse("catalog:product_list")},
            {"name": "My orders", "url": reverse("orders:order_list")},
            {"name": "Requests", "url": reverse("linkage:request_list")},
        ],
    }
    response = HttpResponse(
        json.dumps(data, ensure_ascii=False), content_type="application/manifest+json"
    )
    response["Cache-Control"] = "public, max-age=3600"
    return response


@require_GET
def service_worker(request):
    """Serve the service worker from the site root so it can control every page."""
    # Extension: the service worker provides offline support outside the INT253 syllabus.
    response = render(
        request, "pwa/service-worker.js", content_type="application/javascript"
    )
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response


@require_GET
def offline(request):
    """Show a friendly page when a navigation request has no network."""
    # Extension: this offline fallback belongs to the optional PWA extension.
    return render(request, "core/offline.html")


def permission_denied(request, exception):
    """Show the custom access-denied page with HTTP status 403."""
    # Syllabus: Unit II - custom error handling for forbidden pages.
    return render(request, "403.html", status=403)


def bad_request(request, exception):
    """Show a styled page for a request Django cannot accept."""
    return render(request, "400.html", status=400)


def page_not_found(request, exception):
    """Show a friendly page for an unknown or hidden resource."""
    return render(request, "404.html", status=404)


def server_error(request):
    """Show a safe error page without exposing an internal traceback."""
    return render(request, "500.html", status=500)


def csrf_failure(request, reason=""):
    """Explain an expired or missing form token without exposing details."""
    return render(request, "403.html", {
        "reason": "This form expired. Reload the page and try again."
    }, status=403)
