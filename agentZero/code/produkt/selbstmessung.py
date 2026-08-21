from __future__ import annotations

"""Ein Befehl fuer den ganzen Selbstzustand -- `python3 -m clayverse.selbstmessung`.

Eigner-Auftrag 2026-08-21: Zero (und der kommende Selbstverbesserungsprozess)
soll sich vor/nach jeder Aenderung messen koennen, OHNE dass jemand vorher
lernen muss, welches der ~50 Module welche Tabelle fuehrt. Genau dieselbe
Umkehrung wie bei `udb.zustand()` (siehe /opt/unifieddb/udb/abruf/zustand.py):
EIN Aufruf, der die Frage "wie steht es gerade" beantwortet.

⭐ DIESES MODUL MISST NUR. Es baut KEIN einziges der Messgeraete neu -- jede
Funktion unten ruft ein bereits gebautes, bereits durchdachtes Werkzeug auf:

  1. Testboden          pytest (die Zahl, die CLAUDE.md als Untergrenze fuehrt)
  2. Wegehierarchie      /opt/unifieddb/udb/abruf/wegehierarchie.py:pruefung()
  3. Weckvertrag         clayverse/wake_condition.py:naechste_pruefung()
                         ueber die Tabelle aus clayverse/wake_governor.py
  4. Uebersetzungsausfaelle  wiki.db-Tabelle mv_uebersetzung_ausfall
                         (clayverse/mistral_prestage/pipeline.py)
  5. Stimmen             wiki.db-Tabelle eos_bewertungen (clayverse/bewertung.py)
  6. Abnahmeprobe        clayverse/final_acceptance_probe.py (nur BESCHRIEBEN,
                         nie aufgerufen -- siehe dortiger Abschnitt unten, WARUM)

⚠️⭐ ZENTRALE REGEL, aus wake_condition.py uebernommen und hier genauso
verbindlich: UNBEKANNT ist ein Messausfall, kein Befund. "Die Tabelle fehlt
noch" (noch nie etwas geschrieben -- ein Datenmangel) und "die Messung ist
fehlgeschlagen" (ein echter Fehler) und "der Schwellwert ist erreicht"
(ERFUELLT) sind DREI verschiedene Zustaende und werden hier nie ineinander
verwischt. "kein Log" heisst NICHT "null Vorfaelle" -- es heisst "wir wissen
es noch nicht". Wer diese Unterscheidung spaeter beim Erweitern verwaesserst,
baut denselben Fehler wieder ein, der wake_condition.py und wegehierarchie.py
schon einmal repariert haben.

⚠️⭐ STRIKT LESEND. Diese Datei enthaelt kein einziges INSERT/UPDATE/DELETE/
CREATE und kein `executescript()`. Die Produktions-`wiki.db` (~5 GB, WAL,
mehrere aktive Schreiber) wird ausschliesslich ueber eine mode=ro-Verbindung
angefasst -- bevorzugt ueber die bereits gebaute, bereits gehaertete
`udb.abruf.zustand.verbindung()` (busy_timeout + Wiederholung + `PRAGMA
query_only=ON`, siehe dortiger Kopfkommentar), NICHT ueber
`clayverse.store.UnifiedDB(...)`: deren `__init__` schreibt beim Oeffnen
(Meta-Zeilen, `executescript(SCHEMA)`) -- fuer ein Werkzeug, dessen einziger
Auftrag "nur hinschauen" ist, waere das der falsche Konstruktor.

Ebenso wird `WakeConditionStore(db)` (wake_governor.py) hier bewusst NICHT
instanziiert: ihr `__init__` legt `wake_conditions` per `executescript()` an,
falls sie fehlt -- ein Schreibzugriff, den ein lesendes Werkzeug nicht
ausloesen darf. Stattdessen liest dieses Modul dieselbe Abfrage wie
`WakeConditionStore.offene()` direkt (reines SELECT) und rekonstruiert jede
Zeile weiterhin ausschliesslich ueber `WakeCondition.aus_dict()` -- den
einen gepruefte Entstehungsweg, den wake_condition.py selbst vorschreibt.
"""

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .wake_condition import WakeCondition, WakeConditionError, naechste_pruefung

