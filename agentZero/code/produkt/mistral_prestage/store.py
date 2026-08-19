from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import uuid

DEFAULT_DB_PATH = "/var/lib/clay/wiki.db"

# New table names only. Checked 2026-08-18 against the 105 existing wiki.db
# tables (none named mv_*) before this module was written -- see the M1
# report for the exact list checked. This module never touches the other
# 105 tables or the store.py/UnifiedDB schema.
SCHEMA = """
CREATE TABLE IF NOT EXISTS mv_prestage_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value_json TEXT NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS mv_prestage_turns (
    prestage_id TEXT PRIMARY KEY,
    turn_id TEXT,
    session_id TEXT,
    user_id TEXT,
    raw_prompt TEXT NOT NULL,
    world_digest TEXT,
    connected_systems_json TEXT,
    caveman_prompt TEXT NOT NULL,
    tool_selection_json TEXT,
    memory_artefacts_json TEXT,
    outsourced_json TEXT,
    user_intent TEXT,
    watch_out TEXT,
    hypotheses_json TEXT,
    counter_hypotheses_json TEXT,
    prestage_model TEXT,
    prestage_receipt_json TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS mv_prestage_turns_session_idx
    ON mv_prestage_turns(session_id, created_at);

-- Phase 2b (19.08.): die eigentliche Lernschleife. Die neuen Spalten selbst
-- werden NICHT hier per ALTER TABLE angelegt -- SQLite 3.45.1 kennt kein
-- "ADD COLUMN IF NOT EXISTS" (geprueft: syntax error). Sie werden stattdessen
-- in PrestageStore.__init__ einzeln per ALTER TABLE ADD COLUMN versucht, mit
-- "duplicate column name" abgefangen -- das macht denselben Effekt
-- idempotent. Siehe _MV_PRESTAGE_TURNS_NEUE_SPALTEN unten. Jede Spalte ist
-- ENTWEDER direkt aus dem Zug selbst berechnet (kein Query noetig:
-- self_adapted, translation_raw_fallback kommen von pipeline.py, outcome_ok
-- ist ihre mechanische Kombination) ODER ein bewusst als Naeherung/
-- Best-Effort gekennzeichneter Read aus Zeros eigenen Tabellen
-- (korpus_treffer_n gegen fts_index_artikel, effects_evidence_json gegen
-- effects/causal_episodes ueber ein Zeitfenster -- KEINE echte
-- Fremdschluessel-Verknuepfung, weil turn_id bei record_via_turnlifecycle=
-- False immer NULL bleibt, siehe pipeline.py-Kommentar dort).
--
-- Der Index auf routing_key und die mv_prestage_lernbild-Sicht referenzieren
-- die neuen Spalten -- beide stehen deshalb NICHT hier, sondern in
-- SCHEMA_LERNSCHLEIFE unten, die __init__ erst NACH den ALTER TABLEs
-- ausfuehrt (siehe dort).

CREATE TABLE IF NOT EXISTS mv_translation_log (
    translation_id TEXT PRIMARY KEY,
    turn_id TEXT,
    prestage_id TEXT,
    caveman_original TEXT NOT NULL,
    german_translation TEXT NOT NULL,
    translator_model TEXT,
    translator_receipt_json TEXT,
    faithfulness_score REAL,
    readability_score REAL,
    judge_model TEXT,
    judge_verdict_json TEXT,
    fabrication_flag INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS mv_eval_runs (
    run_id TEXT PRIMARY KEY,
    iteration INTEGER NOT NULL,
    prompt_version TEXT NOT NULL,
    eval_set_size INTEGER NOT NULL,
    pass_rate REAL NOT NULL,
    avg_faithfulness REAL NOT NULL,
    avg_readability REAL NOT NULL,
    fabrication_count INTEGER NOT NULL,
    notes TEXT,
    created_at REAL NOT NULL
);
"""

