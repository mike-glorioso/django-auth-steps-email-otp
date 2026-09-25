from django.http import HttpRequest, HttpResponseBase
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django_auth_steps.constants import DJANGO_AUTH_STEPS_USER_SELECT
from django_auth_steps.errors import UserNotFoundError
from django_auth_steps.utils import clear_pending_user, get_pending_verification_user

from .codes import resend_code


class ResendEmailOTPView(View):
    """POST-only, deliberately: a resend is a real side effect (sends an
    email), so it shouldn't be reachable by a GET/prefetch. Ships as a
    plain server-rendered redirect, matching the rest of this package -
    a consumer wanting an AJAX/fetch()-driven resend button should call
    django_auth_steps_email_otp.codes.resend_code()/
    resend_cooldown_remaining() directly from their own thin view
    instead of using this one."""

    def post(self, request: HttpRequest) -> HttpResponseBase:
        try:
            user = get_pending_verification_user(request)
        except UserNotFoundError:
            clear_pending_user(request)
            return redirect(DJANGO_AUTH_STEPS_USER_SELECT)

        resend_code(user)

        next_url = request.POST.get("next") or "/"
        if not url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            next_url = "/"
        return redirect(next_url)
