"""Session cart, checkout and owner-checked order pages."""

import logging

from django.conf import settings
from django.contrib import messages
from django.db import OperationalError, transaction
from django.db.models import F
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.views import artisan_required, buyer_required
from catalog.models import Product

from .cart import add_to_cart, cart_items, clear_cart, remove_from_cart, update_quantity
from .forms import CheckoutForm
from .models import Order, OrderItem


logger = logging.getLogger(__name__)


class StockChanged(Exception):
    """Tell checkout to show a friendly error instead of creating an order."""


def requested_quantity(request):
    """Read a small whole-number quantity from the POST form."""
    try:
        quantity = int(request.POST.get("quantity", "1"))
    except (TypeError, ValueError):
        return None
    if quantity < 0 or quantity > 9999:
        return None
    return quantity


def invalid_quantity(request, message):
    """Send a styled 400 response for invalid cart quantities."""
    html = render_to_string("400.html", {"reason": message}, request=request)
    return HttpResponseBadRequest(html)


@buyer_required
@require_GET
def cart_page(request):
    """Show the buyer's current session cart and its live total."""
    lines, total = cart_items(request)
    for line in lines:
        line["quantity_choices"] = range(0, min(line["product"].stock, 9999) + 1)
    return render(request, "orders/cart.html", {
        "lines": lines, "total": total, "platform_fee_percent": settings.PLATFORM_FEE_PERCENT,
    })


@buyer_required
@require_POST
def cart_add(request, pk):
    """Add one published product without requesting more than its stock."""
    product = get_object_or_404(Product, pk=pk, status="published")
    quantity = requested_quantity(request)
    if quantity is None or quantity < 1:
        return invalid_quantity(request, "Enter a quantity of at least one.")
    if product.stock == 0:
        messages.warning(request, "This product is sold out.")
        return redirect(product.get_absolute_url())
    add_to_cart(request, product, quantity)
    messages.success(request, "Added to your cart.")
    return redirect("orders:cart")


@buyer_required
@require_POST
def cart_update(request, pk):
    """Change a quantity, limited by this product's current stock."""
    product = get_object_or_404(Product, pk=pk, status="published")
    quantity = requested_quantity(request)
    if quantity is None:
        return invalid_quantity(request, "Enter a valid quantity.")
    update_quantity(request, product, quantity)
    messages.success(request, "Cart updated.")
    return redirect("orders:cart")


@buyer_required
@require_POST
def cart_remove(request, pk):
    """Remove one session cart line using a POST request."""
    remove_from_cart(request, pk)
    messages.info(request, "Removed from your cart.")
    return redirect("orders:cart")


def place_order(request, form):
    """Recheck stock, create price snapshots and decrement inventory atomically."""
    # Syllabus: Unit V - one transaction keeps orders and inventory consistent.
    with transaction.atomic():
        before = dict(request.session.get("cart", {}))
        lines, total = cart_items(request)
        if not lines or before != request.session.get("cart", {}):
            raise StockChanged
        for line in lines:
            changed = Product.objects.filter(
                pk=line["product"].pk, status="published",
                stock__gte=line["quantity"],
            ).update(stock=F("stock") - line["quantity"])
            if changed != 1:
                raise StockChanged
        order = form.save(commit=False)
        order.buyer = request.user
        order.total = total
        order.save()
        for line in lines:
            OrderItem.objects.create(
                order=order, product=line["product"],
                quantity=line["quantity"], unit_price=line["product"].price,
            )
    clear_cart(request)
    return order


@buyer_required
def checkout(request):
    """Confirm delivery details and redirect after a successful purchase."""
    profile = request.user.profile
    initial = {
        "full_name": request.user.get_full_name(), "phone": profile.phone,
        "city": profile.city, "state": profile.state,
    }
    form = CheckoutForm(request.POST if request.method == "POST" else None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            order = place_order(request, form)
        except (StockChanged, OperationalError):
            messages.error(request, "Stock changed. Please check your cart and try again.")
            return redirect("orders:cart")
        messages.success(request, "Order placed. Thank you for choosing handmade.")
        logger.info("Order %s created for buyer ID %s", order.order_number, request.user.pk)
        return redirect("orders:order_detail", pk=f"{order.pk:06d}")
    lines, total = cart_items(request)
    if not lines:
        messages.warning(request, "Your cart is empty.")
        return redirect("orders:cart")
    return render(request, "orders/checkout.html", {
        "form": form, "lines": lines, "total": total,
    })


@buyer_required
@require_GET
def buyer_orders(request):
    """Show only the signed-in buyer's orders."""
    orders = Order.objects.filter(buyer=request.user).prefetch_related("items__product")
    return render(request, "orders/order_list.html", {"orders": orders})


@buyer_required
@require_GET
def order_detail(request, pk):
    """Show an order only when its buyer owns it."""
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"), pk=pk, buyer=request.user
    )
    return render(request, "orders/order_detail.html", {"order": order})


@buyer_required
@require_GET
def invoice(request, pk):
    """Download a plain-text invoice belonging to this buyer."""
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"), pk=pk, buyer=request.user
    )
    lines = [f"Virasat invoice {order.order_number}", f"Buyer: {order.full_name}",
             f"Delivery: {order.address}, {order.city}, {order.state} {order.pincode}", ""]
    for item in order.items.all():
        lines.append(f"{item.product.title} x {item.quantity}: ₹{item.line_total():.2f} ({item.status})")
    lines.append(f"Amount due: ₹{order.total:.2f}")
    lines.append("UPI (demo) does not move money." if order.payment_method == "upi_demo" else "Payment: cash on delivery.")
    response = HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{order.order_number}.txt"'
    return response


@buyer_required
@require_POST
@transaction.atomic
def cancel_item(request, pk):
    """Cancel only a placed item and restore its stock and order total."""
    item = get_object_or_404(
        OrderItem.objects.select_related("order", "product"), pk=pk,
        order__buyer=request.user,
    )
    changed = OrderItem.objects.filter(pk=pk, status="placed").update(
        status="cancelled", updated_at=timezone.now()
    )
    if changed:
        Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)
        Order.objects.filter(pk=item.order_id).update(total=F("total") - item.line_total())
        messages.success(request, "Item cancelled. Stock was returned.")
    else:
        html = render_to_string(
            "403.html", {"reason": "Only placed items can be cancelled."}, request=request
        )
        return HttpResponseForbidden(html)
    return redirect("orders:order_detail", pk=f"{item.order_id:06d}")


@artisan_required
@require_GET
def artisan_orders(request):
    """Show only purchased items belonging to this artisan's products."""
    items = OrderItem.objects.filter(product__artisan=request.user).select_related(
        "order__buyer", "product"
    ).order_by("-order__created_at")
    return render(request, "orders/artisan_orders.html", {"items": items})


@artisan_required
@require_POST
def update_item_status(request, pk):
    """Move only this artisan's item one step forward in delivery."""
    item = get_object_or_404(
        OrderItem, pk=pk, product__artisan=request.user
    )
    next_stage = {"placed": "confirmed", "confirmed": "shipped", "shipped": "delivered"}
    desired = request.POST.get("status")
    if next_stage.get(item.status) != desired:
        messages.error(request, "Choose the next delivery step.")
        return redirect("orders:artisan_orders")
    changed = OrderItem.objects.filter(pk=pk, status=item.status).update(
        status=desired, updated_at=timezone.now()
    )
    if changed:
        messages.success(request, "Order status updated.")
    else:
        messages.warning(request, "Status changed. Refresh your orders.")
    return redirect("orders:artisan_orders")
