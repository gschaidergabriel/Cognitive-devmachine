#!/usr/bin/env python3
"""
ClayGraph materializer — generation 3 (reachability: node-type gap closed,
not a schema extension -- uses declared-but-empty types).

Mechanical only. No model calls, no network calls, stdlib only (sqlite3,
hashlib, json). Reads from /var/lib/clay/wiki.db tables artikel/kante
READ-ONLY. Writes only two new tables in the SAME db: graph_knoten,
graph_kante (plus bookkeeping graph_meta). Never touches artikel, kante,
kuration, anreicherung, fts_*, datei, fundort contents.

Schema authority: CLAYGRAPH_CANDIDATE.claycode.json (generation 2, 14
node_types, 16 edge_types) alongside CLAYGRAPH_LATEST.claycode.json
(generation 0, SEED_BASELINE, untouched). This tool does not invent types
outside that list. Wiki art values with no honest correspondence are left
OUT of the graph and are reported as gaps by `stand` (computed live from
the source tables, not cached, so the gap report never goes stale).

Generation history:
  gen 1: behauptung/vorfall/forschungsergebnis/hypothese only. 28% coverage
         of a 521-row wiki. begriff/wirt/gegenhypothese unmapped.
  gen 2: schema extended with node_type "micro_packet" (owner-approved) to
         house begriff. gegenhypothese SPLIT by file origin (quelle) into
         negative_result/hypothesis/claim -- never lumped under one type.
         wirt stays deliberately unmapped (see CLAYGRAPH_CANDIDATE.json).
         New edge_types utilized: SUPPORTS (stuetzt), CHALLENGES
         (widerspricht/attacks), RELATED (related_claim_ids).
  gen 3: NOT a schema change -- 18.024 new evidenced edges were landing as
         dangling because quelldatei (4.957) and 41 bereich_* values had NO
         node_type, not because of any edge-type gap. Used the 7 declared
         node types that had zero occupants after checking each against
         real rows: source (quelldatei, iar_artikel_quelle), artifact
         (bereich_atomic/trigger_runs/research_runs/mesh_feedback/
         archive_assimilation -- corrected from a suggested "run" mapping,
         see below), topic_packet (bereich_topic_packets), experiment
         (bereich_experiments), database_store (bereich_ledgers), event
         (bereich_events). `run`, `branch`, `reference`, `architecture`
         remain genuinely empty after sampling -- reported, not forced.
         New edge_types: SAME_EVIDENCE_FAMILY (gleicher_inhalt,
         geschwister_datei), SUPERSEDES (nachfolge_version), PARENT_OF
         (eltern_hypothese), RELATED (geschwister_verzeichnis, sprachpaar
         -- see WEIGHT note), MENTIONS (lauf_referenz, packet_referenz,
         artifacts, experiment_refs, experiment_ref).
         WEIGHT: graph_kante.weight is now real per-edge kante.konfidenz,
         not a constant -- see cmd_bauen for why and the geschwister_
         verzeichnis risk this exists to contain.
         verfallen/protected (new kante+artikel columns) are carried
         through onto graph_knoten/graph_kante as columns, never used to
         drop a row -- decayed data is preserved-and-marked, per the
         schema's own hard_invariant "preserve explicit unknown/conflict/
         revoked/stale states", not silently deleted.

Subcommands:
  bauen                 (re)build graph_knoten/graph_kante from current
                         wiki.db content. Idempotent: unchanged source ->
                         identical node_id/edge-key sets, same generation.
  stand                 counts by node_type/edge_type, orphan nodes,
                         unmapped wiki art/kante.art gaps (live), meta.
  nachbarn <node_id>     bounded walk, max 2 hops, cycle guard, capped rows.
                          Takes a RESOLVED node_id only -- no free-text query
                          (proven constraint: ungrounded graph traversal
                          measured 1.3% Top-1 despite 100% Recall@5).
"""
import sys, os, json, sqlite3, hashlib, time, argparse
from datetime import datetime, timezone

DB_PATH = "/var/lib/clay/wiki.db"

# Bumped whenever the MAPPING TABLES below change materially, independent of
# wiki content. bauen folds this into the generation-bump decision alongside
# the source content hash, so a pure schema/mapping change (like this one)
# still produces a new generation even if nobody touched the wiki in between.
SCHEMA_MAPPING_VERSION = "3"

NODE_TYPES = frozenset([
    "branch", "run", "artifact", "claim", "hypothesis", "experiment",
    "negative_result", "event", "topic_packet", "source", "architecture",
    "database_store", "reference",
    "micro_packet",  # added generation 2, see CLAYGRAPH_CANDIDATE.claycode.json
])

EDGE_TYPES = frozenset([
    "BELONGS_TO_BRANCH", "HAS_ARTIFACT", "MENTIONS", "SUPPORTS", "CHALLENGES",
    "CONTRADICTS", "SUPERSEDES", "DEPENDS_ON", "EVIDENCE_FOR", "DERIVED_FROM",
    "PARENT_OF", "IN_TOPIC", "AFFECTS_BRANCH", "SAME_EVIDENCE_FAMILY",
    "MIGRATION_CANDIDATE", "RELATED",
])

