from __future__ import annotations

"""Prozessuebergreifende Weckglocke fuer ClayVerse.

WOZU DAS DA IST
================
`wake_condition.py` liefert `naechste_pruefung()` -- den naechsten Zeitpunkt,
zu dem sich mechanisch etwas aendern KANN. Gemessen ist aber: fuer die zwei
haeufigsten Faelle -- ein Effekt schliesst ab (EFFECT_TERMINAL), ein Mensch
schreibt eine neue Nachricht (RESOURCE_REVISION auf
`session_turn_count:<session_id>`) -- traegt eine WakeCondition typischerweise
KEINE deadline. `naechste_pruefung()` liefert dann `None`. Ein Governor, der
nur auf diese Funktion vertraut, wuerde fuer genau diese beiden Faelle nie
wieder von selbst nachsehen und bliebe am 30s-Puls haengen, den er ersetzen
soll (Schattenlauf: 2769 von 2880 Takten leer, 96,1 %).

Dieses Modul ist der fehlende ereignisgebundene Zweig: eine Glocke, die an der
Schreibstelle laeutet ("hier hat sich etwas geaendert"), plus eine Funktion,
die daraus die Bedingungen herausfiltert, die dadurch weckbar wurden. Es ist
KEIN Scheduler und KEIN Governor -- es entscheidet nichts, es meldet nur.

WARUM EINE TABELLE UND KEIN MODUL-GLOBALES SET
================================================
Der 30s-Puls laeuft im FastAPI-Prozess (`autonomy_pulse.py`). Die Schreibungen,
auf die er reagieren soll, passieren in ANDEREN Prozessen: Claude-Hooks rufen
`turn_lifecycle.py` ueber eigene Prozesse auf, `effect_journal.py` wird von der
Werkzeugausfuehrung aus erreicht. Ein `set()` im Python-Interpreter des
FastAPI-Prozesses saehe von diesen Schreibungen nie etwas. Die kanonische
UnifiedDB ist bereits die einzige Stelle, die alle Prozesse gemeinsam sehen --
also entsteht hier eine kleine, eigene Tabelle darin (append-artig, siehe
Buendelung unten), kein zweiter Zustandsspeicher.

WARUM EINE EIGENE TABELLE UND NICHT `store.SCHEMA`
====================================================
`UnifiedDB.SCHEMA` wird nur einmal, beim Verbindungsaufbau, per
`executescript()` angelegt -- das waere der sauberste Ort, WENN dieses Modul
Teil des Kernvertrags waere. Es ist aber ein optionaler Zusatzbaustein (der
Governor, der ihn liest, existiert noch nicht scharf geschaltet, siehe
`wait` in `autonomy_planner.py`). Der etablierte Weg fuer genau diesen Fall
steht bereits im Repo vor: `memory.py`s `MemoryManager.__init__` legt
`turn_compressions` per `executescript(COMPRESSION_SCHEMA)` an -- EINMALIG bei
der Konstruktion des Objekts, NIE innerhalb einer offenen Schreibklammer
(`store.py:tx()`). Dieses Modul folgt exakt demselben Bauplan: `WakeSignal.__init__`
legt die Tabelle an, `melden()`/`seit()` sind danach reine `execute()`-Aufrufe
(kein `executescript()` mehr), also unbedenklich innerhalb einer offenen
Transaktion wie der in `turn_lifecycle.py:begin_admission()` (siehe deren
Kommentar bei Zeile 197-208: genau ein `executescript()` mitten in dieser
Klammer hat schon einmal vier von vier Zuegen mit
`OperationalError: cannot commit - no transaction is active` zerrissen).
Tabellenname `wake_events` gegen die 87+ Tabellen der echten `/var/lib/clay/wiki.db`
geprueft (2026-08-21, `sqlite3 wiki.db .tables`) -- frei.

BUENDELUNG STATT FLUT
=======================
`melden()` schreibt nicht "eine Zeile pro Ereignis", sondern haelt GENAU eine
Zeile je `coalesce_key` (PRIMARY KEY, per `INSERT ... ON CONFLICT DO UPDATE`).
Der Schluessel entsteht ueber `wake_condition.neue_coalesce_key(kind,
subject_ref)` -- dieselbe Mechanik wie im Vertrag, nicht neu erfunden. 10.000
Abschluesse DESSELBEN Effekts oder 10.000 neue Nachrichten IN DERSELBEN Session
sind dadurch mechanisch eine einzige Zeile mit aktualisiertem `ts` und
hochgezaehltem `count` -- kein Wachstum durch Wiederholung, nur durch echte
NEUE Subjekte (neue Effekt-IDs, neue Sessions).

BESCHRAENKTES WACHSTUM (VERFALL)
==================================
Buendelung allein reicht nicht: jeder abgeschlossene Effekt hat eine EIGENE
`effect_id`, also einen eigenen `coalesce_key` -- die Zeilenzahl waechst mit
der Zahl der jemals abgeschlossenen Effekte, nicht mit Wiederholungen. Deshalb
verfallen Zeilen aelter als `RETENTION_SECONDS` (1h = 3600s). Begruendung fuer
die Zahl: der Governor, den diese Tabelle bedienen soll, prueft im schlimmsten
Fall alle `MINDESTABSTAND` (5s, siehe wake_condition.py) bis alle
`AUTONOMY_PULSE`-Takte (30s) -- eine Ausfallzeit von wenigen Minuten (Neustart,
Deploy) darf also nicht schon zu einem verpassten Weckgrund fuehren. 1h ist
grosszuegig genug fuer jede realistische Downtime dieses Prozesses und trotzdem
um Groessenordnungen kleiner als der dokumentierte Vorfall (128.000
Leerschreibungen = 17,5 GB WAL, siehe `store.py`-Nachbarkommentare): selbst bei
mehreren hundert Effektabschluessen pro Stunde bleibt die Tabelle im
niedrigen dreistelligen Zeilenbereich.

Das Aufraeumen laeuft NICHT bei jedem einzelnen `melden()`-Aufruf (das waere
ein DELETE mit Tabellenscan im heissesten Pfad des Systems), sondern
gedrosselt: hoechstens einmal pro `SWEEP_MINDESTABSTAND` (60s) und nur als
Anhang an einen ohnehin stattfindenden Schreibvorgang. Bei Ueberlappung
mehrerer Prozesse ist ein doppelter Sweep harmlos (DELETE ist idempotent) --
es gibt bewusst keine prozessuebergreifende Sperre dafuer, das waere
Komplexitaet ohne Nutzen.

FAIL-CLOSED, NIE FAIL-SILENT (siehe absicht.py:buchen())
===========================================================
`melden()` laeuft im heissesten Pfad des Systems (`begin_admission()`,
`effect_journal._finish_tx()`) und darf einen Zug NIEMALS kippen -- deshalb
kein `raise`. Aber ein verschluckter Ausfall sieht sonst genauso aus wie "kein
Ereignis" (siehe `absicht.py`, wo genau diese Verwechslung schon einmal
passierte). Deshalb: Zaehler `AUSFAELLE` + eine Zeile auf stderr bei jedem
Fehlschlag, niemals ein stilles `except: pass`.
"""

