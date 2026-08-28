#!/usr/bin/env python3
"""
ClayVerse Wiki Scaffold — Stufe 2 (volle Abdeckung + Hypothesen + Provenienz).

Mechanical only. No model calls, no network calls, stdlib only.
Primary store: SQLite at /var/lib/clay/wiki.db (WAL, shared with other agents'
fts_*/anreicherung/kuration tables — this script only touches artikel/kante).

Subcommands:
  bauen                    generate all articles + edges into the DB
  stand                    counts per article type, edge stats
  artikel <id>             show one article + all edges (both directions), timed
  provenienz_reparieren    re-resolve zuletzt_bearbeitet/zeitquelle/zuletzt_von/
                           von_quelle against real per-repo git history in
                           /var/lib/clay/klone/<repo>/ (2026-08-15, Stufe 3:
                           the /opt/clayverse meta-repo's git history was a
                           degenerate 2-commit bulk import; the 21 unshallowed
                           clones under klone/ carry the REAL commit history).

Stufe-2-Erweiterungen (2026-08-15, Owner-Auftrag):
  - JEDE Datei unter research_entity/ bekommt eine Zeile (Sweep-Builder),
    auch wenn keine Struktur erkennbar ist (Spalte duenn=1, metadaten={}).
  - Neue art-Werte 'hypothese' und 'gegenhypothese', ausschliesslich aus
    EXISTIERENDEN Namens-/Feldmustern erkannt (KMP-HYP-*, HYPOTHESES.json/
    COUNTERHYPOTHESES.json mit id/attacks-Feldern, CLAIMS first_status
    OPEN/REFUTED/SUPERSEDED, NEGATIVE_RESULT*-Dateien). Nichts wird erfunden.
  - Provenienz: zuletzt_bearbeitet + zeitquelle (git > strom > metadaten >
    mtime) und zuletzt_von + von_quelle (git-Autor > Metadaten-Actor-Feld >
    strom instanz/wirt > NULL). Konstante Spalte wirt='clayverse'.
"""
import sys, os, json, sqlite3, hashlib, re, time, glob, subprocess
from datetime import datetime, timezone

RE_ROOT = "/opt/clayverse/baeume/clay-global-research-entity/research_entity"
KARTE_ROOT = "/var/lib/clay/karte"
PROTOKOLL = "/opt/clayverse/bau/protokoll.jsonl"
DB_PATH = "/var/lib/clay/wiki.db"
BUILD_LOG = "/var/lib/clay/wiki/BUILD_LOG.json"  # optional, cheap secondary artifact
CLAYVERSE_REPO = "/opt/clayverse"
GIT_SCOPE = "baeume/clay-global-research-entity/research_entity"  # repo-relative
IAR_SITE_ROOT = "/var/lib/agentforge/projects/6/iar/site"
VERWEISE_PATH = "/opt/clayverse/baeume/VERWEISE.json"
BAEUME_ROOT = "/opt/clayverse/baeume"
STROM_ROOT = "/var/lib/clay"
STROM_DATEIEN = ("ereignisse.jsonl", "tor.jsonl", "eichung.jsonl", "eichnormale.jsonl")

# ---------------------------------------------------------------- utilities

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def slugify(s):
    s = str(s).strip()
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "unbekannt"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def connect_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=30000")
    con.execute("PRAGMA synchronous=NORMAL")
    return con

