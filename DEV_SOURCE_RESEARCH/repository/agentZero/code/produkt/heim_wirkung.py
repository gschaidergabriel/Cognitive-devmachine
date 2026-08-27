"""heim_wirkung.py -- Zeros Griffe an die Rechner der Menschen ins Effektbuch.

Warum: die Tore am Zielrechner (nur Tailscale, Token, Schranke, lokaler Zeuge)
schuetzen -- aber sie erinnern nicht. Im Buch der Entitaet stand bisher NICHTS
davon, dass Zero auf einem echten Rechner getippt, geklickt oder einen Befehl
abgesetzt hat. Wer spaeter fragt "was hat es draussen getan", haette Mails und
EntityOS-Aufrufe gesehen und genau diese Klasse von Wirkung nicht.

Gebaut wie `postfach.senden`: das Tor faellt das Urteil und fuehrt Buch, der
Wirker tut die Sache. Was IM Buch landet, ist bewusst nur Zaehlbares --
Rechner, Art der Handlung, gelungen ja/nein und eine Pruefsumme der Nutzlast.
Der Wortlaut (Befehl, getippter Text, Bildschirminhalt) steht im lokalen Zeugen
auf dem Rechner des Menschen, wo er hingehoert: ein Effektbeleg ist dauerhaft
und wird von vielen gelesen, ein Tastendruck kann ein Passwort sein.

⚠️ Die Buchung darf die Faehigkeit nicht abwuergen. Laesst sich nicht buchen
(keine lebende Sitzung, Generationswechsel), wird die Handlung trotzdem
ausgefuehrt und die Antwort traegt `gebucht: false` mitsamt Grund -- sichtbar,
nicht still. Der Schutz sitzt an den Toren des Zielrechners, das Buch ist das
Gedaechtnis; ein fehlendes Gedaechtnis ist ein Mangel, kein Sicherheitsbruch.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any, Callable

from .effects import EffectGate, EffectRequest

# ── Der lesbare Beleg ─────────────────────────────────────────────────────
# Das Effektbuch redigiert Ziel und Ergebnis grundsaetzlich zu Pruefsummen
# (redacted-target-v1) -- gut fuer Geheimnisse, unbrauchbar fuer die Frage
# "auf WELCHEM Rechner hat es WAS getan". Darum daneben eine lesbare Zeile,
# genau wie das Postfach sie fuer Mails fuehrt: Rechner, Art, Urteil, Zeit --
# und vom Wortlaut nur die Pruefsumme. Beides zusammen beantwortet die Frage,
# ohne einen Tastendruck dauerhaft zu speichern.
BELEG_TABELLE = (
    "CREATE TABLE IF NOT EXISTS heim_belege("
    "beleg_id TEXT PRIMARY KEY, ts REAL NOT NULL, effect_id TEXT, causal_id TEXT,"
    "user_id TEXT NOT NULL, wirt TEXT NOT NULL, aktion TEXT NOT NULL,"
    "nutzlast_sha256 TEXT NOT NULL, urteil TEXT NOT NULL)")


def _beleg(db, effect_id, causal_id, user_id, wirt, aktion, pruefsumme, urteil) -> str:
    """Eine Zeile, ein Vorgang. Schlaegt das Schreiben fehl, faellt deshalb
    keine Handlung um -- der Beleg ist Gedaechtnis, nicht Bedingung."""
    beleg_id = uuid.uuid4().hex
    try:
        db.db.execute(BELEG_TABELLE)
        db.db.execute(
            "INSERT INTO heim_belege(beleg_id,ts,effect_id,causal_id,user_id,wirt,"
            "aktion,nutzlast_sha256,urteil) VALUES(?,?,?,?,?,?,?,?,?)",
            (beleg_id, time.time(), effect_id, causal_id, user_id, wirt, aktion,
             pruefsumme, urteil))
    except Exception:
        return ""
    return beleg_id


def _pruefsumme(nutzlast: Any) -> str:
    try:
        roh = json.dumps(nutzlast, sort_keys=True, ensure_ascii=False, default=str)
    except Exception:
        roh = repr(nutzlast)
    return hashlib.sha256(roh.encode("utf-8")).hexdigest()


def _gelungen(antwort: dict) -> bool:
    """Erreicht UND nicht abgewiesen. Die Schranke des Zielrechners antwortet
    mit erlaubt=False -- das ist kein Fehler, aber auch kein Erfolg."""
    if not isinstance(antwort, dict):
        return False
    if not antwort.get("erreichbar"):
        return False
    if antwort.get("erlaubt") is False:
        return False
    return antwort.get("ok", True) is not False


def wirken(db, user_id: str, session_id: str, wirt: str, aktion: str,
           nutzlast: Any, tun: Callable[[], dict]) -> dict:
    """`tun()` fuehrt die Handlung aus und liefert die rohe Bruecken-Antwort."""
    behaelter: dict[str, Any] = {}

    def wirker(_req: EffectRequest) -> dict:
        behaelter["roh"] = tun()
        return {"ok": _gelungen(behaelter["roh"]), "wirt": wirt, "aktion": aktion,
                "nutzlast_sha256": _pruefsumme(nutzlast)}

    gate = EffectGate(db, heim_wirker=wirker)
    ziel = f"heim:{wirt}:{aktion}"[:2048]
    pruefsumme = _pruefsumme(nutzlast)
    try:
        effect_id, _ausgang = gate.execute(
            EffectRequest(user_id=user_id, session_id=session_id,
                          capability="heim.bedienen", target=ziel))
    except Exception as e:
        roh = behaelter.get("roh")
        if roh is None:                      # das Tor kam gar nicht bis zum Wirker
            roh = tun()
        roh = dict(roh) if isinstance(roh, dict) else {"antwort": roh}
        roh["gebucht"] = False
        roh["buchung_fehler"] = f"{type(e).__name__}: {e}"[:200]
        # Auch der ungebuchte Griff bekommt seine lesbare Zeile: ein Vorgang,
        # der keine Spur hinterlaesst, wird spaeter fuer "nie geschehen"
        # gehalten -- genau die Sorte Nichtwissen, die hier weg soll.
        roh["beleg_id"] = _beleg(db, None, None, user_id, wirt, aktion,
                                 pruefsumme, "UNGEBUCHT")
        return roh

    roh = behaelter.get("roh")
    roh = dict(roh) if isinstance(roh, dict) else {"antwort": roh}
    zeile = db.db.execute("SELECT status FROM effects WHERE effect_id=?",
                          (effect_id,)).fetchone()
    urteil = str(zeile[0]) if zeile else "UNKNOWN"
    roh["gebucht"] = True
    roh["effect_id"] = effect_id
    roh["urteil"] = urteil
    roh["beleg_id"] = _beleg(db, effect_id, gate.causal_for_effect(effect_id),
                             user_id, wirt, aktion, pruefsumme, urteil)
    return roh
