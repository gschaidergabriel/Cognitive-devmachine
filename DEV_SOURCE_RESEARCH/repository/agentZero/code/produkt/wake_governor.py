from __future__ import annotations

"""Governor -- der dritte und letzte Baustein des Weckwerks.

Vertrag (`wake_condition.py`) und Glocke (`wake_signal.py`) beantworten je eine
eigene Frage: "ist diese eine Bedingung mechanisch erfuellt?" und "an welcher
Stelle hat sich seit kurzem etwas geaendert?". Beide entscheiden nichts ueber
den Betrieb selbst. Dieses Modul ist die erste Stelle, die die beiden Zweige
tatsaechlich zusammenfuehrt und daraus EINE betriebliche Frage beantwortet:

    Welche wartenden Bedingungen sind JETZT pruefwuerdig, und darf JETZT
    tatsaechlich geweckt werden?

Der Governor entscheidet NICHT, was nach dem Wecken geschieht -- das bleibt
vollstaendig `AutonomyPlanner`/`AutonomyController` vorbehalten (siehe
autonomy_planner.py: DECISION_KINDS enthaelt weiterhin kein "wait", solange
dieses Modul nicht unabhaengig gemessen scharf geschaltet ist, siehe unten).

⚠️ DIE EINE REGEL, DIE DIESES MODUL TRAEGT: UNBEKANNT ist ein Messausfall,
kein Befund. Jede Funktion hier haelt sich an drei Punkte, sonst waere der
ganze Vertrag aus wake_condition.py wertlos:
  1. UNBEKANNT wird NIE wie ERFUELLT behandelt (kein Wecken).
  2. UNBEKANNT wird NIE stillschweigend zu "nicht eingetreten" (OFFEN) --
     es bleibt sichtbar unterscheidbar, wird gezaehlt und auf stderr gemeldet
     (siehe `_unbekannt_melden`, dasselbe Muster wie `wake_signal.AUSFAELLE`).
  3. UNBEKANNT darf die Deadline-Uhr nicht stillschweigend weiterlaufen lassen,
     als waere ordentlich geprueft worden: `naechster_takt()` erzwingt bei
     JEDER aktuell fälligen UNBEKANNT-Bedingung einen Wiederholungsversuch
     spaetestens nach MINDESTABSTAND -- nie ein `None` (ewiger Schlaf), nur
     weil eine Bedingung selbst keine deadline traegt (siehe dort).
"""

import json
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Any, Iterable

from .store import UnifiedDB
from .wake_condition import (
    MINDESTABSTAND,
    ZUSTAND_ERFUELLT,
    ZUSTAND_UNBEKANNT,
    ZUSTAND_ZEITABLAUF,
    WakeCondition,
    buendeln,
    ist_dringend_faehig,
    naechste_pruefung,
    pruefen,
    wecken_erlaubt,
)
from .wake_signal import WakeSignal, weckbar

# ---------------------------------------------------------------------------
# Messausfall-Zaehlung -- dasselbe Muster wie wake_signal.AUSFAELLE: ein
# Modul-globaler Zaehler statt eines Instanzzaehlers, weil Governor-Aufrufe
# (wie WakeSignal-Objekte) kurzlebig und pro Tick neu sind.
# ---------------------------------------------------------------------------
UNBEKANNT_ZAEHLER = 0


def _unbekannt_melden(bedingung: WakeCondition, ergebnis: dict[str, Any]) -> None:
    global UNBEKANNT_ZAEHLER
    UNBEKANNT_ZAEHLER += 1
    print(
        f"wake_governor: Messausfall ({UNBEKANNT_ZAEHLER}. Mal) bei Bedingung "
        f"kind={bedingung.kind!r} goal_id={bedingung.goal_id!r} step_id={bedingung.step_id!r}: "
        f"{ergebnis['grund']}",
        file=sys.stderr,
    )


