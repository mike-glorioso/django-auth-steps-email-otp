from django.apps import AppConfig


class DjangoAuthStepsEmailOtpConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_auth_steps_email_otp"

    def ready(self) -> None:
        from .strategy import register

        register()
