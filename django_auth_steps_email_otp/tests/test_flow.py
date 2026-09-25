import re
from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.utils import timezone
from django_auth_steps.models import UserAuthMethod

from django_auth_steps_email_otp.codes import resend_cooldown_remaining
from django_auth_steps_email_otp.models import EmailOTPCode


def _code_from_email(body: str) -> str:
    match = re.search(r"code is: (\S+)", body)
    assert match is not None, f"no code found in email body: {body!r}"
    return match.group(1)


class OneStepEmailOTPFlowTests(TestCase):
    def setUp(self):
        self.user: User = User.objects.create_user(
            username="mike", password="x", email="mike@example.com"
        )
        UserAuthMethod.objects.create(user=self.user, code="email_otp", order=1)
        self.client.post("/user-select/", {"user_identifier": "mike"})

    def test_display_sends_exactly_one_email_and_creates_one_code(self):
        response = self.client.get("/verify/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["mike@example.com"])
        self.assertEqual(EmailOTPCode.objects.filter(user=self.user).count(), 1)

    def test_a_second_display_while_the_code_is_still_live_sends_nothing_new(self):
        self.client.get("/verify/")
        self.client.get("/verify/")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(EmailOTPCode.objects.filter(user=self.user).count(), 1)

    def test_correct_code_completes_the_flow_and_consumes_the_code(self):
        self.client.get("/verify/")
        code = _code_from_email(str(mail.outbox[0].body))

        response = self.client.post("/verify/", {"code": code}, follow=True)
        self.assertRedirects(response, "/")
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        otp = EmailOTPCode.objects.get(user=self.user)
        self.assertIsNotNone(otp.consumed_at)

    def test_consumed_code_cannot_be_reused(self):
        self.client.get("/verify/")
        code = _code_from_email(str(mail.outbox[0].body))
        self.client.post("/verify/", {"code": code})

        # start a fresh sign-in attempt, reusing the same (now-consumed) code
        self.client.logout()
        self.client.post("/user-select/", {"user_identifier": "mike"})
        response = self.client.post("/verify/", {"code": code})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Incorrect or expired code", response.content)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_wrong_code_fails_and_triggers_the_existing_throttle(self):
        self.client.get("/verify/")

        response = self.client.post("/verify/", {"code": "WRONGCOD"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Incorrect or expired code", response.content)

        user_auth_method = UserAuthMethod.objects.get(user=self.user, code="email_otp")
        self.assertEqual(user_auth_method.throttle_failure_count, 1)

    def test_expired_code_fails_verification(self):
        self.client.get("/verify/")
        code = _code_from_email(str(mail.outbox[0].body))

        EmailOTPCode.objects.filter(user=self.user).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )

        response = self.client.post("/verify/", {"code": code})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Incorrect or expired code", response.content)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class ResendEmailOTPTests(TestCase):
    def setUp(self):
        self.user: User = User.objects.create_user(
            username="mike", password="x", email="mike@example.com"
        )
        UserAuthMethod.objects.create(user=self.user, code="email_otp", order=1)
        self.client.post("/user-select/", {"user_identifier": "mike"})
        self.client.get("/verify/")  # sends the first code

    def test_resend_within_cooldown_sends_nothing_new(self):
        response = self.client.post("/email-otp/resend/", {"next": "/verify/"})

        self.assertRedirects(response, "/verify/")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(EmailOTPCode.objects.filter(user=self.user).count(), 1)

    def test_resend_after_cooldown_sends_a_new_code_and_invalidates_the_old_one(self):
        old_code = _code_from_email(str(mail.outbox[0].body))
        EmailOTPCode.objects.filter(user=self.user).update(
            created_at=timezone.now() - timedelta(seconds=31)
        )

        response = self.client.post("/email-otp/resend/", {"next": "/verify/"})
        self.assertRedirects(response, "/verify/")
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(EmailOTPCode.objects.filter(user=self.user).count(), 2)

        # the old code no longer verifies - only the newest one does
        response = self.client.post("/verify/", {"code": old_code})
        self.assertIn(b"Incorrect or expired code", response.content)

    def test_unsafe_next_falls_back_to_root(self):
        response = self.client.post(
            "/email-otp/resend/", {"next": "https://evil.example.com/phish"}
        )
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_resend_cooldown_remaining_reflects_the_last_send(self):
        remaining = resend_cooldown_remaining(self.user)
        self.assertGreater(remaining, 0)
        self.assertLessEqual(remaining, 30)
