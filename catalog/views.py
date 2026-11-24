"""Function-based catalog, wishlist and review pages."""

from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db.models import Avg, F, Q
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_GET, require_POST

from accounts.models import Profile
from accounts.views import artisan_required, buyer_required
from orders.models import OrderItem
from linkage.matching import match_requests_for

from .ai_service import fallback_content, generate_catalog_content
from .forms import ProductFilterForm, ProductForm, ProductRawForm, ReviewForm
from .models import Category, CraftTradition, Product, Review, Wishlist


def recent_products(request):
    """Read up to five safe numeric IDs from the recently viewed cookie."""
    identifiers = request.COOKIES.get("recently_viewed", "").split(",")[:5]
    identifiers = [value for value in identifiers if value.isascii() and value.isdigit() and len(value) <= 20]
    found = Product.objects.filter(pk__in=identifiers, status="published").select_related(
        "artisan__profile", "craft", "category"
    )
    by_id = {str(product.pk): product for product in found}
    return [by_id[value] for value in identifiers if value in by_id]


def filtered_products(queryset, form):
    """Apply valid GET filters and sorting to published listings."""
    if not form.is_valid():
        return queryset
    filters = form.cleaned_data
    if filters["q"]:
        search = filters["q"]
        queryset = queryset.filter(
            Q(title__icontains=search) | Q(materials__icontains=search)
            | Q(tags__icontains=search) | Q(craft__name__icontains=search)
        )
    if filters["category"]:
        queryset = queryset.filter(category=filters["category"])
    if filters["craft"]:
        queryset = queryset.filter(craft=filters["craft"])
    if filters["state"]:
        queryset = queryset.filter(craft__state=filters["state"])
    if filters["min_price"] is not None:
        queryset = queryset.filter(price__gte=filters["min_price"])
    if filters["max_price"] is not None:
        queryset = queryset.filter(price__lte=filters["max_price"])
    if filters["verified_only"]:
        queryset = queryset.filter(artisan__profile__is_verified=True)
    if filters["sort"] == "price_asc":
        return queryset.order_by("price", "pk")
    if filters["sort"] == "price_desc":
        return queryset.order_by("-price", "-pk")
    if filters["sort"] == "rated":
        return queryset.annotate(rating=Avg("reviews__rating")).order_by("-rating", "-created_at")
    return queryset.order_by("-created_at")


def active_filter_chips(request, form):
    """Describe each active filter with a query string that removes it."""
    if not form.is_valid():
        return []
    data = form.cleaned_data
    definitions = [
        ("q", "Search", data.get("q")),
        ("category", "Category", str(data["category"]) if data.get("category") else ""),
        ("craft", "Craft", str(data["craft"]) if data.get("craft") else ""),
        ("state", "State", data.get("state")),
        ("min_price", "From", f"₹{data['min_price']}" if data.get("min_price") is not None else ""),
        ("max_price", "To", f"₹{data['max_price']}" if data.get("max_price") is not None else ""),
        ("verified_only", "Verified artisans", "Only verified" if data.get("verified_only") else ""),
    ]
    chips = []
    for key, label, value in definitions:
        if not value:
            continue
        query = request.GET.copy()
        query.pop(key, None)
        query.pop("page", None)
        chips.append({"label": label, "value": value, "query": query.urlencode()})
    return chips


@require_GET
def product_list(request):
    """Browse published products with GET filters and twelve per page."""
    # Syllabus: Unit III - paginate and render a dynamic template.
    form = ProductFilterForm(request.GET)
    queryset = Product.objects.filter(status="published").select_related(
        "artisan__profile", "craft", "category"
    ).prefetch_related("reviews")
    paginator = Paginator(filtered_products(queryset, form), 12)
    page = paginator.get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    chips = active_filter_chips(request, form)
    return render(request, "catalog/product_list.html", {
        "form": form, "page_obj": page, "query_string": query.urlencode(),
        "active_filters": chips, "current_sort": request.GET.get("sort") or "newest",
        "sort_choices": ProductFilterForm.SORT_CHOICES,
        "recent_products": recent_products(request),
    })


