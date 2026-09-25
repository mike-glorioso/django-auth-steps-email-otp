from django.urls import path

from .views import ResendEmailOTPView

app_name = "django_auth_steps_email_otp"

urlpatterns = [
    path("resend/", ResendEmailOTPView.as_view(), name="resend"),
]