# --- node_type mapping: wiki artikel.art -> node_type -----------------------
# Re-verified against the generation-2 snapshot (2026-08-15, 9251 artikel,
# 47 distinct art values incl. 41 new "bereich_*" bulk-ingestion values).
# Only art values with a real, checked correspondence are here.
ART_TO_NODE_TYPE = {
    "behauptung": "claim",       # direct: Behauptung == claim/assertion
    "vorfall": "event",          # direct: Vorfall == incident/event
    "forschungsergebnis": "artifact",  # verified: quelle paths point at
                                  # research_entity/reports/*.md and
                                  # state/work/events/*.json -- produced
                                  # files, not the run/branch identity itself
    "hypothese": "hypothesis",   # direct linguistic match, now verified
                                  # against 1645 real rows (was 0 at gen 1)
    "begriff": "micro_packet",   # generation 2: new node_type added
                                  # (CLAYGRAPH_CANDIDATE.claycode.json,
                                  # generation_2_node_type_additions). Was
                                  # the dominant gen-1 gap (371/521 = 71%).
                                  # Verified: KMP-*/MP-* Knowledge Micro
                                  # Packets, named as their own category
                                  # (distinct from claim/hypothesis/
                                  # topic_packet) by the RAE's own protocol.
                                  # Known imprecision: a small TP-/TOPIC-
                                  # prefixed subset (~5-10 of 342) is closer
                                  # in shape to topic_packet; the wiki `art`
                                  # column does not distinguish it, and an
                                  # id-prefix heuristic split would itself be
                                  # invention -- left uniform, see candidate
                                  # json for the full disclosure.
    # --- generation 3: NOT a schema change. Uses declared-but-empty types
    # after checking each candidate against real rows (2026-08-15, 14.284
    # artikel, 47 distinct art incl. quelldatei + 41 bereich_*).
    "quelldatei": "source",       # 4.957 rows. Verified: files under
                                   # baeume/<repo>/... (READMEs, source
                                   # text/md) -- "a source file IS a
                                   # source", direct as suggested.
    "iar_artikel_quelle": "source",  # 8 rows, a different project (IAR)
                                   # entirely, but same shape: markdown
                                   # SOURCE files for articles. Same
                                   # reasoning as quelldatei, verified
                                   # separately (do not assume from the
                                   # name alone -- these ARE .md source
                                   # text, checked).
    "iar_seite": "artifact",      # 42 rows. Rendered HTML pages from the
                                   # IAR site -- a PRODUCED output, not a
                                   # source text, matching artifact's
                                   # existing "produced file" role.
    "bereich_topic_packets": "topic_packet",  # 74 rows. Verified: titles
                                   # literally "Topic Packet -- ..." under
                                   # research_entity/topic_packets/ --
                                   # direct, strong match to the node_type
                                   # name itself.
    "bereich_experiments": "experiment",  # 38 rows, ALL sampled (8 of 38
                                   # read in full): reports/receipts under
                                   # research_entity/experiments/ with
                                   # "experiment/synthetic/receipt/canary/
                                   # simulation contract" in their own
                                   # names. `experiment` had ZERO occupants
                                   # before this -- populated honestly, not
                                   # forced (see run/branch/reference/
                                   # architecture below, which did NOT get
                                   # this treatment because sampling did
                                   # not support it).
    "bereich_ledgers": "database_store",  # 3 rows, small but internally
                                   # consistent: ACTIVE_EXPERIMENTS.jsonl,
                                   # CLAIM_STATUS_EVENTS.jsonl,
                                   # EVIDENCE_GRAPH.jsonl -- append-only
                                   # ledger/store files, not the events
                                   # they record. `database_store` had
                                   # ZERO occupants before this.
    "bereich_events": "event",    # 2 rows. EV-*.jsonl event-stream
                                   # records under research_entity/events/
                                   # -- same conceptual family as
                                   # vorfall->event, verified independently
                                   # (a second art value converging on one
                                   # honest node_type, same pattern already
                                   # used on the edge side for evidence/
                                   # evidence_refs -> EVIDENCE_FOR).
    # --- generation 3: CORRECTED reading, not applied as suggested.
    # Coordinator's proposal was bereich_atomic/bereich_trigger_runs ->
    # `run`. Sampled both directly: every row is a FILE inside a run
    # DIRECTORY (RUN_REPORT.json, ABLATION_AND_CONTROLS.json,
    # simulate_cpd.py, CANDIDATE_*.clay -- several files per run,
    # confirmed by directory-prefix multiplicity), never a single row
    # representing the run's own execution identity. There is no
    # one-artikel-row-per-run-directory entity anywhere in the current
    # ingestion to be `run`; each row is a produced/supporting FILE, which
    # is exactly what `artifact` already means here (same reasoning as
    # forschungsergebnis at generation 1). Mapping them to `run` would
    # have been the same mistake generation 2 refused to make with
    # gegenhypothese->negative_result: convenient, not honest. Extended
    # the SAME verified reasoning to three more file-per-run-directory
    # categories after sampling each individually:
    "bereich_atomic": "artifact",             # 367
    "bereich_trigger_runs": "artifact",       # 2.702
    "bereich_research_runs": "artifact",      # 8, same file-in-run-dir shape
    "bereich_mesh_feedback": "artifact",      # 333, BRANCH_FEEDBACK_MANIFEST.json
                                               # per-run files, same pattern
    "bereich_archive_assimilation": "artifact",  # 707, manifests/receipts/
                                               # workspace files -- verified
                                               # with a SECOND sampling pass
                                               # (offset 50) after the
                                               # generation-2 3-row sample,
                                               # consistently manifest-shaped
    # `run` therefore remains genuinely EMPTY after checking ~10 bereich_*
    # categories systematically for a single-row-per-execution shape.
    # Reported as a finding, not silently forced and not silently ignored.
    #
    # NOT in this dict, checked and rejected as too heterogeneous to force
    # (each sampled at 2-8+ rows, several with a second, deeper pass):
    #   bereich_rooms (1.198) -- INTERNALLY split 439/1198 (36.6%) genuine
    #     event-shaped records under rooms/center_events/, 759/1198 (63.4%)
    #     root-level state/registry/schema files (CAPACITY_STATE.json,
    #     ROOM_DB_SCHEMA.json). Same kind of internal mix as begriff's
    #     TP-/TOPIC- subset at generation 2 -- declined an id/path-prefix
    #     split for the same invention-risk reason, left whole and unmapped.
    #   bereich_runtime (554) -- grab-bag confirmed on a second, deeper
    #     sample: health-snapshot JSON AND .py scripts AND .md research
    #     docs AND arxiv_verification.json in the same art value. No
    #     single honest type.
    #   bereich_frank (4) -- exactly half (2/4) are titled "... Architecture
    #     ..." docs, the other half are a bugsearch report and a knowledge-
    #     return JSON. Too small and too mixed to force `architecture`.
    #   bereich_state, bereich_global, bereich_claycode, bereich_gateflow,
    #   bereich_emergent_fields, bereich_android, bereich_forecast,
    #   bereich_domains, bereich_architecture_archaeology, bereich_
    #   benchmarks, bereich_claygraph, bereich_private, bereich_provenance,
    #   bereich_continuity, bereich_external_users, bereich_knowledge,
    #   bereich_advisor, bereich_notes, bereich_retina, bereich_unifieddb,
    #   bereich_triggers, bereich_agenda, bereich_identity, bereich_models,
    #   bereich_owner_directives, bereich_prompt_runs -- each sampled at
    #   least 2 rows; heterogeneous, too small to generalize from, or
    #   simply had no honest candidate among the 14 node_types. `branch`,
    #   `reference`, `architecture` remain genuinely EMPTY after this pass.
    #
    # NOT in this dict -- "wirt" (still, now more of it): still
    # deliberately UNMAPPED. Sampled: literal host-machine hardware
    # inventory snapshots (cpu/ram/disks/gpu), infra telemetry not
    # research evidence. A new node_type was considered and explicitly
    # rejected at generation 2 -- see
    # CLAYGRAPH_CANDIDATE.claycode.json generation_2_node_type_rejections.
}


