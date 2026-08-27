from __future__ import annotations

"""Typisierter Wake-Condition-Vertrag fuer ClayVerse.

Kontext: `autonomy.py` kennt seit jeher einen `wait`-Schritt (STEP_KINDS), aber
`autonomy_planner.py` laesst ihn absichtlich nicht zu -- dort steht woertlich:
"The wait kind is intentionally unavailable until a typed wake-condition
contract exists." Dieses Modul ist genau dieser Vertrag. Es schaltet `wait`
NICHT scharf (DECISION_KINDS in autonomy_planner.py bleibt unveraendert) und
der bestehende 30s-Puls (autonomy_pulse.py) bleibt die einzige tatsaechlich
servierende Instanz. Hier entsteht nur die Typisierung + der Auswerter, an
denen ein spaeterer Governor andocken kann.

⚠️ ZENTRALE ENTSCHEIDUNG, WARUM ES NUR VIER ARTEN GIBT (keine freie SQL-
Bedingung, kein vom Modell erzeugter Code, keine natuerlichsprachige
Triggerlogik):

Eine Bedingung, die ein Sprachmodell formuliert ("wache auf, wenn der Nutzer
zufrieden wirkt"), ist keine Bedingung -- sie ist eine Behauptung. Eine
Bedingung muss MECHANISCH entscheidbar sein: ein fester Datentyp, ein fester
Satz Vergleichsoperationen, ein fester Ort im Zustand (effects-Tabelle,
autonomy-State, entity_generation, turns-Tabelle). Deshalb ist der Satz der
erlaubten `kind`-Werte geschlossen (WAKE_CONDITION_KINDS) und jede Bedingung
wird bei der Konstruktion (WakeCondition.aus_dict) gegen ein festes Schema
validiert -- niemals gegen freien Text oder freien SQL-String. Dass die
Auswertungsfunktionen selbst SQL benutzen, ist kein Widerspruch dazu: sie
benutzen FESTE, in diesem Modul geschriebene Abfragen fuer GENAU vier
Tabellen/Felder -- niemals eine vom Aufrufer mitgelieferte Abfrage.

⚠️ ZWEITE ZENTRALE ENTSCHEIDUNG: UNBEKANNT != ERFUELLT und UNBEKANNT != nicht
eingetreten.

An anderer Stelle im System ist genau diese Verwechslung schon einmal passiert:
ein Beobachter schrieb Ausfaelle in ein `except: pass`, wodurch "kein
Verdacht" (nichts gefunden) und "nicht gemessen" (Messung fehlgeschlagen)
gleich aussahen. `pruefen()` haelt diese drei Faelle in diesem Modul deshalb
strikt auseinander: ERFUELLT verlangt immer einen mechanischen Beleg,
UNBEKANNT bedeutet "nicht entscheidbar" und wird niemals stillschweigend zu
ERFUELLT oder OFFEN aufgewertet.
"""

import math
import uuid
from dataclasses import dataclass
from typing import Any

from .autonomy import GOAL_STATUSES, AutonomyController
from .effect_journal import EffectJournal
from .store import UnifiedDB

# ---------------------------------------------------------------------------
# Schema / Vertrag
# ---------------------------------------------------------------------------

WAKE_CONDITION_SCHEMA = "ClayVerseWakeCondition/v1"

KIND_AT_TIME = "AT_TIME"
KIND_EFFECT_TERMINAL = "EFFECT_TERMINAL"
KIND_RESOURCE_REVISION = "RESOURCE_REVISION"
KIND_GOAL_STATE = "GOAL_STATE"
WAKE_CONDITION_KINDS = {KIND_AT_TIME, KIND_EFFECT_TERMINAL, KIND_RESOURCE_REVISION, KIND_GOAL_STATE}

ZUSTAND_ERFUELLT = "ERFUELLT"
ZUSTAND_OFFEN = "OFFEN"
ZUSTAND_ZEITABLAUF = "ZEITABLAUF"
ZUSTAND_UNBEKANNT = "UNBEKANNT"
WAKE_ZUSTAENDE = {ZUSTAND_ERFUELLT, ZUSTAND_OFFEN, ZUSTAND_ZEITABLAUF, ZUSTAND_UNBEKANNT}

