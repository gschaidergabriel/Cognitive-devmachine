"""Erfolge UND Fehlschlaege, nebeneinander -- der Teil, aus dem sich etwas ablesen laesst.

Eignerauftrag woertlich: "eine tabellke ... mit abgeschlossene projekte erfolgrecih
nicht erfolgreich und erfolgreich abgfeschlossene projekte gröste allgemeine erfolge
seit er zero nutzt und fehlschläge".

⚠️ EHRLICHKEIT UEBER DEN ZEITRAUM, ZUERST.

Zero ist seit dem 2026-08-18 in Benutzung. EINEM Tag. Alles unter `seit_zero=1`
stammt aus diesem einen Tag, und das steht auch so in der Tabelle. Eine Liste
grosser Erfolge "seit Nutzung" waere sonst genau die Sorte Angabe, die im
Rueckblick nach einer langen Erfolgsgeschichte aussieht -- der Eigner hat als
Grundregel gesetzt: NICHTS ERFINDEN. Ein kurzer Zeitraum ist kein Makel, aber
ihn zu verschweigen waere einer.

⭐ WARUM DIE FEHLSCHLAEGE HIER GLEICHRANGIG STEHEN

Nicht aus Bescheidenheit. Jeder Eintrag unter `fehlschlag` ist ein Fehler, der
im Betrieb NICHTS geworfen hat -- er wurde nur gefunden, weil jemand nachgesehen
hat. Diese Liste ist damit das genaueste vorhandene Bild davon, wie dieses
System kaputtgeht: still. Wer nur die Erfolge fuehrt, verliert genau das.

Jede Zeile traegt `beleg` -- die Messung oder Beobachtung, aus der sie stammt.
Ohne Beleg kein Eintrag.
"""
from __future__ import annotations
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS entityos_erfolge(
  id TEXT PRIMARY KEY,
  art TEXT NOT NULL,               -- erfolg | fehlschlag
  titel TEXT NOT NULL,
  wirkung TEXT,                    -- was es konkret geaendert hat
  beleg TEXT NOT NULL,             -- Messung/Beobachtung. Ohne Beleg kein Eintrag.
  gehoert TEXT,                    -- gabriel | andreas | gemeinsam
  seit_zero INTEGER NOT NULL DEFAULT 0,
  datum TEXT NOT NULL,
  erfasst REAL NOT NULL
);
"""

# ── Erfolge seit Zero. Alle vom 2026-08-18, dem ersten Tag. ────────────────
ERFOLGE = [
    ("e-gefaess", "Ein Gefaess statt zwei Datenbanken",
     "87 Clay-Korpustabellen und 19 Laufzeitobjekte in EINER Datei, kollisionsfrei.",
     "Gemessen: 0 Namenskollisionen, Schema idempotent, Herz waehrend der Operation "
     "weiter gewachsen (+543 Kanten).", "gemeinsam", 1, "2026-08-18"),
    ("e-container", "EntityOS laeuft im Container auf dem VPS",
     "Ohne nested Virtualisierung, ohne Anruf bei Hostinger.",
     "docker ps: entityos up, healthy. Bereitschaftspruefung gruen.", "gemeinsam", 1, "2026-08-18"),
    ("e-bahnen", "Bahnenrouter: Faehigkeit statt Anbieter",
     "Das Modell fragt nach einer Faehigkeit, der Code waehlt den Anbieter. "
     "Anteilsgrenzen erzwungen, erschoepft = Absage statt stiller Verschlechterung.",
     "clayverse/bahnen.py, leere Antwort zaehlt als Ausfall und schaltet weiter.",
     "gemeinsam", 1, "2026-08-18"),
    ("e-woertlich", "Gedaechtnis mit Woertlichkeitspruefung",
     "Ein Beleg muss zeichengenau im Quelltext stehen, sonst wird der Eintrag verworfen.",
     "Gegen einen absichtlich luegenden Extraktor geprueft: 1 genommen, 2 verworfen. "
     "'Kubernetes' und '12 Server' kamen nie ins Gedaechtnis.", "gemeinsam", 1, "2026-08-18"),
    ("e-zuordnung", "14.284 Wiki-Artikel den Menschen zugeordnet",
     "gemeinsam 11.543, gabriel 1.633, andreas 1.092, unbekannt 16.",
     "Gegenprobe: 0 Artikel aus projekt=Dr.-Unterweger landeten woanders als bei andreas.",
     "gemeinsam", 1, "2026-08-18"),
    ("e-export", "agentZero-Ordner autonom auf GitHub",
     "Code, Schema, leere UnifiedDB, Profile, Bauverlauf -- jede Datei mit Metadaten.",
     "Generation 36, 45 Dateien, Lecksuche nach Adressen leer.", "gabriel", 1, "2026-08-18"),
]

# ── Fehlschlaege. Gleichrangig, gleiche Sorgfalt. ──────────────────────────
FEHLSCHLAEGE = [
    ("f-leck", "Gedaechtnis konnte die zwei Menschen nicht trennen",
     "Andreas bekam in SEINER Sitzung Gabriels private Eintraege woertlich zurueck.",
     "Gemessen im Testlauf. Ursache: memory_tabelle hatte weder user_id noch "
     "session_id -- sie KONNTE strukturell nicht trennen. Behoben: Spalte ergaenzt, "
     "Bestand zugeordnet statt geraten, user_id ohne Vorgabewert.", "gemeinsam", 1, "2026-08-18"),
    ("f-schatten", "Schatten-Datenbank: Zuege gingen in eine zweite Datei",
     "env -i loeschte CLAYVERSE_DB_PATH, die Zuege landeten woanders.",
     "Gefunden beim Nachzaehlen, nicht durch eine Fehlermeldung.", "gemeinsam", 1, "2026-08-18"),
    ("f-77", "Schemaanlage in einer Lesefunktion riss 77 Tests ein",
     "executescript() committet implizit und zerlegte die laufende Transaktion.",
     "77 rote Tests, 'cannot commit - no transaction is active'. Heute per Test "
     "reproduziert: der Rollback-Pfad wirft dann selbst.", "gemeinsam", 1, "2026-08-18"),
    ("f-spalte", "Ein falscher Spaltenname, zweimal, beide Male verdeckt",
     "gehoert statt gehoert_zu. Einmal warf die Abfrage und ein except schluckte es "
     "('nichts gemessen' bei voller Tabelle), einmal gab .get() klaglos None -- "
     "die Vorstufe haette gelesen: kein Rechner gehoert dir.",
     "Beim Nachmessen der Verdichtung aufgefallen, nicht im Betrieb.", "gemeinsam", 1, "2026-08-18"),
    ("f-blind", "Zero war blind fuer die Menschen, obwohl die Daten dalagen",
     "Auf 'wem gehoert andreas-MACO?' kam korrekt UNBEKANNT -- es gab keinen Weg "
     "zu den Tabellen. Die Weigerung war richtig, die Blindheit war der Baufehler.",
     "Gemessener Testlauf, Zeros Antwort woertlich protokolliert. Behoben mit "
     "menschen_profil() und wiki_zuordnung().", "gemeinsam", 1, "2026-08-18"),
    ("f-docstring", "Ein veralteter Docstring erzeugte einen Fehlalarm",
     "Ein Pruefer meldete den Live-Chat-Pfad als unsicher -- gestuetzt auf einen "
     "Kommentar, den die Reparatur schon ueberholt hatte.",
     "Nachgemessen: active_turns leer, Doppel liegen 49 s bis 8 min auseinander "
     "(wiederholte Testeingaben, keine Doppelaufnahme). Veraltete Dokumentation "
     "verbrennt die Aufmerksamkeit, die ein echter Fehler braucht.", "gemeinsam", 1, "2026-08-18"),
    ("f-groq", "Zwei Groq-Modelle sind ohne Ankuendigung verschwunden",
     "llama-3.1-8b-instant und llama-3.3-70b-versatile: am 15.08. gemessen in "
     "Ordnung, am 18.08. beide 404.",
     "Live-Aufruf. Zeigt, dass ein Eichwert von vorgestern kein Betriebszustand ist.",
     "gemeinsam", 1, "2026-08-18"),
]


def sicherstellen(db) -> None:
    db.db.executescript(SCHEMA)


def grundstock(db) -> dict:
    """Wiederholbar. Ueberschreibt sauber, erfindet nichts dazu."""
    sicherstellen(db)
    zeilen = [(i, "erfolg", *rest) for i, *rest in
              [(x[0], *x[1:]) for x in ERFOLGE]]
    zeilen += [(i, "fehlschlag", *rest) for i, *rest in
               [(x[0], *x[1:]) for x in FEHLSCHLAEGE]]
    with db.tx() as sql:
        for z in zeilen:
            sql.execute(
                "INSERT INTO entityos_erfolge(id,art,titel,wirkung,beleg,gehoert,"
                "seit_zero,datum,erfasst) VALUES(?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET art=excluded.art,titel=excluded.titel,"
                "wirkung=excluded.wirkung,beleg=excluded.beleg,gehoert=excluded.gehoert,"
                "seit_zero=excluded.seit_zero,datum=excluded.datum,erfasst=excluded.erfasst",
                (*z, time.time()))
    return {
        "erfolge": db.db.execute(
            "SELECT COUNT(*) FROM entityos_erfolge WHERE art='erfolg'").fetchone()[0],
        "fehlschlaege": db.db.execute(
            "SELECT COUNT(*) FROM entityos_erfolge WHERE art='fehlschlag'").fetchone()[0],
    }


def bilanz(db, user_id: str | None = None) -> dict:
    """Erfolge und Fehlschlaege nebeneinander -- nie nur die eine Haelfte."""
    try:
        db.db.execute("SELECT 1 FROM entityos_erfolge LIMIT 1")
    except Exception:
        return {"stand": "NOCH_NICHT_ERFASST"}
    wo, args = "", []
    if user_id:
        wo, args = " WHERE gehoert IN (?, 'gemeinsam')", [user_id]
    zeilen = [dict(r) for r in db.db.execute(
        "SELECT art,titel,wirkung,beleg,gehoert,seit_zero,datum FROM entityos_erfolge"
        + wo + " ORDER BY art, datum DESC", args)]
    return {
        "erfolge": [z for z in zeilen if z["art"] == "erfolg"],
        "fehlschlaege": [z for z in zeilen if z["art"] == "fehlschlag"],
        "zeitraum": ("Zero ist seit 2026-08-18 in Benutzung -- einem Tag. Alles mit "
                     "seit_zero=1 stammt aus diesem Tag. Das ist kein Makel, aber es "
                     "zu verschweigen waere einer."),
        "warum_fehlschlaege": ("Jeder Fehlschlag hier hat im Betrieb NICHTS geworfen. "
                               "Die Liste ist das genaueste Bild davon, wie dieses "
                               "System kaputtgeht: still."),
    }