def ensure_schema(con):
    # Required minimum schema (owner-specified). We own artikel/kante only.
    con.execute("""
        CREATE TABLE IF NOT EXISTS artikel (
            id TEXT PRIMARY KEY,
            art TEXT NOT NULL,
            titel TEXT,
            quelle TEXT,
            quell_hash TEXT,
            datum TEXT,
            metadaten TEXT,       -- JSON, verbatim source metadata
            offene_fragen TEXT,   -- JSON array
            belegt INTEGER,
            erzeugt_am TEXT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS kante (
            von TEXT NOT NULL,
            nach TEXT NOT NULL,
            art TEXT NOT NULL,    -- which source field produced this edge
            beleg TEXT,           -- provenance: quelle path of the asserting article
            PRIMARY KEY (von, nach, art)
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_kante_von ON kante(von)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_kante_nach ON kante(nach)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_artikel_art ON artikel(art)")
    # Additive Stufe-2-Spalten. try/except macht das idempotent (mehrfach
    # ausfuehrbar ohne Fehler), da SQLite kein "ADD COLUMN IF NOT EXISTS" kennt.
    for coldef in (
        "duenn INTEGER DEFAULT 0",
        "zuletzt_bearbeitet TEXT",
        "zeitquelle TEXT",
        "wirt TEXT",
        "zuletzt_von TEXT",
        "von_quelle TEXT",
        # Stufe 2 / Owner-Addition 3: aus metadaten JSON in echte, indizierbare
        # Spalten gehoben. metadaten bleibt unveraendert der Fallback (Kopie,
        # kein Verschieben).
        "logical_id TEXT",
        "id_quelle TEXT",
        "epistemic_class TEXT",
        "status TEXT",
        "scope TEXT",
        "tags TEXT",
        "konfidenz REAL",
        # Stufe 4 (2026-08-15, Owner-Auftrag projekt/sphaere/IAR):
        "projekt TEXT",       # welcher Baum/Repo/Standort die Quelle trug
        "projekt_art TEXT",   # eigen | fremd | fork | unbekannt
        "sphaere TEXT",       # frank_v0_1 | seimensch | andreas | gabriel | clayverse | iar | fremd | NULL
        # herkunft gehoert der Kommentar-Schicht (eigenes Projekt); wir fuegen
        # sie hier NUR idempotent-additiv hinzu, falls dieses Skript auf einer
        # DB laeuft, die sie noch nicht hat (z.B. isolierte Testdatenbank fuer
        # den Beweis unten). Auf Produktion existiert sie schon -- ALTER
        # schlaegt dort einfach mit 'duplicate column' fehl und wird ignoriert.
        "herkunft TEXT DEFAULT 'gemessen'",
        # verfallen/protected gehoeren der Verfalls-Arbeit (eigenes Projekt);
        # wie bei herkunft nur idempotent-additiv fuer den Fall, dass dieses
        # Skript vor deren Migration laeuft (z.B. isolierte Testdatenbank).
        # Gleicher Typ/Default wie auf Produktion. load_carryforward_snapshot
        # liest diese Spalten jetzt mit (dritter Fund, 2026-08-15).
        "verfallen INTEGER DEFAULT 0",
        "protected INTEGER DEFAULT 0",
    ):
        try:
            con.execute(f"ALTER TABLE artikel ADD COLUMN {coldef}")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
    con.execute("CREATE INDEX IF NOT EXISTS idx_artikel_logical_id ON artikel(logical_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_artikel_epistemic_class ON artikel(epistemic_class)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_artikel_status ON artikel(status)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_artikel_projekt ON artikel(projekt)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_artikel_sphaere ON artikel(sphaere)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_artikel_quelle ON artikel(quelle)")
    # Multi-sphere link table (Owner-Auftrag: "cramming a list into one column"
    # vermeiden). sphaere-Spalte auf artikel bleibt die primaere/erste
    # evidenzierte Zuordnung; hier stehen ALLE evidenzierten Zuordnungen,
    # auch wenn es nur eine ist -- diese Tabelle ist die vollstaendige Quelle.
    con.execute("""
        CREATE TABLE IF NOT EXISTS artikel_sphaere (
            artikel_id TEXT NOT NULL,
            sphaere TEXT NOT NULL,
            beleg TEXT,
            PRIMARY KEY (artikel_id, sphaere)
        )
    """)
    con.commit()

# ---------------------------------------------------------------- STOP-Level-Fix: herkunft/bearbeitung
# Owner-Befund 2026-08-15 (sibling-Agent, isolierte DB bewiesen): INSERT OR
# REPLACE ersetzt die GANZE Zeile. herkunft war nicht in der Spaltenliste ->
# jeder Rebuild hat herkunft auf den Default zurueckgesetzt UND jeden von
# Hand editierten Feldwert mit dem mechanisch berechneten ueberschrieben.
# Fix, zweigeteilt, wie vom Owner verlangt:
#  (a) herkunft wird vor jedem Rebuild pro id ausgelesen und im INSERT OR
#      REPLACE als Wert MITGEGEBEN (nicht der Default) -- ueberlebt jeden Lauf.
#  (b) NACH dem Rebuild werden fuer alle herkunft='nutzer'-Artikel die in
#      bearbeitung(artikel_id, feld, neu_wert) festgehaltenen Handaenderungen
#      erneut angewandt (gewaehlte Variante: "nach dem Rebuild erneut
#      anwenden", NICHT "Felder vom Rebuild ausschliessen" -- einfacher zu
#      pruefen, exakt dieselbe Endwirkung). bearbeitung gehoert der
#      Kommentar-Schicht (fremdes Projekt) -- rein lesend, nie verandert.

def get_artikel_editable_fields(cur):
    """Alle echten artikel-Spalten AUSSER id/herkunft/erzeugt_am (die drei
    sind strukturell reserviert, nie ueber bearbeitung setzbar). Dynamisch
    per PRAGMA, nicht hartkodiert -- bleibt korrekt, wenn weitere Spalten
    dazukommen."""
    cur.execute("PRAGMA table_info(artikel)")
    cols = {r[1] for r in cur.fetchall()}
    return cols - {"id", "herkunft", "erzeugt_am"}

def load_herkunft_snapshot(cur):
    """id -> herkunft VOR dem Rebuild. Fehlt eine id (neuer Artikel), gilt
    der Default 'gemessen' -- korrekt, ein neu erzeugter Artikel ist per
    Definition mechanisch, nicht von Hand editiert."""
    cur.execute("SELECT id, herkunft FROM artikel")
    return {row[0]: (row[1] or "gemessen") for row in cur.fetchall()}

def load_carryforward_snapshot(cur):
    """Selbst gefundener Zwilling desselben Bugs, beim Bauen des Fixes
    entdeckt: cmd_bauen()'s INSERT OR REPLACE listete projekt/projekt_art/
    sphaere NIE auf -- jeder bauen()-Lauf haette also den kompletten
    Stufe-4-Output (cmd_projekt_sphaere) wieder auf NULL zurueckgesetzt,
    unabhaengig von herkunft/bearbeitung (das deckt nur Hand-Edits ab, nicht
    'von einem ANDEREN Rebuild-Pass mechanisch gesetzt').
    2026-08-15, urgent: DRITTER Fund derselben Klasse -- verfallen/protected
    (Verfalls-Arbeit, heute auf artikel UND kante dazugekommen) waren
    ebenfalls nicht in der Spaltenliste. id -> (herkunft, projekt,
    projekt_art, sphaere, verfallen, protected) -- alle sechs werden
    mitgegeben statt implizit auf den Default zurueckzufallen."""
    cur.execute("SELECT id, herkunft, projekt, projekt_art, sphaere, verfallen, protected FROM artikel")
    return {
        row[0]: (row[1] or "gemessen", row[2], row[3], row[4], row[5], row[6])
        for row in cur.fetchall()
    }

def reapply_owner_edits(cur):
    """Nach dem mechanischen Rebuild: fuer jeden Artikel mit herkunft='nutzer'
    die neuesten bearbeitung-Werte je Feld erneut anwenden. Read-only auf
    bearbeitung selbst (nur SELECT). Feldname wird gegen die echte
    Spaltenmenge geprueft, bevor er in ein UPDATE eingesetzt wird (kein
    SQL-Injection-Risiko durch Fremdtabellen-Inhalt, keine Fantasie-Spalten)."""
    try:
        cur.execute("SELECT COUNT(*) FROM bearbeitung")
    except sqlite3.OperationalError:
        return {"bearbeitung_tabelle_vorhanden": False, "nutzer_artikel": 0, "felder_reapplied": 0, "unbekannte_felder_uebersprungen": 0}

    editable = get_artikel_editable_fields(cur)
    cur.execute("SELECT id FROM artikel WHERE herkunft='nutzer'")
    nutzer_ids = [r[0] for r in cur.fetchall()]
    n_reapplied = 0
    n_skipped = 0
    for aid in nutzer_ids:
        cur.execute(
            "SELECT feld, neu_wert FROM bearbeitung WHERE artikel_id=? ORDER BY zeit ASC, id ASC",
            (aid,),
        )
        neueste = {}
        for feld, neu_wert in cur.fetchall():
            neueste[feld] = neu_wert  # letzte Zeile je Feld gewinnt (zeit ASC)
        for feld, neu_wert in neueste.items():
            if feld not in editable:
                n_skipped += 1
                continue
            cur.execute(f"UPDATE artikel SET {feld}=? WHERE id=?", (neu_wert, aid))
            n_reapplied += 1
    return {
        "bearbeitung_tabelle_vorhanden": True,
        "nutzer_artikel": len(nutzer_ids),
        "felder_reapplied": n_reapplied,
        "unbekannte_felder_uebersprungen": n_skipped,
    }

# ---------------------------------------------------------------- generic field extraction

# Fields whose values are candidate GRAPH EDGE TARGETS (raw refs to be resolved
# against known article ids later -- never inserted as free text).
EDGE_FIELDS = [
    "source_refs", "evidence_refs", "predecessor", "predecessor_packet_ids",
    "supersession_links", "supersedes_packet_ids", "experiment_refs",
    "related_experiment_ids", "related_claim_ids", "topic_packets",
    "experiment_ref", "evidence", "artifacts",
    "attacks",  # Stufe 2: counterhypothesis -> hypothesis, real source field
]

# Fields that mechanically indicate an OPEN QUESTION on the source record.
OPEN_FIELDS = [
    "falsifier", "falsifier_or_next_test", "verification_requirement",
    "verification_required", "open_questions", "next_falsifiers",
    "next_falsifier", "remaining_blockers", "offen",
]

def _flatten_to_strs(v):
    out = []
    if v is None:
        return out
    if isinstance(v, str):
        out.append(v)
    elif isinstance(v, (int, float, bool)):
        out.append(str(v))
    elif isinstance(v, list):
        for item in v:
            out.extend(_flatten_to_strs(item))
    elif isinstance(v, dict):
        for item in v.values():
            out.extend(_flatten_to_strs(item))
    return out

def extract_edge_candidates(meta):
    """Returns list of (field_name, raw_ref_string) — top-level only, mechanical."""
    cands = []
    if not isinstance(meta, dict):
        return cands
    for field in EDGE_FIELDS:
        if field in meta:
            for s in _flatten_to_strs(meta[field]):
                s = s.strip()
                if s:
                    cands.append((field, s))
    return cands

def extract_open_questions(meta):
    out = []
    if not isinstance(meta, dict):
        return out
    for field in OPEN_FIELDS:
        if field in meta:
            for s in _flatten_to_strs(meta[field]):
                s = s.strip()
                if s:
                    out.append({"feld": field, "text": s})
    return out

def ref_to_slug_candidates(ref):
    """Mechanical normalizations of a raw ref string to try against id sets.
    No guessing of meaning -- just stripping known path prefixes / extensions."""
    cands = {ref, slugify(ref)}
    r = ref
    if r.startswith("research_entity/"):
        r = r[len("research_entity/"):]
    cands.add(r)
    cands.add(slugify(r))
    base = os.path.basename(r)
    base_noext = re.sub(r"\.(json|md|clay|py)$", "", base)
    cands.add(base)
    cands.add(base_noext)
    cands.add(slugify(base_noext))
    return cands

# ---------------------------------------------------------------- Stufe 2: Provenienz (wann/wer)

# Die drei bekannten Append-only-Stroeme (owner-benannt). Fuer sie gilt der
# in-line-Zeitstempel als praeziser als das datei-weite Git-Commit-Datum
# (das fuer eine Multi-Record-Datei sonst jeder Zeile denselben falschen
# Stempel gaebe -- dieselbe Falle wie mtime, nur eine Ebene tiefer).
# ABWEICHUNG von der woertlichen Reihenfolge (git,strom,metadaten,mtime):
# fuer GENAU diese drei Dateien wird strom VOR git geprueft. Sonst waere
# Regel 2 (strom) tote Kette, weil git fuer jede getrackte Datei "erfolgreich"
# ist. Siehe Bericht.
STROM_BASENAMES = ("protokoll.jsonl", "ereignisse.jsonl", "tor.jsonl")
STROM_TIME_FIELDS = ("zeit", "timestamp", "time")
STROM_ACTOR_FIELDS = ("instanz", "wirt")

META_DATE_FIELDS = [
    "created_at", "updated_at", "datum", "zeit", "date", "Date",
    "timestamp", "processed_at", "effective_from",
]
META_ACTOR_FIELDS = [
    "origin_actor", "actor", "actor_id", "ingested_by", "adjudicated_by",
    "worker", "author",
]

def load_git_provenance():
    """EIN Subprocess-Aufruf fuer den kompletten research_entity-Baum.
    Liefert (datum_map, autor_map): repo-relativer Pfad -> (letzter
    Commit-Zeitstempel, letzter Commit-Autor), neueste Zeile gewinnt.
    Gemessen 2026-08-15: deckt 7699/7699 Dateien auf Platte ab (100%),
    aber nur 2 Commits beruehren den ganzen Baum ueberhaupt (siehe Bericht --
    Bulk-Import, git-Datum ist fuer >99.9% der Zeilen ebenfalls uniform)."""
    try:
        out = subprocess.run(
            ["git", "log", "--format=C|%cI\t%an", "--name-only", "--no-renames",
             "--", GIT_SCOPE],
            cwd=CLAYVERSE_REPO, capture_output=True, text=True, check=False,
            timeout=120,
        ).stdout
    except Exception:
        return {}, {}
    dates, authors = {}, {}
    cur_date = cur_author = None
    for line in out.splitlines():
        if line.startswith("C|"):
            rest = line[2:]
            cur_date, _, cur_author = rest.partition("\t")
            continue
        p = line.strip()
        if not p:
            continue
        if p not in dates:
            dates[p] = cur_date
            authors[p] = cur_author
    return dates, authors

def resolve_provenance(quelle, meta, git_dates, git_authors):
    """Gibt (zuletzt_bearbeitet, zeitquelle, zuletzt_von, von_quelle) zurueck.
    Nie geraten: wenn keine Quelle greift, bleibt der Wert None (NULL)."""
    base = os.path.basename(quelle) if quelle else ""
    rel = None
    if quelle and quelle.startswith(CLAYVERSE_REPO + os.sep):
        rel = quelle[len(CLAYVERSE_REPO) + 1:]
    m = meta if isinstance(meta, dict) else {}

    datum = zq = None
    if base in STROM_BASENAMES:
        for k in STROM_TIME_FIELDS:
            if m.get(k):
                datum, zq = str(m[k]), "strom"
                break
    if datum is None and rel and git_dates.get(rel):
        datum, zq = git_dates[rel], "git"
    if datum is None:
        for k in META_DATE_FIELDS:
            if m.get(k):
                datum, zq = str(m[k]), "metadaten"
                break
    if datum is None and quelle and os.path.exists(quelle):
        try:
            datum = datetime.fromtimestamp(os.path.getmtime(quelle), tz=timezone.utc).isoformat()
            zq = "mtime"
        except OSError:
            pass

    von = vq = None
    if rel and git_authors.get(rel):
        von, vq = git_authors[rel], "git"
    if von is None:
        for k in META_ACTOR_FIELDS:
            if m.get(k):
                von, vq = str(m[k])[:200], "metadaten"
                break
    if von is None and base in STROM_BASENAMES:
        for k in STROM_ACTOR_FIELDS:
            if m.get(k):
                von, vq = str(m[k])[:200], "strom"
                break
    return datum, zq, von, vq

WIRT_KONSTANTE = "clayverse"  # Alles hier Erzeugte laeuft auf dem clayverse-Host.

# ---------------------------------------------------------------- Owner-Addition 3: lift-Spalten

# Gemessen 2026-08-15 auf allen *.json unter R (5750 Dateien), Kandidaten fuer
# logical_id-Regel 3 ("ein stabiles id-Feld, das die Quelle wirklich traegt"):
#   run_id 40.5% · event_id 11.5% · task_id 7.5% · receipt_id 8.5% ·
#   request_id 6.8% · id (dateiweit) 0.5% (aber 100% auf hypothese/
#   gegenhypothese-Sub-Records, da genau das die Aufnahmebedingung war).
LOGICAL_ID_REGEL3_FELDER = ("id", "run_id", "event_id", "receipt_id", "task_id", "request_id")

def resolve_lift_fields(art, meta):
    """logical_id/id_quelle/epistemic_class/status/scope/tags/konfidenz aus
    metadaten heben -- Kopie, nichts wird aus metadaten geloescht. Nie
    erfunden: jedes Feld bleibt NULL, wenn keine Regel greift."""
    m = meta if isinstance(meta, dict) else {}

    epistemic_class = m.get("epistemic_class")
    if epistemic_class is not None:
        epistemic_class = str(epistemic_class)

    status = m.get("status_hint") or m.get("status") or m.get("first_status")
    if status is not None:
        status = str(status)

    scope = m.get("scope") if isinstance(m.get("scope"), str) else None

    tags_list = []
    for k in ("topics", "domains"):
        v = m.get(k)
        if isinstance(v, list):
            tags_list.extend(str(x) for x in v if x is not None)
        elif isinstance(v, str):
            tags_list.append(v)
    tags = ",".join(tags_list) if tags_list else None

    konfidenz = None
    c = m.get("confidence")
    if isinstance(c, bool):
        konfidenz = None
    elif isinstance(c, (int, float)):
        konfidenz = float(c)
    elif isinstance(c, str):
        try:
            konfidenz = float(c)
        except ValueError:
            konfidenz = None

    logical_id = None
    id_quelle = None
    if m.get("packet_id"):
        logical_id = str(m["packet_id"])
        id_quelle = "packet_id"
    elif m.get("claim_id"):
        # Regel 2: Claim-id aus CLAIMS.jsonl -- gilt fuer alle drei arts, in
        # die eine CLAIMS-Zeile mechanisch einsortiert werden kann
        # (behauptung/hypothese/gegenhypothese, siehe build_behauptung).
        logical_id = str(m["claim_id"])
        id_quelle = "claim_id"
    else:
        for k in LOGICAL_ID_REGEL3_FELDER:
            if m.get(k):
                logical_id = str(m[k])
                id_quelle = k
                break

    return epistemic_class, status, scope, tags, konfidenz, logical_id, id_quelle

# ---------------------------------------------------------------- Groessendisziplin (Sweep/Hyp)

GROESSENGRENZE = 32000  # Bytes; ueber dieser Grenze kein Volltext in artikel.metadaten

def _kv_header_from_md(raw):
    """Mechanischer H1-Titel + fuehrender 'Key: value'-Block (auch '- Key: `v`'
    und '**Key:** v'), plus RAE_META-HTML-Kommentarblock falls vorhanden.
    Keine Interpretation, nur Regex-Extraktion vorhandener Strukturen."""
    h1 = re.search(r"^#\s+(.+)$", raw, re.M)
    titel = h1.group(1).strip() if h1 else None
    hdr = {}
    header_re = re.compile(r"^[-*]?\s*\**([A-Za-z][A-Za-z0-9 _/\-]{1,40}?)\**:\s*(.+?)\s*$")
    for ln in raw.splitlines()[:60]:
        s = ln.strip()
        if not s:
            if hdr:
                break
            continue
        m = header_re.match(s)
        if m:
            hdr[m.group(1).strip()] = m.group(2).strip().strip("`")
    m2 = re.search(r"RAE_META\n(.*?)\nRAE_META -->", raw, re.S)
    if m2:
        try:
            hdr["_RAE_META"] = json.loads(m2.group(1))
        except Exception:
            pass
    return titel, hdr

# ---------------------------------------------------------------- article builders (Stufe 1, angepasst)
# Each builder yields dicts:
# {id, art, titel, quelle, quell_hash, datum, metadaten, offene_fragen, belegt, duenn}

def build_begriff_kmp():
    """knowledge_micro_packets: alle Dateien AUSSER KMP-HYP-* (die gehen an
    build_hypothese_kmp, siehe Stufe 2 -- sonst doppelte Quelle, B27-Verstoss).
    .json (23-Feld-Schema), .md (RAE_META HTML-comment JSON, heterogene
    Schluesselmengen je Datei), einige .md ohne RAE_META-Block (reiner Text)."""
    root = os.path.join(RE_ROOT, "knowledge_micro_packets")
    n_json = n_md_meta = n_md_nometa = n_skipped_hyp = 0
    for path in sorted(glob.glob(os.path.join(root, "**", "*"), recursive=True)):
        if not os.path.isfile(path):
            continue
        if os.path.basename(path).upper().startswith("KMP-HYP-"):
            n_skipped_hyp += 1
            continue
        ext = os.path.splitext(path)[1].lower()
        if ext == ".json":
            n_json += 1
            try:
                meta = json.load(open(path, encoding="utf-8"))
            except Exception:
                continue
            pid = meta.get("packet_id") or os.path.splitext(os.path.basename(path))[0]
            titel = meta.get("claim") or pid
            datum = meta.get("created_at") or meta.get("updated_at")
            belegt = True
        elif ext == ".md":
            raw = open(path, encoding="utf-8", errors="replace").read()
            m = re.search(r"RAE_META\n(.*?)\nRAE_META -->", raw, re.S)
            if m:
                n_md_meta += 1
                try:
                    meta = json.loads(m.group(1))
                except Exception:
                    meta = {}
                pid = meta.get("packet_id") or os.path.splitext(os.path.basename(path))[0]
                titel = meta.get("title") or pid
                datum = meta.get("created_at") or meta.get("updated_at")
                belegt = True
            else:
                n_md_nometa += 1
                pid = os.path.splitext(os.path.basename(path))[0]
                h1 = re.search(r"^#\s+(.+)$", raw, re.M)
                titel = h1.group(1).strip() if h1 else pid
                meta = {}
                datum = None
                belegt = True
        else:
            continue
        offene = extract_open_questions(meta)
        if not meta:
            offene.append({"feld": "quelle", "text": "keine strukturierten Metadaten im Quellfile gefunden (kein RAE_META-Block)"})
        yield {
            "id": slugify(pid),
            "art": "begriff",
            "titel": titel,
            "quelle": path,
            "quell_hash": sha256_file(path),
            "datum": datum,
            "metadaten": meta,
            "offene_fragen": offene,
            "belegt": belegt,
            "duenn": 0 if meta else 1,
        }
    sys.stderr.write(f"[begriff/kmp] json={n_json} md_mit_meta={n_md_meta} md_ohne_meta={n_md_nometa} an_hypothese_abgegeben={n_skipped_hyp}\n")

def build_begriff_topic_packets():
    root = os.path.join(RE_ROOT, "topic_packets")
    n = 0
    for path in sorted(glob.glob(os.path.join(root, "*", "PACKET.json"))):
        n += 1
        meta = json.load(open(path, encoding="utf-8"))
        pid = meta.get("packet_id") or os.path.basename(os.path.dirname(path))
        offene = extract_open_questions(meta)
        yield {
            "id": slugify(pid),
            "art": "begriff",
            "titel": meta.get("title") or pid,
            "quelle": path,
            "quell_hash": sha256_file(path),
            "datum": None,
            "metadaten": meta,
            "offene_fragen": offene,
            "belegt": True,
            "duenn": 0,
        }
    sys.stderr.write(f"[begriff/topic_packets] packet_json={n}\n")

def build_behauptung():
    """CLAIMS.jsonl -- Stufe 2: first_status steuert die art mechanisch:
    OPEN -> hypothese, REFUTED/SUPERSEDED -> gegenhypothese, sonst (CURRENT
    u.a.) -> behauptung wie bisher. Gemessen 2026-08-15: OPEN=5, REFUTED=26,
    SUPERSEDED=4, CURRENT=8 (total 43)."""
    path = os.path.join(RE_ROOT, "ledgers", "CLAIMS.jsonl")
    file_hash = sha256_file(path)
    n = 0
    counts = {}
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            n += 1
            meta = json.loads(line)
            cid = meta.get("claim_id") or f"CLAIM-LINE-{i}"
            status = meta.get("first_status")
            if status == "OPEN":
                art = "hypothese"
            elif status in ("REFUTED", "SUPERSEDED"):
                art = "gegenhypothese"
            else:
                art = "behauptung"
            counts[art] = counts.get(art, 0) + 1
            offene = extract_open_questions(meta)
            # CLAIMS hat keine falsifier/open_questions-Felder (geprueft);
            # REFUTED/SUPERSEDED tragen ein 'refutation'-Feld -- keine offene
            # Frage sondern Beleg, daher bewusst NICHT in offene_fragen gemappt.
            yield {
                "id": slugify(cid),
                "art": art,
                "titel": meta.get("proposition") or cid,
                "quelle": path,
                "quell_hash": file_hash,
                "datum": None,
                "metadaten": meta,
                "offene_fragen": offene,
                "belegt": True,
                "duenn": 0,
            }
    sys.stderr.write(f"[behauptung+hyp/CLAIMS] zeilen={n} verteilung={counts}\n")

def build_wirt():
    n = 0
    for wirt_dir in sorted(glob.glob(os.path.join(KARTE_ROOT, "*"))):
        if not os.path.isdir(wirt_dir):
            continue
        snaps = sorted(glob.glob(os.path.join(wirt_dir, "*.json")))
        if not snaps:
            continue
        latest = snaps[-1]  # filenames are zeitstempel-sortierbar (YYYYMMDDTHHMMSSZ.json)
        n += 1
        meta = json.load(open(latest, encoding="utf-8"))
        wirt = meta.get("wirt") or os.path.basename(wirt_dir)
        yield {
            "id": slugify(wirt),
            "art": "wirt",
            "titel": f"Wirt: {wirt}",
            "quelle": latest,
            "quell_hash": sha256_file(latest),
            "datum": meta.get("zeit"),
            "metadaten": meta,
            "offene_fragen": [],
            "belegt": True,
            "duenn": 0,
        }
    sys.stderr.write(f"[wirt] hosts={n}\n")

def build_vorfall():
    file_hash = sha256_file(PROTOKOLL)
    seen = {}
    n = 0
    with open(PROTOKOLL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n += 1
            meta = json.loads(line)
            bauteil = meta.get("bauteil") or "UNBEKANNT"
            zeit = meta.get("zeit") or ""
            base_id = f"{bauteil}-{zeit}"
            base_slug = slugify(base_id)
            if base_slug in seen:
                seen[base_slug] += 1
                slug = f"{base_slug}-{seen[base_slug]}"
            else:
                seen[base_slug] = 0
                slug = base_slug
            offene = []
            if "offen" in meta and meta["offen"]:
                offene.append({"feld": "offen", "text": str(meta["offen"])})
            yield {
                "id": slug,
                "art": "vorfall",
                "titel": meta.get("titel") or bauteil,
                "quelle": PROTOKOLL,
                "quell_hash": file_hash,
                "datum": meta.get("zeit"),
                "metadaten": meta,
                "offene_fragen": offene,
                "belegt": True,
                "duenn": 0,
                "_wirt": meta.get("wirt"),  # used for explicit deterministic edge, stripped before insert
            }
    sys.stderr.write(f"[vorfall] protokoll.jsonl lines={n}\n")

def build_forschungsergebnis():
    n_delta = n_report = n_manifest = 0
    # 1) work events kind == RESEARCH_DELTA
    events_dir = os.path.join(RE_ROOT, "state", "work", "events")
    for path in sorted(glob.glob(os.path.join(events_dir, "*.json"))):
        try:
            meta = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        if meta.get("kind") != "RESEARCH_DELTA":
            continue
        n_delta += 1
        eid = meta.get("event_id") or os.path.splitext(os.path.basename(path))[0]
        offene = extract_open_questions(meta)
        yield {
            "id": slugify(eid),
            "art": "forschungsergebnis",
            "titel": meta.get("mission") or eid,
            "quelle": path,
            "quell_hash": sha256_file(path),
            "datum": None,
            "metadaten": meta,
            "offene_fragen": offene,
            "belegt": True,
            "duenn": 0,
        }
    # 2) reports/*.md -- H1 title + "Key: value" header block, mechanically parsed
    reports_dir = os.path.join(RE_ROOT, "reports")
    header_re = re.compile(r"^\**([A-Za-z][A-Za-z0-9 _/\-]{1,40}?)\**:\s*(.+?)\s*$")
    for path in sorted(glob.glob(os.path.join(reports_dir, "*.md"))):
        n_report += 1
        raw = open(path, encoding="utf-8", errors="replace").read()
        lines = raw.splitlines()
        h1 = None
        header = {}
        started = False
        for ln in lines:
            m1 = re.match(r"^#\s+(.+)$", ln)
            if m1 and h1 is None:
                h1 = m1.group(1).strip()
                started = True
                continue
            if not started:
                continue
            if not ln.strip():
                if header:
                    break
                else:
                    continue
            if ln.strip().startswith("##"):
                break
            m2 = header_re.match(ln.strip())
            if m2:
                key = m2.group(1).strip()
                val = m2.group(2).strip().strip("`")
                header[key] = val
        meta = {"header": header, "quelldatei_basename": os.path.basename(path)}
        offene = extract_open_questions(header)
        rid = os.path.splitext(os.path.basename(path))[0]
        yield {
            "id": slugify(rid),
            "art": "forschungsergebnis",
            "titel": h1 or rid,
            "quelle": path,
            "quell_hash": sha256_file(path),
            "datum": header.get("Date"),
            "metadaten": meta,
            "offene_fragen": offene,
            "belegt": True,
            "duenn": 0,
        }
    # 3) atomic/runs/*/RUN_MANIFEST.json -- structured
    atomic_glob = os.path.join(RE_ROOT, "atomic", "runs", "*", "RUN_MANIFEST.json")
    for path in sorted(glob.glob(atomic_glob)):
        n_manifest += 1
        meta = json.load(open(path, encoding="utf-8"))
        rid = meta.get("run_id") or os.path.basename(os.path.dirname(path))
        offene = extract_open_questions(meta)
        yield {
            "id": slugify(rid),
            "art": "forschungsergebnis",
            "titel": meta.get("subject") or rid,
            "quelle": path,
            "quell_hash": sha256_file(path),
            "datum": None,
            "metadaten": meta,
            "offene_fragen": offene,
            "belegt": True,
            "duenn": 0,
        }
    sys.stderr.write(f"[forschungsergebnis] research_delta_events={n_delta} reports_md={n_report} atomic_run_manifests={n_manifest}\n")

# ---------------------------------------------------------------- Stufe 2: hypothese / gegenhypothese
# Owner-Auftrag: NUR aus Existierendem erkennen, nichts generieren.
# Gemessene Quellen (2026-08-15):
#   KMP-HYP-*.md unter knowledge_micro_packets:                    29 Dateien
#   CLAIMS.jsonl first_status=OPEN / REFUTED / SUPERSEDED:    5 / 26 / 4 Zeilen (in build_behauptung)
#   Dateiname enthaelt "hypothes" (ohne "counter"), ausserhalb kmp:  246 Dateien
#   Dateiname enthaelt "counterhypothes", ausserhalb kmp:            43 Dateien
#   Dateiname enthaelt "negative_result" (case-insens.), ausserh. kmp: 97 Dateien
#   Davon strukturiert (exakt HYPOTHESES.json / COUNTERHYPOTHESES.json,
#   Liste von dicts mit 'id'-Feld) -> Sub-Record-Ingestion je Eintrag:
#     HYPOTHESES.json:        83 Dateien, 796 Sub-Records (795 distinkte id, 1 Dup)
#     COUNTERHYPOTHESES.json:  9 Dateien,  40 Sub-Records, 44 attacks-Kanten
#                              versucht, 14 real aufloesbar (siehe Bericht)
#   HYPOTHESIS_FIELD_*.json / HYPOTHESIS_MATRIX.json haben dieselbe Struktur
#   (Liste unter 'hypotheses' mit 'id') und werden DESHALB strukturell (nicht
#   nach exaktem Dateinamen) ebenfalls sub-record-ingestiert.

def build_hypothese_kmp():
    root = os.path.join(RE_ROOT, "knowledge_micro_packets")
    n = 0
    for path in sorted(glob.glob(os.path.join(root, "**", "KMP-HYP-*.md"), recursive=True)):
        n += 1
        raw = open(path, encoding="utf-8", errors="replace").read()
        m = re.search(r"RAE_META\n(.*?)\nRAE_META -->", raw, re.S)
        if m:
            try:
                meta = json.loads(m.group(1))
            except Exception:
                meta = {}
        else:
            meta = {}
        pid = meta.get("packet_id") or os.path.splitext(os.path.basename(path))[0]
        h1 = re.search(r"^#\s+(.+)$", raw, re.M)
        titel = meta.get("title") or (h1.group(1).strip() if h1 else pid)
        offene = extract_open_questions(meta)
        duenn = 0 if meta else 1
        if not meta:
            offene.append({"feld": "quelle", "text": "kein RAE_META-Block; Titel mechanisch aus H1 uebernommen, Volltext nicht gespeichert (FTS-Aufgabe)"})
            meta = {"_hinweis": "kein RAE_META-Block"}
        yield {
            "id": slugify(pid),
            "art": "hypothese",
            "titel": titel,
            "quelle": path,
            "quell_hash": sha256_file(path),
            "datum": meta.get("created_at") or meta.get("updated_at"),
            "metadaten": meta,
            "offene_fragen": offene,
            "belegt": True,
            "duenn": duenn,
        }
    sys.stderr.write(f"[hypothese/kmp] KMP-HYP-Dateien={n}\n")

def _json_hyp_list(d):
    """Liste von Hypothese/Counterhypothese-Dicts aus heterogener JSON-Form
    (Datei = Liste direkt, ODER Dict mit Schluessel 'hypotheses'/'counterhypotheses')."""
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        for k in ("hypotheses", "counterhypotheses"):
            v = d.get(k)
            if isinstance(v, list):
                return v
    return None

def build_hypothesen_strukturiert():
    """Alle Dateien unter R (ausserhalb knowledge_micro_packets), deren
    Dateiname 'hypothes' enthaelt (case-insensitiv). Mechanische
    Klassifikation: 'counterhypothes' im Namen -> gegenhypothese, sonst
    hypothese. Wenn die geparste JSON eine Liste von Dicts mit 'id'-Feld
    ergibt (egal ob HYPOTHESES.json, HYPOTHESIS_FIELD_N.json oder
    HYPOTHESIS_MATRIX.json genannt -- Struktur entscheidet, nicht der exakte
    Name), wird JEDER Eintrag ein eigener Artikel (Sub-Record). Sonst wird
    die ganze Datei EIN Artikel (Datei-Ebene, wie Auftrag Abschnitt 1)."""
    n_files = n_sub = n_file_level = 0
    for path in sorted(glob.glob(os.path.join(RE_ROOT, "**", "*"), recursive=True)):
        if not os.path.isfile(path):
            continue
        if f"{os.sep}knowledge_micro_packets{os.sep}" in path:
            continue
        base = os.path.basename(path)
        if not re.search(r"hypothes", base, re.I):
            continue
        n_files += 1
        is_counter = bool(re.search(r"counterhypothes", base, re.I))
        art = "gegenhypothese" if is_counter else "hypothese"
        ext = os.path.splitext(path)[1].lower()
        rel = os.path.relpath(path, RE_ROOT)
        handled_as_sub = False
        if ext == ".json":
            try:
                d = json.load(open(path, encoding="utf-8"))
            except Exception:
                d = None
            lst = _json_hyp_list(d) if d is not None else None
            if lst and all(isinstance(x, dict) and x.get("id") for x in lst):
                handled_as_sub = True
                for item in lst:
                    n_sub += 1
                    iid = item["id"]
                    offene = extract_open_questions(item)
                    titel = item.get("claim") or item.get("mechanism") or item.get("counterhypothesis") or str(iid)
                    yield {
                        "id": slugify(iid),
                        "art": art,
                        "titel": str(titel)[:300],
                        "quelle": path,
                        "quell_hash": sha256_file(path),
                        "datum": None,
                        "metadaten": item,
                        "offene_fragen": offene,
                        "belegt": True,
                        "duenn": 0,
                    }
        if handled_as_sub:
            continue
        # Datei-Ebene (kein sub-record-faehiges Listen-Schema erkannt)
        n_file_level += 1
        meta = {}
        titel = base
        duenn = 1
        size = os.path.getsize(path)
        if ext == ".json":
            try:
                d2 = json.load(open(path, encoding="utf-8"))
            except Exception:
                d2 = None
            if isinstance(d2, dict):
                if size <= GROESSENGRENZE:
                    meta = d2
                else:
                    meta = {"_hinweis": "Datei >32KB, kein Volltext gespeichert (FTS-Aufgabe)", "_bytes": size}
                for k in ("title", "candidate", "counterhypothesis", "name", "run_id", "problem"):
                    if d2.get(k):
                        titel = str(d2[k])[:300]
                        duenn = 0
                        break
        elif ext == ".md" and size <= GROESSENGRENZE:
            raw = open(path, encoding="utf-8", errors="replace").read()
            h1_titel, hdr = _kv_header_from_md(raw)
            if h1_titel:
                titel = h1_titel
                duenn = 0
            if hdr:
                meta = hdr
                duenn = 0
        offene = extract_open_questions(meta) if isinstance(meta, dict) else []
        if duenn:
            offene.append({"feld": "quelle", "text": "kein sub-record-faehiges Listenschema und kein Titelfeld gefunden; Datei mechanisch als duenn eingetragen"})
        yield {
            "id": slugify(rel),
            "art": art,
            "titel": titel,
            "quelle": path,
            "quell_hash": sha256_file(path),
            "datum": None,
            "metadaten": meta,
            "offene_fragen": offene,
            "belegt": bool(meta),
            "duenn": duenn,
        }
    sys.stderr.write(f"[hypothese+gegenhypothese/strukturiert] dateien={n_files} sub_records={n_sub} datei_ebene={n_file_level}\n")

def build_gegenhypothese_negative_results():
    """Dateiname enthaelt 'negative_result' (case-insens.), ausserhalb
    knowledge_micro_packets (dort ist keine einzige Datei so benannt --
    geprueft; die dortigen '*-NEGATIVE*'-KMPs bleiben regulaere Begriffe)."""
    n = 0
    for path in sorted(glob.glob(os.path.join(RE_ROOT, "**", "*"), recursive=True)):
        if not os.path.isfile(path):
            continue
        if f"{os.sep}knowledge_micro_packets{os.sep}" in path:
            continue
        base = os.path.basename(path)
        if not re.search(r"negative_result", base, re.I):
            continue
        n += 1
        ext = os.path.splitext(path)[1].lower()
        rel = os.path.relpath(path, RE_ROOT)
        size = os.path.getsize(path)
        meta = {}
        titel = base
        duenn = 1
        if ext == ".json" and size <= GROESSENGRENZE:
            try:
                d = json.load(open(path, encoding="utf-8"))
                if isinstance(d, dict):
                    meta = d
                    for k in ("title", "summary", "claim", "run_id", "hypothesis", "name"):
                        if d.get(k):
                            titel = str(d[k])[:300]
                            duenn = 0
                            break
            except Exception:
                pass
        elif ext == ".md" and size <= GROESSENGRENZE:
            raw = open(path, encoding="utf-8", errors="replace").read()
            h1_titel, hdr = _kv_header_from_md(raw)
            if h1_titel:
                titel = h1_titel
                duenn = 0
            if hdr:
                meta = hdr
        elif ext == ".jsonl" and size <= GROESSENGRENZE:
            try:
                lines = [l for l in open(path, encoding="utf-8") if l.strip()]
                meta = {"_zeilen": len(lines)}
                if lines:
                    first = json.loads(lines[0])
                    if isinstance(first, dict):
                        meta["_erste_zeile"] = first
                        for k in ("title", "claim", "run_id"):
                            if first.get(k):
                                titel = str(first[k])[:300]
                                duenn = 0
                                break
            except Exception:
                pass
        elif size > GROESSENGRENZE:
            meta = {"_hinweis": "Datei >32KB, kein Volltext gespeichert (FTS-Aufgabe)", "_bytes": size}
        offene = extract_open_questions(meta) if isinstance(meta, dict) else []
        if duenn:
            offene.append({"feld": "quelle", "text": "kein Titelfeld gefunden; Datei mechanisch als duenn eingetragen"})
        yield {
            "id": slugify(rel),
            "art": "gegenhypothese",
            "titel": titel,
            "quelle": path,
            "quell_hash": sha256_file(path),
            "datum": None,
            "metadaten": meta,
            "offene_fragen": offene,
            "belegt": bool(meta),
            "duenn": duenn,
        }
    sys.stderr.write(f"[gegenhypothese/negative_result] dateien={n}\n")

# ---------------------------------------------------------------- Stufe 2: Sweep (Vollabdeckung)

def build_sweep(consumed_quelle):
    """JEDE Datei unter R, die kein vorheriger Builder schon als quelle
    beansprucht hat, bekommt eine Zeile. art = 'bereich_<oberster Ordner>'
    (mechanische Tatsache aus der vom Forschungswesen selbst gewaehlten
    Ordnerstruktur, keine erfundene Kategorie). Groessendisziplin: Dateien
    >32KB oder Nicht-Text bekommen keinen Volltext in metadaten."""
    n = 0
    n_thin = 0
    n_oversize = 0
    TEXT_EXT = {
        ".json", ".jsonl", ".md", ".txt", ".py", ".sql", ".lark", ".ebnf",
        ".clay", ".csv", ".diff", ".sh", ".service", ".env", ".c", ".ll",
        ".example",
    }
    for path in sorted(glob.glob(os.path.join(RE_ROOT, "**", "*"), recursive=True)):
        if not os.path.isfile(path):
            continue
        if path in consumed_quelle:
            continue
        n += 1
        rel = os.path.relpath(path, RE_ROOT)
        top = rel.split(os.sep)[0]
        art = f"bereich_{slugify(top)}"
        ext = os.path.splitext(path)[1].lower()
        size = os.path.getsize(path)
        oversize = size > GROESSENGRENZE
        if oversize:
            n_oversize += 1
        meta = {}
        titel = os.path.basename(path)
        duenn = 1
        if oversize:
            meta = {"_hinweis": "Datei >32KB, kein Volltext gespeichert (FTS-Aufgabe)", "_bytes": size}
        elif ext == ".json":
            try:
                d = json.load(open(path, encoding="utf-8"))
                if isinstance(d, dict):
                    meta = d
                    for k in ("title", "titel", "name", "run_id", "event_id",
                              "request_id", "receipt_id", "campaign_id",
                              "packet_id", "summary"):
                        if d.get(k):
                            titel = str(d[k])[:300]
                            duenn = 0
                            break
                elif isinstance(d, list):
                    meta = {"_typ": "liste", "_laenge": len(d)}
                else:
                    meta = {"_wert": d}
            except Exception:
                meta = {"_hinweis": "JSON-Parse fehlgeschlagen"}
        elif ext == ".jsonl":
            try:
                lines = [l for l in open(path, encoding="utf-8") if l.strip()]
                meta = {"_zeilen": len(lines)}
                if lines:
                    first = json.loads(lines[0])
                    if isinstance(first, dict):
                        meta["_erste_zeile"] = first
                        for k in ("title", "run_id", "claim_id", "event_id"):
                            if first.get(k):
                                titel = str(first[k])[:300]
                                duenn = 0
                                break
            except Exception:
                meta = {"_hinweis": "JSONL-Parse fehlgeschlagen"}
        elif ext == ".md":
            raw = open(path, encoding="utf-8", errors="replace").read()
            h1_titel, hdr = _kv_header_from_md(raw)
            if h1_titel:
                titel = h1_titel
                duenn = 0
            if hdr:
                meta = hdr
                duenn = 0
        else:
            # Code/Konfiguration: keine Zweck-Erfindung (Owner-Ehrlichkeitsregel).
            # titel bleibt Dateiname (Tatsache, keine Interpretation), meta leer.
            pass
        offene = extract_open_questions(meta) if isinstance(meta, dict) else []
        if duenn:
            n_thin += 1
            offene.append({"feld": "quelle", "text": "kein strukturiertes Titel-/Metadatenfeld gefunden (mechanisch, kein Modellaufruf); Datei als duenn eingetragen"})
        yield {
            "id": slugify(rel),
            "art": art,
            "titel": titel,
            "quelle": path,
            "quell_hash": sha256_file(path),
            "datum": None,
            "metadaten": meta,
            "offene_fragen": offene,
            "belegt": bool(meta) and not duenn,
            "duenn": duenn,
        }
    sys.stderr.write(f"[sweep] dateien={n} duenn={n_thin} oversize={n_oversize}\n")

# ---------------------------------------------------------------- edge resolution

def build_edges(all_articles):
    """Resolve raw ref strings against the id-set of ALREADY-BUILT articles.
    Only edges where BOTH endpoints are real article ids are kept -- per
    owner directive 'edge ids must be stable article ids, never free text'.

    Stufe 2: zusaetzlich zur generischen feld-benannten Kante werden fuer
    zwei Felder SEMANTISCHE Kanten miterzeugt (beide Male reale, aufgeloeste
    Ziel-ids, keine Erfindung):
      'attacks'                -> zusaetzlich art='widerspricht' (von=gegenhyp, nach=hyp)
      'evidence'/'evidence_refs' -> zusaetzlich art='stuetzt' (von=Beleg-Artikel, nach=Quelle)
    """
    by_id = {a["id"]: a for a in all_articles}
    all_ids = set(by_id.keys())
    edges = []
    unresolved = 0
    resolved = 0
    for a in all_articles:
        cands = extract_edge_candidates(a["metadaten"])
        for field, raw in cands:
            hit = None
            for norm in ref_to_slug_candidates(raw):
                if norm in all_ids and norm != a["id"]:
                    hit = norm
                    break
            if hit:
                edges.append((a["id"], hit, field, a["quelle"]))
                resolved += 1
                if field == "attacks":
                    edges.append((a["id"], hit, "widerspricht", a["quelle"]))
                elif field in ("evidence", "evidence_refs"):
                    edges.append((hit, a["id"], "stuetzt", a["quelle"]))
            else:
                unresolved += 1
        # explicit deterministic vorfall -> wirt edge (field name, not free-text guess)
        w = a.get("_wirt")
        if w:
            wslug = slugify(w)
            if wslug in all_ids:
                edges.append((a["id"], wslug, "wirt", a["quelle"]))
                resolved += 1
            else:
                unresolved += 1
    return edges, resolved, unresolved

# ---------------------------------------------------------------- bauen

def cmd_bauen():
    t0 = time.time()
    con = connect_db()
    ensure_schema(con)

    # Reihenfolge wichtig: alle spezifischen Builder ZUERST, damit ihre
    # 'quelle'-Pfade als "schon verbraucht" gelten, bevor der Sweep laeuft.
    spezifische_builder = [
        build_begriff_kmp(),
        build_begriff_topic_packets(),
        build_behauptung(),
        build_wirt(),
        build_vorfall(),
        build_forschungsergebnis(),
        build_hypothese_kmp(),
        build_hypothesen_strukturiert(),
        build_gegenhypothese_negative_results(),
    ]
    all_articles = []
    consumed_quelle = set()
    id_seen = {}
    for gen in spezifische_builder:
        for art in gen:
            aid = art["id"]
            if aid in id_seen:
                id_seen[aid] += 1
                art["id"] = f"{aid}-dup{id_seen[aid]}"
                sys.stderr.write(f"[warn] id collision, renamed: {aid} -> {art['id']} ({art['quelle']})\n")
            else:
                id_seen[aid] = 0
            all_articles.append(art)
            if art["quelle"] and art["quelle"].startswith(RE_ROOT):
                consumed_quelle.add(art["quelle"])

    t_spezifisch = time.time()

    for art in build_sweep(consumed_quelle):
        aid = art["id"]
        if aid in id_seen:
            id_seen[aid] += 1
            art["id"] = f"{aid}-dup{id_seen[aid]}"
            sys.stderr.write(f"[warn] id collision, renamed: {aid} -> {art['id']} ({art['quelle']})\n")
        else:
            id_seen[aid] = 0
        all_articles.append(art)

    t_sweep = time.time()

    edges, resolved, unresolved = build_edges(all_articles)

    t_edges = time.time()

    git_dates, git_authors = load_git_provenance()

    t_git = time.time()

    ts = now_iso()
    cur = con.cursor()
    carry_snapshot = load_carryforward_snapshot(cur)  # STOP-Level-Fix Teil (a) + selbst gefundener Zwilling (projekt/projekt_art/sphaere)
    zq_counts = {}
    vq_counts = {}
    id_quelle_counts = {}
    logical_id_counts = {}
    epistemic_filled = status_filled = scope_filled = tags_filled = konfidenz_filled = 0
    for a in all_articles:
        datum_wb, zq, von, vq = resolve_provenance(a["quelle"], a["metadaten"], git_dates, git_authors)
        zq_counts[zq] = zq_counts.get(zq, 0) + 1
        vq_counts[vq] = vq_counts.get(vq, 0) + 1
        epistemic_class, status, scope, tags, konfidenz, logical_id, id_quelle = resolve_lift_fields(a["art"], a["metadaten"])
        id_quelle_counts[id_quelle] = id_quelle_counts.get(id_quelle, 0) + 1
        if logical_id:
            logical_id_counts[logical_id] = logical_id_counts.get(logical_id, 0) + 1
        epistemic_filled += 1 if epistemic_class else 0
        status_filled += 1 if status else 0
        scope_filled += 1 if scope else 0
        tags_filled += 1 if tags else 0
        konfidenz_filled += 1 if konfidenz is not None else 0
        # STOP-Level-Fix (a) + Zwilling + dritter Fund (2026-08-15, urgent):
        # vorhandene herkunft/projekt/projekt_art/sphaere/verfallen/protected
        # MITGEBEN statt implizit auf den Default/NULL zurueckfallen zu lassen
        # -- INSERT OR REPLACE ersetzt sonst die GANZE Zeile.
        herkunft_wert, projekt_alt, projekt_art_alt, sphaere_alt, verfallen_alt, protected_alt = carry_snapshot.get(
            a["id"], ("gemessen", None, None, None, 0, 0)
        )
        cur.execute(
            "INSERT OR REPLACE INTO artikel "
            "(id, art, titel, quelle, quell_hash, datum, metadaten, offene_fragen, belegt, erzeugt_am, "
            " duenn, zuletzt_bearbeitet, zeitquelle, wirt, zuletzt_von, von_quelle, "
            " logical_id, id_quelle, epistemic_class, status, scope, tags, konfidenz, herkunft, "
            " projekt, projekt_art, sphaere, verfallen, protected) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                a["id"], a["art"], a["titel"], a["quelle"], a["quell_hash"], a["datum"],
                json.dumps(a["metadaten"], ensure_ascii=False),
                json.dumps(a["offene_fragen"], ensure_ascii=False),
                1 if a["belegt"] else 0,
                ts,
                1 if a.get("duenn") else 0,
                datum_wb, zq, WIRT_KONSTANTE, von, vq,
                logical_id, id_quelle, epistemic_class, status, scope, tags, konfidenz,
                herkunft_wert, projekt_alt, projekt_art_alt, sphaere_alt, verfallen_alt, protected_alt,
            ),
        )
    # URGENT FIX 2026-08-15: kante bekam heute konfidenz/erzeugt_am/
    # zeitquelle/verfallen/protected (Verfalls-Arbeit). Die alte
    # INSERT OR REPLACE (nur von,nach,art,beleg) haette bei jeder
    # Wiederbestaetigung einer bestehenden Kante GENAU denselben Fehler
    # wiederholt wie eben erst bei artikel gefunden -- ganze Zeile ersetzt,
    # Rest auf Default. Gewaehlter Fix: ON CONFLICT DO UPDATE statt Snapshot+
    # Carry-Forward (anders als bei artikel) -- BEGRUENDUNG: wiki.py ist bei
    # kante nie Besitzer von konfidenz/erzeugt_am/zeitquelle/verfallen/
    # protected (die gehoeren verfall.py/kanten.py), sondern nur von beleg.
    # "Ruehr nichts an, was dir nicht gehoert" ist hier direkter ausdrueckbar
    # als ein Snapshot-Read + Copy-Through -- die Ziel-Spalten der DO-UPDATE-
    # Klausel sind explizit NUR beleg, alles andere bleibt unangetastet,
    # unabhaengig vom aktuellen Wert (kein Lesen noetig, kein Race).
    for von, nach, art, beleg in edges:
        cur.execute(
            "INSERT INTO kante (von, nach, art, beleg) VALUES (?,?,?,?) "
            "ON CONFLICT(von, nach, art) DO UPDATE SET beleg=excluded.beleg",
            (von, nach, art, beleg),
        )
    con.commit()
    reapply_stats = reapply_owner_edits(cur)  # STOP-Level-Fix Teil (b)
    con.commit()

    t_insert = time.time()

    # orphan count: articles with zero edges in either direction
    cur.execute("SELECT COUNT(*) FROM artikel")
    n_artikel = cur.fetchone()[0]
    cur.execute("""
        SELECT COUNT(*) FROM artikel a WHERE NOT EXISTS (
            SELECT 1 FROM kante k WHERE k.von = a.id OR k.nach = a.id
        )
    """)
    n_orphan = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM kante")
    n_kante = cur.fetchone()[0]

    elapsed = time.time() - t0
    db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    wal_size = os.path.getsize(DB_PATH + "-wal") if os.path.exists(DB_PATH + "-wal") else 0

    stats = {
        "erzeugt_am": ts,
        "laufzeit_sekunden": round(elapsed, 3),
        "laufzeit_teilschritte_sekunden": {
            "spezifische_builder": round(t_spezifisch - t0, 3),
            "sweep": round(t_sweep - t_spezifisch, 3),
            "kanten_aufloesung": round(t_edges - t_sweep, 3),
            "git_provenienz_ein_pass": round(t_git - t_edges, 3),
            "db_insert": round(t_insert - t_git, 3),
        },
        "artikel_gesamt": n_artikel,
        "artikel_duenn": sum(1 for a in all_articles if a.get("duenn")),
        "herkunft_erhalten": reapply_stats,
        "kanten_gesamt": n_kante,
        "kanten_aufgeloest": resolved,
        "kanten_nicht_aufgeloest_verworfen": unresolved,
        "artikel_ohne_kante": n_orphan,
        "db_bytes": db_size,
        "db_wal_bytes": wal_size,
        "zeitquelle_verteilung": zq_counts,
        "von_quelle_verteilung": vq_counts,
        "id_quelle_verteilung": id_quelle_counts,
        "lift_spalten_fuellgrad": {
            "logical_id": sum(logical_id_counts.values()),
            "epistemic_class": epistemic_filled,
            "status": status_filled,
            "scope": scope_filled,
            "tags": tags_filled,
            "konfidenz": konfidenz_filled,
            "von_artikel_gesamt": len(all_articles),
        },
        "logical_id_distinkt": len(logical_id_counts),
        "logical_id_top5_mehrfach": sorted(
            ({"logical_id": k, "anzahl_artikel": v} for k, v in logical_id_counts.items() if v > 1),
            key=lambda x: -x["anzahl_artikel"],
        )[:5],
    }
    cur.execute("SELECT art, COUNT(*) FROM artikel GROUP BY art")
    stats["pro_typ"] = dict(cur.fetchall())
    cur.execute("SELECT art, COUNT(*) FROM kante GROUP BY art")
    stats["kanten_pro_typ"] = dict(cur.fetchall())
    cur.execute("SELECT MIN(zuletzt_bearbeitet), MAX(zuletzt_bearbeitet) FROM artikel WHERE zuletzt_bearbeitet IS NOT NULL")
    row = cur.fetchone()
    stats["zuletzt_bearbeitet_range"] = {"aeltestes": row[0], "neuestes": row[1]}
    con.close()

    os.makedirs(os.path.dirname(BUILD_LOG), exist_ok=True)
    json.dump(stats, open(BUILD_LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(stats, ensure_ascii=False, indent=2))

# ---------------------------------------------------------------- stand

def cmd_stand():
    con = connect_db()
    ensure_schema(con)
    cur = con.cursor()
    t0 = time.perf_counter()
    cur.execute("SELECT art, COUNT(*) FROM artikel GROUP BY art ORDER BY art")
    rows = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM artikel")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM kante")
    kanten = cur.fetchone()[0]
    cur.execute("""SELECT COUNT(*) FROM artikel a WHERE NOT EXISTS (
        SELECT 1 FROM kante k WHERE k.von=a.id OR k.nach=a.id)""")
    orphans = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM artikel WHERE quell_hash IS NOT NULL AND quell_hash != ''")
    with_hash = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM artikel WHERE duenn=1")
    duenn = cur.fetchone()[0]
    cur.execute("SELECT zeitquelle, COUNT(*) FROM artikel GROUP BY zeitquelle")
    zq = dict(cur.fetchall())
    cur.execute("SELECT von_quelle, COUNT(*) FROM artikel GROUP BY von_quelle")
    vq = dict(cur.fetchall())
    ms = (time.perf_counter() - t0) * 1000
    out = {
        "pro_typ": dict(rows),
        "artikel_gesamt": total,
        "artikel_duenn": duenn,
        "kanten_gesamt": kanten,
        "artikel_ohne_kante": orphans,
        "artikel_mit_quell_hash": with_hash,
        "zeitquelle_verteilung": zq,
        "von_quelle_verteilung": vq,
        "abfragezeit_ms": round(ms, 3),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    con.close()

# ---------------------------------------------------------------- artikel

def cmd_artikel(aid):
    con = connect_db()
    ensure_schema(con)
    cur = con.cursor()
    t0 = time.perf_counter()
    cur.execute("SELECT id, art, titel, quelle, quell_hash, datum, metadaten, offene_fragen, belegt, erzeugt_am, duenn, zuletzt_bearbeitet, zeitquelle, wirt, zuletzt_von, von_quelle, logical_id, id_quelle, epistemic_class, status, scope, tags, konfidenz FROM artikel WHERE id=?", (aid,))
    row = cur.fetchone()
    if not row:
        print(json.dumps({"error": f"kein Artikel mit id={aid}"}, ensure_ascii=False))
        con.close()
        return
    cols = ["id","art","titel","quelle","quell_hash","datum","metadaten","offene_fragen","belegt","erzeugt_am",
            "duenn","zuletzt_bearbeitet","zeitquelle","wirt","zuletzt_von","von_quelle",
            "logical_id","id_quelle","epistemic_class","status","scope","tags","konfidenz"]
    art = dict(zip(cols, row))
    art["metadaten"] = json.loads(art["metadaten"]) if art["metadaten"] else {}
    art["offene_fragen"] = json.loads(art["offene_fragen"]) if art["offene_fragen"] else []
    cur.execute("SELECT von, nach, art, beleg FROM kante WHERE von=? OR nach=?", (aid, aid))
    kanten = [{"von": v, "nach": n, "art": a, "beleg": b} for v, n, a, b in cur.fetchall()]
    ms = (time.perf_counter() - t0) * 1000
    out = {"artikel": art, "kanten": kanten, "abfragezeit_ms": round(ms, 3)}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    con.close()

# ---------------------------------------------------------------- Stufe 3: echte Klon-Historie
# Owner-Befund 2026-08-15: /opt/clayverse selbst hat nur 2 Commits ueber den
# ganzen research_entity-Baum (Bulk-Import) -- git-Datum war praktisch so
# uniform wie die mtime-Falle, nur eine Ebene tiefer. FIX: alle 21 baeume/
# wurden unshallowed unter /var/lib/clay/klone/<repo>/ -- dort steckt die
# echte Herkunfts-Historie (10281 Commits / 19 Autoren allein fuer
# clay-global-research-entity, ab 2026-08-07/08).
#
# Mapping (verifiziert 2026-08-15 an Stichproben, siehe Bericht): artikel.quelle
# = /opt/clayverse/baeume/<repo>/<relpath> ; dieselbe <repo>/<relpath> liegt
# repo-root-relativ in /var/lib/clay/klone/<repo>/. Bestaetigt: git-Log-Pfade
# in der clay-global-research-entity-Klon-Historie beginnen exakt mit
# "research_entity/...", identisch zum RE_ROOT-relativen Pfad.
# Nicht anwendbar (kein baeume/-Praefix): KARTE_ROOT (/var/lib/clay/karte,
# wirt-Artikel) und PROTOKOLL (/opt/clayverse/bau/protokoll.jsonl,
# vorfall-Artikel) -- die liegen ausserhalb jedes Klons, bleiben unveraendert.

KLONE_ROOT = "/var/lib/clay/klone"
BAEUME_PREFIX = "/opt/clayverse/baeume/"

def load_klone_provenance():
    """Ein Subprocess je Klon (21 insgesamt). Liefert
    {repo: (pfad->datum, pfad->autor)}, neueste Commit-Zeile gewinnt je Pfad."""
    result = {}
    if not os.path.isdir(KLONE_ROOT):
        return result
    for repo in sorted(os.listdir(KLONE_ROOT)):
        repo_dir = os.path.join(KLONE_ROOT, repo)
        if not os.path.isdir(os.path.join(repo_dir, ".git")):
            continue
        try:
            out = subprocess.run(
                ["git", "log", "--format=C|%cI\t%an", "--name-only", "--no-renames"],
                cwd=repo_dir, capture_output=True, text=True, check=False, timeout=180,
            ).stdout
        except Exception:
            out = ""
        dates, authors = {}, {}
        cur_date = cur_author = None
        for line in out.splitlines():
            if line.startswith("C|"):
                rest = line[2:]
                cur_date, _, cur_author = rest.partition("\t")
                continue
            p = line.strip()
            if not p:
                continue
            if p not in dates:
                dates[p] = cur_date
                authors[p] = cur_author
        result[repo] = (dates, authors)
    return result

def resolve_via_klone(quelle, klone_map):
    """Gibt (repo, datum_oder_None, autor_oder_None) zurueck.
    repo=None heisst: quelle liegt gar nicht unter baeume/ -- Klon-Lookup
    ist nicht anwendbar (nicht dasselbe wie 'unresolved')."""
    if not quelle or not quelle.startswith(BAEUME_PREFIX):
        return None, None, None
    rest = quelle[len(BAEUME_PREFIX):]
    parts = rest.split("/", 1)
    if len(parts) != 2:
        return None, None, None
    repo, relpath = parts
    dates, authors = klone_map.get(repo, ({}, {}))
    if relpath in dates and dates[relpath]:
        return repo, dates[relpath], authors.get(relpath)
    return repo, None, None

def cmd_provenienz_reparieren():
    t0 = time.time()
    con = connect_db()
    ensure_schema(con)
    cur = con.cursor()

    klone_map = load_klone_provenance()
    t_klone = time.time()
    klone_repo_stats = {r: len(d) for r, (d, _) in klone_map.items()}

    cur.execute("SELECT id, quelle, zeitquelle, zuletzt_von, von_quelle FROM artikel")
    rows = cur.fetchall()

    per_repo_resolved = {}
    per_repo_unresolved = {}
    n_not_applicable = 0
    n_resolved = 0
    n_unresolved_marked = 0
    n_unresolved_kept_quiet = 0
    date_updates = []
    mark_only_updates = []

    for aid, quelle, old_zq, old_von, old_vq in rows:
        repo, datum, autor = resolve_via_klone(quelle, klone_map)
        if repo is None:
            n_not_applicable += 1
            continue
        if datum:
            per_repo_resolved[repo] = per_repo_resolved.get(repo, 0) + 1
            n_resolved += 1
            new_von = autor if autor else old_von
            new_vq = "git" if autor else old_vq
            date_updates.append((datum, "git", new_von, new_vq, aid))
        else:
            per_repo_unresolved[repo] = per_repo_unresolved.get(repo, 0) + 1
            if old_zq == "git":
                # Das war der degenerierte Bulk-Import-Wert -- jetzt sichtbar
                # als Fallback markiert, alter Wert (zuletzt_bearbeitet/-von)
                # bleibt unangetastet stehen, nur zeitquelle/von_quelle
                # bekommen den Fallback-Marker.
                new_vq = "git-bulkimport-fallback" if old_vq == "git" else old_vq
                mark_only_updates.append(("git-bulkimport-fallback", new_vq, aid))
                n_unresolved_marked += 1
            else:
                n_unresolved_kept_quiet += 1

    for datum, zq, von, vq, aid in date_updates:
        cur.execute(
            "UPDATE artikel SET zuletzt_bearbeitet=?, zeitquelle=?, zuletzt_von=?, von_quelle=? WHERE id=?",
            (datum, zq, von, vq, aid),
        )
    for zq, vq, aid in mark_only_updates:
        cur.execute(
            "UPDATE artikel SET zeitquelle=?, von_quelle=? WHERE id=?",
            (zq, vq, aid),
        )
    con.commit()
    t_update = time.time()

    cur.execute("SELECT MIN(zuletzt_bearbeitet), MAX(zuletzt_bearbeitet) FROM artikel WHERE zuletzt_bearbeitet IS NOT NULL")
    rng = cur.fetchone()
    cur.execute("SELECT zuletzt_von, COUNT(*) FROM artikel WHERE zuletzt_von IS NOT NULL GROUP BY zuletzt_von ORDER BY 2 DESC")
    von_counts_all = cur.fetchall()
    cur.execute("SELECT COUNT(DISTINCT zuletzt_von) FROM artikel WHERE zuletzt_von IS NOT NULL")
    distinct_von = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM artikel WHERE zeitquelle='git-bulkimport-fallback'")
    n_fallback_bulk = cur.fetchone()[0]
    cur.execute("SELECT zeitquelle, COUNT(*) FROM artikel GROUP BY zeitquelle")
    zq_after = dict(cur.fetchall())

    stats = {
        "laufzeit_sekunden": round(time.time() - t0, 3),
        "laufzeit_klone_git_log_pass_sekunden": round(t_klone - t0, 3),
        "laufzeit_db_update_sekunden": round(t_update - t_klone, 3),
        "klone_gelesen": len(klone_map),
        "pfade_pro_klon_git_historie": klone_repo_stats,
        "zeilen_gesamt_artikel": len(rows),
        "nicht_anwendbar_ausserhalb_baeume_praefix": n_not_applicable,
        "aufgeloest_gesamt": n_resolved,
        "aufgeloest_pro_repo": per_repo_resolved,
        "nicht_aufgeloest_pro_repo": per_repo_unresolved,
        "nicht_aufgeloest_als_fallback_markiert": n_unresolved_marked,
        "nicht_aufgeloest_unveraendert_ohne_markierung": n_unresolved_kept_quiet,
        "zuletzt_bearbeitet_range_NACH_reparatur": {"aeltestes": rng[0], "neuestes": rng[1]},
        "zuletzt_von_distinkt": distinct_von,
        "zuletzt_von_top10": von_counts_all[:10],
        "faellt_noch_auf_bulk_importdatum_zurueck": n_fallback_bulk,
        "zeitquelle_verteilung_NACH_reparatur": zq_after,
    }
    con.close()
    print(json.dumps(stats, ensure_ascii=False, indent=2, default=str))

# ---------------------------------------------------------------- Stufe 4: projekt / projekt_art / sphaere / IAR
# Owner-Auftrag 2026-08-15 (zwei Teile) + Coordinator-Zusatz (IAR-Institutsseite).
# Teil 1: JEDER Artikel bekommt projekt (mechanisch aus quelle) + projekt_art
#         (gemessen: Remote-URL, VERWEISE.json, Autorenschaft).
# Teil 2: sphaere NUR wo Repo/Pfad es eindeutig entscheidet -- sonst NULL.
# Zusatz: IAR-Seite (iar.frank.ink) einlesen, komplett ausserhalb baeume/,
#         projekt='iar', projekt_art='eigen' (Owner-Vorgabe), sphaere='iar'.

INTERNAL_AUTHOR_RE = re.compile(
    r"(?i)^(gabriel|andreas|gschaider|clay|frank|rae-|claude|github-actions|"
    r"video launch page|hostinger|q23-|clayverse)"
)

def derive_projekt(quelle):
    """Mechanisch aus dem Pfad. Gibt None zurueck, wenn nichts passt (wird
    als 'nicht platzierbar' gezaehlt und gemeldet, nie geraten)."""
    if not quelle:
        return None
    if quelle.startswith(BAEUME_PREFIX):
        rest = quelle[len(BAEUME_PREFIX):]
        repo = rest.split("/", 1)[0] if rest else ""
        return repo or None
    if quelle.startswith(KARTE_ROOT):
        return "kartographie"
    if quelle.startswith(os.path.dirname(PROTOKOLL) + os.sep) or quelle == PROTOKOLL:
        return "clayverse-bau"
    if quelle.startswith(IAR_SITE_ROOT):
        return "iar"
    if quelle.startswith(STROM_ROOT) and os.path.basename(quelle) in STROM_DATEIEN:
        return "clayverse-strom"
    return None

def load_klone_repo_authors():
    """Ein Subprocess je Klon (21), NUR fuer die distinkte Autorenmenge je
    Repo (nicht je Datei -- eigene, leichtere Abfrage als load_git_provenance)."""
    result = {}
    if not os.path.isdir(KLONE_ROOT):
        return result
    for repo in sorted(os.listdir(KLONE_ROOT)):
        repo_dir = os.path.join(KLONE_ROOT, repo)
        if not os.path.isdir(os.path.join(repo_dir, ".git")):
            continue
        try:
            out = subprocess.run(
                ["git", "log", "--format=%an"],
                cwd=repo_dir, capture_output=True, text=True, check=False, timeout=60,
            ).stdout
        except Exception:
            out = ""
        authors = sorted(set(l.strip() for l in out.splitlines() if l.strip()))
        result[repo] = authors
    return result

def load_klone_remotes():
    """Ein weiterer Subprocess je Klon: origin-URL (kann leer sein)."""
    result = {}
    if not os.path.isdir(KLONE_ROOT):
        return result
    for repo in sorted(os.listdir(KLONE_ROOT)):
        repo_dir = os.path.join(KLONE_ROOT, repo)
        if not os.path.isdir(os.path.join(repo_dir, ".git")):
            continue
        try:
            out = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=repo_dir, capture_output=True, text=True, check=False, timeout=30,
            ).stdout.strip()
        except Exception:
            out = ""
        result[repo] = out
    return result

def compute_projekt_art_map():
    """{projekt: (art, begruendung)} -- gemessen, nicht geraten. Regeln in
    Prioritaetsreihenfolge:
      1. VERWEISE.json markiert den Namen explizit als Verweis (Fremdcode,
         nicht gespiegelt) -> 'fork'.
      2. origin-Remote zeigt auf github.com/gschaidergabriel/* UND alle
         distinkten Commit-Autoren matchen das interne Namensschema
         (Gabriel/Andreas/rae-*/clay-*/frank-*/claude/bots) -> 'eigen'.
      3. Remote zeigt auf gschaidergabriel/*, aber mindestens ein Autor
         matcht NICHT -> 'fremd' (externe Beitraege im eigenen Klon).
      4. Remote zeigt auf eine andere Org/Host -> 'fremd'.
      5. Kein Remote konfigurierbar -> 'unbekannt'.
    Nicht-Klon-Projekte (iar/kartographie/clayverse-bau) werden separat mit
    Owner-/strukturell begruendeten Werten ergaenzt (siehe unten)."""
    verweis_names = set()
    if os.path.exists(VERWEISE_PATH):
        try:
            v = json.load(open(VERWEISE_PATH, encoding="utf-8"))
            verweis_names = {e.get("name") for e in v.get("verweise", []) if e.get("name")}
        except Exception:
            pass

    remotes = load_klone_remotes()
    authors_map = load_klone_repo_authors()
    result = {}
    for repo in sorted(set(remotes) | set(authors_map)):
        if repo in verweis_names:
            result[repo] = ("fork", f"VERWEISE.json markiert '{repo}' als Verweis auf fremden Upstream (nicht gespiegelt, kein Klon vorhanden)")
            continue
        url = remotes.get(repo, "")
        authors = authors_map.get(repo, [])
        if not url:
            result[repo] = ("unbekannt", "kein origin-Remote lesbar")
            continue
        eigene_org = ("github.com/gschaidergabriel/" in url) or ("github.com:gschaidergabriel/" in url)
        if not eigene_org:
            result[repo] = ("fremd", f"remote={url} zeigt auf eine andere Organisation/Host als gschaidergabriel")
            continue
        if not authors:
            result[repo] = ("eigen", f"remote={url} (Gabriels eigene GitHub-Org), 0 Commits in der Historie -- Einordnung ausschliesslich aus der Remote-Org")
            continue
        fremde_autoren = [a for a in authors if not INTERNAL_AUTHOR_RE.match(a)]
        if not fremde_autoren:
            result[repo] = ("eigen", f"remote={url} (eigene Org), alle {len(authors)} distinkten Autoren matchen das interne Namensschema (Gabriel/Andreas/rae-*/clay-*/frank-*/Bots)")
        else:
            result[repo] = ("fremd", f"remote={url} (eigene Org), aber {len(fremde_autoren)} Autor(en) ausserhalb des internen Schemas: {fremde_autoren[:5]}")

    # Nicht-Klon-Projekte, die trotzdem als projekt-Wert vorkommen koennen:
    result["iar"] = ("eigen", "Owner-Vorgabe: IAR-Institutsseite ist eigenes Projekt (JSON-LD auf iar.frank.ink: Gruender Dr. Andreas Unterweger + Gabriel Gschaider, office@agentic-research.org, ZVR 1741094409)")
    result["kartographie"] = ("eigen", "ClayVerse-eigene Host-Telemetrie unter /var/lib/clay/karte, kein externer Ursprung feststellbar")
    result["clayverse-bau"] = ("eigen", "ClayVerse-eigenes Build-/Deploy-Protokoll unter /opt/clayverse/bau, kein externer Ursprung feststellbar")
    result["clayverse-strom"] = ("eigen", "ClayVerse-eigene Append-only-Betriebsstroeme (ereignisse/tor/eichung/eichnormale.jsonl) unter /var/lib/clay, kein externer Ursprung feststellbar")
    return result