# ---------------------------------------------------------------------------
# udb (separates Repo, /opt/unifieddb) einhaengen -- exakt dasselbe Muster wie
# mcp_server.py: guarded, weil es in Unit-Test-/Dev-Umgebungen fehlen kann,
# die den Bind-Mount nicht setzen. Ein fehlendes udb ist dann UNBEKANNT fuer
# genau die zwei Instrumente, die es liefert -- nicht ein Absturz des ganzen
# Berichts.
# ---------------------------------------------------------------------------
_UDB_ROOT = os.environ.get("UDB_ROOT", "/opt/unifieddb")
if _UDB_ROOT not in sys.path and os.path.isdir(_UDB_ROOT):
    sys.path.insert(0, _UDB_ROOT)

_UDB_IMPORT_FEHLER: Exception | None = None
try:
    from udb.abruf import wegehierarchie as _wegehierarchie  # type: ignore
    from udb.abruf.zustand import verbindung as _udb_verbindung  # type: ignore
except Exception as _exc:  # pragma: no cover - nur wenn /opt/unifieddb fehlt
    _wegehierarchie = None
    _udb_verbindung = None
    _UDB_IMPORT_FEHLER = _exc

# Produktionspfad, dieselbe Vorgabe wie udb.abruf.zustand.DB_PATH und
# clayverse.store.resolve_db_path()'s CLAYVERSE_DB_PATH -- EIN Wert, nicht neu
# erfunden, damit alle drei Werkzeuge desselben Hauses niemals auseinanderlaufen.
STANDARD_DB_PFAD = os.environ.get(
    "UDB_DB_PATH", os.environ.get("CLAYVERSE_DB_PATH", "/var/lib/clay/wiki.db")
)

# Wo der Testboden laeuft, siehe Auftrag: PYTHONPATH="/opt/entityos/the artefact"
# und /opt/entityos/venv-test/bin/pytest. Beides ueberschreibbar fuer Tests.
ARTEFAKT_ROOT = os.environ.get("CLAYVERSE_ARTEFAKT_ROOT", "/opt/entityos/the artefact")
VENV_PYTEST = os.environ.get("CLAYVERSE_VENV_PYTEST", "/opt/entityos/venv-test/bin/pytest")
BEKANNTER_TESTBODEN = 1067  # CLAUDE.md-Floor -- Erinnerungswert, NIE als "gemessen" ausgegeben


class _NurLesendDB:
    """Duenne Schale, NUR damit `wegehierarchie.pruefung()` (erwartet ein
    UnifiedDB-artiges Objekt mit `.db`) eine rohe mode=ro-Verbindung annehmen
    kann. Traegt selbst keine Methode, die schreibt -- `pruefung()` tut
    ohnehin nichts als SELECT (siehe dortiger Code)."""

    def __init__(self, conn: sqlite3.Connection):
        self.db = conn


def _ro_verbinden(pfad: str) -> sqlite3.Connection:
    """Nur-lesende Verbindung. Bevorzugt `udb.abruf.zustand.verbindung()`
    (gehaertet: busy_timeout + Wiederholung gegen die geteilte 5-GB-WAL-Datei,
    siehe dortiger Kopfkommentar) -- Rueckfall auf eine lokale, aber ebenso
    mode=ro+query_only-gesicherte Verbindung nur dort, wo /opt/unifieddb nicht
    gemountet ist (z.B. dieses Modul im Unit-Test gegen eine tmp_path-Datei).
    Der Rueckfall ist keine zweite Messmethode, nur derselbe Verbindungsaufbau,
    den der Auftrag ausdruecklich verlangt (?mode=ro, uri=True)."""
    if _udb_verbindung is not None:
        conn = _udb_verbindung(pfad)
    else:
        conn = sqlite3.connect(f"file:{pfad}?mode=ro", uri=True, timeout=30)
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA query_only=ON")
    conn.row_factory = sqlite3.Row  # wegehierarchie.pruefung() braucht dict(row)
    return conn


def _unbekannt(grund: str, *, quelle: str, zeile: str | None = None) -> dict[str, Any]:
    return {
        "stand": "UNBEKANNT",
        "grund": grund,
        "quelle": quelle,
        "zeile": zeile or f"UNBEKANNT: {grund}",
    }


