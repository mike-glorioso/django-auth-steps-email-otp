from django.utils.datastructures import MultiValueDict
from django_auth_steps.base_form_handler import BaseFormHandler

from .forms import EmailOTPForm


class EmailOTPFormHandler(BaseFormHandler):
    def fill_form_from_none(self) -> None:
        self.set_form(EmailOTPForm())

    def fill_form_from_request_data(self, data: MultiValueDict[str, str]) -> None:
        self.set_form(EmailOTPForm(data))