def decide_sphaere(projekt, quelle):
    """Gibt (sphaere, beleg) oder (None, None) zurueck. NUR wenn Repo/Pfad es
    eindeutig entscheiden -- sonst explizit (None, None), niemals geraten."""
    if projekt == "iar":
        return "iar", "gesamte iar.frank.ink-Seite ist per Definition das Institut fuer Agentic Research"
    if projekt == "Project-Frankenstein":
        return "frank_v0_1", "Owner-Vorgabe 2026-08-15: Project-Frankenstein -> frank_v0_1"
    if projekt == "gabriel-claude":
        return "gabriel", "Owner-Vorgabe 2026-08-15: gabriel-claude -> gabriel"
    if projekt in ("andreas-claude", "Andreas-Resercher", "AndreasClaude", "Dr.-Unterweger"):
        return "andreas", f"Repo-Name eindeutig Andreas-persoenlich ('{projekt}'), gleiche Evidenzstufe wie Owner-Beispiel andreas-claude"
    if projekt in ("kartographie", "clayverse-bau", "clayverse-strom"):
        return "clayverse", f"'{projekt}' ist ClayVerse-eigene Betriebstelemetrie/-protokoll, keine Forschungsinhalte, unzweideutig ClayVerse-Infrastruktur"
    if projekt == "clay-global-research-entity" and quelle and quelle.startswith(BAEUME_PREFIX):
        rest = quelle[len(BAEUME_PREFIX):]
        parts = rest.split("/", 1)
        rel = parts[1] if len(parts) == 2 else ""
        if rel.startswith("research_entity/frank_v0_1/"):
            return "frank_v0_1", "Pfad-Ebene: liegt im vom Research-Entity SELBST so benannten Ordner research_entity/frank_v0_1/ (mechanische Tatsache, kein Keyword-Sniffing im Inhalt)"
        # research_entity/frank/ (ohne v0_1) bleibt bewusst UNENTSCHIEDEN:
        # der Baum unterscheidet frank_v0_1 und frank als zwei verschiedene
        # Ordner -- welche Epoche/welches Projekt "frank/" konkret meint,
        # ist ohne Inhalts-Interpretation nicht sicher zu sagen.
        return None, None
    # Alle anderen Klon-Repos (agentforge, clay, digital-retina, ...): kein
    # Artikel referenziert sie aktuell als quelle (gemessen -- siehe Bericht),
    # und ohne artikelspezifische Evidenz waere jede Zuordnung eine
    # Vermutung. Bewusst NULL.
    return None, None