# Terminal-Effektzustaende sind eine einzige Quelle der Wahrheit: EffectJournal.FINAL.
# Diese Menge NICHT duplizieren -- sonst laufen die zwei Module irgendwann auseinander.
EFFECT_TERMINAL_STATES = EffectJournal.FINAL

# Goal-Zustaende, die (siehe autonomy.py: complete_goal/cancel_goal) nachweislich nie
# wieder verlassen werden: COMPLETED kann nicht mehr storniert werden, CANCELLED hat
# im Controller keinen Ruecksprung-Pfad. "Terminal" heisst hier also nicht Vermutung,
# sondern durch den Controller selbst erzwungen.
GOAL_TERMINAL_STATES = {"COMPLETED", "CANCELLED"}

# RESOURCE_REVISION beobachtet keine freie SQL-Abfrage, sondern genau diese drei
# geschlossenen Ressourcen-Arten -- die dritte ist ein Praefix-Muster fuer eine
# konkrete Session-ID, die restlichen zwei sind fest:
RESOURCE_KIND_ENTITY_GENERATION = "entity_generation"
RESOURCE_KIND_AUTONOMY_REVISION = "autonomy_revision"
RESOURCE_PREFIX_SESSION_GENERATION = "session_generation:"
# session_turn_count:<session_id> beobachtet die Anzahl der Nutzer-Turns einer Session
# -- der mechanische Nachweis fuer "ein Mensch hat etwas Neues gesagt" (menschliche
# Eingabe), ohne dass dafuer ein Modell etwas behaupten muss.
RESOURCE_PREFIX_SESSION_TURN_COUNT = "session_turn_count:"

MAX_ID_CHARS = 256
MAX_SUBJECT_REF_CHARS = 512
MAX_COALESCE_KEY_CHARS = 256

# Anti-Zeno-Mindestabstand zwischen zwei Weckvorgaengen. Kein neuer, frei erfundener
# Wert: das System kennt bereits eine Untergrenze fuer "wie oft ist ein Nachsehen
# ueberhaupt sinnvoll" -- autonomy_pulse.py:43 laesst den 30s-Puls nur im Bereich
# `5.0 <= interval <= 3600.0` zu. 5.0s ist also die im System bereits etablierte,
# gemessene Untergrenze; sie wird hier uebernommen statt neu geraten.
MINDESTABSTAND = 5.0

# Effekt-Endzustaende, bei denen ein Weckvorgang nicht auf den naechsten Takt warten
# darf (siehe ist_dringend_faehig): ein fehlgeschlagener/abgelehnter Effekt ist ein
# Ereignis, auf das reagiert werden muss, nicht eines, das man buendeln darf.
KRITISCHE_EFFEKT_ENDZUSTAENDE = {"DENIED", "FAILED", "STALE_OUTCOME", "UNKNOWN_AFTER_RESTART"}


class WakeConditionError(ValueError):
    """Fail-closed: eine Bedingung, die dieses Modul nicht sauber typisieren kann,
    existiert nicht. Der Grund steht immer im Text -- niemals stilles Verwerfen."""


def _zahl_oder_none(wert: Any, feld: str) -> float | None:
    if wert is None:
        return None
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):
        raise WakeConditionError(f"{feld} muss eine Zahl oder null sein")
    wert = float(wert)
    if not math.isfinite(wert):
        raise WakeConditionError(f"{feld} ist nicht endlich")
    if wert < 0:
        raise WakeConditionError(f"{feld} ist negativ")
    return wert


def _nichtleerer_string(wert: Any, feld: str, *, max_chars: int) -> str:
    if not isinstance(wert, str) or not wert or "\x00" in wert:
        raise WakeConditionError(f"{feld} muss ein nichtleerer String ohne Nullbyte sein")
    if len(wert) > max_chars:
        raise WakeConditionError(f"{feld} ueberschreitet {max_chars} Zeichen")
    return wert


