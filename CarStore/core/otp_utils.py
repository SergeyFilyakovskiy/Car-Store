import random

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail


def generate_and_send_otp(user):
    """Generates a 6-digit code, saves it to the cache, and sends it via email."""

    otp = str(random.randint(100000, 999999))

    otp_key = f"otp_code_{user.id}"
    attempts_key = f"otp_attempts_{user.id}"

    cache.set(otp_key, otp, timeout=300)
    cache.set(attempts_key, 0, timeout=300)

    subject = "Your verification code"
    message = f"Your one-time login code: {otp}\n The code is valid for 5 minutes."

    send_mail(
        subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False
    )


def verify_otp(user, entered_otp):
    otp_key = f"otp_key{user.id}"
    attempts_key = f"otp_attempts_{user.id}"

    valid_otp = cache.get(otp_key)
    attempts = cache.get(attempts_key, 0)

    if attempts >= 5:
        cache.delete(otp_key)
        return False, "Too many attempts. Code voided; please log in."

    if not valid_otp:
        return False, "The code has expired or was not found."

    if entered_otp != valid_otp:
        cache.set(attempts_key, attempts + 1, timeout=300)
        return False, "Invalid code."

    cache.delete(otp_key)
    cache.delete(attempts_key)
    return True, None


def generate_email_change_otp(user):
    """Generate OTP for email change verification."""

    otp = f"{random.randint(0, 999999): 06d}"

    otp_key = f"email_change_otp_{user.id}"
    attempts_key = f"email_change_attempts_{user.id}"

    cache.set(otp_key, otp, timeout=300)
    cache.delete(attempts_key)

    send_mail(
        subject="Confirm your new email address",
        message=f"Your conrimation code: {otp}\nValid for 5 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.pending_email],
        fail_silently=False,
    )

    return otp


def verify_email_change_otp(user, entered_otp):
    """Verify OTP for email change"""

    otp_key = f"email_change_otp_{user.id}"
    attempts_key = f"email_change_attempts_{user.id}"

    valid_otp = cache.get(otp_key)
    attempts = cache.get(attempts_key, 0)

    if attempts >= 5:
        cache.delete(otp_key)
        return False, "Too many attempts. Request a new code."

    if not valid_otp:
        return False, "Code expired or not found. Request a new code."

    if entered_otp != valid_otp:
        cache.set(attempts_key, attempts + 1, timeout=300)
        return False, f"Invalid code. Attempts left: {5 - attempts}"

    cache.delete(otp_key)
    cache.delete(attempts_key)
    return True, None