# ---------------------------------------------------------------- Stufe 4: IAR-Seite einlesen

_HTML_STRIP_RE = re.compile(r"<(script|style|head|nav|footer)[^>]*>.*?</\1>", re.S | re.I)
_BODY_RE = re.compile(r"<body[^>]*>(.*)</body>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
_META_DESC_RE = re.compile(r'<meta\s+name="description"\s+content="(.*?)"', re.I)
_JSONLD_RE = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S | re.I)
_BYLINE_RE = re.compile(
    r"(?:Von|By)\s+([A-Za-zÄÖÜäöüß.\-' ]{3,60}?)\s*(?:\(.*?\)\s*)?·\s*"
    r"([0-9]{1,2}\.\s*[A-Za-zÄÖÜäöüß]+\s*[0-9]{4}|[A-Za-z]+ [0-9]{1,2}, [0-9]{4})"
)

def strip_html_to_text(path):
    """Mechanisch: script/style/head/nav/footer raus, Rest-Tags raus,
    Entities aufgeloest. Nie gerendert, nie modellbasiert."""
    raw = open(path, encoding="utf-8", errors="replace").read()
    tm = _TITLE_RE.search(raw)
    titel = re.sub(r"\s+", " ", tm.group(1)).strip() if tm else None
    dm = _META_DESC_RE.search(raw)
    beschreibung = dm.group(1).strip() if dm else None
    jsonld = []
    for jm in _JSONLD_RE.finditer(raw):
        try:
            jsonld.append(json.loads(jm.group(1)))
        except Exception:
            pass
    stripped = _HTML_STRIP_RE.sub(" ", raw)
    bm = _BODY_RE.search(stripped)
    inner = bm.group(1) if bm else stripped
    text = _TAG_RE.sub(" ", inner)
    import html as htmlmod
    text = htmlmod.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    text = " ".join(lines)
    return titel, beschreibung, jsonld, text

