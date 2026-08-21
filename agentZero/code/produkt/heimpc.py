"""heimpc.py -- Bruecke von Zero zu den Rechnern der Menschen.

Zero kann die eigenen Maschinen der Eigner sehen und bedienen: Screenshot,
Tastatur/Maus, Fensterliste, Shell hinter der Schranke. Der Host-Dienst laeuft
auf dem jeweiligen Rechner und hat dort seine eigenen Tore (nur Tailscale,
Token, Schranke, lokaler Zeuge). Diese Datei ruft ihn nur an und sieht die
Token nie im Klartext von Zero aus (secrets.load_free_api_keys liest die
abgeschirmte Datei).

⚠️⭐ MEHRERE RECHNER -- der Fehler vom 21.08., der das hier ausgeloest hat:
Es gab genau EIN Paar ZERO_HOSTAGENT_URL/TOKEN. Andreas fragte in SEINER
Sitzung "welche Fenster sind beim maco offen?", und `pc_ausfuehren` landete auf
GABRIELS Rechner in Siem Reap -- ohne dass irgendwo stand, dass gerade die
falsche Maschine antwortet. Zwei Menschen, ein hartverdrahtetes Ziel: das ist
kein Komfortmangel, das ist eine stille Fehlleitung von Befehlen auf einen
fremden Rechner.

Deshalb jetzt:
  * Jeder Aufruf waehlt einen WIRT. Ohne Angabe ist das der Rechner DESSEN,
    der gerade spricht (Nutzerkennung -> Eigner), nie ein Vorgabegeraet.
  * Wer keinen eigenen Rechner hat (headless Zero, Dienstkennungen), MUSS den
    Wirt benennen. Lieber eine klare Rueckfrage als ein stiller Treffer.
  * Jede Antwort traegt `wirt` -- die angesprochene Maschine steht in der
    Antwort, damit eine Fehlleitung sichtbar ist, statt sich zu verstecken.

Ausfallsicher: ist der Rechner aus oder nicht im Tailnet, liefert jede Funktion
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

# ── Wer gehoert zu welchem Rechner ────────────────────────────────────────
# Diese Zuordnung ist eine Sicherheitsentscheidung und steht deshalb im Code,
# nicht in der fuer Zero lesbaren Karte (/var/lib/clay/karte/wirte.json).
# Die Karte beschreibt, was ein Rechner KANN; hier steht, wem er GEHOERT.
EIGNER_WIRT = {
    "gabriel": "gabriel-pc",
    "andreas": "andreas-maco",
}

# Wirt -> (URL-Name, Token-Name, alter URL-Name, alter Token-Name).
# Die alten, nutzerlosen Namen bleiben als Rueckfall fuer Gabriels Rechner
# gueltig, damit ein halb umgestellter Schluesselstand nichts abwirft.
_ZUGANG = {
    "gabriel-pc": ("ZERO_HOSTAGENT_URL_GABRIEL", "ZERO_HOSTAGENT_TOKEN_GABRIEL",
                   "ZERO_HOSTAGENT_URL", "ZERO_HOSTAGENT_TOKEN"),
    "andreas-maco": ("ZERO_HOSTAGENT_URL_ANDREAS", "ZERO_HOSTAGENT_TOKEN_ANDREAS",
                     None, None),
}

# Schreibweisen, die Menschen und Zero benutzen -> kanonischer Wirtsname.
_ALIAS = {
    "gabriel": "gabriel-pc", "gabriel-pc": "gabriel-pc", "gabriels-pc": "gabriel-pc",
    "frankenstein": "gabriel-pc", "ai-core-node": "gabriel-pc",
    "ai-core-node-projekt-frankenstein": "gabriel-pc",
    "andreas": "andreas-maco", "andreas-maco": "andreas-maco", "maco": "andreas-maco",
    "andreas-mac": "andreas-maco", "andreasmaco": "andreas-maco",
}


class KeinWirt(Exception):
    """Kein Rechner bestimmbar -- der Aufrufer muss einen benennen."""


def wirte() -> list[str]:
    return sorted(_ZUGANG)


def wirt_waehlen(wirt: str | None, nutzer: str | None) -> str:
    """Welche Maschine ist gemeint? Angabe schlaegt Herkunft, Herkunft schlaegt
    nichts -- eine Vorgabemaschine gibt es bewusst NICHT."""
    if wirt:
        name = _ALIAS.get(str(wirt).strip().lower())
        if not name:
            raise KeinWirt(f"unbekannter Rechner: {wirt} (bekannt: {', '.join(wirte())})")
        return name
    name = EIGNER_WIRT.get(str(nutzer or "").strip().lower())
    if not name:
        raise KeinWirt(
            "Kein Rechner zugeordnet -- benenne ihn mit `wirt` ("
            + ", ".join(wirte()) + "). Ohne Angabe wird NICHT geraten: ein "
            "Befehl auf dem falschen Rechner ist schlimmer als eine Rueckfrage.")
    return name


def _zugang(wirt: str) -> tuple[str | None, str | None]:
    vals = _secrets.load_free_api_keys()
    url_neu, token_neu, url_alt, token_alt = _ZUGANG[wirt]
    url = vals.get(url_neu) or (vals.get(url_alt) if url_alt else None)
    token = vals.get(token_neu) or (vals.get(token_alt) if token_alt else None)
    return url, token


def _ruf(pfad: str, methode: str = "GET", koerper: dict | None = None,
         roh: bool = False, wirt: str | None = None,
         nutzer: str | None = None) -> dict:
    try:
        ziel = wirt_waehlen(wirt, nutzer)
    except KeinWirt as e:
        return {"erreichbar": False, "grund": str(e)}
    url, token = _zugang(ziel)
    if not url or not token:
        return {"erreichbar": False, "wirt": ziel,
                "grund": f"fuer {ziel} ist kein Host-Dienst hinterlegt "
                         "(URL/Token fehlen in der abgeschirmten Datei)"}
    data = json.dumps(koerper).encode() if koerper is not None else None
    req = urllib.request.Request(
        url.rstrip("/") + pfad, data=data, method=methode,
        headers={"X-Zero-Token": token,
                 "Content-Type": "application/json"} if data else {"X-Zero-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=_ZEIT) as r:
            inhalt = r.read()
            if roh:
                return {"erreichbar": True, "wirt": ziel, "bytes": inhalt,
                        "typ": r.headers.get("Content-Type", "")}
            return {"erreichbar": True, "wirt": ziel, **json.loads(inhalt or b"{}")}
    except urllib.error.HTTPError as e:
        try:
            return {"erreichbar": True, "wirt": ziel, "http": e.code,
                    **json.loads(e.read() or b"{}")}
        except Exception:
            return {"erreichbar": True, "wirt": ziel, "http": e.code,
                    "fehler": "HTTP-Fehler"}
    except Exception as e:
        return {"erreichbar": False, "wirt": ziel,
                "grund": f"{type(e).__name__}: {e}"[:160]}


def gesundheit(wirt: str | None = None, nutzer: str | None = None) -> dict:
    """Laeuft der Dienst, welche Anzeigeschicht, steht die Schranke, sind die
    Augen wach? Unter Wayland ist `augen` das entscheidende Feld -- ohne
    Erweiterung gibt es kein Bild, und das soll man sehen, bevor man es
    versucht."""
    return _ruf("/gesundheit", wirt=wirt, nutzer=nutzer)


def bildschirme(wirt: str | None = None, nutzer: str | None = None) -> dict:
    """Welche Bildschirme hat der Rechner, wo liegen sie?"""
    return _ruf("/bildschirme", wirt=wirt, nutzer=nutzer)


def fenster(wirt: str | None = None, nutzer: str | None = None) -> dict:
    """Welche Fenster sind offen (Titel, Programm, Bildschirm, Groesse)?"""
    return _ruf("/fenster", wirt=wirt, nutzer=nutzer)


def sehen(bildschirm: str = "", wirt: str | None = None,
          nutzer: str | None = None) -> dict:
    """Ein Bild des Desktops. Liefert die Rohbytes des PNG -- der Aufrufer
    entscheidet, ob er sie speichert oder ueber `bild_ansehen` analysieren
    laesst.

    `bildschirm` leer = die Vorgabe DIESES Rechners: auf Gabriels PC sein
    Schirm 2 (Schirm 1 gehoert ihm), sonst der ganze Schreibtisch. Sonst ein
    Anschlussname ("DP-1"), "1"/"2" nach Gabriels Regel oder "alle".
    """
    if not bildschirm:
        try:
            bildschirm = "2" if wirt_waehlen(wirt, nutzer) == "gabriel-pc" else "alle"
        except KeinWirt:
            bildschirm = "alle"
    return _ruf(f"/bild?bildschirm={bildschirm}", roh=True, wirt=wirt, nutzer=nutzer)


def eingabe(typ: str, wirt: str | None = None, nutzer: str | None = None,
            **rest: Any) -> dict:
    """Tastatur/Maus: typ = tippen|taste|maus|klick. Der Host-Dienst spritzt
    echte Eingabeereignisse -- fuer jede App wie ein Mensch."""
    return _ruf("/eingabe", "POST", {"typ": typ, **rest}, wirt=wirt, nutzer=nutzer)


def ausfuehren(befehl: str, frist: int = 120, wirt: str | None = None,
               nutzer: str | None = None) -> dict:
    """Einen Shell-Befehl auf dem Rechner des Menschen. ⚠️ Zerstoerendes weist
    die Schranke des Dienstes ab und verlangt einen am Terminal getippten
    Schein -- das ist gewollt und wird hier nicht umgangen."""
    return _ruf("/ausfuehren", "POST", {"befehl": befehl, "frist": frist},
                wirt=wirt, nutzer=nutzer)
