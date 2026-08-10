from __future__ import annotations

"""Pulse rank V6.2: lexically robust, fail-closed expression-index attestation.

Parent V6 owns provenance-complete BUILD/DROP receipts. V6.2 decides only whether that
physical accelerator is safe to use for compiled cognition. A name match is insufficient.
The attestation binds the lexical sqlite_schema definition, rootpage, exact SQLite source/runtime
fingerprint and parent-V6 material receipt lineage. Any drift routes reads through the correct
NOT INDEXED score-before-LIMIT path until bounded maintenance succeeds.

V6.1 was self-falsified because whitespace-only SQL normalization could reject a correct parent
index. V6.2 removes insignificant whitespace and normalizes case only outside quoted literals or
quoted identifiers, preserving literal/identifier content. This is still intentionally stricter
than semantic SQL equivalence: ambiguous rewrites fail closed rather than being silently adopted.
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
from research_entity.runtime.database_pulse_rank_path_v5 import RankLifecyclePlan, RankPhysicalStateStale
from research_entity.runtime.database_pulse_rank_path_v6 import (
    AdaptiveAuthoritativeRankPathV6,
    NATIVE_PROVENANCE_STATUS,
)
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import (
    EpochReadLifetime,
    decide_compile_from_pulse_history,
)

IMPLEMENTATION_ID = "PULSE_PROVENANCE_PLUS_ATTESTED_RANK_PATH_V6_2"
ATTESTATION_TABLE = "pulse_rank_index_attestations_v6_2"
AUTHORITY = "PHYSICAL_ACCELERATOR_ATTESTATION_ONLY_NO_SEMANTIC_OR_EFFECT_AUTHORITY"


def _stable(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def lexical_sql_identity(sql: str | None) -> str | None:
    """Return a stable SQLite DDL identity without formatting false positives.

    Outside quoted regions, whitespace is insignificant and SQLite keywords/unquoted identifiers
    are case-insensitive, so whitespace is removed and text is case-folded. Inside single/double/
    backtick/bracket quoting, bytes are preserved (including doubled quote escapes). Comments are
    deliberately *not* normalized away: an unfamiliar definition remains a conservative drift.
    """
    if sql is None:
        return None
    source = sql.strip().rstrip(";")
    out: list[str] = []
    closing: str | None = None
    i = 0
    while i < len(source):
        ch = source[i]
        if closing is not None:
            out.append(ch)
            if ch == closing:
                # SQL quote escaping by doubling: ''  ""  ``  ]] .
                if i + 1 < len(source) and source[i + 1] == closing:
                    out.append(source[i + 1])
                    i += 2
                    continue
                closing = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            closing = ch
            out.append(ch)
        elif ch == "[":
            closing = "]"
            out.append(ch)
        elif ch.isspace():
            i += 1
            continue
        else:
            out.append(ch.casefold())
        i += 1
    return "".join(out)


CANONICAL_INDEX_SQL = f"""CREATE INDEX {INDEX_NAME}
    ON state(
      {SCORE_EXPR} DESC,
      domain COLLATE BINARY,
      k COLLATE BINARY,
      semantic_hash COLLATE BINARY
    )
    WHERE status='CURRENT' AND epistemic='KNOWN'"""
CANONICAL_INDEX_IDENTITY = lexical_sql_identity(CANONICAL_INDEX_SQL) or ""
CANONICAL_INDEX_IDENTITY_HASH = _sha(CANONICAL_INDEX_IDENTITY)


@dataclass(frozen=True)
class PhysicalIndexIdentityV62:
    present: bool
    state: str
    definition_hash: str | None
    rootpage: int | None
    runtime_env_hash: str
    latest_v6_receipt_id: str | None
    attestation_receipt_id: str | None
    authority: str = "PHYSICAL_ACCELERATOR_IDENTITY_ONLY"


@dataclass(frozen=True)
class RankLifecyclePlanV62:
    basis_epoch: int
    semantic_state_hash: str
    desired_mode: str
    maintenance_action: str
    physical_state: str
    actual_index_present: bool
    definition_hash: str | None
    rootpage: int | None
    runtime_env_hash: str
    actor: str
    policy_provenance_ref: str
    policy_decision_hash: str
    horizon_status: str
    horizon_reads_lower_bound: float
    compile_reason: str
    guarded_break_even_reads: float | None
    plan_hash: str
    authority: str = "PERFORMANCE_MAINTENANCE_PLAN_ONLY"


@dataclass(frozen=True)
class RankMaintenanceReceiptV62:
    basis_epoch: int
    action: str
    status: str
    physical_state_before: str
    physical_state_after: str
    parent_v6_receipt_ids: tuple[str, ...]
    attestation_receipt_id: str | None
    actor: str
    policy_provenance_ref: str
    policy_decision_hash: str
    plan_hash: str
    persisted: bool
    error_class: str | None = None
    authority: str = AUTHORITY


@dataclass(frozen=True)
class RankSelectionV62:
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
    lifecycle_plan_hash: str
    authority: str = "CONTEXT_ONLY_PERFORMANCE_ROUTING_NO_EFFECT_AUTHORITY"


class AdaptiveAuthoritativeRankPathV62Attested(AdaptiveAuthoritativeRankPathV6):
    def _runtime_payload(self) -> dict[str, str]:
        return {
            "sqlite_version": sqlite3.sqlite_version,
            "sqlite_source_id": str(self.con.execute("SELECT sqlite_source_id()").fetchone()[0]),
            "platform_system": platform.system(),
            "platform_release": platform.release(),
            "platform_machine": platform.machine(),
            "byteorder": sys.byteorder,
        }

    def _runtime(self) -> tuple[str, str]:
        raw = _stable(self._runtime_payload())
        return _sha(raw), raw

    def _raw_index(self) -> tuple[bool, str | None, int | None]:
        row = self.con.execute(
            "SELECT sql,rootpage FROM sqlite_schema WHERE type='index' AND name=?", (INDEX_NAME,)
        ).fetchone()
        if row is None:
            return False, None, None
        identity = lexical_sql_identity(str(row[0])) or ""
        return True, _sha(identity), int(row[1])

    def _attestation_table_exists(self) -> bool:
        return self.con.execute(
            "SELECT 1 FROM sqlite_schema WHERE type='table' AND name=?", (ATTESTATION_TABLE,)
        ).fetchone() is not None

    def _create_attestation_table_no_commit(self) -> None:
        self.con.execute(
            f"""CREATE TABLE IF NOT EXISTS {ATTESTATION_TABLE}(
                receipt_id TEXT PRIMARY KEY,
                basis_epoch INTEGER NOT NULL,
                semantic_state_hash TEXT NOT NULL,
                definition_hash TEXT NOT NULL,
                rootpage INTEGER NOT NULL,
                runtime_env_hash TEXT NOT NULL,
                runtime_env_json TEXT NOT NULL,
                v6_source_receipt_id TEXT,
                actor TEXT NOT NULL,
                policy_provenance_ref TEXT NOT NULL,
                policy_decision_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                authority TEXT NOT NULL
            )"""
        )

    def _latest_attestation(self) -> dict[str, Any] | None:
        if not self._attestation_table_exists():
            return None
        row = self.con.execute(
            f"SELECT * FROM {ATTESTATION_TABLE} ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row is not None else None

    def _latest_v6_marker(self) -> tuple[str | None, str | None, str | None]:
        if not self._v6_log_exists():
            return None, None, None
        row = self.con.execute(
            "SELECT receipt_id,status,provenance_status "
            "FROM pulse_rank_maintenance_receipts_v6 ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None, None, None
        return str(row["receipt_id"]), str(row["status"]), str(row["provenance_status"])

    def _latest_native_v6_material_receipt_id(self) -> str | None:
        rid, status, provenance = self._latest_v6_marker()
        if provenance == NATIVE_PROVENANCE_STATUS and status in {"BUILT", "REBUILT"}:
            return rid
        return None

    def physical_identity(self) -> PhysicalIndexIdentityV62:
        present, definition_hash, rootpage = self._raw_index()
        env_hash, _ = self._runtime()
        marker_id, marker_status, marker_provenance = self._latest_v6_marker()
        latest_v6 = (
            marker_id
            if marker_provenance == NATIVE_PROVENANCE_STATUS
            and marker_status in {"BUILT", "REBUILT"}
            else None
        )
        att = self._latest_attestation()
        att_id = str(att["receipt_id"]) if att else None
        if not present:
            return PhysicalIndexIdentityV62(False, "ABSENT", None, None, env_hash, latest_v6, att_id)
        if definition_hash != CANONICAL_INDEX_IDENTITY_HASH:
            return PhysicalIndexIdentityV62(
                True, "DEFINITION_DRIFT", definition_hash, rootpage, env_hash, latest_v6, att_id
            )
        if not att:
            return PhysicalIndexIdentityV62(
                True, "UNATTESTED", definition_hash, rootpage, env_hash, latest_v6, None
            )
        if str(att["runtime_env_hash"]) != env_hash:
            return PhysicalIndexIdentityV62(
                True, "RUNTIME_DRIFT", definition_hash, rootpage, env_hash, latest_v6, att_id
            )
        if str(att["definition_hash"]) != definition_hash or int(att["rootpage"]) != int(rootpage):
            return PhysicalIndexIdentityV62(
                True, "PHYSICAL_DRIFT", definition_hash, rootpage, env_hash, latest_v6, att_id
            )
        att_v6 = att["v6_source_receipt_id"]
        if marker_provenance == NATIVE_PROVENANCE_STATUS and marker_status == "DROPPED":
            return PhysicalIndexIdentityV62(
                True, "PARENT_V6_DRIFT", definition_hash, rootpage, env_hash, None, att_id
            )
        if latest_v6 is not None and str(att_v6 or "") != latest_v6:
            return PhysicalIndexIdentityV62(
                True, "PARENT_V6_DRIFT", definition_hash, rootpage, env_hash, latest_v6, att_id
            )
        return PhysicalIndexIdentityV62(
            True, "ATTESTED", definition_hash, rootpage, env_hash, latest_v6, att_id
        )

    def plan_lifecycle(
        self,
        *,
        basis_epoch: int,
        economics_without_horizon: CompileEconomics,
        pulse_history: Iterable[EpochReadLifetime],
        actor: str,
        policy_provenance_ref: str,
        policy_decision_hash: str,
        **horizon_kwargs,
    ) -> RankLifecyclePlanV62:
        actor, policy_provenance_ref, policy_decision_hash = self._native_provenance(
            actor=actor,
            policy_provenance_ref=policy_provenance_ref,
            policy_decision_hash=policy_decision_hash,
        )
        if basis_epoch != self.ledger.epoch:
            raise StaleEpoch(f"rank lifecycle basis {basis_epoch}!={self.ledger.epoch}")
        horizon, decision = decide_compile_from_pulse_history(
            economics_without_horizon, list(pulse_history), **horizon_kwargs
        )
        physical = self.physical_identity()
        desired = "COMPILED_INDEX" if decision.mode == "COMPILE" else "ONLINE"
        if desired == "ONLINE":
            action = "DROP_INDEX" if physical.present else "NONE"
        elif not physical.present:
            action = "BUILD_INDEX"
        elif physical.state == "ATTESTED":
            action = "NONE"
        elif physical.state in {"DEFINITION_DRIFT", "PARENT_V6_DRIFT"}:
            action = "REBUILD_INDEX"
        else:
            action = "REFRESH_ATTESTATION"
        body = {
            "implementation": IMPLEMENTATION_ID,
            "basis_epoch": basis_epoch,
            "semantic_state_hash": self.ledger.semantic_state_hash,
            "desired_mode": desired,
            "maintenance_action": action,
            "physical_state": physical.state,
            "actual_index_present": physical.present,
            "definition_hash": physical.definition_hash,
            "rootpage": physical.rootpage,
            "runtime_env_hash": physical.runtime_env_hash,
            "actor": actor,
            "policy_provenance_ref": policy_provenance_ref,
            "policy_decision_hash": policy_decision_hash,
            "horizon_status": horizon.status,
            "horizon_reads_lower_bound": horizon.expected_reads_lower_bound,
            "compile_reason": decision.reason,
            "guarded_break_even_reads": decision.guarded_break_even_reads,
        }
        return RankLifecyclePlanV62(
            basis_epoch=basis_epoch,
            semantic_state_hash=self.ledger.semantic_state_hash,
            desired_mode=desired,
            maintenance_action=action,
            physical_state=physical.state,
            actual_index_present=physical.present,
            definition_hash=physical.definition_hash,
            rootpage=physical.rootpage,
            runtime_env_hash=physical.runtime_env_hash,
            actor=actor,
            policy_provenance_ref=policy_provenance_ref,
            policy_decision_hash=policy_decision_hash,
            horizon_status=horizon.status,
            horizon_reads_lower_bound=horizon.expected_reads_lower_bound,
            compile_reason=decision.reason,
            guarded_break_even_reads=decision.guarded_break_even_reads,
            plan_hash=h(body),
        )

    def _parent_plan(self, plan: RankLifecyclePlanV62, action: str, present: bool) -> RankLifecyclePlan:
        return RankLifecyclePlan(
            basis_epoch=plan.basis_epoch,
            semantic_state_hash=plan.semantic_state_hash,
            desired_mode="COMPILED_INDEX" if action == "BUILD_INDEX" else "ONLINE",
            actual_index_present=present,
            maintenance_action=action,
            horizon_status=plan.horizon_status,
            horizon_reads_lower_bound=plan.horizon_reads_lower_bound,
            compile_reason=f"V6_2:{plan.compile_reason}:{action}",
            guarded_break_even_reads=plan.guarded_break_even_reads,
            plan_hash=h({"v6_2_parent": plan.plan_hash, "action": action, "present": present}),
        )

    def _insert_attestation_no_commit(self, values: dict[str, Any]) -> None:
        columns = list(values)
        marks = ",".join("?" for _ in columns)
        self.con.execute(
            f"INSERT INTO {ATTESTATION_TABLE}({','.join(columns)}) VALUES({marks})",
            [values[c] for c in columns],
        )

    def _attest(self, plan: RankLifecyclePlanV62, *, v6_source_receipt_id: str | None = None) -> str:
        if plan.basis_epoch != self.ledger.epoch or plan.semantic_state_hash != self.ledger.semantic_state_hash:
            raise StaleEpoch("attestation basis stale")
        before = self.physical_identity()
        if not before.present or before.definition_hash != CANONICAL_INDEX_IDENTITY_HASH:
            raise RankPhysicalStateStale("attestation requires canonical rank index")
        roots = (self.ledger.semantic_state_hash, self.ledger.trace_root_hash)
        try:
            self.con.execute("BEGIN IMMEDIATE")
            present, definition_hash, rootpage = self._raw_index()
            if not present or definition_hash != CANONICAL_INDEX_IDENTITY_HASH:
                raise RankPhysicalStateStale("rank index changed before REINDEX")
            if plan.basis_epoch != self.ledger.epoch or plan.semantic_state_hash != self.ledger.semantic_state_hash:
                raise StaleEpoch("semantic basis changed before REINDEX")
            self.con.execute(f"REINDEX {INDEX_NAME}")
            present, definition_hash, rootpage = self._raw_index()
            if not present or definition_hash != CANONICAL_INDEX_IDENTITY_HASH:
                raise AssertionError("REINDEX did not preserve canonical definition")
            self._create_attestation_table_no_commit()
            env_hash, env_json = self._runtime()
            source = (
                v6_source_receipt_id
                if v6_source_receipt_id is not None
                else self._latest_native_v6_material_receipt_id()
            )
            body = {
                "basis_epoch": plan.basis_epoch,
                "semantic_state_hash": plan.semantic_state_hash,
                "definition_hash": definition_hash,
                "rootpage": rootpage,
                "runtime_env_hash": env_hash,
                "v6_source_receipt_id": source,
                "actor": plan.actor,
                "policy_provenance_ref": plan.policy_provenance_ref,
                "policy_decision_hash": plan.policy_decision_hash,
                "authority": AUTHORITY,
            }
            receipt_id = h(body)
            self._insert_attestation_no_commit(
                {
                    "receipt_id": receipt_id,
                    "basis_epoch": plan.basis_epoch,
                    "semantic_state_hash": plan.semantic_state_hash,
                    "definition_hash": definition_hash,
                    "rootpage": rootpage,
                    "runtime_env_hash": env_hash,
                    "runtime_env_json": env_json,
                    "v6_source_receipt_id": source,
                    "actor": plan.actor,
                    "policy_provenance_ref": plan.policy_provenance_ref,
                    "policy_decision_hash": plan.policy_decision_hash,
                    "created_at": self.con.execute(
                        "SELECT strftime('%Y-%m-%dT%H:%M:%fZ','now')"
                    ).fetchone()[0],
                    "authority": AUTHORITY,
                }
            )
            if roots != (self.ledger.semantic_state_hash, self.ledger.trace_root_hash):
                raise AssertionError("attestation mutated semantic/trace roots")
            self.con.commit()
            return receipt_id
        except Exception:
            self.con.rollback()
            raise

    @staticmethod
    def _same_physical(observed: PhysicalIndexIdentityV62, plan: RankLifecyclePlanV62) -> bool:
        return (
            observed.present == plan.actual_index_present
            and observed.state == plan.physical_state
            and observed.definition_hash == plan.definition_hash
            and observed.rootpage == plan.rootpage
            and observed.runtime_env_hash == plan.runtime_env_hash
        )

    def apply_maintenance(self, plan: RankLifecyclePlanV62) -> RankMaintenanceReceiptV62:
        if plan.basis_epoch != self.ledger.epoch or plan.semantic_state_hash != self.ledger.semantic_state_hash:
            raise StaleEpoch("V6.2 maintenance plan stale")
        before = self.physical_identity()
        if not self._same_physical(before, plan):
            raise RankPhysicalStateStale("V6.2 physical precondition changed")
        action = plan.maintenance_action
        parent_ids: list[str] = []
        if action == "NONE":
            return RankMaintenanceReceiptV62(
                plan.basis_epoch, action, "NO_CHANGE", before.state, before.state, (),
                before.attestation_receipt_id, plan.actor, plan.policy_provenance_ref,
                plan.policy_decision_hash, plan.plan_hash, False,
            )
        if action == "DROP_INDEX":
            receipt = super().apply_maintenance(
                self._parent_plan(plan, "DROP_INDEX", True),
                actor=plan.actor,
                policy_provenance_ref=plan.policy_provenance_ref,
                policy_decision_hash=plan.policy_decision_hash,
            )
            if receipt.receipt_id:
                parent_ids.append(receipt.receipt_id)
            after = self.physical_identity()
            return RankMaintenanceReceiptV62(
                plan.basis_epoch, action, receipt.status, before.state, after.state,
                tuple(parent_ids), None, plan.actor, plan.policy_provenance_ref,
                plan.policy_decision_hash, plan.plan_hash, receipt.persisted,
            )
        if action == "REBUILD_INDEX":
            drop = super().apply_maintenance(
                self._parent_plan(plan, "DROP_INDEX", True),
                actor=plan.actor,
                policy_provenance_ref=plan.policy_provenance_ref,
                policy_decision_hash=plan.policy_decision_hash,
            )
            if drop.receipt_id:
                parent_ids.append(drop.receipt_id)
            if drop.status != "DROPPED":
                after = self.physical_identity()
                return RankMaintenanceReceiptV62(
                    plan.basis_epoch, action, "REBUILD_DROP_FAILED_SAFE", before.state, after.state,
                    tuple(parent_ids), None, plan.actor, plan.policy_provenance_ref,
                    plan.policy_decision_hash, plan.plan_hash, drop.persisted,
                )
            build = super().apply_maintenance(
                self._parent_plan(plan, "BUILD_INDEX", False),
                actor=plan.actor,
                policy_provenance_ref=plan.policy_provenance_ref,
                policy_decision_hash=plan.policy_decision_hash,
            )
            if build.receipt_id:
                parent_ids.append(build.receipt_id)
            if build.status != "BUILT":
                after = self.physical_identity()
                return RankMaintenanceReceiptV62(
                    plan.basis_epoch, action, "REBUILD_BUILD_FAILED_SAFE", before.state, after.state,
                    tuple(parent_ids), None, plan.actor, plan.policy_provenance_ref,
                    plan.policy_decision_hash, plan.plan_hash, build.persisted,
                )
            try:
                attestation_id = self._attest(plan, v6_source_receipt_id=build.receipt_id)
            except (StaleEpoch, RankPhysicalStateStale):
                raise
            except Exception as exc:
                after = self.physical_identity()
                return RankMaintenanceReceiptV62(
                    plan.basis_epoch, action, "REBUILT_UNATTESTED_SAFE", before.state, after.state,
                    tuple(parent_ids), None, plan.actor, plan.policy_provenance_ref,
                    plan.policy_decision_hash, plan.plan_hash, False, type(exc).__name__,
                )
            after = self.physical_identity()
            return RankMaintenanceReceiptV62(
                plan.basis_epoch, action,
                "REBUILT_ATTESTED" if after.state == "ATTESTED" else "REBUILT_UNATTESTED_SAFE",
                before.state, after.state, tuple(parent_ids), attestation_id, plan.actor,
                plan.policy_provenance_ref, plan.policy_decision_hash, plan.plan_hash,
                after.state == "ATTESTED",
            )
        if action == "BUILD_INDEX":
            build = super().apply_maintenance(
                self._parent_plan(plan, "BUILD_INDEX", False),
                actor=plan.actor,
                policy_provenance_ref=plan.policy_provenance_ref,
                policy_decision_hash=plan.policy_decision_hash,
            )
            if build.receipt_id:
                parent_ids.append(build.receipt_id)
            if build.status != "BUILT":
                after = self.physical_identity()
                return RankMaintenanceReceiptV62(
                    plan.basis_epoch, action, build.status, before.state, after.state,
                    tuple(parent_ids), None, plan.actor, plan.policy_provenance_ref,
                    plan.policy_decision_hash, plan.plan_hash, False,
                )
            source = build.receipt_id
        elif action == "REFRESH_ATTESTATION":
            source = None
        else:
            raise ValueError(action)
        try:
            attestation_id = self._attest(plan, v6_source_receipt_id=source)
        except (StaleEpoch, RankPhysicalStateStale):
            raise
        except Exception as exc:
            after = self.physical_identity()
            return RankMaintenanceReceiptV62(
                plan.basis_epoch, action, "UNATTESTED_SAFE_FALLBACK", before.state, after.state,
                tuple(parent_ids), None, plan.actor, plan.policy_provenance_ref,
                plan.policy_decision_hash, plan.plan_hash, False, type(exc).__name__,
            )
        after = self.physical_identity()
        return RankMaintenanceReceiptV62(
            plan.basis_epoch, action,
            "ATTESTED" if after.state == "ATTESTED" else "UNATTESTED_SAFE_FALLBACK",
            before.state, after.state, tuple(parent_ids), attestation_id, plan.actor,
            plan.policy_provenance_ref, plan.policy_decision_hash, plan.plan_hash,
            after.state == "ATTESTED",
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
        policy_decision_hash: str,
        reentry_mode: str = "NO_REENTRY",
        previous_focus_refs: tuple[str, ...] = (),
        shuffle_salt: str | None = None,
        **horizon_kwargs,
    ) -> RankSelectionV62:
        if basis_epoch != self.ledger.epoch:
            raise StaleEpoch(f"rank basis {basis_epoch}!={self.ledger.epoch}")
        if not 1 <= max_candidates <= 512:
            raise ValueError("max_candidates out of bounds")
        if not 1 <= max_focus <= min(64, max_candidates):
            raise ValueError("max_focus out of bounds")
        mode = reentry_mode.upper()
        if mode not in {"TRUTHFUL", "NO_REENTRY", "SHUFFLED_CONTROL", "PROVENANCE_BROKEN_CONTROL"}:
            raise ValueError(mode)
        domains = self._domains(source_domains)
        lifecycle = self.plan_lifecycle(
            basis_epoch=basis_epoch,
            economics_without_horizon=economics_without_horizon,
            pulse_history=pulse_history,
            actor=actor,
            policy_provenance_ref=policy_provenance_ref,
            policy_decision_hash=policy_decision_hash,
            **horizon_kwargs,
        )
        physical = self.physical_identity()
        use_index = lifecycle.desired_mode == "COMPILED_INDEX" and physical.state == "ATTESTED"
        if use_index:
            read_mode = "COMPILED_ATTESTED_INDEX"
        elif lifecycle.desired_mode == "COMPILED_INDEX" and not physical.present:
            read_mode = "ONLINE_PENDING_COMPILE"
        elif lifecycle.maintenance_action == "REBUILD_INDEX":
            read_mode = "ONLINE_PENDING_REBUILD"
        elif lifecycle.desired_mode == "COMPILED_INDEX":
            read_mode = "ONLINE_PENDING_ATTESTATION"
        elif physical.present:
            read_mode = "ONLINE_PENDING_DECOMPILE"
        else:
            read_mode = "ONLINE"
        roots = (self.ledger.epoch, self.ledger.semantic_state_hash, self.ledger.trace_root_hash)
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
        ranked: list[tuple[float, str, str]] = []
        for ref, row in by_ref.items():
            score = float(row["score"]) + (REENTRY_BOOST if ref in targets else 0.0)
            ranked.append((score, ref, str(row["semantic_hash"])))
        ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
        ranked = ranked[:max_candidates]
        candidates = tuple(item[1] for item in ranked)
        focus = candidates[:max_focus]
        scores = tuple(round(float(item[0]), 8) for item in ranked)
        universe = self._count(domains, "KNOWN")
        conflicts = self._count(domains, "CONFLICT")
        unknown = self._count(domains, "UNKNOWN")
        if roots != (self.ledger.epoch, self.ledger.semantic_state_hash, self.ledger.trace_root_hash):
            raise AssertionError("V6.2 read phase mutated authoritative ledger roots")
        body = {
            "implementation": IMPLEMENTATION_ID,
            "basis_epoch": basis_epoch,
            "semantic_state_hash": self.ledger.semantic_state_hash,
            "candidate_refs": list(candidates),
            "focus_refs": list(focus),
            "candidate_scores": list(scores),
            "reentry_mode": mode,
            "physical_read_mode": read_mode,
            "physical_state": physical.state,
            "lifecycle_plan_hash": lifecycle.plan_hash,
        }
        return RankSelectionV62(
            basis_epoch=basis_epoch,
            semantic_state_hash=self.ledger.semantic_state_hash,
            candidate_refs=candidates,
            focus_refs=focus,
            candidate_scores=scores,
            candidate_universe_count=universe,
            query_truncated=universe > len(candidates),
            conflicts_present=conflicts,
            unknown_present=unknown,
            selection_hash=h(body),
            query_plan=query_plan,
            reentry_mode=mode,
            physical_read_mode=read_mode,
            desired_mode=lifecycle.desired_mode,
            maintenance_action=lifecycle.maintenance_action,
            physical_state=physical.state,
            lifecycle_plan_hash=lifecycle.plan_hash,
        )