def parse_md_frontmatter(raw):
    """--- YAML --- Block am Dateianfang, NUR flache 'key: "value"'/'key: value'
    Zeilen (mechanisch, kein YAML-Parser noetig fuer dieses simple Schema)."""
    fm = {}
    body = raw
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            block = raw[3:end]
            body = raw[end + 4:].lstrip("\n")
            for ln in block.splitlines():
                m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$', ln.strip())
                if m:
                    val = m.group(2).strip()
                    if val.startswith('"') and val.endswith('"') and len(val) >= 2:
                        val = val[1:-1]
                    fm[m.group(1)] = val
    return fm, body

def build_iar_seiten():
    """de/ und en/ *.html unter IAR_SITE_ROOT. .txt-Geschwister sind
    Next.js-RSC-Flight-Payloads (kein Klartext, geprueft) und werden NICHT
    separat eingelesen -- sonst waere es dieselbe Seite zweimal. de/ und en/
    sind dieselbe Seite in zwei Sprachen -- werden NICHT als zwei Fakten
    gefuehrt, sondern per art='sprachpaar'-Kante verknuepft (siehe cmd)."""
    n = 0
    by_lang_relpath = {}
    for lang in ("de", "en"):
        root = os.path.join(IAR_SITE_ROOT, lang)
        if not os.path.isdir(root):
            continue
        for path in sorted(glob.glob(os.path.join(root, "**", "*.html"), recursive=True)):
            n += 1
            rel = os.path.relpath(path, root)  # z.B. "team.html", "research/ablating-stateful-agent.html"
            titel, beschreibung, jsonld, text = strip_html_to_text(path)
            autor, datum_text = None, None
            bm = _BYLINE_RE.search(text)
            if bm:
                autor, datum_text = bm.group(1).strip(), bm.group(2).strip()
            size = os.path.getsize(path)
            meta = {
                "titel": titel,
                "beschreibung": beschreibung,
                "sprache": lang,
                "text_zeichen": len(text),
            }
            if jsonld:
                meta["jsonld"] = jsonld
            if len(text) <= GROESSENGRENZE:
                meta["text"] = text
            else:
                meta["_hinweis"] = "Text >32KB, nicht vollstaendig gespeichert (FTS-Aufgabe)"
            mtime_iso = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc).isoformat()
            if autor:
                datum_wb, zq, von, vq = mtime_iso, "beleg-byline-mtime", autor, "beleg-byline"
                meta["byline_erkannt"] = f"{autor} · {datum_text}"
            else:
                datum_wb, zq, von, vq = mtime_iso, "mtime", None, None
            aid = "iar-" + lang + "-" + slugify(rel[:-5])
            by_lang_relpath.setdefault(rel, {})[lang] = aid
            yield {
                "id": aid, "art": "iar_seite", "titel": titel or rel,
                "quelle": path, "quell_hash": sha256_file(path), "datum": None,
                "metadaten": meta, "offene_fragen": [], "belegt": True, "duenn": 0,
                "projekt": "iar", "projekt_art": "eigen", "sphaere": "iar",
                "_zuletzt_bearbeitet": datum_wb, "_zeitquelle": zq,
                "_zuletzt_von": von, "_von_quelle": vq,
            }
    sys.stderr.write(f"[iar/seiten] html-dateien={n}\n")
    build_iar_seiten.paare = by_lang_relpath  # fuer den Aufrufer sichtbar

