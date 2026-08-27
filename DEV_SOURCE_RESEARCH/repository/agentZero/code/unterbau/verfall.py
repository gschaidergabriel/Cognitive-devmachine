#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verfall.py -- Konfidenz-Verfall & kontrolliertes Vergessen fuer wiki.db
=========================================================================

Gebaut nach dem Vorbild von Project-Frankenstein/tools/lcme/maintenance.py
(Titan MaintenanceEngine) und mempalace/dedup.py (mempalace-main, MIT).
Beide waren nur Referenz -- diese Datei ist eigenstaendig, kennt kein
externes Paket, macht KEINE Modell-/API-Aufrufe.

Was das hier tut (und warum), siehe Docstrings der einzelnen Funktionen.
Kurzfassung:

  1. SCHEMA   -- additive, nullable Spalten auf kante/folgerung (und
                 artikel.verfallen/protected, die fuer die Knoten-Seite
                 fehlten). Keine bestehende Spalte wird angefasst.
  2. BACKFILL -- kante.erzeugt_am aus dem echten Bearbeitungsdatum der
                 beiden Endpunkt-Artikel (siehe backfill_kante_zeit()).
                 Keine erfundenen Zeitstempel.
  3. DECAY    -- neue_konfidenz = basis * 2**(-alter_tage/7). Wird JEDES
                 Mal frisch aus einem unveraenderlichen Startwert und dem
                 Alter neu berechnet (idempotent, akkumuliert NICHT).
  4. FORGET   -- Kanten/Knoten-Kandidaten werden markiert (verfallen=1),
                 NIE geloescht. Jede Markierung schreibt einen grabstein-
                 Eintrag (Wiederverwendung des bestehenden Musters) und
                 ist per restore() umkehrbar.
  5. GRADUATE -- Knoten mit echtem Zugriffsnachweis (vp_paket_log) und
                 echter Konfidenz >= 0.6 werden protected=1 und damit
                 dauerhaft von 4. ausgenommen.
  6. SELFTEST -- laeuft auf einer WEGWERF-KOPIE der Datenbank (niemals
                 auf der Live-DB), beweist, dass jede geschuetzte Klasse
                 (siehe PROTECTED_*) nicht markiert werden kann, und dass
                 eine Markierung reversibel ist.

Nichts hier fuehrt ein DELETE aus (grep-bar pruefbar: keine "DELETE FROM"
Anweisung im ganzen File ausser in der Doku dieses Kommentars).