@require_GET
def product_detail(request, pk, slug):
    """Show a listing, count the visit and remember it for next time."""
    visible = Q(status="published")
    if request.user.is_authenticated:
        visible |= Q(artisan=request.user)
    product = get_object_or_404(
        Product.objects.filter(visible).select_related("artisan__profile", "craft", "category"), pk=pk
    )
    if slug != slugify(product.title):
        return redirect(product.get_absolute_url(), permanent=True)
    Product.objects.filter(pk=pk).update(view_count=F("view_count") + 1)
    can_review = False
    if request.user.is_authenticated and Profile.objects.filter(user=request.user, role="buyer").exists():
        can_review = OrderItem.objects.filter(
            order__buyer=request.user, product=product, status="delivered"
        ).exists() and not Review.objects.filter(product=product, buyer=request.user).exists()
    more_products = Product.objects.filter(
        artisan=product.artisan, status="published"
    ).exclude(pk=pk).select_related("craft", "artisan__profile").prefetch_related("reviews")[:4]
    related_products = Product.objects.filter(status="published").exclude(pk=pk).filter(
        Q(craft=product.craft) | Q(category=product.category)
    ).select_related("craft", "artisan__profile").prefetch_related("reviews").order_by("-created_at")[:4]
    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = Wishlist.objects.filter(user=request.user, product=product).exists()
    response = render(request, "catalog/product_detail.html", {
        "product": product, "reviews": product.reviews.select_related("buyer"),
        "more_products": more_products, "related_products": related_products,
        "is_wishlisted": is_wishlisted, "can_review": can_review,
        "review_form": ReviewForm(),
        "quantity_choices": range(1, min(product.stock, 10) + 1),
        "platform_fee_percent": settings.PLATFORM_FEE_PERCENT,
        "artisan_percent": Decimal("100") - settings.PLATFORM_FEE_PERCENT,
    })
    if product.status == "published":
        identifiers = [str(pk)] + [str(item.pk) for item in recent_products(request) if item.pk != pk]
        response.set_cookie(
            "recently_viewed", ",".join(identifiers[:5]), max_age=60 * 60 * 24 * 30,
            httponly=True, samesite="Lax", secure=request.is_secure(),
        )
    return response


@require_GET
def craft_detail(request, slug):
    """Show one heritage tradition and its published pieces."""
    craft = get_object_or_404(CraftTradition, slug=slug)
    products = craft.products.filter(status="published").select_related("artisan__profile", "craft")
    return render(request, "catalog/craft_detail.html", {"craft": craft, "products": products})


@require_GET
def category_detail(request, slug):
    """Show all published products in one category."""
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(status="published").select_related("artisan__profile", "craft")
    return render(request, "catalog/category_detail.html", {
        "category": category, "products": products,
    })


@buyer_required
@require_GET
def wishlist(request):
    """List the current buyer's saved published products."""
    entries = Wishlist.objects.filter(
        user=request.user, product__status="published"
    ).select_related("product__craft", "product__artisan__profile")
    return render(request, "catalog/wishlist.html", {"entries": entries})


@buyer_required
@require_POST
def toggle_wishlist(request, pk):
    """Add or remove a published product from this buyer's wishlist."""
    product = get_object_or_404(Product, pk=pk, status="published")
    entry, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request, "Saved for later.")
    else:
        entry.delete()
        messages.info(request, "Removed from saved items.")
    return redirect(product.get_absolute_url())