@dataclass(frozen=True)
class WakeCondition:
    """Eine einzelne, unveraenderliche, bereits validierte Weckbedingung.

    Objekte dieser Klasse entstehen ausschliesslich ueber `WakeCondition.aus_dict()`
    -- der Konstruktor selbst prueft nichts, damit es keinen zweiten, ungeprueften
    Entstehungsweg gibt (dieselbe Bauart wie AutonomyController._validate_goal, das
    ebenfalls nur ueber einen einzigen geprueften Pfad Zustand erzeugt).
    """

    schema: str
    kind: str
    subject_ref: str | None
    expected_predicate: dict[str, Any] | None
    earliest_at: float | None
    deadline: float | None
    goal_id: str
    step_id: str
    generation: int
    coalesce_key: str

    REQUIRED_FIELDS = (
        "schema", "kind", "subject_ref", "expected_predicate", "earliest_at",
        "deadline", "goal_id", "step_id", "generation", "coalesce_key",
    )

    @classmethod
    def aus_dict(cls, payload: dict[str, Any]) -> "WakeCondition":
        """Fail-closed-Konstruktion. Jede Ablehnung traegt einen Grund im Text.

        Reihenfolge der Pruefungen: (1) Grundform/Schema, (2) Art bekannt,
        (3) gemeinsame Pflichtfelder (goal_id/step_id/generation/coalesce_key),
        (4) art-spezifische Felder (subject_ref/expected_predicate), (5) Zeitfenster
        (earliest_at/deadline, inkl. "Deadline vor earliest_at").
        """
        if not isinstance(payload, dict):
            raise WakeConditionError("wake condition payload muss ein Objekt sein")
        if set(payload) != set(cls.REQUIRED_FIELDS):
            fehlend = set(cls.REQUIRED_FIELDS) - set(payload)
            unerwartet = set(payload) - set(cls.REQUIRED_FIELDS)
            raise WakeConditionError(
                f"wake condition hat falsche Felder (fehlend={sorted(fehlend)}, "
                f"unerwartet={sorted(unerwartet)})"
            )
        if payload.get("schema") != WAKE_CONDITION_SCHEMA:
            raise WakeConditionError("wake condition schema mismatch")

        kind = payload.get("kind")
        if kind not in WAKE_CONDITION_KINDS:
            raise WakeConditionError(f"unbekannte Bedingungsart: {kind!r}")

        goal_id = _nichtleerer_string(payload.get("goal_id"), "goal_id", max_chars=MAX_ID_CHARS)
        step_id = _nichtleerer_string(payload.get("step_id"), "step_id", max_chars=MAX_ID_CHARS)
        coalesce_key = _nichtleerer_string(payload.get("coalesce_key"), "coalesce_key", max_chars=MAX_COALESCE_KEY_CHARS)

        generation = payload.get("generation")
        if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
            raise WakeConditionError("generation muss eine ganze Zahl >= 1 sein")

        subject_ref = payload.get("subject_ref")
        expected_predicate = payload.get("expected_predicate")

        if kind == KIND_AT_TIME:
            if subject_ref is not None:
                raise WakeConditionError("AT_TIME erlaubt kein subject_ref")
            if expected_predicate is not None:
                raise WakeConditionError("AT_TIME erlaubt kein expected_predicate")
        elif kind == KIND_EFFECT_TERMINAL:
            subject_ref = _nichtleerer_string(subject_ref, "subject_ref", max_chars=MAX_SUBJECT_REF_CHARS)
            expected_predicate = cls._validiere_effect_terminal_predicate(expected_predicate)
        elif kind == KIND_RESOURCE_REVISION:
            subject_ref = cls._validiere_resource_subject(subject_ref)
            expected_predicate = cls._validiere_resource_predicate(expected_predicate)
        elif kind == KIND_GOAL_STATE:
            subject_ref = _nichtleerer_string(subject_ref, "subject_ref", max_chars=MAX_ID_CHARS)
            expected_predicate = cls._validiere_goal_state_predicate(expected_predicate)

        earliest_at = _zahl_oder_none(payload.get("earliest_at"), "earliest_at")
        deadline = _zahl_oder_none(payload.get("deadline"), "deadline")

        if kind == KIND_AT_TIME and earliest_at is None:
            raise WakeConditionError("AT_TIME erfordert earliest_at")
        if earliest_at is not None and deadline is not None and deadline < earliest_at:
            raise WakeConditionError("Deadline liegt vor earliest_at")

        return cls(
            schema=WAKE_CONDITION_SCHEMA,
            kind=kind,
            subject_ref=subject_ref,
            expected_predicate=expected_predicate,
            earliest_at=earliest_at,
            deadline=deadline,
            goal_id=goal_id,
            step_id=step_id,
            generation=generation,
            coalesce_key=coalesce_key,
        )

    @staticmethod
    def _validiere_effect_terminal_predicate(predicate: Any) -> dict[str, Any]:
        if not isinstance(predicate, dict):
            raise WakeConditionError("EFFECT_TERMINAL erfordert expected_predicate")
        if set(predicate) == {"status"}:
            status = predicate["status"]
            if status not in EFFECT_TERMINAL_STATES:
                raise WakeConditionError(f"unbekannter Effekt-Endzustand: {status!r}")
            return {"status": status}
        if set(predicate) == {"any_terminal"}:
            if predicate["any_terminal"] is not True:
                raise WakeConditionError("any_terminal muss genau true sein")
            return {"any_terminal": True}
        raise WakeConditionError(
            "EFFECT_TERMINAL expected_predicate muss genau {'status': <Endzustand>} "
            "oder {'any_terminal': true} sein"
        )

    @staticmethod
    def _validiere_resource_subject(subject_ref: Any) -> str:
        subject_ref = _nichtleerer_string(subject_ref, "subject_ref", max_chars=MAX_SUBJECT_REF_CHARS)
        if subject_ref in (RESOURCE_KIND_ENTITY_GENERATION, RESOURCE_KIND_AUTONOMY_REVISION):
            return subject_ref
        for prefix in (RESOURCE_PREFIX_SESSION_GENERATION, RESOURCE_PREFIX_SESSION_TURN_COUNT):
            if subject_ref.startswith(prefix) and len(subject_ref) > len(prefix):
                return subject_ref
        raise WakeConditionError(
            f"RESOURCE_REVISION subject_ref nicht in der geschlossenen Ressourcen-Liste: {subject_ref!r}"
        )

    @staticmethod
    def _validiere_resource_predicate(predicate: Any) -> dict[str, Any]:
        if not isinstance(predicate, dict) or set(predicate) != {"min_value"}:
            raise WakeConditionError("RESOURCE_REVISION expected_predicate muss genau {'min_value': int} sein")
        min_value = predicate["min_value"]
        if isinstance(min_value, bool) or not isinstance(min_value, int) or min_value < 0:
            raise WakeConditionError("min_value muss eine ganze Zahl >= 0 sein")
        return {"min_value": min_value}

    @staticmethod
    def _validiere_goal_state_predicate(predicate: Any) -> dict[str, Any]:
        if not isinstance(predicate, dict):
            raise WakeConditionError("GOAL_STATE erfordert expected_predicate")
        if set(predicate) == {"status"}:
            status = predicate["status"]
            if status not in GOAL_STATUSES:
                raise WakeConditionError(f"unbekannter Ziel-Zustand: {status!r}")
            return {"status": status}
        if set(predicate) == {"status_in"}:
            werte = predicate["status_in"]
            if (
                not isinstance(werte, list)
                or not werte
                or len(werte) != len(set(werte))
                or any(w not in GOAL_STATUSES for w in werte)
            ):
                raise WakeConditionError("status_in muss eine nichtleere Liste eindeutiger, bekannter Ziel-Zustaende sein")
            return {"status_in": list(werte)}
        raise WakeConditionError(
            "GOAL_STATE expected_predicate muss genau {'status': <Zustand>} "
            "oder {'status_in': [<Zustaende>]} sein"
        )

    def als_dict(self) -> dict[str, Any]:
        """Kanonische, JSON-faehige Form -- fuer eine spaetere Persistenz (noch nicht
        gebaut; dieser Vertrag beschreibt nur Typ + Auswertung, keine Speicherung)."""
        return {
            "schema": self.schema,
            "kind": self.kind,
            "subject_ref": self.subject_ref,
            "expected_predicate": self.expected_predicate,
            "earliest_at": self.earliest_at,
            "deadline": self.deadline,
            "goal_id": self.goal_id,
            "step_id": self.step_id,
            "generation": self.generation,
            "coalesce_key": self.coalesce_key,
        }