def _fehlt_tabelle(fehler: Exception) -> bool:
    text = str(fehler)
    return isinstance(fehler, sqlite3.OperationalError) and "no such table" in text


# ---------------------------------------------------------------------------
# 1) Wegehierarchie
# ---------------------------------------------------------------------------

def _wege(conn: sqlite3.Connection) -> dict[str, Any]:
    quelle = "/opt/unifieddb/udb/abruf/wegehierarchie.py:pruefung()"
    if _wegehierarchie is None:
        return _unbekannt(f"udb nicht importierbar: {_UDB_IMPORT_FEHLER}", quelle=quelle)
    try:
        ergebnis = _wegehierarchie.pruefung(_NurLesendDB(conn))
    except Exception as exc:  # fail-closed: ein Ausfall ist UNBEKANNT, nie "ok"
        return _unbekannt(f"{type(exc).__name__}: {exc}", quelle=quelle)

    ergebnis = dict(ergebnis)
    ergebnis["quelle"] = quelle
    if ergebnis.get("stand") == "NOCH_KEINE_WEGE":
        ergebnis["zeile"] = "Wegehierarchie: noch keine Wege aufgezeichnet -- kein Urteil moeglich."
    elif "oberes_zehntel_haelt" in ergebnis:
        # Echtes Urteil MIT Schwellenwert (>=10 Wege, siehe pruefung()) --
        # vorher stand hier `"urteil" in ergebnis`, was auch fuer den
        # naechsten Zweig ("zu wenige Wege", n<10) zutraf, weil pruefung()
        # dort AUCH ein "urteil"-Feld setzt (nur ohne "oberes_zehntel_haelt").
        # Das liess diesen Zweig faelschlich zugreifen und den `else`-Zweig
        # unten toter Code werden -- bei n<10 waere ergebnis['oberes_zehntel_
        # haelt'] ein KeyError gewesen. Jetzt auf dem Feld unterschieden, das
        # tatsaechlich nur hier existiert.
        b3 = ergebnis.get("bedingung3_echt", {})
        ergebnis["zeile"] = (
            f"Wegehierarchie: {ergebnis['wege']} Wege, {ergebnis['urteil']} "
            f"(oberes Zehntel haelt {ergebnis['oberes_zehntel_haelt']}); "
            f"Tunnel-Bedingung: {b3.get('stand', 'UNBEKANNT')}"
        )
        # ⚠️⭐ BUG gefunden live 22.08. (Koordinator-Auftrag): `pruefung()`
        # (separates Repo /opt/unifieddb) kennt "stand" gar nicht -- nur der
        # NOCH_KEINE_WEGE-Zweig oben setzt es je. Die anderen drei
        # Instrumente hier (Weckvertrag, Uebersetzungsausfaelle, Stimmen)
        # markieren eine echte Messung immer explizit mit "stand":"GEMESSEN";
        # Wegehierarchie tat das nie, obwohl genau HIER (>=10 Wege, echtes
        # Urteil samt Schwellenwert) dieselbe Art Messung vorliegt. Ohne
        # dieses Feld blieb architekt/hypothesen.py:sammle_messwerte fuer
        # JEDE Wegehierarchie-Schwellenverletzung blind (weg.get("stand")
        # == "GEMESSEN" traf nie zu) -- live gemessen: oberes_zehntel_
        # haelt=0.14 unter der Schwelle 0.20, aber keine Hypothese entstand.
        # Absichtlich NUR in diesem Zweig gesetzt (nicht im "zu wenige
        # Wege"-Zweig unten): dort fehlt der Schwellenwert selbst, "GEMESSEN"
        # ohne ihn waere ein leeres Versprechen (fail-closed bleibt gewahrt).
        ergebnis["stand"] = "GEMESSEN"
    else:  # "zu wenige Wege fuer ein Urteil" (n<10) -- hat "urteil", aber
           # bewusst KEIN "stand": ein Urteil ohne Schwellenwert ist keine
           # Messung, auf die eine Hypothese sich stuetzen koennte.
        ergebnis["zeile"] = f"Wegehierarchie: {ergebnis.get('wege', 0)} Wege -- {ergebnis.get('urteil', '?')}."
    return ergebnis


