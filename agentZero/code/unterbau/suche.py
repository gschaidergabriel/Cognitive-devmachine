#!/usr/bin/env python3
"""suche.py — Wortsuche + Themen-Nachbarschaft ueber den ClayVerse-Wiki-Bestand.

Gemeinsame Datenbank mit anderen Werkzeugen: /var/lib/clay/wiki.db
  Fremde Tabellen (nicht meins, NIE DROP/CREATE/DELETE):
      artikel, kante            (Wiki-Werkzeug)
      anreicherung, kuration    (drittes Werkzeug)
      graph_knoten, graph_kante (viertes Werkzeug)
  Eigene Tabellen (kollisionsfrei, ich baue/droppe nur diese):
      datei              EIN Eintrag pro EINDEUTIGEM Dateiinhalt (Pruefsumme),
                          haelt den Volltext genau EINMAL.
      fundort            EIN Eintrag pro (wirt, pfad) -- jeder Fundort, an dem
                          ein Dateiinhalt liegt. Kein Fundort geht verloren,
                          nur der Inhalt wird nicht mehrfach gespeichert.
      artikel_suchtext   Durchsuchbare Kopie der artikel-Metadaten (521 kleine
                          Zeilen, keine Dedup noetig).
      fts_index_datei    FTS5 ueber datei.text (external content).
      fts_index_artikel  FTS5 ueber artikel_suchtext.text (external content).

Dedup-Regel (Vorgabe des Eigentuemers, 2026-08-15): ein Fund pro INHALT, nie
pro PFAD -- gemessen 51 % Dopplung (693,5 MB gespeicherter Text vs. 356,4 MB
bei eindeutigen Pruefsummen), v.a. durch /srv/sicherung/alt-vps (Backup-
Spiegel) und die doppelten Repo-Klone unter baeume/ vs. klone/. Der Backup
wird NICHT ausgeschlossen -- nur dedupliziert. Was NUR im Backup existiert,
bleibt erhalten (eigener Fundort-Eintrag, geteilter Inhalt).

Kein Modellaufruf. Kein Embedding. Reine Wort-/BM25-Suche via SQLite FTS5
plus Graph-Nachbarschaft ueber `kante`. Diese Schicht kostet 0 Token.

Nebenlaeufigkeit: WAL ist PFLICHT (mehrere Werkzeuge schreiben in dieselbe
Datei, gerade jetzt: eines ALTERt `artikel` und fuegt tausende Zeilen ein,
eines legt graph_knoten/graph_kante an). busy_timeout ist gesetzt, zusaetzlich
retryt jede eigene Schreibung UND Lesung fremder Tabellen mit Backoff. Bei
"database is locked" wird NIE ein Fehler verschluckt und NIE eine Zeile
stillschweigend ausgelassen -- nach Ausschoepfen der Versuche bricht der Lauf
mit einer klaren Fehlermeldung ab.

Blasen-Filter (Vorgabe des Eigentuemers, 2026-08-15):
  Fuer die Konten gabriel / andreas / clayverse (= KERN_KONTEN) gilt KEINE
  Bereichsbeschraenkung. Fuer jedes andere Konto gilt: nur eigene Blase +
  blasenlose (= Kern-)Zeilen. Der Filter sitzt IM WHERE der Suchabfrage
  (EXISTS gegen fundort.blase), nicht als Nachbearbeitung der Trefferliste.
  Ein Inhalt, dessen Fundorte AUSSCHLIESSLICH fremder Blase gehoeren, taucht
  gar nicht erst in der Trefferliste auf.

    suche.py index                               Neu indizieren (voller Rebuild)
    suche.py suche <wort> [--blase B] [--wirt W] [--limit N] [--json]
    suche.py thema <artikel_id> [--json]          Kombinierte Themen-Abfrage
    suche.py stand                                Kennzahlen des aktuellen Index
    suche.py selbsttest                           Blasen-Filter gegen Kanarienzeilen pruefen
    suche.py importieren <manifest.db>            sammeln.py-Manifest idempotent einhaengen
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import sys
import time
from pathlib import Path

WIKI_DB = Path("/var/lib/clay/wiki.db")
WIKI_DIR = Path("/var/lib/clay/wiki")
WIRT = "clayverse"
SCOPE = [Path("/opt/clayverse"), Path("/var/lib/clay"), Path("/srv")]

AUSSCHLUSS_PRAEFIXE = [
    WIKI_DB.with_name(WIKI_DB.name + suf) for suf in ("", "-journal", "-wal", "-shm")
]

KERN_KONTEN = {"gabriel", "andreas", "clayverse", "kern", None}

MAX_TEXT_BYTES = 3_000_000
BUSY_TIMEOUT_MS = 15_000
RETRY_BACKOFF = [0.2, 0.4, 0.8, 1.6, 3.2, 6.4, 12.8]
WIKI_POLL_TIMEOUT_S = 60
WIKI_POLL_SCHRITTE = [1, 2, 3, 5, 8, 13, 21]

TEXT_EXT = {
    ".py", ".md", ".markdown", ".txt", ".json", ".jsonl", ".yaml", ".yml",
    ".sh", ".bash", ".cfg", ".conf", ".ini", ".html", ".htm", ".css",
    ".js", ".ts", ".tsx", ".jsx", ".toml", ".csv", ".log", ".rst", ".xml",
    ".service", ".env", ".gitignore", ".sql", ".ps1",
}
TEXT_NAMEN = {"dockerfile", "makefile", "liesmich", "readme", "changelog"}


class SperreErschoepft(RuntimeError):
    pass


def _jetzt() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _verbindung() -> sqlite3.Connection:
    WIKI_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(WIKI_DB), timeout=BUSY_TIMEOUT_MS / 1000)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
    return con


def _mit_retry(fn, *a, **kw):
    letzter = None
    for pause in RETRY_BACKOFF:
        try:
            return fn(*a, **kw)
        except sqlite3.OperationalError as e:
            if "locked" not in str(e).lower() and "busy" not in str(e).lower():
                raise
            letzter = e
            time.sleep(pause)
    try:
        return fn(*a, **kw)
    except sqlite3.OperationalError as e:
        raise SperreErschoepft(
            f"Datenbank blieb nach {len(RETRY_BACKOFF)} Wiederholungen gesperrt: {e}"
        ) from (letzter or e)


def _wiki_bereit(con: sqlite3.Connection) -> tuple[bool, float]:
    t0 = time.time()
    for pause in WIKI_POLL_SCHRITTE:
        vorhanden = {
            r[0] for r in _mit_retry(lambda: con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name IN ('artikel','kante')"
            ).fetchall())
        }
        if {"artikel", "kante"} <= vorhanden:
            return True, time.time() - t0
        if time.time() - t0 + pause > WIKI_POLL_TIMEOUT_S:
            break
        time.sleep(pause)
    vorhanden = {
        r[0] for r in _mit_retry(lambda: con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name IN ('artikel','kante')"
        ).fetchall())
    }
    return ({"artikel", "kante"} <= vorhanden), time.time() - t0


def _fts5_verfuegbar(con: sqlite3.Connection) -> bool:
    try:
        con.execute("CREATE VIRTUAL TABLE _fts5probe USING fts5(x)")
        con.execute("DROP TABLE _fts5probe")
        return True
    except sqlite3.OperationalError:
        return False


def _eigenes_schema(con: sqlite3.Connection, fts5: bool) -> None:
    """Legt NUR die eigenen Tabellen neu an (datei, fundort, artikel_suchtext,
    fts_index_datei, fts_index_artikel). Fasst artikel/kante/anreicherung/
    kuration/graph_* nie an."""
    def _tun():
        con.executescript(
            """
            -- Altlast aus der VORHERIGEN Schemaversion dieses Werkzeugs
            -- (fts_dokument/fts_index, vor der Pruefsummen-Dedup-Umstellung).
            -- Eigene Tabellen aus einem frueheren eigenen Lauf, sicher zu
            -- droppen. Wurden beim Umbau vergessen -- 995 MB toter Rest lag
            -- deshalb neben dem neuen Schema, gefunden per dbstat-Messung.
            DROP TABLE IF EXISTS fts_index;
            DROP TABLE IF EXISTS fts_dokument;

            DROP TABLE IF EXISTS fts_index_datei;
            DROP TABLE IF EXISTS fts_index_artikel;
            DROP TABLE IF EXISTS fundort;
            DROP TABLE IF EXISTS datei;
            DROP TABLE IF EXISTS artikel_suchtext;

            -- Ein Eintrag pro EINDEUTIGEM Inhalt (Pruefsumme). Text nur einmal.
            CREATE TABLE datei (
                id INTEGER PRIMARY KEY,
                pruefsumme TEXT NOT NULL UNIQUE,
                titel TEXT,                 -- Dateiname des ERSTEN gesehenen Fundorts (nur Anzeige)
                art TEXT NOT NULL,          -- 'text' | 'binaer'
                volltext_indiziert INTEGER NOT NULL DEFAULT 0,
                groesse INTEGER,
                text TEXT,                  -- Volltext, EINMAL gespeichert
                indiziert TEXT NOT NULL
            );

            -- Jeder Fundort eines Inhalts. Kein Fundort geht verloren.
            CREATE TABLE fundort (
                datei_id INTEGER NOT NULL,  -- FK auf datei.id (robuster Join)
                pruefsumme TEXT NOT NULL,   -- wie vom Eigentuemer verlangt, zur Anzeige/Direktabfrage
                wirt TEXT NOT NULL,
                pfad TEXT NOT NULL,
                blase TEXT,                 -- NULL = Kern/unbeschraenkt
                geaendert TEXT,
                PRIMARY KEY (wirt, pfad)
            );
            CREATE INDEX idx_fundort_datei ON fundort(datei_id);
            CREATE INDEX idx_fundort_pruefsumme ON fundort(pruefsumme);
            CREATE INDEX idx_fundort_blase ON fundort(blase);

            -- Artikel-Metadaten durchsuchbar (klein, 521 Zeilen, keine Dedup noetig).
            CREATE TABLE artikel_suchtext (
                id INTEGER PRIMARY KEY,
                artikel_id TEXT NOT NULL UNIQUE,
                titel TEXT,
                text TEXT,
                blase TEXT,
                indiziert TEXT NOT NULL
            );
            """
        )
        con.commit()
    _mit_retry(_tun)

    def _fts_tun():
        if fts5:
            con.execute(
                "CREATE VIRTUAL TABLE fts_index_datei USING fts5("
                "titel, text, content='datei', content_rowid='id')"
            )
            con.execute(
                "CREATE VIRTUAL TABLE fts_index_artikel USING fts5("
                "titel, text, content='artikel_suchtext', content_rowid='id')"
            )
        else:
            con.execute(
                "CREATE TABLE fts_index_datei (id INTEGER PRIMARY KEY, titel TEXT, text TEXT)"
            )
            con.execute(
                "CREATE TABLE fts_index_artikel (id INTEGER PRIMARY KEY, titel TEXT, text TEXT)"
            )
        con.commit()
    _mit_retry(_fts_tun)


def _ist_text(pfad: Path) -> bool:
    if pfad.suffix.lower() in TEXT_EXT:
        return True
    return pfad.name.lower() in TEXT_NAMEN


def _sha256(pfad: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with open(pfad, "rb") as f:
            while True:
                stueck = f.read(1 << 20)
                if not stueck:
                    break
                h.update(stueck)
        return h.hexdigest()
    except OSError:
        return None


def _lies_text(pfad: Path, groesse: int) -> str | None:
    if groesse > MAX_TEXT_BYTES:
        return None
    try:
        with open(pfad, "rb") as f:
            roh = f.read(MAX_TEXT_BYTES + 1)
        return roh.decode("utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def _ausgeschlossen(pfad: Path) -> bool:
    for praefix in AUSSCHLUSS_PRAEFIXE:
        try:
            pfad.relative_to(praefix)
            return True
        except ValueError:
            continue
    return False


def _index_artikel(con: sqlite3.Connection, fts5: bool) -> dict:
    ergebnis = {"artikel": 0}
    zeilen = _mit_retry(lambda: con.execute(
        "SELECT id, art, titel, quelle, quell_hash, datum, metadaten, "
        "offene_fragen, belegt, erzeugt_am FROM artikel"
    ).fetchall())
    puffer = 0
    for (aid, art_typ, titel, quelle, quell_hash, datum, metadaten,
         offene_fragen, belegt, erzeugt_am) in zeilen:
        text_teile = [titel or "", art_typ or "", metadaten or "", offene_fragen or ""]
        text = "\n".join(t for t in text_teile if t)

        def _tun(aid=aid, titel=titel, text=text):
            cur = con.execute(
                "INSERT INTO artikel_suchtext (artikel_id, titel, text, blase, indiziert) "
                "VALUES (?,?,?,?,?)",
                (aid, titel, text, None, _jetzt()),
            )
            rid = cur.lastrowid
            if fts5:
                con.execute(
                    "INSERT INTO fts_index_artikel (rowid, titel, text) VALUES (?,?,?)",
                    (rid, titel or "", text),
                )
            else:
                con.execute(
                    "INSERT INTO fts_index_artikel (id, titel, text) VALUES (?,?,?)",
                    (rid, titel or "", text),
                )
        _mit_retry(_tun)
        ergebnis["artikel"] += 1
        puffer += 1
        if puffer >= 500:
            _mit_retry(con.commit)
            puffer = 0
    _mit_retry(con.commit)
    return ergebnis


def _index_dateien(con: sqlite3.Connection, fts5: bool) -> dict:
    """Ein Durchlauf: haelt den Volltext je EINDEUTIGER Pruefsumme im Speicher
    (max. ~360 MB nach Messung -- passt), sammelt JEDEN Fundort einzeln.
    Am Ende: ein INSERT pro eindeutigem Inhalt, ein INSERT pro Fundort."""
    ergebnis = {"dateien": 0, "text": 0, "binaer": 0, "volltext": 0,
                "uebersprungen_zu_gross": 0, "hash_fehlgeschlagen": 0}
    inhalte: dict[str, dict] = {}   # pruefsumme_oder_ersatz -> {titel,art,groesse,text,volltext_ind}
    fundorte: list[tuple[str, str, str, str]] = []  # (schluessel, wirt, pfad, geaendert)

    for wurzel in SCOPE:
        if not wurzel.exists():
            continue
        for dirpfad, unterordner, dateien in os.walk(wurzel):
            dp = Path(dirpfad)
            if _ausgeschlossen(dp):
                unterordner[:] = []
                continue
            for name in dateien:
                pfad = dp / name
                if _ausgeschlossen(pfad):
                    continue
                try:
                    st = pfad.stat()
                except OSError:
                    continue
                groesse = st.st_size
                pruefsumme = _sha256(pfad)
                if pruefsumme is None:
                    # Hash fehlgeschlagen (z.B. kaputter Symlink, Rechte):
                    # eigener, garantiert eindeutiger Ersatzschluessel -- NIE
                    # unter NULL zusammenfassen, sonst wuerden unabhaengige
                    # Dateien faelschlich als "derselbe Inhalt" gelten.
                    schluessel = f"FEHLT:{WIRT}:{pfad}"
                    ergebnis["hash_fehlgeschlagen"] += 1
                else:
                    schluessel = pruefsumme

                geaendert = time.strftime(
                    "%Y-%m-%dT%H:%M:%S%z", time.localtime(st.st_mtime)
                )
                fundorte.append((schluessel, WIRT, str(pfad), geaendert))

                if schluessel not in inhalte:
                    text_art = _ist_text(pfad)
                    text = _lies_text(pfad, groesse) if text_art else None
                    if text_art and text is None and groesse > MAX_TEXT_BYTES:
                        ergebnis["uebersprungen_zu_gross"] += 1
                    art = "text" if text_art else "binaer"
                    inhalte[schluessel] = {
                        "titel": pfad.name, "art": art, "groesse": groesse,
                        "text": text, "volltext_ind": text is not None,
                    }

                ergebnis["dateien"] += 1

    # Inhalte einfuegen (ein Durchgang, batched commits)
    id_je_schluessel: dict[str, int] = {}
    puffer = 0
    for schluessel, daten in inhalte.items():
        def _tun(schluessel=schluessel, daten=daten):
            cur = con.execute(
                "INSERT INTO datei (pruefsumme, titel, art, volltext_indiziert, "
                "groesse, text, indiziert) VALUES (?,?,?,?,?,?,?)",
                (schluessel, daten["titel"], daten["art"], int(daten["volltext_ind"]),
                 daten["groesse"], daten["text"], _jetzt()),
            )
            rid = cur.lastrowid
            if daten["text"] is not None:
                if fts5:
                    con.execute(
                        "INSERT INTO fts_index_datei (rowid, titel, text) VALUES (?,?,?)",
                        (rid, daten["titel"] or "", daten["text"]),
                    )
                else:
                    con.execute(
                        "INSERT INTO fts_index_datei (id, titel, text) VALUES (?,?,?)",
                        (rid, daten["titel"] or "", daten["text"]),
                    )
            return rid
        rid = _mit_retry(_tun)
        id_je_schluessel[schluessel] = rid
        ergebnis[daten["art"]] += 1
        if daten["volltext_ind"]:
            ergebnis["volltext"] += 1
        puffer += 1
        if puffer >= 500:
            _mit_retry(con.commit)
            puffer = 0
    _mit_retry(con.commit)

    # Fundorte einfuegen (JEDER Pfad, referenziert den gemeinsamen Inhalt)
    puffer = 0
    for schluessel, wirt, pfad, geaendert in fundorte:
        rid = id_je_schluessel[schluessel]
        pruefsumme_anzeige = schluessel if not schluessel.startswith("FEHLT:") else None

        def _tun(rid=rid, pruefsumme_anzeige=pruefsumme_anzeige, wirt=wirt,
                  pfad=pfad, geaendert=geaendert):
            con.execute(
                "INSERT INTO fundort (datei_id, pruefsumme, wirt, pfad, blase, geaendert) "
                "VALUES (?,?,?,?,?,?)",
                (rid, pruefsumme_anzeige, wirt, pfad, None, geaendert),
            )
        _mit_retry(_tun)
        puffer += 1
        if puffer >= 1000:
            _mit_retry(con.commit)
            puffer = 0
    _mit_retry(con.commit)

    ergebnis["inhalte_eindeutig"] = len(inhalte)
    ergebnis["fundorte"] = len(fundorte)
    return ergebnis


def cmd_index(_args: list[str]) -> int:
    t0 = time.time()
    con = _verbindung()
    fts5 = _fts5_verfuegbar(con)

    wiki_bereit, gewartet = _wiki_bereit(con)
    _eigenes_schema(con, fts5)

    artikel_erg = _index_artikel(con, fts5) if wiki_bereit else {"artikel": 0}
    datei_erg = _index_dateien(con, fts5)

    def _idx():
        con.execute("CREATE INDEX IF NOT EXISTS idx_asuchtext_blase ON artikel_suchtext(blase)")
        con.commit()
    _mit_retry(_idx)
    con.close()

    dauer = time.time() - t0
    groesse_mb = WIKI_DB.stat().st_size / (1024 * 1024) if WIKI_DB.exists() else 0.0

    print(f"fts5={fts5}")
    print(f"wiki_db={WIKI_DB}")
    print(f"artikel_kante_tabellen_bereit={wiki_bereit} gewartet_s={gewartet:.1f}")
    print(f"artikel: indiziert={artikel_erg['artikel']}")
    print(f"dateien: fundorte_gesamt={datei_erg['fundorte']} "
          f"inhalte_eindeutig={datei_erg['inhalte_eindeutig']} "
          f"text={datei_erg['text']} binaer={datei_erg['binaer']} "
          f"volltext_indiziert={datei_erg['volltext']} "
          f"zu_gross_uebersprungen={datei_erg['uebersprungen_zu_gross']} "
          f"hash_fehlgeschlagen={datei_erg['hash_fehlgeschlagen']}")
    print(f"db_groesse_mb={groesse_mb:.2f}")
    print(f"laufzeit_s={dauer:.2f}")
    return 0


def _blase_wo(spalte: str, blase: str | None) -> tuple[str, tuple]:
    if blase in KERN_KONTEN:
        return "1=1", ()
    return f"({spalte} IS NULL OR {spalte} = ?)", (blase,)


def _tabelle_existiert(con: sqlite3.Connection, name: str) -> bool:
    return _mit_retry(lambda: con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()) is not None


def _fk_spalte_raten(con: sqlite3.Connection, tabelle: str) -> str | None:
    spalten = [r[1] for r in _mit_retry(lambda: con.execute(
        f"PRAGMA table_info({tabelle})").fetchall())]
    treffer = [s for s in spalten if "artikel" in s.lower()]
    return treffer[0] if len(treffer) == 1 else None


def _nachbarschaft(con: sqlite3.Connection, artikel_id: str) -> dict:
    t0 = time.time()
    ergebnis = {"artikel_id": artikel_id, "artikel": None, "kanten": [],
                "anreicherung": {"verfuegbar": False, "eintraege": []},
                "kuration": {"verfuegbar": False, "eintraege": []}}

    row = _mit_retry(lambda: con.execute(
        "SELECT id, art, titel, quelle, quell_hash, datum, metadaten, "
        "offene_fragen, belegt, erzeugt_am FROM artikel WHERE id = ?",
        (artikel_id,),
    ).fetchone())
    if row:
        felder = ["id", "art", "titel", "quelle", "quell_hash", "datum",
                   "metadaten", "offene_fragen", "belegt", "erzeugt_am"]
        ergebnis["artikel"] = dict(zip(felder, row))

    if _tabelle_existiert(con, "kante"):
        kanten = _mit_retry(lambda: con.execute(
            "SELECT von, nach, art, beleg FROM kante WHERE von = ? OR nach = ?",
            (artikel_id, artikel_id),
        ).fetchall())
        for von, nach, art_kante, beleg in kanten:
            andere_id = nach if von == artikel_id else von
            richtung = "ausgehend" if von == artikel_id else "eingehend"
            titel_zeile = _mit_retry(lambda andere_id=andere_id: con.execute(
                "SELECT titel FROM artikel WHERE id = ?", (andere_id,)
            ).fetchone())
            ergebnis["kanten"].append({
                "andere_id": andere_id,
                "andere_titel": titel_zeile[0] if titel_zeile else None,
                "richtung": richtung,
                "art": art_kante,
                "beleg": beleg,
            })

    for tabelle, key in (("anreicherung", "anreicherung"), ("kuration", "kuration")):
        if not _tabelle_existiert(con, tabelle):
            continue
        ergebnis[key]["verfuegbar"] = True
        fk = _fk_spalte_raten(con, tabelle)
        if fk is None:
            ergebnis[key]["hinweis"] = (
                f"Fremdschluessel-Spalte nicht eindeutig bestimmbar. "
                f"Schema: {[r[1] for r in con.execute(f'PRAGMA table_info({tabelle})').fetchall()]}"
            )
            continue
        spalten = [r[1] for r in _mit_retry(lambda tabelle=tabelle: con.execute(
            f"PRAGMA table_info({tabelle})").fetchall())]
        zeilen = _mit_retry(lambda tabelle=tabelle, fk=fk: con.execute(
            f"SELECT * FROM {tabelle} WHERE {fk} = ?", (artikel_id,)
        ).fetchall())
        ergebnis[key]["eintraege"] = [dict(zip(spalten, z)) for z in zeilen]
        ergebnis[key]["fk_spalte_geraten"] = fk

    ergebnis["dauer_ms"] = (time.time() - t0) * 1000
    return ergebnis


def cmd_thema(args: list[str]) -> int:
    if not args:
        print("Nutzung: suche.py thema <artikel_id> [--json]", file=sys.stderr)
        return 2
    artikel_id = args[0]
    als_json = "--json" in args[1:]
    con = _verbindung()
    bundle = _nachbarschaft(con, artikel_id)
    con.close()
    if als_json:
        print(json.dumps(bundle, ensure_ascii=False, indent=2))
    else:
        print(f"artikel_id={artikel_id} dauer_ms={bundle['dauer_ms']:.2f}")
        print(f"artikel_gefunden={bundle['artikel'] is not None}")
        print(f"kanten={len(bundle['kanten'])}")
        for k in bundle["kanten"]:
            print(f"  {k['richtung']} {k['art']} -> {k['andere_id']} ({k['andere_titel']})")
        print(f"anreicherung_verfuegbar={bundle['anreicherung']['verfuegbar']} "
              f"eintraege={len(bundle['anreicherung']['eintraege'])}")
        print(f"kuration_verfuegbar={bundle['kuration']['verfuegbar']} "
              f"eintraege={len(bundle['kuration']['eintraege'])}")
    return 0


def _suche_datei(con: sqlite3.Connection, fts5: bool, wort: str, blase: str | None,
                  wirt: str | None, limit: int) -> list[dict]:
    blase_sql, blase_params = _blase_wo("fo.blase", blase)
    if fts5:
        sql = (
            "SELECT d.id, d.pruefsumme, d.titel, bm25(fts_index_datei) AS rang "
            "FROM fts_index_datei, datei d "
            "WHERE d.id = fts_index_datei.rowid AND fts_index_datei MATCH ? "
            "AND EXISTS (SELECT 1 FROM fundort fo WHERE fo.datei_id = d.id AND " + blase_sql + ")"
        )
        params = [wort] + list(blase_params)
        if wirt:
            sql += (" AND EXISTS (SELECT 1 FROM fundort fo2 WHERE fo2.datei_id = d.id "
                     "AND fo2.wirt = ?)")
            params.append(wirt)
        sql += " ORDER BY rang LIMIT ?"
        params.append(limit)
    else:
        sql = (
            "SELECT d.id, d.pruefsumme, d.titel, 0 AS rang "
            "FROM fts_index_datei f JOIN datei d ON d.id = f.id "
            "WHERE (f.titel LIKE ? OR f.text LIKE ?) "
            "AND EXISTS (SELECT 1 FROM fundort fo WHERE fo.datei_id = d.id AND " + blase_sql + ")"
        )
        muster = f"%{wort}%"
        params = [muster, muster] + list(blase_params)
        if wirt:
            sql += (" AND EXISTS (SELECT 1 FROM fundort fo2 WHERE fo2.datei_id = d.id "
                     "AND fo2.wirt = ?)")
            params.append(wirt)
        sql += " LIMIT ?"
        params.append(limit)
    zeilen = _mit_retry(lambda: con.execute(sql, params).fetchall())

    treffer = []
    for (id_, pruefsumme, titel, rang) in zeilen:
        ort_sql = ("SELECT wirt, pfad, blase, geaendert FROM fundort WHERE datei_id = ? AND "
                   + blase_sql)
        orte = _mit_retry(lambda id_=id_, ort_sql=ort_sql: con.execute(
            ort_sql, [id_] + list(blase_params)).fetchall())
        treffer.append({
            "herkunft": "datei", "id": id_, "pruefsumme": pruefsumme, "titel": titel,
            "rang": rang,
            "fundorte": [{"wirt": w, "pfad": p, "blase": b, "geaendert": g}
                          for (w, p, b, g) in orte],
        })
    return treffer


def _suche_artikel(con: sqlite3.Connection, fts5: bool, wort: str, blase: str | None,
                    limit: int) -> list[dict]:
    blase_sql, blase_params = _blase_wo("a.blase", blase)
    if fts5:
        sql = (
            "SELECT a.id, a.artikel_id, a.titel, bm25(fts_index_artikel) AS rang "
            "FROM fts_index_artikel, artikel_suchtext a "
            "WHERE a.id = fts_index_artikel.rowid AND fts_index_artikel MATCH ? AND " + blase_sql
            + " ORDER BY rang LIMIT ?"
        )
        params = [wort] + list(blase_params) + [limit]
    else:
        sql = (
            "SELECT a.id, a.artikel_id, a.titel, 0 AS rang "
            "FROM fts_index_artikel f JOIN artikel_suchtext a ON a.id = f.id "
            "WHERE (f.titel LIKE ? OR f.text LIKE ?) AND " + blase_sql + " LIMIT ?"
        )
        muster = f"%{wort}%"
        params = [muster, muster] + list(blase_params) + [limit]
    zeilen = _mit_retry(lambda: con.execute(sql, params).fetchall())

    treffer = []
    for (id_, artikel_id, titel, rang) in zeilen:
        eintrag = {"herkunft": "artikel", "id": id_, "fremd_id": artikel_id,
                    "titel": titel, "rang": rang}
        eintrag["thema"] = _nachbarschaft(con, artikel_id)
        treffer.append(eintrag)
    return treffer


def cmd_suche(args: list[str]) -> int:
    if not args:
        print("Nutzung: suche.py suche <wort> [--blase B] [--wirt W] [--limit N] [--json]",
              file=sys.stderr)
        return 2
    wort = args[0]
    rest = args[1:]
    blase = None
    wirt = None
    limit = 20
    als_json = False
    i = 0
    while i < len(rest):
        if rest[i] == "--blase" and i + 1 < len(rest):
            blase = rest[i + 1]; i += 2
        elif rest[i] == "--wirt" and i + 1 < len(rest):
            wirt = rest[i + 1]; i += 2
        elif rest[i] == "--limit" and i + 1 < len(rest):
            limit = int(rest[i + 1]); i += 2
        elif rest[i] == "--json":
            als_json = True; i += 1
        else:
            i += 1

    con = _verbindung()
    fts5 = _fts5_verfuegbar(con)

    t0 = time.time()
    treffer = (_suche_datei(con, fts5, wort, blase, wirt, limit)
               + _suche_artikel(con, fts5, wort, blase, limit))
    treffer.sort(key=lambda e: e["rang"])
    treffer = treffer[:limit]
    dauer_ms = (time.time() - t0) * 1000
    con.close()

    if als_json:
        print(json.dumps({"wort": wort, "blase": blase, "dauer_ms": dauer_ms,
                           "treffer": treffer}, ensure_ascii=False, indent=2))
    else:
        print(f"wort={wort!r} blase={blase!r} dauer_ms={dauer_ms:.2f} treffer={len(treffer)}")
        for e in treffer:
            if e["herkunft"] == "datei":
                print(f"  [datei] {e['titel']} pruefsumme={e['pruefsumme'][:12] if e['pruefsumme'] else None}.. "
                      f"fundorte={len(e['fundorte'])}")
                for o in e["fundorte"][:3]:
                    print(f"      {o['pfad']} (blase={o['blase']})")
                if len(e["fundorte"]) > 3:
                    print(f"      ... +{len(e['fundorte'])-3} weitere Fundorte")
            else:
                print(f"  [artikel] {e['titel']} ({e['fremd_id']}) "
                      f"kanten={len(e['thema']['kanten'])} thema_ms={e['thema']['dauer_ms']:.2f}")
    return 0


def cmd_stand(_args: list[str]) -> int:
    if not WIKI_DB.exists():
        print("keine Datenbank vorhanden -- suche.py index zuerst ausfuehren")
        return 1
    con = _verbindung()
    if not _tabelle_existiert(con, "datei"):
        print("kein eigener Index vorhanden -- suche.py index zuerst ausfuehren")
        return 1
    inhalte = con.execute("SELECT COUNT(*) FROM datei").fetchone()[0]
    fundorte = con.execute("SELECT COUNT(*) FROM fundort").fetchone()[0]
    nach_art = con.execute(
        "SELECT art, COUNT(*), SUM(volltext_indiziert) FROM datei GROUP BY art"
    ).fetchall()
    artikel_such = con.execute("SELECT COUNT(*) FROM artikel_suchtext").fetchone()[0]
    mehrfach = con.execute(
        "SELECT COUNT(*) FROM (SELECT datei_id FROM fundort GROUP BY datei_id HAVING COUNT(*) > 1)"
    ).fetchone()[0]
    artikel_gesamt = con.execute("SELECT COUNT(*) FROM artikel").fetchone()[0] \
        if _tabelle_existiert(con, "artikel") else None
    kanten_gesamt = con.execute("SELECT COUNT(*) FROM kante").fetchone()[0] \
        if _tabelle_existiert(con, "kante") else None
    nach_wirt = con.execute(
        "SELECT wirt, COUNT(*) FROM fundort GROUP BY wirt"
    ).fetchall()
    mehr_als_1_wirt = con.execute(
        "SELECT COUNT(*) FROM (SELECT datei_id FROM fundort GROUP BY datei_id "
        "HAVING COUNT(DISTINCT wirt) > 1)"
    ).fetchone()[0]
    con.close()

    groesse_mb = WIKI_DB.stat().st_size / (1024 * 1024)
    print(f"datei_eindeutige_inhalte={inhalte}")
    print(f"fundort_gesamt={fundorte}")
    print(f"fundort_nach_wirt={dict(nach_wirt)}")
    print(f"inhalte_mit_mehr_als_1_fundort={mehrfach}")
    print(f"inhalte_auf_mehr_als_1_wirt={mehr_als_1_wirt}")
    print(f"nach_art={[(a, c, v) for a, c, v in nach_art]}")
    print(f"artikel_suchtext={artikel_such}")
    print(f"fremd_artikel_gesamt={artikel_gesamt} fremd_kanten_gesamt={kanten_gesamt}")
    print(f"db_groesse_mb={groesse_mb:.2f} (ganze wiki.db, gemeinsam genutzt)")
    return 0


def cmd_importieren(args: list[str]) -> int:
    """Haengt eine sammeln.py-Manifestdatei (funde+fundorte) idempotent in
    datei/fundort ein. INSERT-only-if-missing bei datei (UNIQUE pruefsumme),
    INSERT OR IGNORE bei fundort (PK wirt,pfad) -- doppeltes Importieren
    derselben Manifestdatei aendert beim zweiten Mal nichts (Beweis: einfach
    zweimal ausfuehren und die gemeldeten neu_* Zahlen vergleichen)."""
    if not args:
        print("Nutzung: suche.py importieren <manifest.db>", file=sys.stderr)
        return 2
    manifest_pfad = args[0]
    t0 = time.time()
    manifest = sqlite3.connect(manifest_pfad)
    con = _verbindung()
    fts5 = _fts5_verfuegbar(con)
    if not _tabelle_existiert(con, "datei"):
        print("kein eigener Index vorhanden -- suche.py index zuerst ausfuehren")
        return 1

    funde = manifest.execute(
        "SELECT pruefsumme, titel, art, volltext_indiziert, groesse, text FROM funde"
    ).fetchall()

    rid_je_pruefsumme: dict[str, int] = {}
    neu_inhalte = 0
    vorhanden_inhalte = 0
    puffer = 0
    for pruefsumme, titel, art, volltext_ind, groesse, text in funde:
        zeile = _mit_retry(lambda p=pruefsumme: con.execute(
            "SELECT id FROM datei WHERE pruefsumme = ?", (p,)).fetchone())
        if zeile:
            rid_je_pruefsumme[pruefsumme] = zeile[0]
            vorhanden_inhalte += 1
            continue

        def _tun(pruefsumme=pruefsumme, titel=titel, art=art, volltext_ind=volltext_ind,
                  groesse=groesse, text=text):
            cur = con.execute(
                "INSERT INTO datei (pruefsumme, titel, art, volltext_indiziert, "
                "groesse, text, indiziert) VALUES (?,?,?,?,?,?,?)",
                (pruefsumme, titel, art, volltext_ind, groesse, text, _jetzt()),
            )
            rid = cur.lastrowid
            if text is not None:
                if fts5:
                    con.execute(
                        "INSERT INTO fts_index_datei (rowid, titel, text) VALUES (?,?,?)",
                        (rid, titel or "", text),
                    )
                else:
                    con.execute(
                        "INSERT INTO fts_index_datei (id, titel, text) VALUES (?,?,?)",
                        (rid, titel or "", text),
                    )
            return rid
        rid = _mit_retry(_tun)
        rid_je_pruefsumme[pruefsumme] = rid
        neu_inhalte += 1
        puffer += 1
        if puffer >= 500:
            _mit_retry(con.commit); puffer = 0
    _mit_retry(con.commit)

    fundorte = manifest.execute(
        "SELECT pruefsumme, wirt, pfad, geaendert FROM fundorte"
    ).fetchall()
    neu_fundorte = 0
    uebersprungen_ohne_inhalt = 0
    puffer = 0
    for pruefsumme, wirt, pfad, geaendert in fundorte:
        rid = rid_je_pruefsumme.get(pruefsumme)
        if rid is None:
            uebersprungen_ohne_inhalt += 1
            continue

        def _tun(rid=rid, pruefsumme=pruefsumme, wirt=wirt, pfad=pfad, geaendert=geaendert):
            cur = con.execute(
                "INSERT OR IGNORE INTO fundort (datei_id, pruefsumme, wirt, pfad, "
                "blase, geaendert) VALUES (?,?,?,?,?,?)",
                (rid, pruefsumme, wirt, pfad, None, geaendert),
            )
            return cur.rowcount
        rc = _mit_retry(_tun)
        if rc:
            neu_fundorte += 1
        puffer += 1
        if puffer >= 1000:
            _mit_retry(con.commit); puffer = 0
    _mit_retry(con.commit)
    con.close()
    manifest.close()

    dauer = time.time() - t0
    print(f"manifest={manifest_pfad}")
    print(f"funde_gelesen={len(funde)} neu_inhalte={neu_inhalte} "
          f"bereits_vorhanden_inhalte={vorhanden_inhalte}")
    print(f"fundorte_gelesen={len(fundorte)} neu_fundorte={neu_fundorte} "
          f"uebersprungen_ohne_inhalt={uebersprungen_ohne_inhalt}")
    print(f"laufzeit_s={dauer:.2f}")
    return 0


def cmd_selbsttest(_args: list[str]) -> int:
    """Zwei Kanarien-INHALTE (unterschiedliche Blase, je EIN Fundort) in den
    eigenen Tabellen datei+fundort. Sucht als beide Blasen, prueft dass jede
    NUR ihre eigene Kanarie sieht, fremde vollstaendig FEHLT. Raeumt danach
    ab (SQL DELETE in eigenen Tabellen, Reihenfolge fundort->fts_index->
    datei wegen externer Content-Bindung)."""
    if not WIKI_DB.exists():
        print("keine Datenbank vorhanden -- suche.py index zuerst ausfuehren")
        return 1
    con = _verbindung()
    if not _tabelle_existiert(con, "datei"):
        print("kein eigener Index vorhanden -- suche.py index zuerst ausfuehren")
        return 1
    fts5 = _fts5_verfuegbar(con)
    wortA = "ZZZKANARIEALPHA" + secrets.token_hex(6)
    wortB = "ZZZKANARIEBETA" + secrets.token_hex(6)
    schluesselA = "TESTHASH-" + secrets.token_hex(16)
    schluesselB = "TESTHASH-" + secrets.token_hex(16)

    def _einfuegen_inhalt(schluessel, titel, text):
        cur = con.execute(
            "INSERT INTO datei (pruefsumme, titel, art, volltext_indiziert, groesse, "
            "text, indiziert) VALUES (?,?,?,?,?,?,?)",
            (schluessel, titel, "text", 1, len(text), text, _jetzt()),
        )
        rid = cur.lastrowid
        if fts5:
            con.execute("INSERT INTO fts_index_datei (rowid, titel, text) VALUES (?,?,?)",
                        (rid, titel, text))
        else:
            con.execute("INSERT INTO fts_index_datei (id, titel, text) VALUES (?,?,?)",
                        (rid, titel, text))
        return rid

    idA = _mit_retry(_einfuegen_inhalt, schluesselA, "kanarie-alpha",
                      f"Inhalt mit dem Wort {wortA} nur in Blase A.")
    idB = _mit_retry(_einfuegen_inhalt, schluesselB, "kanarie-beta",
                      f"Inhalt mit dem Wort {wortB} nur in Blase B.")

    def _fundort_einfuegen(rid, schluessel, pfad, blase):
        con.execute(
            "INSERT INTO fundort (datei_id, pruefsumme, wirt, pfad, blase, geaendert) "
            "VALUES (?,?,?,?,?,?)", (rid, schluessel, WIRT, pfad, blase, _jetzt()),
        )
    _mit_retry(_fundort_einfuegen, idA, schluesselA, "/test/kanarie-alpha", "testblaseA")
    _mit_retry(_fundort_einfuegen, idB, schluesselB, "/test/kanarie-beta", "testblaseB")
    _mit_retry(con.commit)

    def _suche_als(wort: str, blase: str) -> list[int]:
        blase_sql, blase_params = _blase_wo("fo.blase", blase)
        if fts5:
            sql = ("SELECT d.id FROM fts_index_datei, datei d "
                   "WHERE d.id = fts_index_datei.rowid AND fts_index_datei MATCH ? "
                   "AND EXISTS (SELECT 1 FROM fundort fo WHERE fo.datei_id = d.id AND " + blase_sql + ")")
            params = [wort] + list(blase_params)
        else:
            sql = ("SELECT d.id FROM fts_index_datei f JOIN datei d ON d.id = f.id "
                   "WHERE f.text LIKE ? AND EXISTS (SELECT 1 FROM fundort fo "
                   "WHERE fo.datei_id = d.id AND " + blase_sql + ")")
            params = [f"%{wort}%"] + list(blase_params)
        return [r[0] for r in con.execute(sql, params).fetchall()]

    treffer_a_als_a = _suche_als(wortA, "testblaseA")
    treffer_b_als_a = _suche_als(wortB, "testblaseA")
    treffer_b_als_b = _suche_als(wortB, "testblaseB")
    treffer_a_als_b = _suche_als(wortA, "testblaseB")
    treffer_a_als_kern = _suche_als(wortA, "gabriel")
    treffer_b_als_kern = _suche_als(wortB, "andreas")

    ok = (
        idA in treffer_a_als_a and treffer_b_als_a == []
        and idB in treffer_b_als_b and treffer_a_als_b == []
        and idA in treffer_a_als_kern and idB in treffer_b_als_kern
    )

    print(f"eigene_blase_sieht_eigene_kanarie: A={idA in treffer_a_als_a} B={idB in treffer_b_als_b}")
    print(f"fremde_blase_ABWESEND (nicht nur versteckt): "
          f"B_als_A_treffer={treffer_b_als_a} (erwartet []) "
          f"A_als_B_treffer={treffer_a_als_b} (erwartet [])")
    print(f"kern_konten_sehen_alles: A_als_gabriel={idA in treffer_a_als_kern} "
          f"B_als_andreas={idB in treffer_b_als_kern}")
    print(f"SELBSTTEST_BESTANDEN={ok}")

    def _aufraeumen():
        con.execute("DELETE FROM fundort WHERE datei_id IN (?, ?)", (idA, idB))
        if fts5:
            con.execute("DELETE FROM fts_index_datei WHERE rowid IN (?, ?)", (idA, idB))
        else:
            con.execute("DELETE FROM fts_index_datei WHERE id IN (?, ?)", (idA, idB))
        con.execute("DELETE FROM datei WHERE id IN (?, ?)", (idA, idB))
        con.commit()
    _mit_retry(_aufraeumen)
    con.close()
    return 0 if ok else 1


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    befehl = sys.argv[1]
    rest = sys.argv[2:]
    try:
        if befehl == "index":
            return cmd_index(rest)
        if befehl == "suche":
            return cmd_suche(rest)
        if befehl == "thema":
            return cmd_thema(rest)
        if befehl == "stand":
            return cmd_stand(rest)
        if befehl == "selbsttest":
            return cmd_selbsttest(rest)
        if befehl == "importieren":
            return cmd_importieren(rest)
    except SperreErschoepft as e:
        print(f"ABBRUCH (gesperrt): {e}", file=sys.stderr)
        return 3
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
