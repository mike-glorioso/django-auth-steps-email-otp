from django.urls import include, path

urlpatterns = [
    path("", include("django_auth_steps.urls")),
    path("email-otp/", include("django_auth_steps_email_otp.urls")),
]
