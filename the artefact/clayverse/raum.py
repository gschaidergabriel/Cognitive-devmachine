"""Der Raum -- vier Sitzungen, eine Entitaet, alle sehen einander.

Gabriels Entwurf, woertlich: "die 4 sessions haben alle getrennte id sind aber
alle teil der selben entitaet agent zero und wie bei der reserch entitaet sitzen
sie aber alle 4 im selben raum und sehen was der andere macht und koordinieren
sich danach ... sie kommunizieren in caveman englisch, koordinieren sich so dass
nichts kollidiert und greifen alle auf die selbe source of truth zu."

Und ausdruecklich: "das komplizierte matching via timestamps bla bla brauchen
wir nicht, das ist simpel und funktional".

⭐ DESHALB IST DAS HIER SO KLEIN

Kein Nachrichtenbus, keine Sperrverwaltung, keine Wahl eines Anfuehrers, kein
Abgleich von Zeitstempeln. Eine Tafel mit vier Zeilen -- je Sitzung eine --
und ein kurzer Zuruf-Faden. Wer etwas tut, schreibt seine Zeile. Wer etwas tun
will, liest zuerst die Tafel. Das ist alles.

Die Robustheit kommt nicht aus Mechanik, sondern aus der Kleinheit: es gibt
nichts, was auseinanderlaufen kann, weil es nur EINEN Ort gibt (dieselbe
wiki.db, dieselbe Wahrheit wie alles andere) und je Sitzung genau EINE Zeile,
die ueberschrieben wird. Kein Verlauf, der gepflegt werden muesste.

⚠️⚠️ DIE EINE GRENZE, DIE HIER NICHT VERLETZT WERDEN DARF

Der Raum traegt, WAS GETAN WIRD -- niemals, WAS EIN MENSCH GESAGT HAT.

Alle vier Sitzungen sind dieselbe Entitaet, also duerfen sie sich gegenseitig
bei der Arbeit sehen. Aber zwei davon gehoeren Gabriel und zwei Andreas, und
deren Gespraechsinhalte sind getrennt. Wuerde in `was` der Wortlaut einer Frage
stehen, waere der Raum ein Leck -- und zwar ein besonders unauffaelliges, weil
er ja gerade dafuer gebaut ist, dass alle hineinsehen.
Genau dieser Fehler ist heute schon einmal passiert: eine Tabelle ohne
Nutzerspalte hat Andreas Gabriels private Eintraege gezeigt.
Deshalb: kurze Taetigkeitsbeschreibung in Caveman-Englisch, und `_geprueft()`
kappt jede Zeile hart auf Arbeitslaenge. Wer den Wortlaut braucht, liest die
Sitzung -- und dafuer braucht er die Berechtigung dieses Menschen.

⚠️ ZUM ALTER EINER ZEILE, weil "keine Zeitstempel" hier falsch verstanden
werden koennte: es gibt KEIN Zusammenrechnen von Zeitpunkten und keine
Reihenfolgeermittlung. Aber jede Zeile traegt, WANN sie geschrieben wurde, und
der Raum zeigt daraus ein schlichtes Alter an. Ohne das haelt eine abgestuerzte
Sitzung ihren Anspruch fuer immer, und die anderen weichen ewig einem Arbeiter
aus, den es nicht mehr gibt. Das ist keine Komplexitaet, das ist die
Voraussetzung dafuer, dass das Einfache funktioniert.
"""
from __future__ import annotations

