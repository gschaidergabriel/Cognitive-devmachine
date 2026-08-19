#!/usr/bin/env python3
"""
EntityOS Dream Daemon (eos-dream) v1.0
=======================================

Zeros budgetierte Offline-Selbstverarbeitungsphase — angelehnt an Franks
dream_daemon.py (~/repo/services/dream_daemon.py), aber NEU geschrieben fuer
EntityOS/Zero statt uebernommen: Franks Original haengt an chat_memory.db,
consciousness.db, world_experience.db, personality/e_pq.py, Titan Neural
Cortex, Context Relevance Gate und einem lokalen LLM-Router auf
127.0.0.1:8091 — nichts davon existiert in EntityOS. Was UEBERNOMMEN wurde:
die Drei-Phasen-Idee (Replay / Synthese / Konsolidierung), das Prinzip
"budgetiert, unterbrechbar, mit Sperrzeit, kein torch", JSON-Parse-Fallback
fuer LLM-Antworten, und die zweistufige Watchdog-Idee (hier: systemd
Restart=on-failure + Timer statt Dauerlauf-Thread, siehe unten "WARUM
ONESHOT").

WARUM ONESHOT STATT DAUERLAUF-THREAD
-------------------------------------
Franks Original ist ein Dauerdienst, der alle 60s prueft, ob der Nutzer 20min
inaktiv war, und dann pausier-/fortsetzbar traeumt. Zero hat kein Chat-Idle-
Signal in diesem Sinn, und der VPS (4 Kerne/15GB) traegt schon reichlich
Dauerlast (u.a. eine Wikiarbeit mit 14.400 Anfragen/Tag). Ein zusaetzlicher
Dauerlauf-Thread waere hier NICHT budgetierter, sondern zusaetzlicher
Dauerbetrieb. Deshalb: systemd Type=oneshot + Timer 2x/Tag (eos-dream.timer),
mit Sperrzeit (Cooldown) UND Lastpruefung UND Laufzeit-Obergrenze IM Skript,
statt Idle-Erkennung. Ein Zyklus = Replay -> Synthese -> Konsolidierung,
am Stueck, budgetiert, dann Prozessende (kein Restart=always).

WAS EIN ZYKLUS TUT
-------------------
Phase 1 REPLAY (mechanisch, KEIN LLM-Aufruf, wiki.db NUR LESEND geoeffnet):
    liest neue/geaenderte Artikel (art IN baunotiz/bau), abgeschlossene
    entityos_erfolge und entityos_arbeitspaket seit dem letzten Traum aus
    /var/lib/clay/wiki.db. Reine Beobachtung, keine Bewertung.

Phase 2 SYNTHESE (HOECHSTENS EIN Mistral-Aufruf, mistral-small-latest,
    budgetiert): die Beobachtung aus Phase 1 wird zusammengefasst an
    /opt/entityos/tools/mistral_inference.py::chat() gegeben, das den
    vorhandenen FREE_ONLY-Schluesselpool aus /etc/clayverse/freie-zugaenge.env
    nutzt. 2-3 kurze deutsche Reflexionen + Muster als JSON. Schlaegt der
    Aufruf fehl (kein Schluessel, Rate-Limit, Timeout) faellt der Zyklus auf
    eine rein mechanische Zusammenfassung zurueck -- KEIN Blockieren, KEIN
    Wiederholungssturm.

Phase 3 KONSOLIDIERUNG (schreibt NUR in eigene Bereiche):
    a) eigene Tabellen in /opt/entityos/dream/dream.db (dream_state,
       dream_log, dream_hypotheses) -- niemals wiki.db.
    b) GENAU EIN neuer Artikel in wiki.db (art='zero_traum'), nach dem
       etablierten Protokoll aus bau_ins_wiki.py: artikel + artikel_suchtext
       + fts_index_artikel, sonst waere der Artikel unauffindbar (siehe
       Kommentar in auffindbar() unten -- das ist eine gemessene Falle aus
       dem Bestand, keine Vermutung). Es wird NICHTS an bestehenden Zeilen
       veraendert oder geloescht -- die neue id ist pro Zyklus eindeutig.

SICHERHEIT
----------
- wiki.db wird fuer Phase 1 mit `mode=ro` (SQLite URI, hart schreibgeschuetzt
  auf Verbindungsebene) geoeffnet.
- Der einzige Schreibzugriff auf wiki.db (Phase 3b) beschraenkt sich auf
  INSERT einer neuen, eindeutigen artikel_id. Kein UPDATE, kein DELETE auf
  fremden Zeilen (die 'delete'-Befehlsform im FTS-Protokoll wird nur fuer
  die eigene, gerade erst eingefuegte Zeile je verwendet, analog zum
  Referenzprotokoll).
- Eigene Geheimnis-Handhabung folgt der Konvention aus
  clayverse-schluesselwacht.service: KEIN EnvironmentFile in der Unit, das
  Skript liest /etc/clayverse/freie-zugaenge.env selbst und setzt nur
  MISTRAL_API_KEY in os.environ fuer diesen einen Prozess.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Pfade & Konstanten
# ---------------------------------------------------------------------------

DREAM_ROOT = Path(__file__).resolve().parent           # /opt/entityos/dream
CONFIG_PATH = DREAM_ROOT / "config" / "dream.conf"
DREAM_DB_PATH = DREAM_ROOT / "dream.db"
LOCK_PATH = DREAM_ROOT / "dream.lock"
LOG_PATH = DREAM_ROOT / "dream.log"

WIKI_DB_PATH = "/var/lib/clay/wiki.db"
SECRETS_PATH = Path("/etc/clayverse/freie-zugaenge.env")
MISTRAL_TOOLS_DIR = "/opt/entityos/tools"
PULS_WERKZEUG_DIR = "/opt/clayverse/werkzeug"  # vorprozessor.py/puls.py -- NUR LESEN, siehe unten

# Default-Konfiguration -- ueberschreibbar via config/dream.conf
DEFAULTS = {
    "ENABLED": "1",
    "COOLDOWN_HOURS": "8",         # Sperrzeit zwischen zwei Traeumen
    "MAX_RUNTIME_SEC": "480",      # harte Obergrenze je Zyklus (8 min)
    "CPU_LOAD_MAX_PCT": "50",      # ueber dieser Last (load1/nproc*100) kein Traum
    "LLM_MODEL": "mistral-small-latest",
    "LLM_MAX_TOKENS": "400",
    "LLM_TIMEOUT_SEC": "60",
    "LLM_RETRIES": "1",
    "REPLAY_LIMIT": "30",          # max. Zeilen je Beobachtungs-Query
}

LOG = logging.getLogger("eos_dream")


# ---------------------------------------------------------------------------
# Config / Secrets (eigenes, minimalinvasives Lesen -- keine EnvironmentFile)
# ---------------------------------------------------------------------------

def _read_kv_file(path: Path) -> Dict[str, str]:
    """Liest eine einfache KEY=VALUE-Datei (# Kommentare, Leerzeilen ok)."""
    out: Dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def load_config() -> Dict[str, str]:
    cfg = dict(DEFAULTS)
    cfg.update(_read_kv_file(CONFIG_PATH))
    return cfg


def load_mistral_key_into_env() -> bool:
    """Liest NUR MISTRAL_API_KEY aus der zentralen Geheimnis-Datei und setzt
    ihn in os.environ fuer DIESEN Prozess -- analog zur schluesselwacht.py-
    Konvention (kein EnvironmentFile in der systemd-Unit, das Skript liest
    selbst und nur so lange es laeuft)."""
    if os.environ.get("MISTRAL_API_KEY"):
        return True
    kv = _read_kv_file(SECRETS_PATH)
    key = kv.get("MISTRAL_API_KEY", "").strip()
    if not key:
        return False
    os.environ["MISTRAL_API_KEY"] = key
    return True


# ---------------------------------------------------------------------------
# Eigene DB-Schicht (dream.db -- NIEMALS wiki.db)
# ---------------------------------------------------------------------------

_DREAM_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS dream_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT DEFAULT 'idle',
    last_dream_start TEXT,
    last_dream_end TEXT,
    last_dream_end_epoch REAL,
    total_dreams INTEGER DEFAULT 0,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS dream_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dream_session_id TEXT,
    phase TEXT,
    content TEXT,
    duration_sec REAL,
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS dream_hypotheses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dream_session_id TEXT,
    hypothesis TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    created_at TEXT
);
"""


def get_dream_conn() -> sqlite3.Connection:
    DREAM_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DREAM_DB_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.executescript(_DREAM_SCHEMA)
    conn.commit()
    return conn


def get_last_dream_end(conn: sqlite3.Connection) -> Optional[float]:
    row = conn.execute(
        "SELECT last_dream_end_epoch FROM dream_state ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row and row["last_dream_end_epoch"]:
        return float(row["last_dream_end_epoch"])
    return None


def save_state(conn: sqlite3.Connection, **fields: Any) -> None:
    row = conn.execute("SELECT * FROM dream_state ORDER BY id DESC LIMIT 1").fetchone()
    now = datetime.now(timezone.utc).isoformat()
    if row is None:
        conn.execute(
            "INSERT INTO dream_state (status, last_dream_start, last_dream_end, "
            "last_dream_end_epoch, total_dreams, updated_at) VALUES (?,?,?,?,?,?)",
            (
                fields.get("status", "idle"),
                fields.get("last_dream_start"),
                fields.get("last_dream_end"),
                fields.get("last_dream_end_epoch"),
                fields.get("total_dreams", 0),
                now,
            ),
        )
    else:
        merged = dict(row)
        merged.update({k: v for k, v in fields.items() if v is not None})
        conn.execute(
            "UPDATE dream_state SET status=?, last_dream_start=?, last_dream_end=?, "
            "last_dream_end_epoch=?, total_dreams=?, updated_at=? WHERE id=?",
            (
                merged.get("status", "idle"),
                merged.get("last_dream_start"),
                merged.get("last_dream_end"),
                merged.get("last_dream_end_epoch"),
                merged.get("total_dreams", 0),
                now,
                row["id"],
            ),
        )
    conn.commit()


def log_phase(conn: sqlite3.Connection, session_id: str, phase: str,
              content: Any, duration_sec: float) -> None:
    conn.execute(
        "INSERT INTO dream_log (dream_session_id, phase, content, duration_sec, "
        "timestamp) VALUES (?,?,?,?,?)",
        (session_id, phase, json.dumps(content, ensure_ascii=False, default=str),
         duration_sec, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def log_hypothesis(conn: sqlite3.Connection, session_id: str, text: str,
                    confidence: float = 0.5) -> None:
    conn.execute(
        "INSERT INTO dream_hypotheses (dream_session_id, hypothesis, confidence, "
        "created_at) VALUES (?,?,?,?)",
        (session_id, text.strip(), confidence, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Sperrzeit / Lastpruefung / Lockfile
# ---------------------------------------------------------------------------

def get_cpu_load_pct() -> float:
    try:
        with open("/proc/loadavg") as f:
            load1 = float(f.read().split()[0])
        return (load1 / max(1, os.cpu_count() or 1)) * 100.0
    except Exception:
        return 0.0


def acquire_lock():
    """Verhindert parallele Laeufe (Timer + manueller Start ueberlappend).
    Gibt ein offenes Filehandle zurueck, das den Lock haelt, solange der
    Prozess laeuft. None bei Misserfolg (schon gesperrt)."""
    DREAM_ROOT.mkdir(parents=True, exist_ok=True)
    fh = open(LOCK_PATH, "w")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        return None
    fh.write(str(os.getpid()))
    fh.flush()
    return fh


def should_dream(conn: sqlite3.Connection, cfg: Dict[str, str]) -> tuple[bool, str]:
    if cfg.get("ENABLED", "1") != "1":
        return False, "deaktiviert (ENABLED=0 in config/dream.conf)"

    last_end = get_last_dream_end(conn)
    if last_end is not None:
        cooldown_sec = float(cfg["COOLDOWN_HOURS"]) * 3600.0
        since = time.time() - last_end
        if since < cooldown_sec:
            return False, f"Sperrzeit aktiv ({since/3600:.1f}h seit letztem Traum, " \
                           f"Sperrzeit {cfg['COOLDOWN_HOURS']}h)"

    load_pct = get_cpu_load_pct()
    if load_pct > float(cfg["CPU_LOAD_MAX_PCT"]):
        return False, f"Last zu hoch ({load_pct:.1f}% > {cfg['CPU_LOAD_MAX_PCT']}%)"

    return True, "Bedingungen erfuellt"


# ---------------------------------------------------------------------------
# Phase 1: REPLAY (mechanisch, wiki.db read-only)
# ---------------------------------------------------------------------------

def open_wiki_readonly() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{WIKI_DB_PATH}?mode=ro", uri=True, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


def run_phase_replay(cfg: Dict[str, str], since_iso: str,
                      since_epoch: float) -> Dict[str, Any]:
    limit = int(cfg["REPLAY_LIMIT"])
    obs: Dict[str, Any] = {
        "seit": since_iso,
        "neue_bauschritte": [],
        "erfolge": [],
        "fehlschlaege": [],
        "arbeitspakete_fertig": [],
        "kuration_offen": 0,
    }
    conn = open_wiki_readonly()
    try:
        rows = conn.execute(
            "SELECT id, titel, projekt, datum, erzeugt_am FROM artikel "
            "WHERE art IN ('baunotiz','bau') AND erzeugt_am > ? "
            "ORDER BY erzeugt_am DESC LIMIT ?",
            (since_iso, limit),
        ).fetchall()
        obs["neue_bauschritte"] = [
            {"id": r["id"], "titel": (r["titel"] or "")[:160], "projekt": r["projekt"]}
            for r in rows
        ]

        rows = conn.execute(
            "SELECT id, art, titel, wirkung, gehoert, datum FROM entityos_erfolge "
            "WHERE erfasst > ? ORDER BY erfasst DESC LIMIT ?",
            (since_epoch, limit),
        ).fetchall()
        for r in rows:
            item = {"titel": r["titel"], "wirkung": (r["wirkung"] or "")[:200],
                     "gehoert": r["gehoert"], "datum": r["datum"]}
            (obs["erfolge"] if r["art"] == "erfolg" else obs["fehlschlaege"]).append(item)

        rows = conn.execute(
            "SELECT paket_id, besteller, auftrag, ergebnis FROM entityos_arbeitspaket "
            "WHERE stand='fertig' AND geaendert > ? ORDER BY geaendert DESC LIMIT ?",
            (since_epoch, limit),
        ).fetchall()
        obs["arbeitspakete_fertig"] = [
            {"paket_id": r["paket_id"], "besteller": r["besteller"],
             "auftrag": (r["auftrag"] or "")[:160]}
            for r in rows
        ]

        row = conn.execute("SELECT COUNT(*) AS n FROM kuration WHERE status='offen'").fetchone()
        obs["kuration_offen"] = row["n"] if row else 0
    finally:
        conn.close()
    return obs


# ---------------------------------------------------------------------------
# Phase 1b-PRIMAER: LUECKEN-LESEN aus der Puls-Entitaet (LLM-frei)
# ---------------------------------------------------------------------------
# KURSKORREKTUR Eigner (19.08., zweite Fassung): das Zentrum ist NICHT die
# Mistral-Vorstufe, sondern der endogene, LLM-freie Kognitionszyklus:
# clayverse-puls (Dienst, Code puls.py + die eigentliche Kognition
# vorprozessor.py). NUR LESEN -- kein rm/UPDATE/DELETE gegen deren Tabellen,
# kein Eingriff in den Herzschlag (puls.py takt()). vorprozessor.paket() ist
# die eine sanktionierte OEFFENTLICHE Schnittstelle dieser Entitaet und wird
# hier genau so aufgerufen, wie jeder andere Aufrufer sie auch aufruft --
# ihre eigenen, dokumentierten Nebenwirkungen (vp_paket_log/vp_plan_cache/
# vp_edge_lern) sind Teil ihres Entwurfs, nicht etwas, das wir ihr antun.
#
# ⚠️ GEMESSEN, NICHT ANGENOMMEN (Messgeraet vor Glauben, 19.08.):
# vorprozessor.lernen(c, package, war_treffer) hat KEINEN Fehltreffer-
# Schreibpfad. Der Code: `if not war_treffer: return` -- ein fruehizeitiger
# Ausstieg, danach schreibt die Funktion NUR bei war_treffer=True in
# vp_edge_lern (Kantenart-Vertrauensgewichte, 22 Zeilen, zuletzt aktualisiert
# heute). Es gibt keine Tabelle, keine Zeile, die einen Fehltreffer
# materialisiert -- 0 Belegzeilen fuer "was paket() NICHT fand" in JEDER
# Tabelle, die lernen() beruehrt. Der einzige produktive Aufrufer ist
# paket() selbst: `if cache_hit: lernen(c, result, war_treffer=True)`.
#
# Der treueste real vorhandene Ersatz: vp_paket_log protokolliert JEDEN
# echten Aufruf von paket() (7.820 Zeilen gesamt, 4.866 in den letzten 24h --
# das ist aktiv genutzt, nicht totes Gleis). Wiederholte, identische Fragen
# darin sind ein echtes, LLM-freies Bedarfssignal. Fuer die haeufigste
# Wiederholung wird paket() LIVE erneut aufgerufen (die tatsaechliche
# Produktions-Schnittstelle) und deren resolution/hyperposition/treffer
# ausgewertet -- das IST "was paket() nicht fand", direkt gemessen statt aus
# einer nicht existierenden Logtabelle gelesen.
#
# Sekundaer (strukturelles Hintergrundsignal, siehe read_prestage_gaps
# darunter fuer die dritte, noch schwaechere Quelle Mistral-Vorstufe):
# offene Hypothesen (artikel.art='hypothese', status LIKE 'OPEN%') und
# offene Folgerungen (folgerung.status='offen'). GEMESSEN: alle 1.645
# hypothese- + 272 gegenhypothese-Artikel tragen denselben Zeitstempel
# (2026-08-14T22:23:59) -- ein einmaliger Bulk-Import, KEINE laufend
# wachsende Kognition. 0 neue in den letzten 24h. Das wird ehrlich als
# statisch/importiert markiert, nicht als "lebendig" verkauft.

_PULS_MISS_KLASSEN = {"MISS", "AMBIGUOUS", "LOW_CONFIDENCE", "UNRESOLVED"}


def read_puls_gaps(cfg: Dict[str, str], since_epoch: float) -> Dict[str, Any]:
    """PRIMAERE Lueckenquelle: die Puls-Entitaet (vorprozessor.py/puls.py).

    Liefert dieselbe top_thema-Form wie read_prestage_gaps(), damit
    write_gap_article() beide Quellen gleich behandeln kann, plus
    'lebendigkeit' mit den in Schritt 1 verlangten Kennzahlen fuer den
    Report."""
    limit = int(cfg["REPLAY_LIMIT"])
    out: Dict[str, Any] = {
        "verfuegbar": False, "top_thema": None, "fehler": None,
        "lebendigkeit": {}, "wiederholte_fragen": [],
    }
    conn = open_wiki_readonly()
    try:
        out["verfuegbar"] = True

        # ── Lebendigkeit messen (Schritt 1 des Eigner-Auftrags) ──────────
        leb: Dict[str, Any] = {}
        leb["vp_edge_lern_zeilen"] = conn.execute(
            "SELECT COUNT(*) c FROM vp_edge_lern").fetchone()["c"]
        r = conn.execute(
            "SELECT MIN(zuletzt_gelernt) mn, MAX(zuletzt_gelernt) mx FROM vp_edge_lern"
        ).fetchone()
        leb["vp_edge_lern_zeitraum"] = [r["mn"], r["mx"]]

        leb["vp_ereignis_zeilen_gesamt"] = conn.execute(
            "SELECT COUNT(*) c FROM vp_ereignis").fetchone()["c"]
        leb["vp_ereignis_nach_art"] = {
            row["art"]: row["n"] for row in conn.execute(
                "SELECT art, COUNT(*) n FROM vp_ereignis GROUP BY art")
        }
        leb["vp_ereignis_taktarbeit_anteil"] = None
        arb = leb["vp_ereignis_nach_art"].get("puls_arbeit", 0)
        leer = leb["vp_ereignis_nach_art"].get("puls_leer", 0)
        if (arb + leer) > 0:
            leb["vp_ereignis_taktarbeit_anteil"] = round(arb / (arb + leer), 5)

        leb["vp_paket_log_zeilen_gesamt"] = conn.execute(
            "SELECT COUNT(*) c FROM vp_paket_log").fetchone()["c"]
        leb["vp_paket_log_seit_letztem_traum"] = conn.execute(
            "SELECT COUNT(*) c FROM vp_paket_log WHERE epoch_sekunden > ?",
            (since_epoch,)).fetchone()["c"]

        leb["hypothese_artikel_gesamt"] = conn.execute(
            "SELECT COUNT(*) c FROM artikel WHERE art='hypothese'").fetchone()["c"]
        leb["hypothese_artikel_letzte_24h"] = conn.execute(
            "SELECT COUNT(*) c FROM artikel WHERE art='hypothese' AND "
            "erzeugt_am > datetime('now','-1 day')").fetchone()["c"]
        leb["hypothese_offen_status_like_open"] = conn.execute(
            "SELECT COUNT(*) c FROM artikel WHERE art='hypothese' AND "
            "status LIKE 'OPEN%'").fetchone()["c"]
        leb["folgerung_offen"] = conn.execute(
            "SELECT COUNT(*) c FROM folgerung WHERE status='offen'").fetchone()["c"]
        leb["kante_widerspricht_attacks"] = conn.execute(
            "SELECT COUNT(*) c FROM kante WHERE art IN ('widerspricht','attacks')"
        ).fetchone()["c"]
        out["lebendigkeit"] = leb

        # ── Primaersignal: wiederholte echte Fragen aus vp_paket_log ─────
        rows = conn.execute(
            "SELECT frage, epoch_sekunden FROM vp_paket_log "
            "WHERE epoch_sekunden > ? ORDER BY epoch_sekunden DESC LIMIT ?",
            (since_epoch, max(200, limit * 10)),
        ).fetchall()
        from collections import Counter
        norm_counts: Counter = Counter()
        norm_beispiel: Dict[str, str] = {}
        for r in rows:
            frage = (r["frage"] or "").strip()
            if not frage:
                continue
            norm = re.sub(r"\s+", " ", frage.lower()).strip(" ?!.")
            norm_counts[norm] += 1
            norm_beispiel.setdefault(norm, frage)
        wiederholte = [
            {"frage": norm_beispiel[n], "anzahl": c}
            for n, c in norm_counts.most_common(limit) if c >= 2
        ]
        out["wiederholte_fragen"] = wiederholte
    except sqlite3.OperationalError as e:
        out["fehler"] = str(e)
        conn.close()
        return out
    finally:
        try:
            conn.close()
        except Exception:
            pass

    if not out["wiederholte_fragen"]:
        return out

    # ── Live-Nachfrage bei paket() -- der Puls-Entitaet echte Schnittstelle ──
    kandidat = out["wiederholte_fragen"][0]
    try:
        sys.path.insert(0, PULS_WERKZEUG_DIR)
        import vorprozessor as _vp  # type: ignore
        result = _vp.paket(kandidat["frage"], budget=8)
    except Exception as e:
        out["fehler"] = f"paket()-Aufruf fehlgeschlagen: {type(e).__name__}: {e}"
        return out

    resolution = result.get("resolution", {})
    treffer_n = len(result.get("treffer") or [])
    hyp_n = len(result.get("hypothesen") or [])
    gegen_n = len(result.get("gegenseite") or [])
    ist_fehltreffer = (
        resolution.get("klasse") in _PULS_MISS_KLASSEN or treffer_n == 0
    )
    out["live_paket_ergebnis"] = {
        "frage": kandidat["frage"], "resolution_klasse": resolution.get("klasse"),
        "konfidenz": resolution.get("konfidenz"), "treffer_n": treffer_n,
        "hypothesen_n": hyp_n, "gegenseite_n": gegen_n,
        "hyperposition_kandidaten": [
            k.get("id") for k in (result.get("hyperposition") or {}).get("kandidaten", [])
        ] if result.get("hyperposition") else [],
        "paket_id": result.get("paket_id"), "ist_fehltreffer": ist_fehltreffer,
    }

    if ist_fehltreffer:
        out["top_thema"] = {
            "thema": kandidat["frage"],
            "anzahl": kandidat["anzahl"],
            "beispiel_prompt": kandidat["frage"],
            "korpus_treffer_n": treffer_n,
            "quelle": "puls",
            "puls_resolution": resolution.get("klasse"),
        }
    return out


# ---------------------------------------------------------------------------
# Phase 1b-SEKUNDAER: LUECKEN-LESEN aus der Mistral-Retrieval-Vorstufe
# ---------------------------------------------------------------------------
# War bis 19.08. die PRIMAERE Quelle -- per Eigner-Kurskorrektur jetzt
# sekundaer/zusaetzlich, NACHRANGIG gegenueber der Puls-Entitaet oben.
# Eignerauftrag (19.08., erste Fassung): liest, was mistral_prestage (die
# Vorstufe vor jeder Zero-Antwort) nicht fand oder als "unbekannt"
# markierte -- Tabelle mv_prestage_turns, Spalte epistemik_json =
# {"bekannt":[...], "unbekannt":[...]}, gepflegt von
# /opt/entityos/the artefact/clayverse/mistral_prestage/store.py (NUR
# GELESEN, nie importiert -- PrestageStore.__init__ fuehrt ALTER TABLE aus,
# das ist NICHT unser Bereich; wir lesen dieselben Tabellen ueber unsere
# eigene mode=ro-Verbindung).

def read_prestage_gaps(cfg: Dict[str, str], since_epoch: float) -> Dict[str, Any]:
    """Liest, was die Retrieval-Vorstufe seit dem letzten Traum als
    epistemische Luecke protokolliert hat. Rein lesend, wiki.db mode=ro."""
    limit = int(cfg["REPLAY_LIMIT"])
    out: Dict[str, Any] = {"verfuegbar": False, "eintraege": [], "lernbild": [],
                            "top_thema": None, "fehler": None}
    conn = open_wiki_readonly()
    try:
        rows = conn.execute(
            "SELECT prestage_id, raw_prompt, routing_key, epistemik_json, "
            "korpus_treffer_n, created_at FROM mv_prestage_turns "
            "WHERE epistemik_unbekannt_n > 0 AND created_at > ? "
            "ORDER BY created_at DESC LIMIT ?",
            (since_epoch, limit),
        ).fetchall()
        out["verfuegbar"] = True

        eintraege: List[Dict[str, Any]] = []
        for r in rows:
            try:
                ep = json.loads(r["epistemik_json"] or "{}")
            except (json.JSONDecodeError, TypeError):
                ep = {}
            for thema in (ep.get("unbekannt") or []):
                eintraege.append({
                    "thema": str(thema)[:200],
                    "raw_prompt": (r["raw_prompt"] or "")[:300],
                    "routing_key": r["routing_key"],
                    "korpus_treffer_n": r["korpus_treffer_n"],
                    "prestage_id": r["prestage_id"],
                    "created_at": r["created_at"],
                })
        out["eintraege"] = eintraege[:limit]

        try:
            lb_rows = conn.execute(
                "SELECT routing_key, hatte_luecke, n, n_nicht_ok, "
                "n_uebersetzung_ausgefallen, n_selbst_gemeldete_luecke "
                "FROM mv_prestage_lernbild WHERE hatte_luecke=1 "
                "ORDER BY n_nicht_ok DESC, n DESC LIMIT ?",
                (limit,),
            ).fetchall()
            out["lernbild"] = [dict(x) for x in lb_rows]
        except sqlite3.OperationalError:
            pass  # Sicht existiert (noch) nicht -- kein Fehler, nur kein Signal

        if eintraege:
            from collections import Counter
            counts = Counter(e["thema"].lower() for e in eintraege)
            top_lc, n = counts.most_common(1)[0]
            beispiel = next(e for e in eintraege if e["thema"].lower() == top_lc)
            out["top_thema"] = {
                "thema": beispiel["thema"],
                "anzahl": n,
                "beispiel_prompt": beispiel["raw_prompt"],
                "korpus_treffer_n": beispiel["korpus_treffer_n"],
                "quelle": "mistral",
            }
    except sqlite3.OperationalError as e:
        # mv_prestage_turns/-lernbild existieren nicht (z.B. Vorstufe noch nie
        # gelaufen) -- kein Fehler, nur: Lernschicht noch zu duenn.
        out["fehler"] = str(e)
    finally:
        conn.close()
    return out


# Identisch zu vorprozessor._STOPWORDER (gelesen, nicht neu erfunden) --
# ohne diesen Filter zaehlte "was ist iar?" ein AND-Match auf "was"+"ist"
# (haeufige Fuellwoerter) + "iar" als "Treffer", obwohl der gefundene Artikel
# nur zufaellig "was"/"ist" irgendwo enthaelt und NICHTS über IAR erklaert --
# gemessener Fehlfund beim ersten Testlauf (19.08.), hier korrigiert.
_STOPWORDER = {"the", "a", "an", "is", "are", "was", "were", "of", "for", "to", "in", "on",
               "and", "or", "der", "die", "das", "den", "dem", "des", "ein", "eine", "einer",
               "und", "oder", "von", "im", "am", "zu", "fuer", "für", "ist", "sind", "war",
               "waren", "mit", "bei", "wie", "was", "welche", "welcher", "welches",
               "welchem", "welchen", "wer", "wo"}


def _fts_words(text: str) -> List[str]:
    """Wie PrestageStore._korpus_treffer_n, ZUSAETZLICH stopwortgefiltert wie
    vorprozessor._STOPWORDER -- sonst zaehlen Fuellwoerter als Suchbegriff."""
    woerter = [w for w in re.findall(r"[A-Za-zÄÖÜäöüß0-9]+", text or "")
               if len(w) >= 3 and w.lower() not in _STOPWORDER]
    return woerter[:8]


def _fts_query_rows(conn: sqlite3.Connection, query: str, limit: int = 3) -> List[sqlite3.Row]:
    return conn.execute(
        "SELECT s.artikel_id AS artikel_id, s.titel AS titel, "
        "snippet(fts_index_artikel, 1, '[', ']', '...', 12) AS ausschnitt "
        "FROM fts_index_artikel f JOIN artikel_suchtext s ON s.id = f.rowid "
        "WHERE fts_index_artikel MATCH ? LIMIT ?",
        (query, limit),
    ).fetchall()


def search_corpus_for_gap(top_thema: Dict[str, Any]) -> Dict[str, Any]:
    """Rein mechanische FTS-Suche nach der gemeldeten Luecke -- KEIN Erfinden.

    ⚠️ Ein einzelnes OR-Match auf ein haeufiges Wort (z.B. "age") ist KEIN
    Beleg -- gemessen: die erste Version dieser Funktion meldete fuer die
    Luecke "age of Gabriel Gschaider" einen "Treffer", weil irgendein
    voellig fachfremder Artikel zufaellig sowohl "age" als auch "Gabriel"
    enthielt. Deshalb zaehlt NUR ein AND-Treffer (alle Suchwoerter im selben
    Artikel) als "treffer" im Sinn von write_gap_article() -- ein reiner
    OR-Fund landet separat unter schwache_naehe, aendert aber NICHT die
    treffer-Zahl und loest damit auch keine 'geklaert'-Aussage aus."""
    words = _fts_words(top_thema["thema"]) or _fts_words(top_thema["beispiel_prompt"])
    if not words:
        return {"treffer": 0, "suchwoerter": []}

    conn = open_wiki_readonly()
    try:
        and_query = " ".join('"' + w.replace('"', '') + '"' for w in words)  # FTS5-Default: AND
        try:
            and_rows = _fts_query_rows(conn, and_query)
        except Exception:
            and_rows = []

        out: Dict[str, Any] = {
            "treffer": len(and_rows),
            "suchwoerter": words,
            "such_modus": "AND (alle Woerter im selben Artikel)",
            "kandidaten": [
                {"artikel_id": r["artikel_id"], "titel": r["titel"], "ausschnitt": r["ausschnitt"]}
                for r in and_rows
            ],
        }

        if not and_rows and len(words) > 1:
            or_query = " OR ".join('"' + w.replace('"', '') + '"' for w in words)
            try:
                or_rows = _fts_query_rows(conn, or_query)
            except Exception:
                or_rows = []
            out["schwache_naehe"] = [
                {"artikel_id": r["artikel_id"], "titel": r["titel"], "ausschnitt": r["ausschnitt"]}
                for r in or_rows
            ]
            out["schwache_naehe_hinweis"] = (
                "Nur Einzelwort-OR-Treffer, KEIN belastbarer Fund -- wird NICHT als "
                "'geklaert' gewertet."
            )
        return out
    except Exception as e:
        return {"treffer": 0, "suchwoerter": words, "fehler": f"{type(e).__name__}: {e}"}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Phase 2: SYNTHESE (hoechstens ein Mistral-Aufruf)
# ---------------------------------------------------------------------------

def _parse_json_loose(text: str) -> Optional[Dict]:
    """Robuster JSON-Parser fuer LLM-Antworten (Codefences, Praefix-Text)."""
    if not text:
        return None
    text = text.strip()
    if "```" in text:
        lines, buf, in_json = text.split("\n"), [], False
        for line in lines:
            if line.strip().startswith("```") and not in_json:
                in_json = True
                continue
            if line.strip() == "```" and in_json:
                break
            if in_json:
                buf.append(line)
        if buf:
            text = "\n".join(buf)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return None


def run_phase_synthesis(cfg: Dict[str, str], obs: Dict[str, Any],
                         luecken: Dict[str, Any],
                         luecken_suche: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Liefert {"reflexionen": [...], "muster": [...], "llm_verwendet": bool,
    "modell": str|None, "fehler": str|None}.

    Luecken (mv_prestage_turns/-lernbild aus der Retrieval-Vorstufe) werden
    PRIORISIERT: sie stehen zuerst im Prompt und die Systemanweisung verbietet
    explizit, eine offene Luecke zu erfinden -- die mechanische FTS-Suche
    (luecken_suche) ist die einzig zulaessige Quelle fuer "geklaert"."""
    n_bau = len(obs["neue_bauschritte"])
    n_erf = len(obs["erfolge"])
    n_feh = len(obs["fehlschlaege"])
    n_pak = len(obs["arbeitspakete_fertig"])
    n_luecken = len(luecken.get("eintraege") or [])

    fallback = {
        "reflexionen": [
            f"Mechanische Beobachtung (kein LLM): seit dem letzten Traum "
            f"{n_bau} neue Bauschritte, {n_erf} Erfolge, {n_feh} Fehlschlaege, "
            f"{n_pak} abgeschlossene Arbeitspakete, {obs['kuration_offen']} "
            f"offene Kurations-Faelle, {n_luecken} von der Vorstufe gemeldete "
            f"Wissensluecken."
        ],
        "muster": [],
        "llm_verwendet": False,
        "modell": None,
        "fehler": None,
    }

    if n_bau == 0 and n_erf == 0 and n_feh == 0 and n_pak == 0 and n_luecken == 0:
        fallback["reflexionen"] = ["Traumlose Phase -- seit dem letzten Traum keine "
                                    "neuen Bauschritte, Erfolge, Arbeitspakete oder "
                                    "Vorstufen-Luecken gefunden."]
        return fallback

    if not load_mistral_key_into_env():
        fallback["fehler"] = "kein MISTRAL_API_KEY in /etc/clayverse/freie-zugaenge.env"
        return fallback

    try:
        sys.path.insert(0, MISTRAL_TOOLS_DIR)
        from mistral_inference import chat as mistral_chat  # type: ignore
    except Exception as e:
        fallback["fehler"] = f"mistral_inference nicht importierbar: {e}"
        return fallback

    payload = {
        "beobachtung": obs,
        "vorstufen_luecken": luecken.get("eintraege", [])[:10],
        "vorstufen_lernbild": luecken.get("lernbild", [])[:10],
        "mechanische_korpus_suche_zur_top_luecke": luecken_suche,
    }
    prompt_obs = json.dumps(payload, ensure_ascii=False, default=str)[:3500]
    system = (
        "Du bist Zeros Selbstreflexions-Prozess in einer budgetierten "
        "Offline-Traumphase. Du bekommst: (1) eine mechanische Zusammenfassung "
        "dessen, was seit dem letzten Traum in der Wissensbasis (wiki.db) "
        "passiert ist, und (2) Wissensluecken, die Zeros Retrieval-Vorstufe "
        "(mistral_prestage) protokolliert hat -- Fragen, die sie als "
        "'unbekannt' markierte -- plus das Ergebnis einer rein mechanischen "
        "FTS-Suche danach im Korpus. PRIORITAET: geh zuerst auf die "
        "Vorstufen-Luecken ein, dann auf den Rest. "
        "⚠️ HARTE REGEL: Du darfst eine offene Luecke NIEMALS selbst "
        "beantworten oder eine Vermutung als Fakt hinstellen -- auch nicht "
        "aus Weltwissen. Wenn mechanische_korpus_suche_zur_top_luecke "
        "treffer=0 zeigt, ist die Luecke UNGEKLAERT und bleibt es in deiner "
        "Antwort auch. Nur wenn treffer>0, darfst du den gefundenen Artikel "
        "(Titel/Ausschnitt) referenzieren -- nie den Inhalt ausdenken. "
        "Formuliere 2-3 kurze, sachliche Reflexionen auf Deutsch, "
        "Ich-Perspektive. Antworte NUR mit validem JSON: "
        '{"reflexionen": ["..."], "muster": ["..."]}'
    )

    model = cfg["LLM_MODEL"]
    retries = int(cfg["LLM_RETRIES"])
    last_err = None
    for attempt in range(retries + 1):
        if attempt > 0:
            time.sleep(5)
        try:
            result = mistral_chat(
                prompt_obs,
                model=model,
                system=system,
                max_tokens=int(cfg["LLM_MAX_TOKENS"]),
                temperature=0.3,
                reasoning_effort="none",  # mistral-small-latest: nur 'none'|'high' gueltig
                json_mode=True,
                prompt_cache_key="eos-dream-v1",
                timeout=int(cfg["LLM_TIMEOUT_SEC"]),
            )
            answers = result.get("answers") or []
            text = answers[0]["content"] if answers else ""
            parsed = _parse_json_loose(text)
            if parsed and isinstance(parsed.get("reflexionen"), list) and parsed["reflexionen"]:
                return {
                    "reflexionen": [str(r)[:500] for r in parsed["reflexionen"][:5]],
                    "muster": [str(m)[:300] for m in (parsed.get("muster") or [])[:5]],
                    "llm_verwendet": True,
                    "modell": result.get("model") or model,
                    "fehler": None,
                }
            last_err = "LLM-Antwort ohne verwertbares JSON"
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            LOG.warning("Mistral-Aufruf fehlgeschlagen (Versuch %d/%d): %s",
                        attempt + 1, retries + 1, last_err)

    fallback["fehler"] = last_err
    return fallback