# ---------------------------------------------------------------------------
# 2) Weckvertrag-Deckung
# ---------------------------------------------------------------------------

# Empirische Grundlage je Bedingungsart -- keine Messung, sondern ein Zitat aus
# dem eigenen Vertrag: wake_signal.py (Zeilen "Deckt heute nur die zwei
# tatsaechlich verdrahteten Haken ab") sagt selbst, welche Arten ein Ereignis
# tatsaechlich AUSLOESEN und welche nur auf den 30s-Puls angewiesen sind.
# Diese Zuordnung NICHT selbst neu bewerten -- die Quelle dafuer ist der
# Docstring von `wake_signal.weckbar()`, nicht diese Datei.
_WECKVERTRAG_GRUNDLAGE = {
    "EFFECT_TERMINAL": "verdrahtet -- effect_journal.py laeutet die Glocke real bei Abschluss (wake_signal.py:weckbar).",
    "RESOURCE_REVISION": "teilweise verdrahtet -- NUR das Praefix session_turn_count:<sid> laeutet real (turn_lifecycle.py); alle anderen Subjekte haben keinen Haken.",
    "GOAL_STATE": "NICHT verdrahtet -- kein Ereignis-Haken, faellt bis auf Weiteres auf den 30s-Puls zurueck. Unbewiesen, nicht behaupten.",
    "AT_TIME": "mechanisch trivial (reine Uhrzeit), aber in Produktion noch nie eine registrierte Bedingung gesehen. Unbewiesen, nicht behaupten.",
}


def _weckvertrag(conn: sqlite3.Connection, jetzt: float) -> dict[str, Any]:
    quelle = "clayverse/wake_condition.py:naechste_pruefung() ueber wake_conditions (clayverse/wake_governor.py:_CONDITIONS_TABELLE)"
    try:
        zeilen = conn.execute(
            "SELECT schema,kind,subject_ref,expected_predicate,earliest_at,deadline,"
            "goal_id,step_id,generation,coalesce_key FROM wake_conditions WHERE status='OFFEN'"
        ).fetchall()
    except sqlite3.OperationalError as exc:
        if _fehlt_tabelle(exc):
            return {
                "stand": "NOCH_KEINE_TABELLE",
                "offene_bedingungen_gesamt": 0,
                "hinweis": "wake_conditions existiert noch nicht -- der Governor hat noch nie eine Bedingung registriert. Das ist Datenmangel, kein Negativbefund.",
                "quelle": quelle,
                "zeile": "Weckvertrag: Tabelle noch nicht angelegt -- noch keine Bedingung je registriert.",
            }
        return _unbekannt(f"{type(exc).__name__}: {exc}", quelle=quelle)
    except Exception as exc:
        return _unbekannt(f"{type(exc).__name__}: {exc}", quelle=quelle)

    je_art: dict[str, dict[str, int]] = {}
    rekonstruktionsfehler = 0
    for row in zeilen:
        payload = {
            "schema": row["schema"],
            "kind": row["kind"],
            "subject_ref": row["subject_ref"],
            "expected_predicate": (
                json.loads(row["expected_predicate"]) if row["expected_predicate"] is not None else None
            ),
            "earliest_at": row["earliest_at"],
            "deadline": row["deadline"],
            "goal_id": row["goal_id"],
            "step_id": row["step_id"],
            "generation": row["generation"],
            "coalesce_key": row["coalesce_key"],
        }
        try:
            bedingung = WakeCondition.aus_dict(payload)
        except WakeConditionError:
            # Eine Zeile, die dem eigenen Vertrag nicht mehr genuegt, wird
            # gezaehlt statt den ganzen Bericht zu kippen -- derselbe
            # Fail-closed-Gedanke wie im Rest dieser Datei.
            rekonstruktionsfehler += 1
            continue
        eintrag = je_art.setdefault(bedingung.kind, {"offen": 0, "mit_naechster_pruefung": 0})
        eintrag["offen"] += 1
        if naechste_pruefung([bedingung], jetzt) is not None:
            eintrag["mit_naechster_pruefung"] += 1

    gesamt = sum(v["offen"] for v in je_art.values())
    gesamt_mit = sum(v["mit_naechster_pruefung"] for v in je_art.values())
    return {
        "stand": "GEMESSEN",
        "offene_bedingungen_gesamt": gesamt,
        "davon_mit_naechster_pruefung": gesamt_mit,
        "je_art": je_art,
        "rekonstruktionsfehler": rekonstruktionsfehler,
        "empirische_grundlage_je_art": _WECKVERTRAG_GRUNDLAGE,
        "quelle": quelle,
        "zeile": (
            f"Weckvertrag: {gesamt} offene Bedingung(en), {gesamt_mit} davon mit "
            f"berechenbarem naechstem Pruefzeitpunkt; Arten: {sorted(je_art)}."
            if gesamt else "Weckvertrag: Tabelle vorhanden, aber 0 offene Bedingungen."
        ),
    }