import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS zero_raum (
  session_id TEXT PRIMARY KEY,          -- eine Zeile je Sitzung, wird ueberschrieben
  mensch     TEXT NOT NULL,             -- gabriel | andreas
  platz      INTEGER NOT NULL,
  was        TEXT NOT NULL,             -- Caveman: was ich gerade tue
  womit      TEXT,                      -- die angefasste Sache: Datei, Tabelle, Dienst
  zustand    TEXT NOT NULL,             -- arbeitet | wartet | frei
  seit       REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS zero_raum_ruf (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL,
  von TEXT NOT NULL,
  text TEXT NOT NULL
);
"""

MAX_WAS = 160
MAX_WOMIT = 120
MAX_RUF = 240
RUFE_SICHTBAR = 12
VERALTET_NACH_S = 900          # danach gilt ein Anspruch als verwaist


def _geprueft(text: str, grenze: int) -> str:
    """Hart kappen. Der Raum ist fuer Taetigkeiten da, nicht fuer Gespraechstext.

    Die Grenze ist keine Formatierung, sondern die Leckdichtung: was nicht
    hineinpasst, kann auch nicht versehentlich hineingeraten.
    """
    t = " ".join(str(text or "").split())
    return t[:grenze]


def sicherstellen(db) -> None:
    """NUR am Start aufrufen. executescript committet implizit."""
    db.db.executescript(SCHEMA)


def sagen(db, *, session_id: str, mensch: str, platz: int,
          was: str, womit: str = "", zustand: str = "arbeitet") -> dict:
    """Meine Zeile schreiben. Ueberschreibt die vorige -- kein Verlauf noetig."""
    if zustand not in ("arbeitet", "wartet", "frei"):
        raise ValueError("zustand muss arbeitet|wartet|frei sein")
    w = _geprueft(womit, MAX_WOMIT)
    # ⭐ ERST pruefen, DANN eintragen. Andersherum meldet man die eigene,
    # gerade geschriebene Zeile als Kollision mit sich selbst -- und die
    # Pruefung gehoert HIERHER, nicht in einen Aufrufer: eine
    # Sicherungseigenschaft, die von der Hoeflichkeit des Aufrufers abhaengt,
    # ist keine. Vorher sass sie nur in der MCP-Bruecke; jeder direkte Aufruf
    # (Takt, Skript, kuenftiger Dienst) lief blind daran vorbei.
    stoss = kollision(db, womit=w, ich=session_id) if (w and zustand == "arbeitet") else None
    with db.tx() as sql:
        sql.execute(
            "INSERT INTO zero_raum(session_id,mensch,platz,was,womit,zustand,seit) "
            "VALUES(?,?,?,?,?,?,?) ON CONFLICT(session_id) DO UPDATE SET "
            "was=excluded.was, womit=excluded.womit, zustand=excluded.zustand, seit=excluded.seit",
            (session_id, mensch, platz, _geprueft(was, MAX_WAS), w, zustand, time.time()))
    return {"eingetragen": session_id, "kollision": stoss}


def rufen(db, *, session_id: str, text: str) -> dict:
    """Ein kurzer Zuruf an die anderen drei. Caveman, kein Gespraechstext."""
    with db.tx() as sql:
        sql.execute("INSERT INTO zero_raum_ruf(ts,von,text) VALUES(?,?,?)",
                    (time.time(), session_id, _geprueft(text, MAX_RUF)))
        # Nur die letzten paar behalten: ein Raum ist kein Archiv, und ein
        # unbegrenzter Faden waere genau die Komplexitaet, die hier nicht
        # gewollt ist.
        sql.execute("DELETE FROM zero_raum_ruf WHERE id NOT IN "
                    "(SELECT id FROM zero_raum_ruf ORDER BY id DESC LIMIT 60)")
    return {"gerufen": True}


def sehen(db, *, ich: str | None = None) -> dict:
    """Wer sitzt im Raum und tut gerade was. Ein Lesezugriff, kein DDL."""
    try:
        db.db.execute("SELECT 1 FROM zero_raum LIMIT 1")
    except Exception:
        return {"stand": "RAUM_NOCH_NICHT_ANGELEGT",
                "hinweis": "Tabelle zero_raum fehlt. Sag das, statt es zu deuten."}
    jetzt = time.time()
    plaetze = []
    for r in db.db.execute(
            "SELECT session_id,mensch,platz,was,womit,zustand,seit FROM zero_raum "
            "ORDER BY mensch, platz"):
        alter = jetzt - float(r["seit"])
        plaetze.append({
            "session_id": r["session_id"],
            "ich": (r["session_id"] == ich),
            "mensch": r["mensch"],
            "was": r["was"],
            "womit": r["womit"] or None,
            "zustand": r["zustand"],
            "vor_s": round(alter),
            # Verwaist statt "arbeitet noch": sonst weichen die anderen ewig
            # einem Arbeiter aus, den es nicht mehr gibt.
            "verwaist": alter > VERALTET_NACH_S,
        })
    rufe = [{"von": r["von"], "text": r["text"], "vor_s": round(jetzt - float(r["ts"]))}
            for r in db.db.execute(
                "SELECT von,text,ts FROM zero_raum_ruf ORDER BY id DESC LIMIT ?",
                (RUFE_SICHTBAR,))][::-1]
    return {
        "plaetze": plaetze,
        "rufe": rufe,
        "regel": ("Alle vier Plaetze sind DIESELBE Entitaet -- ihr seht einander bei der "
                  "Arbeit. Der Raum traegt, WAS getan wird, nie WAS EIN MENSCH GESAGT HAT: "
                  "zwei Plaetze gehoeren Gabriel, zwei Andreas, und deren Gespraeche sind "
                  "getrennt. Bevor du etwas anfasst, sieh nach, ob es schon jemand hat. "
                  "Ein Platz mit verwaist=true haelt keinen Anspruch mehr."),
    }


def frei(db, *, session_id: str) -> dict:
    """Anspruch zurueckgeben. Wer fertig ist, raeumt die Bank."""
    with db.tx() as sql:
        sql.execute("UPDATE zero_raum SET zustand='frei', womit=NULL, was='idle', seit=? "
                    "WHERE session_id=?", (time.time(), session_id))
    return {"freigegeben": session_id}


def kollision(db, *, womit: str, ich: str) -> dict | None:
    """Haelt gerade ein ANDERER Platz dieselbe Sache? Sonst None."""
    w = _geprueft(womit, MAX_WOMIT)
    if not w:
        return None
    jetzt = time.time()
    for r in db.db.execute(
            "SELECT session_id,mensch,was,seit FROM zero_raum "
            "WHERE womit=? AND session_id<>? AND zustand='arbeitet'", (w, ich)):
        if jetzt - float(r["seit"]) <= VERALTET_NACH_S:
            return {"haelt": r["session_id"], "mensch": r["mensch"], "was": r["was"],
                    "seit_s": round(jetzt - float(r["seit"]))}
    return None