@dataclass(frozen=True)
class Faellig:
    """Eine Bedingung, die JETZT pruefwuerdig war, plus ihr `pruefen()`-Ergebnis
    und woher die Faelligkeit kam -- fuer Diagnose/Metriken, aendert nichts an
    der Auswertung selbst."""

    bedingung: WakeCondition
    ergebnis: dict[str, Any]
    quelle: str  # "zeit" | "ereignis" | "zeit+ereignis"


# ---------------------------------------------------------------------------
# 1) faellige() -- vereinigt den zeitgesteuerten und den ereignisgesteuerten Zweig
# ---------------------------------------------------------------------------

def faellige(
    bedingungen: Iterable[WakeCondition],
    db: UnifiedDB,
    jetzt: float,
    *,
    wake_signal: WakeSignal | None = None,
) -> list[Faellig]:
    """Welche der uebergebenen Bedingungen sind JETZT pruefwuerdig, und was
    ergibt `pruefen()` fuer jede davon?

    Zwei unabhaengige Gruende machen eine Bedingung faellig:
      - ZEIT: `earliest_at` oder `deadline` liegt nicht mehr in der Zukunft.
        Das ist bewusst eine direkte `<= jetzt`-Pruefung und NICHT
        `naechste_pruefung()` -- jene liefert nur zukuenftige Kandidaten (fuer
        die Ablaufplanung), waehrend hier genau die bereits FAELLIGEN
        Zeitpunkte gebraucht werden.
      - EREIGNIS: `weckbar()` fand ein passendes gemeldetes Ereignis
        (`WakeSignal.seit`). `seit(0.0)` genuegt als Fenster -- `wake_events`
        vergisst sich selbst nach RETENTION_SECONDS (siehe wake_signal.py
        BESCHRAENKTES WACHSTUM), ein zweiter Vergiss-Mechanismus hier waere
        doppelt gebaut.

    Jede faellige Bedingung wird GENAU EINMAL mit `pruefen()` ausgewertet --
    auch wenn beide Gruende gleichzeitig zutreffen (`quelle="zeit+ereignis"`).
    Das Ergebnis wird roh zurueckgegeben (inkl. UNBEKANNT); dieser Aufrufer
    entscheidet NICHTS darueber, das bleibt den Aufrufern von `faellige()`
    vorbehalten (siehe `entscheiden()` unten fuer die naechste Schicht).

    ⚠️ Bewusste, dokumentierte Luecke (uebernommen aus wake_signal.py:weckbar):
    eine Bedingung ohne earliest_at/deadline UND ohne verdrahteten Melder
    (heute: AT_TIME hat immer earliest_at also nie betroffen; GOAL_STATE und
    die uebrigen RESOURCE_REVISION-Subjekte OHNE deadline) wird von diesem
    Governor NIE faellig -- es gibt fuer sie schlicht keinen mechanischen
    Ausloeser. Das ist keine neue Luecke, nur eine, die hier sichtbar bleibt
    statt versteckt zu werden.
    """
    bedingungen = list(bedingungen)
    signal = wake_signal if wake_signal is not None else WakeSignal(db)
    ereignisse = signal.seit(0.0)
    # Bewusst eine LISTE, kein `set()`: WakeCondition ist ein frozen dataclass,
    # dessen `__hash__` bei einem dict-Feld (`expected_predicate`, bei allen
    # ausser AT_TIME belegt) zur Laufzeit mit TypeError scheitert. Der
    # Mitgliedstest unten (`in`) braucht nur `__eq__`, das mit einem dict-Feld
    # anstandslos funktioniert -- also reicht die Liste, ein `set()` waere ein
    # Absturz auf dem haeufigsten Pfad gewesen (nicht der seltene AT_TIME-Fall).
    ereignisgebunden = weckbar(bedingungen, ereignisse)

    ergebnisse: list[Faellig] = []
    for bedingung in bedingungen:
        zeit_faellig = (
            bedingung.earliest_at is not None and bedingung.earliest_at <= jetzt
        ) or (
            bedingung.deadline is not None and bedingung.deadline <= jetzt
        )
        ereignis_faellig = bedingung in ereignisgebunden
        if not (zeit_faellig or ereignis_faellig):
            continue
        ergebnis = pruefen(bedingung, db, jetzt)
        if ergebnis["zustand"] == ZUSTAND_UNBEKANNT:
            _unbekannt_melden(bedingung, ergebnis)
        if zeit_faellig and ereignis_faellig:
            quelle = "zeit+ereignis"
        elif zeit_faellig:
            quelle = "zeit"
        else:
            quelle = "ereignis"
        ergebnisse.append(Faellig(bedingung, ergebnis, quelle))
    return ergebnisse


