#!/usr/bin/env python3
"""Fail-closed provider admission for the bounded ClayCog paid-training lane."""
import os

EXECUTION_MODE_ENV = "CLAY_EXECUTION_MODE"
PAID_PROVIDER_AUTH_ENV = "CLAYCOG_PAID_PROVIDER_AUTHORIZATION"
FREE_ONLY_MODE = "FREE_ONLY"
PAID_AUTHORIZED_MODE = "PAID_AUTHORIZED"
PAID_PROVIDER_AUTH_VALUE = "OWNER_AUTHORIZED_QWEN35_08B_PREFLIGHT_V1"


def require_together_paid_provider_admission(environ=None):
    """Reject paid-provider contact by default, before secret lookup or network I/O."""
    env = os.environ if environ is None else environ
    mode = env.get(EXECUTION_MODE_ENV, FREE_ONLY_MODE)
    if type(mode) is not str:
        raise SystemExit("PROVIDER_MODE_REJECTED execution mode must be an exact string")
    if mode == FREE_ONLY_MODE:
        raise SystemExit(
            "FREE_ONLY_PROVIDER_BLOCK Together is PAID/SUBSCRIPTION; "
            "blocked before provider secret lookup and network I/O"
        )
    if mode != PAID_AUTHORIZED_MODE:
        raise SystemExit(f"PROVIDER_MODE_REJECTED unsupported execution mode {mode!r}")
    authorization = env.get(PAID_PROVIDER_AUTH_ENV, "")
    if type(authorization) is not str or authorization != PAID_PROVIDER_AUTH_VALUE:
        raise SystemExit(
            "PAID_PROVIDER_AUTHORIZATION_REQUIRED exact owner-authorized preflight token missing"
        )
    return {
        "execution_mode": PAID_AUTHORIZED_MODE,
        "provider": "together",
        "provider_class": "PAID",
        "authorization": "EXPLICIT_PREFLIGHT_ADMISSION",
    }
