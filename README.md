# django_auth_steps_email_otp

An email one-time-code enroll/verify step for
[`django_auth_steps`](https://github.com/mike-glorioso/django-auth-steps).
Sends an 8-character code to the user's existing email address, gated
behind `django_auth_steps`'s own routing, throttling, and session
handling — this package only supplies the step itself.

## Usage

```python
INSTALLED_APPS = [
    ...,
    "django_auth_steps",
    "django_auth_steps_email_otp",
]
```

That's it for registration — `django_auth_steps_email_otp`'s `apps.py`
registers an `email_otp` method (permission `None`) automatically on
startup, the same way `django_auth_steps`'s own `passphrase` method
registers itself. Give a user a `UserAuthMethod` row with
`code="email_otp"` and they'll be routed through it by
`django_auth_steps`'s existing `/enroll/`/`/verify/` views — nothing
else to wire up.

Enrollment and verification are the same flow here: there's no separate
one-time setup step (unlike TOTP, which needs a QR-code scan) — a user
is considered enrolled as soon as they have a usable email address
(`is_enrolled=lambda user: bool(user.email)`).

### Settings

```python
EMAIL_OTP_EXPIRY_SECONDS = 600        # default: 10 minutes
EMAIL_OTP_RESEND_COOLDOWN_SECONDS = 30  # default: 30 seconds
```

Both optional; the defaults above apply if unset.

### Resend

A plain, server-rendered "Resend code" button ships in the default
template (`email_otp_verify.html`) — full page reload, no JS, matching
the rest of this package. It posts to `django_auth_steps_email_otp`'s
own `resend/` URL (mount it wherever you like, e.g.
`path("auth/email-otp/", include("django_auth_steps_email_otp.urls"))`)
and is rate-limited by `EMAIL_OTP_RESEND_COOLDOWN_SECONDS` — a request
inside the cooldown window is a silent no-op, not an error.

Want a JS-driven resend (a countdown button, `fetch()`-based, etc.)
instead of the shipped page-reload version? Don't fight the shipped
view — call the underlying functions directly from your own thin view:

```python
from django_auth_steps_email_otp.codes import resend_code, resend_cooldown_remaining

# resend_cooldown_remaining(user) -> float: seconds until another
# resend is allowed (0 or less means allowed now) - read this to seed
# a countdown.
#
# resend_code(user) -> EmailOTPCode | None: sends a fresh code and
# returns it, or returns None (no-op) if still within the cooldown.
```

Both are plain functions with no Django view/request coupling, so they
work equally well from a traditional view or a DRF/ninja/whatever JSON
endpoint you build yourself.

## Status

Real: code generation (8 chars, excludes visually-ambiguous characters
since it's hand-typed from an email), hashed storage
(`django.contrib.auth.hashers`, never stored in plaintext), expiry,
resend with cooldown, and full test coverage
(`django_auth_steps_email_otp/tests/`, run via `./test.sh`) — sending,
skipping a redundant send while a code is still live, verifying,
consuming (can't be replayed), wrong-code throttling (via
`django_auth_steps`'s existing `UserAuthMethod`), expiry, and resend.

Extracted from an internal project (glotronic.net), with full commit
history preserved via `git subtree split`.

## License

BSD-3-Clause — see [LICENSE](LICENSE).