# ---------------------------------------------------------------------------
# 3) Uebersetzungsausfaelle
# ---------------------------------------------------------------------------

def _uebersetzungsausfaelle(conn: sqlite3.Connection, *, fenster_s: float = 86400.0) -> dict[str, Any]:
    quelle = "wiki.db:mv_uebersetzung_ausfall (clayverse/mistral_prestage/pipeline.py:_log_uebersetzungsausfall)"
    try:
        gesamt = conn.execute("SELECT COUNT(*) FROM mv_uebersetzung_ausfall").fetchone()[0]
    except sqlite3.OperationalError as exc:
        if _fehlt_tabelle(exc):
            return {
                "stand": "NOCH_KEINE_TABELLE",
                "gesamt": 0,
                "hinweis": "mv_uebersetzung_ausfall existiert noch nicht -- der Uebersetzer ist noch nie ausgefallen ODER noch nie ein Zug gelaufen. Beides sieht hier gleich aus, das ist eine bekannte Grenze dieser Zeile.",
                "quelle": quelle,
                "zeile": "Uebersetzungsausfaelle: Tabelle noch nicht angelegt -- kein Ausfall bekannt (kann auch heissen: noch nie gelaufen).",
            }
        return _unbekannt(f"{type(exc).__name__}: {exc}", quelle=quelle)
    except Exception as exc:
        return _unbekannt(f"{type(exc).__name__}: {exc}", quelle=quelle)

    grenze = time.time() - fenster_s
    kuerzlich = conn.execute(
        "SELECT COUNT(*) FROM mv_uebersetzung_ausfall WHERE ts >= ?", (grenze,)
    ).fetchone()[0]
    letzte_zeile = conn.execute(
        "SELECT ts, fehler FROM mv_uebersetzung_ausfall ORDER BY ts DESC LIMIT 1"
    ).fetchone()

    letzter_fehler = None
    einordnung = None
    if letzte_zeile is not None:
        letzter_fehler = {"ts": letzte_zeile["ts"], "fehler": letzte_zeile["fehler"]}
        text = letzte_zeile["fehler"] or ""
        # Nur die zwei in CLAUDE.md bereits benannten Codes einordnen -- alles
        # andere bleibt roh stehen, statt eine Bedeutung zu erfinden.
        if "429" in text:
            einordnung = "429 -- Uebersetzer-Lane ausgeschoepft (Rate-Limit)"
        elif "402" in text:
            einordnung = "402 -- fehlendes Abo/Kontingent beim Uebersetzer"

    return {
        "stand": "GEMESSEN",
        "gesamt": gesamt,
        "kuerzlich_24h": kuerzlich,
        "letzter_fehler": letzter_fehler,
        "einordnung_letzter_fehler": einordnung,
        "quelle": quelle,
        "zeile": (
            f"Uebersetzungsausfaelle: {gesamt} insgesamt, {kuerzlich} in den letzten 24h"
            + (f"; juengster: {einordnung or letzter_fehler['fehler']}" if letzter_fehler else "")
            + ". Ein Rueckstau ist ein Signal, kein automatischer Fehlschlag."
        ),
    }


# ---------------------------------------------------------------------------
# 4) Stimmen (Daumen hoch/runter)
# ---------------------------------------------------------------------------