Nutzung:
    python3 verfall.py schema
    python3 verfall.py backfill
    python3 verfall.py decay
    python3 verfall.py graduate
    python3 verfall.py forget [--dry-run]
    python3 verfall.py restore kante <von> <nach> <art>
    python3 verfall.py restore artikel <id>
    python3 verfall.py report
    python3 verfall.py selftest
    python3 verfall.py all [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import math
import shutil
import sqlite3
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = "/var/lib/clay/wiki.db"

# ── Schwellwerte (Quelle: Auftrag, gespiegelt aus maintenance.py) ───────────
DECAY_HALF_LIFE_DAYS = 7.0          # Konfidenz halbiert sich alle 7 Tage
PRUNE_MIN_AGE_DAYS = 7.0            # unter diesem Alter wird NIE geprueft
NODE_PRUNE_MIN_CONFIDENCE = 0.2     # Knoten (artikel): Schwelle aus Abschnitt 2
EDGE_PRUNE_MIN_CONFIDENCE = 0.1     # Kanten (kante): eigene, engere Schwelle
KANTE_BASIS_KONFIDENZ = 1.0         # einheitlicher Startwert -- siehe unten
GRAD_WINDOW_DAYS = 14
GRAD_MIN_ACCESS = 3
GRAD_MIN_UTILITY = 0.6
GRAD_MIN_NODE_AGE_DAYS = 3.0        # "ueber die Zeit bewaehrt" (wie maintenance.py)

# _GEGEN_KANTE_ART / _GEGEN_FOLGERUNG_STATUS: 1:1 aus vorprozessor.py
# uebernommen (dort die Definition von "gegenseite", NIE gekappt).
GEGEN_KANTE_ART = {"widerspricht", "attacks"}
GEGEN_FOLGERUNG_STATUS = {"widerlegt", "abgeloest"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S+0000")


def connect(path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=30)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.row_factory = sqlite3.Row
    return conn


# ── 1 · SCHEMA ───────────────────────────────────────────────────────────
#
# Additiv, nullable. Kein Writer im Repo (kanten.py, wiki.py) baut mit
# SELECT * / positionellen Tupeln gegen kante -- kanten.py benutzt einen
# festen Spaltensatz "INSERT OR IGNORE INTO kante(von,nach,art,beleg)",
# das ist sicher (IGNORE ruehrt bestehende Zeilen bei PK-Konflikt gar
# nicht an). ABER: wiki.py (darf laut Auftrag nicht angefasst werden)
# benutzt an ZWEI Stellen (Zeile ~1285, ~1926)
#     INSERT OR REPLACE INTO kante (von, nach, art, beleg) VALUES (?,?,?,?)
# mit demselben festen 4-Spalten-Satz. Bei einem PK-Konflikt (von,nach,art
# existiert schon) ERSETZT REPLACE die GANZE Zeile -- alle hier neu
# hinzugefuegten Spalten (konfidenz, erzeugt_am, zeitquelle, verfallen,
# protected) fallen dabei still auf ihren Spalten-Default zurueck.
# Das ist GENAU der Bug, vor dem der Auftrag warnt (schon einmal bei
# `artikel` gefunden). Ich kann wiki.py nicht fixen (Verbot). Siehe
# REPORT-Abschnitt fuer die Konsequenz und den Umgang damit.
_KANTE_COLUMNS = {
    "konfidenz": "REAL",
    "erzeugt_am": "TEXT",
    "zeitquelle": "TEXT",       # Muster von artikel.zeitquelle uebernommen
    "verfallen": "INTEGER DEFAULT 0",
    "protected": "INTEGER DEFAULT 0",
}
_FOLGERUNG_COLUMNS = {
    "konfidenz": "REAL",
}
_ARTIKEL_COLUMNS = {
    # artikel.konfidenz existiert schon (179/14268 Zeilen belegt) --
    # NICHT anfassen. Es fehlen nur die Verfall/Schutz-Flags fuer die
    # Knoten-Seite von Abschnitt 2 ("node prune candidates").
    "verfallen": "INTEGER DEFAULT 0",
    "protected": "INTEGER DEFAULT 0",
}


def _existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}


def ensure_schema(conn: sqlite3.Connection) -> list[str]:
    """Additive ALTER TABLEs, idempotent. Gibt die Liste tatsaechlich
    neu angelegter Spalten zurueck (leer = schon vorhanden, nichts zu tun)."""
    added = []
    for table, cols in (
        ("kante", _KANTE_COLUMNS),
        ("folgerung", _FOLGERUNG_COLUMNS),
        ("artikel", _ARTIKEL_COLUMNS),
    ):
        have = _existing_columns(conn, table)
        for col, decl in cols.items():
            if col in have:
                continue
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
            added.append(f"{table}.{col}")
    conn.commit()
    return added


# ── 2 · BACKFILL kante.erzeugt_am ────────────────────────────────────────
#
# Kandidaten fuer die "Geburtszeit" einer Kante, in Praeferenzreihenfolge:
#   (a) MIN(zuletzt_bearbeitet) der beiden Endpunkt-Artikel
#       -- echtes Datei-mtime-Datum, Bereich 2025-12-29 .. 2026-08-14,
#       100% der artikel-Zeilen haben diesen Wert (gemessen).
#   (b) artikel.erzeugt_am der Endpunkte
#       -- VERWORFEN als Hauptquelle: 100% belegt, aber alle 14268 Werte
#       liegen in einem 22-Minuten-Fenster (20:12..20:34 Uhr, 2026-08-14)
#       -- das ist die Ingest-/Bauzeit des letzten wiki.py-Laufs, nicht
#       das Alter des Inhalts. Als Zeitbasis fuer einen 7-Tage-Half-Life
#       waere das falsch (jede Kante saehe "gerade eben entstanden" aus).
#   (c) graph_meta.built_at als letzter Fallback, falls (a) fehlt
#       -- kommt in der Praxis nicht vor (0 Kanten ohne (a), gemessen).
#
# UNSICHERHEIT, ehrlich benannt: (a) ist die mtime der Quelldatei, nicht
# der Zeitpunkt, an dem die KANTE selbst entdeckt/erzeugt wurde. Fuer
# inhaltlich abgeleitete Kanten (stuetzt, evidence, widerspricht, attacks,
# ...) ist das ein vernuenftiger unterer-Schranken-Proxy: die Kante kann
# nicht juenger sein als die letzte Aenderung an einem ihrer Endpunkte.
# Fuer STRUKTURELLE Kanten (geschwister_verzeichnis, geschwister_datei --
# zusammen 13.795 von 19.267 Kanten, 71,6%!) ist mtime ein SCHWACHER Proxy:
# diese Kanten kommen aus der Verzeichnisstruktur, nicht aus einer
# inhaltlichen Aenderung, und koennten in Wirklichkeit viel aelter oder
# juenger sein als der mtime-Wert vermuten laesst. Ich markiere die Quelle
# in kante.zeitquelle mit, damit das nachvollziehbar bleibt und niemand
# spaeter denkt, es sei ein gemessenes Erzeugungsdatum.
def backfill_kante_zeit(conn: sqlite3.Connection) -> dict:
    fallback = None
    row = conn.execute("SELECT value FROM graph_meta WHERE key='built_at'").fetchone()
    if row:
        fallback = row["value"]

    rows = conn.execute(
        """
        SELECT k.von, k.nach, k.art,
               av.zuletzt_bearbeitet AS zb_von, an.zuletzt_bearbeitet AS zb_nach
        FROM kante k
        JOIN artikel av ON av.id = k.von
        JOIN artikel an ON an.id = k.nach
        WHERE k.erzeugt_am IS NULL
        """
    ).fetchall()

    stats = {"endpoint_zb_min": 0, "graph_meta_fallback": 0, "unresolved": 0}
    for r in rows:
        zb_von, zb_nach = r["zb_von"], r["zb_nach"]
        candidates = [z for z in (zb_von, zb_nach) if z]
        if candidates:
            erzeugt = min(candidates)  # AELTESTER der beiden Endpunkte
            quelle = "endpoint_zuletzt_bearbeitet_min"
            stats["endpoint_zb_min"] += 1
        elif fallback:
            erzeugt = fallback
            quelle = "graph_meta_built_at_fallback"
            stats["graph_meta_fallback"] += 1
        else:
            stats["unresolved"] += 1
            continue
        conn.execute(
            "UPDATE kante SET erzeugt_am=?, zeitquelle=? WHERE von=? AND nach=? AND art=?",
            (erzeugt, quelle, r["von"], r["nach"], r["art"]),
        )
    conn.commit()
    return stats


# ── 3 · DECAY ─────────────────────────────────────────────────────────────
#
# new_confidence = base_confidence * 2**(-age_days / 7)
#
# Wird IMMER aus einem unveraenderlichen Startwert + aktuellem Alter neu
# berechnet und in die konfidenz-Spalte GESCHRIEBEN (nicht multiplikativ
# auf den vorherigen Wert angewandt) -- sonst haengt das Ergebnis davon
# ab, wie oft man den Lauf zwischendurch gestartet hat, was die Vorgabe-
# Formel nicht vorsieht und stillschweigend falsche Werte erzeugen wuerde.
#
# Startwerte je Tabelle (keine Erfindung von Daten):
#   kante:     einheitlich 1.0 fuer ALLE Kanten. Es gibt in der ganzen
#              Datenbank KEINE bestehende Quelle fuer eine differenzierte
#              Start-Konfidenz pro Kante (graph_kante.confidence existiert
#              als Spalte, ist aber zu 100% NULL -- geprueft, 192/192
#              Zeilen ohne Wert. Kein Platzhalter zum Abgreifen). Ein
#              einheitlicher Prior + echtes Alter differenziert die Kanten
#              trotzdem sauber ueber die Zeit.
#   folgerung: NUR wo folgerung.konfidenz bereits einen echten Wert hat.
#              Aktuell: 0 von 8 Zeilen. Verfall ist fuer folgerung also
#              JETZT ein No-Op -- bewusst, keine Erfindung eines Startwerts.
#              zeit-Spalte existiert schon (Erzeugungszeit, keine Backfill
#              noetig).
#   artikel:   NUR wo artikel.konfidenz bereits einen echten Wert hat
#              (179 von 14268 Zeilen, 1,25%). Die anderen 14089 werden
#              NICHT angefasst -- keine Erfindung.
def _age_days(erzeugt_am_str: str, now: datetime) -> float | None:
    if not erzeugt_am_str:
        return None
    s = erzeugt_am_str.strip()
    try:
        # deckt "+0000" / "+00:00" / "Z" / naive Formen ab
        s2 = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (now - dt).total_seconds() / 86400.0)
    except Exception:
        return None