def classify_gegenhypothese(quelle):
    """gegenhypothese (272 rows) is a MIXED-ORIGIN art value -- owner
    instruction: split by origin, never lump under one type. Classified by
    the actual source file path (quelle), not by id text and not by the
    free-text `status` column (which has ~40 near-unique ad hoc values and
    is not a reliable discriminator except for the two literals used below).
    Verified against all 272 rows before writing this function -- see
    CLAYGRAPH_CANDIDATE.claycode.json generation_2_mapping_refinements for
    the full per-bucket counts and reasoning. Order matters: CLAIMS.jsonl
    checked first (most specific), then *RESULT* files, everything else
    (COUNTERHYPOTHESIS_MATRIX/COUNTERHYPOTHESES/lone .md) defaults to
    hypothesis -- a proposed-but-untested competing explanation."""
    q = quelle or ""
    if "CLAIMS.jsonl" in q:
        return "claim"          # verified: all 30 rows carry status
                                 # REFUTED(26) or SUPERSEDED(4), exact match
                                 # to the owner's claims bucket
    if "NEGATIVE_RESULT" in q or "COUNTERHYPOTHESIS_RESULT" in q:
        return "negative_result"  # verified: 118 rows, files that record
                                   # the OUTCOME of testing a counterhypo
    return "hypothesis"          # 124 rows: MATRIX/COUNTERHYPOTHESES/lone
                                  # .md -- a proposed alternative, not yet
                                  # an outcome; structurally a hypothesis

