from __future__ import annotations

import os


_MAX_MODEL_CHARS = 256
_MAX_TOKEN_CHARS = 16_384


def validate_final_mistral_runtime_config() -> str:
    """Validate non-persistent Mistral config for the final sandbox probe.

    Final acceptance must bind a fixed provider model identity rather than a moving
    ``*-latest`` alias. The bearer secret must also be representable as a single
    visible-ASCII HTTP header value. The secret is intentionally read only for this
    validation and the local reference is scrubbed before any validation error is
    raised; the value is never returned or persisted by this helper.
    """

    model = os.environ.get("CLAYVERSE_MISTRAL_MODEL", "")
    model_invalid = (
        not model
        or model != model.strip()
        or len(model) > _MAX_MODEL_CHARS
        or any(ord(char) < 0x21 or ord(char) > 0x7E for char in model)
        or model.lower().endswith("-latest")
    )

    token = os.environ.get("MISTRAL_API_KEY", "")
    token_invalid = (
        not token
        or len(token) > _MAX_TOKEN_CHARS
        or any(ord(char) < 0x21 or ord(char) > 0x7E for char in token)
    )
    token = ""

    if model_invalid:
        raise RuntimeError(
            "final Mistral acceptance requires a fixed visible-ASCII model identifier"
        )
    if token_invalid:
        raise RuntimeError(
            "MISTRAL_API_KEY is missing or invalid for final acceptance"
        )
    return model