import sys
import time
from typing import Any, Iterable

from .store import UnifiedDB
from .wake_condition import (  # dieselben vier Arten wie im Vertrag -- importiert, nicht neu getippt
    KIND_AT_TIME,
    KIND_EFFECT_TERMINAL,
    KIND_GOAL_STATE,
    KIND_RESOURCE_REVISION,
    MAX_COALESCE_KEY_CHARS,
    MAX_SUBJECT_REF_CHARS,
    WAKE_CONDITION_KINDS,
    WakeCondition,
    neue_coalesce_key,
)

_TABELLE = """
CREATE TABLE IF NOT EXISTS wake_events(
    coalesce_key TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    subject_ref TEXT,
    ts REAL NOT NULL,
    first_ts REAL NOT NULL,
    count INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_wake_events_ts ON wake_events(ts);
"""

# Siehe Docstring "BESCHRAENKTES WACHSTUM": 1h Verfallsfenster, 60s Sweep-Abstand.
RETENTION_SECONDS = 3600.0
SWEEP_MINDESTABSTAND = 60.0

# Wie oft `melden()` stillschweigend gescheitert waere -- siehe absicht.py:AUSFAELLE,
# dasselbe Muster. Modul-global, weil `WakeSignal`-Objekte kurzlebig sind (pro
# TurnLifecycle/EffectJournal-Instanz neu gebaut) und ein Instanzzaehler die
# Ausfaelle beim naechsten Zug wieder auf 0 setzen wuerde.
AUSFAELLE = 0
_letzter_sweep = 0.0


