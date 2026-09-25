from django.http import HttpRequest
from django_auth_steps.base_form_handler import BaseFormHandler
from django_auth_steps.registry import AuthMethod, register_strategy
from django_auth_steps.strategies.enroll_strategy import EnrollStrategy
from django_auth_steps.strategies.verify_strategy import VerifyStrategy
from django_auth_steps.utils import get_pending_verification_user

from .codes import send_if_none_live, verify_and_consume_code
from .form_handlers import EmailOTPFormHandler


class _EmailOTPStrategyMixin:
    """Shared by EmailOTPEnrollStrategy and EmailOTPVerifyStrategy: there's
    no separate one-time setup step the way TOTP needs a QR scan - email
    OTP enrollment and verification are the same send-a-code/check-it
    flow, against whatever email address the user already has."""

    @property
    def html(self) -> str:
        return "email_otp_verify.html"

    def get_form_handler(self) -> BaseFormHandler:
        return EmailOTPFormHandler()

    def on_display(self, request: HttpRequest, form_handler: BaseFormHandler) -> None:
        user = get_pending_verification_user(request)
        send_if_none_live(user)

    def execute(self, request: HttpRequest, form_handler: BaseFormHandler) -> None:
        form = form_handler.get_form()
        submitted_code = form.cleaned_data["code"]
        user = get_pending_verification_user(request)
        if not verify_and_consume_code(user, submitted_code):
            form_handler.add_error("code", "Incorrect or expired code.")
            form_handler.set_execution_state(False)
            return
        form_handler.set_execution_state(True)


class EmailOTPEnrollStrategy(_EmailOTPStrategyMixin, EnrollStrategy):
    pass


class EmailOTPVerifyStrategy(_EmailOTPStrategyMixin, VerifyStrategy):
    pass


def register(*, permission: str | None = None) -> bool:
    return register_strategy(
        AuthMethod(
            code="email_otp",
            label="Email code",
            permission=permission,
            is_enrolled=lambda user: bool(user.email),
            enroll_strategy=EmailOTPEnrollStrategy(),
            verify_strategy=EmailOTPVerifyStrategy(),
        )
    )
