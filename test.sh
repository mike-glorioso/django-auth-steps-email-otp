#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

PYTHON="$(cd .venv/bin && pwd)/python3"

DJANGO_SETTINGS_MODULE=django_auth_steps_email_otp.tests.settings \
    "$PYTHON" -m django test django_auth_steps_email_otp.tests.test_flow -v 2