# ---------------------------------------------------------------------------
# 2) naechster_takt() -- wann muss der Governor fruehestens wieder laufen?
# ---------------------------------------------------------------------------

def naechster_takt(bedingungen: Iterable[WakeCondition], db: UnifiedDB, jetzt: float) -> float | None:
    """Der Kern von "self-triggered": statt stur alle 30s nachzusehen (der
    heutige Puls, siehe autonomy_pulse.py), errechnet dies den fruehesten
    Zeitpunkt, zu dem sich mechanisch ueberhaupt etwas aendern KANN.

    Zwei Kandidaten, das Minimum gewinnt:
      1. `naechste_pruefung()` -- der reine Zeit-Zweig aus wake_condition.py,
         unveraendert uebernommen (auch dessen bewusster Verzicht auf eine
         MINDESTABSTAND-Klammer, siehe dortige Begruendung: eine nahe Deadline
         darf nicht hinter den Mindestabstand rutschen).
      2. Der UNBEKANNT-Wiederholungs-Boden: ruft intern `faellige()` auf
         denselben Bedingungen auf (dieselbe Quelle der Wahrheit, keine
         zweite, driftende Kopie der Faelligkeitslogik) und prueft, ob
         darunter ein Messausfall (UNBEKANNT) war. Wenn ja: spaetestens in
         MINDESTABSTAND Sekunden erneut nachsehen -- NIE `None`, auch wenn
         Kandidat 1 `None` liefert (rein ereignisgebundene Bedingung) oder
         eine ferne Zukunft nennt. Das ist die technische Umsetzung von
         "UNBEKANNT laesst die Deadline-Uhr nicht so weiterlaufen, als waere
         ordentlich geprueft worden": ein fehlgeschlagener Lesevorgang jetzt
         darf NIE dazu fuehren, dass der Governor bis zu einer fernen
         statischen Deadline schlaeft und den Ausfall gar nicht erst erneut
         anschaut.

    `faellige()` zaehlt/meldet UNBEKANNT bereits selbst -- dieser Aufruf
    zaehlt also nicht doppelt, er liest nur das bereits gemeldete Ergebnis.
    """
    bedingungen = list(bedingungen)
    zeit_kandidat = naechste_pruefung(bedingungen, jetzt)

    ergebnisse = faellige(bedingungen, db, jetzt)
    unbekannt_kandidat = None
    if any(f.ergebnis["zustand"] == ZUSTAND_UNBEKANNT for f in ergebnisse):
        unbekannt_kandidat = jetzt + MINDESTABSTAND

    kandidaten = [w for w in (zeit_kandidat, unbekannt_kandidat) if w is not None]
    return min(kandidaten) if kandidaten else None


# ---------------------------------------------------------------------------
# 3) Anti-Zeno DURCHGESETZT: eine einzige Entscheidungsfunktion, die
#    wecken_erlaubt()/ist_dringend_faehig() nicht optional macht, sondern in
#    die Rueckgabe einbaut -- ein Aufrufer kann den Schritt nicht vergessen.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WeckEntscheidung:
    """Das vollstaendige Ergebnis eines Governor-Takts.

    `soll_wecken` ist bereits die durchgesetzte Anti-Zeno-Entscheidung
    (`wecken_erlaubt()` inklusive `ist_dringend_faehig()`-Uebersteuerung) --
    kein Aufrufer muss diese zwei Funktionen selbst noch verketten, und kann
    sie folglich auch nicht vergessen.

    `unbekannt` ist niemals Teil von `auslöser`/`soll_wecken` -- ein
    Messausfall weckt nie, egal wie viele es gerade gibt (siehe Modul-Docstring
    Punkt 1).
    """

    soll_wecken: bool
    dringend: bool
    auslöser: list[tuple[WakeCondition, dict[str, Any]]]  # ERFUELLT + ZEITABLAUF, gebuendelt
    unbekannt: list[tuple[WakeCondition, dict[str, Any]]]
    naechster_takt: float | None
    grund: str


