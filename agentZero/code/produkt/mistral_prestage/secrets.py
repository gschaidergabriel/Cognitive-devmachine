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


# ── Drei Mistral-Token, fest verdrahtet fuer die Vorverarbeitung ───────────
# Gabriel 19.08.: alle drei rotieren, damit nie wieder Ratelimit.
_MISTRAL_KEY_NAMES = ("MISTRAL_API_KEY", "MISTRAL2_API_KEY", "MISTRAL3_API_KEY")


def mistral_keys(path: str | None = None) -> list[str]:
    """Alle vorhandenen Mistral-Token, in fester Reihenfolge, ohne Doppel.

    Reihenfolge ist stabil, damit Round-Robin fair ueber die Aufrufe streut.
    Doppelte Werte werden entfernt -- zwei Namen mit demselben Token waeren
    keine zwei Kontingente.
    """
    vals = load_free_api_keys(path)
    keys, seen = [], set()
    for name in _MISTRAL_KEY_NAMES:
        k = vals.get(name)
        if k and k not in seen:
            seen.add(k)
            keys.append(k)
    return keys
