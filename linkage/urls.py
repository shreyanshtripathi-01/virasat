"""Named market-linkage URLs."""

from django.urls import path

from . import views


app_name = "linkage"

urlpatterns = [
    path("requests/", views.request_list, name="request_list"),
    path("requests/matches/", views.matched_requests, name="matched_requests"),
    path("requests/new/", views.new_request, name="request_new"),
    path("requests/mine/", views.my_requests, name="my_requests"),
    path("requests/<int:pk>/", views.request_detail, name="request_detail"),
    path("requests/<int:pk>/propose/", views.propose, name="propose"),
    path("requests/<int:pk>/close/", views.close_request, name="close_request"),
    path("proposals/mine/", views.my_proposals, name="my_proposals"),
    path("proposals/<int:pk>/accept/", views.accept_proposal, name="accept_proposal"),
    path("proposals/<int:pk>/reject/", views.reject_proposal, name="reject_proposal"),
]
