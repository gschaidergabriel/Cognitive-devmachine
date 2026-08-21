"""browser_fern.py -- Bruecke von Zero zum Browser-Dienst auf dem Rechner des
Menschen. Steuert Chrome/Firefox/Brave mit dem echten, angemeldeten Profil.

Der Browser-Dienst hat seine eigenen Tore (Token, nur-Tailscale-Bind) und
protokolliert nach-aussen wirkende Klicks selbst. Zero benutzt die Faehigkeit,
sieht das Token aber nie.

⚠️⭐ MEHRERE RECHNER: gleiche Lehre wie in heimpc.py. Es gab EIN Paar
ZERO_BROWSER_URL/TOKEN -- damit haette Andreas' Sitzung Gabriels Browser
bedient, mit dessen Anmeldungen. Also auch hier: Wirt aus der Nutzerkennung,
Angabe schlaegt Herkunft, keine Vorgabemaschine, und `wirt` steht in jeder
Antwort. Die Wirtswahl selbst liegt in heimpc -- EINE Stelle, an der
entschieden wird, welcher Rechner gemeint ist.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error

from . import heimpc as _heimpc
from .mistral_prestage import secrets as _secrets

_ZEIT = 45

# Wirt -> (URL-Name, Token-Name, alter URL-Name, alter Token-Name)
_ZUGANG = {
    "gabriel-pc": ("ZERO_BROWSER_URL_GABRIEL", "ZERO_BROWSER_TOKEN_GABRIEL",
                   "ZERO_BROWSER_URL", "ZERO_BROWSER_TOKEN"),
    "andreas-maco": ("ZERO_BROWSER_URL_ANDREAS", "ZERO_BROWSER_TOKEN_ANDREAS",
                     None, None),
}


def _zugang(wirt: str):
    vals = _secrets.load_free_api_keys()
    url_neu, token_neu, url_alt, token_alt = _ZUGANG[wirt]
    return (vals.get(url_neu) or (vals.get(url_alt) if url_alt else None),
            vals.get(token_neu) or (vals.get(token_alt) if token_alt else None))


def _ruf(pfad, methode="POST", koerper=None, roh=False, wirt=None, nutzer=None):
    try:
        ziel = _heimpc.wirt_waehlen(wirt, nutzer)
    except _heimpc.KeinWirt as e:
        return {"erreichbar": False, "grund": str(e)}
    url, token = _zugang(ziel)
    if not url or not token:
        return {"erreichbar": False, "wirt": ziel,
                "grund": f"auf {ziel} laeuft kein Browser-Dienst "
                         "(nicht eingerichtet -- nicht mit 'kaputt' verwechseln)"}
    data = json.dumps(koerper).encode() if koerper is not None else None
    kopf = {"X-Zero-Token": token}
    if data:
        kopf["Content-Type"] = "application/json"
    req = urllib.request.Request(url.rstrip("/") + pfad, data=data, method=methode,
                                 headers=kopf)
    try:
        with urllib.request.urlopen(req, timeout=_ZEIT) as r:
            inhalt = r.read()
            if roh:
                return {"erreichbar": True, "wirt": ziel, "bytes": inhalt}
            return {"erreichbar": True, "wirt": ziel,
                    **(json.loads(inhalt or b"{}") if inhalt else {})}
    except urllib.error.HTTPError as e:
        try:
            return {"erreichbar": True, "wirt": ziel, "http": e.code,
                    **json.loads(e.read() or b"{}")}
        except Exception:
            return {"erreichbar": True, "wirt": ziel, "http": e.code}
    except Exception as e:
        return {"erreichbar": False, "wirt": ziel,
                "grund": f"{type(e).__name__}: {e}"[:160]}


def _q(browser):
    return f"?browser={browser}" if browser else ""


def oeffnen(url, browser="", wirt=None, nutzer=None):
    return _ruf("/oeffnen", "POST",
                {"url": url, **({"browser": browser} if browser else {})},
                wirt=wirt, nutzer=nutzer)


def lesen(browser="", wirt=None, nutzer=None):
    return _ruf("/lesen" + _q(browser), "GET", wirt=wirt, nutzer=nutzer)


def screenshot(browser="", wirt=None, nutzer=None):
    return _ruf("/screenshot" + _q(browser), "GET", roh=True, wirt=wirt, nutzer=nutzer)


def klick(selektor=None, x=None, y=None, browser="", wirkt_nach_aussen=False,
          wirt=None, nutzer=None):
    b = {"wirkt_nach_aussen": bool(wirkt_nach_aussen)}
    if browser:
        b["browser"] = browser
    if selektor:
        b["selektor"] = selektor
    elif x is not None and y is not None:
        b["x"], b["y"] = x, y
    return _ruf("/klick", "POST", b, wirt=wirt, nutzer=nutzer)


def tippen(selektor, text, browser="", wirt=None, nutzer=None):
    b = {"selektor": selektor, "text": text}
    if browser:
        b["browser"] = browser
    return _ruf("/tippen", "POST", b, wirt=wirt, nutzer=nutzer)


def formular(felder, absenden_selektor=None, browser="", wirt=None, nutzer=None):
    b = {"felder": felder}
    if absenden_selektor:
        b["absenden_selektor"] = absenden_selektor
    if browser:
        b["browser"] = browser
    return _ruf("/formular_ausfuellen", "POST", b, wirt=wirt, nutzer=nutzer)


def navigieren(richtung="neu_laden", browser="", wirt=None, nutzer=None):
    pfad = {"zurueck": "/zurueck", "vor": "/vor", "neu_laden": "/neu_laden"}.get(richtung)
    if not pfad:
        return {"erreichbar": True, "fehler": f"unbekannte Richtung: {richtung}"}
    return _ruf(pfad, "POST", {"browser": browser} if browser else {},
                wirt=wirt, nutzer=nutzer)
