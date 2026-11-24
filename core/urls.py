"""Named public information URLs."""

from django.urls import path, re_path

from . import views


app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("impact/", views.impact, name="impact"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
    path("sw.js", views.service_worker, name="service_worker"),
    path("offline/", views.offline, name="offline"),
    re_path(r"^language/(?P<language>en|hi)/$", views.change_language, name="language"),
]