# ---------------------------------------------------------------------------
# Auswerter
# ---------------------------------------------------------------------------

def _ergebnis(zustand: str, grund: str, beleg: dict[str, Any] | None) -> dict[str, Any]:
    assert zustand in WAKE_ZUSTAENDE
    return {"zustand": zustand, "grund": grund, "beleg": beleg}


def _unbekannt(grund: str) -> dict[str, Any]:
    return _ergebnis(ZUSTAND_UNBEKANNT, grund, None)


def pruefen(bedingung: WakeCondition, db: UnifiedDB, jetzt: float) -> dict[str, Any]:
    """Wertet genau eine WakeCondition mechanisch aus.

    Rueckgabe immer `{"zustand": ..., "grund": ..., "beleg": ...}` mit
    zustand in {ERFUELLT, OFFEN, ZEITABLAUF, UNBEKANNT}. Wirft NIE eine
    Ausnahme fuer eine bereits gueltig konstruierte WakeCondition -- ein
    Governor muss dieses Ergebnis unbedingt (ohne try/except) verwerten
    koennen, sonst waere genau der Fehler wieder moeglich, der dieses Modul
    verhindern soll (Ausfall wird stillschweigend zu "kein Befund").

    ⚠️ Generation zuerst: eine Bedingung, die aus einer frueheren Generation
    stammt (z.B. vor einem Neustart/Reset ueber advance_entity_generation),
    darf niemals ueber den aktuellen, neuen Zustand entscheiden -- das waere
    genau die Art stiller Fehlentscheidung, vor der `store.py`s Lease-/
    Generation-Fencing ueberall sonst im System schuetzt. Deshalb: nicht
    passende Generation -> UNBEKANNT, nie ERFUELLT und nie OFFEN.
    """
    try:
        live_generation = db.entity_generation()
    except Exception as exc:  # pragma: no cover - defensive; entity_generation() ist heute robust
        return _unbekannt(f"entity_generation nicht lesbar: {exc}")
    if int(bedingung.generation) != int(live_generation):
        return _unbekannt(
            f"Bedingung stammt aus Generation {bedingung.generation}, aktuell live ist "
            f"{live_generation} -- eine veraltete Bedingung darf nicht ueber eine neue "
            "Generation entscheiden"
        )

    # ⚠️ NACHGEZOGEN 2026-08-21: der Docstring oben verspricht, NIE zu werfen --
    # abgesichert war aber nur `entity_generation()`. Die vier Pruefer lesen
    # ebenfalls die Datenbank (`AutonomyController(db).snapshot()`,
    # `EffectJournal`), und eine gesperrte oder gestoerte Datenbank haette die
    # Ausnahme an den Governor durchgereicht. Genau dagegen ist dieses Modul
    # gebaut: wer die Ausnahme dann in einem beilaeufigen `except` faengt, hat
    # aus einem AUSFALL ein "kein Befund" gemacht -- und damit UNBEKANNT
    # wieder von OFFEN ununterscheidbar. Der Ausfall wird deshalb HIER zu
    # einem ausdruecklichen UNBEKANNT mit Grund, statt dem Aufrufer
    # ueberlassen zu werden.
    #
    # Gefunden beim unabhaengigen Nachpruefen mit einem zu duennen Datenbank-
    # Ersatz: `AttributeError: 'StubDB' object has no attribute 'tx'` schlug bis
    # zum Aufrufer durch, obwohl die Bedingung selbst gueltig gebaut war.
    try:
        if bedingung.kind == KIND_AT_TIME:
            sofort = _pruefe_at_time(bedingung, jetzt)
        elif bedingung.kind == KIND_EFFECT_TERMINAL:
            sofort = _pruefe_effect_terminal(bedingung, db)
        elif bedingung.kind == KIND_RESOURCE_REVISION:
            sofort = _pruefe_resource_revision(bedingung, db)
        elif bedingung.kind == KIND_GOAL_STATE:
            sofort = _pruefe_goal_state(bedingung, db)
        else:  # pragma: no cover - durch aus_dict() ausgeschlossen; Verteidigung in der Tiefe
            return _unbekannt(f"unbekannte Bedingungsart: {bedingung.kind!r}")
    except Exception as exc:
        return _unbekannt(
            f"Pruefung der Art {bedingung.kind} nicht durchfuehrbar: "
            f"{type(exc).__name__}: {exc}")

    if sofort is not None:
        return sofort

    # Bis hierher: die Bedingung ist mechanisch weder erfuellt noch unwiderruflich
    # verfehlt. Jetzt entscheidet nur noch die Zeit zwischen OFFEN und ZEITABLAUF.
    if bedingung.deadline is not None and jetzt > bedingung.deadline:
        return _ergebnis(
            ZUSTAND_ZEITABLAUF,
            "Deadline ueberschritten, ohne dass die Bedingung eintrat",
            {"deadline": bedingung.deadline, "jetzt": jetzt},
        )
    return _ergebnis(ZUSTAND_OFFEN, "noch nicht eingetreten", None)