# ---------------------------------------------------------------------------
# Phase 3: KONSOLIDIERUNG -- eigene DB + genau EIN neuer wiki.db-Artikel
# ---------------------------------------------------------------------------

def _artikel_text(obs: Dict[str, Any], synth: Dict[str, Any]) -> str:
    teile = ["ZERO-TRAUM -- automatisch erzeugte Reflexion (eos-dream-daemon)", ""]
    teile += ["REFLEXIONEN"] + [f"- {r}" for r in synth["reflexionen"]] + [""]
    if synth.get("muster"):
        teile += ["MUSTER"] + [f"- {m}" for m in synth["muster"]] + [""]
    teile += [
        "BEOBACHTUNG (mechanisch aus wiki.db, seit " + obs["seit"] + ")",
        f"Neue Bauschritte: {len(obs['neue_bauschritte'])}",
    ]
    teile += [f"  - {b['titel']}" for b in obs["neue_bauschritte"][:15]]
    teile += [f"Erfolge: {len(obs['erfolge'])}"]
    teile += [f"  - {e['titel']}: {e['wirkung']}" for e in obs["erfolge"][:10]]
    teile += [f"Fehlschlaege: {len(obs['fehlschlaege'])}"]
    teile += [f"  - {e['titel']}: {e['wirkung']}" for e in obs["fehlschlaege"][:10]]
    teile += [f"Abgeschlossene Arbeitspakete: {len(obs['arbeitspakete_fertig'])}"]
    teile += [f"  - ({p['besteller']}) {p['auftrag']}" for p in obs["arbeitspakete_fertig"][:10]]
    teile += [f"Offene Kurations-Faelle: {obs['kuration_offen']}"]
    teile += ["", f"LLM verwendet: {synth['llm_verwendet']} (Modell: {synth.get('modell')})"]
    if synth.get("fehler"):
        teile += [f"LLM-Fehler (Fallback griff): {synth['fehler']}"]
    return "\n".join(teile)


