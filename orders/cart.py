"""Small helpers for an ordinary Django session shopping cart."""

from decimal import Decimal

from django.contrib import messages

from catalog.models import Product


def add_to_cart(request, product, quantity):
    """Add available stock to the session without exceeding it."""
    # Syllabus: Unit VI - sessions hold only product IDs and integer quantities.
    cart = request.session.setdefault("cart", {})
    key = str(product.pk)
    cart[key] = min(cart.get(key, 0) + quantity, product.stock)
    request.session.modified = True


def update_quantity(request, product, quantity):
    """Change a cart quantity or remove an item when it reaches zero."""
    cart = request.session.setdefault("cart", {})
    if quantity <= 0:
        cart.pop(str(product.pk), None)
    else:
        cart[str(product.pk)] = min(quantity, product.stock)
    request.session.modified = True


def remove_from_cart(request, product_id):
    """Remove one product ID from the current session cart."""
    request.session.setdefault("cart", {}).pop(str(product_id), None)
    request.session.modified = True


def clear_cart(request):
    """Empty the session only after a successful checkout."""
    request.session["cart"] = {}
    request.session.modified = True


def cart_items(request):
    """Read all products in one query and return cart lines and their total."""
    cart = request.session.get("cart", {})
    identifiers = [key for key in cart if str(key).isascii() and str(key).isdigit()]
    products = Product.objects.filter(pk__in=identifiers).select_related("artisan")
    by_id = {str(product.pk): product for product in products}
    lines = []
    total = Decimal("0.00")
    for key, quantity in list(cart.items()):
        product = by_id.get(key)
        if product is None or product.status != "published" or product.stock == 0:
            cart.pop(key)
            request.session.modified = True
            messages.warning(request, "An unavailable product was removed from your cart.")
            continue
        if not isinstance(quantity, int) or quantity < 1:
            cart.pop(key)
            request.session.modified = True
            continue
        if quantity > product.stock:
            quantity = product.stock
            cart[key] = quantity
            request.session.modified = True
            messages.warning(request, "Quantity was reduced to the available stock.")
        subtotal = product.price * quantity
        lines.append({"product": product, "quantity": quantity, "subtotal": subtotal})
        total += subtotal
    return lines, total
