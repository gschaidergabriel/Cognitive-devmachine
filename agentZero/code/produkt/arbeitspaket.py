"""Arbeitspakete -- Zero denkt und schnuert, jemand anderes fuehrt aus.

Gabriels Regel, woertlich: "agent zero handelt nie selbst er spawnt immer sonet
agenten ... die fuer ihn die richtige arbeit uebernehmen er koordiniert und
denkt."

GEMESSEN, warum das gebraucht wird: Andreas bat Zero, eine Telefonnummer von
seimensch.net zu entfernen. Zero versuchte `request_effect` mit vier
Faehigkeitsnamen -- alle vier verweigert -- meldete dann korrekt, dass es nicht
handeln kann, und nannte Gabriel als richtige Ansprechperson. Sauber gedacht,
null Arbeit getan. Zeros Faehigkeiten sind absichtlich auf {state.noop,
entityos.exec} begrenzt; es KANN keine Datei anfassen, und diese Grenze bleibt.

⭐ WAS HIER GEBAUT IST UND WAS NICHT

    GEBAUT      das Paket: dauerhaft, zurechenbar, mit Belegpflicht
    NICHT       der Ausfuehrer

Der Ausfuehrer waere ein Dienst, der Schalbefehle nach dem Text eines
Sprachmodells ausfuehrt. Das ist eine Rechteerweiterung und gehoert dem
Menschen, nicht einem Agenten -- ein Sonett-Arbeiter hat genau das heute
abgelehnt, mit Recht. Bis diese Entscheidung getroffen ist, ist ein Paket eine
FRAGE an einen Menschen, kein Auftrag an eine Maschine, und der Status sagt das
auch so.

⚠️ EIN PAKET IST UNTRUSTED. Es entsteht aus dem Text eines Sprachmodells. Was
darin steht, ist ein Vorschlag -- niemals ein Freibrief. Deshalb traegt jedes
Paket, WER es bestellt hat (aus dem verifizierten Zustand, nie aus einem
Argument), und der Status beginnt bei `offen`, nicht bei `freigegeben`.
"""
from __future__ import annotations

