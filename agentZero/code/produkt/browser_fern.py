"""browser_fern.py -- Bruecke von Zero zum Browser-Dienst auf dem Rechner des
Menschen. Steuert Chrome/Firefox/Brave mit dem echten, angemeldeten Profil,
Fenster auf Bildschirm 2. Gleiches Muster wie heimpc.py: Token aus
freie-zugaenge.env (gegen Zero abgeschirmt), nur ueber Tailscale, ausfallsicher.

Der Browser-Dienst hat seine eigenen Tore (Token, nur-Tailscale-Bind) und
protokolliert nach-aussen wirkende Klicks selbst. Zero benutzt die Faehigkeit,
sieht das Token aber nie.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error

from .mistral_prestage import secrets as _secrets

_ZEIT = 45


def _zugang():
    v = _secrets.load_free_api_keys()
    return v.get("ZERO_BROWSER_URL"), v.get("ZERO_BROWSER_TOKEN")


def _ruf(pfad, methode="POST", koerper=None, roh=False):
    url, token = _zugang()
    if not url or not token:
        return {"erreichbar": False, "grund": "kein Browser-Dienst konfiguriert"}
    data = json.dumps(koerper).encode() if koerper is not None else None
    kopf = {"X-Zero-Token": token}
    if data:
        kopf["Content-Type"] = "application/json"
    req = urllib.request.Request(url.rstrip("/") + pfad, data=data, method=methode, headers=kopf)
    try:
        with urllib.request.urlopen(req, timeout=_ZEIT) as r:
            inhalt = r.read()
            if roh:
                return {"erreichbar": True, "bytes": inhalt}
            return {"erreichbar": True, **(json.loads(inhalt or b"{}") if inhalt else {})}
    except urllib.error.HTTPError as e:
        try:
            return {"erreichbar": True, "http": e.code, **json.loads(e.read() or b"{}")}
        except Exception:
            return {"erreichbar": True, "http": e.code}
    except Exception as e:
        return {"erreichbar": False, "grund": f"{type(e).__name__}: {e}"[:160]}


def _q(browser):
    return f"?browser={browser}" if browser else ""


def oeffnen(url, browser=""):
    return _ruf("/oeffnen", "POST", {"url": url, **({"browser": browser} if browser else {})})


def lesen(browser=""):
    return _ruf("/lesen" + _q(browser), "GET")


def screenshot(browser=""):
    return _ruf("/screenshot" + _q(browser), "GET", roh=True)


def klick(selektor=None, x=None, y=None, browser="", wirkt_nach_aussen=False):
    b = {"wirkt_nach_aussen": bool(wirkt_nach_aussen)}
    if browser:
        b["browser"] = browser
    if selektor:
        b["selektor"] = selektor
    elif x is not None and y is not None:
        b["x"], b["y"] = x, y
    return _ruf("/klick", "POST", b)


def tippen(selektor, text, browser=""):
    b = {"selektor": selektor, "text": text}
    if browser:
        b["browser"] = browser
    return _ruf("/tippen", "POST", b)


def formular(felder, absenden_selektor=None, browser=""):
    b = {"felder": felder}
    if absenden_selektor:
        b["absenden_selektor"] = absenden_selektor
    if browser:
        b["browser"] = browser
    return _ruf("/formular_ausfuellen", "POST", b)


def navigieren(richtung="neu_laden", browser=""):
    pfad = {"zurueck": "/zurueck", "vor": "/vor", "neu_laden": "/neu_laden"}.get(richtung)
    if not pfad:
        return {"erreichbar": True, "fehler": f"unbekannte Richtung: {richtung}"}
    return _ruf(pfad, "POST", {"browser": browser} if browser else {})