def build_iar_artikel_quellen():
    """articles/*.md -- eigene Markdown-Quellen mit YAML-Frontmatter,
    unabhaengig von den gerenderten research/news-Seiten (keine
    Aequivalenzpruefung durchgefuehrt -- daher als eigene Artikel gefuehrt,
    nicht mit research/news verschmolzen)."""
    root = os.path.join(IAR_SITE_ROOT, "articles")
    n = 0
    for path in sorted(glob.glob(os.path.join(root, "*.md"))):
        n += 1
        raw = open(path, encoding="utf-8", errors="replace").read()
        fm, body = parse_md_frontmatter(raw)
        titel = fm.get("title") or os.path.splitext(os.path.basename(path))[0]
        meta = dict(fm)
        if len(body) <= GROESSENGRENZE:
            meta["text"] = body
        else:
            meta["_hinweis"] = "Text >32KB, nicht vollstaendig gespeichert (FTS-Aufgabe)"
            meta["text_zeichen"] = len(body)
        mtime_iso = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc).isoformat()
        slug = fm.get("slug") or os.path.splitext(os.path.basename(path))[0]
        yield {
            "id": "iar-artikel-" + slugify(slug), "art": "iar_artikel_quelle",
            "titel": titel, "quelle": path, "quell_hash": sha256_file(path), "datum": None,
            "metadaten": meta, "offene_fragen": [], "belegt": True, "duenn": 0,
            "projekt": "iar", "projekt_art": "eigen", "sphaere": "iar",
            "_zuletzt_bearbeitet": mtime_iso, "_zeitquelle": "mtime",
            "_zuletzt_von": None, "_von_quelle": None,
        }
    sys.stderr.write(f"[iar/artikel_quellen] md-dateien={n}\n")