@buyer_required
@require_POST
def submit_review(request, pk):
    """Allow one review only after this buyer receives the product."""
    product = get_object_or_404(Product, pk=pk, status="published")
    delivered = OrderItem.objects.filter(
        product=product, order__buyer=request.user, status="delivered"
    ).exists()
    if not delivered:
        raise Http404("A delivered purchase is required before reviewing.")
    if Review.objects.filter(product=product, buyer=request.user).exists():
        messages.info(request, "You have already reviewed this piece.")
        return redirect(product.get_absolute_url())
    form = ReviewForm(request.POST)
    if form.is_valid():
        _, created = Review.objects.get_or_create(
            product=product, buyer=request.user,
            defaults={"rating": form.cleaned_data["rating"], "comment": form.cleaned_data["comment"]},
        )
        if created:
            messages.success(request, "Thank you for your review.")
        else:
            messages.info(request, "You have already reviewed this piece.")
    else:
        messages.error(request, "Choose a rating from 1 to 5.")
    return redirect(product.get_absolute_url())


def draft_content_for(request, craft, materials, technique, notes):
    """Use the offline draft when the session has exhausted today's AI calls."""
    language = request.user.profile.preferred_language
    facts = (craft.name, craft.state, materials, technique, notes, language)
    if not settings.ANTHROPIC_API_KEY:
        return generate_catalog_content(*facts)
    today = timezone.localdate().isoformat()
    if request.session.get("ai_calls_date") != today:
        request.session["ai_calls_date"] = today
        request.session["ai_calls_count"] = 0
    if request.session["ai_calls_count"] >= 15:
        messages.warning(request, "Daily AI limit reached. An offline draft was used.")
        return fallback_content(*facts)
    request.session["ai_calls_count"] += 1
    return generate_catalog_content(*facts)


def apply_catalog_draft(product, content):
    """Copy generated text and its source to one editable product."""
    for name in [
        "description", "hindi_description", "heritage_story", "care_instructions", "tags",
    ]:
        setattr(product, name, content[name])
    product.ai_source = content["source"]
    product.ai_edited = False


def artisan_earnings(artisan):
    """Sum delivered and pending earnings from this artisan's order items."""
    delivered = Decimal("0.00")
    pending = Decimal("0.00")
    for item in OrderItem.objects.filter(product__artisan=artisan).select_related("product"):
        if item.status == "delivered":
            delivered += item.artisan_amount()
        elif item.status in {"placed", "confirmed", "shipped"}:
            pending += item.artisan_amount()
    return {"delivered": delivered, "pending": pending}


@artisan_required
@require_GET
def artisan_dashboard(request):
    """Summarise this artisan's products and orders."""
    products = Product.objects.filter(artisan=request.user)
    earnings = artisan_earnings(request.user)
    total_earnings = earnings["delivered"] + earnings["pending"]
    matches = match_requests_for(request.user)
    return render(request, "catalog/dashboard.html", {
        "draft_count": products.filter(status="draft").count(),
        "published_count": products.filter(status="published").count(),
        "archived_count": products.filter(status="archived").count(),
        "pending_orders": OrderItem.objects.filter(
            product__artisan=request.user, status="placed"
        ).count(),
        "matching_requests": matches.count(),
        "matched_preview": matches[:2],
        "earnings": earnings,
        "delivered_percent": round(earnings["delivered"] / total_earnings * 100) if total_earnings else 0,
        "recent_orders": OrderItem.objects.filter(product__artisan=request.user).select_related(
            "order", "product"
        ).order_by("-order__created_at")[:4],
        "recent_products": products[:4],
    })


@artisan_required
@require_GET
def artisan_products(request):
    """List only this artisan's products with optional status tabs."""
    status = request.GET.get("status", "")
    products = Product.objects.filter(artisan=request.user).select_related("craft", "category")
    if status in {"draft", "published", "archived"}:
        products = products.filter(status=status)
    return render(request, "catalog/artisan_products.html", {
        "products": products, "status": status,
    })


@artisan_required
@require_GET
def new_product(request):
    """Show the simple notes form before creating a catalog draft."""
    return render(request, "catalog/product_new.html", {"form": ProductRawForm()})