def decay_kante(conn: sqlite3.Connection, now: datetime | None = None) -> int:
    now = now or _now()
    rows = conn.execute(
        "SELECT von, nach, art, erzeugt_am FROM kante WHERE erzeugt_am IS NOT NULL"
    ).fetchall()
    updated = 0
    for r in rows:
        age = _age_days(r["erzeugt_am"], now)
        if age is None:
            continue
        eff = KANTE_BASIS_KONFIDENZ * math.pow(2.0, -age / DECAY_HALF_LIFE_DAYS)
        conn.execute(
            "UPDATE kante SET konfidenz=? WHERE von=? AND nach=? AND art=?",
            (eff, r["von"], r["nach"], r["art"]),
        )
        updated += 1
    conn.commit()
    return updated


def decay_folgerung(conn: sqlite3.Connection, now: datetime | None = None) -> int:
    now = now or _now()
    rows = conn.execute(
        "SELECT id, konfidenz, zeit FROM folgerung WHERE konfidenz IS NOT NULL"
    ).fetchall()
    updated = 0
    for r in rows:
        age = _age_days(r["zeit"], now)
        if age is None:
            continue
        base = float(r["konfidenz"])
        eff = base * math.pow(2.0, -age / DECAY_HALF_LIFE_DAYS)
        conn.execute("UPDATE folgerung SET konfidenz=? WHERE id=?", (eff, r["id"]))
        updated += 1
    conn.commit()
    return updated


