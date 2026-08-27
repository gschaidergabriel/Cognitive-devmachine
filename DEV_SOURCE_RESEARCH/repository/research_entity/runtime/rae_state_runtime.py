#!/usr/bin/env python3
"""Central runtime fabric for the persistent FRANK Global Research Entity (RAE).

Identity boundary:
- RAE is `frank-project-global-research-entity`.
- Claude Code / ChatGPT / later models are temporary research actor nodes.
- `frankv0.1` is a live pilot/reference Harness and research source, never RAE identity.

Authority boundary:
- Existing canonical RAE JSON/ledgers remain scientific truth/governance sources.
- This runtime provides one central operational UnifiedDB plus one derived ClayGraph.
- ClayGraph activation/association is never fact authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = ROOT / "research_entity/runtime"
STATE_DIR = ROOT / "research_entity/state"
UDB_PATH = STATE_DIR / "RAE_UNIFIED.sqlite"
GRAPH_PATH = STATE_DIR / "RAE_CLAYGRAPH.sqlite"
CANON = ROOT / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json"
BOOT = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
ACTORS = ROOT / "research_entity/global/RESEARCH_ACTOR_REGISTRY.json"
WORLD = ROOT / "research_entity/global/GLOBAL_RESEARCH_WORLD_MODEL.json"
SELF = ROOT / "research_entity/global/GLOBAL_RESEARCH_SELF_MODEL.json"
PROGRAM = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
CLAIMS = ROOT / "research_entity/ledgers/CLAIMS.jsonl"
CLAIM_STATUS = ROOT / "research_entity/ledgers/CLAIM_STATUS_EVENTS.jsonl"
ROOM_REGISTRY = ROOT / "research_entity/rooms/ROOM_REGISTRY.json"

ENTITY = "frank-project-global-research-entity"
PILOT_SOURCE = "gschaidergabriel/frankv0.1"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def uid(prefix: str) -> str:
    return f"{prefix}:{uuid.uuid4().hex}"


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


class RAEStateRuntime:
    def __init__(self, state_dir: Path | str | None = None, *, test_mode: bool = False):
        requested = Path(state_dir).resolve() if state_dir else STATE_DIR.resolve()
        if not test_mode and requested != STATE_DIR.resolve():
            raise RuntimeError(f"RAE central state is repository-owned: {STATE_DIR}")
        self.root = requested
        self.test_mode = test_mode
        self.root.mkdir(parents=True, exist_ok=True)
        self.u = sqlite3.connect(self.root / "RAE_UNIFIED.sqlite", timeout=10)
        self.g = sqlite3.connect(self.root / "RAE_CLAYGRAPH.sqlite", timeout=10)
        self.u.row_factory = sqlite3.Row
        self.g.row_factory = sqlite3.Row
        for c in (self.u, self.g):
            c.execute("PRAGMA foreign_keys=ON")
            c.execute("PRAGMA busy_timeout=10000")
            c.execute("PRAGMA journal_mode=WAL")
        self.u.executescript((RUNTIME_DIR / "RAE_UNIFIEDDB_SCHEMA.sql").read_text(encoding="utf-8"))
        self.g.executescript((RUNTIME_DIR / "RAE_CLAYGRAPH_SCHEMA.sql").read_text(encoding="utf-8"))
        self._bootstrap()
        self.materialize_repo_sources()

    def close(self) -> None:
        self.u.close(); self.g.close()

    def current_epoch(self) -> int:
        return int(self.u.execute("SELECT COALESCE(MAX(epoch),0) FROM state_epochs").fetchone()[0])

    def current_graph_epoch(self) -> int:
        return int(self.g.execute("SELECT COALESCE(MAX(graph_epoch),0) FROM graph_epochs").fetchone()[0])

    def integrity(self) -> dict[str, str]:
        return {
            "UnifiedDB": self.u.execute("PRAGMA integrity_check").fetchone()[0],
            "ClayGraph": self.g.execute("PRAGMA integrity_check").fetchone()[0],
        }

    def _bootstrap(self) -> None:
        ts = now()
        canon = read_json(CANON, {}) or {}
        boot = read_json(BOOT, {}) or {}
        meta = {
            "schema_version": "1.0",
            "entity_id": ENTITY,
            "entity_kind": "PERSISTENT_RESEARCH_ENTITY",
            "canonical_revision": str(canon.get("revision", "UNKNOWN")),
            "canonical_state_hash": str(canon.get("state_hash", "UNKNOWN")),
            "state_topology": "ONE_REPO_CENTRAL_RESEARCH_UNIFIEDDB_PLUS_DERIVED_CLAYGRAPH",
            "node_owned_databases": "FORBIDDEN",
            "claygraph_authority": "DERIVED_NEVER_FACT_AUTHORITY",
            "pilot_reference_harness": PILOT_SOURCE,
            "identity_boundary": "RAE_NOT_FRANK",
            "research_team_rule": str((boot.get("research_team") or {}).get("rule", "evidence first")),
        }
        self.u.executemany("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", meta.items())
        self.u.execute(
            "INSERT OR IGNORE INTO research_entities VALUES(?,?,?,?,?,?)",
            (ENTITY, "research_entity", "FRANK Global Research Entity", "ACTIVE", ts, ts),
        )
        if not self.u.execute("SELECT 1 FROM state_epochs LIMIT 1").fetchone():
            root_hash = sha_text(json.dumps({"entity": ENTITY, "canon": canon.get("state_hash")}, sort_keys=True))
            self.u.execute(
                "INSERT INTO state_epochs(epoch,parent_epoch,tx_id,root_hash,committed_at,writer_node) VALUES(0,NULL,NULL,?,?,?)",
                (root_hash, ts, "SYSTEM"),
            )
        if not self.g.execute("SELECT 1 FROM graph_epochs LIMIT 1").fetchone():
            self.g.execute("INSERT INTO graph_epochs VALUES(?,?,?,?,?)", (1, self.current_epoch(), "bootstrap", ts, "CURRENT"))
        self.g.executemany("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", {
            "schema_version": "1.0",
            "entity_id": ENTITY,
            "source_of_truth": "research_entity/state/RAE_UNIFIED.sqlite + canonical RAE ledgers",
            "authority": "NEVER_FACT_AUTHORITY",
        }.items())
        self.u.commit(); self.g.commit()

    def _upsert_world(self, key: str, payload: Any, epistemic: str, source: str, source_hash: str | None) -> None:
        ts = now()
        self.u.execute(
            """INSERT INTO world_state(world_key,payload_clay,epistemic_class,source_ref,source_hash,valid_from,valid_to,status,updated_at)
               VALUES(?,?,?,?,?,?,NULL,'CURRENT',?)
               ON CONFLICT(world_key) DO UPDATE SET payload_clay=excluded.payload_clay,epistemic_class=excluded.epistemic_class,
               source_ref=excluded.source_ref,source_hash=excluded.source_hash,status='CURRENT',updated_at=excluded.updated_at""",
            (key, json.dumps(payload, ensure_ascii=False, sort_keys=True), epistemic, source, source_hash, ts, ts),
        )

    def _upsert_self(self, key: str, payload: Any, evidence: str, source: str) -> None:
        ts = now()
        self.u.execute(
            """INSERT INTO self_state(self_key,payload_clay,evidence_class,source_ref,status,updated_at)
               VALUES(?,?,?,?, 'CURRENT', ?)
               ON CONFLICT(self_key) DO UPDATE SET payload_clay=excluded.payload_clay,evidence_class=excluded.evidence_class,
               source_ref=excluded.source_ref,status='CURRENT',updated_at=excluded.updated_at""",
            (key, json.dumps(payload, ensure_ascii=False, sort_keys=True), evidence, source, ts),
        )

    def materialize_repo_sources(self) -> None:
        """Materialize current RAE source files into central operational state.

        This is not a claim promotion path; provenance/status from canonical sources is preserved.
        """
        canon = read_json(CANON, {}) or {}
        world = read_json(WORLD, {}) or {}
        self_model = read_json(SELF, {}) or {}
        program = read_json(PROGRAM, {}) or {}
        self._upsert_world("canonical_frontier", {
            "architecture_frontier": canon.get("architecture_frontier", []),
            "active_experiment_ids": canon.get("active_experiment_ids", []),
            "active_hypothesis_ids": canon.get("active_hypothesis_ids", []),
            "critical_negative_result_ids": canon.get("critical_negative_result_ids", []),
            "open_contradiction_ids": canon.get("open_contradiction_ids", []),
        }, "CANONICAL_DERIVED", str(CANON.relative_to(ROOT)), sha_file(CANON))
        for k in ("realized", "open", "contradictions_resolved", "forbidden_inferences"):
            if k in world:
                self._upsert_world(f"research_world:{k}", world[k], "SOURCE_PRESERVED", str(WORLD.relative_to(ROOT)), sha_file(WORLD))
        for k, v in self_model.items():
            if k not in {"schema_version"}:
                self._upsert_self(f"research_self:{k}", v, "SELF_OBSERVATION_SOURCE", str(SELF.relative_to(ROOT)))
        self.u.execute(
            """INSERT INTO research_focus_state(focus_key,payload_clay,priority,confidence,source_ref,status,updated_at)
               VALUES('program',?,?,?,?, 'CURRENT', ?)
               ON CONFLICT(focus_key) DO UPDATE SET payload_clay=excluded.payload_clay,source_ref=excluded.source_ref,status='CURRENT',updated_at=excluded.updated_at""",
            (json.dumps({
                "current_stage": program.get("current_stage"),
                "current_stage_goal": program.get("current_stage_goal"),
                "stage_order": program.get("stage_order", []),
                "dynamic_targets": program.get("dynamic_targets", {}),
            }, ensure_ascii=False, sort_keys=True), 1.0, 1.0, str(PROGRAM.relative_to(ROOT)), now()),
        )

        statuses: dict[str, str] = {}
        for ev in read_jsonl(CLAIM_STATUS):
            if ev.get("claim_id"):
                statuses[ev["claim_id"]] = ev.get("to") or statuses.get(ev["claim_id"], "OPEN")
        for c in read_jsonl(CLAIMS):
            cid = c.get("claim_id")
            if not cid:
                continue
            self.u.execute(
                """INSERT INTO claim_refs(claim_id,status,scope,proposition,source_ref,updated_at) VALUES(?,?,?,?,?,?)
                   ON CONFLICT(claim_id) DO UPDATE SET status=excluded.status,scope=excluded.scope,proposition=excluded.proposition,
                   source_ref=excluded.source_ref,updated_at=excluded.updated_at""",
                (cid, statuses.get(cid, c.get("first_status", "OPEN")), c.get("scope"), c.get("proposition"), str(CLAIMS.relative_to(ROOT)), now()),
            )
        self._materialize_rooms()
        self.u.commit()
        self.project(reason="repo-materialization")

    def _materialize_rooms(self) -> None:
        reg = read_json(ROOM_REGISTRY, {}) or {}
        rooms = reg.get("rooms") or reg.get("registered_rooms") or []
        if isinstance(rooms, dict):
            room_ids = list(rooms.keys())
        else:
            room_ids = []
            for r in rooms:
                if isinstance(r, str): room_ids.append(r)
                elif isinstance(r, dict) and r.get("room_id"): room_ids.append(r["room_id"])
        for room_id in room_ids:
            p = ROOT / "research_entity/rooms/rooms" / room_id / "state/ROOM_STATE.json"
            state = read_json(p, {}) or {}
            workers = state.get("active_workers") or state.get("workers") or []
            self.u.execute(
                """INSERT INTO room_state_refs(room_id,room_state_ref,room_state_hash,active_worker_count,last_pulse_at,status)
                   VALUES(?,?,?,?,?,?) ON CONFLICT(room_id) DO UPDATE SET room_state_ref=excluded.room_state_ref,
                   room_state_hash=excluded.room_state_hash,active_worker_count=excluded.active_worker_count,last_pulse_at=excluded.last_pulse_at,status=excluded.status""",
                (room_id, str(p.relative_to(ROOT)), sha_file(p), len(workers) if isinstance(workers, list) else 0,
                 state.get("updated_at") or state.get("last_updated"), state.get("status", "INDEXED")),
            )

    def register_node(self, node_id: str, actor_id: str, provider: str, model: str, runtime_class: str, session_id: str | None = None) -> None:
        ts = now()
        registry = read_json(ACTORS, {}) or {}
        actor = next((a for a in registry.get("actors", []) if a.get("actor_id") == actor_id), {})
        authority = json.dumps({"role": actor.get("role"), "authority_scope": actor.get("authority_scope", []), "may_override_empirical_evidence": False}, ensure_ascii=False)
        self.u.execute(
            """INSERT INTO actor_nodes(node_id,actor_id,provider,model,runtime_class,lifecycle_state,session_id,capabilities_clay,authority_clay,joined_at,last_verified_at,session_epoch)
               VALUES(?,?,?,?,?,'ACTIVE_CURRENT_SESSION',?,'{}',?,?,?,1)
               ON CONFLICT(node_id) DO UPDATE SET actor_id=excluded.actor_id,provider=excluded.provider,model=excluded.model,
               runtime_class=excluded.runtime_class,lifecycle_state='ACTIVE_CURRENT_SESSION',session_id=excluded.session_id,
               authority_clay=excluded.authority_clay,last_verified_at=excluded.last_verified_at,session_epoch=actor_nodes.session_epoch+1""",
            (node_id, actor_id, provider, model, runtime_class, session_id, authority, ts, ts),
        )
        self.u.commit()

    def begin_cycle(self, text: str, node_id: str, actor_id: str, provider: str, model: str, event: str,
                    session_id: str | None = None, home_room: str | None = None, trigger: str | None = None) -> str:
        self.register_node(node_id, actor_id, provider, model, "interactive", session_id)
        cycle = uid("cycle")
        self.u.execute(
            "INSERT INTO prompt_cycles VALUES(?,?,?,?,?,NULL,'ACTIVE',?,?,NULL,NULL,?,?)",
            (cycle, node_id, actor_id, sha_text(text), now(), self.current_epoch(), self.current_graph_epoch(), home_room, trigger),
        )
        self.u.commit()
        return cycle

    def end_cycle(self, cycle: str, node_id: str) -> None:
        self.project(reason=f"cycle:{cycle}")
        self.u.execute(
            "UPDATE prompt_cycles SET ended_at=?,status='DONE',state_epoch_end=?,graph_epoch_end=? WHERE cycle_id=?",
            (now(), self.current_epoch(), self.current_graph_epoch(), cycle),
        )
        self.u.execute("UPDATE actor_nodes SET lifecycle_state='IDLE',last_verified_at=? WHERE node_id=?", (now(), node_id))
        self.u.commit()

    def record_injection(self, cycle: str | None, node_id: str, event: str, capsule: dict[str, Any]) -> str:
        text = json.dumps(capsule, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        iid = uid("inject")
        self.u.execute(
            "INSERT INTO state_injections VALUES(?,?,?,?,?,?,?,?,?)",
            (iid, cycle, node_id, event, sha_text(text), self.current_epoch(), self.current_graph_epoch(), text, now()),
        )
        self.u.commit(); return iid

    def record_query(self, cycle: str | None, node_id: str, kind: str, intent: str, planner: Any,
                     result_refs: Any, admissibility: Any) -> str:
        qid = uid("query")
        results = json.dumps(result_refs, ensure_ascii=False, sort_keys=True)
        self.u.execute(
            "INSERT INTO query_receipts VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (qid, cycle, node_id, kind, intent, self.current_epoch(), self.current_graph_epoch(),
             json.dumps(planner, ensure_ascii=False, sort_keys=True), results,
             json.dumps(admissibility, ensure_ascii=False, sort_keys=True), sha_text(results), now()),
        )
        self.u.commit(); return qid

    def project(self, reason: str) -> int:
        """Build an append-versioned derived research ClayGraph from current UnifiedDB state."""
        source_epoch = self.current_epoch()
        prev = self.current_graph_epoch()
        ge = prev + 1
        ts = now()
        self.g.execute("INSERT INTO graph_epochs VALUES(?,?,?,?,?)", (ge, source_epoch, reason, ts, "CURRENT"))

        nodes: list[tuple[str, str, str, Any, float, float, float | None, str | None, str]] = []
        nodes.append((ENTITY, "research_entity", "RAE", {"entity": ENTITY}, 1.0, 1.0, 1.0, str(CANON.relative_to(ROOT)), "CANONICAL_ENTITY"))
        for r in self.u.execute("SELECT world_key,payload_clay,epistemic_class,source_ref FROM world_state WHERE status='CURRENT'"):
            nodes.append((f"world:{r['world_key']}", "world_state", r["world_key"], r["payload_clay"], .72, .72, None, r["source_ref"], r["epistemic_class"]))
        for r in self.u.execute("SELECT self_key,payload_clay,evidence_class,source_ref FROM self_state WHERE status='CURRENT'"):
            nodes.append((f"self:{r['self_key']}", "self_state", r["self_key"], r["payload_clay"], .68, .65, None, r["source_ref"], r["evidence_class"]))
        for r in self.u.execute("SELECT claim_id,status,scope,proposition,source_ref FROM claim_refs"):
            activation = .55 if r["status"] in {"CURRENT", "OPEN"} else .25
            nodes.append((f"claim:{r['claim_id']}", "claim", r["claim_id"], {"status": r["status"], "scope": r["scope"], "proposition": r["proposition"]}, activation, activation, None, r["source_ref"], "CLAIM_STATUS_PRESERVED"))
        for r in self.u.execute("SELECT room_id,active_worker_count,last_pulse_at,status,room_state_ref FROM room_state_refs"):
            nodes.append((f"room:{r['room_id']}", "research_room", r["room_id"], {"active_workers": r["active_worker_count"], "last_pulse_at": r["last_pulse_at"], "status": r["status"]}, .6, .6, None, r["room_state_ref"], "COORDINATION_DERIVED"))
        for r in self.u.execute("SELECT node_id,actor_id,provider,model,lifecycle_state FROM actor_nodes"):
            nodes.append((f"actor_node:{r['node_id']}", "actor_node", r["actor_id"], dict(r), .75 if r["lifecycle_state"].startswith("ACTIVE") else .35, .55, None, None, "OBSERVED_RUNTIME"))
        for r in self.u.execute("SELECT case_id,failure_classes_clay,repair_target,status,confidence FROM misunderstanding_cases"):
            nodes.append((f"failure:{r['case_id']}", "misunderstanding_case", r["case_id"], dict(r), .85 if r["status"] != "CLOSED" else .3, .9, r["confidence"], None, "PILOT_EVIDENCE"))

        for logical_id, kind, label, payload, activation, salience, confidence, source_ref, authority in nodes:
            self.g.execute(
                "INSERT INTO graph_nodes VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (uid("gn"), logical_id, ge, kind, label,
                 payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, sort_keys=True),
                 activation, salience, confidence, source_ref, authority, "CURRENT", ts),
            )

        def edge(src: str, dst: str, relation: str, weight: float, provenance: dict[str, Any], causal: str | None = None):
            logical = sha_text(f"{src}|{relation}|{dst}")[:24]
            self.g.execute(
                "INSERT INTO graph_edges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (uid("ge"), logical, ge, src, dst, relation, weight, None,
                 json.dumps(provenance, ensure_ascii=False, sort_keys=True),
                 json.dumps({"task_admission": "QUERY_DEPENDENT", "fact_authority": False}), causal, "CURRENT", ts),
            )

        for r in self.u.execute("SELECT self_key FROM self_state WHERE status='CURRENT'"):
            edge(ENTITY, f"self:{r['self_key']}", "has_self_observation", .7, {"source": "self_state"})
        for r in self.u.execute("SELECT world_key FROM world_state WHERE status='CURRENT'"):
            edge(ENTITY, f"world:{r['world_key']}", "maintains_world_model", .7, {"source": "world_state"})
        for r in self.u.execute("SELECT room_id FROM room_state_refs"):
            edge(ENTITY, f"room:{r['room_id']}", "researches_in", .55, {"source": "room_state"})
        for r in self.u.execute("SELECT node_id FROM actor_nodes"):
            edge(f"actor_node:{r['node_id']}", ENTITY, "temporary_node_of", .95, {"identity_boundary": "node_not_entity"})
        for r in self.u.execute("SELECT case_id,repair_target FROM misunderstanding_cases"):
            edge(f"failure:{r['case_id']}", ENTITY, "observed_failure_of_reference_harness", .8, {"pilot": "Andreas"}, "DIAGNOSTIC")

        self.g.execute(
            "INSERT INTO graph_deltas VALUES(?,?,?,?,?,?,?,?,?,?)",
            (uid("delta"), prev, ge, json.dumps([n[0] for n in nodes]), "[]", "[]", "[]", "{}", source_epoch, reason, ts),
        )
        self.g.commit(); return ge

    def capsule(self, node_id: str, actor_id: str, cycle: str | None = None, event: str = "PROMPT") -> dict[str, Any]:
        canon = read_json(CANON, {}) or {}
        program = read_json(PROGRAM, {}) or {}
        active_nodes = [dict(r) for r in self.u.execute(
            "SELECT node_id,actor_id,provider,model,lifecycle_state,last_verified_at FROM actor_nodes ORDER BY last_verified_at DESC LIMIT 8"
        )]
        failures = [dict(r) for r in self.u.execute(
            "SELECT case_id,failure_classes_clay,repair_target,confidence,status FROM misunderstanding_cases WHERE status!='CLOSED' ORDER BY detected_at DESC LIMIT 6"
        )]
        world = [dict(r) for r in self.u.execute(
            "SELECT world_key,payload_clay,epistemic_class,source_ref FROM world_state WHERE status='CURRENT' ORDER BY world_key LIMIT 10"
        )]
        self_state = [dict(r) for r in self.u.execute(
            "SELECT self_key,payload_clay,evidence_class,source_ref FROM self_state WHERE status='CURRENT' ORDER BY self_key LIMIT 10"
        )]
        top_graph = [dict(r) for r in self.g.execute(
            "SELECT logical_id,node_kind,label,activation,salience,authority_class FROM v_latest_graph_nodes ORDER BY activation DESC,salience DESC LIMIT 14"
        )]
        return {
            "entity": {"id": ENTITY, "identity_rule": "persistent Research Entity; actor nodes are temporary; never become Frank"},
            "actor": actor_id,
            "node": node_id,
            "event": event,
            "cycle": cycle,
            "canonical": {"revision": canon.get("revision"), "state_hash": canon.get("state_hash"), "entity_version": canon.get("entity_version")},
            "epochs": {"unified": self.current_epoch(), "claygraph": self.current_graph_epoch()},
            "program": {"current_stage": program.get("current_stage"), "goal": program.get("current_stage_goal")},
            "reference_harness": {"repo": PILOT_SOURCE, "role": "live H1 baseline + longitudinal pilot evidence source", "pilot_user": "Andreas"},
            "active_nodes": active_nodes,
            "world_state": world,
            "self_state": self_state,
            "open_misunderstandings": failures,
            "claygraph_active": top_graph,
            "invariants": [
                "evidence outranks researcher rank",
                "Claude Code lead and ChatGPT secondary share one research state",
                "ClayGraph activation is never fact authority",
                "preserve negative results/conflicts/unknown/stale states",
                "H1 Reference Harness baseline is frankv0.1 until frozen replacement",
                "Andreas is longitudinal pilot user; personalize state, generalize architecture only with evidence",
                "screen live interactions for misunderstanding/error/success patterns and regressionize material failures",
            ],
        }

    def ingest_pilot_manifest(self, manifest: dict[str, Any]) -> dict[str, Any]:
        """Ingest a sanitized pilot telemetry manifest exported/reference-resolved from frankv0.1.

        Raw secrets/private payloads are not accepted into this operational table by design.
        """
        interaction_id = manifest.get("interaction_id") or uid("pilot")
        privacy = manifest.get("privacy_class", "SANITIZED_DERIVED")
        if privacy not in {"SANITIZED_DERIVED", "REDACTED", "SENSITIVE_REFERENCE_ONLY"}:
            raise ValueError("pilot manifest privacy_class must be minimized/reference-safe")
        self.u.execute(
            "INSERT OR REPLACE INTO pilot_interactions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (interaction_id, manifest.get("pilot_user_id", "founding-user-01"), PILOT_SOURCE,
             manifest["source_interaction_ref"], manifest.get("started_at"), manifest.get("ended_at"),
             json.dumps(manifest.get("provider_path", []), ensure_ascii=False), manifest.get("task_class"),
             manifest.get("outcome_class"), manifest.get("user_effort_score"), privacy, manifest.get("source_hash"),
             manifest.get("status", "INGESTED"), now()),
        )
        for ev in manifest.get("events", []):
            self.u.execute(
                "INSERT OR REPLACE INTO pilot_harness_events VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (ev.get("event_id") or uid("phe"), interaction_id, ev.get("event_time") or now(), ev.get("event_type", "UNKNOWN"),
                 ev.get("node_id"), ev.get("state_epoch"), ev.get("graph_epoch"), ev.get("event_ref"),
                 json.dumps(ev.get("payload", {}), ensure_ascii=False, sort_keys=True), privacy, now()),
            )
        for case in manifest.get("misunderstanding_cases", []):
            cid = case.get("case_id") or uid("case")
            self.u.execute(
                """INSERT OR REPLACE INTO misunderstanding_cases VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (cid, interaction_id, case.get("detected_at") or now(), json.dumps(case.get("failure_classes", [])),
                 case.get("user_correction_ref"), json.dumps(case.get("expected_or_intended"), ensure_ascii=False),
                 json.dumps(case.get("observed_behavior", {}), ensure_ascii=False), case.get("state_epoch_before"),
                 case.get("state_epoch_after"), case.get("graph_epoch"), json.dumps(case.get("node_path", [])),
                 json.dumps(case.get("query_receipts", [])), json.dumps(case.get("graph_refs", [])),
                 json.dumps(case.get("tool_effect_refs", [])), json.dumps(case.get("candidate_causes", []), ensure_ascii=False),
                 json.dumps(case.get("selected_cause"), ensure_ascii=False), case.get("confidence"), case.get("repair_target"),
                 case.get("regression_fixture_ref"), case.get("candidate_fix_ref"), case.get("shadow_result_ref"),
                 case.get("live_verification_ref"), case.get("promotion_scope"), case.get("status", "OPEN"), now()),
            )
        self.u.commit(); self.project(reason=f"pilot-ingest:{interaction_id}")
        return {"interaction_id": interaction_id, "events": len(manifest.get("events", [])), "cases": len(manifest.get("misunderstanding_cases", []))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state-dir")
    ap.add_argument("--test-mode", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("status")
    c = sub.add_parser("capsule")
    c.add_argument("--node", required=True); c.add_argument("--actor", required=True)
    c.add_argument("--provider", default="unknown"); c.add_argument("--model", default="unknown")
    c.add_argument("--event", default="PROMPT"); c.add_argument("--prompt", default=""); c.add_argument("--session-id")
    c.add_argument("--home-room"); c.add_argument("--trigger")
    i = sub.add_parser("ingest-pilot")
    i.add_argument("manifest")
    args = ap.parse_args()
    rt = RAEStateRuntime(args.state_dir, test_mode=args.test_mode)
    try:
        if args.cmd == "init":
            print(json.dumps({"ok": True, "integrity": rt.integrity(), "epoch": rt.current_epoch(), "graph_epoch": rt.current_graph_epoch()}, indent=2))
        elif args.cmd == "status":
            print(json.dumps({"entity": ENTITY, "integrity": rt.integrity(), "epoch": rt.current_epoch(), "graph_epoch": rt.current_graph_epoch(),
                              "nodes": [dict(r) for r in rt.u.execute("SELECT node_id,actor_id,lifecycle_state,last_verified_at FROM actor_nodes")],
                              "open_misunderstandings": rt.u.execute("SELECT COUNT(*) FROM v_open_misunderstandings").fetchone()[0]}, indent=2))
        elif args.cmd == "capsule":
            cycle = rt.begin_cycle(args.prompt, args.node, args.actor, args.provider, args.model, args.event, args.session_id, args.home_room, args.trigger)
            cap = rt.capsule(args.node, args.actor, cycle, args.event)
            rt.record_injection(cycle, args.node, args.event, cap)
            print(json.dumps(cap, ensure_ascii=False, indent=2))
        elif args.cmd == "ingest-pilot":
            manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
            print(json.dumps(rt.ingest_pilot_manifest(manifest), ensure_ascii=False, indent=2))
    finally:
        rt.close()


if __name__ == "__main__":
    main()
