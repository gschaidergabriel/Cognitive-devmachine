"""Bug-Meldekanal: Andreas/Gabriel melden im Chat einen Bug, landet in
`eos_bug_hypothesen`. Der EINGANG des inneren Architekten (Hypothesen-Quelle 4
von 5, siehe SELBSTFORSCHUNG.md Abschnitt 5 und 7).

Bauplan wortwoertlich von clayverse/bewertung.py uebernommen (gleiche Ablage,
gleiche Anmeldepruefung, gleiche `tx()`-Disziplin) -- ein zweites Muster fuer
denselben fachlichen Bereich (Mensch schreibt etwas ueber einen Zug/eine
Beobachtung in die UnifiedDB) waere der zweite Dialekt, den dieses Haus
ausdruecklich vermeidet.

⚠️ Ablage: /var/lib/clay/wiki.db -- dieselbe UnifiedDB wie ueberall sonst,
NICHT eine eigene Datei (dieselbe Begruendung wie bewertung.py: der Architekt
braucht Bug-Meldungen im selben Bezugsrahmen wie turns/eos_bewertungen fuer
Korrelation, ein ATTACH ueber eine zweite Datei waere ein zweites
Betriebsrisiko fuer denselben fachlichen Bereich).

⚠️ NIE executescript() hier -- siehe store.tx()-Kommentar und den f-77-
Zwischenfall (erfolge.py). Genau EIN CREATE TABLE, je ein eigenes execute().

⭐ EIN Bug-Report ist eine HYPOTHESE, kein Befehl (SELBSTFORSCHUNG.md
Abschnitt 7). Dieses Modul speichert nur die Meldung des Menschen -- das
Reproduzieren, das Finden der echten Ursache und das Schliessen des Kreises
("was WIRKLICH war") macht der Architekt (architekt/), NICHT dieses Modul.
Ein Mensch kann NIE selbst `status`/`befund` setzen -- die HTTP-Aussenseite
(terminal_gateway.py) bietet dafuer bewusst keinen Weg an; nur der Architekt
schreibt dorthin (direkt, vom Wirt aus, ausserhalb des Behaelters), siehe
`status_setzen` unten.

Metadaten je Zeile:
  bug_id       -- eigene Kennung (wie bewertung_id bei bewertung.py).
  user_id      -- wer gemeldet hat (gabriel/andreas, aus dem Clerk-Token,
                  NIE aus der Anfrage selbst -- exakt derselbe Weg wie bei
                  jedem anderen Endpunkt in diesem Haus).
  ts           -- Meldezeitpunkt.
  beschreibung -- der Klartext der Meldung. Bewusst Klartext (anders als bei
                  bewertung.py, wo turns.content die Quelle ist): eine
                  Bug-Meldung HAT keine turns-Zeile, die sie schon traegt --
                  hier ist dieses Feld die einzige Quelle.
  wo           -- optionaler Kontext ("wo?" laut Spezifikation), z.B. eine
                  Seite/ein Merkmal, das der Mensch nennt. Kann NULL sein.
  status       -- OFFEN (Vorgabe) / REPRODUZIERT / WIDERLEGT / BEHOBEN.
  befund       -- die vom Architekten GEMESSENE echte Ursache, wenn er sie
                  gefunden hat (Abschnitt 7, Punkt 4: "gib ihm den gemessenen
                  Befund zurueck", nicht bloss "behoben"). NULL bis dahin.
"""
from __future__ import annotations

import time
import uuid

SCHEMA_SQL = (
    "CREATE TABLE IF NOT EXISTS eos_bug_hypothesen("
    "bug_id TEXT PRIMARY KEY,"
    "user_id TEXT NOT NULL,"
    "ts REAL NOT NULL,"
    "beschreibung TEXT NOT NULL,"
    "wo TEXT,"
    "status TEXT NOT NULL DEFAULT 'OFFEN' "
    "CHECK(status IN ('OFFEN','REPRODUZIERT','WIDERLEGT','BEHOBEN')),"
    "befund TEXT)"
)
SCHEMA_INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS eos_bug_hypothesen_status_idx "
    "ON eos_bug_hypothesen(status, ts)"
)
SCHEMA_USER_INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS eos_bug_hypothesen_user_idx "
    "ON eos_bug_hypothesen(user_id, ts)"
)

# Unter der Chat-Nachrichtengrenze (_CHAT_MESSAGE_MAX_CHARS in
# terminal_gateway.py = 8000) -- eine Bug-Meldung ist ein kurzer Text, kein
# Log-Dump. Wer einen ganzen Stacktrace melden will, soll ihn per
# /api/dateien anhaengen (dateien.py existiert schon fuer genau das).
BESCHREIBUNG_MAX_CHARS = 4_000
WO_MAX_CHARS = 200

_GUELTIGE_STATUS = ("OFFEN", "REPRODUZIERT", "WIDERLEGT", "BEHOBEN")


class BugFehler(ValueError):
    """Ungueltige Eingabe oder unbekannte bug_id."""