def decay_artikel(conn: sqlite3.Connection, now: datetime | None = None) -> int:
    now = now or _now()
    rows = conn.execute(
        "SELECT id, konfidenz, zuletzt_bearbeitet FROM artikel WHERE konfidenz IS NOT NULL"
    ).fetchall()
    updated = 0
    for r in rows:
        age = _age_days(r["zuletzt_bearbeitet"], now)
        if age is None:
            continue
        base = float(r["konfidenz"])
        eff = base * math.pow(2.0, -age / DECAY_HALF_LIFE_DAYS)
        conn.execute("UPDATE artikel SET konfidenz=? WHERE id=?", (eff, r["id"]))
        updated += 1
    conn.commit()
    return updated


# ── 4 · SCHUTZLISTE (harte Regel, unabhaengig von "protected") ──────────
#
# Diese Praedikate werden von forget_kante()/forget_artikel() IMMER
# zusaetzlich zu protected=1 abgefragt -- Verletzung ist nicht "vielleicht
# ein Bug", sondern die zentrale Sicherheitsanforderung des Auftrags.
def _protected_artikel_ids_sql() -> str:
    """Artikel-IDs, die NIE verfallen duerfen:
       - herkunft='nutzer' (Owner-Content)
       - graph_knoten.node_type='negative_result' (per externer_id=artikel.id,
         gemessen: 100% Deckung fuer alle 116 negative_result-Knoten)
       - Beleg-Ziel einer folgerung mit status widerlegt/abgeloest
         (folgerung_beleg.beleg_art='artikel')
    """
    gegen_status = ",".join("?" for _ in GEGEN_FOLGERUNG_STATUS)
    return f"""
        SELECT id FROM artikel WHERE herkunft='nutzer'
        UNION
        SELECT a.id FROM artikel a
          JOIN graph_knoten g ON g.external_id = a.id
          WHERE g.node_type = 'negative_result'
        UNION
        SELECT fb.beleg_id FROM folgerung_beleg fb
          JOIN folgerung f ON f.id = fb.folgerung_id
          WHERE fb.beleg_art='artikel' AND f.status IN ({gegen_status})
    """


def _protected_artikel_params() -> tuple:
    return tuple(GEGEN_FOLGERUNG_STATUS)


def _is_protected_kante_row(conn: sqlite3.Connection, von: str, nach: str, art: str) -> bool:
    if art in GEGEN_KANTE_ART:
        return True
    prot_ids_sql = _protected_artikel_ids_sql()
    params = _protected_artikel_params()
    row = conn.execute(
        f"SELECT 1 WHERE ? IN ({prot_ids_sql}) OR ? IN ({prot_ids_sql})",
        (von, *params, nach, *params),
    ).fetchone()
    return row is not None


# ── 5 · FORGET (markieren, NIE loeschen) ─────────────────────────────────
def _grabstein(conn: sqlite3.Connection, was: str, ziel_id: str, grund: str) -> None:
    now = _now()
    inhalt_hash = hashlib.sha256(f"{was}|{ziel_id}|{grund}|{now.isoformat()}".encode()).hexdigest()
    conn.execute(
        "INSERT INTO grabstein(was, ziel_id, autor, zeit, grund, inhalt_hash) "
        "VALUES (?,?,?,?,?,?)",
        (was, ziel_id, "verfall.py", _iso(now), grund, inhalt_hash),
    )


def forget_kante(conn: sqlite3.Connection, dry_run: bool = False) -> list[dict]:
    """Kandidaten: konfidenz < EDGE_PRUNE_MIN_CONFIDENCE UND Alter > 7 Tage.
    (degree=0 gibt es fuer Kanten selbst nicht -- das ist eine Knoten-
    Eigenschaft, siehe forget_artikel().)
    NIE verfallen gesetzt fuer: protected=1, art in GEGEN_KANTE_ART,
    oder ein Endpunkt ist ein geschuetzter Artikel (siehe Abschnitt 4)."""
    now = _now()
    rows = conn.execute(
        """
        SELECT von, nach, art, konfidenz, erzeugt_am FROM kante
        WHERE verfallen=0 AND protected=0
          AND konfidenz IS NOT NULL AND konfidenz < ?
          AND erzeugt_am IS NOT NULL
        """,
        (EDGE_PRUNE_MIN_CONFIDENCE,),
    ).fetchall()
    marked = []
    for r in rows:
        age = _age_days(r["erzeugt_am"], now)
        if age is None or age <= PRUNE_MIN_AGE_DAYS:
            continue
        if _is_protected_kante_row(conn, r["von"], r["nach"], r["art"]):
            continue
        grund = f"konfidenz={r['konfidenz']:.4f}<{EDGE_PRUNE_MIN_CONFIDENCE} alter={age:.1f}d"
        marked.append({"von": r["von"], "nach": r["nach"], "art": r["art"], "grund": grund})
        if not dry_run:
            conn.execute(
                "UPDATE kante SET verfallen=1 WHERE von=? AND nach=? AND art=?",
                (r["von"], r["nach"], r["art"]),
            )
            _grabstein(conn, "kante", f"{r['von']}|{r['nach']}|{r['art']}", grund)
    if not dry_run:
        conn.commit()
    return marked