def cmd_iar_einlesen():
    t0 = time.time()
    con = connect_db()
    ensure_schema(con)
    cur = con.cursor()

    seiten = list(build_iar_seiten())
    paare = getattr(build_iar_seiten, "paare", {})
    quellen = list(build_iar_artikel_quellen())
    alle = seiten + quellen

    ts = now_iso()
    carry_snapshot = load_carryforward_snapshot(cur)  # STOP-Level-Fix Teil (a) + Zwilling + dritter Fund (verfallen/protected)
    for a in alle:
        epistemic_class, status, scope, tags, konfidenz, logical_id, id_quelle = resolve_lift_fields(a["art"], a["metadaten"])
        herkunft_wert, _p, _pa, _s, verfallen_alt, protected_alt = carry_snapshot.get(
            a["id"], ("gemessen", None, None, None, 0, 0)
        )
        cur.execute(
            "INSERT OR REPLACE INTO artikel "
            "(id, art, titel, quelle, quell_hash, datum, metadaten, offene_fragen, belegt, erzeugt_am, "
            " duenn, zuletzt_bearbeitet, zeitquelle, wirt, zuletzt_von, von_quelle, "
            " logical_id, id_quelle, epistemic_class, status, scope, tags, konfidenz, "
            " projekt, projekt_art, sphaere, herkunft, verfallen, protected) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                a["id"], a["art"], a["titel"], a["quelle"], a["quell_hash"], a["datum"],
                json.dumps(a["metadaten"], ensure_ascii=False),
                json.dumps(a["offene_fragen"], ensure_ascii=False),
                1 if a["belegt"] else 0, ts, 1 if a.get("duenn") else 0,
                a["_zuletzt_bearbeitet"], a["_zeitquelle"], WIRT_KONSTANTE,
                a["_zuletzt_von"], a["_von_quelle"],
                logical_id, id_quelle, epistemic_class, status, scope, tags, konfidenz,
                a["projekt"], a["projekt_art"], a["sphaere"], herkunft_wert, verfallen_alt, protected_alt,
            ),
        )
        cur.execute(
            "INSERT OR REPLACE INTO artikel_sphaere (artikel_id, sphaere, beleg) VALUES (?,?,?)",
            (a["id"], "iar", "gesamte iar.frank.ink-Seite ist IAR-Sphaere per Definition"),
        )

    n_paare = 0
    paar_details = []
    for rel, langs in paare.items():
        if "de" in langs and "en" in langs:
            n_paare += 1
            # URGENT FIX 2026-08-15: siehe cmd_bauen -- ON CONFLICT DO UPDATE,
            # ruehrt konfidenz/erzeugt_am/zeitquelle/verfallen/protected nicht an.
            cur.execute(
                "INSERT INTO kante (von, nach, art, beleg) VALUES (?,?,?,?) "
                "ON CONFLICT(von, nach, art) DO UPDATE SET beleg=excluded.beleg",
                (langs["de"], langs["en"], "sprachpaar", f"gleicher relativer Pfad '{rel}' unter de/ und en/"),
            )
            paar_details.append(rel)
    con.commit()
    reapply_stats = reapply_owner_edits(cur)  # STOP-Level-Fix Teil (b)
    con.commit()

    n_articles = len(alle)
    stats = {
        "laufzeit_sekunden": round(time.time() - t0, 3),
        "herkunft_erhalten": reapply_stats,
        "iar_seiten_html": len(seiten),
        "iar_artikel_md": len(quellen),
        "iar_artikel_gesamt": n_articles,
        "de_en_paare_gematcht": n_paare,
        "de_en_paar_regel": "gleicher Pfad relativ zu de//en/ (z.B. 'team.html', 'research/ablating-stateful-agent.html') -- eine Seite, zwei Sprachen, verknuepft per kante.art='sprachpaar', NICHT als zwei Artikel gefuehrt",
        "bylines_erkannt": sum(1 for a in seiten if a["_von_quelle"] == "beleg-byline"),
        "bewusst_nicht_eingelesen": {
            "*.txt unter de/en (RSC-Flight-Payload, kein Klartext -- geprueft an de/team.txt)": True,
            "_next/ (JS/CSS-Build-Artefakte)": True,
            "*.jpg/*.png/*.webp/*.svg (Bilder, ~mehrere MB)": True,
            "papers/*.pdf (nicht gelesen, nur Bild-/Binaerdatei-Klasse)": True,
            "de.html/de.txt/en.html/en.txt/index.html/index.txt/llms.txt/llms-full.txt (Seiten-weite Aggregat-Dumps, ueberlappen inhaltlich vollstaendig mit den bereits pro Seite eingelesenen Artikeln -- sonst gleicher Fakt doppelt getragen)": True,
            "404.html/robots.txt/sitemap.xml (Infrastruktur, kein Inhalt)": True,
        },
    }
    con.close()
    print(json.dumps(stats, ensure_ascii=False, indent=2, default=str))

# ---------------------------------------------------------------- Stufe 4: projekt/projekt_art/sphaere fuellen

def cmd_projekt_sphaere():
    t0 = time.time()
    con = connect_db()
    ensure_schema(con)
    cur = con.cursor()

    art_map = compute_projekt_art_map()
    t_map = time.time()

    cur.execute("SELECT id, quelle, art FROM artikel")
    rows = cur.fetchall()

    projekt_counts = {}
    projekt_art_counts = {}
    sphaere_counts = {}
    n_unplaceable = 0
    unplaceable_samples = []
    n_sphaere_null = 0
    n_multi_sphere_capable = 0

    for aid, quelle, art in rows:
        projekt = derive_projekt(quelle)
        if projekt is None:
            n_unplaceable += 1
            if len(unplaceable_samples) < 10:
                unplaceable_samples.append({"id": aid, "quelle": quelle})
            cur.execute("UPDATE artikel SET projekt=NULL, projekt_art=NULL WHERE id=?", (aid,))
            continue
        projekt_counts[projekt] = projekt_counts.get(projekt, 0) + 1
        p_art, p_begruendung = art_map.get(projekt, ("unbekannt", "Projekt hat keinen Klon unter /var/lib/clay/klone und keine Sonderregel -- keine Evidenz vorhanden"))
        projekt_art_counts[p_art] = projekt_art_counts.get(p_art, 0) + 1

        sphaere, beleg = decide_sphaere(projekt, quelle)
        if sphaere:
            sphaere_counts[sphaere] = sphaere_counts.get(sphaere, 0) + 1
        else:
            n_sphaere_null += 1

        cur.execute(
            "UPDATE artikel SET projekt=?, projekt_art=?, sphaere=? WHERE id=?",
            (projekt, p_art, sphaere, aid),
        )
        if sphaere:
            cur.execute(
                "INSERT OR REPLACE INTO artikel_sphaere (artikel_id, sphaere, beleg) VALUES (?,?,?)",
                (aid, sphaere, beleg),
            )
    con.commit()
    t_update = time.time()

    cur.execute("SELECT artikel_id, COUNT(*) c FROM artikel_sphaere GROUP BY artikel_id HAVING c > 1 ORDER BY c DESC LIMIT 5")
    multi = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM (SELECT artikel_id FROM artikel_sphaere GROUP BY artikel_id HAVING COUNT(*) > 1)")
    n_multi = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM artikel WHERE projekt IS NOT NULL")
    n_projekt_filled = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM artikel")
    n_total = cur.fetchone()[0]

    stats = {
        "laufzeit_sekunden": round(time.time() - t0, 3),
        "laufzeit_klon_messung_sekunden": round(t_map - t0, 3),
        "laufzeit_update_sekunden": round(t_update - t_map, 3),
        "artikel_gesamt": n_total,
        "projekt_fuellgrad": {"gefuellt": n_projekt_filled, "nicht_platzierbar": n_unplaceable, "quote": round(n_projekt_filled / n_total, 4) if n_total else None},
        "nicht_platzierbar_beispiele": unplaceable_samples,
        "projekt_verteilung": projekt_counts,
        "projekt_art_regeln": art_map,
        "projekt_art_verteilung": projekt_art_counts,
        "sphaere_verteilung": sphaere_counts,
        "sphaere_NULL_anzahl": n_sphaere_null,
        "sphaere_fuellgrad_quote": round((n_total - n_sphaere_null) / n_total, 4) if n_total else None,
        "artikel_in_mehr_als_einer_sphaere": {"anzahl": n_multi, "top5": multi},
    }
    con.close()
    print(json.dumps(stats, ensure_ascii=False, indent=2, default=str))