def _fts_insert_new(sql: sqlite3.Connection, artikel_id: str, titel: str,
                     text: str, blase: Optional[str]) -> None:
    """Fuegt Suchtext + FTS-Eintrag fuer eine NEUE (garantiert noch nicht
    vorhandene) artikel_id ein -- Protokoll identisch zu auffindbar() aus
    /opt/agentzero-export/repo/agentZero/code/export/bau_ins_wiki.py, dem
    einzigen Weg, der einen Artikel tatsaechlich auffindbar macht (2498 von
    2536 Bauschritten waren dort ohne dieses Protokoll unauffindbar
    liegengeblieben -- gemessener Befund, kein Vermuten)."""
    zeile = sql.execute(
        "INSERT INTO artikel_suchtext(artikel_id,titel,text,blase,indiziert) "
        "VALUES(?,?,?,?,1)", (artikel_id, titel, text, blase),
    ).lastrowid
    sql.execute(
        "INSERT INTO fts_index_artikel(rowid,titel,text) VALUES(?,?,?)",
        (zeile, titel, text),
    )


def write_wiki_article(session_id: str, obs: Dict[str, Any],
                        synth: Dict[str, Any], elapsed_sec: float) -> str:
    now = datetime.now(timezone.utc)
    artikel_id = f"zero-traum-{now.strftime('%Y%m%d')}-{session_id}"
    titel = f"Zero-Traum {now.strftime('%Y-%m-%d')}"
    text = _artikel_text(obs, synth)
    metadaten = json.dumps({
        "session_id": session_id,
        "beobachtung": obs,
        "reflexionen": synth["reflexionen"],
        "muster": synth["muster"],
        "llm_verwendet": synth["llm_verwendet"],
        "modell": synth.get("modell"),
        "llm_fehler": synth.get("fehler"),
        "dauer_sek": round(elapsed_sec, 1),
        "erzeuger": "eos-dream-daemon",
    }, ensure_ascii=False, default=str)

    conn = sqlite3.connect(WIKI_DB_PATH, timeout=30.0)
    conn.execute("PRAGMA busy_timeout=30000")
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "INSERT INTO artikel (id, art, titel, quelle, quell_hash, datum, "
            "metadaten, offene_fragen, belegt, erzeugt_am, wirt, zuletzt_von, "
            "herkunft, verfallen, protected) VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,0,0)",
            (
                artikel_id, "zero_traum", titel, "eos-dream-daemon", None,
                now.strftime("%Y-%m-%d"), metadaten, "[]", 1,
                now.isoformat(), "clayverse", "eos-dream-daemon", "gemessen",
            ),
        )
        _fts_insert_new(conn, artikel_id, titel, text, "zero_traum")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return artikel_id


