"""Named cart, buyer order and artisan fulfillment routes."""

from django.urls import path, re_path

from . import views


app_name = "orders"

urlpatterns = [
    path("cart/", views.cart_page, name="cart"),
    path("cart/add/<int:pk>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:pk>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:pk>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.buyer_orders, name="order_list"),
    # Syllabus: Unit II - the six-digit public order number is a regex route.
    re_path(r"^orders/VR(?P<pk>\d{6})/invoice/$", views.invoice, name="invoice"),
    re_path(r"^orders/VR(?P<pk>\d{6})/$", views.order_detail, name="order_detail"),
    path("orders/items/<int:pk>/cancel/", views.cancel_item, name="cancel_item"),
    path("dashboard/orders/", views.artisan_orders, name="artisan_orders"),
    path("dashboard/orders/items/<int:pk>/status/", views.update_item_status, name="item_status"),
]
