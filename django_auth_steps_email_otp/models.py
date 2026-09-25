from __future__ import annotations

from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db.models import CASCADE, CharField, DateTimeField, ForeignKey, Model
from django.utils import timezone


class EmailOTPCode(Model):
    # settings.AUTH_USER_MODEL (a string), not a hardcoded concrete User
    # class, so the FK stays swappable-safe - same reasoning as
    # django_auth_steps.models.UserAuthMethod.
    user: ForeignKey[AbstractUser, AbstractUser] = ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="email_otp_codes"
    )
    # Hashed via django.contrib.auth.hashers.make_password/check_password -
    # the plaintext code is never stored, same as a real password.
    code_hash: CharField[str, str] = CharField(max_length=128)
    created_at: DateTimeField[datetime, datetime] = DateTimeField(auto_now_add=True)
    expires_at: DateTimeField[datetime, datetime] = DateTimeField()
    consumed_at: DateTimeField[datetime | None, datetime | None] = DateTimeField(
        null=True, blank=True, default=None
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} - code created {self.created_at}"

    def is_live(self) -> bool:
        """Not consumed yet, and not expired."""
        return self.consumed_at is None and timezone.now() < self.expires_at