def _stimmen(conn: sqlite3.Connection, *, letzte_n: int = 10) -> dict[str, Any]:
    quelle = "wiki.db:eos_bewertungen (clayverse/bewertung.py:setzen())"
    try:
        zeilen = conn.execute("SELECT wert, COUNT(*) AS n FROM eos_bewertungen GROUP BY wert").fetchall()
    except sqlite3.OperationalError as exc:
        if _fehlt_tabelle(exc):
            return {
                "stand": "NOCH_KEINE_TABELLE",
                "hoch": 0,
                "runter": 0,
                "hinweis": "eos_bewertungen existiert noch nicht -- noch nie eine Stimme abgegeben.",
                "quelle": quelle,
                "zeile": "Stimmen: Tabelle noch nicht angelegt -- noch keine Bewertung je abgegeben.",
            }
        return _unbekannt(f"{type(exc).__name__}: {exc}", quelle=quelle)
    except Exception as exc:
        return _unbekannt(f"{type(exc).__name__}: {exc}", quelle=quelle)

    hoch = sum(r["n"] for r in zeilen if r["wert"] == 1)
    runter = sum(r["n"] for r in zeilen if r["wert"] == -1)

    juengste_runter: list[dict[str, Any]] = []
    if runter:
        try:
            rows = conn.execute(
                "SELECT turn_id, session_id, antwort_hash, modell, ts FROM eos_bewertungen "
                "WHERE wert=-1 ORDER BY ts DESC LIMIT ?",
                (letzte_n,),
            ).fetchall()
            juengste_runter = [
                {
                    "turn_id": r["turn_id"],
                    "session_id": r["session_id"],
                    "antwort_hash": r["antwort_hash"],
                    "modell": r["modell"],
                    "ts": r["ts"],
                }
                for r in rows
            ]
        except Exception as exc:  # eine defekte Detailzeile darf die Zaehlung nicht kippen
            return {
                "stand": "TEILWEISE_UNBEKANNT",
                "hoch": hoch,
                "runter": runter,
                "grund_fuer_fehlende_details": f"{type(exc).__name__}: {exc}",
                "quelle": quelle,
                "zeile": f"Stimmen: {hoch} hoch / {runter} runter (Details zu Downvotes nicht lesbar).",
            }

    return {
        "stand": "GEMESSEN" if (hoch or runter) else "NOCH_KEINE_STIMMEN",
        "hoch": hoch,
        "runter": runter,
        "juengste_downvotes": juengste_runter,
        "quelle": quelle,
        "zeile": f"Stimmen: {hoch} hoch / {runter} runter"
        + (f", {len(juengste_runter)} juengste Downvote(s) mitgeliefert." if juengste_runter else "."),
    }


# ---------------------------------------------------------------------------
# 5) Abnahmeprobe -- NUR beschrieben, nie aufgerufen
# ---------------------------------------------------------------------------

def _abnahmeprobe() -> dict[str, Any]:
    """`final_acceptance_probe.run_mistral_acceptance_probe()` fuehrt einen
    ECHTEN Mistral-Zug durch die ganze ClayVerse-Kausalkette: `ClayVerseEngine
    (...).ingest(...)` schreibt Zuege/Effekte in `wiki.db`, kostet ein
    Mistral-API-Kontingent und ist NICHT idempotent. Das ist das Gegenteil von
    "billig und seiteneffektfrei" -- ein strikt lesendes Selbstmessungswerkzeug
    darf das nie automatisch ausloesen. Diese Funktion beschreibt deshalb nur,
    was die Probe prueft, statt sie zu rufen."""
    return {
        "stand": "NICHT_AUSGEFUEHRT",
        "grund": (
            "run_mistral_acceptance_probe() schreibt einen echten Mistral-Zug "
            "(turns/effects) und verbraucht Kontingent -- kein seiteneffektfreier "
            "Aufruf, deshalb bewusst nicht automatisch gerufen."
        ),
        "was_es_prueft": [
            "der kanonische Mistral-Inference-Beleg traegt genau die erwarteten Felder (request/response-Hash, finish_reason=stop)",
            "die Antwort lief durch die pre-effect-reingest-Phase, bevor ein Effekt zugelassen wurde",
            "workspace_episode_id aus der Provenienz stimmt mit der aus dem Ingest-Ergebnis ueberein (keine Verwechslung zweier Episoden)",
            "die reasoning_generation ist noch live (assert_live_generation) -- keine veraltete Generation wird als aktuell durchgereicht",
            "optional (require_effect=True): ein Effekt wurde angefordert UND kam verifiziert (outcome.ok) zurueck",
        ],
        "quelle": "clayverse/final_acceptance_probe.py:run_mistral_acceptance_probe() (beschrieben, nicht ausgefuehrt)",
        "zeile": "Abnahmeprobe: nicht ausgefuehrt (schreibt echte Zuege/Effekte, kostet Kontingent) -- nur beschrieben.",
    }