def write_gap_article(session_id: str, top_thema: Dict[str, Any],
                       suche: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    """Schliesst die Schleife zur Retrieval-Vorstufe: schreibt EINEN Artikel
    zur haeufigsten seit dem letzten Traum gemeldeten Wissensluecke, verbatim
    zitiert, NIE erfunden. Rueckgabe (artikel_id, hinweis) -- hinweis erklaert
    ein Uebersprungen (z.B. schon dokumentiert).

    Dedup: dieselbe Lueckenfrage bekommt nicht bei jedem Zyklus einen neuen
    Artikel -- das wuerde wiki.db bei einer dauerhaft offenen Luecke fluten.
    Stattdessen wird der bestehende Artikel als 'schon dokumentiert' erkannt
    (Titel-Gleichheit) und uebersprungen; die Beobachtung bleibt trotzdem im
    eigenen dream_log."""
    now = datetime.now(timezone.utc)
    frage = (top_thema.get("beispiel_prompt") or top_thema["thema"]).strip()
    titel = f"Wissensluecke: {frage}"[:200]
    quelle = top_thema.get("quelle", "unbekannt")
    quelle_text = {
        "puls": "DER PULS-ENTITAET (vorprozessor.paket()/vp_paket_log, LLM-frei, PRIMAER)",
        "mistral": "DER MISTRAL-RETRIEVAL-VORSTUFE (mv_prestage_turns, SEKUNDAER)",
    }.get(quelle, f"unbekannte Quelle ({quelle})")
    quelle_tabelle = {
        "puls": "vp_paket_log + vorprozessor.paket() live",
        "mistral": "mv_prestage_turns",
    }.get(quelle, quelle)

    conn = sqlite3.connect(WIKI_DB_PATH, timeout=30.0)
    conn.execute("PRAGMA busy_timeout=30000")
    try:
        exists = conn.execute(
            "SELECT id FROM artikel WHERE art='zero_luecke' AND titel=?", (titel,)
        ).fetchone()
        if exists:
            return None, f"bereits dokumentiert als {exists[0]}"

        treffer = suche.get("treffer", 0)
        if treffer > 0:
            kand = suche["kandidaten"][0]
            befund = (
                f"MOEGLICHER TREFFER im Korpus (mechanische FTS-Suche, KEINE "
                f"inhaltliche Bewertung durch das LLM): Artikel '{kand['titel']}' "
                f"(id={kand['artikel_id']}). Ausschnitt (verbatim): {kand['ausschnitt']}"
            )
        else:
            befund = (
                f"UNGEKLAERT: der Korpus enthaelt zu den Suchwoertern "
                f"{suche.get('suchwoerter')} keinen FTS-Treffer (Stand "
                f"{now.strftime('%Y-%m-%d')}). Nichts erfunden -- diese Luecke "
                f"ist bestaetigt offen und braucht eine echte Quelle."
            )

        zusatz = ""
        if quelle == "puls" and top_thema.get("puls_resolution"):
            zusatz = (f"\nEntitaetsaufloesung bei erneutem Live-Aufruf von paket(): "
                       f"{top_thema['puls_resolution']} (kein sicherer Anker -- "
                       f"resolve_entities() ratet nie).")

        text = "\n".join([
            f"WISSENSLUECKE AUS {quelle_text}",
            "",
            f"Frage verbatim: {frage}",
            f"Von der Quelle als Luecke/unbekannt/Fehltreffer erkannt: {top_thema['thema']}",
            f"Haeufigkeit seit letztem Traum: {top_thema['anzahl']}",
            f"Treffer bei der Anfrage (mechanisch gezaehlt): {top_thema.get('korpus_treffer_n')}",
            zusatz,
            "",
            befund,
        ])

        artikel_id = "zero-luecke-" + hashlib.sha1(titel.encode("utf-8")).hexdigest()[:12]
        metadaten = json.dumps({
            "session_id": session_id,
            "quelle": quelle,
            "quelle_tabelle": quelle_tabelle,
            "thema": top_thema["thema"],
            "anzahl_seit_letztem_traum": top_thema["anzahl"],
            "beispiel_prompt": frage,
            "korpus_treffer_n_bei_erkennung": top_thema.get("korpus_treffer_n"),
            "puls_resolution": top_thema.get("puls_resolution"),
            "mechanische_suche": suche,
            "erzeuger": "eos-dream-daemon",
        }, ensure_ascii=False, default=str)

        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "INSERT INTO artikel (id, art, titel, quelle, quell_hash, datum, "
            "metadaten, offene_fragen, belegt, erzeugt_am, wirt, zuletzt_von, "
            "herkunft, verfallen, protected) VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,0,0)",
            (
                artikel_id, "zero_luecke", titel, "eos-dream-daemon",
                quelle_tabelle, now.strftime("%Y-%m-%d"), metadaten,
                json.dumps([frage], ensure_ascii=False), 1, now.isoformat(),
                "clayverse", "eos-dream-daemon", "gemessen",
            ),
        )
        _fts_insert_new(conn, artikel_id, titel, text, "zero_luecke")
        conn.commit()
        return artikel_id, None
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Ein voller Zyklus
# ---------------------------------------------------------------------------