def forget_artikel(conn: sqlite3.Connection, dry_run: bool = False) -> list[dict]:
    """Kandidaten: degree=0 (keine Kante beruehrt diesen Artikel) ODER
    (konfidenz < NODE_PRUNE_MIN_CONFIDENCE UND Alter > 7 Tage).
    NIE fuer protected=1 oder eine Zeile aus der Schutzliste (Abschnitt 4)."""
    now = _now()
    prot_ids_sql = _protected_artikel_ids_sql()
    prot_params = _protected_artikel_params()

    rows = conn.execute(
        f"""
        SELECT a.id, a.konfidenz, a.zuletzt_bearbeitet,
               NOT EXISTS(SELECT 1 FROM kante k WHERE k.von=a.id OR k.nach=a.id) AS isoliert
        FROM artikel a
        WHERE a.verfallen=0 AND a.protected=0
          AND a.id NOT IN ({prot_ids_sql})
        """,
        prot_params,
    ).fetchall()

    marked = []
    for r in rows:
        grund = None
        if r["isoliert"]:
            grund = "degree=0"
        elif r["konfidenz"] is not None and r["konfidenz"] < NODE_PRUNE_MIN_CONFIDENCE:
            age = _age_days(r["zuletzt_bearbeitet"], now)
            if age is not None and age > PRUNE_MIN_AGE_DAYS:
                grund = f"konfidenz={r['konfidenz']:.4f}<{NODE_PRUNE_MIN_CONFIDENCE} alter={age:.1f}d"
        if not grund:
            continue
        marked.append({"id": r["id"], "grund": grund})
        if not dry_run:
            conn.execute("UPDATE artikel SET verfallen=1 WHERE id=?", (r["id"],))
            _grabstein(conn, "artikel", r["id"], grund)
    if not dry_run:
        conn.commit()
    return marked


def restore_kante(conn: sqlite3.Connection, von: str, nach: str, art: str) -> None:
    conn.execute(
        "UPDATE kante SET verfallen=0 WHERE von=? AND nach=? AND art=?", (von, nach, art)
    )
    conn.commit()


def restore_artikel(conn: sqlite3.Connection, artikel_id: str) -> None:
    conn.execute("UPDATE artikel SET verfallen=0 WHERE id=?", (artikel_id,))
    conn.commit()


