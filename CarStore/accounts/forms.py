from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from accounts.models import User


class SignUpForm(UserCreationForm):
    """
    User register form
    """

    email = forms.EmailField(max_length=256, help_text="Required field. Enter email.")

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
