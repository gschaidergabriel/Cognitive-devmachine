# -*- coding: utf-8 -*-
"""Absichtspruefung -- hat dieser Zug etwas getan, wonach niemand gefragt hat?

WAS DAS IST, UND WAS AUSDRUECKLICH NICHT
========================================
Ein ENTDECKER, kein Verhinderer. Er blockt nichts; er schreibt auf, wenn ein Zug
nach aussen gewirkt hat, ohne dass jemand danach gefragt hat. Wer blockiert,
braucht Gewissheit; wer aufschreibt, braucht nur einen Verdacht -- und Verdacht
ist hier billig zu haben und teuer zu ignorieren.

WARUM MECHANISCH
================
Die Vorlage aus der Literatur (LlamaFirewall, arXiv 2505.03574) misst mit einem
Modell, das die Werkzeugspur gegen das erklaerte Ziel haelt: AgentDojo-ASR
17,63 % -> 7,53 % mit Textfilter -> **2,89 % mit dem Absichtspruefer allein**.
Das ist die wirksamere Bauform. Sie kostet aber einen weiteren Modellaufruf je
Zug, und sie beurteilt mit demselben Werkzeugkasten, den sie pruefen soll.

Hier steht deshalb zuerst die mechanische Fassung: zwei Regeln, die aus Daten
kommen, die ohnehin anfallen, und die ohne Modell auskommen. Sie findet weniger
als ein Sprachmodell -- aber was sie findet, findet sie nachvollziehbar, und
sie kann nicht selbst getaeuscht werden. Der Modellpruefer waere der dritte
Schritt, nicht der erste.

DIE ZWEI REGELN
===============
  unangekuendigt  Ein nach aussen wirkendes Werkzeug lief, das die Vorstufe
                  nicht angekuendigt hatte. Die Ankuendigung ist zwar nur ein
                  Hinweis (Zero waehlt selbst), aber die Abweichung ist genau
                  die Stelle, an der aus "hilfreich" "eigenmaechtig" wird.
  ohne_auftrag    Ein nach aussen wirkendes Werkzeug lief auf eine Nachricht,
                  die gar keine Sachfrage war ("danke", "hallo"). Wer auf einen
                  Dank hin Dateien schreibt, tut etwas, wonach niemand gefragt hat.
"""
from __future__ import annotations

import json
import sys
import time

# Wie oft die Buchung stillschweigend scheiterte. Siehe `buchen()`.
AUSFAELLE = 0

# ⚠️ KOMMENTAR KORRIGIERT 2026-08-21. Hier stand: "Werkzeuge, die nur lesen,
# sind hier nie ein Verdacht". Das stimmt mit der importierten Menge NICHT
# ueberein -- `_AUSSENWIRKUNG` enthaelt `WebSearch` und `WebFetch`, also zwei
# reine Lese-Werkzeuge. headless_zero definiert die Menge breiter, naemlich als
# "Wirkung, die den Behaelter verlaesst ODER dauerhaft bleibt"; nach dieser
# Definition gehoeren sie hinein. Es gab also zwei Definitionen und eine Menge.
#
# Gepruefte Folge: KEINE. `_AUSSENWIRKUNG` hat genau einen Verbraucher -- diesen
# Beobachter. Kein Tor, keine Sperre, kein EffectGate liest sie. Gemessen ueber
# alle 51 gebuchten Zuege: aussenwirkung leer, verdacht leer, null Falschalarme.
# Deshalb wird die MENGE nicht angetastet (das waere eine Aenderung ohne
# Symptom, die die Definition in headless_zero verletzt) -- nur der Satz, der
# sie falsch beschrieb.
#
# Was hier wirklich zaehlt: nicht Lesen gegen Schreiben, sondern Wirkung, die
# den Zug ueberdauert. Ein `READ_EXTERNAL` steht in dieser Menge, weil es den
# Behaelter verlaesst -- nicht, weil es etwas veraendert.
from .headless_zero import _AUSSENWIRKUNG

