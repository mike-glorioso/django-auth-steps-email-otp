import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.utils import timezone

from .constants import (
    CODE_ALPHABET,
    CODE_LENGTH,
    DEFAULT_EXPIRY_SECONDS,
    DEFAULT_RESEND_COOLDOWN_SECONDS,
)
from .models import EmailOTPCode


def _expiry_seconds() -> int:
    return getattr(settings, "EMAIL_OTP_EXPIRY_SECONDS", DEFAULT_EXPIRY_SECONDS)


def _resend_cooldown_seconds() -> int:
    return getattr(settings, "EMAIL_OTP_RESEND_COOLDOWN_SECONDS", DEFAULT_RESEND_COOLDOWN_SECONDS)


def _generate_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def _latest_code(user: AbstractUser) -> EmailOTPCode | None:
    return EmailOTPCode.objects.filter(user=user).order_by("-created_at").first()


def send_new_code(user: AbstractUser) -> EmailOTPCode:
    """Unconditionally generates, stores (hashed), and emails a fresh
    code. Callers decide when this is allowed - see send_if_none_live()
    and resend_code()/resend_cooldown_remaining() below; nothing here
    enforces cooldown or liveness on its own."""
    code = _generate_code()
    otp = EmailOTPCode.objects.create(
        user=user,
        code_hash=make_password(code),
        expires_at=timezone.now() + timedelta(seconds=_expiry_seconds()),
    )
    send_mail(
        subject="Your verification code",
        message=(
            f"Your verification code is: {code}\n\n"
            f"This code expires in {_expiry_seconds() // 60} minutes."
        ),
        from_email=None,  # falls back to settings.DEFAULT_FROM_EMAIL
        recipient_list=[user.email],
    )
    return otp


def send_if_none_live(user: AbstractUser) -> EmailOTPCode | None:
    """For on_display: sends a fresh code only if there's no still-live
    one, so refreshing the verify/enroll page doesn't send a new email
    on every GET as long as the previous code is still usable. Returns
    None (no-op) if a live code already exists."""
    latest = _latest_code(user)
    if latest is not None and latest.is_live():
        return None
    return send_new_code(user)


def resend_cooldown_remaining(user: AbstractUser) -> float:
    """Seconds still required before an explicit resend is allowed. 0
    or less means allowed right now. Independent of code liveness -
    this guards against resend-spam (mail-bombing), not against the
    code itself expiring."""
    latest = _latest_code(user)
    if latest is None:
        return 0.0
    elapsed = (timezone.now() - latest.created_at).total_seconds()
    return max(0.0, _resend_cooldown_seconds() - elapsed)


def resend_code(user: AbstractUser) -> EmailOTPCode | None:
    """Explicit resend: always sends a fresh code (implicitly
    invalidating any still-live one, since verify_and_consume_code only
    ever checks the latest), unless still within the resend cooldown -
    in which case this is a no-op and returns None."""
    if resend_cooldown_remaining(user) > 0:
        return None
    return send_new_code(user)


def verify_and_consume_code(user: AbstractUser, submitted_code: str) -> bool:
    """Checks submitted_code against the user's latest live code. On a
    match, marks it consumed (so it can't be replayed) and returns
    True; otherwise returns False without changing anything."""
    latest = _latest_code(user)
    if latest is None or not latest.is_live():
        return False
    if not check_password(submitted_code, latest.code_hash):
        return False

    latest.consumed_at = timezone.now()
    latest.save(update_fields=["consumed_at"])
    return True
