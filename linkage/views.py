"""Buyer craft requests and artisan offers, with owner checks."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.views import artisan_required, buyer_required
from accounts.models import Profile
from .forms import BuyerRequestForm, ProposalForm
from .matching import match_requests_for
from .models import BuyerRequest, Proposal


def request_card_context(requests):
    """Attach a presentation-only deadline count without changing stored data."""
    rows = list(requests)
    for row in rows:
        row.days_left = (row.needed_by - timezone.localdate()).days
    return rows


@login_required
@require_GET
def request_list(request):
    """Let signed-in visitors browse open handmade requests."""
    requests = BuyerRequest.objects.filter(status="open").select_related(
        "buyer", "category", "craft"
    )
    return render(request, "linkage/request_list.html", {"requests": request_card_context(requests)})


@artisan_required
@require_GET
def matched_requests(request):
    """Show open requests ordered by this artisan's craft and state matches."""
    return render(request, "linkage/matched_requests.html", {
        "requests": request_card_context(match_requests_for(request.user)),
    })


@buyer_required
def new_request(request):
    """Save a new buyer request after validating its date and budget."""
    form = BuyerRequestForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        buyer_request = form.save(commit=False)
        buyer_request.buyer = request.user
        buyer_request.save()
        messages.success(request, "Your request is open for artisans.")
        return redirect("linkage:request_detail", pk=buyer_request.pk)
    return render(request, "linkage/request_new.html", {"form": form})


@buyer_required
@require_GET
def my_requests(request):
    """List only requests created by this buyer."""
    requests = BuyerRequest.objects.filter(buyer=request.user).select_related("category", "craft")
    return render(request, "linkage/my_requests.html", {"requests": request_card_context(requests)})


@login_required
@require_GET
def request_detail(request, pk):
    """Show an open request or a closed one only to involved people."""
    visible = Q(status="open") | Q(buyer=request.user) | Q(proposals__artisan=request.user)
    buyer_request = get_object_or_404(
        BuyerRequest.objects.filter(visible).select_related("buyer", "category", "craft").distinct(),
        pk=pk,
    )
    is_owner = buyer_request.buyer_id == request.user.pk
    proposals = buyer_request.proposals.select_related("artisan") if is_owner else None
    my_proposal = None
    if not is_owner and Profile.objects.filter(user=request.user, role="artisan").exists():
        my_proposal = buyer_request.proposals.filter(artisan=request.user).first()
    return render(request, "linkage/request_detail.html", {
        "buyer_request": buyer_request, "is_owner": is_owner,
        "proposals": proposals, "my_proposal": my_proposal,
    })


@artisan_required
def propose(request, pk):
    """Let an artisan submit one offer for an open buyer request."""
    buyer_request = get_object_or_404(BuyerRequest, pk=pk, status="open")
    form = ProposalForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        if Proposal.objects.filter(request=buyer_request, artisan=request.user).exists():
            form.add_error(None, "You have already sent an offer for this request.")
        elif form.is_valid():
            proposal = form.save(commit=False)
            proposal.request = buyer_request
            proposal.artisan = request.user
            try:
                with transaction.atomic():
                    proposal.save()
            except IntegrityError:
                form.add_error(None, "You have already sent an offer for this request.")
            else:
                messages.success(request, "Your offer has been sent.")
                return redirect("linkage:request_detail", pk=pk)
    return render(request, "linkage/propose.html", {
        "form": form, "buyer_request": buyer_request,
    })


@buyer_required
@require_POST
@transaction.atomic
def accept_proposal(request, pk):
    """Accept one pending offer, reject the others and close the request."""
    proposal = get_object_or_404(
        Proposal.objects.select_related("request"), pk=pk,
        request__buyer=request.user, status="pending",
    )
    buyer_request = BuyerRequest.objects.select_for_update().get(pk=proposal.request_id)
    if buyer_request.status != "open":
        messages.warning(request, "This request is already closed.")
        return redirect("linkage:request_detail", pk=buyer_request.pk)
    Proposal.objects.filter(request=buyer_request, status="pending").exclude(
        pk=pk
    ).update(status="rejected")
    Proposal.objects.filter(pk=pk, status="pending").update(status="accepted")
    buyer_request.status = "closed"
    buyer_request.save(update_fields=["status"])
    messages.success(request, "Offer accepted. Your request is now closed.")
    return redirect("linkage:request_detail", pk=buyer_request.pk)


@buyer_required
@require_POST
def reject_proposal(request, pk):
    """Reject a pending offer only when this buyer owns its request."""
    proposal = get_object_or_404(
        Proposal, pk=pk, request__buyer=request.user, status="pending"
    )
    proposal.status = "rejected"
    proposal.save(update_fields=["status"])
    messages.info(request, "Offer declined.")
    return redirect("linkage:request_detail", pk=proposal.request_id)


@buyer_required
@require_POST
@transaction.atomic
def close_request(request, pk):
    """Close only the owner's open request and decline pending offers."""
    buyer_request = get_object_or_404(
        BuyerRequest.objects.select_for_update(), pk=pk, buyer=request.user, status="open"
    )
    buyer_request.proposals.filter(status="pending").update(status="rejected")
    buyer_request.status = "closed"
    buyer_request.save(update_fields=["status"])
    messages.success(request, "Request closed.")
    return redirect("linkage:request_detail", pk=pk)


@artisan_required
@require_GET
def my_proposals(request):
    """List this artisan's offers and their buyer decisions."""
    proposals = Proposal.objects.filter(artisan=request.user).select_related("request")
    return render(request, "linkage/my_proposals.html", {"proposals": proposals})