@artisan_required
@require_POST
def generate_product(request):
    """Validate raw notes, generate text and save an unpublished draft."""
    form = ProductRawForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, "catalog/product_new.html", {"form": form}, status=400)
    data = form.cleaned_data
    content = draft_content_for(request, data["craft"], data["materials"], data["technique"], data["notes"])
    product = Product(
        artisan=request.user, craft=data["craft"], category=data["category"],
        title=data["title_hint"] or content["title"], raw_notes=data["notes"],
        materials=data["materials"], technique=data["technique"],
        price=data["price"], stock=data["stock"], image=data["image"], status="draft",
    )
    apply_catalog_draft(product, content)
    product.save()
    messages.success(request, "Draft ready. Read and edit it before publishing.")
    return redirect("catalog:product_edit", pk=product.pk)


@artisan_required
def edit_product(request, pk):
    """Let the owner review, change and save or publish catalog text."""
    product = get_object_or_404(Product, pk=pk, artisan=request.user)
    original = {name: getattr(product, name) for name in [
        "title", "description", "hindi_description", "heritage_story", "care_instructions", "tags",
    ]}
    form = ProductForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None, instance=product,
    )
    if request.method == "POST" and form.is_valid():
        action = request.POST.get("action", "save")
        if action not in {"save", "publish"}:
            messages.error(request, "Choose Save draft or Publish.")
            return redirect("catalog:product_edit", pk=pk)
        product = form.save(commit=False)
        if product.ai_source != "manual" and any(getattr(product, key) != value for key, value in original.items()):
            product.ai_edited = True
        product.status = "published" if action == "publish" else "draft"
        product.save()
        messages.success(request, "Product published." if action == "publish" else "Draft saved.")
        return redirect("catalog:product_edit", pk=pk)
    return render(request, "catalog/product_edit.html", {
        "product": product, "form": form,
        "confirm_regenerate": request.GET.get("confirm_regenerate") == "1",
    })


@artisan_required
@require_POST
def regenerate_product(request, pk):
    """Replace the owner's text with a new draft after confirmation."""
    product = get_object_or_404(Product, pk=pk, artisan=request.user)
    if request.POST.get("confirm") != "yes":
        messages.warning(request, "Please confirm before replacing your draft.")
        return redirect("catalog:product_edit", pk=pk)
    content = draft_content_for(
        request, product.craft, product.materials, product.technique, product.raw_notes
    )
    apply_catalog_draft(product, content)
    product.title = content["title"]
    product.status = "draft"
    product.save()
    messages.success(request, "New draft ready. Review it before publishing.")
    return redirect("catalog:product_edit", pk=pk)


@artisan_required
@require_POST
def change_product_status(request, pk):
    """Publish, archive or return only the owner's product to draft."""
    product = get_object_or_404(Product, pk=pk, artisan=request.user)
    status = request.POST.get("status")
    if status not in {"published", "archived", "draft"}:
        messages.error(request, "Choose a valid product status.")
        return redirect("catalog:artisan_products")
    if status == "published":
        if product.ai_source != "manual" and request.POST.get("reviewed") != "yes":
            messages.warning(request, "Read and confirm the catalog draft before publishing.")
            return redirect("catalog:product_edit", pk=pk)
        try:
            product.full_clean()
        except ValidationError:
            messages.error(request, "Complete the product details before publishing.")
            return redirect("catalog:product_edit", pk=pk)
    product.status = status
    product.save(update_fields=["status", "updated_at"])
    messages.success(request, "Product status updated.")
    return redirect("catalog:artisan_products")


@artisan_required
def delete_product(request, pk):
    """Confirm deletion and keep products with historical orders."""
    product = get_object_or_404(Product, pk=pk, artisan=request.user)
    if request.method == "POST":
        try:
            product.delete()
        except ProtectedError:
            messages.error(request, "This product has orders. Archive it instead.")
        else:
            messages.success(request, "Product deleted.")
        return redirect("catalog:artisan_products")
    return render(request, "catalog/product_delete.html", {"product": product})
