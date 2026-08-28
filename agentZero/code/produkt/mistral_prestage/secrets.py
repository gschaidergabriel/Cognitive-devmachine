from __future__ import annotations

# ⭐⭐⭐ WURZELFIX (2026-08-22, kontrollierte Kanarie-Verifikation, Gabriel):
# `python-dotenv` steht NUR in `venv-test`, nicht auf dem nackten
# `/usr/bin/python3`, mit dem `eos-architekt.service`/`architekt-schleife.sh`/
# `architekt/blog_lauf.py` auf dem WIRT laufen. Ein unbedingter `from dotenv
# import ...` liess JEDEN Wirt-seitigen Aufrufpfad, der -- auch nur
# transitiv -- hier hindurchlief (z.B. architekt/lauf.py -> clayverse.
# mistral_prestage.pipeline -> ...innenraum -> secrets), mit
# `ModuleNotFoundError: dotenv` abstuerzen. `clayverse/architekt_blog.py`
# wich diesem Modul deshalb bisher komplett aus und dupliziert dieselbe
# Parse-Logik selbst (siehe dortiger Kommentar "kein dotenv auf dem Wirt")
# -- Leitsatz "Umstellen statt anbauen": die Wiederverwendung gehoert
# HIERHER, in die Wurzel, nicht in jeden Aufrufer einzeln dupliziert.
# Fix: `dotenv` bleibt der Erstweg (identisches Verhalten, wo verfuegbar),
# faellt aber GRACEFUL auf einen minimalen Hand-Parser zurueck (dieselbe
# Logik wie `architekt_blog.py:_lade_freie_zugaenge`), statt beim blossen
# Importieren dieses Moduls abzustuerzen.
try:
    from dotenv import dotenv_values as _dotenv_values
except ImportError:  # kein venv, z.B. Wirt-seitiger eos-architekt.service
    _dotenv_values = None

DEFAULT_PATH = "/etc/clayverse/freie-zugaenge.env"


def _dotenv_values_ohne_paket(pfad: str) -> dict[str, str]:
    """Minimaler Fallback-Parser (kein `python-dotenv` installiert) --
    einfache `SCHLUESSEL=WERT`-Zeilen, `#`-Kommentare/Leerzeilen
    uebersprungen. Deckt genau das ab, was `/etc/clayverse/freie-
    zugaenge.env` tatsaechlich enthaelt (keine Anfuehrungszeichen-
    Verarbeitung, kein Multiline -- dieselbe Einschraenkung, die
    `architekt_blog.py`s Version schon hatte, hier nur an einer Stelle,
    nicht dupliziert)."""
    werte: dict[str, str] = {}
    try:
        with open(pfad, encoding="utf-8") as f:
            for zeile in f:
                zeile = zeile.strip()
                if zeile and not zeile.startswith("#") and "=" in zeile:
                    k, v = zeile.split("=", 1)
                    if v.strip():
                        werte[k.strip()] = v.strip()
    except OSError:
        pass
    return werte


def load_free_api_keys(path: str | None = None) -> dict[str, str]:
    """Read-only load of the free-API credential file.

    Values are returned to the caller for immediate one-shot use and must
    never be printed, logged, persisted, or committed (project rule). This
    module does not mutate process environment -- it reads the file fresh
    on every call, independent of whatever service.py does at startup.

    Uses `python-dotenv` where available (unchanged behaviour), falls back
    to `_dotenv_values_ohne_paket` on the bare-python3 host path (see
    module-head WURZELFIX) -- never crashes on import alone.
    """
    pfad = path or DEFAULT_PATH
    values = _dotenv_values(pfad) if _dotenv_values is not None else _dotenv_values_ohne_paket(pfad)
    return {k: v for k, v in values.items() if v}


# ── Mistral-Token, fest verdrahtet fuer die Vorverarbeitung ───────────────
# Gabriel 19.08.: alle drei rotieren, damit nie wieder Ratelimit.
#
# KORREKTUR 2026-08-22 (gemessen, nicht vermutet -- Sonde gegen
# https://api.mistral.ai/v1/models, ein Aufruf pro Schluessel, keine
# Tokenkosten): MISTRAL_API_KEY liefert HTTP 402 "Check your subscription"
# -- kein Abo mehr, keine Ratenlage, die sich erholt. transport.py rotiert
# 402 zwar bereits pro Anfrage weg (_PRO_SCHLUESSEL), aber das verbrennt bei
# JEDEM Aufruf zuerst einen sicher toten Versuch auf Schluessel 1, bevor
# Schluessel 2/3 drankommen -- unnoetig, wenn der Ausfall schon bekannt ist.
# Deckt sich mit dem bereits an anderer Stelle dokumentierten Befund
# (clayverse/omnimind_anreicherung.py: "NIE MISTRAL_API_KEY"). Also HIER
# an der Wurzel (secrets.mistral_keys() ist der gemeinsame Pool fuer
# prestage/innenraum/translator/motor_kaskade): nur die lebenden zwei sind
# der Fallback-Pool. MISTRAL2_API_KEY/MISTRAL3_API_KEY beide 200 OK,
# dieselbe Minute gemessen -- Rotation bleibt zwischen den beiden bestehen.
_MISTRAL_KEY_NAMES = ("MISTRAL2_API_KEY", "MISTRAL3_API_KEY")


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