# Phase 2b (19.08.): die Lernschleife auf mv_prestage_turns. Additive Spalten
# -- SQLite 3.45.1 hat KEIN "ADD COLUMN IF NOT EXISTS" (geprueft: syntax
# error), also einzeln per ALTER TABLE versucht und "duplicate column name"
# abgefangen (siehe __init__). Jede Spalte ist ENTWEDER direkt aus dem Zug
# selbst berechnet (self_adapted/translation_raw_fallback kommen von
# pipeline.py, outcome_ok ist ihre rein mechanische Kombination -- NIE eine
# Bewertung inhaltlicher Richtigkeit) ODER ein bewusst als Naeherung/
# Best-Effort gekennzeichneter Read aus Zeros eigenen Tabellen
# (korpus_treffer_n gegen fts_index_artikel, effects_evidence_json gegen
# effects/causal_episodes ueber ein Zeitfenster -- KEINE echte
# Fremdschluessel-Verknuepfung, weil turn_id bei record_via_turnlifecycle=
# False immer NULL bleibt, siehe pipeline.py-Kommentar dort).
_MV_PRESTAGE_TURNS_NEUE_SPALTEN = (
    ("epistemik_json", "TEXT"),
    ("epistemik_bekannt_n", "INTEGER"),
    ("epistemik_unbekannt_n", "INTEGER"),
    ("routing_key", "TEXT"),
    ("self_adapted", "INTEGER"),
    ("translation_raw_fallback", "INTEGER"),
    ("self_reported_gap", "INTEGER"),
    ("self_reported_gap_marker", "TEXT"),
    ("outcome_ok", "INTEGER"),
    ("korpus_treffer_n", "INTEGER"),
    ("effects_evidence_json", "TEXT"),
)

# Index + "was-ist-falsch"-Sicht: referenzieren die Spalten oben, deshalb ERST
# ausgefuehrt, nachdem __init__ die ALTER TABLEs durchgelaufen ist.
# outcome_ok ist NIE eine Modellbewertung -- nur die mechanische Kombination
# aus self_adapted (Zero brauchte Runde 2) und translation_raw_fallback
# (Uebersetzung ausgefallen). Rohzahlen mit, absichtlich, damit n=1 nicht wie
# eine Gewissheit aussieht.
SCHEMA_LERNSCHLEIFE = """
CREATE INDEX IF NOT EXISTS mv_prestage_turns_routing_idx
    ON mv_prestage_turns(routing_key, epistemik_unbekannt_n);

CREATE VIEW IF NOT EXISTS mv_prestage_lernbild AS
SELECT
    routing_key,
    CASE WHEN epistemik_unbekannt_n > 0 THEN 1 ELSE 0 END AS hatte_luecke,
    COUNT(*) AS n,
    SUM(COALESCE(self_adapted, 0)) AS n_self_adapted,
    SUM(COALESCE(translation_raw_fallback, 0)) AS n_uebersetzung_ausgefallen,
    SUM(COALESCE(self_reported_gap, 0)) AS n_selbst_gemeldete_luecke,
    SUM(CASE WHEN outcome_ok = 0 THEN 1 ELSE 0 END) AS n_nicht_ok
FROM mv_prestage_turns
WHERE routing_key IS NOT NULL AND routing_key != ''
GROUP BY routing_key, CASE WHEN epistemik_unbekannt_n > 0 THEN 1 ELSE 0 END;
"""

# Mechanischer Substring-Scan, KEINE Modellbewertung: erfasst, dass Zero SELBST
# eine Wissensluecke/einen Fehlschlag gemeldet hat (die uebliche ehrliche
# Formulierung nach rule H). Das ist NICHT dasselbe wie "war falsch" -- eine
# ehrliche Luecke bei einer wirklich unbeantwortbaren Frage ist KORREKTES
# Verhalten. Deshalb ist dieses Signal in der Aggregation eine eigene Spalte
# (n_selbst_gemeldete_luecke), nie in outcome_ok verrechnet.
_LUECKE_MARKER = (
    "nicht gefunden", "nicht ermittelbar", "nicht bekannt", "keine information",
    "kann ich nicht", "konnte nicht", "nicht moeglich", "nicht möglich",
    "fehlgeschlagen", "kein zugriff", "ist unbekannt", "weiss ich nicht",
    "weiß ich nicht", "habe ich nicht gefunden",
)


def _als_text(wert) -> str:
    """Bugfix, unabhaengig von Phase 2b gefunden (19.08. beim E2E-Test 'wer bin
    ich?'): mistral-small liefert user_intent/watch_out gelegentlich als LISTE
    statt als String -- sqlite3 kann das nicht binden ("type 'list' is not
    supported"), und der GANZE Zug flog deshalb aus record_prestage_turn, NACH
    dem Zero schon geantwortet hatte. TEXT-Spalten in SQLite duerfen nie einen
    rohen Python-Wert bekommen, der nicht schon str ist -- betrifft nur diese
    beiden Felder (die anderen freien Textfelder werden bereits json.dumps()t).
    """
    if wert is None:
        return ""
    if isinstance(wert, str):
        return wert
    try:
        return json.dumps(wert, ensure_ascii=False)
    except Exception:
        return str(wert)


def _selbst_gemeldete_luecke(text: str) -> tuple[int, str | None]:
    if not text:
        return 0, None
    low = text.lower()
    for m in _LUECKE_MARKER:
        if m in low:
            return 1, m
    return 0, None


