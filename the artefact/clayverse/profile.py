"""Profile der zwei Menschen -- und wem was gehoert.

Warum das mehr ist als ein Adressbuch: Zero wurde im Testlauf gefragt "wer bin
ich?" und antwortete sinngemaess *"session_state.user_id = gabriel -- ein
Kennzeichen, kein Identitaetsbeleg"*. Das war epistemisch korrekt und trotzdem
ein Loch: die Clerk-gepruefte Identitaet erreichte Zero nie als BELEG, nur als
Zeichenkette. Ein Profil im kanonischen Zustand schliesst das.

Drei Regeln:

1. JEDES FELD TRAEGT SEINE HERKUNFT. `eigner` = vom Eigner erklaert,
   `iar.frank.ink` = von der Institutsseite gelesen, `abgeleitet` = aus Daten
   geschlossen. Ohne Herkunft ist ein Profilfeld eine Behauptung ueber einen
   Menschen -- und die gehoert belegt.

2. ZUGEHOERIGKEIT UND URHEBERSCHAFT SIND ZWEI DINGE. SeiMensch ist Andreas'
   Projekt, den Code hat Gabriel geschrieben. Wer das in ein Feld presst, macht
   aus einer Zusammenarbeit einen Besitzstreit. Deshalb `gehoert` und `gebaut`
   getrennt, und `gemeinsam` ist eine eigene Kategorie, keine Verlegenheitsloesung.

3. ERFOLG UND FEHLSCHLAG STEHEN NEBENEINANDER. Eine Projekttabelle, die nur
   Gelungenes fuehrt, ist ein Werbeblatt. Der Eigner hat Fehlschlaege
   ausdruecklich mitverlangt -- sie sind der Teil, aus dem sich etwas ablesen
   laesst.
"""
from __future__ import annotations