def _pruefe_at_time(bedingung: WakeCondition, jetzt: float) -> dict[str, Any] | None:
    # AT_TIME ist der mechanisch trivialste Fall: die Uhrzeit ist monoton, also kann
    # diese Art nie in ZEITABLAUF laufen (aus_dict() lehnt deadline < earliest_at
    # ohnehin ab) und nie UNBEKANNT sein -- entweder es ist so weit, oder noch nicht.
    if jetzt >= bedingung.earliest_at:
        return _ergebnis(ZUSTAND_ERFUELLT, "Zeitpunkt erreicht", {"earliest_at": bedingung.earliest_at, "jetzt": jetzt})
    return None


def _pruefe_effect_terminal(bedingung: WakeCondition, db: UnifiedDB) -> dict[str, Any] | None:
    row = db.db.execute(
        "SELECT status, verified_at FROM effects WHERE effect_id=?",
        (bedingung.subject_ref,),
    ).fetchone()
    if row is None:
        return _unbekannt(f"Effekt {bedingung.subject_ref!r} existiert nicht im Journal")
    status = row["status"]
    if status not in EFFECT_TERMINAL_STATES:
        # Effekt ist noch PENDING -- weder erfuellt noch je unmoeglich, faellt auf die
        # normale OFFEN/ZEITABLAUF-Zeitlogik in pruefen() zurueck.
        return None
    predicate = bedingung.expected_predicate
    erwartet_beliebig = predicate.get("any_terminal") is True
    erwarteter_status = predicate.get("status")
    beleg = {"effect_id": bedingung.subject_ref, "status": status, "verified_at": row["verified_at"]}
    if erwartet_beliebig or status == erwarteter_status:
        return _ergebnis(ZUSTAND_ERFUELLT, "Effekt hat den erwarteten Endzustand erreicht", beleg)
    # Effekte koennen einen FINAL-Zustand nachweislich nie wieder verlassen (siehe
    # EffectJournal._finish_tx: eine zweite Transition verlangt status=='PENDING' und
    # scheitert sonst hart). Ein Effekt, der terminal, aber im FALSCHEN Zustand endete,
    # kann die erwartete Bedingung also nie mehr erreichen -- das ist kein "noch nicht",
    # sondern ein "nie mehr". Das ist inhaltlich ein Zeitablauf (die Gelegenheit ist
    # unwiderruflich vorbei), deshalb ZEITABLAUF statt endlosem OFFEN.
    return _ergebnis(
        ZUSTAND_ZEITABLAUF,
        f"Effekt endete terminal in {status!r}, erwartet war {predicate!r} -- kann nicht mehr eintreten",
        beleg,
    )


