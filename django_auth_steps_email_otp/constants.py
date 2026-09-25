CODE_LENGTH = 8
# Excludes visually-ambiguous characters (0/O, 1/I/L) - this code is
# hand-typed from an email, unlike a TOTP code copied from an app.
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

DEFAULT_EXPIRY_SECONDS = 60 * 10  # 10 minutes
DEFAULT_RESEND_COOLDOWN_SECONDS = 30
