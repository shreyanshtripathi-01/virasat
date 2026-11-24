"""Named public catalog and buyer review URLs."""

from django.urls import path, re_path

from . import views


app_name = "catalog"

urlpatterns = [
    path("products/", views.product_list, name="product_list"),
    path("product/<int:pk>/review/", views.submit_review, name="review"),
    # Syllabus: Unit II - capture both a number and a slug with a regular expression.
    re_path(r"^product/(?P<pk>\d+)/(?P<slug>[-\w]+)/$", views.product_detail, name="product_detail"),
    path("craft/<slug:slug>/", views.craft_detail, name="craft_detail"),
    path("category/<slug:slug>/", views.category_detail, name="category_detail"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/toggle/<int:pk>/", views.toggle_wishlist, name="wishlist_toggle"),
    path("dashboard/", views.artisan_dashboard, name="dashboard"),
    path("dashboard/products/", views.artisan_products, name="artisan_products"),
    path("dashboard/products/new/", views.new_product, name="product_new"),
    path("dashboard/products/generate/", views.generate_product, name="product_generate"),
    path("dashboard/products/<int:pk>/edit/", views.edit_product, name="product_edit"),
    path("dashboard/products/<int:pk>/regenerate/", views.regenerate_product, name="product_regenerate"),
    path("dashboard/products/<int:pk>/status/", views.change_product_status, name="product_status"),
    path("dashboard/products/<int:pk>/delete/", views.delete_product, name="product_delete"),
]