def entscheiden(
    bedingungen: Iterable[WakeCondition],
    db: UnifiedDB,
    jetzt: float,
    *,
    letzter_weckzeitpunkt: float | None,
    wake_signal: WakeSignal | None = None,
) -> WeckEntscheidung:
    """Fasst faellige()/naechster_takt()/wecken_erlaubt()/ist_dringend_faehig()
    zu der einen Antwort zusammen, die der Modul-Docstring verspricht.

    ERFUELLT und ZEITABLAUF zaehlen beide als Weckgrund: beides sind
    TERMINALE, mechanisch belegte Ausgaenge, ueber die der Aufrufer (Planer/
    Controller) informiert werden muss -- ZEITABLAUF ist "die Gelegenheit ist
    unwiderruflich vorbei", kein Rauschen (siehe wake_condition.py:
  `_pruefe_effect_terminal`/`_pruefe_goal_state`, dieselbe Begruendung).
    UNBEKANNT ist NIE ein Weckgrund (siehe Modul-Docstring Punkt 1) -- es
    landet ausschliesslich in `unbekannt`, niemals in `auslöser`.

    ⚠️ Aus genau diesem Grund darf ein Aufrufer, der `soll_wecken` als "letzter
    Weckzeitpunkt" fuer den naechsten Aufruf von `wecken_erlaubt()` mitfuehrt,
    diesen Zeitpunkt NUR aktualisieren, wenn `soll_wecken` hier True war --
    ein reiner UNBEKANNT-Takt (soll_wecken=False, unbekannt nicht leer) ist
    kein Wecken und darf die Anti-Zeno-Uhr nicht so weiterlaufen lassen, als
    waere tatsaechlich geweckt worden (dieselbe Regel wie bei der Deadline-Uhr
    in naechster_takt(), nur auf der Wecken-statt-Pruefen-Seite).
    """
    ergebnisse = faellige(bedingungen, db, jetzt, wake_signal=wake_signal)

    auslöser_roh = [
        (f.bedingung, f.ergebnis)
        for f in ergebnisse
        if f.ergebnis["zustand"] in (ZUSTAND_ERFUELLT, ZUSTAND_ZEITABLAUF)
    ]
    unbekannt = [
        (f.bedingung, f.ergebnis) for f in ergebnisse if f.ergebnis["zustand"] == ZUSTAND_UNBEKANNT
    ]
    auslöser = buendeln(auslöser_roh)

    dringend = any(ist_dringend_faehig(b) for b, _ in auslöser)
    soll_wecken = bool(auslöser) and wecken_erlaubt(letzter_weckzeitpunkt, jetzt, dringend=dringend)

    takt = naechster_takt(bedingungen, db, jetzt)

    erfuellt_n = sum(1 for _, e in auslöser if e["zustand"] == ZUSTAND_ERFUELLT)
    zeitablauf_n = sum(1 for _, e in auslöser if e["zustand"] == ZUSTAND_ZEITABLAUF)
    if not ergebnisse:
        grund = "keine Bedingung faellig"
    elif soll_wecken:
        grund = f"{erfuellt_n} erfuellt, {zeitablauf_n} zeitabgelaufen -> Wecken erlaubt (dringend={dringend})"
    elif auslöser:
        grund = f"{erfuellt_n} erfuellt, {zeitablauf_n} zeitabgelaufen, aber Mindestabstand ({MINDESTABSTAND}s) verhindert Wecken"
    else:
        grund = f"nur Messausfaelle ({len(unbekannt)}) -- kein Weckgrund"

    return WeckEntscheidung(
        soll_wecken=soll_wecken,
        dringend=dringend,
        auslöser=auslöser,
        unbekannt=unbekannt,
        naechster_takt=takt,
        grund=grund,
    )


