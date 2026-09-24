# django_auth_steps_email_otp

**Status: scaffolding, not a working package.** Extracted (with git history
preserved) from glotronic.net's `src/glotronic/accounts-totp/`, which mixed
TOTP and email-OTP concerns in the same files, written against the old,
now-deleted `glotronic.accounts` system.

There's currently just one form (`EmailOTPForm`) — no view, no code path
that actually generates or sends an email OTP code. That's the real work
still ahead, built against
[`django_auth_steps`](https://github.com/mike-glorioso/django-auth-steps)'s
`AuthMethod`/strategy registry contract.

Shares its origin with
[`django_auth_steps_totp`](https://github.com/mike-glorioso/django-auth-steps_totp) —
both started from the same extraction and were pruned separately afterward,
rather than having independently clean histories.