def _pruefe_resource_revision(bedingung: WakeCondition, db: UnifiedDB) -> dict[str, Any] | None:
    subject_ref = bedingung.subject_ref
    try:
        if subject_ref == RESOURCE_KIND_ENTITY_GENERATION:
            aktuell = db.entity_generation()
        elif subject_ref == RESOURCE_KIND_AUTONOMY_REVISION:
            # Einzige Quelle der Wahrheit fuer die Autonomy-Revision ist der
            # AutonomyController selbst -- kein Nachbau seiner JSON-Validierung hier.
            aktuell = AutonomyController(db).snapshot()["revision"]
        elif subject_ref.startswith(RESOURCE_PREFIX_SESSION_GENERATION):
            session_id = subject_ref[len(RESOURCE_PREFIX_SESSION_GENERATION):]
            aktuell = db.session_generation(session_id)
        elif subject_ref.startswith(RESOURCE_PREFIX_SESSION_TURN_COUNT):
            session_id = subject_ref[len(RESOURCE_PREFIX_SESSION_TURN_COUNT):]
            row = db.db.execute(
                "SELECT COUNT(*) n FROM turns WHERE session_id=? AND role='user'",
                (session_id,),
            ).fetchone()
            if row is None or row["n"] == 0:
                zeile = db.db.execute("SELECT 1 FROM sessions WHERE session_id=?", (session_id,)).fetchone()
                if zeile is None:
                    return _unbekannt(f"Session {session_id!r} existiert nicht")
            aktuell = int(row["n"]) if row else 0
        else:  # pragma: no cover - durch aus_dict()/_validiere_resource_subject ausgeschlossen
            return _unbekannt(f"unbekannter subject_ref: {subject_ref!r}")
    except KeyError:
        return _unbekannt(f"Ressource fuer {subject_ref!r} existiert nicht")
    min_value = bedingung.expected_predicate["min_value"]
    if aktuell >= min_value:
        return _ergebnis(
            ZUSTAND_ERFUELLT,
            "Ressourcenwert hat min_value erreicht",
            {"subject_ref": subject_ref, "aktuell": aktuell, "min_value": min_value},
        )
    return None


