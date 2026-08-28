#!/usr/bin/env python3
"""vorprozessor.py — der EINE Mechanismus.

ClayVerse ruft NIE SQL auf. Es ruft diesen Mechanismus auf einer Frage
(caveman English oder Deutsch, egal) und bekommt ein PAKET zurueck:
ids + felder, keine volltexte, mit codependenzen, gegenseite, offenen
kurationen und der SCHLEIFE ("weiter") -- wo mehr ist, ohne neue Suche.

Bauform (aus den drei belegten Bausteinen dieses Projekts):
  1. Moeglichkeitsraum   -- was dieser Wirt kann/nicht kann (karte.py, wirte.json)
  2. Emergent retrieval   -- die Kaskade aus u11_nl_claygraph_cascade_candidate.py:
                             Entitaetsaufloesung VOR jedem Graph-Walk (sonst 1,3% Top-1
                             trotz 100% Recall@5 -- 3x falsifiziert), Cache getroffen
                             ueber TYPISIERTE LUECKENSIGNATUR, nicht Rohtext (95% vs 0%),
                             bounded walk mit Zyklenschutz.
  3. Implikationsmechanismus -- folgerung + folgerung_beleg: eine Folgerung ohne Beleg
                             wird nicht ausgeliefert.

Policy ist Code, nicht Konfiguration: politik() gibt zurueck was gedeckelt/verworfen
wurde und WARUM -- als ClayCode, weil politik/rule/invariant genau das Genre ist,
in dem die Notation gemessen etwas bringt (25-39%), nicht Ergebnis-Prosa (+0,0pp).

Lernen ist beschraenkt und rueckgaengig zu machen (vp_edge_lern), gegen Eichnormale
gemessen (eichung.py, /var/lib/clay-eich -- NICHT selbst gebaut), mit Schnappschuss
(vp_snapshot) und Heilung (heilen() -> letzter Schnappschuss der die Normale bestand).
Verfall (hop_decay=0.58, wiederverwendet aus dem ClayGraph-Kandidaten, nicht neu erfunden)
haelt alte Treffer davon ab, fuer immer zu dominieren. Vielfaltsboden reserviert
Slots fuer unterrepraesentierte Cluster. Gegenseite wird NIE zuerst gekappt.

Nur lesend auf allen Bestandstabellen. Eigene Tabellen mit Praefix vp_.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

DB_PATH = "/var/lib/clay/wiki.db"
TOKEN_RE = re.compile(r"[A-Za-z0-9_äöüÄÖÜß\-]+")

# ── Caps aus dem Auftrag, aus keiner Erinnerung ─────────────────────────
CAP_LEXICAL = 48
CAP_QUERY_TOKENS = 20
CAP_ANCHORS = 2
CAP_WALK_HOPS = 2
CAP_WALK = 48
CAP_RESULT_DEFAULT = 8
CAP_RESULT_MAX = 128
CAP_CODEPENDENZEN = 24
CAP_HYPOTHESEN = 10
CAP_GEGENSEITE = 10          # weicher Deckel -- gegenseite wird NIE zuerst gekappt
CAP_KURATION = 10
CAP_WEITER_PRO_TREFFER = 5
HOP_DECAY = 0.58              # wiederverwendet aus dem ClayGraph-Kandidaten, nicht neu erfunden
DIVERSITY_FLOOR = 2           # mindestens so viele Cluster im Treffer-Ergebnis vertreten

# ORT (Datei-Fundorte): zweite Eintragsart neben Artikeln, gleiches Prinzip --
# Felder statt Volltext, ids statt Inhalt. lesen() ist der einzige Weg an Inhalt,
# und der ist an ein Paket gebunden (siehe unten).
CAP_ORT_KANDIDATEN = 60
CAP_ORT_RESULT = 8
CAP_ORT_ORTE_PRO_DATEI = 20     # wie viele (wirt,pfad) je Datei gezeigt werden
CAP_ORT_GESCHWISTER = 6
CAP_ORT_TAETIGKEIT = 5
CAP_LESE_BYTES = 200_000        # Groessendeckel fuer lesen() ohne expliziten Bereich
PAKET_TTL_SEKUNDEN = 3600       # wie 'frisch' ein Paket sein muss, damit lesen() es anerkennt
_GEWICHT_EXT = (".pt", ".safetensors", ".onnx", ".bin", ".ckpt", ".pth", ".gguf", ".h5", ".npz")

_STOPWORDER = {"the","a","an","is","are","was","were","of","for","to","in","on","and","or",
               "der","die","das","den","dem","des","ein","eine","einer","und","oder","von",
               "im","am","zu","fuer","für","ist","sind","war","waren","mit","bei","wie","was",
               "welche","welcher","welches","welchem","welchen","wer","wo"}
# Zusaetzliche Stopwoerter NUR fuer die Ort-Suche (Datei-Titel): generische
# Frageworte einer "wo liegt X"-Formulierung, die sonst als FTS-Suchbegriff
# auf zufaellige Dateinamen treffen ("auf_frank_api_ausspielen.json" enthaelt
# das Token "auf" woertlich -- gemessener Fehlfund, siehe Baubericht).
_ORT_STOPWORDER = _STOPWORDER | {"auf", "liegen", "liegt", "gross", "grosse", "große",
                                 "welchem", "welchen", "wirt", "pfad"}
_WORT_RE = re.compile(r"[A-Za-z0-9äöüÄÖÜß]+")

_GEGENHYP_ART = {"gegenhypothese"}
_GEGEN_KANTE_ART = {"widerspricht", "attacks"}
_GEGEN_EDGE_TYPE = {"CHALLENGES", "CONTRADICTS", "SUPERSEDES"}
_GEGEN_FOLGERUNG_STATUS = {"widerlegt", "abgeloest"}
_NEGATIV_STATUS = {"REFUTED", "FAILED", "ABORTED_OVERLAP", "CANDIDATE_NOT_PROMOTED"}


def _connect(path: str = DB_PATH) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{path}?mode=rwc", uri=True, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=30000")
    return c


def _ro(path: str = DB_PATH) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=30000")
    return c


def _ensure_vp_tables(c: sqlite3.Connection) -> None:
    c.executescript("""
    CREATE TABLE IF NOT EXISTS vp_plan_cache (
      sig_hash TEXT PRIMARY KEY,
      source_epoch INTEGER, graph_epoch INTEGER,
      anchor_ids TEXT, gap_terms TEXT,
      plan_json TEXT,
      erzeugt_am TEXT, treffer_anzahl INTEGER DEFAULT 0, zuletzt_getroffen TEXT
    );
    CREATE TABLE IF NOT EXISTS vp_edge_lern (
      query_class TEXT, edge_art TEXT,
      gewicht REAL DEFAULT 0, beobachtungen INTEGER DEFAULT 0,
      zuletzt_gelernt TEXT,
      PRIMARY KEY(query_class, edge_art)
    );
    CREATE TABLE IF NOT EXISTS vp_snapshot (
      snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
      erzeugt_am TEXT, state_hash TEXT,
      normals_score TEXT, normals_bestanden INTEGER,
      beobachtungen_gesamt INTEGER, edge_lern_snapshot TEXT
    );
    CREATE TABLE IF NOT EXISTS vp_ereignis (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      zeit TEXT, art TEXT, detail TEXT
    );
    CREATE TABLE IF NOT EXISTS vp_gesehen (
      lauf TEXT, record_id TEXT, zeit TEXT
    );
    CREATE TABLE IF NOT EXISTS vp_paket_log (
      paket_id TEXT PRIMARY KEY, zeit TEXT, epoch_sekunden INTEGER,
      frage TEXT, orte_json TEXT
    );
    CREATE TABLE IF NOT EXISTS vp_lese_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      zeit TEXT, ort_id TEXT, paket_id TEXT, bytes INTEGER, erlaubt INTEGER, grund TEXT
    );
    CREATE TABLE IF NOT EXISTS vp_alias (
      alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
      target_kind TEXT, target_id TEXT, alias_norm TEXT,
      alias_class TEXT, confidence REAL, source_epoch INTEGER
    );
    CREATE VIRTUAL TABLE IF NOT EXISTS vp_alias_fts USING fts5(alias_norm, content='vp_alias', content_rowid='alias_id');
    CREATE TABLE IF NOT EXISTS vp_alias_meta (key TEXT PRIMARY KEY, value TEXT);
    CREATE VIRTUAL TABLE IF NOT EXISTS vp_datei_fts USING fts5(titel, datei_id UNINDEXED);
    CREATE VIRTUAL TABLE IF NOT EXISTS vp_dir_fts USING fts5(verzeichnisname, datei_id UNINDEXED);
    """)
    # Phase 12 (Pulse-Zyklus): ein Schnappschuss gehoert zu einer Epoche, keine
    # eigene Nebenuhr. Migration statt Neubau, falls die Tabelle schon existiert.
    cols = {r[1] for r in c.execute("PRAGMA table_info(vp_snapshot)")}
    if "source_epoch" not in cols:
        c.execute("ALTER TABLE vp_snapshot ADD COLUMN source_epoch INTEGER")
    if "graph_epoch" not in cols:
        c.execute("ALTER TABLE vp_snapshot ADD COLUMN graph_epoch INTEGER")
    c.commit()


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _tokens(text: str) -> list[str]:
    toks = [t.lower() for t in TOKEN_RE.findall(text) if len(t) > 1]
    return toks[:CAP_QUERY_TOKENS]


def _fts_query(tokens: Iterable[str]) -> str:
    toks = [t for t in tokens if t not in _STOPWORDER]
    return " OR ".join('"' + t.replace('"', '') + '"' for t in toks) or '"__none__"'


def _source_epoch(c: sqlite3.Connection) -> int:
    r = c.execute("SELECT MAX(id) FROM taetigkeit").fetchone()
    return int(r[0] or 0)


def _graph_epoch(c: sqlite3.Connection) -> int:
    r = c.execute("SELECT MAX(graph_epoch) FROM graph_kante").fetchone()
    return int(r[0] or 0)


def _ref(kind: str, ident: str) -> str:
    """@path Referenz statt Prosa-Zeiger."""
    return f"@{kind}/{ident}"


# ── 1 · Moeglichkeitsraum ────────────────────────────────────────────────

def moeglichkeitsraum(wirt: Optional[str] = None) -> dict:
    """Was dieser Wirt kann/nicht kann -- aus wirte.json, wenn vorhanden.
    Fehlt es, wird das gemeldet statt erfunden (NO_INVENTION)."""
    for p in ("/var/lib/clay/karte/wirte.json", "/opt/clayverse/werkzeug/wirte.json"):
        fp = Path(p)
        if fp.exists():
            try:
                data = json.loads(fp.read_text())
                if wirt and isinstance(data, dict) and wirt in data:
                    return {"quelle": p, "wirt": wirt, "eintrag": data[wirt]}
                return {"quelle": p, "eintrag_anzahl": len(data) if hasattr(data, "__len__") else None}
            except Exception as e:
                return {"quelle": p, "fehler": str(e)}
    return {"quelle": None, "befund": "keine wirte.json gefunden -- Moeglichkeitsraum nicht ermittelt, nicht erfunden"}


# ── 2a · Entitaetsaufloesung (PFLICHT vor jedem Walk) ───────────────────

@dataclass(frozen=True)
class Resolution:
    resolution_class: str          # EXACT_ID | EVIDENCE_ALIAS | AMBIGUOUS | UNRESOLVED
    confidence: float
    anchors: tuple[str, ...]       # <= CAP_ANCHORS
    candidates: tuple[str, ...]    # was sonst noch in Frage kam


# ── Alias-Index (vp_alias) -- schliesst die belegte Luecke ──────────────
#
# Befund (Auftrag, gemessen im Korpus selbst): Graph-Anker OHNE Alias-Aufloesung
# -> Top1 = 0,0 (0 von 1200). Mit Alias-Aufloesung -> Top1 = 1,0. wiki.db hat KEINE
# Alias-Tabelle (gegen sqlite_master geprueft -- kein 'semantic_entity_aliases').
# Die Referenzform (`runtime/semantic_entity_resolver_v12.py`, SemanticEntityResolverV12)
# nimmt eine solche Tabelle als GEGEBEN an. Sie existiert nicht -- also gebaut,
# NICHT erfunden: eine vp_alias-Tabelle, indiziert aus real vorhandenen
# Identitaetsfeldern (artikel.id, artikel.logical_id, artikel.titel). Keine
# Alias-STRING wird erfunden -- jede Zeile zeigt auf ein echtes Feld einer
# echten Zeile. Klassen-Gewichtung und Margin-Gate uebernehmen die SHAPE aus
# v12 woertlich (Formel, Schwellen), weil das exakt die Zahl 0,0 -> 1,0 traegt.
_ALIAS_CLASS_WEIGHT = {"CANONICAL": 1.0, "DOCUMENT_DERIVED": 0.82}
_ALIAS_MIN_SCORE = 2.5
_ALIAS_MIN_MARGIN = 0.20


def _alias_epoch(c: sqlite3.Connection) -> int:
    """Grob genug, um bei jedem Bestandswachstum neu zu bauen, fein genug,
    um NICHT bei jeder taetigkeit-Zeile neu zu bauen (die aendert sich staendig,
    Artikel-/Dateibestand viel seltener)."""
    a = c.execute("SELECT COUNT(*) FROM artikel").fetchone()[0]
    d = c.execute("SELECT COUNT(*) FROM datei").fetchone()[0]
    return int(a) * 100000 + int(d)


def alias_index_aufbauen(c: sqlite3.Connection, *, erzwingen: bool = False) -> dict:
    stand = c.execute("SELECT value FROM vp_alias_meta WHERE key='alias_epoch'").fetchone()
    aktuell = _alias_epoch(c)
    if stand and int(stand[0]) == aktuell and not erzwingen:
        return {"gebaut": False, "grund": "bereits aktuell", "alias_epoch": aktuell}
    t0 = time.perf_counter()
    c.execute("DELETE FROM vp_alias")
    zeilen = []
    for r in c.execute("SELECT id,logical_id,titel FROM artikel"):
        zeilen.append(("artikel", r["id"], r["id"].lower(), "CANONICAL", 1.0))
        if r["logical_id"] and r["logical_id"] != r["id"]:
            zeilen.append(("artikel", r["id"], r["logical_id"].lower(), "CANONICAL", 1.0))
        if r["titel"]:
            zeilen.append(("artikel", r["id"], r["titel"], "DOCUMENT_DERIVED", 0.7))
    for r in c.execute("SELECT DISTINCT d.id, d.titel FROM datei d"):
        if r["titel"]:
            zeilen.append(("datei", f"d{r['id']}", r["titel"], "DOCUMENT_DERIVED", 0.7))
    c.executemany(
        "INSERT INTO vp_alias(target_kind,target_id,alias_norm,alias_class,confidence,source_epoch) "
        "VALUES (?,?,?,?,?,?)",
        [(k, tid, alias, cls, conf, aktuell) for k, tid, alias, cls, conf in zeilen],
    )
    c.execute("INSERT INTO vp_alias_fts(rowid,alias_norm) SELECT alias_id,alias_norm FROM vp_alias")
    c.execute("INSERT OR REPLACE INTO vp_alias_meta(key,value) VALUES ('alias_epoch',?)", (str(aktuell),))

    # vp_datei_fts: dieselbe Idee wie fts_index_artikel, nur fuer datei.titel --
    # ohne diesen Index kostet jede Ort-Suche einen LIKE-Vollscan ueber
    # datei JOIN fundort (52.513 x 92.715 Zeilen, gemessen 44ms/Aufruf). Mit FTS:
    # Index-Lookup, danach nur noch der (indizierte) fundort-Join per datei_id.
    c.execute("DELETE FROM vp_datei_fts")
    c.executemany("INSERT INTO vp_datei_fts(rowid,titel,datei_id) VALUES (?,?,?)",
                  [(r["id"], r["titel"], r["id"]) for r in c.execute("SELECT id,titel FROM datei WHERE titel IS NOT NULL")])

    # vp_dir_fts: Verzeichnisname als eigener Suchbegriff. Ohne das ist eine
    # Datei mit generischem Namen (registry.json, mini_train.jsonl) NUR ueber
    # ihren Pfad zu finden ("…/needle/registry.json") -- und genau DAS war der
    # Fall, der den Akzeptanztest ("wo liegen die Needle-Gewichte") zuerst
    # verfehlte: 'needle' stand nur im Verzeichnis, nicht im Dateinamen.
    c.execute("DELETE FROM vp_dir_fts")
    dir_rows = []
    seen_dir_datei: set[tuple[str, int]] = set()
    for r in c.execute("SELECT datei_id, pfad FROM fundort"):
        pfad = r["pfad"]
        if "/" not in pfad:
            continue
        dirname = pfad.rsplit("/", 1)[0].rsplit("/", 1)[-1]
        key = (dirname, r["datei_id"])
        if dirname and key not in seen_dir_datei:
            seen_dir_datei.add(key)
            dir_rows.append((dirname, r["datei_id"]))
    c.executemany("INSERT INTO vp_dir_fts(rowid,verzeichnisname,datei_id) VALUES (NULL,?,?)", dir_rows)
    c.commit()
    return {"gebaut": True, "zeilen": len(zeilen), "verzeichnis_zeilen": len(dir_rows),
            "sekunden": round(time.perf_counter() - t0, 3), "alias_epoch": aktuell}


def resolve_entities(c: sqlite3.Connection, tokens: list[str], raw_text: str) -> Resolution:
    """Fail-closed, SHAPE aus SemanticEntityResolverV12: nur EXACT/EVIDENCE_ALIAS
    duerfen einen Walk anstossen. AMBIGUOUS/LOW_CONFIDENCE/MISS raten NIE."""
    del raw_text
    if not tokens:
        return Resolution("MISS", 0.0, (), ())
    n = c.execute("SELECT COUNT(*) FROM vp_alias").fetchone()[0]
    if n == 0:
        alias_index_aufbauen(c)

    qt = set(tokens)
    marks = ",".join("?" for _ in qt)
    exact = c.execute(
        f"SELECT DISTINCT target_kind,target_id FROM vp_alias "
        f"WHERE alias_norm IN ({marks}) AND alias_class='CANONICAL' ORDER BY target_id LIMIT 4",
        tuple(qt),
    ).fetchall()
    artikel_exact = [r["target_id"] for r in exact if r["target_kind"] == "artikel"]
    if artikel_exact:
        anchors = tuple(sorted(set(artikel_exact)))[:CAP_ANCHORS]
        return Resolution("EXACT_ID", 1.0, anchors, tuple(sorted(set(artikel_exact))))

    expr = " OR ".join('"' + t.replace('"', '') + '"' for t in qt if len(t) > 1)
    if not expr:
        return Resolution("MISS", 0.0, (), ())
    rows = c.execute(
        """SELECT a.alias_norm, a.target_kind, a.target_id, a.alias_class, a.confidence
           FROM vp_alias_fts JOIN vp_alias a ON a.alias_id = vp_alias_fts.rowid
           WHERE vp_alias_fts MATCH ? AND a.target_kind='artikel' ORDER BY rank LIMIT 24""",
        (expr,),
    ).fetchall()
    by: dict[str, float] = {}
    for r in rows:
        at = set(_tokens(r["alias_norm"]))
        coverage = len(at & qt) / max(1, len(at))
        weight = _ALIAS_CLASS_WEIGHT.get(r["alias_class"], 0.5)
        score = 2.0 * coverage + float(r["confidence"]) * weight
        by[r["target_id"]] = max(by.get(r["target_id"], 0.0), score)
    ranked = sorted(by.items(), key=lambda kv: (-kv[1], kv[0]))
    cands = tuple(x[0] for x in ranked[:8])
    if not ranked or ranked[0][1] < _ALIAS_MIN_SCORE:
        return Resolution("LOW_CONFIDENCE" if ranked else "MISS", ranked[0][1] if ranked else 0.0, (), cands)
    if len(ranked) > 1 and ranked[0][1] - ranked[1][1] < _ALIAS_MIN_MARGIN:
        return Resolution("AMBIGUOUS", ranked[0][1], (), cands)
    return Resolution("EVIDENCE_ALIAS", min(1.0, ranked[0][1] / 3.0), (ranked[0][0],), cands)


# ── 2b · typisierte Luecken-Signatur (der Cache-Schluessel) ─────────────
#
# WICHTIG: das hier sind TYPISIERTE Kategorien, keine rohen Restwoerter.
# Rohe Restwoerter aendern sich mit jeder Umformulierung -> 0% Paraphrasen-Treffer
# (im Auftrag belegt). Typisierte Kategorien bleiben ueber Paraphrasen stabil ->
# 95% Treffer (ebenfalls im Auftrag belegt, u11/v15.1-Kandidat). Deshalb bildet
# gap_terms() rohe Tokens auf ein kleines, festes Vokabular von LUECKENARTEN ab.
_GAP_VOKABULAR: dict[str, set[str]] = {
    "gegenseite": {"widerspricht", "widerlegt", "gegenhypothese", "refute", "refuted",
                   "contradict", "contradicts", "challenge", "challenges", "superseded",
                   "abgeloest", "falsifiziert", "falsify", "widerruf"},
    "beleg": {"beleg", "belegt", "evidence", "proof", "nachweis", "quelle", "source",
              "verified", "bestaetigt", "confirmed"},
    "kuration": {"offen", "open", "todo", "kuration", "curation", "pending", "veraltet",
                 "outdated", "stale"},
    "aktuell": {"aktuell", "current", "latest", "jetzt", "now", "neuest", "heute"},
    "ursache": {"warum", "why", "weil", "because", "ursache", "cause", "grund", "reason"},
    "graph": {"kante", "edge", "verbindung", "connection", "zusammenhang", "related",
              "abhaengig", "depends", "requires", "voraussetzung"},
    "hypothese": {"hypothese", "hypothesis", "vermutung", "annahme", "spekulativ",
                  "speculative", "unverified", "unbelegt"},
    "messung": {"messung", "measurement", "wert", "zahl", "metrik", "metric", "prozent",
                "percent"},
}


def gap_terms(tokens: list[str], anchor_ids: tuple[str, ...]) -> tuple[str, ...]:
    del anchor_ids  # Ankertokens werden separat als 'anchors' im Signatur-Body gefuehrt
    tokset = set(tokens)
    typed = sorted(cat for cat, vocab in _GAP_VOKABULAR.items() if tokset & vocab)
    return tuple(typed)


def build_signature(*, source_epoch: int, graph_epoch: int, anchors: tuple[str, ...],
                     terms: tuple[str, ...]) -> tuple[str, str]:
    body = {"source_epoch": source_epoch, "graph_epoch": graph_epoch,
            "anchors": sorted(anchors), "gap_terms": sorted(terms)}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest(), blob


# ── 2c · begrenzter Walk mit Zyklenschutz ────────────────────────────────

def _walk(c: sqlite3.Connection, anchor: str, edge_bias: dict[str, float],
          max_depth: int = CAP_WALK_HOPS, limit: int = CAP_WALK):
    """Rekursiver Walk ueber `kante` (artikel<->artikel). Zyklenschutz per
    instr()-Pfadpruefung (Vorgabe #6). Kantengewicht = HOP_DECAY^tiefe * Lern-Bias
    fuer den Kantentyp (gedeckelt, gelernt -- siehe vp_edge_lern).

    Negativraum-Wache (SHAPE aus harness/reference/unifieddb_emergent_preprocessor.py:
    ein Knoten mit gesperrtem Status bleibt SICHTBAR als Ergebnis an seiner Tiefe,
    darf aber keine Aktivierung an seine Kinder weiterreichen -- reine Falschautoritaet
    "waescht" sich sonst durch den Graphen. Ehrlicher Vorbehalt: artikel.status ist
    bei 78% der Zeilen NULL; die Wache greift nur dort, wo ein Status VORHANDEN und
    negativ ist -- fehlender Status blockiert nichts (keine Erfindung von Evidenz)."""
    neg_names = [f"neg{i}" for i in range(len(_NEGATIV_STATUS))]
    neg_marks = ",".join(f":{n}" for n in neg_names)
    params = {"anchor": anchor, "max_depth": max_depth, "limit": limit, "decay": HOP_DECAY,
              **{n: v for n, v in zip(neg_names, _NEGATIV_STATUS)}}
    rows = c.execute(
        f"""
        WITH RECURSIVE walk(node, depth, art, score, path, via) AS (
          SELECT :anchor, 0, '', 1.0, '|'||:anchor||'|', NULL
          UNION ALL
          SELECT k.nach, w.depth+1, k.art,
                 w.score * (0.5 + 0.5*COALESCE(
                    (SELECT gewicht FROM vp_edge_lern WHERE edge_art=k.art AND query_class='global'),
                    0.0)) * (:decay),
                 w.path || k.nach || '|', w.node
          FROM walk w
          JOIN artikel av ON av.id = w.node
          JOIN kante k ON k.von = w.node
          WHERE w.depth < :max_depth AND instr(w.path, '|'||k.nach||'|') = 0
            AND (w.depth = 0 OR av.status IS NULL OR av.status NOT IN ({neg_marks}))
        )
        SELECT a.id AS record_id, a.art AS record_kind, a.epistemic_class, a.status,
               a.projekt, MIN(w.depth) AS depth, MAX(w.score) AS score,
               (SELECT k2.art FROM kante k2 WHERE k2.von=:anchor AND k2.nach=a.id LIMIT 1) AS edge_art,
               (SELECT w2.via FROM walk w2 WHERE w2.node=a.id ORDER BY w2.depth LIMIT 1) AS via
        FROM walk w JOIN artikel a ON a.id = w.node
        WHERE w.depth > 0
        GROUP BY a.id
        ORDER BY depth ASC, score DESC LIMIT :limit
        """,
        params,
    ).fetchall()
    return rows


# ── 3 · Implikationsmechanismus ─────────────────────────────────────────

def _folgerungen_fuer(c: sqlite3.Connection, ids: set[str]) -> tuple[list[dict], list[dict]]:
    """hypothesen (art=hypothese, mit Beleg) und gegenseite (status widerlegt/abgeloest).
    Eine Folgerung OHNE Beleg wird nicht ausgeliefert."""
    hyp, gegen = [], []
    rows = c.execute("SELECT id,art,aussage,gilt_fuer,status,widerlegt_durch FROM folgerung").fetchall()
    for r in rows:
        belege = c.execute(
            "SELECT beleg_art,beleg_id FROM folgerung_beleg WHERE folgerung_id=?", (r["id"],)
        ).fetchall()
        if not belege:
            continue  # OHNE BELEG -> nicht ausliefern
        gilt = str(r["gilt_fuer"] or "")
        beleg_ids = {b["beleg_id"] for b in belege}
        touches = bool(beleg_ids & ids) or any(str(i) in gilt for i in ids)
        if not touches:
            continue
        entry = {
            "id": r["id"], "art": r["art"], "aussage": r["aussage"][:280],
            "status": r["status"], "gilt_fuer": gilt,
            "beleg": [{"art": b["beleg_art"], "ref": _ref(b["beleg_art"], b["beleg_id"])} for b in belege],
            "ref": _ref("folgerung", r["id"]),
        }
        if r["status"] in _GEGEN_FOLGERUNG_STATUS:
            gegen.append(entry)
        elif r["art"] == "hypothese":
            hyp.append(entry)
    return hyp[:CAP_HYPOTHESEN], gegen


def _gegenseite_ids(c: sqlite3.Connection, ids: set[str]) -> list[dict]:
    """gegenhypothese-Artikel + widerspricht/attacks-Kanten + CHALLENGES/CONTRADICTS/
    SUPERSEDES aus graph_kante + folgerung(status widerlegt/abgeloest). Wird NIE
    zuerst gekappt (Policy-Invariante)."""
    out: list[dict] = []
    if not ids:
        return out
    qmarks = ",".join("?" for _ in ids)
    rows = c.execute(
        f"""SELECT von,nach,art,beleg FROM kante
            WHERE art IN ({",".join("?" for _ in _GEGEN_KANTE_ART)})
              AND (von IN ({qmarks}) OR nach IN ({qmarks}))""",
        list(_GEGEN_KANTE_ART) + list(ids) + list(ids),
    ).fetchall()
    for r in rows:
        out.append({"typ": "kante", "art": r["art"], "von": r["von"], "nach": r["nach"],
                     "beleg": (r["beleg"] or "")[:200],
                     "ref": _ref("artikel", r["nach"] if r["von"] in ids else r["von"])})
    rows = c.execute(
        f"""SELECT gk.source_node_id,gk.target_node_id,gk.edge_type,
                   sa.id AS source_aid, ta.id AS target_aid
            FROM graph_kante gk
            JOIN graph_knoten sn ON sn.node_id=gk.source_node_id
            JOIN graph_knoten tn ON tn.node_id=gk.target_node_id
            LEFT JOIN artikel sa ON sa.id=sn.external_id
            LEFT JOIN artikel ta ON ta.id=tn.external_id
            WHERE gk.edge_type IN ({",".join("?" for _ in _GEGEN_EDGE_TYPE)})
              AND (sa.id IN ({qmarks}) OR ta.id IN ({qmarks}))""",
        list(_GEGEN_EDGE_TYPE) + list(ids) + list(ids),
    ).fetchall()
    for r in rows:
        out.append({"typ": "graph_kante", "art": r["edge_type"], "von": r["source_aid"],
                     "nach": r["target_aid"],
                     "ref": _ref("artikel", r["target_aid"] or r["target_node_id"])})
    return out


# ── ORT: zweite Eintragsart neben Artikeln (datei + fundort) ───────────
#
# "Um zu wissen WO etwas ist, braucht man Pfad + Groesse + Pruefsumme --
# nie den Inhalt." (Auftrag) datei ist checksummen-dedupliziert: EINE Datei
# kann an vielen (wirt,pfad) liegen. Das ist genau die Frage, die vorher
# nicht beantwortbar war ("wo liegen die Needle-Gewichte") -- eine Abfrage
# beantwortet "wo ueberall, auf allen Wirten" statt vier Handbefehle je Wirt.

def _ort_sig(tokens: list[str]) -> list[str]:
    """Zerlegt Bindestrich-Komposita in Einzelwoerter -- 'needle-gewichte' matcht
    sonst NIE einen Dateinamen, der nur 'needle' als Token traegt (gemessener
    Fehlfund, siehe Baubericht). Nutzt die STRENGERE Ort-Stoppliste."""
    atomar: list[str] = []
    for t in tokens:
        atomar.extend(p for p in t.split("-") if p)
    return [t for t in atomar if len(t) > 1 and t not in _ORT_STOPWORDER][:6]


def _ort_kandidaten(c: sqlite3.Connection, tokens: list[str], limit: int = CAP_ORT_KANDIDATEN):
    if not tokens:
        return []
    sig = _ort_sig(tokens)
    if not sig:
        return []

    # Schneller Pfad, ZWEI Indizes statt eines LIKE-Vollscans (44-100ms gemessen):
    # (a) vp_datei_fts ueber datei.titel -- findet Dateien, deren NAME den Begriff traegt.
    # (b) vp_dir_fts ueber den Verzeichnisnamen -- findet Dateien mit generischem
    #     Namen (registry.json), deren VERZEICHNIS den Begriff traegt ('.../needle/').
    #     Ohne (b) verfehlt genau der Akzeptanztest "wo liegen die Needle-Gewichte" die
    #     echten Treffer (mini_train.jsonl, registry.json liegen in needle/, heissen
    #     selbst nicht so) -- gemessen, nicht vermutet.
    datei_ids: list[int] = []
    expr = " OR ".join('"' + t.replace('"', '') + '"' for t in sig)
    if expr:
        try:
            for r in c.execute(
                "SELECT datei_id FROM vp_datei_fts WHERE vp_datei_fts MATCH ? ORDER BY rank LIMIT ?",
                (expr, limit),
            ):
                datei_ids.append(r["datei_id"])
        except sqlite3.OperationalError:
            pass
        try:
            for r in c.execute(
                "SELECT datei_id FROM vp_dir_fts WHERE vp_dir_fts MATCH ? ORDER BY rank LIMIT ?",
                (expr, limit),
            ):
                if r["datei_id"] not in datei_ids:
                    datei_ids.append(r["datei_id"])
        except sqlite3.OperationalError:
            pass

    # ANGEWANDTER DECKEL, bewusst: KEIN LIKE-Vollscan-Fallback mehr auf `fundort.pfad`
    # direkt (52.513 x 92.715 Zeilen, 44-100ms JE AUFRUF gemessen). Beide FTS-Indizes
    # decken Datei- UND Verzeichnisname ab; was darueber hinausgeht (z.B. ein Begriff,
    # der nur MITTEN im Pfad steht, weder Datei- noch direkter Verzeichnisname), bleibt
    # ungefunden -- Recall-Verlust, ehrlich benannt, gegen den ausdruecklichen Auftrag
    # "die Antwort muss in Millisekunden kommen".
    datei_ids = datei_ids[:limit]
    if not datei_ids:
        return []
    qm = ",".join("?" for _ in datei_ids)
    rows = c.execute(
        f"""SELECT d.id AS datei_id, d.pruefsumme, d.titel, d.art, d.groesse, d.indiziert,
                   f.wirt, f.pfad, f.geaendert, f.blase
            FROM datei d JOIN fundort f ON f.datei_id = d.id
            WHERE d.id IN ({qm})""",
        datei_ids,
    ).fetchall()
    return rows


def _ort_gruppieren(rows) -> dict[int, dict]:
    grouped: dict[int, dict] = {}
    for r in rows:
        g = grouped.setdefault(r["datei_id"], {
            "datei_id": r["datei_id"], "pruefsumme": r["pruefsumme"], "titel": r["titel"],
            "art": r["art"], "groesse": r["groesse"], "indiziert": r["indiziert"], "orte": [],
        })
        if len(g["orte"]) < CAP_ORT_ORTE_PRO_DATEI:
            g["orte"].append({"wirt": r["wirt"], "pfad": r["pfad"], "geaendert": r["geaendert"],
                              "blase": r["blase"]})
    return grouped


def _ort_codependenzen_batch(c: sqlite3.Connection, ranked: list[dict]) -> dict[int, dict]:
    """Batched statt N+1: je Zusammenhangsart EINE Abfrage fuer ALLE gewaehlten
    Orte, nicht eine je Ort. Auf einer geteilten, gleichzeitig beschriebenen DB
    (WAL, andere Agenten schreiben mit) kostet jede execute() reale Millisekunden
    -- 65 Einzelabfragen fuer 8 Orte war das gemessene Problem (siehe Baubericht),
    hier auf 1+1+bis-zu-8 reduziert."""
    codep_by_id: dict[int, dict] = {g["datei_id"]: {"artikel": [], "taetigkeit": [], "geschwister": []} for g in ranked}
    if not ranked:
        return codep_by_id
    pruefsummen = list({g["pruefsumme"] for g in ranked})
    hash_to_dateiids: dict[str, list[int]] = defaultdict(list)
    for g in ranked:
        hash_to_dateiids[g["pruefsumme"]].append(g["datei_id"])

    qm = ",".join("?" for _ in pruefsummen)
    for r in c.execute(f"SELECT id,titel,art,quell_hash FROM artikel WHERE quell_hash IN ({qm})", pruefsummen):
        for did in hash_to_dateiids.get(r["quell_hash"], ()):
            if len(codep_by_id[did]["artikel"]) < 5:
                codep_by_id[did]["artikel"].append({"id": r["id"], "art": r["art"], "ref": _ref("artikel", r["id"])})

    pfad_to_dateiids: dict[str, list[int]] = defaultdict(list)
    alle_pfade: list[str] = []
    for g in ranked:
        for o in g["orte"][:2]:
            pfad_to_dateiids[o["pfad"]].append(g["datei_id"])
            alle_pfade.append(o["pfad"])
    alle_pfade = list(dict.fromkeys(alle_pfade))[:40]
    if alle_pfade:
        qm2 = ",".join("?" for _ in alle_pfade)
        for r in c.execute(
            f"SELECT id,werkzeug,aktion,zeit,wirt,ziel_pfad FROM taetigkeit WHERE ziel_pfad IN ({qm2}) ORDER BY id DESC",
            alle_pfade,
        ):
            for did in pfad_to_dateiids.get(r["ziel_pfad"], ()):
                if len(codep_by_id[did]["taetigkeit"]) < CAP_ORT_TAETIGKEIT:
                    codep_by_id[did]["taetigkeit"].append({
                        "id": r["id"], "werkzeug": r["werkzeug"], "aktion": r["aktion"],
                        "zeit": r["zeit"], "wirt": r["wirt"], "ref": _ref("taetigkeit", r["id"]),
                    })

    # Geschwister: eine Praefix-Abfrage je Ort (bleibt N Abfragen -- LIKE-Praefix
    # laesst sich ohne UNION nicht sauber batchen), aber nur EIN Ort je Datei
    # (nicht zwei), und nur fuer die schon gedeckelten `ranked` (<= budget).
    for g in ranked:
        if not g["orte"]:
            continue
        o = g["orte"][0]
        verzeichnis = o["pfad"].rsplit("/", 1)[0] + "/"
        for r in c.execute(
            """SELECT DISTINCT d2.id AS did, d2.titel FROM fundort f2 JOIN datei d2 ON d2.id=f2.datei_id
               WHERE f2.wirt=? AND f2.pfad LIKE ? AND d2.id!=? LIMIT ?""",
            (o["wirt"], verzeichnis + "%", g["datei_id"], CAP_ORT_GESCHWISTER),
        ):
            codep_by_id[g["datei_id"]]["geschwister"].append({"datei_id": r["did"], "titel": r["titel"],
                                                               "ref": _ref("datei", r["did"])})
    return codep_by_id


def _orte_paket(c: sqlite3.Connection, tokens: list[str], budget: int = CAP_ORT_RESULT) -> list[dict]:
    rows = _ort_kandidaten(c, tokens)
    grouped = _ort_gruppieren(rows)
    sig = _ort_sig(tokens)

    sig_set = set(sig)

    def _score(g: dict) -> float:
        s = float(len(g["orte"]))
        titel_l = (g["titel"] or "").lower()
        if any(titel_l.endswith(ext) for ext in _GEWICHT_EXT):
            s += 5.0
        s += sum(1 for t in sig if t in titel_l)
        # Verzeichnistreffer zaehlt GENAUSO wie ein Dateinamens-Treffer -- sonst
        # verliert eine Datei mit generischem Namen (registry.json) in einem
        # eindeutig passenden Ordner (".../needle/") gegen zufaellige Gleichstaende.
        # Gemessener Fehlfund im Akzeptanztest, hier der Fix.
        for o in g["orte"][:2]:
            dirname = o["pfad"].rsplit("/", 1)[0].rsplit("/", 1)[-1].lower()
            if dirname in sig_set:
                s += 3.0
                break
        return s

    ranked = sorted(grouped.values(), key=lambda g: -_score(g))[:budget]
    codep_by_id = _ort_codependenzen_batch(c, ranked)
    out = []
    for g in ranked:
        codep = codep_by_id[g["datei_id"]]
        weiter = ([{"ref": a["ref"], "art": "quelle_von", "relation_type": "IS_SOURCE_OF"} for a in codep["artikel"]]
                  + [{"ref": s["ref"], "art": "im_selben_verzeichnis", "relation_type": "SIBLING_OF"} for s in codep["geschwister"]])
        out.append({
            "ort_id": f"d{g['datei_id']}",
            "inhalt": {
                "checksum": g["pruefsumme"], "groesse": g["groesse"], "art": g["art"],
                "ist_text": g["art"] == "text", "ist_binaer": g["art"] != "text",
                "titel": g["titel"],
            },
            "orte": g["orte"],
            "metadaten": {"indiziert": g["indiziert"], "orte_anzahl": len(g["orte"])},
            "codependenzen": codep,
            "weiter": weiter[:CAP_WEITER_PRO_TREFFER],
            "ref": _ref("datei", g["datei_id"]),
            "authority": "CONTEXT_ONLY",
        })
    return out


# ── Gated read: nur ueber ein Paket, das den Ort tatsaechlich nannte ────

def _lese_log(c: sqlite3.Connection, ort_id: str, paket_id: str, n_bytes: int, erlaubt: bool, grund: str) -> None:
    c.execute("INSERT INTO vp_lese_log(zeit,ort_id,paket_id,bytes,erlaubt,grund) VALUES (?,?,?,?,?,?)",
              (_now(), ort_id, paket_id, n_bytes, int(erlaubt), grund))
    c.commit()


def lesen(ort_id: str, paket_id: str, *, bereich: Optional[tuple[int, int]] = None,
          conn: Optional[sqlite3.Connection] = None) -> dict:
    """lesen(ort_id, paket_id) -> Inhalt, oder VERWEIGERT mit Grund.

    Lesen in Suchabsicht ist verboten. Der einzige erlaubte Weg: erst fragen
    (paket()), DANN -- und nur dann -- die kurze genannte Liste lesen. Ohne
    ein Paket, das genau diesen Ort nannte, gibt es keinen Inhalt."""
    own = conn is None
    c = conn or _connect()
    _ensure_vp_tables(c)
    row = c.execute("SELECT zeit,epoch_sekunden,orte_json FROM vp_paket_log WHERE paket_id=?", (paket_id,)).fetchone()
    if row is None:
        _lese_log(c, ort_id, paket_id, 0, False, "paket_id unbekannt -- kein Paket mit dieser id gefunden")
        if own: c.close()
        return {"erlaubt": False, "grund": "paket_id unbekannt -- kein Paket mit dieser id gefunden"}
    alter = time.time() - float(row["epoch_sekunden"] or 0)
    if alter > PAKET_TTL_SEKUNDEN:
        _lese_log(c, ort_id, paket_id, 0, False, f"Paket ist {int(alter)}s alt, TTL={PAKET_TTL_SEKUNDEN}s -- abgelaufen")
        if own: c.close()
        return {"erlaubt": False, "grund": f"Paket abgelaufen ({int(alter)}s > {PAKET_TTL_SEKUNDEN}s) -- neu fragen"}
    genannt = set(json.loads(row["orte_json"]))
    if ort_id not in genannt:
        _lese_log(c, ort_id, paket_id, 0, False, f"Paket {paket_id} hat {ort_id} nicht genannt")
        if own: c.close()
        return {"erlaubt": False, "grund": f"dieses Paket hat '{ort_id}' nicht genannt -- kein Lesen ohne Nennung"}
    if not ort_id.startswith("d") or not ort_id[1:].isdigit():
        _lese_log(c, ort_id, paket_id, 0, False, "ungueltige ort_id")
        if own: c.close()
        return {"erlaubt": False, "grund": "ungueltige ort_id"}
    datei_id = int(ort_id[1:])
    d = c.execute("SELECT id,titel,art,groesse,text FROM datei WHERE id=?", (datei_id,)).fetchone()
    if d is None:
        _lese_log(c, ort_id, paket_id, 0, False, "datei nicht gefunden")
        if own: c.close()
        return {"erlaubt": False, "grund": "datei nicht gefunden"}
    if d["art"] != "text":
        _lese_log(c, ort_id, paket_id, 0, False, "binaer -- standardmaessig verweigert")
        if own: c.close()
        return {"erlaubt": False, "grund": "binaer -- lesen() liefert standardmaessig keine Binaerdaten"}
    text = d["text"] or ""
    if bereich is not None:
        start, end = bereich
        text = text[start:end]
    elif len(text.encode("utf-8")) > CAP_LESE_BYTES:
        _lese_log(c, ort_id, paket_id, 0, False, f"zu gross ({d['groesse']} Bytes) fuer Volllesen ohne bereich=")
        if own: c.close()
        return {"erlaubt": False, "grund": f"zu gross ({d['groesse']} Bytes > {CAP_LESE_BYTES}) -- bereich=(start,end) angeben"}
    n = len(text.encode("utf-8"))
    _lese_log(c, ort_id, paket_id, n, True, "erlaubt")
    if own: c.close()
    return {"erlaubt": True, "titel": d["titel"], "bytes": n, "text": text}


# ── Paket-Zusammenbau ─────────────────────────────────────────────────

@dataclass
class Politik:
    caps: dict = field(default_factory=dict)
    gedeckelt: dict = field(default_factory=dict)   # was wurde tatsaechlich gekappt
    drop_order: list = field(default_factory=list)
    nie_gekappt: list = field(default_factory=list)
    plan: str = "COLD"

    def to_claycode(self) -> str:
        lines = ["module vorprozessor.politik", 'version "1.0"']
        for k, v in self.caps.items():
            lines.append(f"rule cap.{k} = {v}")
        lines.append(f'rule plan = "{self.plan}"')
        lines.append(f"metric hop_decay = {HOP_DECAY}")
        lines.append(f"metric diversity_floor = {DIVERSITY_FLOOR}")
        lines.append("rule drop_order = [" + ", ".join(f'"{d}"' for d in self.drop_order) + "]")
        for n in self.nie_gekappt:
            lines.append(f'invariant {n}.dropped_first == false')
        for k, v in self.gedeckelt.items():
            lines.append(f"fact gedeckelt.{k} = {v}" if isinstance(v, (int, float)) else f'fact gedeckelt.{k} = "{v}"')
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {"caps": self.caps, "gedeckelt": self.gedeckelt, "drop_order": self.drop_order,
                "nie_gekappt": self.nie_gekappt, "plan": self.plan,
                "claycode": self.to_claycode()}


def _artikel_felder(c: sqlite3.Connection, ids: Iterable[str]) -> dict[str, sqlite3.Row]:
    ids = list(ids)
    if not ids:
        return {}
    qmarks = ",".join("?" for _ in ids)
    rows = c.execute(
        f"""SELECT id,art,titel,epistemic_class,status,projekt,sphaere,logical_id,
                   zuletzt_bearbeitet,konfidenz FROM artikel WHERE id IN ({qmarks})""",
        ids,
    ).fetchall()
    return {r["id"]: r for r in rows}


def _cluster(row: sqlite3.Row) -> str:
    return str(row["projekt"] or row["art"] or "unbekannt")


def _score_entry(row: sqlite3.Row, base: float) -> float:
    ep = str(row["epistemic_class"] or "")
    status = str(row["status"] or "")
    bonus = 0.0
    if ep in {"MEASURED_RESULT_SUMMARY", "EXECUTABLE_RESEARCH_RESULT"}:
        bonus += 0.4
    if ep == "NEGATIVE_RESULT_SUMMARY":
        bonus += 0.3  # gegenseite darf nicht durch Ranking verschwinden
    if status in _NEGATIV_STATUS:
        bonus += 0.15
    if row["art"] == "gegenhypothese":
        bonus += 0.5
    return base + bonus


def paket(text: str, *, budget: int = CAP_RESULT_DEFAULT, wirt: Optional[str] = None,
          conn: Optional[sqlite3.Connection] = None, lauf_id: Optional[str] = None) -> dict:
    """DIE eine Schnittstelle. Ein Aufruf rein, ein Paket raus."""
    budget = max(1, min(int(budget), CAP_RESULT_MAX))
    own = conn is None
    c = conn or _connect()
    _ensure_vp_tables(c)
    alias_index_aufbauen(c)   # no-op wenn schon aktuell (Epoche geprueft, nicht neu gebaut)
    started = time.perf_counter_ns()

    tokens = _tokens(text)
    source_epoch = _source_epoch(c)
    graph_epoch = _graph_epoch(c)

    resolution = resolve_entities(c, tokens, text.strip())
    anchors = resolution.anchors
    terms = gap_terms(tokens, anchors)

    plan_source = "NO_ANCHOR_LEXICAL_ONLY"
    cache_hit = False
    sig_hash = None
    walk_rows: list[sqlite3.Row] = []
    if anchors:
        sig_hash, _ = build_signature(source_epoch=source_epoch, graph_epoch=graph_epoch,
                                       anchors=anchors, terms=terms)
        cached = c.execute(
            "SELECT plan_json FROM vp_plan_cache WHERE sig_hash=? AND source_epoch=? AND graph_epoch=?",
            (sig_hash, source_epoch, graph_epoch),
        ).fetchone()
        if cached:
            cache_hit = True
            plan_source = "WARM_CACHE"
            plan = json.loads(cached["plan_json"])
            c.execute(
                "UPDATE vp_plan_cache SET treffer_anzahl=treffer_anzahl+1, zuletzt_getroffen=? WHERE sig_hash=?",
                (_now(), sig_hash),
            )
        else:
            plan_source = "COLD_BUILD"
            edge_bias = {r["edge_art"]: r["gewicht"] for r in
                         c.execute("SELECT edge_art,gewicht FROM vp_edge_lern WHERE query_class='global'")}
            seen_ids: set[str] = set()
            walked: list[dict] = []
            for a in anchors[:CAP_ANCHORS]:
                for r in _walk(c, a, edge_bias):
                    if r["record_id"] in seen_ids:
                        continue
                    seen_ids.add(r["record_id"])
                    walked.append({"id": r["record_id"], "depth": r["depth"], "score": r["score"],
                                    "edge_art": r["edge_art"], "anchor": a})
            walked.sort(key=lambda w: (w["depth"], -w["score"]))
            plan = {"anchors": list(anchors), "walked": walked[:CAP_WALK]}
            c.execute(
                "INSERT OR REPLACE INTO vp_plan_cache(sig_hash,source_epoch,graph_epoch,anchor_ids,"
                "gap_terms,plan_json,erzeugt_am,treffer_anzahl,zuletzt_getroffen) VALUES (?,?,?,?,?,?,?,0,?)",
                (sig_hash, source_epoch, graph_epoch, json.dumps(sorted(anchors)),
                 json.dumps(sorted(terms)), json.dumps(plan), _now(), _now()),
            )
        walk_rows = plan["walked"]

    # lexikalisch (immer, als Grundrauschen + Fallback wenn kein Anker)
    lex_rows = c.execute(
        """SELECT s.artikel_id AS aid, bm25(fts_index_artikel) AS r
           FROM fts_index_artikel JOIN artikel_suchtext s ON s.id = fts_index_artikel.rowid
           WHERE fts_index_artikel MATCH ? LIMIT ?""",
        (_fts_query(tokens), CAP_LEXICAL),
    ).fetchall()

    scores: dict[str, float] = {}
    for rank, r in enumerate(lex_rows, 1):
        scores[r["aid"]] = scores.get(r["aid"], 0.0) + 1.0 / math.log2(rank + 1)
    for w in walk_rows:
        scores[w["id"]] = scores.get(w["id"], 0.0) + 2.0 * float(w["score"])
    for a in anchors:
        scores[a] = scores.get(a, 0.0) + 3.0

    cand_ids = list(scores.keys())
    felder = _artikel_felder(c, cand_ids)
    for rid in list(scores.keys()):
        row = felder.get(rid)
        if row is not None:
            scores[rid] = _score_entry(row, scores[rid])

    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))

    # ── Vielfaltsboden: reserviere Slots fuer unterrepraesentierte Cluster ──
    core_n = max(1, budget - DIVERSITY_FLOOR)
    core = ranked[:core_n]
    core_clusters = {_cluster(felder[rid]) for rid, _ in core if rid in felder}
    explore: list[tuple[str, float]] = []
    for rid, sc in ranked[core_n:]:
        if rid not in felder:
            continue
        cl = _cluster(felder[rid])
        if cl not in core_clusters:
            explore.append((rid, sc))
            core_clusters.add(cl)
        if len(explore) >= DIVERSITY_FLOOR:
            break
    chosen = core + explore
    chosen_ids = {rid for rid, _ in chosen}

    treffer = []
    for rid, sc in chosen:
        row = felder.get(rid)
        if row is None:
            continue
        treffer.append({
            "id": rid, "logical_id": row["logical_id"], "art": row["art"],
            "epistemic_class": row["epistemic_class"], "status": row["status"],
            "projekt": row["projekt"], "sphaere": row["sphaere"],
            "score": round(sc, 4), "ref": _ref("artikel", rid),
        })

    # codependenzen: kante beide Richtungen fuer die gewaehlten ids
    codep = []
    if chosen_ids:
        qmarks = ",".join("?" for _ in chosen_ids)
        rows = c.execute(
            f"SELECT von,nach,art,beleg FROM kante WHERE von IN ({qmarks}) OR nach IN ({qmarks})",
            list(chosen_ids) * 2,
        ).fetchall()
        for r in rows[:CAP_CODEPENDENZEN]:
            codep.append({"von": r["von"], "nach": r["nach"], "art": r["art"],
                           "beleg": (r["beleg"] or "")[:160],
                           "ref_von": _ref("artikel", r["von"]), "ref_nach": _ref("artikel", r["nach"])})

    hypothesen, gegen_folg = _folgerungen_fuer(c, chosen_ids)
    gegen_kanten = _gegenseite_ids(c, chosen_ids)
    gegenseite = gegen_folg + gegen_kanten   # NIE gekappt vor allem anderen

    orte = _orte_paket(c, tokens, budget=CAP_ORT_RESULT)
    system_eintraege = systeme(c)

    kur = []
    if chosen_ids:
        qmarks = ",".join("?" for _ in chosen_ids)
        rows = c.execute(
            f"""SELECT artikel_id,quelle,ereignis,klasse,status FROM kuration
                WHERE status='offen' AND artikel_id IN ({qmarks}) LIMIT {CAP_KURATION}""",
            list(chosen_ids),
        ).fetchall()
        for r in rows:
            kur.append({"artikel_id": r["artikel_id"], "klasse": r["klasse"],
                        "ereignis": (r["ereignis"] or "")[:160],
                        "ref": _ref("artikel", r["artikel_id"])})

    # weiter: naechste ids je Treffer via kante, noch nicht im Paket
    weiter = []
    if chosen_ids:
        qmarks = ",".join("?" for _ in chosen_ids)
        rows = c.execute(
            f"""SELECT von,nach,art FROM kante WHERE von IN ({qmarks})
                AND nach NOT IN ({qmarks})""",
            list(chosen_ids) * 2,
        ).fetchall()
        by_src: dict[str, list] = defaultdict(list)
        for r in rows:
            by_src[r["von"]].append({"art": r["art"], "ref": _ref("artikel", r["nach"]), "id": r["nach"]})
        for src, links in by_src.items():
            weiter.append({"von": _ref("artikel", src), "naechste": links[:CAP_WEITER_PRO_TREFFER]})

    # ── Policy-Bericht ───────────────────────────────────────────────
    gedeckelt = {
        "lexikalisch_gefunden": len(lex_rows), "lexikalisch_verwendet": min(len(lex_rows), CAP_LEXICAL),
        "walk_gefunden": len(walk_rows), "codependenzen_gefunden": len(rows) if chosen_ids else 0,
        "codependenzen_verwendet": len(codep),
        "resultat_angefordert": budget, "resultat_geliefert": len(treffer),
    }
    pol = Politik(
        caps={"lexical": CAP_LEXICAL, "query_tokens": CAP_QUERY_TOKENS, "anchors": CAP_ANCHORS,
              "walk_hops": CAP_WALK_HOPS, "walk": CAP_WALK, "result_default": CAP_RESULT_DEFAULT,
              "result_max": CAP_RESULT_MAX, "codependenzen": CAP_CODEPENDENZEN,
              "hypothesen": CAP_HYPOTHESEN, "kuration": CAP_KURATION},
        gedeckelt=gedeckelt,
        drop_order=["weiter.extra", "treffer.tail_ueber_budget", "kuration.extra", "hypothesen.tail"],
        nie_gekappt=["gegenseite"],
        plan=plan_source,
    )

    elapsed_us = (time.perf_counter_ns() - started) // 1000
    paket_id = uuid.uuid4().hex[:16]
    orte_refs = [o["ort_id"] for o in orte]
    c.execute(
        "INSERT INTO vp_paket_log(paket_id,zeit,epoch_sekunden,frage,orte_json) VALUES (?,?,?,?,?)",
        (paket_id, _now(), time.time(), text[:200], json.dumps(orte_refs)),
    )

    # Hyperposition: bei AMBIGUOUS/LOW_CONFIDENCE werden die Kandidaten NICHT
    # stillschweigend auf einen zusammengeklappt (Phase 7 des Pulse-Zyklus:
    # "Preservation/reopening of unresolved alternatives"). Sie stehen als
    # offene, ungeloeste Alternativen im Paket -- der Aufrufer entscheidet
    # oder fragt praeziser, statt dass hier fuer ihn geraten wird.
    hyperposition = None
    if resolution.resolution_class in ("AMBIGUOUS", "LOW_CONFIDENCE") and resolution.candidates:
        hyperposition = {
            "zustand": resolution.resolution_class,
            "nicht_kollabiert": True,
            "kandidaten": [{"id": cid, "ref": _ref("artikel", cid)} for cid in resolution.candidates[:8]],
            "grund": "Marge/Score unter Schwelle -- kein Anker gesetzt, kein Walk, keine geratene Wahl.",
        }

    # Phase-4/5-Beobachtungen des Pulse-Zyklus (FRANK_DATABASE_PULSE_CONTRACT.md):
    # explizit auseinandergehalten, nie zusammengeworfen. model_call_count=0 ist
    # hier keine Behauptung, sondern strukturell wahr -- kein Codepfad in diesem
    # Werkzeug ruft ein Modell.
    beobachtungen = {
        "pulse_count": 1, "state_transition_count": 0, "graph_change": 0,
        "hypothesis_count": len(hypothesen), "memory_update": 0,
        "reentry_count": int(cache_hit), "model_call_count": 0, "tool_call_count": None,
        "effect_count": 0, "environment_observation_count": 0,
        "time_in_state_us": int(elapsed_us), "situated_state_change_count": 0,
    }

    result = {
        "paket_id": paket_id,
        "autoritaet": "CONTEXT_ONLY",   # ClayGraph-Aktivierung wird NIE zu Wahrheit, nur weil sie hoch war
        "pulse_phase": "4+5 (Aktivierung/Relevanz-Propagation + Hypothesen/Codependenz/Alternativen) -- "
                       "erzeugt eine begrenzte, herkunftstragende Assembly fuer Phase 6 (Auswahl/Routing). "
                       "Selektion/Routing/Effekt liegen NICHT in diesem Werkzeug.",
        "treffer": treffer,
        "hyperposition": hyperposition,
        "orte": orte,
        "systeme": system_eintraege,
        "codependenzen": codep,
        "hypothesen": hypothesen,
        "gegenseite": gegenseite,
        "kuration": kur,
        "weiter": weiter,
        "politik": pol.to_dict(),
        "beobachtungen": beobachtungen,
        "resolution": {"klasse": resolution.resolution_class, "konfidenz": resolution.confidence,
                       "anker": list(anchors), "gap_terms": list(terms)},
        "basis": {"source_epoch": source_epoch, "graph_epoch": graph_epoch, "sig_hash": sig_hash,
                  "cache_hit": cache_hit},
        "latenz_us": int(elapsed_us),
    }
    if lauf_id:
        for t in treffer:
            c.execute("INSERT INTO vp_gesehen(lauf,record_id,zeit) VALUES (?,?,?)", (lauf_id, t["id"], _now()))
    # Echtes Lernsignal: NUR aus einem Cache-Treffer (eine Signatur, die schon
    # einmal echt gebraucht wurde) -- nie aus der eigenen Ausgabe dieses Laufs.
    if cache_hit:
        lernen(c, result, war_treffer=True)
    c.commit()
    if own:
        c.close()
    return result


# ── Lernen (beschraenkt, rueckgaengig zu machen) ────────────────────────

def lernen(c: sqlite3.Connection, package: dict, war_treffer: bool) -> None:
    """Lernt NUR aus Cache-Treffern (also aus bereits verifizierten Signaturen),
    NIE aus dem eigenen Ausgabetext. gewicht wird gedeckelt, nie unbegrenzt."""
    if not war_treffer:
        return
    edge_arts = {e["art"] for e in package.get("codependenzen", [])}
    for art in edge_arts:
        row = c.execute(
            "SELECT gewicht,beobachtungen FROM vp_edge_lern WHERE query_class='global' AND edge_art=?",
            (art,),
        ).fetchone()
        g, n = (row["gewicht"], row["beobachtungen"]) if row else (0.0, 0)
        g = min(3.0, g + 0.1)
        n += 1
        c.execute(
            "INSERT INTO vp_edge_lern(query_class,edge_art,gewicht,beobachtungen,zuletzt_gelernt) "
            "VALUES ('global',?,?,?,?) " "ON CONFLICT(query_class,edge_art) DO UPDATE SET gewicht=excluded.gewicht, beobachtungen=excluded.beobachtungen, zuletzt_gelernt=excluded.zuletzt_gelernt", (art, g, n, _now()),
        )
    c.commit()


def verfall(c: sqlite3.Connection) -> int:
    """Verfall: multiplikativ mit HOP_DECAY. Alte Treffer duerfen nicht fuer immer
    dominieren. Zahl wiederverwendet aus dem ClayGraph-Kandidaten, nicht neu erfunden."""
    c.execute("UPDATE vp_edge_lern SET gewicht = gewicht * ?", (HOP_DECAY,))
    n = c.execute("SELECT changes()").fetchone()[0]
    c.commit()
    return n


# ── Eichung: eigene Normale bewerten (misst gegen den Massstab, baut ihn nicht) ──

def normalen_score() -> tuple[str, bool]:
    """Ruft eichung.py pruefen auf und liest das Ergebnis. Baut KEIN eigenes
    Scoreboard -- das waere derselbe Fehler wie ein Messgeraet, das sich selbst eicht."""
    try:
        r = subprocess.run(["python3", "/opt/clayverse/werkzeug/eichung.py", "pruefen"],
                           capture_output=True, text=True, timeout=90)
        out = (r.stdout + r.stderr)
        m = re.search(r"(\d+)/(\d+) belegt", out)
        if m:
            passed, total = int(m.group(1)), int(m.group(2))
            return f"{passed}/{total}", (r.returncode == 0)
        return "UNBEKANNT", False
    except Exception as e:
        return f"FEHLER:{e}", False


# ── Snapshot + Heilung ───────────────────────────────────────────────────

def _state_hash(c: sqlite3.Connection) -> str:
    rows = c.execute("SELECT query_class,edge_art,gewicht,beobachtungen FROM vp_edge_lern ORDER BY query_class,edge_art").fetchall()
    blob = json.dumps([tuple(r) for r in rows], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def schnappschuss(c: sqlite3.Connection, *, mit_normalen: bool = True) -> dict:
    score, bestanden = normalen_score() if mit_normalen else ("UEBERSPRUNGEN", True)
    rows = c.execute("SELECT query_class,edge_art,gewicht,beobachtungen,zuletzt_gelernt FROM vp_edge_lern").fetchall()
    dump = json.dumps([dict(r) for r in rows])
    total_obs = sum(r["beobachtungen"] for r in rows)
    sh = _state_hash(c)
    se, ge = _source_epoch(c), _graph_epoch(c)
    c.execute(
        "INSERT INTO vp_snapshot(erzeugt_am,state_hash,normals_score,normals_bestanden,"
        "beobachtungen_gesamt,edge_lern_snapshot,source_epoch,graph_epoch) VALUES (?,?,?,?,?,?,?,?)",
        (_now(), sh, score, int(bestanden), total_obs, dump, se, ge),
    )
    sid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.execute("INSERT INTO vp_ereignis(zeit,art,detail) VALUES (?,?,?)",
              (_now(), "snapshot", json.dumps({"snapshot_id": sid, "state_hash": sh, "normals": score})))
    c.commit()
    return {"snapshot_id": sid, "state_hash": sh, "normals_score": score, "normals_bestanden": bestanden,
            "beobachtungen_gesamt": total_obs, "source_epoch": se, "graph_epoch": ge}


def heilen(c: sqlite3.Connection) -> dict:
    """Rollt zurueck zum NEUESTEN Schnappschuss der die Normale bestand. Ausgeloest
    durch fehlgeschlagene Normale, NIE durch ein Gefuehl von 'schlechter'. Heilung
    ohne Eintrag ist nicht von einem Bug zu unterscheiden."""
    row = c.execute(
        "SELECT * FROM vp_snapshot WHERE normals_bestanden=1 ORDER BY snapshot_id DESC LIMIT 1"
    ).fetchone()
    if row is None:
        detail = {"ergebnis": "kein bestandener Schnappschuss vorhanden -- keine Heilung moeglich"}
        c.execute("INSERT INTO vp_ereignis(zeit,art,detail) VALUES (?,?,?)", (_now(), "heilung_fehlgeschlagen", json.dumps(detail)))
        c.commit()
        return detail
    vorher = _state_hash(c)
    daten = json.loads(row["edge_lern_snapshot"])
    c.execute("DELETE FROM vp_edge_lern")
    for e in daten:
        c.execute("INSERT INTO vp_edge_lern(query_class,edge_art,gewicht,beobachtungen,zuletzt_gelernt) VALUES (?,?,?,?,?)",
                  (e["query_class"], e["edge_art"], e["gewicht"], e["beobachtungen"], e["zuletzt_gelernt"]))
    nachher = _state_hash(c)
    detail = {"zurueck_zu_snapshot": row["snapshot_id"], "state_hash_vorher": vorher,
              "state_hash_nachher": nachher, "normals_score_des_ziels": row["normals_score"]}
    c.execute("INSERT INTO vp_ereignis(zeit,art,detail) VALUES (?,?,?)", (_now(), "heilung", json.dumps(detail)))
    c.commit()
    return detail


# ── MESSUNG: grep / fts / voll / paket, gleiche Definition von "Faktum" ─
#
# Ein "belegtes Faktum" ist hier ueberall dieselbe Sache: eine Zeile aus
# {kante, folgerung MIT Beleg, kuration, artikel MIT epistemic_class != NULL},
# die im jeweiligen Ergebnis auftaucht. grep liefert strukturell NIE ein
# Faktum in diesem Sinn (0 ueberall, wie in der Vorgabe belegt). fts liefert
# nur Artikel-Treffer (kein Join). voll und paket liefern denselben
# strukturellen Umfang -- der einzige Unterschied ist Volltext vs. ID+Feld.

BAEUME_PFAD = "/opt/clayverse/baeume/clay-global-research-entity/research_entity"


def _messen_grep(term: str) -> dict:
    """Echtes grep -r (Zeileninhalt, nicht nur Dateinamen) -- liest Dateien, UM zu
    suchen (genau das Muster, das der Auftrag verbietet, hier als Baseline)."""
    t0 = time.perf_counter_ns()
    try:
        r = subprocess.run(["grep", "-rn", term, BAEUME_PFAD], capture_output=True, text=True, timeout=90)
        matched_lines = r.stdout
        total_bytes = len(matched_lines.encode("utf-8"))
        n_lines = matched_lines.count("\n")
    except Exception:
        matched_lines, total_bytes, n_lines = "", 0, 0
    us = (time.perf_counter_ns() - t0) // 1000
    return {"methode": "grep", "latenz_us": us, "bytes": total_bytes, "belegte_fakten": 0,
            "treffer_zeilen": n_lines, "payload": matched_lines}


def _artikel_epistemic_ids(c: sqlite3.Connection, ids: Iterable[str]) -> set[str]:
    ids = list(ids)
    if not ids:
        return set()
    qmarks = ",".join("?" for _ in ids)
    rows = c.execute(f"SELECT id FROM artikel WHERE id IN ({qmarks}) AND epistemic_class IS NOT NULL", ids).fetchall()
    return {r["id"] for r in rows}


def _messen_fts(c: sqlite3.Connection, tokens: list[str], limit: int = 20) -> dict:
    t0 = time.perf_counter_ns()
    rows = c.execute(
        """SELECT s.artikel_id AS aid, fts_index_artikel.titel AS titel, fts_index_artikel.text AS text
           FROM fts_index_artikel JOIN artikel_suchtext s ON s.id = fts_index_artikel.rowid
           WHERE fts_index_artikel MATCH ? LIMIT ?""",
        (_fts_query(tokens), limit),
    ).fetchall()
    us = (time.perf_counter_ns() - t0) // 1000
    payload_text = "\n\n".join(f"{r['titel']}\n{r['text']}" for r in rows)
    total_bytes = len(payload_text.encode("utf-8"))
    fakten = _artikel_epistemic_ids(c, {r["aid"] for r in rows})
    return {"methode": "fts", "latenz_us": us, "bytes": total_bytes, "belegte_fakten": len(fakten),
            "treffer_artikel": len(rows), "payload": payload_text}


def _messen_voll(c: sqlite3.Connection, text: str, limit: int = 20) -> dict:
    """Volltext + alle strukturellen Zusammenhaenge, UNKOMPRIMIERT (Baseline)."""
    t0 = time.perf_counter_ns()
    tokens = _tokens(text)
    resolution = resolve_entities(c, tokens, text.strip())
    anchors = resolution.anchors
    fts_rows = c.execute(
        """SELECT s.artikel_id AS aid, fts_index_artikel.titel AS titel, fts_index_artikel.text AS text
           FROM fts_index_artikel JOIN artikel_suchtext s ON s.id = fts_index_artikel.rowid
           WHERE fts_index_artikel MATCH ? LIMIT ?""",
        (_fts_query(tokens), limit),
    ).fetchall()
    ids = {r["aid"] for r in fts_rows} | set(anchors)
    walked_ids: set[str] = set()
    for a in anchors[:CAP_ANCHORS]:
        for w in _walk(c, a, {}):
            walked_ids.add(w["record_id"])
    ids |= walked_ids
    teile = [f"{r['titel']}\n{r['text']}" for r in fts_rows]

    kante_rows, folg_rows, kur_rows = [], [], []
    if ids:
        qmarks = ",".join("?" for _ in ids)
        kante_rows = c.execute(f"SELECT von,nach,art,beleg FROM kante WHERE von IN ({qmarks}) OR nach IN ({qmarks})",
                                list(ids) * 2).fetchall()
        kur_rows = c.execute(f"SELECT artikel_id,quelle,ereignis,klasse FROM kuration WHERE status='offen' AND artikel_id IN ({qmarks})",
                              list(ids)).fetchall()
        hyp, geg = _folgerungen_fuer(c, ids)
        folg_rows = hyp + geg
    for r in kante_rows:
        teile.append(f"{r['von']} -{r['art']}-> {r['nach']} :: {r['beleg'] or ''}")
    for r in kur_rows:
        teile.append(f"{r['artikel_id']} {r['klasse']}: {r['ereignis'] or ''}")
    for r in folg_rows:
        teile.append(r.get("aussage") or "")
    payload_text = "\n\n".join(teile)
    total_bytes = len(payload_text.encode("utf-8"))
    us = (time.perf_counter_ns() - t0) // 1000
    fakten_epistemic = _artikel_epistemic_ids(c, ids)
    belegte_fakten = len(fakten_epistemic) + len(kante_rows) + len(kur_rows) + len(folg_rows)
    return {"methode": "voll", "latenz_us": us, "bytes": total_bytes, "belegte_fakten": belegte_fakten,
            "treffer_artikel": len(fts_rows), "kante": len(kante_rows), "kuration": len(kur_rows),
            "folgerung": len(folg_rows), "payload": payload_text}


def _messen_paket(c: sqlite3.Connection, text: str, budget: int = CAP_RESULT_DEFAULT) -> dict:
    t0 = time.perf_counter_ns()
    pkt = paket(text, budget=budget, conn=c)
    us = (time.perf_counter_ns() - t0) // 1000
    payload = {k: pkt[k] for k in ("treffer", "codependenzen", "hypothesen", "gegenseite", "kuration", "weiter")}
    payload_bytes = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    epistemic_ids = {t["id"] for t in pkt["treffer"] if t.get("epistemic_class")}
    belegte_fakten = (len(epistemic_ids) + len(pkt["codependenzen"]) + len(pkt["kuration"])
                      + len(pkt["hypothesen"]) + len(pkt["gegenseite"]))
    return {"methode": "paket", "latenz_us": us, "bytes": payload_bytes, "belegte_fakten": belegte_fakten,
            "treffer": len(pkt["treffer"]), "resolution": pkt["resolution"]["klasse"],
            "cache_hit": pkt["basis"]["cache_hit"], "payload": payload}


def vergleichsmessung(fragen: list[str], out_path: Optional[str] = None) -> dict:
    c = _connect()
    _ensure_vp_tables(c)
    ergebnisse = []
    for f in fragen:
        tokens = _tokens(f)
        g = _messen_grep(" OR ".join(tokens[:3]) if tokens else f.split()[0])
        # grep braucht EIN Suchwort; nimm das laengste Token als Stellvertreter
        haupt = max(tokens, key=len) if tokens else f
        g = _messen_grep(haupt)
        fts = _messen_fts(c, tokens)
        voll = _messen_voll(c, f)
        pk = _messen_paket(c, f)
        ergebnisse.append({"frage": f, "grep": g, "fts": fts, "voll": voll, "paket": pk})
    c.close()
    out = {"fragen_anzahl": len(fragen), "ergebnisse": ergebnisse}
    if out_path:
        Path(out_path).write_text(json.dumps(out, ensure_ascii=False, indent=2))
    return out


# ── MESSUNG: Plan-Cache kalt/warm, Paraphrasen-Trefferquote ─────────────

def cache_messung(gruppen: list[list[str]]) -> dict:
    """gruppen: Liste von Paraphrasen-Gruppen (je 3 Umschreibungen derselben Frage)."""
    c = _connect()
    _ensure_vp_tables(c)
    ergebnisse = []
    for gruppe in gruppen:
        laeufe = []
        for text in gruppe:
            pk = paket(text, conn=c)
            laeufe.append({"text": text, "cache_hit": pk["basis"]["cache_hit"],
                           "sig_hash": pk["basis"]["sig_hash"], "latenz_us": pk["latenz_us"],
                           "resolution": pk["resolution"]["klasse"], "anker": pk["resolution"]["anker"],
                           "gap_terms": pk["resolution"]["gap_terms"]})
        hits = sum(1 for l in laeufe[1:] if l["cache_hit"])
        ergebnisse.append({"gruppe": gruppe, "laeufe": laeufe, "warme_treffer_von": f"{hits}/{len(gruppe)-1}"})
    c.close()
    gesamt_hits = sum(int(e["warme_treffer_von"].split("/")[0]) for e in ergebnisse)
    gesamt_moeglich = sum(int(e["warme_treffer_von"].split("/")[1]) for e in ergebnisse)
    return {"gruppen": ergebnisse, "trefferquote": f"{gesamt_hits}/{gesamt_moeglich}"}


# ── MESSUNG: Kaskaden-Effekt (Abdeckung 0->1, Latenz faellt) ────────────

def kaskaden_messung(anker_liste: list[str], wiederholungen: int = 3) -> dict:
    """Ruft dieselben Anker mehrfach auf. Erster Lauf je Anker = kalt (Walk+FTS),
    Folgelaeufe = warm (Cache). Zeigt die 'wird schneller mit Nutzung' Kurve."""
    c = _connect()
    _ensure_vp_tables(c)
    kurve = []
    abdeckung_getroffen = 0
    for i, anker in enumerate(anker_liste):
        for w in range(wiederholungen):
            pk = paket(anker, conn=c)
            if pk["basis"]["cache_hit"]:
                abdeckung_getroffen += 1
            kurve.append({"anker": anker, "wiederholung": w, "cache_hit": pk["basis"]["cache_hit"],
                         "latenz_us": pk["latenz_us"]})
    c.close()
    return {"kurve": kurve}


# ── MESSUNG: Anti-Degeneration -- Entropie, Erreichbarkeit, Normale, Cache ──

def degenerations_simulation(fragen: list[str], zyklen: int = 5) -> dict:
    """Simuliert Nutzung ueber `zyklen` Runden. Nach jeder Runde: lernen() aus
    Cache-Treffern, Verfall, Schnappschuss. Misst je Runde: Entropie der
    zurueckgegebenen ids (Cluster), Anteil des Korpus der ueberhaupt erreichbar
    war (kumulativ ueber alle bisherigen Läufe), Normale-Score, Cache-Trefferquote."""
    c = _connect()
    _ensure_vp_tables(c)
    gesamt_ids: set[str] = set()
    korpusgroesse = c.execute("SELECT COUNT(*) FROM artikel").fetchone()[0]
    kurve = []
    for runde in range(zyklen):
        lauf_id = f"deg-{runde}"
        runden_ids: list[str] = []
        cluster_counter: Counter = Counter()
        hits = 0
        for f in fragen:
            pk = paket(f, conn=c, lauf_id=lauf_id)
            if pk["basis"]["cache_hit"]:
                hits += 1
            lernen(c, pk, war_treffer=pk["basis"]["cache_hit"])
            for t in pk["treffer"]:
                runden_ids.append(t["id"])
                cluster_counter[t.get("projekt") or t.get("art") or "unbekannt"] += 1
        gesamt_ids |= set(runden_ids)
        n = sum(cluster_counter.values())
        entropie = 0.0
        if n:
            for cnt in cluster_counter.values():
                p = cnt / n
                entropie -= p * math.log2(p)
        verfall(c)
        snap = schnappschuss(c, mit_normalen=False)
        kurve.append({
            "runde": runde,
            "entropie_bits": round(entropie, 4),
            "cluster_anzahl": len(cluster_counter),
            "erreichbar_kumulativ": len(gesamt_ids),
            "erreichbar_anteil_korpus": round(len(gesamt_ids) / korpusgroesse, 6),
            "cache_trefferquote": f"{hits}/{len(fragen)}",
            "snapshot": snap,
        })
    c.close()
    return {"zyklen": zyklen, "korpusgroesse": korpusgroesse, "kurve": kurve}


def ort_dichte_messung() -> dict:
    """Dieselbe Dichte-Messung (Fakten je 1000 Token) wie fuer Artikel, jetzt fuer
    Datei-Orte. grep bezahlt vollen Preis fuer Pfade; das Paket antwortet strukturiert."""
    c = _connect(); _ensure_vp_tables(c)
    frage = "wo liegen die Needle-Gewichte / needle-Artefakte, auf welchem Wirt, welcher Pfad, wie gross?"
    g = _messen_grep("needle")
    t0 = time.perf_counter_ns()
    pk = paket(frage, conn=c)
    us = (time.perf_counter_ns() - t0) // 1000
    payload = {"orte": pk["orte"], "weiter": pk["weiter"]}
    payload_bytes = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    fakten = sum(
        len(e["orte"]) + len(e["codependenzen"]["artikel"]) + len(e["codependenzen"]["taetigkeit"])
        + len(e["codependenzen"]["geschwister"])
        for e in pk["orte"]
    )
    c.close()
    return {"frage": frage, "grep": g,
            "paket": {"methode": "paket_ort", "latenz_us": us, "bytes": payload_bytes,
                     "belegte_fakten": fakten, "orte_gefunden": len(pk["orte"])}}


# ── Akzeptanztest: "wo liegen die Needle-Gewichte" ──────────────────────

# ── SYSTEM: dritte Eintragsart -- Wirte, Hardware, Wege, Alter ──────────
#
# Quellen bereits vorhanden, alle gemessen, nichts erfunden: wirte.json
# (ip/konto/hostname/geprueft), /var/lib/clay/karte/<wirt>-<zeit>.json
# (hardware/disks/usb/netz/horchend/dienste/benutzer, alle 15 Min. erneuert),
# `weg` (bewiesene Routen mit Alter+Beleg). Ein alter Hardware-Fund ist nur MIT
# seinem Alter brauchbar -- ein toter Wirt erscheint als bekannt-tot mit seinem
# Fehler, nie als Leere.
#
# Blasenregel, ehrlich eingeschraenkt: wirte.json traegt HIER nur die eigenen
# vier Wirte (ai-core-node-projekt-frankenstein, andreas-MACO, clayverse,
# clayverse-alt) -- keine Mandanten-/Kunden-Kennung im Datensatz. Eine echte
# Mandantentrennung wurde NICHT gebaut, weil die Quelle kein Merkmal dafuer
# hat -- das zu erfinden waere Erfindung von Metadaten, kein Befund.
CAP_SYSTEME = 8
KARTE_PFAD = Path("/var/lib/clay/karte")
WIRTE_JSON = Path("/var/lib/clay/wirte.json")


def _wirte_laden() -> dict:
    if not WIRTE_JSON.exists():
        return {}
    try:
        return json.loads(WIRTE_JSON.read_text()).get("wirte", {})
    except Exception:
        return {}


def _neueste_karte(wirt: str) -> Optional[dict]:
    kand = sorted(KARTE_PFAD.glob(f"{wirt}-*.json")) if KARTE_PFAD.exists() else []
    if not kand:
        return None
    try:
        d = json.loads(kand[-1].read_text())
        d["_datei"] = kand[-1].name
        return d
    except Exception:
        return None


def systeme(c: sqlite3.Connection, budget: int = CAP_SYSTEME) -> list[dict]:
    wirte = _wirte_laden()
    out = []
    jetzt = time.time()
    for name, meta in list(wirte.items())[:budget]:
        karte = _neueste_karte(name)
        eintrag = {"wirt": name, "ip": meta.get("ip"), "konto": meta.get("konto"),
                   "hostname": meta.get("hostname"), "geprueft": meta.get("geprueft"),
                   "ref": _ref("wirt", name)}
        if karte:
            alter_s = None
            try:
                t = time.strptime(karte.get("zeit", "")[:19], "%Y-%m-%dT%H:%M:%S")
                alter_s = jetzt - time.mktime(t)
            except Exception:
                pass
            eintrag.update({
                "erreichbar": karte.get("erreichbar"),
                "hardware": karte.get("hardware"),
                "disks_anzahl": len(karte.get("disks", []) or []),
                "dienste_anzahl": len(karte.get("dienste", []) or []),
                "horchend_anzahl": len(karte.get("horchend", []) or []),
                "karte_alter_sekunden": round(alter_s) if alter_s is not None else None,
                "karte_datei": karte.get("_datei"),
            })
        else:
            eintrag["erreichbar"] = None
            eintrag["befund"] = "keine Karte gefunden -- Stand unbekannt, nicht erfunden"
        try:
            wege = c.execute(
                "SELECT ursprung,transport,erreichbar,fehler,zuletzt_bewiesen FROM weg "
                "WHERE ziel_wirt=? ORDER BY zuletzt_bewiesen DESC LIMIT 3",
                (name,),
            ).fetchall()
            eintrag["wege"] = [{"von": w["ursprung"], "transport": w["transport"],
                               "erreichbar": bool(w["erreichbar"]), "fehler": w["fehler"],
                               "bewiesen_am": w["zuletzt_bewiesen"]} for w in wege]
        except sqlite3.OperationalError:
            eintrag["wege"] = []
        out.append(eintrag)
    return out


# ── Puls: EIN Zyklusschritt (Delta -> Lernen -> Kuration), keine Uhr ────
#
# NICHT gebaut: der volle 12-Phasen-Zyklus, der 4-Sekunden-Daemon, ein
# systemd-Timer. Zeitbudget-Entscheidung, hier ehrlich benannt. Gebaut: EIN
# aufrufbarer Schritt, der die geforderte Eigenschaft PRUEFBAR macht -- billiger
# Leerlauf ohne Delta, teurer Pfad nur bei echtem Delta -- damit ein spaeterer
# Timer diese Funktion einfach alle 4s aufrufen kann, ohne dass hier vorab neu
# gebaut werden muesste. `kuration.rowid` als Fortschrittsmarke: die Tabelle hat
# keinen deklarierten Integer-PK, rowid ist der ehrlichste verfuegbare Zaehler.
# Wie lange zwischen zwei Leermeldungen mindestens liegen muss. 900 s bei 4 s
# Takt heisst: eine Zeile je ~225 Leertakte statt 225 Zeilen.
LEER_BUENDEL_S = 900.0


def puls(c: sqlite3.Connection) -> dict:
    _ensure_vp_tables(c)
    t0 = time.perf_counter()
    letzter = c.execute("SELECT value FROM vp_alias_meta WHERE key='puls_letzte_kuration_rowid'").fetchone()
    seit = int(letzter[0]) if letzter else 0
    neu = c.execute("SELECT rowid,artikel_id,klasse,status FROM kuration WHERE rowid > ? ORDER BY rowid", (seit,)).fetchall()
    if not neu:
        us = (time.perf_counter() - t0) * 1e6
        # ⭐⭐ LEERTAKTE WERDEN GEBUENDELT, NICHT EINZELN GESCHRIEBEN.
        # Gemessen 2026-08-21: `vp_ereignis` hielt **128.109 Zeilen `puls_leer`
        # gegen 195 `puls_arbeit`** -- 99,8 % der Eintraege sagen "nichts
        # passiert". Bei 4 s Takt sind das ~20.000 Schreibvorgaenge mit Commit
        # pro Tag, und zwar auf genau die Datei, deren WAL sich nicht
        # zuruecksetzen laesst, solange ein Leser offen ist (und es ist immer
        # einer offen). Ergebnis: der WAL wuchs auf 17,5 GB, die Platte lief auf
        # 87 %, echte Zuege scheiterten an "database is locked", und der Puls
        # verlor 48 % seiner eigenen Takte die Datenbank -- er hat sich das
        # Problem selbst gebaut, indem er seine Untaetigkeit protokollierte.
        #
        # Der BELEG bleibt erhalten und ist sogar besser als vorher: die Zeile
        # traegt jetzt, wie lange seit der letzten Leermeldung vergangen ist.
        # Daraus ergibt sich die Zahl der Takte (Abstand / Taktdauer), ohne je
        # Takt eine Zeile zu kosten. Aus 20.000 Schreibvorgaengen taeglich
        # werden 96.
        letzte = c.execute(
            "SELECT zeit FROM vp_ereignis WHERE art='puls_leer' "
            "ORDER BY rowid DESC LIMIT 1").fetchone()
        # ⚠️ `_now()` liefert einen ISO-Zeitstempel als TEXT, keinen Unix-Wert.
        # Erster Anlauf rechnete `float(_now())` -- das wirft, der Rueckfall
        # setzte "unbekannt", und die Buendelung haette NIE gegriffen. Genau die
        # Sorte stiller Nulleffekt, die wir heute schon dreimal hatten.
        vergangen = None
        if letzte and letzte[0]:
            try:
                from datetime import datetime as _dt
                vorher = _dt.strptime(str(letzte[0]), "%Y-%m-%dT%H:%M:%S%z")
                jetzt = _dt.strptime(_now(), "%Y-%m-%dT%H:%M:%S%z")
                vergangen = round((jetzt - vorher).total_seconds(), 1)
            except (TypeError, ValueError):
                vergangen = None
        if vergangen is None or vergangen >= LEER_BUENDEL_S:
            c.execute("INSERT INTO vp_ereignis(zeit,art,detail) VALUES (?,?,?)",
                      (_now(), "puls_leer", json.dumps(
                          {"kosten_us": round(us, 1), "seit_letzter_s": vergangen})))
            c.commit()
        return {"art": "leer", "delta": 0, "kosten_us": round(us, 1)}

    betroffene: Counter = Counter()
    ids = [r["artikel_id"] for r in neu]
    qm = ",".join("?" for _ in ids)
    for k in c.execute(f"SELECT art FROM kante WHERE von IN ({qm}) OR nach IN ({qm})", ids * 2):
        betroffene[k["art"]] += 1
    for art, n in betroffene.items():
        row = c.execute("SELECT gewicht,beobachtungen FROM vp_edge_lern WHERE query_class='global' AND edge_art=?", (art,)).fetchone()
        g, b = (row["gewicht"], row["beobachtungen"]) if row else (0.0, 0)
        g = min(3.0, g + 0.02 * n)
        b += n
        c.execute("INSERT INTO vp_edge_lern(query_class,edge_art,gewicht,beobachtungen,zuletzt_gelernt) "
                  "VALUES ('global',?,?,?,?) " "ON CONFLICT(query_class,edge_art) DO UPDATE SET gewicht=excluded.gewicht, beobachtungen=excluded.beobachtungen, zuletzt_gelernt=excluded.zuletzt_gelernt", (art, g, b, _now()))
    letzte_rowid = max(r["rowid"] for r in neu)
    c.execute("INSERT OR REPLACE INTO vp_alias_meta(key,value) VALUES ('puls_letzte_kuration_rowid',?)", (str(letzte_rowid),))
    us = (time.perf_counter() - t0) * 1e6
    c.execute("INSERT INTO vp_ereignis(zeit,art,detail) VALUES (?,?,?)",
              (_now(), "puls_arbeit", json.dumps({"delta": len(neu), "arten": dict(betroffene), "kosten_us": round(us, 1)})))
    c.commit()
    return {"art": "arbeit", "delta": len(neu), "betroffene_kantenarten": dict(betroffene), "kosten_us": round(us, 1)}


def needle_test() -> dict:
    c = _connect(); _ensure_vp_tables(c)
    frage = "wo liegen die Needle-Gewichte / needle-Artefakte, auf welchem Wirt, welcher Pfad, wie gross?"
    t0 = time.perf_counter_ns()
    pk = paket(frage, conn=c)
    ms = (time.perf_counter_ns() - t0) / 1e6
    payload = {"orte": pk["orte"], "weiter": pk["weiter"]}
    payload_bytes = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    gefunden_wirte = sorted({o["wirt"] for e in pk["orte"] for o in e["orte"]})
    gewicht_dateien = [e for e in pk["orte"]
                      if any((e["inhalt"]["titel"] or "").lower().endswith(ext) for ext in _GEWICHT_EXT)]
    hand_erwartet = {"mini_train.jsonl", "mini_val.jsonl", "registry.json"}
    hand_bestaetigt = sorted({e["inhalt"]["titel"] for e in pk["orte"] if e["inhalt"]["titel"] in hand_erwartet})

    befund = {
        "frage": frage, "latenz_ms": round(ms, 3), "payload_bytes": payload_bytes,
        "paket_id": pk["paket_id"], "gefundene_dateien": len(pk["orte"]),
        "wirte_gesehen": gefunden_wirte,
        "handrecherche_bestaetigt": hand_bestaetigt,
        "handrecherche_vollstaendig_bestaetigt": set(hand_bestaetigt) == hand_erwartet,
        "gewichtsdateien_pt_safetensors_onnx_etc": [
            {"titel": e["inhalt"]["titel"], "orte": e["orte"]} for e in gewicht_dateien
        ],
        "befund_gewichte": ("KEINE .pt/.safetensors/.onnx/... Gewichtsdatei mit 'needle' im Namen im Index "
                            "gefunden -- bestaetigt die Handrecherche (kein Widerspruch)." if not gewicht_dateien
                            else f"{len(gewicht_dateien)} Gewichtsdatei(en) gefunden -- widerspricht der Handrecherche."),
        "index_stand": {"wirt_verteilung": {r["wirt"]: r["n"] for r in c.execute(
            "SELECT wirt, COUNT(*) AS n FROM fundort GROUP BY wirt")}},
    }
    c.close()
    return befund


def beweis_verweigerung() -> dict:
    """Zeigt: kein Lesen ohne Paket, kein Lesen ohne Nennung, kein Lesen von Binaer
    ohne Ausnahme -- und dann ein erlaubtes Lesen. Kein Read fand vorher statt."""
    c = _connect(); _ensure_vp_tables(c)
    pk = paket("registry.json needle Registry Konfiguration", conn=c)
    text_orte = [o for o in pk["orte"] if o["inhalt"]["ist_text"]]
    faelle = []
    faelle.append({"fall": "unbekannte paket_id", "ergebnis": lesen("d1", "nicht-existent-xyz", conn=c)})
    if pk["orte"]:
        fremder_ort = "d999999999"
        faelle.append({"fall": "ort_id die das Paket nicht nannte", "ergebnis": lesen(fremder_ort, pk["paket_id"], conn=c)})
    if text_orte:
        ziel = text_orte[0]
        faelle.append({"fall": "erlaubt (Paket nannte den Ort, Text, unter Groessendeckel)",
                       "ort_id": ziel["ort_id"],
                       "ergebnis": lesen(ziel["ort_id"], pk["paket_id"], conn=c)})
    else:
        faelle.append({"fall": "kein Text-Ort im Paket gefunden fuer den positiven Fall", "ergebnis": None})
    c.close()
    return {"paket_id": pk["paket_id"], "gefundene_orte": [o["ort_id"] for o in pk["orte"]], "faelle": faelle}


def lese_kosten_vergleich(fragen: list[str]) -> dict:
    """ms/Token: Paket allein vs. Paket+ein autorisiertes Lesen. Und die Quote
    'Paket beantwortete es, kein Lesen noetig' vs 'Lesen war noetig'."""
    c = _connect(); _ensure_vp_tables(c)
    ergebnisse = []
    kein_lesen_noetig = 0
    for f, braucht_lesen in fragen:
        t0 = time.perf_counter_ns()
        pk = paket(f, conn=c)
        ms_paket = (time.perf_counter_ns() - t0) / 1e6
        payload = {k: pk[k] for k in ("treffer", "orte", "codependenzen", "hypothesen", "gegenseite", "kuration", "weiter")}
        bytes_paket = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        eintrag = {"frage": f, "braucht_lesen_lt_testfall": braucht_lesen,
                  "ms_paket_allein": round(ms_paket, 3), "bytes_paket_allein": bytes_paket}
        if braucht_lesen and pk["orte"]:
            ziel = next((o for o in pk["orte"] if o["inhalt"]["ist_text"]), None)
            if ziel:
                t1 = time.perf_counter_ns()
                r = lesen(ziel["ort_id"], pk["paket_id"], conn=c)
                ms_lesen = (time.perf_counter_ns() - t1) / 1e6
                eintrag["ms_paket_plus_lesen"] = round(ms_paket + ms_lesen, 3)
                eintrag["bytes_mit_lesen"] = bytes_paket + (r.get("bytes", 0) if r.get("erlaubt") else 0)
                eintrag["lesen_erlaubt"] = r.get("erlaubt")
        else:
            kein_lesen_noetig += 1
        ergebnisse.append(eintrag)
    c.close()
    n = len(fragen)
    return {"ergebnisse": ergebnisse,
            "quote_paket_reicht": f"{kein_lesen_noetig}/{n}",
            "quote_lesen_noetig": f"{n - kein_lesen_noetig}/{n}"}


# ── Beweis: drei Schritte "weiter" ohne neue Suche ──────────────────────

def beweis_schleife(start_text: str, schritte: int = 3) -> dict:
    c = _connect()
    _ensure_vp_tables(c)
    kette = []
    pk = paket(start_text, conn=c)
    kette.append({"schritt": 0, "eingabe": start_text, "quelle": "SUCHE", "treffer": [t["id"] for t in pk["treffer"]],
                 "weiter_verfuegbar": sum(len(w["naechste"]) for w in pk["weiter"])})
    naechste_kandidaten = [n["id"] for w in pk["weiter"] for n in w["naechste"]]
    for s in range(1, schritte + 1):
        if not naechste_kandidaten:
            kette.append({"schritt": s, "befund": "keine weiteren Kandidaten in 'weiter' -- Kette endet"})
            break
        naechste_id = naechste_kandidaten[0]
        pk = paket(naechste_id, conn=c)  # id direkt als Text -> EXACT_ID Aufloesung, KEINE neue Volltextsuche
        kette.append({"schritt": s, "eingabe_id": naechste_id, "quelle": "WEITER (keine neue Suche)",
                     "resolution": pk["resolution"]["klasse"], "treffer": [t["id"] for t in pk["treffer"]],
                     "weiter_verfuegbar": sum(len(w["naechste"]) for w in pk["weiter"])})
        naechste_kandidaten = [n["id"] for w in pk["weiter"] for n in w["naechste"]]
    c.close()
    return {"kette": kette}


# ── CLI ──────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd")

    p1 = sub.add_parser("paket", help="ein Paket fuer eine Frage")
    p1.add_argument("text")
    p1.add_argument("--budget", type=int, default=CAP_RESULT_DEFAULT)

    sub.add_parser("schnappschuss")
    sub.add_parser("heilen")
    sub.add_parser("verfall")

    p2 = sub.add_parser("messen")
    p2.add_argument("--out", default=None)

    p3 = sub.add_parser("cache-messen")
    p4 = sub.add_parser("degeneration")
    p4.add_argument("--zyklen", type=int, default=5)
    p5 = sub.add_parser("beweis")
    p5.add_argument("text")

    sub.add_parser("needle-test")
    sub.add_parser("beweis-verweigerung")
    sub.add_parser("lese-kosten")
    sub.add_parser("ort-messen")
    sub.add_parser("systeme")
    p7 = sub.add_parser("puls")
    p7.add_argument("--wiederholungen", type=int, default=1)

    p6 = sub.add_parser("lesen")
    p6.add_argument("ort_id")
    p6.add_argument("paket_id")

    args = ap.parse_args()
    if args.cmd == "paket":
        print(json.dumps(paket(args.text, budget=args.budget), ensure_ascii=False, indent=2))
    elif args.cmd == "schnappschuss":
        c = _connect(); _ensure_vp_tables(c)
        print(json.dumps(schnappschuss(c), ensure_ascii=False, indent=2)); c.close()
    elif args.cmd == "heilen":
        c = _connect(); _ensure_vp_tables(c)
        print(json.dumps(heilen(c), ensure_ascii=False, indent=2)); c.close()
    elif args.cmd == "verfall":
        c = _connect(); _ensure_vp_tables(c)
        print(json.dumps({"aktualisiert": verfall(c)})); c.close()
    elif args.cmd == "messen":
        fragen = [
            "ClayGraph Trefferquote Waisenproblem Pfade normalisiert",
            "gegenhypothese widerlegt superseded promotion",
            "hop_decay walk depth graph epoch",
            "kuration offen quelle geaendert",
            "Digital Retina CPU vision pipeline recall",
        ]
        print(json.dumps(vergleichsmessung(fragen, args.out), ensure_ascii=False, indent=2))
    elif args.cmd == "cache-messen":
        gruppen = [
            ["Was sagt ClayGraph ueber das Waisenproblem?",
             "ClayGraph Waisenproblem -- was gilt dort?",
             "Erklaer mir, was ClayGraph zum Waisenproblem sagt."],
            ["Welche Hypothese wurde widerlegt?",
             "Was wurde als falsch erkannt und widerlegt?",
             "Zeig mir eine widerlegte Annahme."],
        ]
        print(json.dumps(cache_messung(gruppen), ensure_ascii=False, indent=2))
    elif args.cmd == "degeneration":
        fragen = [
            "ClayGraph Waisenproblem",
            "gegenhypothese widerlegt",
            "kuration offen",
            "Digital Retina CPU vision",
            "hop_decay walk epoch",
            "folgerung beleg messung",
        ]
        print(json.dumps(degenerations_simulation(fragen, args.zyklen), ensure_ascii=False, indent=2))
    elif args.cmd == "beweis":
        print(json.dumps(beweis_schleife(args.text), ensure_ascii=False, indent=2))
    elif args.cmd == "needle-test":
        print(json.dumps(needle_test(), ensure_ascii=False, indent=2))
    elif args.cmd == "beweis-verweigerung":
        print(json.dumps(beweis_verweigerung(), ensure_ascii=False, indent=2))
    elif args.cmd == "lese-kosten":
        fragen = [
            ("wo liegt registry.json fuer needle, welcher Wirt welcher Pfad", False),
            ("wo liegen die needle mini_train mini_val Dateien", False),
            ("was genau steht in der needle registry.json Konfiguration", True),
            ("wo ist CLAUDE.md zu finden", False),
            ("welchen Inhalt hat die needle registry -- Modellname und Version", True),
        ]
        print(json.dumps(lese_kosten_vergleich(fragen), ensure_ascii=False, indent=2))
    elif args.cmd == "ort-messen":
        print(json.dumps(ort_dichte_messung(), ensure_ascii=False, indent=2))
    elif args.cmd == "systeme":
        c = _connect(); _ensure_vp_tables(c)
        print(json.dumps(systeme(c), ensure_ascii=False, indent=2)); c.close()
    elif args.cmd == "puls":
        c = _connect(); _ensure_vp_tables(c)
        for _ in range(args.wiederholungen):
            print(json.dumps(puls(c), ensure_ascii=False))
        c.close()
    elif args.cmd == "lesen":
        bereich = None
        print(json.dumps(lesen(args.ort_id, args.paket_id, bereich=bereich), ensure_ascii=False, indent=2))
    else:
        ap.print_help()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