import time
import uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS entityos_arbeitspaket (
  paket_id   TEXT PRIMARY KEY,
  besteller  TEXT NOT NULL,          -- gabriel | andreas, aus dem gepruefsten Zustand
  session_id TEXT NOT NULL,
  auftrag    TEXT NOT NULL,          -- Caveman: was zu tun ist
  womit      TEXT,                   -- die Sache: Datei, Dienst, Tabelle
  warum      TEXT,                   -- die Begruendung, damit ein Mensch pruefen kann
  stand      TEXT NOT NULL,          -- offen | laeuft | fertig | gescheitert | abgelehnt
  ergebnis   TEXT,
  beleg      TEXT,                   -- WOMIT belegt der Ausfuehrer, dass es getan ist
  erstellt   REAL NOT NULL,
  geaendert  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_arbeitspaket_stand ON entityos_arbeitspaket(stand, erstellt);
"""

STAENDE = ("offen", "laeuft", "fertig", "gescheitert", "abgelehnt")
# ⭐ `abgelehnt` ist bewusst KEIN Fehlschlag: der Arbeiter hat erkannt, dass die
# Aufgabe mit seinen Mitteln nicht machbar ist, und das sauber aufgeschrieben.
# Das in `gescheitert` zu pressen verwischt den Unterschied zwischen "hat
# versagt" und "war fuer ihn nicht machbar". Die Arbeit wartet in beiden
# Faellen -- aber nur in einem davon liegt es am Arbeiter.
MAX_AUFTRAG = 1200
MAX_FELD = 300


def sicherstellen(db) -> None:
    """NUR am Start. executescript committet implizit."""
    db.db.executescript(SCHEMA)


def _kurz(t, n):
    return " ".join(str(t or "").split())[:n]


def schnueren(db, *, besteller: str, session_id: str,
              auftrag: str, womit: str = "", warum: str = "") -> dict:
    """Ein Paket anlegen. Es ist damit NICHT freigegeben -- nur festgehalten."""
    if not str(auftrag or "").strip():
        raise ValueError("ein Paket ohne Auftrag ist keins")
    pid = "ap-" + uuid.uuid4().hex[:12]
    jetzt = time.time()
    with db.tx() as sql:
        sql.execute(
            "INSERT INTO entityos_arbeitspaket(paket_id,besteller,session_id,auftrag,"
            "womit,warum,stand,ergebnis,beleg,erstellt,geaendert) "
            "VALUES(?,?,?,?,?,?,'offen',NULL,NULL,?,?)",
            (pid, besteller, session_id, _kurz(auftrag, MAX_AUFTRAG),
             _kurz(womit, MAX_FELD), _kurz(warum, MAX_FELD), jetzt, jetzt))
    return {
        "paket_id": pid,
        "stand": "offen",
        "hinweis": ("Festgehalten, nicht freigegeben. Ein Ausfuehrer existiert bewusst "
                    "noch nicht: ein Dienst, der Schalbefehle nach dem Text eines "
                    "Sprachmodells ausfuehrt, ist eine Rechteerweiterung und gehoert "
                    "einem Menschen. Bis dahin ist dieses Paket eine Frage an einen "
                    "Menschen, kein Auftrag an eine Maschine."),
    }


def lage(db, *, besteller: str | None = None, grenze: int = 20) -> dict:
    """Welche Pakete gibt es, wie stehen sie. Lesezugriff, kein DDL."""
    try:
        db.db.execute("SELECT 1 FROM entityos_arbeitspaket LIMIT 1")
    except Exception:
        return {"stand": "NOCH_KEINE_PAKETE",
                "hinweis": "Tabelle fehlt. Sag das, statt es zu deuten."}
    wo, args = "", []
    if besteller:
        wo, args = " WHERE besteller=?", [besteller]
    zeilen = [dict(r) for r in db.db.execute(
        "SELECT paket_id,besteller,auftrag,womit,warum,stand,ergebnis,beleg,erstellt "
        "FROM entityos_arbeitspaket" + wo + " ORDER BY erstellt DESC LIMIT ?",
        (*args, grenze))]
    nach_stand: dict[str, int] = {}
    for z in zeilen:
        nach_stand[z["stand"]] = nach_stand.get(z["stand"], 0) + 1
    return {
        "pakete": zeilen,
        "nach_stand": nach_stand,
        "hinweis": ("`offen` heisst: festgehalten und wartet auf einen Menschen. Es gibt "
                    "keinen automatischen Ausfuehrer -- behaupte nie, ein Paket sei "
                    "erledigt, solange kein `beleg` daran haengt."),
    }


def stand_setzen(db, *, paket_id: str, stand: str,
                 ergebnis: str = "", beleg: str = "") -> dict:
    """Nur mit BELEG darf ein Paket `fertig` werden.

    Ohne diese Bedingung waere `fertig` eine Behauptung. Genau davor schuetzt
    die ganze Beweisdisziplin dieses Hauses -- sie darf nicht ausgerechnet an
    der Stelle aufhoeren, an der etwas als getan gilt.
    """
    if stand not in STAENDE:
        raise ValueError(f"stand muss eines von {STAENDE} sein")
    if stand == "fertig" and not str(beleg or "").strip():
        raise ValueError("fertig ohne Beleg ist eine Behauptung, kein Ergebnis")
    if stand == "fertig":
        # ⚠️ Der Beleg muss `fertig` auch TRAGEN. Vorher wurde nur geprueft, ob
        # ueberhaupt einer da ist -- und ein Arbeiter, der korrekt verweigert,
        # schreibt einen ehrlichen Bericht darueber. Der ging als Beleg durch.
        # Damit bestrafte die Regel genau das Verhalten, das sie foerdern soll.
        _zeugnis = f"{ergebnis} {beleg}".upper()
        for _leer in ("NICHTS GETAN", "NICHT AUSGEFUEHRT", "NICHT AUSGEFÜHRT",
                      "KEINE WIRKUNG", "NOTHING DONE", "NICHT MOEGLICH",
                      "NICHT MÖGLICH", "KEIN ZUGRIFF"):
            if _leer in _zeugnis:
                raise ValueError(
                    f"der Beleg sagt selbst {_leer!r} -- dann ist das Paket nicht fertig. "
                    "Nimm `abgelehnt`, wenn die Aufgabe fuer den Arbeiter nicht machbar "
                    "war und er das richtig erkannt hat. Das ist kein Fehlschlag, aber "
                    "auch keine Erledigung: die Arbeit wartet weiter auf jemanden.")
    with db.tx() as sql:
        cur = sql.execute(
            "UPDATE entityos_arbeitspaket SET stand=?, ergebnis=?, beleg=?, geaendert=? "
            "WHERE paket_id=?",
            (stand, _kurz(ergebnis, MAX_AUFTRAG), _kurz(beleg, MAX_AUFTRAG),
             time.time(), paket_id))
        if cur.rowcount != 1:
            raise ValueError(f"kein Paket {paket_id}")
    return {"paket_id": paket_id, "stand": stand}
