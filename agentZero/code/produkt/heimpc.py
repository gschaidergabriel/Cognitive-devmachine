"""heimpc.py -- die Bruecke von Zero (im Behaelter, auf dem VPS) zum
Host-Dienst auf dem Rechner des Menschen (sehen/eingeben/ausfuehren).

Der Host-Dienst laeuft auf dem PC hinter der Tailscale-Adresse; er hat seine
eigenen Tore (nur Tailscale, Token, Schranke, lokaler Zeuge -- siehe
~/zero-hostagent/hostagent.py). Diese Bruecke ruft ihn nur an; die Sicherheit
sitzt am Dienst, nicht hier.

⚠️ Das Token wird aus `freie-zugaenge.env` gelesen (secrets.load_free_api_keys)
-- derselbe gegen Zero abgeschirmte Weg wie die freien API-Schluessel. Zero
BENUTZT die Faehigkeit ueber diese Werkzeuge, bekommt das Token aber nie zu
sehen: der fence_hook sperrt das Lesen der Datei, und keine Funktion hier gibt
es zurueck. So kann Zero den PC bedienen, aber nicht das Token herausloesen, um
an den Toren des Dienstes vorbei etwas anderes zu tun.

Ausfallsicher: ist der PC aus oder nicht im Tailnet, liefert jede Funktion
`{"erreichbar": false, ...}` statt eine Ausnahme -- ein abgeschalteter Heim-PC
darf keinen Zug kippen.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any

from .mistral_prestage import secrets as _secrets

_ZEIT = 30


def _zugang() -> tuple[str | None, str | None]:
    vals = _secrets.load_free_api_keys()
    return vals.get("ZERO_HOSTAGENT_URL"), vals.get("ZERO_HOSTAGENT_TOKEN")


def _ruf(pfad: str, methode: str = "GET", koerper: dict | None = None,
         roh: bool = False) -> dict:
    url, token = _zugang()
    if not url or not token:
        return {"erreichbar": False, "grund": "kein Host-Dienst konfiguriert "
                "(ZERO_HOSTAGENT_URL/TOKEN fehlen)"}
    data = json.dumps(koerper).encode() if koerper is not None else None
    req = urllib.request.Request(
        url.rstrip("/") + pfad, data=data, method=methode,
        headers={"X-Zero-Token": token,
                 "Content-Type": "application/json"} if data else {"X-Zero-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=_ZEIT) as r:
            inhalt = r.read()
            if roh:
                return {"erreichbar": True, "bytes": inhalt,
                        "typ": r.headers.get("Content-Type", "")}
            return {"erreichbar": True, **json.loads(inhalt or b"{}")}
    except urllib.error.HTTPError as e:
        try:
            return {"erreichbar": True, "http": e.code,
                    **json.loads(e.read() or b"{}")}
        except Exception:
            return {"erreichbar": True, "http": e.code, "fehler": "HTTP-Fehler"}
    except Exception as e:
        return {"erreichbar": False, "grund": f"{type(e).__name__}: {e}"[:160]}


def bildschirme() -> dict:
    """Welche Bildschirme hat der Rechner, wo liegen sie? Bildschirm 2 = der
    grosse, auf dem Zero arbeiten darf; Bildschirm 1 (primary) gehoert dem
    Menschen und bleibt unangetastet."""
    return _ruf("/bildschirme")


def sehen(bildschirm: str = "2") -> dict:
    """Ein Bild des Desktops. Vorgabe Bildschirm 2 (der des Menschen bleibt
    aussen vor). Liefert die Rohbytes des PNG -- der Aufrufer entscheidet, ob
    er sie speichert oder ueber `bild_ansehen` (Retina) analysieren laesst."""
    return _ruf(f"/bild?bildschirm={bildschirm}", roh=True)


def eingabe(typ: str, **rest: Any) -> dict:
    """Tastatur/Maus: typ = tippen|taste|maus|klick. Der Dienst spritzt echte
    X11-Ereignisse -- fuer jede App wie ein Mensch. Sichtbares gehoert auf
    Bildschirm 2."""
    return _ruf("/eingabe", "POST", {"typ": typ, **rest})


def ausfuehren(befehl: str, frist: int = 120) -> dict:
    """Einen Shell-Befehl auf dem Rechner des Menschen. ⚠️ Zerstoerendes weist
    die Schranke des Dienstes ab und verlangt einen am Terminal getippten
    Schein -- das ist gewollt und wird hier nicht umgangen."""
    return _ruf("/ausfuehren", "POST", {"befehl": befehl, "frist": frist})
