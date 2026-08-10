from __future__ import annotations

"""Database Pulse rank-path V5.1: attested physical expression-index lifecycle.

V5 made rank-index maintenance two-phase and atomic. V5.1 closes a narrower continuity gap:
an index with the expected *name* is not sufficient evidence that it is the expected physical
accelerator. Compiled reads are admitted only when the current sqlite_schema definition,
rootpage and runtime capability fingerprint match the latest atomic maintenance attestation.

StateLedger remains semantic truth. This module controls performance routing only and grants no
truth, model, tool or effect authority. Any missing/drifted attestation falls back to the correct
NOT INDEXED score-before-LIMIT query and requests inter-Pulse rebuild/drop maintenance.
"""

from dataclasses import dataclass
import hashlib
import json
import platform
import sqlite3
import sys
from typing import Any, Iterable

from research_entity.harness.reference.state_ledger import StaleEpoch, h
from research_entity.runtime.database_pulse_rank_index_v3 import INDEX_NAME, REENTRY_BOOST, SCORE_EXPR
from research_entity.runtime.database_pulse_rank_path_v5 import (
    AdaptiveAuthoritativeRankPathV5,
    MAINTENANCE_LOG_TABLE,
    RankPhysicalStateStale,
)
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import (
    EpochReadLifetime,
    decide_compile_from_pulse_history,
)

IMPLEMENTATION_ID = "PULSE_ATTESTED_AUTHORITATIVE_RANK_PATH_V5_1"
AUTHORITY = "PHYSICAL_INDEX_MAINTENANCE_ONLY_NO_SEMANTIC_OR_EFFECT_AUTHORITY"