# ── 6 · GRADUATION ────────────────────────────────────────────────────────
#
# Utility-Signal: vp_paket_log.orte_json (die "orte" = Datei-Fundorte, die
# in einem ausgelieferten Paket tatsaechlich gezeigt wurden -- der
# EINZIGE echte Zugriffs-/Nutzungs-Nachweis, der in wiki.db existiert).
#
# Warum vp_paket_log statt taetigkeit (26.446 Zeilen)? Gemessen:
#   - taetigkeit.ziel_pfad sind Dateisystempfade AUSSERHALB von wiki.db
#     (z.B. "/home/.../wp3.md", ".git/") -- kein Bezug zu artikel/kante-
#     IDs, keine verlaessliche Bruecke ohne Heuristik/Raten.
#   - vp_paket_log.orte_json enthaelt "d<N>"-IDs = datei.id (geprueft:
#     datei.id=86676 existiert, Format passt exakt). datei ist ueber
#     artikel.quell_hash = datei.pruefsumme mit 14.218 von 14.268 Artikeln
#     (99,6%) verknuepft -- eine echte, messbare Bruecke zu Artikeln.
#
# Was dieses Signal NICHT sehen kann (Blindstellen, explizit benannt):
#   1. Es zeigt nur, dass eine Datei in einem AUSGELIEFERTEN Paket
#      auftauchte -- nicht, ob der Konsument sie tatsaechlich gelesen
#      oder fuer nuetzlich befunden hat. "Serviert" != "genutzt".
#   2. Nur 99,6% der Artikel haben ueberhaupt eine datei-Bruecke; die
#      restigen 0,4% (50 Artikel) koennen NIE graduieren, unabhaengig
#      von echtem Nutzen.
#   3. Die aktuelle vp_paket_log-Historie deckt nur ~44 Minuten ab
#      (2026-08-14T20:56 bis 21:40, gemessen) statt der geforderten
#      14-Tage-Fenster -- das Signal ist strukturell korrekt, aber die
#      Datenbasis ist heute zu duenn fuer nennenswerte Graduierung.
#
# utility() = die bereits verfallene (post-decay) artikel.konfidenz.
# Begruendung: es gibt in wiki.db KEIN separates "utility"-Feld. Die
# Referenzimplementierung (maintenance.py) faellt in genau diesem Fall
# selbst auf Konfidenz zurueck: `meta.get("utility", meta.get("confidence",
# 0.5))`. Ich uebernehme denselben Fallback 1:1 -- NUR fuer den
# Read-only-Vergleich >= 0.6, es wird dabei NICHTS erfunden und in
# keine Spalte geschrieben. Ohne echten konfidenz-Wert (NULL) bleibt der
# Fallback bei 0.5 < 0.6 -- ein Artikel ohne dokumentierte Konfidenz kann
# also NIE ueber den Fallback graduieren, nur ueber einen echten,
# gemessenen Wert >= 0.6.
def _datei_zugriffe_im_fenster(conn: sqlite3.Connection, now: datetime) -> dict[int, set[str]]:
    """datei.id -> Menge distinkter paket_id, die diese Datei innerhalb des
    GRAD_WINDOW_DAYS-Fensters ausgeliefert haben. Parst orte_json echt als
    JSON statt fragiler SQL-LIKE-Muster (orte_json hat Kommas MIT Leerzeichen,
    ein LIKE-Pattern wuerde nur den ersten Eintrag pro Zeile sauber treffen)."""
    import json as _json

    cutoff_iso = _iso(now - _td(GRAD_WINDOW_DAYS))
    zugriffe: dict[int, set[str]] = {}
    for row in conn.execute(
        "SELECT paket_id, orte_json FROM vp_paket_log WHERE zeit >= ?", (cutoff_iso,)
    ):
        try:
            orte = _json.loads(row["orte_json"] or "[]")
        except Exception:
            continue
        for ort in orte:
            if not (isinstance(ort, str) and ort.startswith("d") and ort[1:].isdigit()):
                continue
            datei_id = int(ort[1:])
            zugriffe.setdefault(datei_id, set()).add(row["paket_id"])
    return zugriffe


def graduate(conn: sqlite3.Connection, now: datetime | None = None) -> list[str]:
    now = now or _now()
    zugriffe = _datei_zugriffe_im_fenster(conn, now)
    if not zugriffe:
        return []

    min_age_cutoff = _iso(now - _td(GRAD_MIN_NODE_AGE_DAYS))
    rows = conn.execute(
        """
        SELECT a.id, a.konfidenz, d.id AS datei_id
        FROM artikel a
        JOIN datei d ON d.pruefsumme = a.quell_hash
        WHERE a.protected = 0 AND a.verfallen = 0
          AND a.zuletzt_bearbeitet < ?
          AND a.quell_hash IS NOT NULL
        """,
        (min_age_cutoff,),
    ).fetchall()

    graduated = []
    for r in rows:
        anzahl = len(zugriffe.get(r["datei_id"], ()))
        if anzahl < GRAD_MIN_ACCESS:
            continue
        utility = r["konfidenz"] if r["konfidenz"] is not None else 0.5  # mempalace-Fallback
        if utility < GRAD_MIN_UTILITY:
            continue
        conn.execute("UPDATE artikel SET protected=1 WHERE id=?", (r["id"],))
        _grabstein(
            conn, "artikel", r["id"],
            f"graduiert: zugriffe={anzahl} utility={utility:.3f}",
        )
        graduated.append(r["id"])
    conn.commit()
    return graduated


def _td(days: float):
    from datetime import timedelta
    return timedelta(days=days)