def _pruefe_goal_state(bedingung: WakeCondition, db: UnifiedDB) -> dict[str, Any] | None:
    # snapshot(user_id=None) liefert ALLE Ziele in Queue-Reihenfolge -- die beobachtete
    # goal_id (subject_ref) kann zu einem ANDEREN Ziel gehoeren als das wartende
    # (bedingung.goal_id); Cross-Goal-Abhaengigkeiten sind ausdruecklich erlaubt.
    goals = AutonomyController(db).snapshot(user_id=None)["goals"]
    ziel = next((g for g in goals if g["goal_id"] == bedingung.subject_ref), None)
    if ziel is None:
        return _unbekannt(f"Ziel {bedingung.subject_ref!r} existiert nicht (mehr)")
    status = ziel["status"]
    predicate = bedingung.expected_predicate
    erwartet = {predicate["status"]} if "status" in predicate else set(predicate["status_in"])
    beleg = {"goal_id": bedingung.subject_ref, "status": status}
    if status in erwartet:
        return _ergebnis(ZUSTAND_ERFUELLT, "Ziel hat den erwarteten Zustand erreicht", beleg)
    if status in GOAL_TERMINAL_STATES:
        # COMPLETED/CANCELLED sind im Controller nachweislich Endzustaende ohne
        # Ruecksprung (siehe GOAL_TERMINAL_STATES oben) -- dieselbe "nie mehr"-Logik
        # wie bei EFFECT_TERMINAL, deshalb ebenfalls ZEITABLAUF statt endlosem OFFEN.
        return _ergebnis(
            ZUSTAND_ZEITABLAUF,
            f"Ziel endete terminal in {status!r}, erwartet war {predicate!r} -- kann nicht mehr eintreten",
            beleg,
        )
    return None


# ---------------------------------------------------------------------------
# Selbst errechneter naechster Pruefzeitpunkt
# ---------------------------------------------------------------------------

def naechste_pruefung(bedingungen: list[WakeCondition], jetzt: float) -> float | None:
    """Minimum der noch in der Zukunft liegenden earliest_at/deadline-Werte.

    Das ist der Kern von "self-triggered": statt alle 30s stur nachzusehen (der
    heutige Puls), kann ein Governor ausrechnen, wann sich FRUEHESTENS ueberhaupt
    etwas aendern kann, und bis dahin schlafen.

    Gibt None zurueck, wenn keine der uebergebenen Bedingungen einen zukuenftigen
    Zeitwert traegt (nur rein ereignisgebundene Bedingungen offen sind, z.B. ein
    EFFECT_TERMINAL ohne deadline) -- solche Bedingungen koennen nur durch das
    Ereignis selbst aufgeloest werden, nie durch Zeitablauf.

    ⚠️ Bewusst OHNE Mindestabstand-Klammer: wuerde hier mit MINDESTABSTAND nach
    unten geklammert, koennte eine nahe Deadline (z.B. in 1s) hinter den
    Mindestabstand (5s) rutschen und so verspaetet als ZEITABLAUF erkannt werden --
    das waere ein stiller Korrektheitsfehler. Der Mindestabstand gehoert an die
    Stelle, die tatsaechliche Weckvorgaenge ausloest (siehe wecken_erlaubt), nicht
    an die Stelle, die nur die naechste noetige PRUEFUNG berechnet.
    """
    kandidaten = [
        wert
        for bedingung in bedingungen
        for wert in (bedingung.earliest_at, bedingung.deadline)
        if wert is not None and wert > jetzt
    ]
    return min(kandidaten) if kandidaten else None


