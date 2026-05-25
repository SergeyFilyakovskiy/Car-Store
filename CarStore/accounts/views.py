from django.contrib.auth import authenticate, login
from django.http import HttpRequest
from django.shortcuts import redirect, render

from .forms import LoginForm, SignUpForm


def signup_view(request: HttpRequest):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = SignUpForm()
    return render(request, "signup.html", {"form": form})


def login_view(request: HttpRequest):
    form = LoginForm(data=request.POST or None)
    if request.POST == "POST":
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(
                username=username,
                password=password,
            )
            if user is not None:
                login(request, user)
                return redirect("home")
    return render(request, "login.html", {"form": form})