def run_dream_cycle(cfg: Dict[str, str]) -> Dict[str, Any]:
    t_start = time.time()
    session_id = str(uuid.uuid4())[:8]
    max_runtime = float(cfg["MAX_RUNTIME_SEC"])
    conn = get_dream_conn()

    save_state(conn, status="dreaming",
               last_dream_start=datetime.now(timezone.utc).isoformat())

    last_end_epoch = get_last_dream_end(conn)
    if last_end_epoch is None:
        since_epoch = time.time() - 86400.0  # erster Lauf: letzte 24h
    else:
        since_epoch = last_end_epoch
    since_iso = datetime.fromtimestamp(since_epoch, tz=timezone.utc).isoformat()

    result: Dict[str, Any] = {"session_id": session_id}

    # Phase 1: Replay (mechanisch)
    p1_start = time.time()
    obs = run_phase_replay(cfg, since_iso, since_epoch)
    p1_dur = time.time() - p1_start
    log_phase(conn, session_id, "replay", obs, p1_dur)
    result["phase1_replay"] = {"dauer_sek": round(p1_dur, 2), "beobachtung": obs}

    # Phase 1b: Luecken-Lesen -- PRIMAER die Puls-Entitaet (vorprozessor.py/
    # puls.py, LLM-frei), SEKUNDAER die Mistral-Vorstufe (mv_prestage_turns),
    # nur falls die Puls-Entitaet keinen Fehltreffer liefert. Mechanisch,
    # read-only bis auf den einen sanktionierten paket()-Live-Aufruf.
    p1b_start = time.time()
    puls_luecken = read_puls_gaps(cfg, since_epoch)
    mistral_luecken = read_prestage_gaps(cfg, since_epoch)

    if puls_luecken.get("top_thema"):
        top_thema = puls_luecken["top_thema"]
        lueckenquelle = "puls"
    elif mistral_luecken.get("top_thema"):
        top_thema = mistral_luecken["top_thema"]
        lueckenquelle = "mistral"
    else:
        top_thema = None
        lueckenquelle = None

    luecken_suche = None
    if top_thema:
        luecken_suche = search_corpus_for_gap(top_thema)
    p1b_dur = time.time() - p1b_start
    log_phase(conn, session_id, "luecken_lesen", {
        "puls": puls_luecken, "mistral": mistral_luecken,
        "gewaehlte_quelle": lueckenquelle, "korpus_suche": luecken_suche,
    }, p1b_dur)
    result["phase1b_luecken"] = {
        "dauer_sek": round(p1b_dur, 2),
        "gewaehlte_quelle": lueckenquelle,
        "top_thema": top_thema,
        "korpus_suche": luecken_suche,
        "puls_lebendigkeit": puls_luecken.get("lebendigkeit"),
        "puls_wiederholte_fragen": puls_luecken.get("wiederholte_fragen"),
        "puls_live_paket_ergebnis": puls_luecken.get("live_paket_ergebnis"),
        "puls_fehler": puls_luecken.get("fehler"),
        "mistral_anzahl_luecken": len(mistral_luecken.get("eintraege") or []),
        "mistral_fehler": mistral_luecken.get("fehler"),
    }
    # Fuer die spaeteren Phasen (Synthese/Konsolidierung) bleibt der Rest
    # des Codes bei den Namen 'luecken'/'luecken_suche' -- 'luecken' zeigt
    # jetzt auf die gewaehlte Quelle (Puls bevorzugt, Mistral als Fallback),
    # behaelt aber dieselbe eintraege/lernbild-Form aus read_prestage_gaps
    # fuer den Fall, dass Phase 2 zusaetzlichen Mistral-Kontext einbezieht.
    luecken = {**mistral_luecken, "top_thema": top_thema}

    if time.time() - t_start > max_runtime:
        save_state(conn, status="abgebrochen_budget")
        result["abgebrochen"] = "Laufzeit-Budget vor Phase 2 erschoepft"
        conn.close()
        return result

    # Phase 2: Synthese (hoechstens ein LLM-Aufruf, Luecken priorisiert)
    p2_start = time.time()
    synth = run_phase_synthesis(cfg, obs, luecken, luecken_suche)
    p2_dur = time.time() - p2_start
    log_phase(conn, session_id, "synthesis", synth, p2_dur)
    for m in synth.get("muster", []):
        log_hypothesis(conn, session_id, m)
    result["phase2_synthesis"] = {"dauer_sek": round(p2_dur, 2), **synth}

    # Phase 3: Konsolidierung -- eigene DB + Artikel in wiki.db
    p3_start = time.time()
    wiki_article_id = None
    wiki_error = None
    try:
        elapsed_so_far = time.time() - t_start
        wiki_article_id = write_wiki_article(session_id, obs, synth, elapsed_so_far)
    except Exception as e:
        wiki_error = f"{type(e).__name__}: {e}"
        LOG.error("Konnte wiki.db-Zusammenfassungsartikel nicht schreiben: %s", wiki_error)

    gap_article_id = None
    gap_note = None
    gap_error = None
    if luecken.get("top_thema"):
        try:
            gap_article_id, gap_note = write_gap_article(
                session_id, luecken["top_thema"], luecken_suche or {"treffer": 0})
        except Exception as e:
            gap_error = f"{type(e).__name__}: {e}"
            LOG.error("Konnte wiki.db-Luecken-Artikel nicht schreiben: %s", gap_error)

    p3_dur = time.time() - p3_start
    log_phase(conn, session_id, "consolidation",
              {"wiki_article_id": wiki_article_id, "fehler": wiki_error,
               "gap_article_id": gap_article_id, "gap_note": gap_note,
               "gap_fehler": gap_error}, p3_dur)
    result["phase3_consolidation"] = {
        "dauer_sek": round(p3_dur, 2),
        "wiki_article_id": wiki_article_id,
        "fehler": wiki_error,
        "gap_article_id": gap_article_id,
        "gap_note": gap_note,
        "gap_fehler": gap_error,
    }

    total_elapsed = time.time() - t_start
    now = datetime.now(timezone.utc)
    row = conn.execute("SELECT total_dreams FROM dream_state ORDER BY id DESC LIMIT 1").fetchone()
    total_dreams = (row["total_dreams"] if row else 0) + 1
    save_state(conn, status="completed", last_dream_end=now.isoformat(),
               last_dream_end_epoch=now.timestamp(), total_dreams=total_dreams)
    log_phase(conn, session_id, "summary", result, total_elapsed)
    conn.close()

    result["gesamt_dauer_sek"] = round(total_elapsed, 2)
    result["cpu_last_pct_bei_start"] = get_cpu_load_pct()
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def get_status() -> Dict[str, Any]:
    conn = get_dream_conn()
    row = conn.execute("SELECT * FROM dream_state ORDER BY id DESC LIMIT 1").fetchone()
    n_log = conn.execute("SELECT COUNT(*) AS n FROM dream_log").fetchone()["n"]
    n_hyp = conn.execute("SELECT COUNT(*) AS n FROM dream_hypotheses").fetchone()["n"]
    conn.close()
    if not row:
        return {"status": "noch_nie_getraeumt"}
    return {
        "status": row["status"],
        "total_dreams": row["total_dreams"],
        "last_dream_start": row["last_dream_start"],
        "last_dream_end": row["last_dream_end"],
        "dream_log_zeilen": n_log,
        "dream_hypotheses_zeilen": n_hyp,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="EntityOS Dream Daemon (oneshot)")
    parser.add_argument("--run", action="store_true", help="Einen Traum-Zyklus versuchen")
    parser.add_argument("--force", action="store_true",
                         help="Sperrzeit/Lastpruefung ignorieren (nur fuer Verifikation)")
    parser.add_argument("--status", action="store_true", help="Status anzeigen und beenden")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler(sys.stdout)],
    )

    if args.status:
        print(json.dumps(get_status(), indent=2, ensure_ascii=False))
        return 0

    if not args.run:
        parser.print_help()
        return 1

    cfg = load_config()
    lock_fh = acquire_lock()
    if lock_fh is None:
        LOG.warning("Bereits ein Lauf aktiv (Lockfile gesperrt) -- beende ohne Aktion")
        print(json.dumps({"status": "uebersprungen", "grund": "bereits aktiv"}))
        return 0

    try:
        conn = get_dream_conn()
        ok, grund = should_dream(conn, cfg)
        conn.close()
        if not ok and not args.force:
            LOG.info("Kein Traum diesmal: %s", grund)
            print(json.dumps({"status": "uebersprungen", "grund": grund}, ensure_ascii=False))
            return 0
        if not ok and args.force:
            LOG.warning("--force gesetzt, ignoriere: %s", grund)

        LOG.info("Starte Traum-Zyklus...")
        result = run_dream_cycle(cfg)
        LOG.info("Traum-Zyklus fertig: %s", json.dumps(result, ensure_ascii=False)[:500])
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        return 0
    finally:
        lock_fh.close()
        try:
            LOCK_PATH.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