# ---------------------------------------------------------------------------
# Anti-Zeno: Mindestabstand + Buendelung gleichartiger Ereignisse
# ---------------------------------------------------------------------------

def ist_dringend_faehig(bedingung: WakeCondition) -> bool:
    """Kann diese Bedingung, wenn sie eintritt, den Mindestabstand uebersteuern?

    Zwei Faelle, beide statisch an der Bedingung selbst erkennbar (keine DB-Abfrage
    noetig, damit diese Funktion auch bei der Planung/vor dem Eintreten benutzbar ist):

    - EFFECT_TERMINAL: ein Effekt ist im ClayVerse-Modell die einzige Stelle, an der
      ueberhaupt Wirkung nach aussen entsteht (siehe effects.py/EffectGate). Sein
      Abschluss -- ob Erfolg oder ein kritischer Endzustand wie DENIED/FAILED -- ist
      per Definition ein konsequenzielles Ereignis, kein Hintergrundrauschen.
    - RESOURCE_REVISION auf session_turn_count:<...>: das ist der mechanische Beleg
      fuer "ein Mensch hat gerade etwas Neues gesagt". Ein wartender Mensch darf nie
      dadurch verzoegert werden, dass kurz zuvor schon andere Bedingungen gebuendelt
      wurden.
    """
    if bedingung.kind == KIND_EFFECT_TERMINAL:
        return True
    if bedingung.kind == KIND_RESOURCE_REVISION and bedingung.subject_ref is not None:
        return bedingung.subject_ref.startswith(RESOURCE_PREFIX_SESSION_TURN_COUNT)
    return False


def wecken_erlaubt(letzter_weckzeitpunkt: float | None, jetzt: float, *, dringend: bool = False) -> bool:
    """Reine Anti-Zeno-Bremse fuer tatsaechliche Weckvorgaenge (nicht fuer Pruefungen).

    Ohne diese Bremse koennten beliebig viele, beliebig eng beieinanderliegende
    Bedingungen zu ebenso vielen einzelnen Weckvorgaengen fuehren (Zeno-Paradoxon:
    unendlich viele, beliebig kleine Intervalle summieren sich nie zu Ruhe). Sie
    erzwingt mindestens MINDESTABSTAND Sekunden zwischen zwei Weckvorgaengen --
    ausser `dringend=True` (siehe ist_dringend_faehig): menschliche Eingabe und
    kritische Effektendzustaende duerfen NICHT auf den naechsten freien Takt warten,
    nur weil kurz zuvor aus anderem Grund schon geweckt wurde.
    """
    if letzter_weckzeitpunkt is None or dringend:
        return True
    return (jetzt - letzter_weckzeitpunkt) >= MINDESTABSTAND


def buendeln(erfuellte: list[tuple[WakeCondition, dict[str, Any]]]) -> list[tuple[WakeCondition, dict[str, Any]]]:
    """Fasst mehrere ERFUELLTe Bedingungen mit demselben coalesce_key zu einem
    einzigen Weckvorgang zusammen (10.000 gleichartige Ereignisse -> ein Weckvorgang,
    nicht 10.000). Reihenfolge bleibt stabil; das erste Auftreten je coalesce_key
    gewinnt, weil es den frühesten Beleg traegt."""
    gesehen: set[str] = set()
    ergebnis: list[tuple[WakeCondition, dict[str, Any]]] = []
    for bedingung, resultat in erfuellte:
        if bedingung.coalesce_key in gesehen:
            continue
        gesehen.add(bedingung.coalesce_key)
        ergebnis.append((bedingung, resultat))
    return ergebnis


def neue_coalesce_key(*teile: str) -> str:
    """Hilfsfunktion fuer Aufrufer, die noch keinen natuerlichen coalesce_key haben
    (z.B. ein Einzelfall ohne Gleichartige): erzeugt einen eindeutigen Schluessel, der
    also mit niemandem gebuendelt wird. Kein Ersatz dafuer, bei GLEICHARTIGEN
    Bedingungen bewusst denselben Schluessel zu waehlen."""
    basis = "|".join(teile) if teile else uuid.uuid4().hex
    return basis[:MAX_COALESCE_KEY_CHARS]