# ---------------------------------------------------------------------------
# 6) Testboden
# ---------------------------------------------------------------------------

_PYTEST_ZAHL = re.compile(r"(\d+)\s+(passed|failed|skipped|error(?:s)?|xfailed|xpassed)")


def _pytest_zusammenfassung_parsen(text: str) -> dict[str, int] | None:
    treffer = _PYTEST_ZAHL.findall(text)
    if not treffer:
        return None
    zaehler = {"passed": 0, "failed": 0, "skipped": 0, "error": 0, "xfailed": 0, "xpassed": 0}
    for zahl, art in treffer:
        schluessel = "error" if art.startswith("error") else art
        zaehler[schluessel] = zaehler.get(schluessel, 0) + int(zahl)
    return zaehler


def _testboden(modus: str, *, zeitlimit_s: int = 170) -> dict[str, Any]:
    quelle = f"pytest ({VENV_PYTEST}) gegen {ARTEFAKT_ROOT}/tests"
    if modus == "ueberspringen":
        return {
            "stand": "NICHT_AUSGEFUEHRT_DIESEN_ZYKLUS",
            "grund": "Standardmodus ueberspringt den Lauf (kostet Minuten je Aufruf). Mit --tests=schnell oder --tests=voll anfordern.",
            "zuletzt_bekannter_boden_aus_claude_md": BEKANNTER_TESTBODEN,
            "quelle": quelle,
            "zeile": f"Testboden: nicht in diesem Zyklus ausgefuehrt (bekannter Boden laut CLAUDE.md: {BEKANNTER_TESTBODEN}, KEIN aktueller Messwert).",
        }

    if modus == "schnell":
        ziel = ["tests/test_selbstmessung.py"]
        beschreibung = "Teilmenge (nur die eigenen Selbstmessungs-Tests) -- NICHT der volle Boden."
    else:  # "voll"
        ziel = ["tests", "-q", "--timeout", "180"]
        beschreibung = "voller Lauf ueber tests/."

    befehl = [VENV_PYTEST, *ziel] if modus == "voll" else [VENV_PYTEST, *ziel, "-q"]
    umgebung = dict(os.environ)
    umgebung["PYTHONPATH"] = ARTEFAKT_ROOT
    try:
        lauf = subprocess.run(
            befehl,
            cwd=ARTEFAKT_ROOT,
            env=umgebung,
            capture_output=True,
            text=True,
            timeout=zeitlimit_s,
        )
    except subprocess.TimeoutExpired:
        return _unbekannt(f"pytest lief laenger als {zeitlimit_s}s (Zeitlimit ueberschritten)", quelle=quelle)
    except FileNotFoundError as exc:
        return _unbekannt(f"pytest nicht erreichbar: {exc}", quelle=quelle)
    except Exception as exc:
        return _unbekannt(f"{type(exc).__name__}: {exc}", quelle=quelle)

    text = (lauf.stdout or "") + "\n" + (lauf.stderr or "")
    zaehler = _pytest_zusammenfassung_parsen(text)
    if zaehler is None:
        return _unbekannt(
            f"pytest-Ausgabe nicht auswertbar (returncode={lauf.returncode}); letzte Zeilen: {text.strip()[-500:]!r}",
            quelle=quelle,
        )

    gruen, rot = zaehler["passed"], zaehler["failed"] + zaehler["error"]
    besteht = None
    if modus == "voll":
        besteht = gruen >= BEKANNTER_TESTBODEN and rot == 0
    return {
        "stand": "GEMESSEN",
        "teilmenge": beschreibung,
        "gruen": gruen,
        "rot": rot,
        "uebersprungen": zaehler["skipped"],
        "returncode": lauf.returncode,
        "besteht": besteht,
        "quelle": quelle,
        "zeile": (
            f"Testboden ({beschreibung}): {gruen} gruen, {rot} rot"
            + (f" -- FLOOR {BEKANNTER_TESTBODEN} {'gehalten' if besteht else 'UNTERSCHRITTEN'}" if modus == "voll" else "")
            + "."
        ),
    }


