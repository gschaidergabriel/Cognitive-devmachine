#!/usr/bin/env python3
"""eos_hypothesen.py -- EntityOS Hypothesen-Generator (LLM-frei, mechanisch).

Fuellt die gemessene Luecke: die Retrieval-Entitaet (Puls/Vorprozessor auf
/var/lib/clay/wiki.db) hat 1.645 hypothese- + 272 gegenhypothese-Artikel,
ALLE aus dem Bulk-Import vom 14.08. -- 0 neue seit 24h, weil beide
Retrieval-Module nur VORHANDENE Hypothesen lesen. Dieses Skript ERZEUGT
neue, offene Kandidaten-Hypothesen -- mechanisch, regelbasiert, KEIN
Modellaufruf, kein Netzwerkzugriff.

Quellen (beide read-only ausser den eigenen neuen Zeilen):
  1. artikel WHERE art='zero_luecke'  -- vom eos-dream-daemon geschriebene,
     bereits als wiederkehrend erkannte Wissensluecken.
  2. vp_paket_log WHERE orte_json='[]' -- echte Nulltreffer aus dem
     laufenden Puls-Betrieb. Werden per Schluesselwort-Signatur geclustert;
     nur WIEDERKEHRENDE Cluster (>= CLUSTER_MIN Zeilen) werden Kandidaten.

Schreibt NUR:
  - neue artikel-Zeilen (art='hypothese', eigene id 'eos-hyp-<hash>'),
    korrekt in artikel_suchtext + fts_index_artikel indiziert (gleiches
    externes-Content-FTS5-Muster wie der Rest des Wikis) -- das macht sie
    per Retrieval (paket()) auffindbar, sobald ein kuenftiger Aufruf
    dieselben Schluesselwoerter trifft.
  - neue folgerung-Zeilen ueber die vorhandene, sanktionierte
    Schreib-Fassade /opt/clayverse/werkzeug/folgerung.py (NICHT selbst
    SQL gegen die folgerung-Tabelle schreiben) -- IMMER status='offen',
    NIE 'gestuetzt'/'widerlegt'. Jede folgerung bekommt mind. einen
    beleg_art='artikel'-Beleg auf die neue artikel-Zeile (dadurch bei
    Wiederauffinden ausgeliefert, siehe _folgerungen_fuer() in
    vorprozessor.py: "Eine Folgerung OHNE Beleg wird nicht ausgeliefert").

Ruehrt NIE an: puls.py, vorprozessor.py (nur gelesen, fuers Schema),
dream/, invariants/, neural_immune/, mistral_prestage/, retrieval.py,
systemwacht/dienststeuerung. Mutiert/loescht NIE bestehende Zeilen.

Zentral abschaltbar: ENABLED=0 in config/hypothesen.conf, ohne den
systemd-Timer anzufassen (gleiches Muster wie eos-dream).

CLI:
    eos_hypothesen.py --run          Einen Zyklus versuchen (schreibt)
    eos_hypothesen.py --dry-run      Zeigt Kandidaten, schreibt NICHTS
    eos_hypothesen.py stand          Zaehler: eigene Artikel/Folgerungen
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Pfade / Konfiguration
# ---------------------------------------------------------------------------

BASE = Path("/opt/entityos/hypothesen")
CONFIG_PATH = BASE / "config" / "hypothesen.conf"
STATE_PATH = BASE / "data" / "state.json"
LOG_PATH = BASE / "data" / "generator.log"
DB_PATH = "/var/lib/clay/wiki.db"

WERKZEUG_DIR = "/opt/clayverse/werkzeug"  # nur zum Importieren von folgerung.py

DEFAULT_CONFIG = {
    "ENABLED": "1",
    "COOLDOWN_HOURS": "10",       # Sperrzeit zwischen zwei Laeufen (Timer laeuft 12h)
    "CPU_LOAD_MAX_PCT": "60",     # ueber dieser Last (load1/nproc*100) kein Lauf
    "MAX_PER_RUN": "3",           # neue Hypothesen je Zyklus (Budget, Frank-Vorbild: 30/Tag)
    "CLUSTER_MIN": "5",           # Mindestanzahl Nulltreffer, um als "wiederkehrend" zu gelten
    "PAKET_LOG_LOOKBACK_DAYS": "30",
}

LOG = logging.getLogger("eos_hypothesen")

# ---------------------------------------------------------------------------
# Stoppwoerter (DE+EN) fuer die Schluesselwort-Signatur -- rein mechanisch,
# keine Bedeutungszuweisung, nur Funktionswoerter draussen halten.
# ---------------------------------------------------------------------------

_STOP = set("""
der die das ein eine einer eines einem einen und oder mit von zu im in auf
fuer für an als ist sind war waren wird werden hat haben nicht kein keine
keinen keiner dass wie was wo wer wann warum bei aus nach vor ueber über
unter durch um also nur noch schon mehr sehr sich sie er es ich du wir
ihr euch dich mich uns denen dem den zum zur bin bist sein seid habt
the a an of and or is are was were will be to for with on in at as not
no that this these those how what where who when why do does did can
could would should may might must shall will
""".split())

_WORD_RE = re.compile(r"[a-zA-ZäöüÄÖÜßé]{3,}")


def signature(text: str, top_n: int = 6) -> tuple:
    """Deterministische Schluesselwort-Signatur: lowercase, Stoppwoerter raus,
    sortiert, auf top_n gekappt. Gleicher Text -> gleiche Signatur -> gleiche
    id -> Wiederholungen des Skripts erzeugen KEINE Duplikate."""
    words = _WORD_RE.findall(text.lower())
    words = [w for w in words if w not in _STOP]
    return tuple(sorted(set(words))[:top_n])


def slug_id(prefix: str, sig: tuple) -> str:
    h = hashlib.sha1("|".join(sig).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{h}"


# ---------------------------------------------------------------------------
# Konfiguration / Zustand
# ---------------------------------------------------------------------------

def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        for line in CONFIG_PATH.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            pass
    return {"last_run_epoch": 0, "created_total": 0}


def save_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=1))


def gate(cfg: dict, state: dict) -> tuple:
    """Sperrzeit + Abschaltung + Last, gleiches Muster wie dream_daemon.py."""
    if cfg.get("ENABLED", "1") != "1":
        return False, "deaktiviert (ENABLED=0 in config/hypothesen.conf)"

    cooldown_h = float(cfg.get("COOLDOWN_HOURS", "10"))
    since = time.time() - state.get("last_run_epoch", 0)
    if since < cooldown_h * 3600:
        return False, f"Sperrzeit aktiv ({since/3600:.1f}h seit letztem Lauf, Sperrzeit {cooldown_h}h)"

    try:
        load1 = os.getloadavg()[0]
        nproc = os.cpu_count() or 1
        load_pct = (load1 / nproc) * 100
        max_pct = float(cfg.get("CPU_LOAD_MAX_PCT", "60"))
        if load_pct > max_pct:
            return False, f"Last zu hoch ({load_pct:.0f}% > {max_pct:.0f}%)"
    except Exception:
        pass

    return True, "ok"


# ---------------------------------------------------------------------------
# DB-Zugriff (gleiches Muster wie folgerung.py: WAL, busy_timeout, kurze
# Transaktionen -- drei andere Agenten schreiben diese DB parallel)
# ---------------------------------------------------------------------------

def connect_db():
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=30000")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def already_exists(con, artikel_id: str) -> bool:
    return con.execute("SELECT 1 FROM artikel WHERE id=?", (artikel_id,)).fetchone() is not None


# ---------------------------------------------------------------------------
# Kandidatenquelle 1: zero_luecke-Artikel (vom eos-dream-daemon geschrieben)
# ---------------------------------------------------------------------------

def candidates_from_zero_luecke(con) -> list:
    out = []
    rows = con.execute(
        "SELECT id, titel, metadaten, offene_fragen, datum FROM artikel WHERE art='zero_luecke'"
    ).fetchall()
    for r in rows:
        try:
            meta = json.loads(r["metadaten"] or "{}")
        except Exception:
            meta = {}
        thema = meta.get("thema") or r["titel"] or ""
        sig = signature(thema)
        if len(sig) < 1:
            continue
        new_id = slug_id("eos-hyp-luecke", sig)
        if already_exists(con, new_id):
            continue  # bereits erzeugt -- idempotent

        kandidaten = (meta.get("mechanische_suche") or {}).get("kandidaten") or []
        kand_titel = [k.get("titel", "") for k in kandidaten if k.get("titel")]
        anzahl = meta.get("anzahl_seit_letztem_traum", "?")

        aussage = (
            f"Wiederkehrende Wissensluecke (vom Traum-Daemon erkannt): "
            f"'{thema}' wurde {anzahl}x ohne befriedigenden Treffer angefragt "
            f"(puls_resolution={meta.get('puls_resolution', '?')}). "
            + (
                f"Mechanische Teiltreffer deuten moeglicherweise auf: "
                f"{', '.join(kand_titel[:3])} -- UNGEPRUEFTER Kandidat, keine Behauptung "
                f"ueber den Inhalt selbst. "
                if kand_titel else ""
            )
            + "[MECHANISCH ERZEUGT -- UNGEPRUEFT, Status offen]"
        )
        begruendung = (
            f"Quelle: artikel.id={r['id']} (art=zero_luecke, geschrieben von "
            f"eos-dream-daemon, datum={r['datum']}). offene_fragen={r['offene_fragen']}. "
            f"Erzeugt von eos-hypothesen-generator (LLM-frei, mechanisch: uebernimmt "
            f"die vom Traum-Daemon bereits als wiederkehrend erkannte Luecke unveraendert "
            f"als offene Hypothese, damit sie im Retrieval-Pfad ueber folgerung/paket() "
            f"auffindbar wird -- der Traum-Daemon selbst schreibt nur den zero_luecke-Artikel, "
            f"keine Hypothese)."
        )
        out.append({
            "new_id": new_id,
            "titel": f"Wissensluecke: {thema}"[:200],
            "aussage": aussage[:1200],
            "begruendung": begruendung[:2000],
            "gilt_fuer": f"ClayVerse · Wiki-Luecke · {' '.join(sig)}"[:200],
            "suchtext": f"{thema}\n{aussage}\n{' '.join(sig)}",
            "offene_fragen": [thema],
            "belege": [("artikel", r["id"])],
            "quelle": "zero_luecke",
            "quelle_id": r["id"],
            "signature": sig,
        })
    return out


# ---------------------------------------------------------------------------
# Kandidatenquelle 2: vp_paket_log-Nulltreffer, geclustert
# ---------------------------------------------------------------------------

def candidates_from_paket_log(con, cluster_min: int, lookback_days: int) -> list:
    cutoff_epoch = time.time() - lookback_days * 86400
    rows = con.execute(
        "SELECT paket_id, zeit, epoch_sekunden, frage FROM vp_paket_log "
        "WHERE orte_json='[]' AND epoch_sekunden >= ?",
        (cutoff_epoch,),
    ).fetchall()

    clusters = defaultdict(list)
    for r in rows:
        sig = signature(r["frage"])
        if len(sig) < 2:
            continue  # zu generisch, um ein Thema zu tragen
        clusters[sig].append(r)

    out = []
    for sig, members in clusters.items():
        if len(members) < cluster_min:
            continue
        new_id = slug_id("eos-hyp-nulltreffer", sig)
        if already_exists(con, new_id):
            continue  # idempotent -- dieser Cluster wurde schon einmal erzeugt

        members_sorted = sorted(members, key=lambda r: r["epoch_sekunden"])
        first, last = members_sorted[0], members_sorted[-1]
        repr_frage = last["frage"]

        aussage = (
            f"Wiederkehrende Wissensluecke im Wiki: die Anfrage '{repr_frage[:200]}' "
            f"(und {len(members) - 1} textaehnliche Varianten mit denselben Schluessel"
            f"woertern [{', '.join(sig)}]) erzielte {len(members)}x in Folge 0 Fundstellen "
            f"(orte_json='[]') im Wiki. Kandidat: zu [{', '.join(sig)}] fehlt ein Artikel im "
            f"Wiki-Bestand. [MECHANISCH ERZEUGT -- UNGEPRUEFT, keine inhaltliche Aussage ueber "
            f"{', '.join(sig)} selbst, Status offen]"
        )
        begruendung = (
            f"Quelle: vp_paket_log, orte_json='[]' bei {len(members)} Zeilen mit "
            f"uebereinstimmender Schluesselwort-Signatur, Zeitraum {first['zeit']} bis "
            f"{last['zeit']}. Repraesentative paket_id: {last['paket_id']}. Erzeugt von "
            f"eos-hypothesen-generator (LLM-frei, regelbasiert: Stoppwort-Filterung + "
            f"Signatur-Clustering ueber vp_paket_log, Schwelle CLUSTER_MIN={cluster_min})."
        )
        belege = [("protokoll", m["paket_id"]) for m in members_sorted[-3:]]
        out.append({
            "new_id": new_id,
            "titel": f"Wissensluecke: {' '.join(sig)}"[:200],
            "aussage": aussage[:1200],
            "begruendung": begruendung[:2000],
            "gilt_fuer": f"ClayVerse · Wiki-Luecke · {' '.join(sig)}"[:200],
            "suchtext": f"{repr_frage}\n{aussage}\n{' '.join(sig)}",
            "offene_fragen": [repr_frage],
            "belege": belege,
            "quelle": "vp_paket_log",
            "quelle_id": last["paket_id"],
            "signature": sig,
            "n": len(members),
        })
    out.sort(key=lambda c: -c.get("n", 0))
    return out


# ---------------------------------------------------------------------------
# Kandidatenquelle 3: Zeros eigene Epistemik-Luecken, geclustert
# ---------------------------------------------------------------------------

def _wortmenge(text: str) -> set:
    """Inhaltswoerter eines Kurzlabels -- dieselbe Stoppwortlage wie signature(),
    aber ohne Kappung auf die staerksten sechs: bei zwei bis vier Woertern gibt
    es nichts zu kappen."""
    return set(signature(text, top_n=99))


def _buendel(labels: list, deckel: float = 0.6) -> list:
    """Union-Find ueber geteilte UNTERSCHEIDENDE Woerter.

    Ein Wort, das in mehr als `deckel` aller Etiketten vorkommt, verbindet
    nichts -- es wuerde nur alles mit allem verschmelzen (gemessen: "human"
    steckt in fast jedem Etikett dieser Anlage). Rueckgabe: Liste von Listen
    der urspruenglichen Indizes.
    """
    mengen = [_wortmenge(l) for l in labels]
    n = len(labels)
    if n == 0:
        return []
    df = Counter()
    for m in mengen:
        df.update(m)
    grenze = max(1, int(deckel * n))
    eltern = list(range(n))

    def finde(i):
        while eltern[i] != i:
            eltern[i] = eltern[eltern[i]]
            i = eltern[i]
        return i

    def eine(a, b):
        ra, rb = finde(a), finde(b)
        if ra != rb:
            eltern[max(ra, rb)] = min(ra, rb)

    nach_wort = defaultdict(list)
    for i, m in enumerate(mengen):
        for w in m:
            if df[w] <= grenze:      # nur unterscheidende Woerter verbinden
                nach_wort[w].append(i)
    for _wort, idxs in nach_wort.items():
        for j in idxs[1:]:
            eine(idxs[0], j)

    gruppen = defaultdict(list)
    for i in range(n):
        gruppen[finde(i)].append(i)
    return list(gruppen.values())


def candidates_from_epistemik(con, epistemik_min: int, lookback_days: int) -> list:
    """Wiederkehrendes bewusstes Nichtwissen aus mv_prestage_turns.

    Anders als Quelle 1+2 (eine Suche fand nichts) steht hier eine
    Selbstaussage der Vorstufe: diese Tatsache BRAUCHT die Frage und sie steht
    in keiner Quelle (Feld-gegen-Frage-Pruefung, prestage.py Regel H).
    Buendelung und Schwelle sind eigens fuer diese Quelle gebaut -- siehe
    _buendel() und die Modul-Historie 2026-08-20.
    """
    cutoff = time.time() - lookback_days * 86400
    try:
        rows = con.execute(
            "SELECT prestage_id, raw_prompt, epistemik_json, created_at "
            "FROM mv_prestage_turns "
            "WHERE epistemik_unbekannt_n > 0 AND created_at >= ?",
            (cutoff,),
        ).fetchall()
    except sqlite3.Error:
        # Tabelle/Spalte fehlt (aeltere Anlage) -- kein Grund, den ganzen
        # Zyklus zu kippen; die anderen beiden Quellen laufen weiter.
        LOG.info("Quelle 3 uebersprungen: mv_prestage_turns/epistemik nicht verfuegbar")
        return []

    eintraege = []
    for r in rows:
        try:
            unbekannt = (json.loads(r["epistemik_json"] or "{}") or {}).get("unbekannt") or []
        except (ValueError, TypeError):
            continue
        for label in unbekannt:
            if not isinstance(label, str) or not label.strip():
                continue
            if not _wortmenge(label):
                continue   # nur Stoppwoerter -- traegt kein Thema
            eintraege.append({"prestage_id": r["prestage_id"],
                              "raw_prompt": r["raw_prompt"],
                              "label": label.strip(),
                              "created_at": r["created_at"]})

    out = []
    for gruppe in _buendel([e["label"] for e in eintraege]):
        if len(gruppe) < epistemik_min:
            continue
        members = sorted((eintraege[i] for i in gruppe), key=lambda m: m["created_at"] or 0)
        # Signatur des Buendels: die haeufigsten Inhaltswoerter darin -- das ist
        # der Name, unter dem es wiedererkannt wird (Idempotenz).
        zaehler = Counter()
        for m in members:
            zaehler.update(_wortmenge(m["label"]))
        # NICHT most_common(3): das bricht Gleichstaende nach Einfuegereihenfolge
        # und liefert damit ueber Laeufe hinweg wechselnde Signaturen -- siehe
        # Modul-Historie 2026-08-20. Gleichstand alphabetisch brechen.
        sig = tuple(sorted(w for w, _ in
                           sorted(zaehler.items(), key=lambda kv: (-kv[1], kv[0]))[:3]))
        new_id = slug_id("eos-hyp-epistemik", sig)
        if already_exists(con, new_id):
            continue   # idempotent

        first, last = members[0], members[-1]
        formulierungen = sorted({m["label"] for m in members})
        aussage = (
            f"Wiederkehrendes bewusstes Nichtwissen: die Vorstufe hat {len(members)}x "
            f"festgestellt, dass eine Frage die Tatsache '{last['label'][:160]}' braucht "
            f"und sie in keiner Quelle steht (Formulierungen: "
            f"{'; '.join(f[:60] for f in formulierungen[:4])}). Kandidat: zu "
            f"[{', '.join(sig)}] fehlt eine belegte Angabe -- im Profil, im Korpus oder "
            f"im dauerhaften Gedaechtnis. [MECHANISCH ERZEUGT -- UNGEPRUEFT, keine "
            f"inhaltliche Aussage ueber {', '.join(sig)} selbst, Status offen]"
        )
        begruendung = (
            f"Quelle: mv_prestage_turns.epistemik_json, Schluessel 'unbekannt', "
            f"{len(members)} Eintraege in einem Buendel (geteilte unterscheidende "
            f"Woerter) zwischen {first['created_at']} und {last['created_at']}. Anders "
            f"als die Nulltreffer-Quelle ist dies eine SELBSTAUSSAGE der Vorstufe "
            f"(Feld-gegen-Frage-Pruefung, prestage.py Regel H), kein fehlgeschlagener "
            f"Suchlauf -- deshalb die eigene, niedrigere Schwelle "
            f"EPISTEMIK_MIN={epistemik_min}. Erzeugt von eos-hypothesen-generator "
            f"(LLM-frei, regelbasiert)."
        )
        out.append({
            "new_id": new_id,
            "titel": f"Eigene Wissensluecke: {' '.join(sig)}"[:200],
            "aussage": aussage[:1200],
            "begruendung": begruendung[:2000],
            "gilt_fuer": f"EntityOS · Selbstpruefung · {' '.join(sig)}"[:200],
            "suchtext": f"{last['label']}\n{aussage}\n{' '.join(sig)}",
            "offene_fragen": [m["raw_prompt"] for m in members[-2:] if m["raw_prompt"]],
            # Entdoppelt: ein Zug kann mehrere Luecken tragen und stuende sonst
            # mehrfach als Beleg derselben Folgerung (siehe Modul-Historie).
            "belege": [("protokoll", pid) for pid in list(dict.fromkeys(
                m["prestage_id"] for m in reversed(members)))[:3]],
            "quelle": "epistemik",
            "quelle_id": last["prestage_id"],
            "signature": sig,
            "n": len(members),
        })
    out.sort(key=lambda c: -c.get("n", 0))
    return out


# ---------------------------------------------------------------------------
# Schreiben: artikel + artikel_suchtext + fts_index_artikel, dann folgerung
# ---------------------------------------------------------------------------

def write_artikel(con, cand: dict) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000")
    metadaten = json.dumps({
        "erzeuger": "eos-hypothesen-generator",
        "quelle": cand["quelle"],
        "quelle_id": cand["quelle_id"],
        "signatur": list(cand["signature"]),
        "mechanisch": True,
        "modellaufruf": False,
    }, ensure_ascii=False)

    con.execute("BEGIN IMMEDIATE")
    try:
        con.execute(
            "INSERT INTO artikel (id, art, titel, quelle, datum, metadaten, "
            "offene_fragen, belegt, erzeugt_am, duenn, wirt, zuletzt_von, "
            "epistemic_class, status, herkunft, verfallen, protected) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                cand["new_id"], "hypothese", cand["titel"],
                "eos-hypothesen-generator", now, metadaten,
                json.dumps(cand["offene_fragen"], ensure_ascii=False),
                1, now, 0, "clayverse", "eos-hypothesen-generator",
                "MECHANICAL_GAP_HYPOTHESIS", "offen", "gemessen", 0, 0,
            ),
        )
        cur = con.execute(
            "INSERT INTO artikel_suchtext (artikel_id, titel, text, indiziert) "
            "VALUES (?,?,?,?)",
            (cand["new_id"], cand["titel"], cand["suchtext"], now),
        )
        suchtext_rowid = cur.lastrowid
        con.execute(
            "INSERT INTO fts_index_artikel (rowid, titel, text) VALUES (?,?,?)",
            (suchtext_rowid, cand["titel"], cand["suchtext"]),
        )
        con.commit()
        return cand["new_id"]
    except Exception:
        con.rollback()
        raise


def write_folgerung(cand: dict, artikel_id: str) -> int:
    """Ueber die sanktionierte Schreib-Fassade folgerung.py -- NICHT selbst
    SQL gegen die folgerung-Tabelle. status IMMER 'offen'."""
    sys.path.insert(0, WERKZEUG_DIR)
    import folgerung as folgerung_mod  # lokal importiert, nur gelesen/aufgerufen

    con = folgerung_mod.connect_db()
    try:
        folgerung_mod.ensure_schema(con)
        belege = [("artikel", artikel_id)] + list(cand["belege"])
        fid = folgerung_mod.neu(
            con,
            art="hypothese",
            aussage=cand["aussage"],
            begruendung=cand["begruendung"],
            gilt_fuer=cand["gilt_fuer"],
            belege=belege,
            autor="eos-hypothesen-generator",
            status="offen",
        )
        return fid
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Hauptzyklus
# ---------------------------------------------------------------------------

def _reihum(cands: list, budget: int) -> list:
    """Budget reihum ueber die Quellen verteilen statt nach reiner Haeufigkeit.

    Die Quellen zaehlen Verschiedenes (Suchlaeufe vs. bewusste Selbstaussagen),
    ihre n-Werte sind deshalb NICHT vergleichbar -- siehe Modul-Historie
    2026-08-20. Innerhalb einer Quelle bleibt die n-Sortierung.
    """
    nach_quelle = defaultdict(list)
    for c in cands:
        nach_quelle[c["quelle"]].append(c)
    for lst in nach_quelle.values():
        lst.sort(key=lambda c: -c.get("n", 0))
    # Stabile Reihenfolge der Quellen: die mit dem knappsten Angebot zuerst,
    # damit eine seltene Quelle nicht dauerhaft hinter einer ergiebigen wartet.
    reihen = sorted(nach_quelle.values(), key=len)
    out = []
    runde = 0
    while len(out) < budget and any(len(r) > runde for r in reihen):
        for r in reihen:
            if len(out) >= budget:
                break
            if len(r) > runde:
                out.append(r[runde])
        runde += 1
    return out


def _artikel_zuruecknehmen(con, artikel_id: str) -> None:
    """Einen gerade selbst erzeugten Hypothesen-Artikel wieder entfernen.

    Bewusst eng: NUR Zeilen, die diese Datei in DIESEM Lauf angelegt hat
    (zuletzt_von='eos-hypothesen-generator'), und nur dieser eine Schluessel.
    Der FTS-Eintrag haengt an der rowid von artikel_suchtext, deshalb erst
    lesen, dann beide loeschen.
    """
    try:
        row = con.execute(
            "SELECT s.rowid AS rid FROM artikel_suchtext s "
            "JOIN artikel a ON a.id = s.artikel_id "
            "WHERE s.artikel_id = ? AND a.zuletzt_von = 'eos-hypothesen-generator'",
            (artikel_id,),
        ).fetchone()
        if row is not None:
            con.execute("DELETE FROM fts_index_artikel WHERE rowid = ?", (row["rid"],))
            con.execute("DELETE FROM artikel_suchtext WHERE rowid = ?", (row["rid"],))
        con.execute(
            "DELETE FROM artikel WHERE id = ? AND zuletzt_von = 'eos-hypothesen-generator'",
            (artikel_id,),
        )
        con.commit()
        LOG.info("Artikel %s zurueckgenommen", artikel_id)
    except Exception as fehler:
        con.rollback()
        # Nicht verschweigen: eine misslungene Ruecknahme ist genau die
        # Halbbuchung, die diese Funktion verhindern soll.
        LOG.error("Ruecknahme von %s fehlgeschlagen: %s: %s", artikel_id,
                  type(fehler).__name__, fehler)


def run_cycle(cfg: dict, dry_run: bool = False) -> dict:
    con = connect_db()
    try:
        cluster_min = int(cfg.get("CLUSTER_MIN", "5"))
        # Eigene, niedrigere Schwelle fuer Quelle 3 -- siehe Modul-Historie 2026-08-20.
        epistemik_min = int(cfg.get("EPISTEMIK_MIN", 3))
        lookback = int(cfg.get("PAKET_LOG_LOOKBACK_DAYS", "30"))
        max_per_run = int(cfg.get("MAX_PER_RUN", "3"))

        cands = candidates_from_zero_luecke(con)
        cands += candidates_from_paket_log(con, cluster_min, lookback)
        cands += candidates_from_epistemik(con, epistemik_min, lookback)

        LOG.info("Kandidaten gefunden: %d (vor Budget-Kappung)", len(cands))
        chosen = _reihum(cands, max_per_run)
        LOG.info("Budget %d verteilt auf Quellen: %s", max_per_run,
                 dict(Counter(c["quelle"] for c in chosen)))

        created = []
        for cand in chosen:
            if dry_run:
                LOG.info("[DRY-RUN] wuerde erzeugen: %s aus %s (n=%s) sig=%s",
                          cand["new_id"], cand["quelle"], cand.get("n", 1),
                          cand["signature"])
                continue
            artikel_id = write_artikel(con, cand)
            try:
                fid = write_folgerung(cand, artikel_id)
            except Exception as fehler:
                # Artikel + Folgerung sind EINE Buchung. Der Artikel ist schon
                # committet (write_artikel committet selbst), also hier von Hand
                # zuruecknehmen -- sonst bleibt eine Luecke im Wiki stehen, an
                # der nie jemand arbeitet, und already_exists() verhindert jeden
                # weiteren Versuch.
                LOG.error("Folgerung fuer %s fehlgeschlagen (%s: %s) -- Artikel "
                          "wird zurueckgenommen", artikel_id,
                          type(fehler).__name__, fehler)
                _artikel_zuruecknehmen(con, artikel_id)
                continue
            LOG.info("Erzeugt: artikel=%s folgerung=#%d quelle=%s sig=%s",
                      artikel_id, fid, cand["quelle"], cand["signature"])
            created.append({"artikel_id": artikel_id, "folgerung_id": fid,
                             "quelle": cand["quelle"], "signature": list(cand["signature"])})

        return {"kandidaten_gesamt": len(cands), "erzeugt": created}
    finally:
        con.close()


def cmd_stand():
    con = connect_db()
    try:
        n_art = con.execute(
            "SELECT COUNT(*) FROM artikel WHERE zuletzt_von='eos-hypothesen-generator'"
        ).fetchone()[0]
        n_folg = con.execute(
            "SELECT COUNT(*) FROM folgerung WHERE autor='eos-hypothesen-generator'"
        ).fetchone()[0]
        print(f"eigene artikel (art=hypothese, eos-hypothesen-generator): {n_art}")
        print(f"eigene folgerung-Zeilen (autor=eos-hypothesen-generator): {n_folg}")
        state = load_state()
        print(f"letzter Lauf: {state.get('last_run_epoch', 0)}")
    finally:
        con.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="run",
                     choices=["run", "stand"], help="run (Default) oder stand")
    ap.add_argument("--run", action="store_true", help="Zyklus ausfuehren (schreibt)")
    ap.add_argument("--dry-run", action="store_true", help="Nur zeigen, nichts schreiben")
    ap.add_argument("--force", action="store_true",
                     help="Sperrzeit/Last ignorieren (nur zur Verifikation)")
    args = ap.parse_args()

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
    )

    if args.cmd == "stand":
        cmd_stand()
        return 0

    cfg = load_config()
    state = load_state()

    if not args.dry_run and not args.force:
        ok, reason = gate(cfg, state)
        if not ok:
            LOG.info("Uebersprungen: %s", reason)
            return 0

    result = run_cycle(cfg, dry_run=args.dry_run)
    LOG.info("Zyklus fertig: %d Kandidaten gesehen, %d neu erzeugt",
              result["kandidaten_gesamt"], len(result["erzeugt"]))

    if not args.dry_run:
        state["last_run_epoch"] = time.time()
        state["created_total"] = state.get("created_total", 0) + len(result["erzeugt"])
        state["last_result"] = result
        save_state(state)

    return 0


if __name__ == "__main__":
    sys.exit(main())