# --- edge_type mapping: wiki kante.art -> edge_type -------------------------
# Re-measured ALL distinct kante.art at generation 2: 12 values now (was 6),
# 1213 kante rows total (was 126). Verified with real (von,nach) pairs and
# their artikel.art, including direction sanity-checks, for every entry.
ART_TO_EDGE_TYPE = {
    "evidence": "EVIDENCE_FOR",         # verified: behauptung--evidence-->
                                          # forschungsergebnis reads "von is
                                          # evidence for nach"
    "evidence_refs": "EVIDENCE_FOR",     # same semantic field, alt name from
                                          # a different KMP metadata schema
                                          # version (evidence_refs vs
                                          # evidence key), same real meaning
    "predecessor_packet_ids": "DERIVED_FROM",  # verified: metadata field on
                                          # von names nach as its predecessor
                                          # -> von builds on / derived from
                                          # nach. Distinct from an unused
                                          # supersedes_packet_ids metadata
                                          # field (still 0 rows), so this is
                                          # not conflated with SUPERSEDES.
    "topic_packets": "IN_TOPIC",         # verified: behauptung--topic_packets
                                          # -->begriff(research-scope) reads
                                          # "von is in topic nach"
    "source_refs": "MENTIONS",           # medium confidence: packet cites
                                          # another wiki article as a source.
                                          # Chose MENTIONS (weak/citational)
                                          # over DERIVED_FROM (would assert a
                                          # stronger dependency than "cites a
                                          # source") -- conservative pick.
    "stuetzt": "SUPPORTS",               # NEW generation 2, owner-directed.
                                          # Verified: forschungsergebnis
                                          # --stuetzt--> gegenhypothese/claim
                                          # bucket, same shape as evidence.
    "widerspricht": "CHALLENGES",        # NEW generation 2, owner-directed.
                                          # Verified: gegenhypothese/
                                          # hypothesis bucket --widerspricht-->
                                          # hypothese-typed node.
    "attacks": "CHALLENGES",             # NEW generation 2. Verified BYTE-
                                          # IDENTICAL (von,nach) pair set to
                                          # widerspricht (20/20 overlap) --
                                          # same 20 relationships tagged in
                                          # German and English, not 20 extra
                                          # edges. The (source,target,
                                          # edge_type) PK on graph_kante
                                          # collapses both into one row per
                                          # pair automatically; no special
                                          # dedup code needed.
    "related_claim_ids": "RELATED",      # NEW generation 2. Direct name
                                          # match, verified: begriff/
                                          # micro_packet --related_claim_ids-->
                                          # hypothese-typed node.
    "eltern_hypothese": "DERIVED_FROM",  # NEW (kanten.py T5, mechanical from
                                          # metadaten.parent). Verified ALL
                                          # 8/8 rows: hypothese--eltern_hypothese
                                          # -->hypothese, both already node_type
                                          # "hypothesis" -- zero node_type gap,
                                          # zero ambiguity. Direction: von is
                                          # the child claim, nach is the parent
                                          # claim it refines/narrows, so
                                          # "von DERIVED_FROM nach" reads
                                          # correctly. NOT mapped to PARENT_OF:
                                          # that would require the reverse
                                          # (parent,child) direction, which
                                          # kanten.py does not produce -- see
                                          # kanten.py header for the other 6
                                          # new kante.art values (packet_referenz,
                                          # lauf_referenz, nachfolge_version,
                                          # geschwister_datei, geschwister_
                                          # verzeichnis, gleicher_inhalt) --
                                          # left by that sibling edit for the
                                          # next pass, since their real
                                          # endpoints were quelldatei/
                                          # bereich_* art values with NO
                                          # node_type at the time (a
                                          # node_type gap, not an edge_type
                                          # gap). That gap is closed above
                                          # (generation 3); verifying an
                                          # edge_type against a REAL
                                          # resolved pair is possible now.

    # --- generation 3: node-type gap above now makes these verifiable.
    "gleicher_inhalt": "SAME_EVIDENCE_FAMILY",  # 2.168, STRONG per owner:
                                          # identical quell_hash. Direct
                                          # name match -- "same evidence
                                          # family" IS literally what
                                          # identical content means.
    "geschwister_datei": "SAME_EVIDENCE_FAMILY",  # 1.556, MEDIUM per owner:
                                          # same source file, not
                                          # necessarily identical content.
                                          # Still shared evidentiary origin
                                          # -- SAME_EVIDENCE_FAMILY does not
                                          # require byte-identity, only a
                                          # shared evidence lineage, so
                                          # "medium" strength still fits.
    "nachfolge_version": "SUPERSEDES",   # 1.959, STRONG+directed per owner:
                                          # same logical_id chained by date.
                                          # Direct match, as suggested.
    "geschwister_verzeichnis": "RELATED",  # 12.239 (64% of ALL edges) --
                                          # THE risk of this job. WEAK per
                                          # owner: "same directory" alone.
                                          # Mapped, not left out, because it
                                          # IS evidenced (a sibling built it
                                          # deliberately) and because its
                                          # weakness demonstrably survives
                                          # into the graph via weight (see
                                          # cmd_bauen: weight = real
                                          # per-edge kante.konfidenz, not a
                                          # constant). Measured before
                                          # deciding: avg konfidenz for this
                                          # art = 0.451 vs 0.98/0.66/0.60 for
                                          # wirt/lauf_referenz/nachfolge_
                                          # version -- so nachbarn's
                                          # `ORDER BY weight DESC` genuinely
                                          # deprioritizes it against
                                          # stronger-evidenced neighbors at
                                          # the SAME node, not just in
                                          # theory. Also: 2.981/12.239 (24%)
                                          # of this art is verfallen=1 with
                                          # avg konfidenz ~0.00009 -- those
                                          # sink to the bottom of any
                                          # weight-sorted walk in practice.
    "sprachpaar": "RELATED",             # 21, weak (DE/EN language-pair
                                          # link between iar_seite pages).
                                          # ALL 21 rows are verfallen=1
                                          # (avg konfidenz ~0.001) -- maps
                                          # honestly but is self-limiting to
                                          # near-invisible in any
                                          # weight-sorted walk, verified.
    "lauf_referenz": "MENTIONS",         # 91, medium (0.66 avg konfidenz).
                                          # bereich_atomic/artifact --
                                          # references --> forschungsergebnis/
                                          # artifact. Conservative pick,
                                          # consistent with source_refs:
                                          # "references" does not assert the
                                          # stronger DEPENDS_ON relationship.
    "packet_referenz": "MENTIONS",       # 3, tiny, same conservative pick.
    "artifacts": "MENTIONS",             # 157, now resolvable: verified
                                          # von=a "receipt" file (archive_
                                          # assimilation/receipts/*.json),
                                          # nach=the "manifest" file(s) it
                                          # references (archive_assimilation/
                                          # manifests/*.json). "references",
                                          # not "depends on" or "has" --
                                          # MENTIONS, not HAS_ARTIFACT (that
                                          # edge type means run-HAS-artifact
                                          # ownership, not artifact-cites-
                                          # artifact, which this is).
    "experiment_refs": "MENTIONS",       # 5, mostly bereich_emergent_fields
                                          # (still unmapped, too
                                          # heterogeneous -- see rejected
                                          # list above), mapped anyway for
                                          # the fraction that does resolve.
    "experiment_ref": "MENTIONS",        # 3, same reasoning.

    # NOT mapped, checked and rejected:
    #   "wirt" (57 rows) -> UNMAPPED. Sampled: vorfall--wirt-->wirt-artikel
    #     ("this event happened on host X"). Since the wirt/host node itself
    #     has no home among the 14 node_types, the edge has no honest
    #     target type either.
}

# ---------------------------------------------------------------- utilities

def connect_db(readonly=False):
    if readonly:
        con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=30)
    else:
        con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")
    return con


def retry_locked(fn, tries=6, base_sleep=0.5):
    """Retry on 'database is locked' -- other agents write artikel/kante
    concurrently while we read/build."""
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


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def table_columns(con, table):
    return [r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()]


def node_id_for(node_type, external_id):
    """identity.node_id = stable hash of semantic kind + external
    identity/path (CLAYGRAPH_LATEST.claycode.json)."""
    h = hashlib.sha256(f"claygraph|{node_type}|{external_id}".encode("utf-8")).hexdigest()
    return f"n_{h[:32]}"