# ---------------------------------------------------------------------------
# Persistenz fuer WakeCondition-Objekte: registrieren, offene lesen, mit
# Endzustand abschliessen. `als_dict()` liegt in wake_condition.py bereits
# fertig und war bisher ungenutzt -- dieser Speicher ist der erste Verbraucher.
# ---------------------------------------------------------------------------

_CONDITIONS_TABELLE = """
CREATE TABLE IF NOT EXISTS wake_conditions(
    condition_id TEXT PRIMARY KEY,
    schema TEXT NOT NULL,
    kind TEXT NOT NULL,
    subject_ref TEXT,
    expected_predicate TEXT,
    earliest_at REAL,
    deadline REAL,
    goal_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    generation INTEGER NOT NULL,
    coalesce_key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OFFEN' CHECK(status IN ('OFFEN','ERFUELLT','ZEITABLAUF')),
    registered_at REAL NOT NULL,
    resolved_at REAL,
    resolved_grund TEXT,
    UNIQUE(goal_id, step_id)
);
CREATE INDEX IF NOT EXISTS idx_wake_conditions_status ON wake_conditions(status);
"""
# Tabellenname gegen die echten wiki.db-Tabellen geprueft (2026-08-21,
# `sqlite3 -readonly wiki.db .tables`) -- frei, kein Konflikt mit
# `wake_events` (wake_signal.py) oder einer der 87+ Bestandstabellen.
#
# UNIQUE(goal_id, step_id): genau EIN Wait-Grund je Schritt. Ein Schritt, der
# eine zweite Bedingung braucht, ist ein neuer Schritt -- kein Nachtragen an
# eine bestehende Zeile (dieselbe Bauart wie `AutonomyController.propose_step`:
# ein Schritt hat genau einen aktuellen Zustand, kein Anhaengen).
#
# ⚠️ GENERATION-FENCING: `offene()` liest `generation` unveraendert aus der
# Zeile und reicht es unangetastet an `WakeCondition.aus_dict()` weiter --
# NIE auf die aktuell laufende Generation "aktualisiert". Der einzige Ort, der
# entscheidet, ob eine Generation noch gueltig ist, bleibt `pruefen()`
# (`wake_condition.py`, Kommentar "Generation zuerst"). Eine zweite Kopie
# dieser Pruefung hier waere genau die Art doppelt gebauter Logik, die schon
# einmal (EFFECT_TERMINAL_STATES) explizit vermieden wurde, weil zwei Kopien
# irgendwann auseinanderlaufen.
#
# ⚠️ BEKANNTE, NICHT BEHOBENE LUECKE: eine Bedingung aus einer VERWORFENEN
# Generation bleibt in dieser Tabelle auf ewig 'OFFEN' stehen, weil `pruefen()`
# fuer sie fuer immer UNBEKANNT liefert (nie ERFUELLT/ZEITABLAUF) und
# `abschliessen()` bewusst NUR diese zwei Endzustaende akzeptiert (siehe
# dort). Generationswechsel sind im System selten (Neustart/Reset ueber
# `advance_entity_generation`, siehe `autonomy.py:recover_generation` als
# bestehendes Vorbild fuer aehnliches Rebinding) -- das haelt das Wachstum
# klein, behebt die Luecke aber nicht. Ein Aufraeumer dafuer ist NICHT Teil
# dieses Auftrags (nur registrieren/offene lesen/abschliessen) und wird hier
# bewusst nicht miterfunden.


