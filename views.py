import base64
from io import BytesIO

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django_otp import login as otp_login
from django_otp.plugins.otp_totp.models import TOTPDevice


class TtopVerifyView(View):
    def get(request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated and request.user.is_verified():  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]  # django_otp's OTPMiddleware attaches is_verified() at runtime; no stubs know about it
            return redirect("accounts:home")

        if request.method == "POST":
            form = LoginForm(request.POST)
            if form.is_valid():
                user_identifier = form.cleaned_data["user_identifier"]
                user = User.objects.filter(username__iexact=user_identifier).first()
                generic_error = "User not found."

                if user is None:
                    form.add_error(None, generic_error)
                    return render(request, "accounts/login.html", {"form": form})

                request.session[PENDING_USER_KEY] = user.pk
                request.session[PENDING_STAGE_KEY] = "verify"
                method = UserAuthMethod.objects.filter(user=user).first()
                if method is None:
                    form.add_error(None, "No auth method found.")
                    return render(request, "accounts/login.html", {"form": form})
                request.session[NEXT_VERIFICATION_METHOD] = method.code
                return redirect("accounts:verify_next")
        else:
            _clear_pending_login(request)
            form = LoginForm()

        return render(request, "accounts/login.html", {"form": form})


def _clear_pending_login(request: HttpRequest) -> None:
    for key in (PENDING_USER_KEY, PENDING_STAGE_KEY, NEXT_VERIFICATION_METHOD, VERIFIED_METHODS):
        request.session.pop(key, None)


class TotpEnrollView(View):
    @login_required
    def get(request: HttpRequest) -> HttpResponse:
        user = request.user
        if TOTPDevice.objects.filter(user=user, confirmed=True).exists():
            return redirect("accounts:staff_home")

        device, _ = TOTPDevice.objects.get_or_create(
            user=user, confirmed=False, defaults={"name": "default"}
        )

        qr_img = qrcode.make(device.config_url)
        buf = BytesIO()
        qr_img.save(buf, format="PNG")  # type: ignore[reportCallIssue]  # qrcode has no type stubs; this is a documented, working call
        qr_data_uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

        if request.method == "POST":
            form = TOTPTokenForm(request.POST)
            if form.is_valid():
                if device.verify_token(form.cleaned_data["token"]):
                    device.confirmed = True
                    device.save()
                    otp_login(request, device)
                    messages.success(request, "Two-factor authentication is now enabled.")
                    return redirect("accounts:staff_home")
                form.add_error("token", "Invalid or expired code.")
        else:
            form = TOTPTokenForm()

        secret = base64.b32encode(device.bin_key).decode()
        return render(
            request,
            "accounts/setup.html",
            {"form": form, "qr_data_uri": qr_data_uri, "secret": secret},
        )

totp_view_pair = ViewPairPresentation(
    enroll_view=TotpEnrollView,
    verify_view=TotpVerifyView,
)