class WakeSignal:
    """Duenner Melder auf einer UnifiedDB. Kein Urteil, keine Bedingungslogik --
    das bleibt vollstaendig `wake_condition.py` vorbehalten."""

    def __init__(self, db: UnifiedDB):
        self.db = db
        # Einmalig bei Konstruktion, NIE innerhalb einer offenen Schreibklammer --
        # siehe Docstring oben und `memory.py:MemoryManager.__init__` als Vorbild.
        self.db.db.executescript(_TABELLE)

    def melden(self, kind: str, subject_ref: str, *, jetzt: float | None = None) -> bool:
        """An dieser Stelle hat sich etwas geaendert. Wirft NIE -- siehe Docstring
        FAIL-CLOSED. Rueckgabe ist nur fuer Tests/Diagnose gedacht, kein Aufrufer
        im heissen Pfad darf sein Ergebnis auswerten muessen."""
        global AUSFAELLE, _letzter_sweep
        if kind not in WAKE_CONDITION_KINDS:
            # Fail-closed auch hier: eine Art, die der Vertrag nicht kennt, wird
            # nicht aufgeschrieben -- sonst koennte ein Governor sie nie einer
            # WakeCondition zuordnen und haette stillen Muell in der Tabelle.
            AUSFAELLE += 1
            print(f"wake_signal: unbekannte Art verworfen ({AUSFAELLE}. Ausfall): {kind!r}", file=sys.stderr)
            return False
        try:
            wert_jetzt = time.time() if jetzt is None else float(jetzt)
            subject_ref = str(subject_ref)[:MAX_SUBJECT_REF_CHARS]
            key = neue_coalesce_key(kind, subject_ref)[:MAX_COALESCE_KEY_CHARS]
            self.db.db.execute(
                "INSERT INTO wake_events(coalesce_key,kind,subject_ref,ts,first_ts,count) "
                "VALUES(?,?,?,?,?,1) "
                "ON CONFLICT(coalesce_key) DO UPDATE SET ts=excluded.ts, count=count+1",
                (key, kind, subject_ref, wert_jetzt, wert_jetzt),
            )
            # Gedrosseltes Aufraeumen -- siehe Docstring BESCHRAENKTES WACHSTUM.
            wanduhr = time.time()
            if wanduhr - _letzter_sweep >= SWEEP_MINDESTABSTAND:
                _letzter_sweep = wanduhr
                self.db.db.execute("DELETE FROM wake_events WHERE ts < ?", (wanduhr - RETENTION_SECONDS,))
            return True
        except Exception as exc:
            AUSFAELLE += 1
            # Bewusst nur stderr, kein raise: der Melder darf den Zug nicht
            # kippen (siehe absicht.py:buchen()). Aber "kein Ereignis" und
            # "nicht gemessen" muessen unterscheidbar bleiben.
            print(f"wake_signal: Meldung fehlgeschlagen ({AUSFAELLE}. Mal): "
                  f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return False

    def seit(self, seit_ts: float, *, kinds: Iterable[str] | None = None) -> list[dict[str, Any]]:
        """Alle gebuendelten Ereigniszeilen mit `ts > seit_ts`. Liest, schreibt nie --
        darf also frei ausserhalb jeder Schreibklammer aufgerufen werden."""
        query = "SELECT coalesce_key,kind,subject_ref,ts,first_ts,count FROM wake_events WHERE ts > ?"
        params: list[Any] = [float(seit_ts)]
        kinds = list(kinds) if kinds is not None else None
        if kinds:
            platzhalter = ",".join("?" for _ in kinds)
            query += f" AND kind IN ({platzhalter})"
            params.extend(kinds)
        query += " ORDER BY ts"
        rows = self.db.db.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def weckbar(bedingungen: Iterable[WakeCondition], ereignisse: Iterable[dict[str, Any]]) -> list[WakeCondition]:
    """Ergaenzt `naechste_pruefung()` um den ereignisgebundenen Zweig.

    `naechste_pruefung()` beantwortet "wann fruehestens erneut pruefen wegen der
    ZEIT". Diese Funktion beantwortet die andere Haelfte: "welche Bedingungen
    sind durch ein bereits eingetretenes EREIGNIS pruefwuerdig geworden, auch
    wenn sie gar keine deadline/earliest_at tragen (also `naechste_pruefung()`
    fuer sie `None` liefert)". Sie ERSETZT `pruefen()` nicht -- sie sagt nur,
    WELCHE Bedingungen ein Governor jetzt zusaetzlich mit `pruefen()`
    tatsaechlich nachpruefen sollte, statt blind alle oder gar keine.

    Abgleich ueber (kind, subject_ref), NICHT ueber `coalesce_key`: der
    `coalesce_key` einer WakeCondition wird vom ZIEL-Ersteller (dem noch nicht
    scharf geschalteten Planer) frei vergeben und muss nicht mit dem
    `coalesce_key` uebereinstimmen, unter dem `melden()` das Ereignis intern
    buendelt. `subject_ref` dagegen ist in `wake_condition.py` fest an das
    beobachtete Objekt gebunden (effect_id bzw. `session_turn_count:<id>`) --
    das ist der einzige Schluessel, der auf beiden Seiten garantiert dasselbe
    Ding meint.

    Deckt heute nur die zwei tatsaechlich verdrahteten Haken ab (EFFECT_TERMINAL
    in effect_journal.py, RESOURCE_REVISION/session_turn_count in
    turn_lifecycle.py). AT_TIME und GOAL_STATE sowie andere RESOURCE_REVISION-
    Subjekte (entity_generation, autonomy_revision, session_generation) haben
    keinen Melder -- fuer sie liefert diese Funktion nichts, bis ein spaeterer
    Baustein dort ebenfalls meldet. Das ist eine bewusste Luecke, keine
    versteckte: `naechste_pruefung()` bleibt fuer AT_TIME der einzige Weg.
    """
    vorhanden = {(str(e.get("kind")), str(e.get("subject_ref"))) for e in ereignisse}
    return [b for b in bedingungen if (b.kind, b.subject_ref) in vorhanden]
