from __future__ import annotations

from dotenv import dotenv_values

DEFAULT_PATH = "/etc/clayverse/freie-zugaenge.env"


def load_free_api_keys(path: str | None = None) -> dict[str, str]:
    """Read-only load of the free-API credential file.

    Values are returned to the caller for immediate one-shot use and must
    never be printed, logged, persisted, or committed (project rule). This
    module does not mutate process environment -- it reads the file fresh
    on every call, independent of whatever service.py does at startup.
    """
    values = dotenv_values(path or DEFAULT_PATH)
    return {k: v for k, v in values.items() if v}
