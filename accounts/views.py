from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .forms import SignUpForm, ProfileForm
from .models import Profile

def _get_next_url(request, default_name="offers:list") -> str:
    return (
        request.GET.get("next")
        or request.POST.get("next")
        or reverse(default_name)
    )

def signup_view(request):
    if request.user.is_authenticated:
        return redirect("offers:list")

    next_url = _get_next_url(request)

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)

            return redirect(f"{reverse('accounts:profile_setup')}?next={next_url}")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form, "next": next_url})


@login_required
def profile_setup(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    next_url = _get_next_url(request)

    if request.method == "POST":
        if "skip" in request.POST:
            return redirect(f"{reverse('accounts:add_preferences')}?next={next_url}")

        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect(f"{reverse('accounts:add_preferences')}?next={next_url}")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "accounts/profile_setup.html", {"form": form, "next": next_url})


@login_required
def add_preferences(request):
    next_url = _get_next_url(request)

    if request.method == "POST":
        return redirect(next_url)

    return render(request, "accounts/add_preferences.html", {"next": next_url})