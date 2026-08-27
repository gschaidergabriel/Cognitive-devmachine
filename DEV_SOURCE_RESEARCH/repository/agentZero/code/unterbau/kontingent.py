#!/usr/bin/env python3
"""
kontingent.py — B17, das Kontingentbuch.

ClayVerse ist GETAKTET, nicht reaktiv: alles, was einen Modellaufruf kostet,
geht in eine Warteschlange, ein Takt nimmt ein BATCH, und vor jedem Batch
prueft er das Restbudget. Ohne Buch kann kein Takt entscheiden, wie gross
sein Batch sein darf. Dieses Werkzeug IST das Buch.

Phase A (dieses Werkzeug): funktioniert mit NULL echten Schluesseln.
Struktur, Buchfuehrung, Warnlogik -- alles mit synthetischen Eintraegen
pruefbar. Es wird kein Geheimnis bewegt, gelesen oder ausgegeben.
Phase B (spaeter, nicht hier): Schluessel kommen dazu (Muster: GH-Token unter
/etc/clayverse/github-token.env, 600 root:root, EnvironmentFile= in der Unit).

Zwei Dimensionen, aus dem Plan (B17-Tabelle, wortgleich uebernommen):

  kb_konto   WER bucht         Vorrang, eigenes Limit (falls vorhanden), an
                                wen die Warnung geht. 4 Zeilen aus dem Plan:
                                Master Clay, Clay (Andreas), kuenftige Nutzer,
                                ClayVerse selbst.
  kb_zugang  WOFUER gebucht    Externe Konten/Abos mit ihren eigenen, von
             wird              aussen gesetzten Grenzen (5h-Fenster, Credits,
                                Anfragen/Tag, ...). Diese Grenze ist GETEILT
                                ueber alle Konten, die diesen Zugang nutzen --
                                das innere Limit aus kb_konto ist zusaetzlich,
                                nicht dasselbe.

  kb_buchung  jede verzeichnete Verbrauchsmenge (konto x zugang x zeit)
  kb_warnung  jede ausgeloeste Warnung, angehaengt, nicht ueberschrieben

Vier Unterbefehle, mindestens:
  buchen    einen Verbrauch verzeichnen
  stand     Stand je Zugang und je Konto
  darf      darf ein Batch der Groesse N jetzt laufen -- der Aufruf des Takts.
            Antwortet mit einer ZAHL (wie viele Einheiten leistbar sind),
            nicht mit ja/nein, und nennt, welches Limit gebunden hat.
  warnung   was gerade vom eigenen Normalzustand abweicht

Dazu, zur Einrichtung/Pruefung:
  init      Katalog anlegen/aktualisieren (idempotent, aus KONTEN/ZUGAENGE
            unten -- Quelle ist dieser Code, nicht Handarbeit in der DB)
  katalog   Katalog anzeigen

Mechanisch, keine Modellaufrufe. stdlib: sqlite3, argparse, statistics, json,
zoneinfo. Schreibt NUR kb_*-Tabellen in /var/lib/clay/wiki.db. Liest lesend
aus `taetigkeit` (Fortschritts-Signal fuer die dritte Warnung) -- schreibt
dort nichts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sqlite3
import sys

# Modulgrenze: der LESE-Zweig oeffnet die Datenbank nicht mehr selbst.
# udb ist die Vordertuer fuer den nur-lesenden Fall; der Schreib-Zweig
# bleibt lokal, weil udb.verbindung() strukturell nur liest.
sys.path.insert(0, "/opt/unifieddb")
import udb
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

DB_PATH = "/var/lib/clay/wiki.db"
TZ = ZoneInfo("Europe/Vienna")           # "9 Uhr unserer Zeit, NICHT Mitternacht"

# ---------------------------------------------------------------- Katalog --
# Wortgleich aus dem B17-Plan uebernommen. Zahlen NUR dort eingetragen, wo
# der Plan eine Zahl nennt -- "je eigene Grenzen" bleibt NULL, nicht
# geraten. Das ist Grundregel des Kunden/der Methode: nichts erfinden.

KONTEN = [
    # konto, anzeige, vorrang(0=hoechster), hat_eigenes_limit,
    # eigenes_limit_wert, eigenes_limit_einheit, eigenes_limit_fenster,
    # warnung_an, wirt (Bruecke zu taetigkeit.wirt -- GEMESSEN, nicht geraten:
    # 'ai-core-node-projekt-frankenstein' ist der Wirtsname dieser Maschine,
    # 'andreas-MACO' und 'clayverse' stehen so in taetigkeit; siehe Bericht)
    ("master_clay", "Master Clay (Gabriel)", 0, 0, None, None, None,
     "gabriel", "ai-core-node-projekt-frankenstein"),
    ("clay_andreas", "Clay (Andreas)", 0, 0, None, None, None,
     "andreas,gabriel", "andreas-MACO"),
    ("kuenftige_nutzer", "kuenftige Nutzer", 1, 1, None, None, None,
     "nutzer,gabriel", None),
    ("clayverse", "ClayVerse selbst (Grundlast)", 2, 1, None, None, "tag",
     "gabriel", "clayverse"),
]

ZUGAENGE = [
    # zugang, anzeige, einheit, fenster_dauer_sekunden, fenster_limit,
    # woche_limit, tag_limit, minute_limit, tageswechsel_stunde,
    # spitzenzeit_json, geteilt_mit, besonderheit, mehrdeutiger_schluessel
    ("claude_pro", "Claude Pro", "token", 5 * 3600, None, None, None, None,
     None, None, "chat",
     "5-Stunden-Fenster + Wochendeckel, rollierend, geteilt mit dem Chat. "
     "Keine Zahl im Plan genannt -- daher kein hartes Limit hier gefuehrt, "
     "nur Normbremse.", 0),
    ("zai_glm_lite", "z.ai GLM Lite", "credits", 5 * 3600, 2000, 10000,
     None, None, None,
     json.dumps({"von_stunde": 8, "bis_stunde": 12,
                 "faktor_spitze": 3, "faktor_sonst": 2}),
     None,
     "2.000 Credits je 5h, 10.000/Woche. Spitzenzeit 8-12 Uhr kostet 3x, "
     "sonst 2x.", 0),
    ("openrouter", "OpenRouter", "euro", None, None, None, None, None,
     None, None, None,
     "Restguthaben in Euro. Aufladung mit Mindestgebuehr. Kein periodisches "
     "Limit, sondern ein sinkender Kontostand -- darf() behandelt das "
     "gesondert (Reserve statt Fenster).", 0),
    ("deepseek", "DeepSeek", "?", None, None, None, None, None, None,
     json.dumps({"nebenzeit_faktor": 0.5}), None,
     "Guthaben. Ab 16.08. Spitzen-/Nebenzeit, Nebenzeit halb (Faktor "
     "gegeben, absolute Uhrzeiten NICHT -- nicht erfunden).", 0),
    ("gemini_frei", "Gemini frei", "anfragen", 86400, None, None, 1500, 15,
     9, None, None,
     "1.500 Anfragen/Tag, 15/min. Tageswechsel 9 Uhr unserer Zeit, NICHT "
     "Mitternacht.", 0),
    ("mistral", "Mistral", None, None, None, None, None, None, None, None,
     None, "je eigene Grenzen -- im Plan nicht beziffert.", 1),
    ("groq", "Groq", None, None, None, None, None, None, None, None, None,
     "je eigene Grenzen -- im Plan nicht beziffert.", 1),
    ("nvidia", "NVIDIA", None, None, None, None, None, None, None, None,
     None, "je eigene Grenzen -- im Plan nicht beziffert.", 1),
    ("hf", "HF (Hugging Face)", None, None, None, None, None, None, None,
     None, None, "je eigene Grenzen -- im Plan nicht beziffert.", 1),
    ("cloudflare", "Cloudflare", None, None, None, None, None, None, None,
     None, None, "je eigene Grenzen -- im Plan nicht beziffert.", 1),
    ("ocrspace", "OCRSpace", None, None, None, None, None, None, None, None,
     None, "je eigene Grenzen -- im Plan nicht beziffert.", 0),
    # --- am 2026-08-15 gemessen (Werkzeug-Zugaenge, siehe werkzeuge.py) ------
    # Zahlen NUR wo gemessen oder vom Anbieter veroeffentlicht. Sonst NULL.
    ("tavily", "Tavily (Suche fuer LLMs)", "credits", None, None, None, None,
     None, None, None, None,
     "Gemessen 2026-08-15: HTTP 200, ~1,4 s. Anbieter nennt 1.000 Credits je "
     "Monat frei; basic=1, advanced=2 Credits. Monatsfenster fuehrt dieser "
     "Katalog nicht -- daher kein hartes Limit, nur Zaehlung.", 0),
    ("exa", "Exa (semantische Suche)", "credits", None, None, None, None,
     None, None, None, None,
     "Gemessen 2026-08-15: HTTP 200, ~1,1 s. Anbieter nennt 20 USD bei "
     "Anmeldung plus 10 USD je Monat, danach ~7 USD je 1.000 Suchen. Kein "
     "Anfragen-Limit veroeffentlicht -- daher nur Zaehlung.", 0),
    ("openalex", "OpenAlex (Literatur)", "credits", None, None, None, 10000,
     None, 2, None, None,
     "GEMESSEN 2026-08-15 an den Kopfzeilen: MIT unserem Schluessel "
     "x-ratelimit-limit=10000 Credits bzw. 1 USD je Tag; OHNE Schluessel "
     "(polite pool) nur 1000 bzw. 0,1 USD -- der Schluessel bringt also "
     "Faktor 10. Eine Werksuche kostet 10 Credits (0,001 USD). Ruecksetzung "
     "Mitternacht UTC; tageswechsel_stunde=2 gilt fuer Sommerzeit, im Winter "
     "waere es 1 -- die Sommer-/Winterzeit bildet dieses Feld nicht ab.", 0),
    ("e2b", "E2B (Code-Sandkasten)", "sandkaesten", None, None, None, None,
     None, None, None, None,
     "Gemessen 2026-08-15: Sandkasten erzeugen HTTP 201 in ~0,6 s, Code "
     "laeuft (Rechenprobe korrekt), Loeschen HTTP 204. Freies Kontingent "
     "UNBEKANNT: die Quellen widersprechen sich (100 h je Monat gegen "
     "einmalig 100 USD Guthaben; 5 gegen 20 parallele Sandkaesten). Nicht "
     "geraten.", 0),
    ("rapidapi", "RapidAPI (Tor zu vielen APIs)", None, None, None, None,
     None, None, None, None, None,
     "Gemessen 2026-08-15: Schluessel wird angenommen, aber JEDE geprobte "
     "API antwortet HTTP 403 'You are not subscribed to this API'. Ohne "
     "Abonnement je API im RapidAPI-Konto unbrauchbar. Kontingent daher "
     "UNBEKANNT.", 0),
]

# Normbremse: fuer Zugaenge OHNE hartes Limit (claude_pro, openrouter,
# deepseek, mistral, groq, nvidia, hf, cloudflare) ist die Warnung der
# EINZIGE Bremsklotz, siehe Plan-Warnung. darf() braucht trotzdem eine Zahl
# -- sie faellt auf ein Vielfaches des eigenen Stundenmittels zurueck.
NORM_FAKTOR = 2.0          # Deckel = Mittel(gleiche Stunde) * NORM_FAKTOR
NORM_MIN_SAMPLES = 5        # unter dieser Anzahl: kein Muster, keine Bremse
WARN_Z = 2.0                # Sigma-Schwelle fuer "ueber_norm"
WARN_LOOKBACK_TAGE = 21     # wie weit zurueck der Normwert gebildet wird


# --------------------------------------------------------------- DB-Basis --


# ── VORRANG ALS RESERVIERUNG ────────────────────────────────────────────
# Anteil des Fensters, der nachrangigen Konten NICHT zur Verfuegung steht.
# vorrang 0 = Gabriel und Andreas: voller Topf.
# vorrang 1 = kuenftige Nutzer: ein Viertel bleibt reserviert.
# vorrang 2 = ClayVerses eigene Grundlast: zwei Fuenftel bleiben reserviert.
# Gemessen am GESAMTVERBRAUCH des Topfes, nicht am eigenen -- sonst waere
# es keine Reservierung, sondern nur ein zweites eigenes Limit.
RESERVE_JE_VORRANG = {0: 0.0, 1: 0.25, 2: 0.40}

def connect_db(readonly: bool = False) -> sqlite3.Connection:
    if readonly:
        con = udb.verbindung()
    else:
        con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")
    con.row_factory = sqlite3.Row
    return con


def retry_locked(fn, tries: int = 6, base_sleep: float = 0.5):
    last = None
    for i in range(tries):
        try:
            return fn()
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() or "busy" in str(e).lower():
                last = e
                time.sleep(base_sleep * (i + 1))
                continue
            raise
    raise last


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_zeit(z: str) -> datetime:
    dt = datetime.fromisoformat(z.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def ensure_schema(con: sqlite3.Connection) -> None:
    con.executescript("""
        CREATE TABLE IF NOT EXISTS kb_konto (
            konto                 TEXT PRIMARY KEY,
            anzeige                TEXT NOT NULL,
            vorrang                 INTEGER NOT NULL,
            hat_eigenes_limit        INTEGER NOT NULL DEFAULT 0
                                     CHECK (hat_eigenes_limit IN (0,1)),
            eigenes_limit_wert       REAL,
            eigenes_limit_einheit    TEXT,
            eigenes_limit_fenster    TEXT,
            warnung_an              TEXT NOT NULL,
            wirt                    TEXT,
            angelegt                TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS kb_zugang (
            zugang                    TEXT PRIMARY KEY,
            anzeige                    TEXT NOT NULL,
            einheit                    TEXT,
            fenster_dauer_sekunden      INTEGER,
            fenster_limit                REAL,
            woche_limit                  REAL,
            tag_limit                    REAL,
            minute_limit                 REAL,
            tageswechsel_stunde          INTEGER,
            spitzenzeit_json             TEXT,
            geteilt_mit                  TEXT,
            besonderheit                TEXT NOT NULL,
            mehrdeutiger_schluessel      INTEGER NOT NULL DEFAULT 0
                                         CHECK (mehrdeutiger_schluessel IN (0,1)),
            angelegt                    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS kb_buchung (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            zeit                   TEXT NOT NULL,
            konto                   TEXT NOT NULL REFERENCES kb_konto(konto),
            zugang                   TEXT NOT NULL REFERENCES kb_zugang(zugang),
            menge                    REAL NOT NULL CHECK (menge >= 0),
            einheit                  TEXT,
            zweck                    TEXT,
            batch_id                 TEXT,
            taetigkeit_id             INTEGER,
            schluessel_hinweis        TEXT,
            quelle                   TEXT NOT NULL DEFAULT 'buchen'
                                     CHECK (quelle IN ('buchen','synthetic')),
            roh_hash                 TEXT UNIQUE
        );
        CREATE INDEX IF NOT EXISTS kb_buchung_kz_zeit
            ON kb_buchung(konto, zugang, zeit);
        CREATE INDEX IF NOT EXISTS kb_buchung_batch
            ON kb_buchung(batch_id);

        CREATE TABLE IF NOT EXISTS kb_warnung (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            zeit                TEXT NOT NULL,
            konto                TEXT,
            zugang                TEXT,
            art                  TEXT NOT NULL CHECK (art IN (
                                 'ueber_norm', 'reset_naehert_sich',
                                 'verbrauch_ohne_fortschritt',
                                 'mehrdeutiger_schluessel',
                                 'kein_limit_kein_muster')),
            text                 TEXT NOT NULL,
            kennzahlen_json       TEXT
        );
        CREATE INDEX IF NOT EXISTS kb_warnung_zeit ON kb_warnung(zeit);
    """)
    con.commit()


def cmd_init(_a) -> None:
    con = connect_db()
    ensure_schema(con)
    t = now_iso()
    for (konto, anzeige, vorrang, hat_limit, wert, einheit, fenster,
         warnung_an, wirt) in KONTEN:
        con.execute("""
            INSERT INTO kb_konto (konto, anzeige, vorrang, hat_eigenes_limit,
                eigenes_limit_wert, eigenes_limit_einheit,
                eigenes_limit_fenster, warnung_an, wirt, angelegt)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(konto) DO UPDATE SET
                anzeige=excluded.anzeige, vorrang=excluded.vorrang,
                hat_eigenes_limit=excluded.hat_eigenes_limit,
                eigenes_limit_einheit=excluded.eigenes_limit_einheit,
                eigenes_limit_fenster=excluded.eigenes_limit_fenster,
                warnung_an=excluded.warnung_an, wirt=excluded.wirt
        """, (konto, anzeige, vorrang, hat_limit, wert, einheit, fenster,
              warnung_an, wirt, t))
    for (zugang, anzeige, einheit, fd, fl, wl, tl, ml, twh, spitz, geteilt,
         bes, mehrdeutig) in ZUGAENGE:
        con.execute("""
            INSERT INTO kb_zugang (zugang, anzeige, einheit,
                fenster_dauer_sekunden, fenster_limit, woche_limit, tag_limit,
                minute_limit, tageswechsel_stunde, spitzenzeit_json,
                geteilt_mit, besonderheit, mehrdeutiger_schluessel, angelegt)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(zugang) DO UPDATE SET
                anzeige=excluded.anzeige, einheit=excluded.einheit,
                fenster_dauer_sekunden=excluded.fenster_dauer_sekunden,
                fenster_limit=excluded.fenster_limit,
                woche_limit=excluded.woche_limit, tag_limit=excluded.tag_limit,
                minute_limit=excluded.minute_limit,
                tageswechsel_stunde=excluded.tageswechsel_stunde,
                spitzenzeit_json=excluded.spitzenzeit_json,
                geteilt_mit=excluded.geteilt_mit,
                besonderheit=excluded.besonderheit,
                mehrdeutiger_schluessel=excluded.mehrdeutiger_schluessel
        """, (zugang, anzeige, einheit, fd, fl, wl, tl, ml, twh, spitz,
              geteilt, bes, mehrdeutig, t))
    con.commit()
    print(f"kb_konto: {len(KONTEN)} Zeilen · kb_zugang: {len(ZUGAENGE)} Zeilen "
          f"(angelegt/aktualisiert)")


def cmd_katalog(_a) -> None:
    con = connect_db(readonly=True)
    ensure_schema_checked(con)
    print("\n-- kb_konto -----------------------------------------------")
    for r in con.execute("SELECT * FROM kb_konto ORDER BY vorrang, konto"):
        limit = ("keins" if not r["hat_eigenes_limit"] else
                 (f"{r['eigenes_limit_wert']} {r['eigenes_limit_einheit'] or ''}"
                  f"/{r['eigenes_limit_fenster']}" if r["eigenes_limit_wert"]
                  is not None else "ja, noch nicht konfiguriert (Phase B)"))
        print(f"  {r['konto']:<18} vorrang={r['vorrang']}  limit={limit}"
              f"  warnung_an={r['warnung_an']}  wirt={r['wirt']}")
    print("\n-- kb_zugang ----------------------------------------------")
    for r in con.execute("SELECT * FROM kb_zugang ORDER BY zugang"):
        mehrd = " ⚠mehrdeutiger Schluessel" if r["mehrdeutiger_schluessel"] else ""
        print(f"  {r['zugang']:<14} einheit={r['einheit'] or '?':<8} "
              f"{r['besonderheit']}{mehrd}")
    print()


def ensure_schema_checked(con: sqlite3.Connection) -> None:
    """Fuer lesende Befehle: Schema pruefen, nicht schreiben. Wenn der
    Katalog leer ist, deutlich sagen -- statt stumm auf leeren Tabellen zu
    rechnen (das waere eine Messung, die etwas Falsches fuer 'kein
    Verbrauch' haelt)."""
    row = con.execute(
        "SELECT count(*) c FROM sqlite_master WHERE name='kb_konto'"
    ).fetchone()
    if row["c"] == 0:
        sys.exit("kb_konto fehlt. Erst 'kontingent.py init' laufen lassen.")


# ------------------------------------------------------------- buchen -----

def cmd_buchen(a) -> None:
    con = connect_db()
    ensure_schema(con)
    _pruefe_katalog_eintrag(con, "kb_konto", "konto", a.konto)
    _pruefe_katalog_eintrag(con, "kb_zugang", "zugang", a.zugang)
    if a.menge < 0:
        sys.exit("menge muss >= 0 sein.")

    zeit = a.zeit or now_iso()
    roh_hash = None
    if a.dedupe_key:
        roh_hash = hashlib.sha256(
            f"{a.konto}|{a.zugang}|{a.dedupe_key}".encode()).hexdigest()[:32]

    def _insert():
        cur = con.execute("""
            INSERT INTO kb_buchung (zeit, konto, zugang, menge, einheit,
                zweck, batch_id, taetigkeit_id, schluessel_hinweis, quelle,
                roh_hash)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (zeit, a.konto, a.zugang, a.menge, a.einheit, a.zweck,
              a.batch_id, a.taetigkeit_id, a.schluessel_hinweis, a.quelle,
              roh_hash))
        con.commit()
        return cur.lastrowid

    try:
        rid = retry_locked(_insert)
    except sqlite3.IntegrityError:
        print(f"schon gebucht (dedupe_key={a.dedupe_key!r}) -- uebersprungen")
        return

    print(f"gebucht #{rid}: {a.konto} x {a.zugang}  {a.menge} "
          f"{a.einheit or '(Zugang-Einheit)'}  [{a.quelle}]"
          + (f"  zweck={a.zweck}" if a.zweck else "")
          + (f"  batch={a.batch_id}" if a.batch_id else ""))


def _pruefe_katalog_eintrag(con, tabelle, spalte, wert):
    row = con.execute(
        f"SELECT 1 FROM {tabelle} WHERE {spalte}=?", (wert,)).fetchone()
    if not row:
        sys.exit(f"Unbekannt: {spalte}={wert!r} steht nicht in {tabelle}. "
                  f"'kontingent.py katalog' zeigt die gueltigen Werte.")


# -------------------------------------------------------------- Fenster ---

def _fensteranfang(zugang_row: sqlite3.Row, jetzt: datetime) -> dict:
    """Fuer jede bekannte Fenstersorte (rollierendes Fenster, Minute, Tag,
    Woche) den Beginn des aktuell laufenden Fensters -- nur fuer die, die
    der Katalog tatsaechlich fuehrt (Wert ungleich NULL)."""
    jetzt_lokal = jetzt.astimezone(TZ)
    grenzen = {}
    if zugang_row["fenster_limit"] is not None and zugang_row["fenster_dauer_sekunden"]:
        dauer = zugang_row["fenster_dauer_sekunden"]
        epoch = int(jetzt.timestamp())
        beginn_epoch = epoch - (epoch % dauer)
        grenzen["fenster"] = (datetime.fromtimestamp(beginn_epoch, tz=timezone.utc),
                               zugang_row["fenster_limit"])
    if zugang_row["minute_limit"] is not None:
        beginn = jetzt.replace(second=0, microsecond=0)
        grenzen["minute"] = (beginn, zugang_row["minute_limit"])
    if zugang_row["tag_limit"] is not None:
        wechsel = zugang_row["tageswechsel_stunde"] or 0
        lok = jetzt_lokal
        grenze_heute = lok.replace(hour=wechsel, minute=0, second=0, microsecond=0)
        beginn_lok = grenze_heute if lok >= grenze_heute else grenze_heute - timedelta(days=1)
        grenzen["tag"] = (beginn_lok.astimezone(timezone.utc), zugang_row["tag_limit"])
    if zugang_row["woche_limit"] is not None:
        lok = jetzt_lokal
        beginn_lok = (lok - timedelta(days=lok.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0)
        grenzen["woche"] = (beginn_lok.astimezone(timezone.utc), zugang_row["woche_limit"])
    return grenzen


def _verbraucht_seit(con, konto, zugang, seit: datetime) -> float:
    row = con.execute("""
        SELECT COALESCE(SUM(menge), 0) s FROM kb_buchung
        WHERE zugang=? AND zeit >= ?
          AND (? IS NULL OR konto = ?)
    """, (zugang, seit.isoformat(), konto, konto)).fetchone()
    return row["s"] or 0.0


# ------------------------------------------------------------------ darf --

def cmd_darf(a) -> None:
    con = connect_db()
    ensure_schema(con)
    _pruefe_katalog_eintrag(con, "kb_konto", "konto", a.konto)
    zrow = con.execute("SELECT * FROM kb_zugang WHERE zugang=?",
                        (a.zugang,)).fetchone()
    if not zrow:
        sys.exit(f"Unbekannt: zugang={a.zugang!r}.")
    krow = con.execute("SELECT * FROM kb_konto WHERE konto=?",
                        (a.konto,)).fetchone()

    jetzt = parse_zeit(a.zeit) if a.zeit else datetime.now(timezone.utc)
    n = a.menge
    erlaubt = n
    grund = "angefragt"
    einzelheiten = {}

    # 1) Aeusseres Limit (Zugang, GETEILT ueber alle Konten, die diesen
    #    Zugang nutzen -- shared pool, kein Konto-Filter).
    fenster = _fensteranfang(zrow, jetzt)
    vorrang = int(krow["vorrang"]) if krow and krow["vorrang"] is not None else 2
    reserve = RESERVE_JE_VORRANG.get(vorrang, 0.40)
    for name, (beginn, limit) in fenster.items():
        verbraucht = _verbraucht_seit(con, None, a.zugang, beginn)
        rest = max(0.0, limit - verbraucht)
        einzelheiten[f"zugang.{name}"] = {
            "limit": limit, "verbraucht": verbraucht, "rest": rest,
            "beginn": beginn.isoformat()}
        if rest < erlaubt:
            erlaubt, grund = rest, f"zugang-{name}"
        # Reservierung: nachrangige Konten sehen nur den unreservierten Teil.
        if reserve > 0.0:
            decke = limit * (1.0 - reserve)
            rest_res = max(0.0, decke - verbraucht)
            einzelheiten[f"zugang.{name}.reserviert"] = {
                "vorrang": vorrang, "reserve_anteil": reserve,
                "decke_fuer_dieses_konto": round(decke, 3),
                "rest_unter_decke": round(rest_res, 3)}
            if rest_res < erlaubt:
                erlaubt, grund = rest_res, f"vorrang-reserve-{name}"

    # 2) Inneres Limit (Konto, NUR fuer dieses eine Konto).
    if krow and krow["hat_eigenes_limit"]:
        if krow["eigenes_limit_wert"] is None:
            einzelheiten["konto.limit"] = "vorgesehen, aber Phase B noch " \
                                           "nicht konfiguriert -- keine Bremse hier"
        else:
            f = krow["eigenes_limit_fenster"] or "tag"
            jetzt_lokal = jetzt.astimezone(TZ)
            if f == "tag":
                beginn = jetzt_lokal.replace(hour=0, minute=0, second=0,
                                              microsecond=0).astimezone(timezone.utc)
            else:
                beginn = jetzt - timedelta(seconds=86400)
            verbraucht = _verbraucht_seit(con, a.konto, a.zugang, beginn)
            rest = max(0.0, krow["eigenes_limit_wert"] - verbraucht)
            einzelheiten["konto.limit"] = {
                "limit": krow["eigenes_limit_wert"], "verbraucht": verbraucht,
                "rest": rest}
            if rest < erlaubt:
                erlaubt, grund = rest, "konto-limit"

    # 3) Kein aeusseres UND kein konfiguriertes inneres Limit gefunden ->
    #    Normbremse. Das ist der Fall, den die Plan-Warnung meint: "kein
    #    Limit heisst nicht keine Grenze". claude_pro/openrouter/deepseek/
    #    mistral/groq/nvidia/hf/cloudflare landen hier.
    hat_hartes_limit = bool(fenster) or (krow and krow["hat_eigenes_limit"]
                                          and krow["eigenes_limit_wert"] is not None)
    if not hat_hartes_limit:
        mittel, n_samples = _stundenmittel(con, a.konto, a.zugang, jetzt)
        if n_samples >= NORM_MIN_SAMPLES:
            deckel = mittel * NORM_FAKTOR
            einzelheiten["norm.deckel"] = {
                "mittel_gleiche_stunde": mittel, "n": n_samples,
                "deckel": deckel}
            if deckel < erlaubt:
                erlaubt, grund = deckel, "norm-bremse"
        else:
            einzelheiten["norm.deckel"] = (
                f"nur {n_samples} Beobachtungen zur gleichen Stunde "
                f"(< {NORM_MIN_SAMPLES}) -- noch kein Muster, keine Bremse. "
                f"'kein Limit' UND 'kein Muster': erlaubt bleibt die "
                f"angefragte Menge.")
            if grund == "angefragt":
                grund = "kein_limit_kein_muster"

    erlaubt = max(0.0, min(erlaubt, n))
    if a.json:
        print(json.dumps({"erlaubt": erlaubt, "angefragt": n, "grund": grund,
                          "einzelheiten": einzelheiten}, ensure_ascii=False,
                         default=str, indent=2))
    else:
        print(f"\n{erlaubt:g} von {n:g} angefragten Einheiten erlaubt "
              f"({a.konto} x {a.zugang})")
        print(f"gebunden durch: {grund}\n")
        for k, v in einzelheiten.items():
            print(f"  {k}: {v}")
        print()


def _stundenmittel(con, konto, zugang, jetzt: datetime) -> tuple[float, int]:
    """Mittel der Buchungen zur GLEICHEN Stunde des Tages (Europe/Vienna),
    ueber die letzten WARN_LOOKBACK_TAGE Tage, fuer genau dieses
    (konto, zugang)-Paar. Ein fixer Schwellwert waere an einem ruhigen Tag
    zu niedrig, an einem Bautag zu hoch -- deshalb der eigene Massstab statt
    einer absoluten Zahl."""
    seit = (jetzt - timedelta(days=WARN_LOOKBACK_TAGE)).isoformat()
    stunde = jetzt.astimezone(TZ).hour
    rows = con.execute("""
        SELECT zeit, menge FROM kb_buchung
        WHERE konto=? AND zugang=? AND zeit >= ?
    """, (konto, zugang, seit)).fetchall()
    werte = [r["menge"] for r in rows
             if parse_zeit(r["zeit"]).astimezone(TZ).hour == stunde]
    if not werte:
        return 0.0, 0
    return statistics.mean(werte), len(werte)


# ------------------------------------------------------------------ stand -

def cmd_stand(a) -> None:
    con = connect_db(readonly=True)
    ensure_schema_checked(con)
    jetzt = datetime.now(timezone.utc)
    zugaenge = con.execute(
        "SELECT * FROM kb_zugang" + (" WHERE zugang=?" if a.zugang else "")
        + " ORDER BY zugang", (a.zugang,) if a.zugang else ()).fetchall()

    print(f"\nKontingentbuch -- Stand {jetzt.astimezone(TZ).isoformat(timespec='seconds')}\n")
    print("-- je Zugang (geteilt ueber alle Konten) -------------------")
    for z in zugaenge:
        fenster = _fensteranfang(z, jetzt)
        if not fenster:
            gesamt = con.execute(
                "SELECT COALESCE(SUM(menge),0) s FROM kb_buchung WHERE zugang=?",
                (z["zugang"],)).fetchone()["s"]
            print(f"  {z['zugang']:<14} kein hartes Limit im Katalog "
                  f"-- gesamt gebucht (alle Zeit): {gesamt:g} {z['einheit'] or ''}")
            continue
        for name, (beginn, limit) in fenster.items():
            verbraucht = _verbraucht_seit(con, None, z["zugang"], beginn)
            rest = max(0.0, limit - verbraucht)
            pct = (verbraucht / limit * 100) if limit else 0
            print(f"  {z['zugang']:<14} [{name}] seit {beginn.astimezone(TZ):%H:%M} "
                  f"Wien: {verbraucht:g}/{limit:g} {z['einheit'] or ''} "
                  f"({pct:.0f}%) -- Rest {rest:g}")

    print("\n-- je Konto -------------------------------------------------")
    konten = con.execute(
        "SELECT * FROM kb_konto" + (" WHERE konto=?" if a.konto else "")
        + " ORDER BY vorrang, konto", (a.konto,) if a.konto else ()).fetchall()
    for k in konten:
        letzte = con.execute("""
            SELECT zeit, zugang, menge, einheit FROM kb_buchung
            WHERE konto=? ORDER BY zeit DESC LIMIT 1
        """, (k["konto"],)).fetchone()
        gesamt24h = con.execute("""
            SELECT COALESCE(SUM(menge),0) s FROM kb_buchung
            WHERE konto=? AND zeit >= ?
        """, (k["konto"], (jetzt - timedelta(hours=24)).isoformat())).fetchone()["s"]
        limit_txt = "keins (nur Warnung als Bremse)" if not k["hat_eigenes_limit"] \
            else (f"{k['eigenes_limit_wert']} {k['eigenes_limit_einheit'] or ''}"
                  if k["eigenes_limit_wert"] is not None
                  else "vorgesehen, Phase B steht noch aus")
        print(f"  {k['konto']:<18} Vorrang {k['vorrang']}  eigenes Limit: {limit_txt}")
        print(f"      24h gebucht (alle Zugaenge): {gesamt24h:g}")
        if letzte:
            print(f"      letzte Buchung: {letzte['zeit']}  "
                  f"{letzte['zugang']} {letzte['menge']:g} {letzte['einheit'] or ''}")
        else:
            print(f"      letzte Buchung: keine")
    print()


# --------------------------------------------------------------- warnung --

def cmd_warnung(a) -> None:
    con = connect_db()
    ensure_schema(con)
    jetzt = datetime.now(timezone.utc)
    ausgeloest = []

    paare = con.execute("""
        SELECT DISTINCT konto, zugang FROM kb_buchung
        WHERE zeit >= ?
    """, ((jetzt - timedelta(days=WARN_LOOKBACK_TAGE)).isoformat(),)).fetchall()

    for p in paare:
        konto, zugang = p["konto"], p["zugang"]
        if a.konto and konto != a.konto:
            continue
        if a.zugang and zugang != a.zugang:
            continue
        zrow = con.execute("SELECT * FROM kb_zugang WHERE zugang=?",
                            (zugang,)).fetchone()
        krow = con.execute("SELECT * FROM kb_konto WHERE konto=?",
                            (konto,)).fetchone()

        # 1) ueber_norm: aktuelles Fenster (letzte Stunde) vs. eigenes
        #    Mittel zur gleichen Stunde, über die letzten WARN_LOOKBACK_TAGE.
        w = _pruefe_ueber_norm(con, konto, zugang, jetzt)
        if w:
            ausgeloest.append(_verzeichne(con, jetzt, konto, zugang,
                                          "ueber_norm", w))

        # 2) reset_naehert_sich: Verbrauchsrate im laufenden Fenster
        #    projiziert das Limit vor dem Reset leer.
        if zrow:
            w = _pruefe_reset_naeher(con, konto, zrow, jetzt)
            if w:
                ausgeloest.append(_verzeichne(con, jetzt, konto, zugang,
                                              "reset_naehert_sich", w))

        # 3) verbrauch_ohne_fortschritt: der wichtigste. Braucht wirt-Bruecke.
        if krow and krow["wirt"]:
            w = _pruefe_ohne_fortschritt(con, konto, zugang, krow["wirt"], jetzt)
            if w:
                ausgeloest.append(_verzeichne(con, jetzt, konto, zugang,
                                              "verbrauch_ohne_fortschritt", w))
        elif a.zeigen_luecken:
            print(f"  (uebersprungen: {konto} hat keinen wirt in kb_konto "
                  f"-- Fortschritts-Check nicht moeglich)")

    # 4) mehrdeutiger Schluessel -- kein Verbrauchs-, sondern Herkunftsbefund.
    for z in con.execute("SELECT * FROM kb_zugang WHERE mehrdeutiger_schluessel=1"):
        offen = con.execute("""
            SELECT count(*) c FROM kb_buchung
            WHERE zugang=? AND schluessel_hinweis IS NULL
              AND zeit >= ?
        """, (z["zugang"], (jetzt - timedelta(days=WARN_LOOKBACK_TAGE)).isoformat())
        ).fetchone()["c"]
        if offen:
            text = (f"{z['zugang']}: {offen} Buchung(en) ohne "
                    f"schluessel_hinweis, obwohl der Tresor mehrere "
                    f"Kandidaten fuer diesen Zugang haelt -- welcher "
                    f"Schluessel wirklich verbraucht hat, ist unbekannt.")
            ausgeloest.append(_verzeichne(con, jetzt, None, z["zugang"],
                                          "mehrdeutiger_schluessel",
                                          {"text": text, "offene_buchungen": offen}))

    if not ausgeloest:
        print("keine Warnung -- alles im eigenen Normalbereich "
              f"(geprueft: {len(paare)} Konto/Zugang-Paare mit Buchungen)")
        return
    for w in ausgeloest:
        print(f"  ⚠ [{w['art']}] {w['konto'] or '-'} x {w['zugang'] or '-'}: "
              f"{w['text']}")


def _pruefe_ueber_norm(con, konto, zugang, jetzt) -> dict | None:
    letzte_stunde = jetzt - timedelta(hours=1)
    aktuell = _verbraucht_seit(con, konto, zugang, letzte_stunde)
    seit = jetzt - timedelta(days=WARN_LOOKBACK_TAGE)
    stunde = jetzt.astimezone(TZ).hour
    rows = con.execute("""
        SELECT zeit, menge FROM kb_buchung
        WHERE konto=? AND zugang=? AND zeit >= ? AND zeit < ?
    """, (konto, zugang, seit.isoformat(), letzte_stunde.isoformat())).fetchall()
    werte = [r["menge"] for r in rows
             if parse_zeit(r["zeit"]).astimezone(TZ).hour == stunde]
    if len(werte) < NORM_MIN_SAMPLES:
        return None
    mittel = statistics.mean(werte)
    sigma = statistics.pstdev(werte) if len(werte) > 1 else 0.0
    schwelle = mittel + WARN_Z * sigma if sigma > 0 else mittel * 3
    if aktuell > schwelle and aktuell > 0:
        return {
            "text": (f"letzte Stunde {aktuell:g} verbraucht, eigenes Mittel "
                     f"zur {stunde}-Uhr-Stunde ist {mittel:.1f} "
                     f"(sigma={sigma:.1f}, n={len(werte)}) -- {aktuell/mittel:.1f}x."),
            "aktuell": aktuell, "mittel": mittel, "sigma": sigma, "n": len(werte)}
    return None


def _pruefe_reset_naeher(con, konto, zrow, jetzt) -> dict | None:
    fenster = _fensteranfang(zrow, jetzt)
    for name, (beginn, limit) in fenster.items():
        verbraucht = _verbraucht_seit(con, konto, zrow["zugang"], beginn)
        dauer_bisher = (jetzt - beginn).total_seconds()
        if dauer_bisher <= 0 or verbraucht <= 0:
            continue
        if name == "fenster":
            dauer_gesamt = zrow["fenster_dauer_sekunden"]
        elif name == "minute":
            dauer_gesamt = 60
        elif name == "tag":
            dauer_gesamt = 86400
        elif name == "woche":
            dauer_gesamt = 7 * 86400
        else:
            continue
        rate = verbraucht / dauer_bisher
        projiziert = rate * dauer_gesamt
        if projiziert > limit:
            return {
                "text": (f"[{name}] bei aktueller Rate ({rate*3600:.1f}/h) "
                         f"waere das Fenster bei {projiziert:.0f} "
                         f"(Limit {limit:g}) -- leer VOR dem Reset."),
                "fenster": name, "rate_pro_stunde": rate * 3600,
                "projiziert": projiziert, "limit": limit}
    return None


def _pruefe_ohne_fortschritt(con, konto, zugang, wirt, jetzt) -> dict | None:
    """DIE wichtigste Warnung: viele Token, nichts bewegt sich. Signal:
    `taetigkeit` (26.446 Werkzeugaufrufe MIT Ergebnis, gemessen -- siehe
    Bericht). Fortschritt = Anteil ergebnis='ok' an allen Werkzeugaufrufen
    dieses wirt im Fenster, verglichen mit dem EIGENEN Mittel des wirt zur
    gleichen Stunde. Konsum steigt UND Erfolgsquote faellt deutlich unter
    das eigene Muster -> Verdacht auf Leerlauf (das Muster von 82
    Kontext-Ueberlaeufen in 89 Minuten)."""
    fenster_min = 60
    beginn = jetzt - timedelta(minutes=fenster_min)
    verbrauch_jetzt = _verbraucht_seit(con, konto, zugang, beginn)
    if verbrauch_jetzt <= 0:
        return None

    def _erfolgsquote(von: datetime, bis: datetime) -> tuple[float, int]:
        rows = con.execute("""
            SELECT ergebnis FROM taetigkeit
            WHERE wirt=? AND zeit >= ? AND zeit < ?
        """, (wirt, von.isoformat(), bis.isoformat())).fetchall()
        if not rows:
            return -1.0, 0
        ok = sum(1 for r in rows if r["ergebnis"] == "ok")
        return ok / len(rows), len(rows)

    quote_jetzt, n_jetzt = _erfolgsquote(beginn, jetzt)
    if n_jetzt == 0:
        return None  # keine taetigkeit-Zeilen im Fenster -- kein Urteil moeglich

    seit = jetzt - timedelta(days=WARN_LOOKBACK_TAGE)
    stunde = jetzt.astimezone(TZ).hour
    quoten = []
    cur = seit
    while cur < beginn:
        naechst = cur + timedelta(minutes=fenster_min)
        if cur.astimezone(TZ).hour == stunde:
            q, n = _erfolgsquote(cur, naechst)
            if n >= 3:
                quoten.append(q)
        cur = naechst
    if len(quoten) < NORM_MIN_SAMPLES:
        return None

    eigenes_mittel = statistics.mean(quoten)
    if eigenes_mittel <= 0:
        return None
    verbrauch_mittel, n_verbrauch = _stundenmittel(con, konto, zugang, jetzt)
    verbrauch_ueber_norm = (verbrauch_jetzt > verbrauch_mittel * 1.5
                             if n_verbrauch >= NORM_MIN_SAMPLES else True)
    quote_eingebrochen = quote_jetzt < eigenes_mittel * 0.5

    if verbrauch_ueber_norm and quote_eingebrochen:
        return {
            "text": (f"letzte {fenster_min}min: {verbrauch_jetzt:g} verbraucht "
                     f"bei {wirt}, aber nur {quote_jetzt:.0%} der "
                     f"{n_jetzt} Werkzeugaufrufe erfolgreich (eigenes Mittel "
                     f"zur {stunde}-Uhr-Stunde: {eigenes_mittel:.0%}, "
                     f"n={len(quoten)} Fenster). Verbrauch ohne Fortschritt."),
            "verbrauch": verbrauch_jetzt, "erfolgsquote_jetzt": quote_jetzt,
            "erfolgsquote_mittel": eigenes_mittel, "n_aufrufe": n_jetzt}
    return None


def _verzeichne(con, jetzt, konto, zugang, art, daten: dict) -> dict:
    text = daten.pop("text")
    con.execute("""
        INSERT INTO kb_warnung (zeit, konto, zugang, art, text, kennzahlen_json)
        VALUES (?,?,?,?,?,?)
    """, (jetzt.isoformat(), konto, zugang, art, text,
          json.dumps(daten, ensure_ascii=False, default=str)))
    con.commit()
    return {"konto": konto, "zugang": zugang, "art": art, "text": text}


# ------------------------------------------------------------------- main -

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    u = p.add_subparsers(dest="befehl", required=True)

    s = u.add_parser("init", help="Katalog anlegen/aktualisieren (idempotent)")
    s.set_defaults(fn=cmd_init)

    s = u.add_parser("katalog", help="Katalog anzeigen")
    s.set_defaults(fn=cmd_katalog)

    s = u.add_parser("buchen", help="einen Verbrauch verzeichnen")
    s.add_argument("--konto", required=True)
    s.add_argument("--zugang", required=True)
    s.add_argument("--menge", required=True, type=float)
    s.add_argument("--einheit", default=None)
    s.add_argument("--zweck", default=None)
    s.add_argument("--batch-id", dest="batch_id", default=None)
    s.add_argument("--taetigkeit-id", dest="taetigkeit_id", type=int, default=None)
    s.add_argument("--schluessel-hinweis", dest="schluessel_hinweis", default=None,
                   help="welcher Tresor-Kandidat verwendet wurde, bei "
                        "mehrdeutigen Zugaengen (frei, wird nicht geprueft)")
    s.add_argument("--quelle", default="buchen", choices=("buchen", "synthetic"))
    s.add_argument("--zeit", default=None, help="ISO8601, sonst jetzt (UTC)")
    s.add_argument("--dedupe-key", dest="dedupe_key", default=None,
                   help="wiederholte Buchung mit gleichem Schluessel wird "
                        "uebersprungen statt doppelt gezaehlt")
    s.set_defaults(fn=cmd_buchen)

    s = u.add_parser("stand", help="Stand je Zugang und je Konto")
    s.add_argument("--konto", default=None)
    s.add_argument("--zugang", default=None)
    s.set_defaults(fn=cmd_stand)

    s = u.add_parser("darf", help="darf ein Batch der Groesse N jetzt laufen")
    s.add_argument("--konto", required=True)
    s.add_argument("--zugang", required=True)
    s.add_argument("--menge", required=True, type=float,
                   help="gewuenschte Batch-Groesse (angefragte Einheiten)")
    s.add_argument("--zeit", default=None, help="ISO8601, sonst jetzt (UTC) "
                   "-- fuer reproduzierbare Tests")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_darf)

    s = u.add_parser("warnung", help="was gerade vom eigenen Normalzustand abweicht")
    s.add_argument("--konto", default=None)
    s.add_argument("--zugang", default=None)
    s.add_argument("--zeigen-luecken", dest="zeigen_luecken", action="store_true",
                   help="auch Konto/Zugang-Paare nennen, die uebersprungen "
                        "wurden (z.B. weil kein wirt hinterlegt ist)")
    s.set_defaults(fn=cmd_warnung)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