def _stable(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_sql(sql: str | None) -> str | None:
    if sql is None:
        return None
    return " ".join(sql.strip().rstrip(";").split())


def canonical_index_sql() -> str:
    return _normalize_sql(
        f"""CREATE INDEX {INDEX_NAME}
            ON state(
              {SCORE_EXPR} DESC,
              domain COLLATE BINARY,
              k COLLATE BINARY,
              semantic_hash COLLATE BINARY
            )
            WHERE status='CURRENT' AND epistemic='KNOWN'"""
    ) or ""


EXPECTED_INDEX_SQL = canonical_index_sql()
EXPECTED_INDEX_SQL_HASH = _sha(EXPECTED_INDEX_SQL)


@dataclass(frozen=True)
class PhysicalIndexIdentity:
    present: bool
    state: str
    sql_hash: str | None
    rootpage: int | None
    schema_version: int
    runtime_env_hash: str
    latest_receipt_id: str | None
    authority: str = "PHYSICAL_IDENTITY_OBSERVATION_ONLY"


@dataclass(frozen=True)
class AttestedRankLifecyclePlan:
    basis_epoch: int
    semantic_state_hash: str
    desired_mode: str
    maintenance_action: str
    physical_state: str
    actual_index_present: bool
    index_sql_hash: str | None
    index_rootpage: int | None
    schema_version: int
    runtime_env_hash: str
    actor: str
    policy_provenance_ref: str
    horizon_status: str
    horizon_reads_lower_bound: float
    compile_reason: str
    guarded_break_even_reads: float | None
    plan_hash: str
    authority: str = "PERFORMANCE_MAINTENANCE_PLAN_ONLY"


@dataclass(frozen=True)
class AttestedRankMaintenanceReceipt:
    basis_epoch: int
    action: str
    status: str
    physical_state_before: str
    physical_state_after: str
    index_present_before: bool
    index_present_after: bool
    index_sql_hash_before: str | None
    index_sql_hash_after: str | None
    index_rootpage_before: int | None
    index_rootpage_after: int | None
    schema_version_before: int
    schema_version_after: int
    semantic_state_hash_before: str
    semantic_state_hash_after: str
    trace_root_hash_before: str
    trace_root_hash_after: str
    runtime_env_hash: str
    actor: str
    policy_provenance_ref: str
    plan_hash: str
    receipt_id: str | None = None
    persisted: bool = False
    authority: str = AUTHORITY


@dataclass(frozen=True)
class AttestedRankSelection:
    basis_epoch: int
    semantic_state_hash: str
    candidate_refs: tuple[str, ...]
    focus_refs: tuple[str, ...]
    candidate_scores: tuple[float, ...]
    candidate_universe_count: int
    query_truncated: bool
    conflicts_present: int
    unknown_present: int
    selection_hash: str
    query_plan: tuple[str, ...]
    reentry_mode: str
    physical_read_mode: str
    desired_mode: str
    maintenance_action: str
    physical_state: str
    index_present: bool
    runtime_env_hash: str
    lifecycle_plan_hash: str
    authority: str = "CONTEXT_ONLY_PERFORMANCE_ROUTING_NO_EFFECT_AUTHORITY"


class AttestedAdaptiveAuthoritativeRankPathV5_1(AdaptiveAuthoritativeRankPathV5):
    """V5 rank path that treats physical acceleration as attested, revocable capability."""

    @staticmethod
    def _require_provenance(actor: str, policy_provenance_ref: str) -> tuple[str, str]:
        actor = actor.strip()
        policy_provenance_ref = policy_provenance_ref.strip()
        if not actor:
            raise ValueError("actor is required for physical maintenance provenance")
        if not policy_provenance_ref:
            raise ValueError("policy_provenance_ref is required for physical maintenance provenance")
        return actor, policy_provenance_ref

    def _runtime_env_payload(self) -> dict[str, str]:
        sqlite_source_id = str(self.con.execute("SELECT sqlite_source_id()").fetchone()[0])
        return {
            "sqlite_version": sqlite3.sqlite_version,
            "sqlite_source_id": sqlite_source_id,
            "platform_system": platform.system(),
            "platform_release": platform.release(),
            "platform_machine": platform.machine(),
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "byteorder": sys.byteorder,
        }

    def _runtime_env(self) -> tuple[str, str]:
        payload = self._runtime_env_payload()
        encoded = _stable(payload)
        return _sha(encoded), encoded

    def _schema_version(self) -> int:
        return int(self.con.execute("PRAGMA schema_version").fetchone()[0])

    def _raw_index_info(self) -> tuple[bool, str | None, int | None]:
        row = self.con.execute(
            "SELECT sql,rootpage FROM sqlite_schema WHERE type='index' AND name=?", (INDEX_NAME,)
        ).fetchone()
        if row is None:
            return False, None, None
        sql_hash = _sha(_normalize_sql(str(row[0])) or "")
        return True, sql_hash, int(row[1])

    def _log_columns(self) -> set[str]:
        if not self._maintenance_log_exists():
            return set()
        return {str(r[1]) for r in self.con.execute(f"PRAGMA table_info({MAINTENANCE_LOG_TABLE})")}

    def _latest_material_receipt(self) -> dict[str, Any] | None:
        cols = self._log_columns()
        required = {
            "receipt_id",
            "status",
            "index_present_after",
            "index_sql_hash_after",
            "index_rootpage_after",
            "runtime_env_hash",
        }
        if not required.issubset(cols):
            return None
        row = self.con.execute(f"SELECT * FROM {MAINTENANCE_LOG_TABLE} ORDER BY rowid DESC LIMIT 1").fetchone()
        return dict(row) if row is not None else None

    def physical_identity(self) -> PhysicalIndexIdentity:
        present, sql_hash, rootpage = self._raw_index_info()
        env_hash, _ = self._runtime_env()
        schema_version = self._schema_version()
        if not present:
            return PhysicalIndexIdentity(False, "ABSENT", None, None, schema_version, env_hash, None)
        latest = self._latest_material_receipt()
        if sql_hash != EXPECTED_INDEX_SQL_HASH:
            return PhysicalIndexIdentity(
                True, "DEFINITION_DRIFT", sql_hash, rootpage, schema_version, env_hash,
                str(latest["receipt_id"]) if latest else None,
            )
        if not latest:
            return PhysicalIndexIdentity(True, "UNATTESTED", sql_hash, rootpage, schema_version, env_hash, None)
        receipt_id = str(latest["receipt_id"])
        if latest.get("status") not in {"BUILT", "REBUILT"} or int(latest.get("index_present_after") or 0) != 1:
            return PhysicalIndexIdentity(True, "UNATTESTED", sql_hash, rootpage, schema_version, env_hash, receipt_id)
        if not latest.get("runtime_env_hash") or not latest.get("index_sql_hash_after"):
            return PhysicalIndexIdentity(True, "UNATTESTED", sql_hash, rootpage, schema_version, env_hash, receipt_id)
        if str(latest["runtime_env_hash"]) != env_hash:
            return PhysicalIndexIdentity(True, "RUNTIME_DRIFT", sql_hash, rootpage, schema_version, env_hash, receipt_id)
        if str(latest["index_sql_hash_after"]) != sql_hash or int(latest["index_rootpage_after"]) != int(rootpage):
            return PhysicalIndexIdentity(True, "PHYSICAL_DRIFT", sql_hash, rootpage, schema_version, env_hash, receipt_id)
        return PhysicalIndexIdentity(True, "ATTESTED", sql_hash, rootpage, schema_version, env_hash, receipt_id)

    def plan_lifecycle(
        self,
        *,
        basis_epoch: int,
        economics_without_horizon: CompileEconomics,
        pulse_history: Iterable[EpochReadLifetime],
        actor: str,
        policy_provenance_ref: str,
        **horizon_kwargs,
    ) -> AttestedRankLifecyclePlan:
        actor, policy_provenance_ref = self._require_provenance(actor, policy_provenance_ref)
        if basis_epoch != self.ledger.epoch:
            raise StaleEpoch(f"rank lifecycle basis {basis_epoch}!={self.ledger.epoch}")
        horizon, decision = decide_compile_from_pulse_history(
            economics_without_horizon, list(pulse_history), **horizon_kwargs
        )
        physical = self.physical_identity()
        desired = "COMPILED_INDEX" if decision.mode == "COMPILE" else "ONLINE"
        if desired == "COMPILED_INDEX":
            if not physical.present:
                action = "BUILD_INDEX"
            elif physical.state == "ATTESTED":
                action = "NONE"
            else:
                action = "REBUILD_INDEX"
        else:
            action = "DROP_INDEX" if physical.present else "NONE"
        body = {
            "basis_epoch": basis_epoch,
            "semantic_state_hash": self.ledger.semantic_state_hash,
            "desired_mode": desired,
            "maintenance_action": action,
            "physical_state": physical.state,
            "actual_index_present": physical.present,
            "index_sql_hash": physical.sql_hash,
            "index_rootpage": physical.rootpage,
            "schema_version": physical.schema_version,
            "runtime_env_hash": physical.runtime_env_hash,
            "actor": actor,
            "policy_provenance_ref": policy_provenance_ref,
            "horizon_status": horizon.status,
            "horizon_reads_lower_bound": horizon.expected_reads_lower_bound,
            "compile_reason": decision.reason,
            "guarded_break_even_reads": decision.guarded_break_even_reads,
        }
        return AttestedRankLifecyclePlan(
            basis_epoch=basis_epoch,
            semantic_state_hash=self.ledger.semantic_state_hash,
            desired_mode=desired,
            maintenance_action=action,
            physical_state=physical.state,
            actual_index_present=physical.present,
            index_sql_hash=physical.sql_hash,
            index_rootpage=physical.rootpage,
            schema_version=physical.schema_version,
            runtime_env_hash=physical.runtime_env_hash,
            actor=actor,
            policy_provenance_ref=policy_provenance_ref,
            horizon_status=horizon.status,
            horizon_reads_lower_bound=horizon.expected_reads_lower_bound,
            compile_reason=decision.reason,
            guarded_break_even_reads=decision.guarded_break_even_reads,
            plan_hash=h(body),
        )

    def _ensure_attestation_log_no_commit(self) -> None:
        self._create_maintenance_log_no_commit()
        wanted = {
            "actor": "TEXT",
            "policy_provenance_ref": "TEXT",
            "physical_state_before": "TEXT",
            "physical_state_after": "TEXT",
            "index_sql_hash_before": "TEXT",
            "index_sql_hash_after": "TEXT",
            "index_rootpage_before": "INTEGER",
            "index_rootpage_after": "INTEGER",
            "schema_version_before": "INTEGER",
            "schema_version_after": "INTEGER",
            "sqlite_version": "TEXT",
            "sqlite_source_id": "TEXT",
            "runtime_env_hash": "TEXT",
            "runtime_env_json": "TEXT",
        }
        existing = self._log_columns()
        for name, typ in wanted.items():
            if name not in existing:
                self.con.execute(f"ALTER TABLE {MAINTENANCE_LOG_TABLE} ADD COLUMN {name} {typ}")

    def _create_canonical_index_no_commit(self) -> None:
        self.con.execute(EXPECTED_INDEX_SQL)

    def _persist_receipt_no_commit(self, values: dict[str, Any]) -> None:
        columns = list(values)
        marks = ",".join("?" for _ in columns)
        self.con.execute(
            f"INSERT INTO {MAINTENANCE_LOG_TABLE}({','.join(columns)}) VALUES({marks})",
            [values[c] for c in columns],
        )

    @staticmethod
    def _same_physical(a: PhysicalIndexIdentity, b: AttestedRankLifecyclePlan) -> bool:
        return (
            a.present == b.actual_index_present
            and a.state == b.physical_state
            and a.sql_hash == b.index_sql_hash
            and a.rootpage == b.index_rootpage
            and a.schema_version == b.schema_version
            and a.runtime_env_hash == b.runtime_env_hash
        )

    def apply_maintenance(self, plan: AttestedRankLifecyclePlan) -> AttestedRankMaintenanceReceipt:
        if plan.basis_epoch != self.ledger.epoch or plan.semantic_state_hash != self.ledger.semantic_state_hash:
            raise StaleEpoch("attested rank maintenance plan no longer matches authoritative ledger")
        observed = self.physical_identity()
        if not self._same_physical(observed, plan):
            raise RankPhysicalStateStale("attested rank maintenance physical precondition changed")
        state_before = self.ledger.semantic_state_hash
        trace_before = self.ledger.trace_root_hash
        action = plan.maintenance_action
        if action == "NONE":
            return AttestedRankMaintenanceReceipt(
                basis_epoch=plan.basis_epoch, action=action, status="NO_CHANGE",
                physical_state_before=observed.state, physical_state_after=observed.state,
                index_present_before=observed.present, index_present_after=observed.present,
                index_sql_hash_before=observed.sql_hash, index_sql_hash_after=observed.sql_hash,
                index_rootpage_before=observed.rootpage, index_rootpage_after=observed.rootpage,
                schema_version_before=observed.schema_version, schema_version_after=observed.schema_version,
                semantic_state_hash_before=state_before, semantic_state_hash_after=state_before,
                trace_root_hash_before=trace_before, trace_root_hash_after=trace_before,
                runtime_env_hash=observed.runtime_env_hash, actor=plan.actor,
                policy_provenance_ref=plan.policy_provenance_ref, plan_hash=plan.plan_hash,
            )
        if action not in {"BUILD_INDEX", "REBUILD_INDEX", "DROP_INDEX"}:
            raise ValueError(f"unsupported maintenance action: {action}")

        try:
            self.con.execute("BEGIN IMMEDIATE")
            if plan.basis_epoch != self.ledger.epoch or plan.semantic_state_hash != self.ledger.semantic_state_hash:
                raise StaleEpoch("attested rank maintenance plan became stale before physical commit")
            tx_observed = self.physical_identity()
            if not self._same_physical(tx_observed, plan):
                raise RankPhysicalStateStale("attested rank maintenance physical CAS failed")

            schema_before = tx_observed.schema_version
            self._ensure_attestation_log_no_commit()
            if action == "BUILD_INDEX":
                if tx_observed.present:
                    raise RankPhysicalStateStale("BUILD_INDEX requires absent index")
                self._create_canonical_index_no_commit()
                status = "BUILT"
            elif action == "REBUILD_INDEX":
                if not tx_observed.present:
                    raise RankPhysicalStateStale("REBUILD_INDEX requires present untrusted index")
                self._drop_index_no_commit()
                self._create_canonical_index_no_commit()
                status = "REBUILT"
            else:
                self._drop_index_no_commit()
                status = "DROPPED"

            present_after, sql_hash_after, rootpage_after = self._raw_index_info()
            schema_after = self._schema_version()
            env_hash, env_json = self._runtime_env()
            env = json.loads(env_json)
            state_after = self.ledger.semantic_state_hash
            trace_after = self.ledger.trace_root_hash
            if (state_before, trace_before) != (state_after, trace_after):
                raise AssertionError("attested physical maintenance mutated semantic/trace roots")
            if action in {"BUILD_INDEX", "REBUILD_INDEX"}:
                if not present_after or sql_hash_after != EXPECTED_INDEX_SQL_HASH:
                    raise AssertionError("canonical rank index definition was not established")
                physical_after = "ATTESTED"
            else:
                if present_after:
                    raise AssertionError("rank index drop did not remove index")
                physical_after = "ABSENT"

            receipt_body = {
                "basis_epoch": plan.basis_epoch, "action": action, "status": status,
                "physical_state_before": tx_observed.state, "physical_state_after": physical_after,
                "index_present_before": tx_observed.present, "index_present_after": present_after,
                "index_sql_hash_before": tx_observed.sql_hash, "index_sql_hash_after": sql_hash_after,
                "index_rootpage_before": tx_observed.rootpage, "index_rootpage_after": rootpage_after,
                "schema_version_before": schema_before, "schema_version_after": schema_after,
                "semantic_state_hash_before": state_before, "semantic_state_hash_after": state_after,
                "trace_root_hash_before": trace_before, "trace_root_hash_after": trace_after,
                "runtime_env_hash": env_hash, "actor": plan.actor,
                "policy_provenance_ref": plan.policy_provenance_ref,
                "plan_hash": plan.plan_hash, "authority": AUTHORITY,
            }
            receipt_id = h(receipt_body)
            values = {
                "receipt_id": receipt_id, "plan_hash": plan.plan_hash, "basis_epoch": plan.basis_epoch,
                "action": action, "status": status, "index_present_before": int(tx_observed.present),
                "index_present_after": int(present_after), "semantic_state_hash_before": state_before,
                "semantic_state_hash_after": state_after, "trace_root_hash_before": trace_before,
                "trace_root_hash_after": trace_after,
                "executed_at": self.con.execute("SELECT strftime('%Y-%m-%dT%H:%M:%fZ','now')").fetchone()[0],
                "authority": AUTHORITY, "actor": plan.actor,
                "policy_provenance_ref": plan.policy_provenance_ref,
                "physical_state_before": tx_observed.state, "physical_state_after": physical_after,
                "index_sql_hash_before": tx_observed.sql_hash, "index_sql_hash_after": sql_hash_after,
                "index_rootpage_before": tx_observed.rootpage, "index_rootpage_after": rootpage_after,
                "schema_version_before": schema_before, "schema_version_after": schema_after,
                "sqlite_version": env["sqlite_version"], "sqlite_source_id": env["sqlite_source_id"],
                "runtime_env_hash": env_hash, "runtime_env_json": env_json,
            }
            self._persist_receipt_no_commit(values)
            self.con.commit()
            return AttestedRankMaintenanceReceipt(
                basis_epoch=plan.basis_epoch, action=action, status=status,
                physical_state_before=tx_observed.state, physical_state_after=physical_after,
                index_present_before=tx_observed.present, index_present_after=present_after,
                index_sql_hash_before=tx_observed.sql_hash, index_sql_hash_after=sql_hash_after,
                index_rootpage_before=tx_observed.rootpage, index_rootpage_after=rootpage_after,
                schema_version_before=schema_before, schema_version_after=schema_after,
                semantic_state_hash_before=state_before, semantic_state_hash_after=state_after,
                trace_root_hash_before=trace_before, trace_root_hash_after=trace_after,
                runtime_env_hash=env_hash, actor=plan.actor,
                policy_provenance_ref=plan.policy_provenance_ref, plan_hash=plan.plan_hash,
                receipt_id=receipt_id, persisted=True,
            )
        except (StaleEpoch, RankPhysicalStateStale):
            self.con.rollback()
            raise
        except Exception:
            self.con.rollback()
            present_after, sql_hash_after, rootpage_after = self._raw_index_info()
            schema_after = self._schema_version()
            env_hash, _ = self._runtime_env()
            state_after = self.ledger.semantic_state_hash
            trace_after = self.ledger.trace_root_hash
            if (state_before, trace_before) != (state_after, trace_after):
                raise AssertionError("failed attested maintenance changed semantic/trace roots")
            return AttestedRankMaintenanceReceipt(
                basis_epoch=plan.basis_epoch, action=action,
                status="FAILED_RETRYABLE_PHYSICAL_MAINTENANCE",
                physical_state_before=observed.state, physical_state_after=self.physical_identity().state,
                index_present_before=observed.present, index_present_after=present_after,
                index_sql_hash_before=observed.sql_hash, index_sql_hash_after=sql_hash_after,
                index_rootpage_before=observed.rootpage, index_rootpage_after=rootpage_after,
                schema_version_before=observed.schema_version, schema_version_after=schema_after,
                semantic_state_hash_before=state_before, semantic_state_hash_after=state_after,
                trace_root_hash_before=trace_before, trace_root_hash_after=trace_after,
                runtime_env_hash=env_hash, actor=plan.actor,
                policy_provenance_ref=plan.policy_provenance_ref, plan_hash=plan.plan_hash,
                persisted=False,
            )

    def select(
        self,
        *,
        source_domains: tuple[str, ...],
        basis_epoch: int,
        max_candidates: int,
        max_focus: int,
        economics_without_horizon: CompileEconomics,
        pulse_history: Iterable[EpochReadLifetime],
        actor: str,
        policy_provenance_ref: str,
        reentry_mode: str = "NO_REENTRY",
        previous_focus_refs: tuple[str, ...] = (),
        shuffle_salt: str | None = None,
        **horizon_kwargs,
    ) -> AttestedRankSelection:
        if basis_epoch != self.ledger.epoch:
            raise StaleEpoch(f"attested rank selection basis {basis_epoch}!={self.ledger.epoch}")
        if not 1 <= max_candidates <= 512:
            raise ValueError("max_candidates out of bounds")
        if not 1 <= max_focus <= min(64, max_candidates):
            raise ValueError("max_focus out of bounds")
        mode = reentry_mode.upper()
        if mode not in {"TRUTHFUL", "NO_REENTRY", "SHUFFLED_CONTROL", "PROVENANCE_BROKEN_CONTROL"}:
            raise ValueError(mode)
        domains = self._domains(source_domains)
        lifecycle = self.plan_lifecycle(
            basis_epoch=basis_epoch, economics_without_horizon=economics_without_horizon,
            pulse_history=pulse_history, actor=actor, policy_provenance_ref=policy_provenance_ref,
            **horizon_kwargs,
        )
        physical = self.physical_identity()
        use_index = lifecycle.desired_mode == "COMPILED_INDEX" and physical.state == "ATTESTED"
        if use_index:
            read_mode = "COMPILED_ATTESTED_INDEX"
        elif lifecycle.desired_mode == "COMPILED_INDEX" and not physical.present:
            read_mode = "ONLINE_PENDING_COMPILE"
        elif lifecycle.desired_mode == "COMPILED_INDEX":
            read_mode = "ONLINE_PENDING_REBUILD"
        elif physical.present:
            read_mode = "ONLINE_PENDING_DECOMPILE"
        else:
            read_mode = "ONLINE"

        root_before = (self.ledger.epoch, self.ledger.semantic_state_hash, self.ledger.trace_root_hash)
        rows, query_plan = self._rows(domains, max_candidates, use_index=use_index)
        by_ref = {f"{r['domain']}:{r['k']}": r for r in rows}
        targets: set[str] = set()
        if mode == "TRUTHFUL":
            allowed = set(domains)
            for ref in previous_focus_refs:
                if ":" not in ref or ref.split(":", 1)[0] not in allowed:
                    continue
                row = self._row_by_ref(ref)
                if row is not None:
                    by_ref[ref] = row
                    targets.add(ref)
        elif mode == "SHUFFLED_CONTROL" and previous_focus_refs:
            salt = shuffle_salt or h({"control": "SHUFFLED", "basis": basis_epoch})
            ordered = sorted(by_ref, key=lambda ref: h({"salt": salt, "ref": ref}))
            targets = set(ordered[: min(len(previous_focus_refs), len(ordered))])

        ranked = []
        for ref, row in by_ref.items():
            score = float(row["score"]) + (REENTRY_BOOST if ref in targets else 0.0)
            ranked.append((score, ref, str(row["semantic_hash"])))
        ranked.sort(key=lambda x: (-x[0], x[1], x[2]))
        ranked = ranked[:max_candidates]
        candidates = tuple(x[1] for x in ranked)
        focus = candidates[:max_focus]
        scores = tuple(round(float(x[0]), 8) for x in ranked)
        universe = self._count(domains, "KNOWN")
        conflicts = self._count(domains, "CONFLICT")
        unknown = self._count(domains, "UNKNOWN")
        if root_before != (self.ledger.epoch, self.ledger.semantic_state_hash, self.ledger.trace_root_hash):
            raise AssertionError("attested rank read phase mutated ledger roots")
        body = {
            "implementation": IMPLEMENTATION_ID, "basis_epoch": basis_epoch,
            "semantic_state_hash": self.ledger.semantic_state_hash, "domains": list(domains),
            "candidate_refs": list(candidates), "candidate_scores": list(scores),
            "focus_refs": list(focus), "reentry_mode": mode, "physical_read_mode": read_mode,
            "desired_mode": lifecycle.desired_mode, "maintenance_action": lifecycle.maintenance_action,
            "physical_state": physical.state, "runtime_env_hash": physical.runtime_env_hash,
            "lifecycle_plan_hash": lifecycle.plan_hash,
        }
        return AttestedRankSelection(
            basis_epoch=basis_epoch, semantic_state_hash=self.ledger.semantic_state_hash,
            candidate_refs=candidates, focus_refs=focus, candidate_scores=scores,
            candidate_universe_count=universe, query_truncated=universe > len(candidates),
            conflicts_present=conflicts, unknown_present=unknown, selection_hash=h(body),
            query_plan=query_plan, reentry_mode=mode, physical_read_mode=read_mode,
            desired_mode=lifecycle.desired_mode, maintenance_action=lifecycle.maintenance_action,
            physical_state=physical.state, index_present=physical.present,
            runtime_env_hash=physical.runtime_env_hash, lifecycle_plan_hash=lifecycle.plan_hash,
        )