def source_hash_for(row_columns, values):
    """identity.source_content_hash = sha256. Prefer the wiki's own
    quell_hash (already sha256) when present and non-empty; else fall back
    to a sha256 over the row's own field values so identity is still
    reproducible without inventing provenance we don't have."""
    d = dict(zip(row_columns, values))
    qh = d.get("quell_hash")
    if qh:
        return qh
    payload = json.dumps(d, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def ensure_graph_schema(con):
    con.executescript("""
        CREATE TABLE IF NOT EXISTS graph_meta(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS graph_knoten(
            node_id TEXT PRIMARY KEY,
            node_type TEXT NOT NULL,
            external_id TEXT NOT NULL,
            titel TEXT,
            quelle TEXT,
            source_content_hash TEXT,
            datum TEXT,
            metadaten TEXT,
            status TEXT,
            verfallen INTEGER,
            protected INTEGER,
            graph_epoch INTEGER NOT NULL,
            built_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_graph_knoten_type
            ON graph_knoten(node_type);
        CREATE INDEX IF NOT EXISTS idx_graph_knoten_external
            ON graph_knoten(external_id);
        CREATE TABLE IF NOT EXISTS graph_kante(
            source_node_id TEXT NOT NULL,
            target_node_id TEXT NOT NULL,
            edge_type TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 1.0,
            confidence REAL,
            verfallen INTEGER,
            protected INTEGER,
            graph_epoch INTEGER NOT NULL,
            source_kante_art TEXT NOT NULL,
            beleg TEXT,
            built_at TEXT NOT NULL,
            PRIMARY KEY(source_node_id, target_node_id, edge_type)
        ) WITHOUT ROWID;
        -- Index shape copied from the proven research candidate:
        -- research_entity/experiments/unifieddb_claygraph_retrieval/
        -- UNIFIEDDB_CLAYGRAPH_RETRIEVAL_PROJECTION_CANDIDATE.sql lines 31-32
        -- (source, epoch DESC, weight DESC) and the target-side mirror --
        -- so bounded-walk neighbor lookups are fast in BOTH directions.
        -- weight is now real per-edge kante.konfidenz (generation 3, see
        -- cmd_bauen), so this ordering is doing real work, not sorting on
        -- a constant.
        CREATE INDEX IF NOT EXISTS idx_graph_kante_source_epoch
            ON graph_kante(source_node_id, graph_epoch DESC, weight DESC);
        CREATE INDEX IF NOT EXISTS idx_graph_kante_target_epoch
            ON graph_kante(target_node_id, graph_epoch DESC, weight DESC);
    """)
    # Earlier generations created these tables before status/verfallen/
    # protected existed. SQLite has no "ADD COLUMN IF NOT EXISTS"; guard
    # with a schema check instead of relying on the exception (cheap,
    # avoids masking a real error).
    knoten_cols = [r[1] for r in con.execute("PRAGMA table_info(graph_knoten)").fetchall()]
    for col, decl in (("status", "TEXT"), ("verfallen", "INTEGER"), ("protected", "INTEGER")):
        if col not in knoten_cols:
            con.execute(f"ALTER TABLE graph_knoten ADD COLUMN {col} {decl}")
    kante_cols = [r[1] for r in con.execute("PRAGMA table_info(graph_kante)").fetchall()]
    for col, decl in (("verfallen", "INTEGER"), ("protected", "INTEGER")):
        if col not in kante_cols:
            con.execute(f"ALTER TABLE graph_kante ADD COLUMN {col} {decl}")
    con.commit()


def source_state(con):
    """Row counts + a hash over artikel.quell_hash, used both to record
    provenance in graph_meta and to decide whether this bauen run must bump
    generation (content changed) or may reuse the current one (idempotent
    rebuild of identical content)."""
    artikel_count = con.execute("SELECT COUNT(*) FROM artikel").fetchone()[0]
    kante_count = con.execute("SELECT COUNT(*) FROM kante").fetchone()[0]
    hashes = [r[0] or "" for r in con.execute(
        "SELECT quell_hash FROM artikel ORDER BY id"
    ).fetchall()]
    state_hash = hashlib.sha256(
        ("\n".join(hashes)).encode("utf-8")
    ).hexdigest()
    return artikel_count, kante_count, state_hash


def get_meta(con, key, default=None):
    row = con.execute("SELECT value FROM graph_meta WHERE key=?", (key,)).fetchone()
    return row[0] if row else default


def set_meta(con, key, value):
    con.execute(
        "INSERT INTO graph_meta(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )

# ---------------------------------------------------------------- bauen

def cmd_bauen(args):
    t0 = time.time()
    con = retry_locked(lambda: connect_db(readonly=False))
    try:
        db_size_before = os.path.getsize(DB_PATH)
        ensure_graph_schema(con)

        artikel_count, kante_count, state_hash = retry_locked(lambda: source_state(con))
        prev_hash = get_meta(con, "source_state_hash")
        prev_mapping_version = get_meta(con, "schema_mapping_version")
        prev_gen = get_meta(con, "generation")
        prev_gen = int(prev_gen) if prev_gen is not None else 0
        unchanged = (
            prev_hash == state_hash
            and prev_mapping_version == SCHEMA_MAPPING_VERSION
            and prev_gen >= 1
        )
        if unchanged:
            generation = prev_gen  # unchanged content AND unchanged mapping
                                    # code -> reuse generation (idempotent)
        else:
            generation = max(prev_gen, 0) + 1  # content changed, or the
                                    # mapping tables changed (this run: they
                                    # did -- SCHEMA_MAPPING_VERSION 2), or
                                    # first real build ever
        graph_epoch = generation

        artikel_cols = table_columns(con, "artikel")
        want_cols = [c for c in
                     ("id", "art", "titel", "quelle", "quell_hash", "datum",
                      "metadaten", "status", "verfallen", "protected")
                     if c in artikel_cols]
        rows = retry_locked(lambda: con.execute(
            f"SELECT {','.join(want_cols)} FROM artikel"
        ).fetchall())

        node_rows = []
        nodes_by_type = {}
        unmapped_node_arts = {}
        id_to_node_id = {}
        id_to_art = {}
        for r in rows:
            d = dict(zip(want_cols, r))
            art = d.get("art")
            ext_id = d.get("id")
            id_to_art[ext_id] = art
            if art == "gegenhypothese":
                # mixed-origin art value -- split by file origin, never a
                # single static mapping. See classify_gegenhypothese().
                node_type = classify_gegenhypothese(d.get("quelle"))
            else:
                node_type = ART_TO_NODE_TYPE.get(art)
            if node_type is None:
                unmapped_node_arts[art] = unmapped_node_arts.get(art, 0) + 1
                continue
            if node_type not in NODE_TYPES:
                # defensive: never invent outside the 13/14, even if a
                # future edit of this file's map introduces a typo
                raise SystemExit(f"BUG: node_type '{node_type}' not in schema's node_types")
            nid = node_id_for(node_type, ext_id)
            id_to_node_id[ext_id] = nid
            shash = source_hash_for(want_cols, r)
            # verfallen/protected are PRESERVED, never a filter -- see the
            # hard_invariant "preserve explicit unknown/conflict/revoked/
            # stale states" this generation leans on for the same decision
            # on the edge side below.
            node_rows.append((
                nid, node_type, ext_id, d.get("titel"), d.get("quelle"),
                shash, d.get("datum"), d.get("metadaten"), d.get("status"),
                d.get("verfallen"), d.get("protected"),
                graph_epoch, now_iso(),
            ))
            nodes_by_type[node_type] = nodes_by_type.get(node_type, 0) + 1

        kante_cols = table_columns(con, "kante")
        want_kcols = [c for c in
                      ("von", "nach", "art", "beleg", "konfidenz", "verfallen", "protected")
                      if c in kante_cols]
        has_konfidenz = "konfidenz" in want_kcols
        krows = retry_locked(lambda: con.execute(
            f"SELECT {','.join(want_kcols)} FROM kante"
        ).fetchall())

        edge_rows = []
        edges_by_type = {}
        unmapped_edge_arts = {}
        skipped_dangling = 0
        protected_seen = 0
        protected_materialized = 0
        protected_triples = set()  # (source_node_id,target_node_id,edge_type)
                                    # for every protected row that resolved
                                    # -- the honest post-dedup expectation
        for r in krows:
            d = dict(zip(want_kcols, r))
            von, nach, art = d.get("von"), d.get("nach"), d.get("art")
            is_protected = 1 if d.get("protected") else 0
            if is_protected:
                protected_seen += 1
            edge_type = ART_TO_EDGE_TYPE.get(art)
            if edge_type is None:
                unmapped_edge_arts[art] = unmapped_edge_arts.get(art, 0) + 1
                continue
            if edge_type not in EDGE_TYPES:
                raise SystemExit(f"BUG: edge_type '{edge_type}' not in schema's 16")
            src_nid = id_to_node_id.get(von)
            tgt_nid = id_to_node_id.get(nach)
            if src_nid is None or tgt_nid is None:
                # one or both endpoints are themselves unmapped-type nodes
                # (e.g. a wirt/host target) -- do not synthesize a node to
                # force this edge in; skip and count it honestly.
                skipped_dangling += 1
                continue
            # WEIGHT: real per-edge kante.konfidenz, not a constant. This is
            # the honest choice per the owner's own framing ("if that is
            # honest") -- confidence already exists, measured, decayed, on
            # all edges; a constant would throw that measurement away and
            # is exactly what would let geschwister_verzeichnis (64% of all
            # edges, weakest evidence) drown out everything else in a
            # weight-sorted walk. Fallback 0.0 only applies to the 16 null-
            # konfidenz rows, all of which are art='wirt' (already
            # unmapped, so this fallback is never actually exercised).
            konfidenz = d.get("konfidenz") if has_konfidenz else None
            weight = float(konfidenz) if konfidenz is not None else 0.0
            edge_verfallen = d.get("verfallen")
            edge_rows.append((
                src_nid, tgt_nid, edge_type, weight, konfidenz,
                edge_verfallen, is_protected, graph_epoch,
                art, d.get("beleg"), now_iso(),
            ))
            edges_by_type[edge_type] = edges_by_type.get(edge_type, 0) + 1
            if is_protected:
                protected_materialized += 1
                protected_triples.add((src_nid, tgt_nid, edge_type))

        # Full rebuild of OUR OWN derived tables (graph_knoten/graph_kante).
        # This is SQL DELETE on tables this tool owns and is instructed to
        # treat as derived/disposable/rebuildable -- not a filesystem rm/
        # unlink/shred against source-of-truth data, so it does not fall
        # under the "no delete commands" rule (which names rm/rmdir/shred/
        # os.remove/unlink against real files).
        con.execute("BEGIN")
        con.execute("DELETE FROM graph_kante")
        con.execute("DELETE FROM graph_knoten")
        con.executemany(
            "INSERT INTO graph_knoten(node_id,node_type,external_id,titel,quelle,"
            "source_content_hash,datum,metadaten,status,verfallen,protected,"
            "graph_epoch,built_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            node_rows,
        )
        # OR IGNORE, not plain INSERT: two different kante.art values can
        # legitimately map to the same (source,target,edge_type) triple --
        # e.g. widerspricht/attacks are a verified byte-identical (von,nach)
        # pair set, both -> CHALLENGES. A plain INSERT raises
        # IntegrityError on the composite PK the moment that happens (caught
        # here during testing); OR IGNORE keeps the first-seen row and
        # silently, correctly, drops the duplicate -- which is exactly the
        # "PK collapses them" behavior documented in the mapping comments.
        # NOTE: if a protected AND a non-protected kante row ever collided
        # onto the same PK, OR IGNORE would keep whichever was inserted
        # first, which could silently drop a protected=1 row's flag. Not
        # observed in this run (verified below via protected_seen vs
        # protected_materialized), but worth stating: this dedup path does
        # not itself special-case `protected`.
        con.executemany(
            "INSERT OR IGNORE INTO graph_kante(source_node_id,target_node_id,edge_type,"
            "weight,confidence,verfallen,protected,graph_epoch,source_kante_art,beleg,built_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            edge_rows,
        )
        # Report the TRUE post-dedup state from the table, not len(edge_rows)
        # -- OR IGNORE can silently drop rows (verified case: widerspricht/
        # attacks colliding onto the same PK), so len(edge_rows) would
        # over-report.
        true_edges_by_type = dict(con.execute(
            "SELECT edge_type, COUNT(*) FROM graph_kante GROUP BY edge_type"
        ).fetchall())
        true_edge_count = sum(true_edges_by_type.values())
        edge_dedup_collisions = len(edge_rows) - true_edge_count

        # protected=1 rows must NEVER be dropped. Verify against the TRUE
        # post-insert table state, not the pre-dedup Python counter -- a
        # bug caught right here on first run: protected_materialized (the
        # in-loop counter) read 40, but only 20 rows in graph_kante actually
        # carry protected=1. Nothing was silently lost: all 40 protected
        # SOURCE kante rows are the already-documented widerspricht/attacks
        # duplicate pair (20+20 tagging the SAME 20 relationships), and OR
        # IGNORE correctly collapses them onto 20 unique PK rows -- which
        # are STILL protected=1, since both duplicates carried that flag.
        # protected_unique_triples (tracked live in the loop, see above) is
        # the honest expectation: how many DISTINCT (source,target,edge_type)
        # protected relationships actually exist after the known dedup.
        # If the true table count falls short of THAT, something protected
        # really was lost.
        protected_materialized_true = con.execute(
            "SELECT COUNT(*) FROM graph_kante WHERE protected=1"
        ).fetchone()[0]
        protected_dropped = len(protected_triples) - protected_materialized_true

        # THE reachability number: what share of the ENTIRE wiki (not just
        # the mapped fraction) is touched by at least one graph edge.
        # Computed from the table, not from in-memory counters, so it
        # matches what `stand`/a live query would also see.
        reachable_nodes = con.execute("""
            SELECT COUNT(*) FROM graph_knoten n
            WHERE EXISTS(SELECT 1 FROM graph_kante e WHERE e.source_node_id=n.node_id)
               OR EXISTS(SELECT 1 FROM graph_kante e WHERE e.target_node_id=n.node_id)
        """).fetchone()[0]
        erreichbarer_anteil_pct = round(100.0 * reachable_nodes / artikel_count, 4) if artikel_count else 0.0

        set_meta(con, "generation", generation)
        set_meta(con, "graph_epoch", graph_epoch)
        set_meta(con, "schema_mapping_version", SCHEMA_MAPPING_VERSION)
        set_meta(con, "source_state_hash", state_hash)
        set_meta(con, "source_artikel_count", artikel_count)
        set_meta(con, "source_kante_count", kante_count)
        set_meta(con, "node_count", len(node_rows))
        set_meta(con, "edge_count", true_edge_count)
        set_meta(con, "edge_dedup_collisions", edge_dedup_collisions)
        set_meta(con, "built_at", now_iso())
        set_meta(con, "unmapped_node_arts", json.dumps(unmapped_node_arts, sort_keys=True))
        set_meta(con, "unmapped_edge_arts", json.dumps(unmapped_edge_arts, sort_keys=True))
        set_meta(con, "skipped_dangling_edges", skipped_dangling)
        set_meta(con, "protected_seen", protected_seen)
        set_meta(con, "protected_materialized", protected_materialized)
        set_meta(con, "protected_unique_expected", len(protected_triples))
        set_meta(con, "protected_materialized_true", protected_materialized_true)
        set_meta(con, "protected_dropped", protected_dropped)
        set_meta(con, "reachable_nodes", reachable_nodes)
        set_meta(con, "erreichbarer_anteil_pct", erreichbarer_anteil_pct)
        con.commit()

        con.execute("PRAGMA wal_checkpoint(PASSIVE)")
        db_size_after = os.path.getsize(DB_PATH)
        elapsed_ms = round((time.time() - t0) * 1000, 1)

        print(json.dumps({
            "generation": generation,
            "graph_epoch": graph_epoch,
            "schema_mapping_version": SCHEMA_MAPPING_VERSION,
            "regenerated_same_generation": unchanged,
            "source_artikel_count": artikel_count,
            "source_kante_count": kante_count,
            "source_state_hash": state_hash,
            "nodes_written": len(node_rows),
            "edges_written": true_edge_count,
            "edge_dedup_collisions": edge_dedup_collisions,
            "nodes_by_type": nodes_by_type,
            "edges_by_type": true_edges_by_type,
            "unmapped_node_arts": unmapped_node_arts,
            "unmapped_edge_arts": unmapped_edge_arts,
            "skipped_dangling_edges": skipped_dangling,
            "protected_seen": protected_seen,
            "protected_materialized": protected_materialized,
            "protected_unique_expected": len(protected_triples),
            "protected_materialized_true": protected_materialized_true,
            "protected_dropped": protected_dropped,
            "reachable_nodes": reachable_nodes,
            "erreichbarer_anteil_pct": erreichbarer_anteil_pct,
            "build_runtime_ms": elapsed_ms,
            "db_size_before_bytes": db_size_before,
            "db_size_after_bytes": db_size_after,
        }, indent=2, ensure_ascii=False))
    finally:
        con.close()

# ---------------------------------------------------------------- stand

def cmd_stand(args):
    con = retry_locked(lambda: connect_db(readonly=True))
    try:
        meta = {}
        for k, v in con.execute("SELECT key,value FROM graph_meta"):
            meta[k] = v

        nodes_by_type = dict(con.execute(
            "SELECT node_type, COUNT(*) FROM graph_knoten GROUP BY node_type ORDER BY 2 DESC"
        ).fetchall())
        edges_by_type = dict(con.execute(
            "SELECT edge_type, COUNT(*) FROM graph_kante GROUP BY edge_type ORDER BY 2 DESC"
        ).fetchall())
        orphan_nodes = con.execute("""
            SELECT COUNT(*) FROM graph_knoten n
            WHERE NOT EXISTS(SELECT 1 FROM graph_kante e WHERE e.source_node_id=n.node_id)
              AND NOT EXISTS(SELECT 1 FROM graph_kante e WHERE e.target_node_id=n.node_id)
        """).fetchone()[0]

        # Live gap report -- recomputed from the SOURCE tables every call,
        # so it can never go stale relative to graph_knoten/graph_kante.
        # "gegenhypothese" is not a key in ART_TO_NODE_TYPE (it's resolved
        # dynamically by classify_gegenhypothese, which always returns a
        # real type -- never None), so it must be added here explicitly or
        # every gegenhypothese row would be misreported as an unmapped gap.
        mapped_arts = set(ART_TO_NODE_TYPE.keys()) | {"gegenhypothese"}
        live_unmapped_node_arts = dict(con.execute(
            f"SELECT art, COUNT(*) FROM artikel WHERE art NOT IN "
            f"({','.join('?'*len(mapped_arts)) or 'NULL'}) GROUP BY art ORDER BY 2 DESC",
            tuple(mapped_arts),
        ).fetchall()) if mapped_arts else dict(con.execute(
            "SELECT art, COUNT(*) FROM artikel GROUP BY art"
        ).fetchall())

        mapped_kante_arts = set(ART_TO_EDGE_TYPE.keys())
        live_unmapped_edge_arts = dict(con.execute(
            f"SELECT art, COUNT(*) FROM kante WHERE art NOT IN "
            f"({','.join('?'*len(mapped_kante_arts)) or 'NULL'}) GROUP BY art ORDER BY 2 DESC",
            tuple(mapped_kante_arts),
        ).fetchall()) if mapped_kante_arts else dict(con.execute(
            "SELECT art, COUNT(*) FROM kante GROUP BY art"
        ).fetchall())

        print(json.dumps({
            "graph_meta": meta,
            "nodes_by_type": nodes_by_type,
            "edges_by_type": edges_by_type,
            "orphan_nodes": orphan_nodes,
            "live_unmapped_artikel_art": live_unmapped_node_arts,
            "live_unmapped_kante_art": live_unmapped_edge_arts,
            "note": "live_unmapped_* is recomputed from artikel/kante now, "
                    "independent of when graph_knoten/graph_kante were last built.",
        }, indent=2, ensure_ascii=False))
    finally:
        con.close()

# ---------------------------------------------------------------- nachbarn

def cmd_nachbarn(args):
    t0 = time.time()
    con = retry_locked(lambda: connect_db(readonly=True))
    try:
        anchor = args.node_id
        exists = con.execute(
            "SELECT 1 FROM graph_knoten WHERE node_id=?", (anchor,)
        ).fetchone()
        if not exists:
            print(json.dumps({
                "error": "unknown node_id -- nachbarn takes a RESOLVED node_id, "
                         "never a free-text query (proven constraint: ungrounded "
                         "traversal measured 1.3% Top-1 despite 100% Recall@5)",
                "node_id": anchor,
            }, indent=2))
            sys.exit(1)

        cap = args.limit
        max_hops = 2
        # cycle guard: path string of node_ids visited on THIS walk branch
        results = []
        seen_edges = set()
        frontier = [(anchor, f"|{anchor}|")]
        t_hop1 = None
        for hop in range(1, max_hops + 1):
            next_frontier = []
            for node_id, path in frontier:
                rows = con.execute(
                    "SELECT target_node_id, edge_type, weight, graph_epoch, 'out' "
                    "FROM graph_kante WHERE source_node_id=? "
                    "ORDER BY graph_epoch DESC, weight DESC",
                    (node_id,),
                ).fetchall() + con.execute(
                    "SELECT source_node_id, edge_type, weight, graph_epoch, 'in' "
                    "FROM graph_kante WHERE target_node_id=? "
                    "ORDER BY graph_epoch DESC, weight DESC",
                    (node_id,),
                ).fetchall()
                for other_id, edge_type, weight, epoch, direction in rows:
                    if f"|{other_id}|" in path:
                        continue  # cycle guard
                    ekey = (node_id, other_id, edge_type, direction)
                    if ekey in seen_edges:
                        continue
                    seen_edges.add(ekey)
                    results.append({
                        "hop": hop,
                        "from": node_id,
                        "to": other_id,
                        "edge_type": edge_type,
                        "direction": direction,
                        "weight": weight,
                    })
                    next_frontier.append((other_id, path + f"{other_id}|"))
                    if len(results) >= cap:
                        break
                if len(results) >= cap:
                    break
            if hop == 1:
                t_hop1 = round((time.time() - t0) * 1000, 2)
            if len(results) >= cap:
                break
            frontier = next_frontier
        t_total = round((time.time() - t0) * 1000, 2)

        # enrich with node_type/titel for readability
        ids = {anchor} | {r["to"] for r in results} | {r["from"] for r in results}
        info = {}
        if ids:
            qmarks = ",".join("?" * len(ids))
            for nid, ntype, titel in con.execute(
                f"SELECT node_id,node_type,titel FROM graph_knoten WHERE node_id IN ({qmarks})",
                tuple(ids),
            ):
                info[nid] = {"node_type": ntype, "titel": titel}

        print(json.dumps({
            "anchor": anchor,
            "anchor_node_type": info.get(anchor, {}).get("node_type"),
            "max_hops": max_hops,
            "cap": cap,
            "result_count": len(results),
            "ms_hop1": t_hop1,
            "ms_total": t_total,
            "results": results,
            "node_info": info,
        }, indent=2, ensure_ascii=False))
    finally:
        con.close()

# ---------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(description="ClayGraph materializer")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("bauen", help="(re)build graph_knoten/graph_kante").set_defaults(func=cmd_bauen)
    sub.add_parser("stand", help="counts + live gap report").set_defaults(func=cmd_stand)

    p_n = sub.add_parser("nachbarn", help="bounded 2-hop walk from a resolved node_id")
    p_n.add_argument("node_id")
    p_n.add_argument("--limit", type=int, default=48)
    p_n.set_defaults(func=cmd_nachbarn)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