import json
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS entityos_profil(
  user_id TEXT NOT NULL,
  feld TEXT NOT NULL,
  wert TEXT NOT NULL,
  herkunft TEXT NOT NULL,          -- eigner | iar.frank.ink | abgeleitet | gemessen
  beleg TEXT,
  erfasst REAL NOT NULL,
  PRIMARY KEY(user_id, feld)
);
CREATE TABLE IF NOT EXISTS entityos_projekte(
  projekt TEXT PRIMARY KEY,
  gehoert TEXT,                    -- gabriel | andreas | gemeinsam
  gebaut_von TEXT,                 -- kann abweichen: Besitz ist nicht Urheberschaft
  stand TEXT NOT NULL,             -- laufend | abgeschlossen | gescheitert | ruht
  erfolg TEXT,                     -- erfolgreich | nicht_erfolgreich | offen
  seit_zero INTEGER NOT NULL DEFAULT 0,
  beschreibung TEXT,
  beleg TEXT,
  herkunft TEXT NOT NULL,
  erfasst REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS entityos_artikel_zuordnung(
  artikel_id TEXT PRIMARY KEY,
  gehoert TEXT NOT NULL,           -- gabriel | andreas | gemeinsam | unbekannt
  grund TEXT NOT NULL,
  sicherheit REAL NOT NULL,        -- 0..1
  erfasst REAL NOT NULL
);
"""

# ── Was der Eigner ausdruecklich erklaert hat ──────────────────────────────
ERKLAERT = [
    ("andreas", "rolle_institut", "Founder, Obmann (Chair), Senior Researcher", "iar.frank.ink", "Teamseite"),
    ("andreas", "titel", "Dipl.-Ing. Dr.nat.techn.", "iar.frank.ink", "Teamseite"),
    ("andreas", "name", "Dr. Andreas Unterweger", "iar.frank.ink", "Teamseite"),
    ("andreas", "ort", "Graz, Austria", "iar.frank.ink", "Teamseite"),
    ("andreas", "mail", "genuinos@gmail.com", "eigner", "Eignerbestaetigung 18.08., gegen Clerk geprueft"),
    ("andreas", "taetigkeit", "ehrenamtlich", "iar.frank.ink", "Zwei Gruender. Beide ehrenamtlich."),
    ("gabriel", "rolle_institut", "Co-founder, Vizeobmann (Deputy Chair), Lead Researcher", "iar.frank.ink", "Teamseite"),
    ("gabriel", "name", "Gabriel Gschaider", "iar.frank.ink", "Teamseite"),
    ("gabriel", "ort", "Knittelfeld -> Graz -> Siem Reap", "iar.frank.ink", "Teamseite"),
    ("gabriel", "mail", "structured.thinking.gschaider@gmail.com", "eigner", "gegen Clerk geprueft"),
    ("gabriel", "taetigkeit", "ehrenamtlich", "iar.frank.ink", "Zwei Gruender. Beide ehrenamtlich."),
    ("gabriel", "rolle_technisch", "schreibt den Code", "eigner",
     "Eigner 18.08.: 'seimensch ist das projekt von andreas aber allen code habe ich gemacht'"),
    ("gabriel", "github", "Eigentuemer des GitHub-Kontos gschaidergabriel", "eigner", "Eigner 18.08."),
]

GEMEINSAM = [
    ("institut", "Institut fuer Agentic Research (IAR), ZVR 1741094409, Feldkirchen bei Graz. "
                 "Unabhaengiger gemeinnuetziger Forschungsverein. Zwei Gruender, beide ehrenamtlich.",
     "iar.frank.ink", "Fusszeile und Teamseite"),
    ("herkunft_zero", "Zero ist aus diesem Institut hervorgegangen.", "eigner", "Eigner 18.08."),
]

PROJEKTE = [
    ("SeiMensch.net", "andreas", "gabriel", "laufend", "erfolgreich", 0,
     "Gemeinnuetziger Verein, Feldkirchen bei Graz. Projekt von Andreas, Code von Gabriel.",
     "Eigner 18.08.: 'seimensch ist das projekt von andreas aber allen code habe ich gemacht'", "eigner"),
    ("Naturareal SeiMensch", "andreas", None, "laufend", "offen", 0,
     "Gehoert Andreas.", "Eigner 18.08.", "eigner"),
    ("Project Frankenstein", "gabriel", "gabriel", "laufend", "offen", 0,
     "Gabriels Projekt.", "Eigner 18.08.", "eigner"),
    ("GitHub-Konto gschaidergabriel", "gabriel", "gabriel", "laufend", "erfolgreich", 0,
     "Traegt alle Repos des Aufbaus.", "Eigner 18.08.", "eigner"),
    ("Institut fuer Agentic Research", "gemeinsam", "gemeinsam", "laufend", "erfolgreich", 0,
     "ZVR 1741094409. Beide Gruender, beide ehrenamtlich.", "iar.frank.ink", "iar.frank.ink"),
    ("EntityOS / Zero", "gemeinsam", "gabriel", "laufend", "offen", 1,
     "Das System, in dem diese Zeilen stehen. Aufbau ab 2026-08-18.",
     "Bauverlauf in agentZero/bauverlauf", "abgeleitet"),
]


def sicherstellen(db) -> None:
    db.db.executescript(SCHEMA)


def _setze(db, user_id, feld, wert, herkunft, beleg=None) -> None:
    with db.tx() as sql:
        sql.execute(
            "INSERT INTO entityos_profil(user_id,feld,wert,herkunft,beleg,erfasst) "
            "VALUES(?,?,?,?,?,?) ON CONFLICT(user_id,feld) DO UPDATE SET "
            "wert=excluded.wert, herkunft=excluded.herkunft, beleg=excluded.beleg, "
            "erfasst=excluded.erfasst",
            (user_id, feld, wert, herkunft, beleg, time.time()))


def grundstock(db) -> dict:
    """Erklaerte und gelesene Angaben eintragen. Wiederholbar, ueberschreibt sauber."""
    sicherstellen(db)
    for uid, feld, wert, herkunft, beleg in ERKLAERT:
        _setze(db, uid, feld, wert, herkunft, beleg)
    for feld, wert, herkunft, beleg in GEMEINSAM:
        _setze(db, "gemeinsam", feld, wert, herkunft, beleg)
    for p in PROJEKTE:
        with db.tx() as sql:
            sql.execute(
                "INSERT INTO entityos_projekte(projekt,gehoert,gebaut_von,stand,erfolg,"
                "seit_zero,beschreibung,beleg,herkunft,erfasst) VALUES(?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(projekt) DO UPDATE SET gehoert=excluded.gehoert,"
                "gebaut_von=excluded.gebaut_von,stand=excluded.stand,erfolg=excluded.erfolg,"
                "seit_zero=excluded.seit_zero,beschreibung=excluded.beschreibung,"
                "beleg=excluded.beleg,herkunft=excluded.herkunft,erfasst=excluded.erfasst",
                (*p, time.time()))
    return {
        "profilfelder": db.db.execute("SELECT COUNT(*) FROM entityos_profil").fetchone()[0],
        "projekte": db.db.execute("SELECT COUNT(*) FROM entityos_projekte").fetchone()[0],
    }


def profil(db, user_id: str, *, mit_gemeinsam: bool = True) -> dict:
    """Was Zero ueber den gerade anwesenden Menschen wissen darf.

    ⚠️ Legt KEINE Tabellen an. sicherstellen() ruft executescript(), und das
    committet implizit -- aus einem laufenden Zug heraus aufgerufen reisst es
    dessen Transaktion auseinander (gemessen: 77 rote Tests). Schemaanlage ist
    eine Startaufgabe, keine Leseaufgabe. Eine Lesefunktion, die nebenbei
    Tabellen anlegt, ist eine Schreiboperation im Tarnanzug.
    """
    try:
        db.db.execute("SELECT 1 FROM entityos_profil LIMIT 1")
    except Exception:
        return {"user_id": user_id, "felder": {}, "gemeinsam": {}, "projekte": [],
                "rechner": [], "hinweis": "Profiltabellen noch nicht angelegt."}
    felder = {r["feld"]: {"wert": r["wert"], "herkunft": r["herkunft"]}
              for r in db.db.execute(
                  "SELECT feld,wert,herkunft FROM entityos_profil WHERE user_id=?", (user_id,))}
    geteilt = {}
    if mit_gemeinsam:
        geteilt = {r["feld"]: {"wert": r["wert"], "herkunft": r["herkunft"]}
                   for r in db.db.execute(
                       "SELECT feld,wert,herkunft FROM entityos_profil WHERE user_id='gemeinsam'")}
    projekte = [dict(r) for r in db.db.execute(
        "SELECT projekt,gehoert,gebaut_von,stand,erfolg,seit_zero,beschreibung "
        "FROM entityos_projekte WHERE gehoert IN (?, 'gemeinsam') OR gebaut_von=? "
        "ORDER BY seit_zero DESC, projekt", (user_id, user_id))]
    # Welcher Rechner wem gehoert -- Eignerforderung, damit die Vorstufe es
    # einbezieht und Zero es weiss. Quelle ist die Wirtetabelle, die aus den
    # Herzschlaegen gespeist wird; die Zuordnung selbst ist deklariert.
    rechner = []
    try:
        for r in db.db.execute(
                "SELECT wirt,gehoert_zu,gesund,zuletzt_gesehen FROM entityos_wirte ORDER BY wirt"):
            rechner.append({"wirt": r["wirt"], "gehoert_zu": r["gehoert_zu"],
                            "meiner": r["gehoert_zu"] == user_id,
                            "gesund": bool(r["gesund"])})
    except Exception:
        pass

    return {
        "user_id": user_id,
        "felder": felder,
        "gemeinsam": geteilt,
        "projekte": projekte,
        "rechner": rechner,
        "hinweis": ("Jedes Feld traegt seine Herkunft. 'eigner' heisst vom Eigner erklaert, "
                    "'iar.frank.ink' gelesen, 'abgeleitet' geschlossen, 'gemessen' belegt. "
                    "Zugehoerigkeit (gehoert) und Urheberschaft (gebaut_von) sind getrennt: "
                    "wer beides in ein Feld presst, macht aus Zusammenarbeit einen Besitzstreit."),
    }


def sitzungsvorspann(db, user_id: str, session_id: str, platz: int | None = None) -> str:
    """Der Satz, der im Prompt steht: WER gerade da ist -- als Beleg, nicht als Zeichenkette."""
    p = profil(db, user_id)
    name = (p["felder"].get("name") or {}).get("wert", user_id)
    rolle = (p["felder"].get("rolle_institut") or {}).get("wert", "")
    andere = "andreas" if user_id == "gabriel" else "gabriel"
    zeilen = [
        "<anwesender_mensch autoritaet=\"clerk-verifiziert\">",
        f"  Diese Sitzung gehoert {name} ({user_id}).",
        f"  Sitzung: {session_id}" + (f", Platz {platz}" if platz else ""),
        f"  Rolle: {rolle}" if rolle else "",
        "  Das ist KEIN Kennzeichen aus dem Text, sondern der kanonische Zustand nach",
        "  geprüfter Clerk-Anmeldung. Du darfst diesen Menschen beim Namen nennen.",
        f"  Der andere Mensch ist {andere} und ist hier NICHT anwesend. Nichts aus dieser",
        "  Sitzung gehoert in seine.",
        "",
        "  NACHSCHLAGEN statt schaetzen -- diese Angaben stehen NICHT in memory_search",
        "  oder embedding_search, sondern in eigenen Tabellen:",
        "    menschen_profil()          Rolle, Projekte, welche Rechner ihm gehoeren,",
        "                               welcher Teil des Wikis. Jedes Feld mit Herkunft.",
        "    wiki_zuordnung(projekt)    welcher Teil des Wikis wem zugerechnet wird.",
        "  Wenn du nach Zugehoerigkeit gefragt wirst, RUF SIE AUF. Findest du dort",
        "  nichts, sage das -- aber sage es erst danach.",
        "</anwesender_mensch>",
    ]
    return "\n".join(z for z in zeilen if z)
