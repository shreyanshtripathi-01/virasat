"""Named account and public artisan URLs."""

from django.urls import path

from . import views


app_name = "accounts"

# Syllabus: Unit II - name each route and capture the artisan's numeric ID.
urlpatterns = [
    path("accounts/register/", views.register, name="register"),
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("accounts/profile/", views.profile, name="profile"),
    path("accounts/profile/edit/", views.edit_profile, name="profile_edit"),
    path("artisans/<int:pk>/", views.artisan_detail, name="artisan_detail"),
    path("accounts/verify/", views.verification_queue, name="verification_queue"),
    path("accounts/verify/<int:pk>/approve/", views.approve_artisan, name="approve"),
    path("accounts/verify/<int:pk>/reject/", views.reject_artisan, name="reject"),
]