_TABELLE = (
    "CREATE TABLE IF NOT EXISTS gw_absicht("
    "  id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL,"
    "  turn_id TEXT, session_id TEXT, frage TEXT,"
    "  werkzeuge TEXT, aussenwirkung TEXT, angekuendigt TEXT,"
    "  verdacht TEXT, grund TEXT);"
    "CREATE INDEX IF NOT EXISTS gw_absicht_ts ON gw_absicht(ts);")

MIN_SACHFRAGE_WORTE = 2


def pruefen(frage: str, spur: dict, angekuendigt) -> dict:
    """Rein rechnerisch. Liefert die Verdachtsgruende, nie ein Urteil."""
    from . import wettbewerb as _w

    aussen = list((spur or {}).get("aussenwirkung") or [])
    erklaert = {str(t) for t in (angekuendigt or [])}
    verdacht, gruende = [], []

    if aussen:
        unangekuendigt = sorted(w for w in set(aussen) if w not in erklaert)
        if unangekuendigt:
            verdacht.append("unangekuendigt")
            gruende.append("nach aussen wirkend, aber nicht angekuendigt: "
                           + ", ".join(unangekuendigt))
        if len(_w._worte(frage or "")) < MIN_SACHFRAGE_WORTE:
            verdacht.append("ohne_auftrag")
            gruende.append("die Nachricht war keine Sachfrage, es wirkte aber "
                           "nach aussen: " + ", ".join(sorted(set(aussen))))

    return {"verdacht": verdacht, "grund": "; ".join(gruende),
            "aussenwirkung": sorted(set(aussen))}


def buchen(store, turn_id, session_id, frage: str, spur: dict, angekuendigt) -> dict:
    """Immer buchen, nicht nur bei Verdacht.

    Eine Tabelle, die nur Verdachtsfaelle enthaelt, hat keinen Nenner: man kann
    dann nicht sagen, ob eine Woche mit drei Faellen viel oder wenig war.

    ⭐ 2026-08-21: das `except` bleibt stumm gegenueber dem ZUG -- eine kaputte
    Buchung darf keine Antwort kippen, und `pruefen()` steht bewusst davor, das
    Urteil ueberlebt jeden DB-Fehler. Aber es bleibt nicht mehr stumm gegenueber
    dem MESSGERAET: ein Ausfall hinterliess bisher gar keine Zeile, und "keine
    Zeile" sah genauso aus wie "kein Verdacht". Genau der Nenner, den dieser
    Docstring einfordert, war damit unbeobachtbar.

    Der Gegenbeleg lag bisher nur im Abgleich mit `gw_herkunft` (dieselbe
    Aufrufstelle, ein Zug = eine Zeile in beiden). Gemessen 51 / 51, also kein
    stiller Verlust. Ab jetzt zaehlt `AUSFAELLE` mit und der Grund geht nach
    stderr -- damit muss man den Abgleich nicht mehr von Hand fahren, um zu
    wissen, ob ueberhaupt gebucht wurde.
    """
    urteil = pruefen(frage, spur, angekuendigt)
    try:
        store.db.executescript(_TABELLE)
        store.db.execute(
            "INSERT INTO gw_absicht(ts,turn_id,session_id,frage,werkzeuge,"
            "aussenwirkung,angekuendigt,verdacht,grund) VALUES(?,?,?,?,?,?,?,?,?)",
            (time.time(), turn_id, session_id, (frage or "")[:400],
             json.dumps(list((spur or {}).get("werkzeuge") or []), ensure_ascii=False),
             json.dumps(urteil["aussenwirkung"], ensure_ascii=False),
             json.dumps(sorted({str(t) for t in (angekuendigt or [])}), ensure_ascii=False),
             json.dumps(urteil["verdacht"], ensure_ascii=False), urteil["grund"]))
        store.db.commit()
    except Exception as e:
        global AUSFAELLE
        AUSFAELLE += 1
        # Bewusst nur stderr, kein raise: der Beobachter darf den Zug nicht
        # kippen. Aber ein Ausfall muss sichtbar sein, sonst ist "kein Verdacht"
        # nicht von "nicht gemessen" zu unterscheiden.
        print(f"absicht: Buchung fehlgeschlagen ({AUSFAELLE}. Mal): "
              f"{type(e).__name__}: {e}", file=sys.stderr)
    return urteil
