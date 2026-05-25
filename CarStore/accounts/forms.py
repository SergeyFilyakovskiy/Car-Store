from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from accounts.models import User


class SignUpForm(UserCreationForm):
    """
    Форма регистрации пользователя
    """

    email = forms.EmailField(
        max_length=256, help_text="Обязательное поле. Введите email."
    )

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Имя пользователя")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)