class WakeConditionStore:
    """Schmale Persistenz auf einer UnifiedDB. Kein Urteil, keine
    Bedingungslogik -- das bleibt vollstaendig wake_condition.py vorbehalten,
    genau wie bei WakeSignal (siehe dortiger Docstring)."""

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.db.db.executescript(_CONDITIONS_TABELLE)

    def registrieren(self, bedingung: WakeCondition) -> str:
        """Legt eine bereits validierte WakeCondition (aus `aus_dict()`) als
        offene Zeile an. `condition_id` ist der einzige neue, hier vergebene
        Bezeichner -- `goal_id`/`step_id`/`coalesce_key` kommen unveraendert
        von der Bedingung selbst."""
        payload = bedingung.als_dict()
        condition_id = str(uuid.uuid4())
        expected_predicate = (
            json.dumps(payload["expected_predicate"], sort_keys=True, separators=(",", ":"))
            if payload["expected_predicate"] is not None
            else None
        )
        self.db.db.execute(
            "INSERT INTO wake_conditions(condition_id,schema,kind,subject_ref,expected_predicate,"
            "earliest_at,deadline,goal_id,step_id,generation,coalesce_key,status,registered_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,'OFFEN',?)",
            (
                condition_id,
                payload["schema"],
                payload["kind"],
                payload["subject_ref"],
                expected_predicate,
                payload["earliest_at"],
                payload["deadline"],
                payload["goal_id"],
                payload["step_id"],
                payload["generation"],
                payload["coalesce_key"],
                time.time(),
            ),
        )
        return condition_id

    def offene(self) -> list[WakeCondition]:
        """Alle offenen Bedingungen, rekonstruiert AUSSCHLIESSLICH ueber
        `WakeCondition.aus_dict()` -- derselbe geprueft Weg wie bei der
        urspruenglichen Konstruktion (siehe wake_condition.py: "Objekte dieser
        Klasse entstehen ausschliesslich ueber aus_dict()"). Kein zweiter,
        ungeprueft Entstehungsweg ueber einen direkten Feld-Zusammenbau."""
        rows = self.db.db.execute(
            "SELECT schema,kind,subject_ref,expected_predicate,earliest_at,deadline,"
            "goal_id,step_id,generation,coalesce_key FROM wake_conditions WHERE status='OFFEN'"
        ).fetchall()
        ergebnis = []
        for row in rows:
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
            ergebnis.append(WakeCondition.aus_dict(payload))
        return ergebnis

    def abschliessen(self, condition_id: str, endzustand: str, grund: str) -> bool:
        """Schliesst genau eine offene Zeile mit einem TERMINALEN Zustand ab.

        Fail-closed auf genau ZWEI zulaessige Endzustaende: ERFUELLT und
        ZEITABLAUF. OFFEN ist kein Abschluss (dafuer gibt es keinen Aufruf --
        eine offene Bedingung bleibt einfach offen). UNBEKANNT ist NIE ein
        gueltiger Endzustand fuer diese Funktion -- genau das ist die
        Persistenz-Seite der zentralen Regel dieses Moduls: ein Messausfall
        schliesst eine Bedingung nicht ab, er wird nur gezaehlt/gemeldet
        (`_unbekannt_melden`) und die Zeile bleibt 'OFFEN' fuer den naechsten
        Versuch. Wer hier versehentlich UNBEKANNT einsetzen wollte, bekommt
        sofort einen ValueError statt eines stillschweigend falsch
        geschlossenen Weckgrunds.
        """
        if endzustand not in (ZUSTAND_ERFUELLT, ZUSTAND_ZEITABLAUF):
            raise ValueError(
                f"kein gueltiger Endzustand fuer die Persistenz: {endzustand!r} -- "
                "nur ERFUELLT/ZEITABLAUF schliessen eine Bedingung ab; UNBEKANNT ist "
                "ein Messausfall, kein Befund, und bleibt OFFEN (siehe Modul-Docstring)"
            )
        cur = self.db.db.execute(
            "UPDATE wake_conditions SET status=?, resolved_at=?, resolved_grund=? "
            "WHERE condition_id=? AND status='OFFEN'",
            (endzustand, time.time(), str(grund)[:2000], condition_id),
        )
        return cur.rowcount == 1