class PrestageStore:
    """Own connection to the shared wiki.db, own tables only.

    Deliberately does NOT go through clayverse.store.UnifiedDB (that class
    executescript()s the coordinator-owned 87/19-table schema on open,
    which this module has no business touching). SQLite's WAL mode makes a
    second independent connection to the same file safe.
    """

    def __init__(self, db_path: str | None = None):
        self.path = db_path or os.environ.get("CLAYVERSE_DB_PATH", DEFAULT_DB_PATH)
        self.db = sqlite3.connect(self.path, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA busy_timeout=30000")
        self.db.executescript(SCHEMA)
        self.db.commit()
        # Phase 2b: additive Spalten auf der bestehenden mv_prestage_turns.
        # Einzeln, weil SQLite kein "ADD COLUMN IF NOT EXISTS" kennt (siehe
        # SCHEMA_LERNSCHLEIFE-Kommentar) -- "duplicate column name" ist der
        # erwartete, harmlose Fall auf jedem zweiten und weiteren Start.
        for _name, _typ in _MV_PRESTAGE_TURNS_NEUE_SPALTEN:
            try:
                self.db.execute(f"ALTER TABLE mv_prestage_turns ADD COLUMN {_name} {_typ}")
            except sqlite3.OperationalError as _e:
                if "duplicate column name" not in str(_e).lower():
                    raise
        self.db.commit()
        # Index + Sicht kommen erst jetzt, wo die Spalten sicher existieren.
        self.db.executescript(SCHEMA_LERNSCHLEIFE)
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # -- the pre-stage's own small persistent state / learning loop --
    def state_get(self, key: str, default=None):
        row = self.db.execute(
            "SELECT value_json FROM mv_prestage_state WHERE key=?", (key,)
        ).fetchone()
        return json.loads(row["value_json"]) if row else default

    def state_set(self, key: str, value) -> None:
        self.db.execute(
            "INSERT INTO mv_prestage_state(key,value_json,updated_at) VALUES(?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at=excluded.updated_at",
            (key, json.dumps(value, ensure_ascii=False, sort_keys=True), time.time()),
        )
        self.db.commit()

    # -- Phase 2b: best-effort, read-only Blick in ZEROS eigene Tabellen -----
    def _korpus_treffer_n(self, text: str) -> int | None:
        """War die Frage im Korpus ueberhaupt beantwortbar? Guenstige FTS-Zaehlung,
        kein Ranking. None, wenn nichts Brauchbares im Text steht oder die
        Abfrage scheitert (z.B. FTS-Tabelle fehlt in einer Testdatenbank)."""
        try:
            woerter = [w for w in re.findall(r"[A-Za-zÄÖÜäöüß0-9]+", text or "") if len(w) >= 3][:8]
            if not woerter:
                return None
            query = " OR ".join('"' + w.replace('"', '') + '"' for w in woerter)
            row = self.db.execute(
                "SELECT COUNT(*) c FROM fts_index_artikel WHERE fts_index_artikel MATCH ?",
                (query,),
            ).fetchone()
            return int(row["c"]) if row else None
        except Exception:
            return None

    def _effects_evidence(self, user_id: str | None, seit_ts: float | None) -> dict:
        """Zeitliches Naeherungsfenster auf effects/causal_episodes fuer diesen
        Menschen waehrend der Laufzeit des Zuges. KEINE Fremdschluessel-
        Verknuepfung -- turn_id/episode_id werden vom Vorstufe-Pfad (record_
        via_turnlifecycle=False, der Normalfall) nicht gesetzt, siehe
        pipeline.py. Ehrlich als Naeherung benannt, nicht als Beweis."""
        if not user_id or not seit_ts:
            return {"status": "KEIN_FENSTER"}
        try:
            bis_ts = time.time()
            eff = self.db.execute(
                "SELECT status, COUNT(*) c FROM effects WHERE user_id=? AND ts BETWEEN ? AND ? "
                "GROUP BY status",
                (user_id, seit_ts, bis_ts),
            ).fetchall()
            credit = self.db.execute(
                "SELECT AVG(credit) a, COUNT(*) c FROM causal_episodes WHERE ts BETWEEN ? AND ?",
                (seit_ts, bis_ts),
            ).fetchone()
            return {
                "fenster_s": round(bis_ts - seit_ts, 1),
                "effects_status": {r["status"]: r["c"] for r in eff},
                "causal_episoden_n": credit["c"] if credit else 0,
                "causal_credit_avg": credit["a"] if credit else None,
                "hinweis": "Zeitfenster je user_id, keine direkte FK-Verknuepfung zu diesem Zug",
            }
        except Exception as e:
            return {"status": "FEHLER", "grund": (type(e).__name__ + ": " + str(e))[:150]}

    def record_prestage_turn(self, **fields) -> str:
        prestage_id = str(uuid.uuid4())

        # -- Phase 2b Lernsignal: rein additiv. Ein Fehler HIER darf die
        # urspruengliche Aufzeichnung (die 18 Felder von vorher) nie kippen --
        # deshalb eigener try/except-Block mit sicheren Defaults, bevor der
        # unveraenderte INSERT unten laeuft.
        lern = {
            "epistemik_json": "{}", "epistemik_bekannt_n": None,
            "epistemik_unbekannt_n": None, "routing_key": None,
            "self_adapted": None, "translation_raw_fallback": None,
            "self_reported_gap": None, "self_reported_gap_marker": None,
            "outcome_ok": None, "korpus_treffer_n": None,
            "effects_evidence_json": None,
        }
        try:
            epistemik = fields.get("epistemik") or {}
            bekannt = epistemik.get("bekannt") or []
            unbekannt = epistemik.get("unbekannt") or []
            tool_sel = fields.get("tool_selection") or []
            routing_key = ",".join(sorted(t for t in tool_sel if isinstance(t, str)))
            self_adapted = int(bool(fields.get("self_adapted", False)))
            translation_raw_fallback = int(bool(fields.get("translation_raw_fallback", False)))
            gap_hit, gap_marker = _selbst_gemeldete_luecke(fields.get("reply_text", ""))
            lern.update({
                "epistemik_json": json.dumps(epistemik, ensure_ascii=False, sort_keys=True),
                "epistemik_bekannt_n": len(bekannt),
                "epistemik_unbekannt_n": len(unbekannt),
                "routing_key": routing_key,
                "self_adapted": self_adapted,
                "translation_raw_fallback": translation_raw_fallback,
                "self_reported_gap": gap_hit,
                "self_reported_gap_marker": gap_marker,
                # outcome_ok: rein mechanisch aus zwei bereits berechneten
                # Strukturmerkmalen -- KEINE Bewertung der inhaltlichen
                # Richtigkeit (die kann diese Schleife nicht messen).
                "outcome_ok": int(not (self_adapted or translation_raw_fallback)),
            })
        except Exception:
            pass
        try:
            lern["korpus_treffer_n"] = self._korpus_treffer_n(fields.get("raw_prompt", ""))
        except Exception:
            pass
        try:
            lern["effects_evidence_json"] = json.dumps(
                self._effects_evidence(fields.get("user_id"), fields.get("turn_started_at")),
                ensure_ascii=False,
            )
        except Exception:
            pass

        self.db.execute(
            "INSERT INTO mv_prestage_turns(prestage_id,turn_id,session_id,user_id,raw_prompt,"
            "world_digest,connected_systems_json,caveman_prompt,tool_selection_json,"
            "memory_artefacts_json,outsourced_json,user_intent,watch_out,hypotheses_json,"
            "counter_hypotheses_json,prestage_model,prestage_receipt_json,created_at,"
            "epistemik_json,epistemik_bekannt_n,epistemik_unbekannt_n,routing_key,"
            "self_adapted,translation_raw_fallback,self_reported_gap,self_reported_gap_marker,"
            "outcome_ok,korpus_treffer_n,effects_evidence_json) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                prestage_id,
                fields.get("turn_id"),
                fields.get("session_id"),
                fields.get("user_id"),
                fields["raw_prompt"],
                fields.get("world_digest"),
                json.dumps(fields.get("connected_systems", {}), ensure_ascii=False, sort_keys=True),
                fields["caveman_prompt"],
                json.dumps(fields.get("tool_selection", []), ensure_ascii=False, sort_keys=True),
                json.dumps(fields.get("memory_artefacts", []), ensure_ascii=False, sort_keys=True),
                json.dumps(fields.get("outsourced", []), ensure_ascii=False, sort_keys=True),
                _als_text(fields.get("user_intent", "")),
                _als_text(fields.get("watch_out", "")),
                json.dumps(fields.get("hypotheses", []), ensure_ascii=False, sort_keys=True),
                json.dumps(fields.get("counter_hypotheses", []), ensure_ascii=False, sort_keys=True),
                fields.get("prestage_model"),
                json.dumps(fields.get("prestage_receipt", {}), ensure_ascii=False, sort_keys=True),
                time.time(),
                lern["epistemik_json"],
                lern["epistemik_bekannt_n"],
                lern["epistemik_unbekannt_n"],
                lern["routing_key"],
                lern["self_adapted"],
                lern["translation_raw_fallback"],
                lern["self_reported_gap"],
                lern["self_reported_gap_marker"],
                lern["outcome_ok"],
                lern["korpus_treffer_n"],
                lern["effects_evidence_json"],
            ),
        )
        self.db.commit()
        return prestage_id

    def record_translation(self, **fields) -> str:
        translation_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO mv_translation_log(translation_id,turn_id,prestage_id,caveman_original,"
            "german_translation,translator_model,translator_receipt_json,faithfulness_score,"
            "readability_score,judge_model,judge_verdict_json,fabrication_flag,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                translation_id,
                fields.get("turn_id"),
                fields.get("prestage_id"),
                fields["caveman_original"],
                fields["german_translation"],
                fields.get("translator_model"),
                json.dumps(fields.get("translator_receipt", {}), ensure_ascii=False, sort_keys=True),
                fields.get("faithfulness_score"),
                fields.get("readability_score"),
                fields.get("judge_model"),
                json.dumps(fields.get("judge_verdict", {}), ensure_ascii=False, sort_keys=True),
                int(bool(fields.get("fabrication_flag", False))),
                time.time(),
            ),
        )
        self.db.commit()
        return translation_id

    def record_eval_run(self, **fields) -> str:
        run_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO mv_eval_runs(run_id,iteration,prompt_version,eval_set_size,pass_rate,"
            "avg_faithfulness,avg_readability,fabrication_count,notes,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                run_id,
                fields["iteration"],
                fields["prompt_version"],
                fields["eval_set_size"],
                fields["pass_rate"],
                fields["avg_faithfulness"],
                fields["avg_readability"],
                fields["fabrication_count"],
                fields.get("notes", ""),
                time.time(),
            ),
        )
        self.db.commit()
        return run_id

    # -- Phase 2b Schritt 2/3: Aggregation + Rueckspeise-Text ----------------
    def lernbild(self, min_n: int = 3) -> list[dict]:
        """"Was ist falsch": Fehlerquote je Routing-Muster, aus echten Rohzahlen.

        Gruppiert ueber routing_key (sortierte tool_selection dieses Zuges) x
        ob eine epistemische Luecke vorlag (epistemik_unbekannt_n > 0).
        outcome_ok ist rein mechanisch (siehe record_prestage_turn) -- NIE
        eine Modellbewertung der inhaltlichen Richtigkeit. min_n filtert
        Muster mit zu wenigen Zuegen raus, damit n=1 nicht wie ein Befund
        aussieht.
        """
        rows = self.db.execute(
            "SELECT routing_key, hatte_luecke, n, n_self_adapted, "
            "n_uebersetzung_ausgefallen, n_selbst_gemeldete_luecke, n_nicht_ok "
            "FROM mv_prestage_lernbild WHERE n >= ? "
            "ORDER BY (1.0 * n_nicht_ok / n) DESC, n DESC",
            (min_n,),
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["fehlerquote"] = round(d["n_nicht_ok"] / d["n"], 3) if d["n"] else 0.0
            out.append(d)
        return out

    def gelernter_block(self, max_items: int = 3, min_n: int = 3) -> str:
        """Kurzer, ehrlicher Rueckspeise-Text fuer die Vorstufe (Phase 2b Schritt 3).

        Nur Muster mit Fehlerquote > 0 und genug Zuegen (min_n) -- Rohzahlen
        immer mit, damit nichts als Gewissheit verkauft wird. Leerer String,
        wenn (noch) nichts gelernt werden kann -- KEIN erfundenes Muster als
        Fuellsel. Darf nie werfen (Aufrufer haengt es direkt in den
        Vorstufe-Kontext).
        """
        try:
            muster = [m for m in self.lernbild(min_n=min_n) if m["fehlerquote"] > 0][:max_items]
        except Exception:
            return ""
        if not muster:
            return ""
        zeilen = []
        for m in muster:
            tools = m["routing_key"] or "(keine Werkzeuge)"
            luecke = "mit Wissensluecke" if m["hatte_luecke"] else "ohne Wissensluecke"
            zeilen.append(
                "- tools=%s (%s): %d/%d Zuege brauchten Nachbesserung "
                "(self_adapted=%d, uebersetzung_ausgefallen=%d)"
                % (tools, luecke, m["n_nicht_ok"], m["n"], m["n_self_adapted"],
                   m["n_uebersetzung_ausgefallen"])
            )
        gesamt_n = sum(m["n"] for m in muster)
        return (
            "gelernt aus %d frueheren Zuegen (Rohzahlen, kein Urteil):\n%s"
            % (gesamt_n, "\n".join(zeilen))
        )