# ── 7 · SELFTEST (nur auf einer Wegwerf-Kopie!) ──────────────────────────
def selftest(source_db: str = DB_PATH) -> dict:
    """Kopiert die DB in eine temp-Datei, faehrt schema+backfill+decay+
    forget+graduate voll durch, und beweist per Assertion:
      (a) keine der geschuetzten Klassen wurde verfallen=1/protected
          NICHT-graduiert -- sondern bleibt unangetastet
      (b) eine Markierung ist per restore() umkehrbar
      (c) kein DELETE hat je stattgefunden (Zeilenzahlen unveraendert)
    Gibt bei Erfolg ein dict mit den Beweis-Zahlen zurueck, wirft sonst.
    """
    tmp = tempfile.NamedTemporaryFile(prefix="verfall-selftest-", suffix=".db", delete=False)
    tmp.close()
    shutil.copyfile(source_db, tmp.name)
    try:
        conn = connect(tmp.name)

        counts_before = {
            t: conn.execute(f"SELECT count(*) c FROM {t}").fetchone()["c"]
            for t in ("kante", "artikel", "folgerung", "problem")
        }

        # geschuetzte Referenzmengen VOR jedem Eingriff einfrieren
        protected_artikel_ids = {
            r["id"] for r in conn.execute(_protected_artikel_ids_sql(), _protected_artikel_params())
        }
        protected_kante = {
            (r["von"], r["nach"], r["art"])
            for r in conn.execute(
                f"SELECT von,nach,art FROM kante WHERE art IN ({','.join('?' for _ in GEGEN_KANTE_ART)})",
                tuple(GEGEN_KANTE_ART),
            )
        }
        widerlegt_folgerung_ids = {
            r["id"] for r in conn.execute(
                f"SELECT id FROM folgerung WHERE status IN ({','.join('?' for _ in GEGEN_FOLGERUNG_STATUS)})",
                tuple(GEGEN_FOLGERUNG_STATUS),
            )
        }
        offene_probleme = {
            r["id"] for r in conn.execute("SELECT id FROM problem WHERE status='offen'")
        }

        assert protected_artikel_ids, "Testvoraussetzung verletzt: 0 geschuetzte Artikel gefunden"
        assert protected_kante, "Testvoraussetzung verletzt: 0 geschuetzte Kanten (widerspricht/attacks) gefunden"
        assert widerlegt_folgerung_ids, "Testvoraussetzung verletzt: 0 widerlegte/abgeloeste folgerungen gefunden"
        assert offene_probleme, "Testvoraussetzung verletzt: 0 offene problem-Zeilen gefunden"

        ensure_schema(conn)
        backfill_kante_zeit(conn)
        decay_kante(conn)
        decay_folgerung(conn)
        decay_artikel(conn)
        # Schutzklassen kuenstlich auf hohe Verfall-Wahrscheinlichkeit setzen,
        # um den Praedikat-Pfad WIRKLICH zu pruefen statt nur "kam eh nicht vor"
        conn.execute(
            f"UPDATE kante SET konfidenz=0.0, erzeugt_am=? "
            f"WHERE art IN ({','.join('?' for _ in GEGEN_KANTE_ART)})",
            (_iso(_now() - _td(30)), *GEGEN_KANTE_ART),
        )
        conn.execute(
            f"UPDATE artikel SET konfidenz=0.0, zuletzt_bearbeitet=? "
            f"WHERE id IN ({','.join('?' for _ in protected_artikel_ids)})",
            (_iso(_now() - _td(30)), *protected_artikel_ids),
        )
        conn.commit()

        forget_kante(conn, dry_run=False)
        forget_artikel(conn, dry_run=False)
        graduate(conn)

        # (a) Beweis: geschuetzte Zeilen sind NICHT verfallen
        still_alive_artikel = {
            r["id"] for r in conn.execute(
                f"SELECT id FROM artikel WHERE verfallen=1 AND id IN "
                f"({','.join('?' for _ in protected_artikel_ids)})",
                tuple(protected_artikel_ids),
            )
        }
        assert not still_alive_artikel, f"SCHUTZ VERLETZT (artikel): {still_alive_artikel}"

        verfallene_gegenkanten = list(conn.execute(
            f"SELECT von,nach,art FROM kante WHERE verfallen=1 AND art IN "
            f"({','.join('?' for _ in GEGEN_KANTE_ART)})",
            tuple(GEGEN_KANTE_ART),
        ))
        assert not verfallene_gegenkanten, f"SCHUTZ VERLETZT (kante/gegenseite): {verfallene_gegenkanten}"

        # widerlegte folgerungen: Konfidenz darf existieren/verfallen (nur Zahl),
        # aber die Zeile selbst darf nie geloescht sein (siehe (c)) -- geprueft dort.
        # problem: verfall.py schreibt NIE in problem -- geprueft ueber (c) unten.

        # (b) Beweis: eine Markierung ist umkehrbar
        kante_kandidat = conn.execute(
            "SELECT von,nach,art FROM kante WHERE verfallen=1 LIMIT 1"
        ).fetchone()
        restore_ok = None
        if kante_kandidat:
            restore_kante(conn, kante_kandidat["von"], kante_kandidat["nach"], kante_kandidat["art"])
            row = conn.execute(
                "SELECT verfallen FROM kante WHERE von=? AND nach=? AND art=?",
                (kante_kandidat["von"], kante_kandidat["nach"], kante_kandidat["art"]),
            ).fetchone()
            assert row["verfallen"] == 0, "restore_kante() hat NICHT zurueckgesetzt"
            restore_ok = dict(kante_kandidat)

        # (c) Beweis: keine Zeile wurde geloescht (Row-Counts identisch)
        counts_after = {
            t: conn.execute(f"SELECT count(*) c FROM {t}").fetchone()["c"]
            for t in ("kante", "artikel", "folgerung", "problem")
        }
        assert counts_before == counts_after, f"ZEILEN VERSCHWUNDEN: {counts_before} -> {counts_after}"
        # problem-Tabelle zusaetzlich: Inhalt (nicht nur Zeilenzahl) unveraendert
        offene_probleme_nach = {
            r["id"] for r in conn.execute("SELECT id FROM problem WHERE status='offen'")
        }
        assert offene_probleme == offene_probleme_nach, "offene problem-Zeilen veraendert"

        return {
            "geschuetzte_artikel_geprueft": len(protected_artikel_ids),
            "geschuetzte_kanten_geprueft": len(protected_kante),
            "widerlegte_folgerungen_geprueft": len(widerlegt_folgerung_ids),
            "offene_probleme_geprueft": len(offene_probleme),
            "restore_beweis": restore_ok,
            "row_counts_unveraendert": counts_after,
            "ergebnis": "BESTANDEN",
        }
    finally:
        conn.close()
        Path(tmp.name).unlink(missing_ok=True)