# ---------------------------------------------------------------- Stufe 5: die restlichen 20 Baeume + bau + strom
# Owner-Auftrag 2026-08-15: "clay-global-research-entity bereits erledigt",
# die restlichen 20 Klon-Repos unter baeume/ + der Rest von bau/ (ausser dem
# schon strukturiert eingelesenen protokoll.jsonl) + die 4 Stroeme unter
# /var/lib/clay/*.jsonl. Gleiche Regeln wie der letzte Sweep: duenn=1 ohne
# Metadaten, nie ein erfundenes Schema, keine Bodies >32KB, Binaerdateien nur
# Metadaten.

KNOWN_BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ico", ".bmp", ".tiff",
    ".pdf", ".zip", ".tar", ".gz", ".xz", ".bz2", ".7z", ".rar",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".mp3", ".mp4", ".mov", ".avi", ".webm", ".wav", ".flac", ".ogg",
    ".so", ".dylib", ".dll", ".exe", ".bin", ".o", ".a", ".class", ".jar", ".wasm",
    ".db", ".sqlite", ".sqlite3", ".pyc", ".pyo", ".ttc", ".icns",
}

def build_baum_sweep(projekt_slug, root, ausschluss=None, nur_diese_dateien=None):
    """Generischer Voll-Sweep eines beliebigen Baumes (Code-Repo, bau/,
    Strom-Verzeichnis). art='quelldatei' einheitlich -- Baum-Facettierung
    laeuft jetzt ueber die projekt-Spalte (Stufe 4), nicht mehr ueber art
    wie noch beim research_entity-Sweep. nur_diese_dateien: wenn gesetzt,
    KEIN rekursiver Verzeichnis-Walk (z.B. fuer /var/lib/clay, das auch
    wiki.db/klone/karte enthaelt) -- nur exakt diese absoluten Pfade."""
    ausschluss = ausschluss or set()
    n = n_thin = n_oversize = n_binary = 0
    kandidaten = sorted(nur_diese_dateien) if nur_diese_dateien is not None else \
        sorted(glob.glob(os.path.join(root, "**", "*"), recursive=True))
    for path in kandidaten:
        if not os.path.isfile(path):
            continue
        if f"{os.sep}.git{os.sep}" in path or path.endswith(f"{os.sep}.git"):
            continue
        if path in ausschluss:
            continue
        n += 1
        ext = os.path.splitext(path)[1].lower()
        size = os.path.getsize(path)
        oversize = size > GROESSENGRENZE
        is_bin = ext in KNOWN_BINARY_EXT
        meta = {}
        titel = os.path.basename(path)
        duenn = 1
        if oversize or is_bin:
            if is_bin:
                n_binary += 1
            if oversize:
                n_oversize += 1
            meta = {"_hinweis": "Binaer oder >32KB, kein Inhalt gespeichert (Metadaten-only)", "_bytes": size}
        elif ext == ".json":
            try:
                d = json.load(open(path, encoding="utf-8"))
                if isinstance(d, dict):
                    meta = d
                    for k in ("title", "titel", "name", "run_id", "event_id",
                              "request_id", "receipt_id", "campaign_id",
                              "packet_id", "summary", "description"):
                        if d.get(k):
                            titel = str(d[k])[:300]
                            duenn = 0
                            break
                elif isinstance(d, list):
                    meta = {"_typ": "liste", "_laenge": len(d)}
                else:
                    meta = {"_wert": d}
            except Exception:
                meta = {"_hinweis": "JSON-Parse fehlgeschlagen"}
        elif ext == ".jsonl":
            try:
                lines = [l for l in open(path, encoding="utf-8") if l.strip()]
                meta = {"_zeilen": len(lines)}
                if lines:
                    first = json.loads(lines[0])
                    if isinstance(first, dict):
                        meta["_erste_zeile"] = first
                        for k in ("title", "run_id", "claim_id", "event_id"):
                            if first.get(k):
                                titel = str(first[k])[:300]
                                duenn = 0
                                break
            except Exception:
                meta = {"_hinweis": "JSONL-Parse fehlgeschlagen"}
        elif ext == ".md":
            raw = open(path, encoding="utf-8", errors="replace").read()
            h1_titel, hdr = _kv_header_from_md(raw)
            if h1_titel:
                titel = h1_titel
                duenn = 0
            if hdr:
                meta = hdr
                duenn = 0
        else:
            # Code/Konfiguration: keine Zweck-Erfindung (Owner-Ehrlichkeitsregel)
            pass
        offene = extract_open_questions(meta) if isinstance(meta, dict) else []
        if duenn:
            n_thin += 1
            offene.append({"feld": "quelle", "text": "kein strukturiertes Titel-/Metadatenfeld gefunden (mechanisch, kein Modellaufruf); Datei als duenn eingetragen"})
        rel = os.path.relpath(path, root)
        yield {
            "id": slugify(projekt_slug + "--" + rel),
            "art": "quelldatei", "titel": titel, "quelle": path,
            "quell_hash": sha256_file(path), "datum": None,
            "metadaten": meta, "offene_fragen": offene,
            "belegt": bool(meta) and not duenn, "duenn": duenn,
        }
    sys.stderr.write(f"[baum_sweep:{projekt_slug}] dateien={n} duenn={n_thin} oversize={n_oversize} binaer={n_binary}\n")

def cmd_baeume_sweep():
    t0 = time.time()
    con = connect_db()
    ensure_schema(con)
    cur = con.cursor()

    klone_map = load_klone_provenance()
    t_klone = time.time()

    ziele = []  # (projekt_slug, root, ausschluss, nur_diese_dateien)
    for repo in sorted(os.listdir(BAEUME_ROOT)):
        if repo == "clay-global-research-entity":
            continue  # Owner: "bereits erledigt", nicht anfassen
        repo_dir = os.path.join(BAEUME_ROOT, repo)
        if not os.path.isdir(repo_dir):
            continue  # LIESMICH.md, VERWEISE.json -- keine Baeume
        ziele.append((repo, repo_dir, set(), None))
    ziele.append(("clayverse-bau", os.path.dirname(PROTOKOLL), {PROTOKOLL}, None))
    # "strom": NUR die 4 genannten Dateien, NIE ein Walk von /var/lib/clay
    # selbst (enthaelt wiki.db, klone/, karte/ -- die duerfen nicht rein).
    strom_pfade = {os.path.join(STROM_ROOT, b) for b in STROM_DATEIEN if os.path.isfile(os.path.join(STROM_ROOT, b))}
    if strom_pfade:
        ziele.append(("clayverse-strom", STROM_ROOT, set(), strom_pfade))

    ts = now_iso()
    carry_snapshot = load_carryforward_snapshot(cur)  # STOP-Level-Fix Teil (a) + Zwilling + dritter Fund (verfallen/protected)
    art_map = compute_projekt_art_map()

    n_gesamt = 0
    pro_baum = {}
    for projekt_slug, root, ausschluss, nur_diese_dateien in ziele:
        n_baum = 0
        for a in build_baum_sweep(projekt_slug, root, ausschluss, nur_diese_dateien):
            herkunft_wert, _p, _pa, _s, verfallen_alt, protected_alt = carry_snapshot.get(
                a["id"], ("gemessen", None, None, None, 0, 0)
            )
            repo_key, datum, autor = resolve_via_klone(a["quelle"], klone_map)
            if datum:
                zq_wert, von_wert, vq_wert = "git", autor, ("git" if autor else None)
            else:
                try:
                    datum = datetime.fromtimestamp(os.path.getmtime(a["quelle"]), tz=timezone.utc).isoformat()
                    zq_wert = "mtime"
                except OSError:
                    datum = None
                    zq_wert = None
                von_wert, vq_wert = None, None
            projekt = derive_projekt(a["quelle"])
            p_art, _ = art_map.get(projekt, ("unbekannt", "keine Evidenz"))
            sphaere, sphaere_beleg = decide_sphaere(projekt, a["quelle"])
            epistemic_class, status, scope, tags, konfidenz, logical_id, id_quelle = resolve_lift_fields(a["art"], a["metadaten"])
            cur.execute(
                "INSERT OR REPLACE INTO artikel "
                "(id, art, titel, quelle, quell_hash, datum, metadaten, offene_fragen, belegt, erzeugt_am, "
                " duenn, zuletzt_bearbeitet, zeitquelle, wirt, zuletzt_von, von_quelle, "
                " logical_id, id_quelle, epistemic_class, status, scope, tags, konfidenz, herkunft, "
                " projekt, projekt_art, sphaere, verfallen, protected) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    a["id"], a["art"], a["titel"], a["quelle"], a["quell_hash"], a["datum"],
                    json.dumps(a["metadaten"], ensure_ascii=False),
                    json.dumps(a["offene_fragen"], ensure_ascii=False),
                    1 if a["belegt"] else 0, ts, 1 if a.get("duenn") else 0,
                    datum, zq_wert, WIRT_KONSTANTE, von_wert, vq_wert,
                    logical_id, id_quelle, epistemic_class, status, scope, tags, konfidenz,
                    herkunft_wert, projekt, p_art, sphaere, verfallen_alt, protected_alt,
                ),
            )
            if sphaere:
                cur.execute(
                    "INSERT OR REPLACE INTO artikel_sphaere (artikel_id, sphaere, beleg) VALUES (?,?,?)",
                    (a["id"], sphaere, sphaere_beleg),
                )
            n_baum += 1
            n_gesamt += 1
        pro_baum[projekt_slug] = n_baum
    con.commit()
    reapply_stats = reapply_owner_edits(cur)
    con.commit()

    t_insert = time.time()
    cur.execute("SELECT COUNT(*) FROM artikel")
    n_total = cur.fetchone()[0]
    cur.execute("SELECT MIN(zuletzt_bearbeitet), MAX(zuletzt_bearbeitet) FROM artikel WHERE zuletzt_bearbeitet IS NOT NULL")
    rng = cur.fetchone()
    cur.execute("SELECT COUNT(DISTINCT zuletzt_von) FROM artikel WHERE zuletzt_von IS NOT NULL")
    n_von = cur.fetchone()[0]
    db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0

    stats = {
        "laufzeit_sekunden": round(time.time() - t0, 3),
        "laufzeit_klone_git_log_pass_sekunden": round(t_klone - t0, 3),
        "laufzeit_sweep_und_insert_sekunden": round(t_insert - t_klone, 3),
        "herkunft_erhalten": reapply_stats,
        "artikel_neu_diese_sitzung": n_gesamt,
        "artikel_pro_baum": pro_baum,
        "artikel_gesamt_NACHHER": n_total,
        "zuletzt_bearbeitet_range_NACHHER": {"aeltestes": rng[0], "neuestes": rng[1]},
        "distinkte_zuletzt_von_NACHHER": n_von,
        "db_bytes_NACHHER": db_size,
    }
    con.close()
    print(json.dumps(stats, ensure_ascii=False, indent=2, default=str))

# ---------------------------------------------------------------- Stufe 5: taetigkeit-Abgleich (Vorhersage-Test)

def cmd_taetigkeit_abgleich():
    """Read-only auf taetigkeit. Vergleicht distinkte ziel_pfad-Werte gegen
    artikel.quelle -- die vom Owner vorab festgelegte Falsifizierbarkeits-
    Schwelle (250 von 5089, 5%) entscheidet BESTAETIGT/REFUTED."""
    t0 = time.time()
    con = connect_db()
    ensure_schema(con)  # legt u.a. idx_artikel_quelle an, falls noch nicht vorhanden
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM taetigkeit")
    n_taetigkeit = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT ziel_pfad) FROM taetigkeit")
    n_distinct = cur.fetchone()[0]
    cur.execute("""
        SELECT COUNT(DISTINCT t.ziel_pfad) FROM taetigkeit t
        WHERE EXISTS (SELECT 1 FROM artikel a WHERE a.quelle = t.ziel_pfad)
    """)
    n_matched = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM artikel")
    n_artikel = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM artikel a WHERE NOT EXISTS (SELECT 1 FROM kante k WHERE k.von=a.id OR k.nach=a.id)")
    n_orphan = cur.fetchone()[0]

    quote = n_matched / n_distinct if n_distinct else 0.0
    SCHWELLE_ANZAHL = 250
    SCHWELLE_QUOTE = 0.05
    bestaetigt = (n_matched >= SCHWELLE_ANZAHL) and (quote >= SCHWELLE_QUOTE)

    stats = {
        "laufzeit_sekunden": round(time.time() - t0, 3),
        "taetigkeit_zeilen": n_taetigkeit,
        "taetigkeit_distinkte_ziel_pfade": n_distinct,
        "davon_matched_auf_artikel_quelle": n_matched,
        "match_quote": round(quote, 4),
        "artikel_gesamt": n_artikel,
        "artikel_ohne_kante_orphans": n_orphan,
        "falsifizierbarkeits_schwelle": {"anzahl": SCHWELLE_ANZAHL, "quote": SCHWELLE_QUOTE},
        "urteil": "BESTAETIGT" if bestaetigt else "REFUTED",
    }
    con.close()
    print(json.dumps(stats, ensure_ascii=False, indent=2, default=str))

# ---------------------------------------------------------------- main

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "bauen":
        cmd_bauen()
    elif cmd == "stand":
        cmd_stand()
    elif cmd == "artikel":
        if len(sys.argv) < 3:
            print("usage: wiki.py artikel <id>")
            sys.exit(1)
        cmd_artikel(sys.argv[2])
    elif cmd == "provenienz_reparieren":
        cmd_provenienz_reparieren()
    elif cmd == "iar_einlesen":
        cmd_iar_einlesen()
    elif cmd == "projekt_sphaere":
        cmd_projekt_sphaere()
    elif cmd == "baeume_sweep":
        cmd_baeume_sweep()
    elif cmd == "taetigkeit_abgleich":
        cmd_taetigkeit_abgleich()
    else:
        print(f"unbekanntes Subcommand: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