def sicherstellen(db) -> None:
    """Idempotent, billig -- wie bewertung.sicherstellen(): vor jeder
    Operation aufgerufen statt an einem eigenen Start-Hook."""
    db.db.execute(SCHEMA_SQL)
    db.db.execute(SCHEMA_INDEX_SQL)
    db.db.execute(SCHEMA_USER_INDEX_SQL)


def melden(db, *, user_id: str, beschreibung: str, wo: str | None = None) -> dict:
    """Eine neue Bug-Hypothese ablegen. `user_id` MUSS vom Aufrufer bereits
    gegen CANONICAL_USER_IDS geprueft sein (wie bei jedem anderen Schreibweg
    in diesem Haus) -- dieses Modul prueft es nicht nochmal, um keine zweite
    Quelle fuer dieselbe Regel zu fuehren."""
    text = (beschreibung or "").strip()
    if not text:
        raise BugFehler("beschreibung fehlt")
    if len(text) > BESCHREIBUNG_MAX_CHARS:
        raise BugFehler(f"beschreibung ueber {BESCHREIBUNG_MAX_CHARS} Zeichen")

    ort = (wo or "").strip() or None
    if ort is not None and len(ort) > WO_MAX_CHARS:
        raise BugFehler(f"wo ueber {WO_MAX_CHARS} Zeichen")

    sicherstellen(db)
    bug_id = uuid.uuid4().hex
    now = time.time()
    with db.tx() as sql:
        sql.execute(
            "INSERT INTO eos_bug_hypothesen(bug_id,user_id,ts,beschreibung,wo,status,befund) "
            "VALUES(?,?,?,?,?,'OFFEN',NULL)",
            (bug_id, user_id, now, text, ort),
        )
    return {"ok": True, "bug_id": bug_id, "status": "OFFEN"}


def _zeile_zu_dict(row) -> dict:
    return {
        "bug_id": row["bug_id"],
        "user_id": row["user_id"],
        "ts": row["ts"],
        "beschreibung": row["beschreibung"],
        "wo": row["wo"],
        "status": row["status"],
        "befund": row["befund"],
    }


def lesen_fuer_nutzer(db, *, user_id: str) -> list[dict]:
    """Alle eigenen Meldungen, juengste zuerst. Nie fremde -- der Filter sitzt
    in der WHERE-Klausel, nicht in einer Pruefung danach."""
    sicherstellen(db)
    zeilen = db.db.execute(
        "SELECT bug_id,user_id,ts,beschreibung,wo,status,befund "
        "FROM eos_bug_hypothesen WHERE user_id=? ORDER BY ts DESC",
        (user_id,),
    ).fetchall()
    return [_zeile_zu_dict(r) for r in zeilen]


def lesen_eins(db, *, bug_id: str, user_id: str) -> dict:
    """Eine einzelne Meldung -- nur dem Melder selbst zugaenglich.

    Gleiche Bauart wie bewertung.setzen()/ist_kanonische_sitzung: die Zeile
    gehoert dem, der sie angelegt hat. Eine dritte Rolle (Architekt/Admin, der
    ALLE lesen darf) gibt es HTTP-seitig bewusst nicht -- der Architekt liest
    diese Tabelle direkt aus der DB vom Wirt, nicht ueber diesen Weg (siehe
    Modul-Kopfkommentar).
    """
    sicherstellen(db)
    row = db.db.execute(
        "SELECT bug_id,user_id,ts,beschreibung,wo,status,befund "
        "FROM eos_bug_hypothesen WHERE bug_id=?",
        (bug_id,),
    ).fetchone()
    if row is None:
        raise BugFehler("unbekannte Meldung")
    if row["user_id"] != user_id:
        raise PermissionError("fremde Meldung")
    return _zeile_zu_dict(row)


def status_setzen(db, *, bug_id: str, status: str, befund: str | None = None) -> dict:
    """NUR fuer den Architekten (architekt/architekt.py), der vom Wirt aus
    direkt schreibt -- kein HTTP-Weg fuehrt hierher (siehe Modul-Kopf). Setzt
    Status + optional den gemessenen Befund, wenn die Hypothese reproduziert
    (oder widerlegt) wurde.
    """
    if status not in _GUELTIGE_STATUS:
        raise BugFehler(f"unbekannter Status: {status!r}")
    sicherstellen(db)
    with db.tx() as sql:
        cur = sql.execute(
            "UPDATE eos_bug_hypothesen SET status=?, befund=COALESCE(?, befund) "
            "WHERE bug_id=?",
            (status, befund, bug_id),
        )
        if cur.rowcount == 0:
            raise BugFehler("unbekannte Meldung")
    return {"ok": True, "bug_id": bug_id, "status": status}


def offene_fuer_architekt(db) -> list[dict]:
    """Alle Meldungen im Status OFFEN -- das Eingangsfach des Architekten
    (Hypothesen-Quelle 4). REPRODUZIERT/WIDERLEGT/BEHOBEN sind bereits
    bearbeitet und tauchen hier nicht mehr auf."""
    sicherstellen(db)
    zeilen = db.db.execute(
        "SELECT bug_id,user_id,ts,beschreibung,wo,status,befund "
        "FROM eos_bug_hypothesen WHERE status='OFFEN' ORDER BY ts ASC",
    ).fetchall()
    return [_zeile_zu_dict(r) for r in zeilen]
