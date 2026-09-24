from django.forms import CharField, Form, TextInput


class EmailOTPForm(Form):
    code = CharField(
        label="Code from your email",
        max_length=8,
        min_length=8,
        widget=TextInput(attrs={"autocomplete": "one-time-code", "autocapitalize": "characters"}),
    )

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()