# ---------------------------------------------------------------------------
# Aggregation -- der eine Aufruf
# ---------------------------------------------------------------------------

def erstelle_bericht(
    *, pfad: str | None = None, tests: str = "ueberspringen", jetzt: float | None = None
) -> dict[str, Any]:
    """Der ganze Selbstzustand in einer Struktur. Fail-closed je Instrument:
    ein Ausfall in EINEM Messgeraet darf die anderen fuenf nicht mitreissen."""
    jetzt = time.time() if jetzt is None else jetzt
    pfad = pfad or STANDARD_DB_PFAD

    bericht: dict[str, Any] = {
        "schema": "ClayVerseSelbstzustand/v1",
        "erzeugt_um": jetzt,
        "erzeugt_um_iso": datetime.fromtimestamp(jetzt, tz=timezone.utc).isoformat(),
        "db_pfad": str(pfad),
        "instrumente": {},
    }

    conn: sqlite3.Connection | None = None
    try:
        conn = _ro_verbinden(str(pfad))
    except Exception as exc:
        grund = f"Datenbank nicht lesend erreichbar: {type(exc).__name__}: {exc}"
        for name, quelle in (
            ("wegehierarchie", "/opt/unifieddb/udb/abruf/wegehierarchie.py:pruefung()"),
            ("weckvertrag", "clayverse/wake_condition.py:naechste_pruefung()"),
            ("uebersetzungsausfaelle", "wiki.db:mv_uebersetzung_ausfall"),
            ("stimmen", "wiki.db:eos_bewertungen"),
        ):
            bericht["instrumente"][name] = _unbekannt(grund, quelle=quelle)
    else:
        try:
            bericht["instrumente"]["wegehierarchie"] = _wege(conn)
            bericht["instrumente"]["weckvertrag"] = _weckvertrag(conn, jetzt)
            bericht["instrumente"]["uebersetzungsausfaelle"] = _uebersetzungsausfaelle(conn)
            bericht["instrumente"]["stimmen"] = _stimmen(conn)
        finally:
            conn.close()

    bericht["instrumente"]["testboden"] = _testboden(tests)
    bericht["instrumente"]["abnahmeprobe"] = _abnahmeprobe()

    bericht["zusammenfassung"] = [
        v.get("zeile", f"{k}: keine Zeile") for k, v in bericht["instrumente"].items()
    ]
    return bericht


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python3 -m clayverse.selbstmessung",
        description="EIN Bericht ueber den echten, gemessenen Selbstzustand -- keine Behauptung.",
    )
    ap.add_argument("--db", default=None, help=f"Pfad zur wiki.db (Standard: {STANDARD_DB_PFAD})")
    ap.add_argument(
        "--tests",
        choices=("ueberspringen", "schnell", "voll"),
        default="ueberspringen",
        help="ueberspringen (Standard, billig) | schnell (nur diese Test-Datei) | voll (ganze Suite, teuer)",
    )
    ap.add_argument("--kompakt", action="store_true", help="JSON ohne Einrueckung ausgeben")
    ns = ap.parse_args(argv)

    bericht = erstelle_bericht(pfad=ns.db, tests=ns.tests)
    if ns.kompakt:
        print(json.dumps(bericht, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(bericht, ensure_ascii=False, indent=2, sort_keys=False))
    return 0


def main() -> None:  # pragma: no cover - trivialer Einstiegspunkt
    sys.exit(_cli())


if __name__ == "__main__":  # pragma: no cover
    main()
