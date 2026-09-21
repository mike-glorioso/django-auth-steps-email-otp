
from django.forms import CharField, EmailField, Form, TextInput


class LoginForm(Form):
    """Step 1: identify by email, plus TOTP code — except on a brand-new
    account with no device enrolled yet, where the token field is left
    blank (there's nothing to check yet; the email code that follows is
    what bootstraps first-time TOTP enrollment instead)."""

    email = EmailField()
    totp_token = CharField(
        label="Authenticator code",
        max_length=6,
        min_length=6,
        required=False,
        widget=TextInput(attrs={"autocomplete": "one-time-code", "inputmode": "numeric"}),
    )


class TOTPTokenForm(Form):
    token = CharField(
        label="Authentication code",
        max_length=6,
        min_length=6,
        widget=TextInput(attrs={"autocomplete": "one-time-code", "inputmode": "numeric"}),
    )


class EmailOTPForm(Form):
    code = CharField(
        label="Code from your email",
        max_length=8,
        min_length=8,
        widget=TextInput(attrs={"autocomplete": "one-time-code", "autocapitalize": "characters"}),
    )

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()