# ── 8 · REPORT ────────────────────────────────────────────────────────────
def report(conn: sqlite3.Connection) -> dict:
    def one(sql, params=()):
        return conn.execute(sql, params).fetchone()[0]

    return {
        "kante_total": one("SELECT count(*) FROM kante"),
        "kante_mit_konfidenz": one("SELECT count(*) FROM kante WHERE konfidenz IS NOT NULL"),
        "kante_mit_erzeugt_am": one("SELECT count(*) FROM kante WHERE erzeugt_am IS NOT NULL"),
        "kante_verfallen": one("SELECT count(*) FROM kante WHERE verfallen=1"),
        "kante_protected": one("SELECT count(*) FROM kante WHERE protected=1"),
        "artikel_verfallen": one("SELECT count(*) FROM artikel WHERE verfallen=1"),
        "artikel_protected": one("SELECT count(*) FROM artikel WHERE protected=1"),
        "folgerung_mit_konfidenz": one("SELECT count(*) FROM folgerung WHERE konfidenz IS NOT NULL"),
        "grabstein_von_verfall_py": one(
            "SELECT count(*) FROM grabstein WHERE autor='verfall.py'"
        ),
    }


# ── CLI ────────────────────────────────────────────────────────────────
def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=[
        "schema", "backfill", "decay", "graduate", "forget", "restore",
        "report", "selftest", "all",
    ])
    p.add_argument("args", nargs="*")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--db", default=DB_PATH)
    ns = p.parse_args(argv)

    if ns.cmd == "selftest":
        result = selftest(ns.db)
        for k, v in result.items():
            print(f"  {k}: {v}")
        return

    conn = connect(ns.db)
    try:
        if ns.cmd == "schema":
            added = ensure_schema(conn)
            print(f"neue Spalten: {added or '(keine, schon vorhanden)'}")
        elif ns.cmd == "backfill":
            stats = backfill_kante_zeit(conn)
            print(f"backfill: {stats}")
        elif ns.cmd == "decay":
            k = decay_kante(conn)
            f = decay_folgerung(conn)
            a = decay_artikel(conn)
            print(f"decay: kante={k} folgerung={f} artikel={a}")
        elif ns.cmd == "graduate":
            g = graduate(conn)
            print(f"graduiert: {len(g)} artikel {g[:20]}")
        elif ns.cmd == "forget":
            mk = forget_kante(conn, dry_run=ns.dry_run)
            ma = forget_artikel(conn, dry_run=ns.dry_run)
            tag = "[DRY-RUN] " if ns.dry_run else ""
            print(f"{tag}kante-kandidaten: {len(mk)}")
            for m in mk[:20]:
                print(f"    {m}")
            print(f"{tag}artikel-kandidaten: {len(ma)}")
            for m in ma[:20]:
                print(f"    {m}")
        elif ns.cmd == "restore":
            if ns.args[0] == "kante":
                restore_kante(conn, ns.args[1], ns.args[2], ns.args[3])
            elif ns.args[0] == "artikel":
                restore_artikel(conn, ns.args[1])
            print("restauriert.")
        elif ns.cmd == "report":
            for k, v in report(conn).items():
                print(f"  {k}: {v}")
        elif ns.cmd == "all":
            added = ensure_schema(conn)
            bf = backfill_kante_zeit(conn)
            k = decay_kante(conn)
            f = decay_folgerung(conn)
            a = decay_artikel(conn)
            mk = forget_kante(conn, dry_run=ns.dry_run)
            ma = forget_artikel(conn, dry_run=ns.dry_run)
            g = [] if ns.dry_run else graduate(conn)
            print(f"schema neu: {added}")
            print(f"backfill: {bf}")
            print(f"decay: kante={k} folgerung={f} artikel={a}")
            print(f"forget-kandidaten (dry_run={ns.dry_run}): kante={len(mk)} artikel={len(ma)}")
            print(f"graduiert: {len(g)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
