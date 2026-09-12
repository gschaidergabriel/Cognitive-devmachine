from __future__ import annotations

import datetime as dt
import hashlib
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Iterable


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canon(value).encode("utf-8")).hexdigest()


class EffectIdentityConflict(RuntimeError):
    """An existing effect_id was presented with different immutable identity material."""


class UnifiedStore:
    """Typed writer facade for OMEGA's central SQLite convergence substrate."""

    def __init__(self, db_path: str | Path, schema_dir: str | Path) -> None:
        self.db_path = Path(db_path)
        self.schema_dir = Path(schema_dir)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path, timeout=30)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=30000")
        return con

    def _init_schema(self) -> None:
        files: list[Path] = []
        base = self.schema_dir / "omega.sql"
        if base.exists():
            files.append(base)
        files.extend(sorted(p for p in self.schema_dir.glob("[0-9][0-9][0-9]_*.sql") if p != base))
        if not files:
            raise FileNotFoundError(f"no OMEGA schema files in {self.schema_dir}")
        with self.connect() as con:
            for path in files:
                con.executescript(path.read_text(encoding="utf-8"))

    def register_source(self, source: dict[str, Any]) -> None:
        t = now()
        with self.connect() as con:
            con.execute(
                """
                INSERT INTO source_subject(source_id,source_kind,canonical_name,owner_id,machine_id,installation_id,metadata_json,first_seen_at,last_seen_at)
                VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(source_id) DO UPDATE SET
                  source_kind=excluded.source_kind,
                  canonical_name=excluded.canonical_name,
                  owner_id=COALESCE(excluded.owner_id,source_subject.owner_id),
                  machine_id=COALESCE(excluded.machine_id,source_subject.machine_id),
                  installation_id=COALESCE(excluded.installation_id,source_subject.installation_id),
                  metadata_json=excluded.metadata_json,
                  last_seen_at=excluded.last_seen_at
                """,
                (
                    source["source_id"], source["source_kind"], source["canonical_name"],
                    source.get("owner_id"), source.get("machine_id"), source.get("installation_id"),
                    canon(source.get("metadata", {})), t, t,
                ),
            )

    def register_sources(self, sources: Iterable[dict[str, Any]]) -> None:
        for source in sources:
            self.register_source(source)

    def record_observation(
        self,
        *,
        source_id: str,
        subject_id: str,
        payload: Any,
        observed_at: str,
        evidence_class: str,
        owner_id: str | None = None,
        machine_id: str | None = None,
        installation_id: str | None = None,
        runtime_epoch_id: str | None = None,
        source_repo: str | None = None,
        source_commit: str | None = None,
        source_path: str | None = None,
        receipt_id: str | None = None,
        raw_locator: str | None = None,
        authority_rank: int = 0,
        confidence: float | None = None,
    ) -> str:
        d = digest(payload)
        oid = "obs_" + hashlib.sha256(
            f"{source_id}\0{subject_id}\0{runtime_epoch_id or ''}\0{observed_at}\0{d}".encode()
        ).hexdigest()[:40]
        with self.connect() as con:
            con.execute(
                """
                INSERT OR IGNORE INTO observation(
                  observation_id,source_id,subject_id,owner_id,machine_id,installation_id,runtime_epoch_id,
                  source_repo,source_commit,source_path,receipt_id,raw_locator,observed_at,ingested_at,
                  evidence_class,authority_rank,confidence,content_digest,payload_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    oid,source_id,subject_id,owner_id,machine_id,installation_id,runtime_epoch_id,
                    source_repo,source_commit,source_path,receipt_id,raw_locator,observed_at,now(),
                    evidence_class,int(authority_rank),confidence,d,canon(payload),
                ),
            )
        return oid

    def record_telemetry(self, organ_id: str, payload: dict[str, Any]) -> None:
        observed_at = str(payload.get("observed_at") or now())
        d = digest(payload)
        with self.connect() as con:
            con.execute(
                """
                INSERT OR IGNORE INTO organ_telemetry(
                  organ_id,observed_at,owner_id,machine_id,health,cpu_load,ram_load,gpu_load,payload_json,content_digest
                ) VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    organ_id,observed_at,payload.get("owner_id") or payload.get("owner"),payload.get("machine_id"),
                    str(payload.get("health","UNKNOWN")),payload.get("cpu_load"),payload.get("ram_load"),
                    payload.get("gpu_load"),canon(payload),d,
                ),
            )

    def record_effect_intent(self, intent: dict[str, Any], *, owner_id: str | None, machine_id: str | None) -> None:
        """Persist an immutable effect identity or reject an effect-id rebind.

        Idempotence is allowed only when the complete persisted identity material is
        byte-for-byte/canonically equivalent. Reusing an effect_id for a different
        request, route, owner or machine fails closed instead of silently keeping the
        first row and letting later code dispatch under ambiguous provenance.
        """
        t = now()
        request = intent.get("task", {}).get("effect") or intent.get("task", {}).get("execution") or {}
        request_digest = digest(request)
        payload_json = canon(intent)
        organ_id = str(intent["organ_id"])
        effect_id = str(intent["effect_id"])
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT organ_id,owner_id,machine_id,request_digest,payload_json FROM effect_intent WHERE effect_id=?",
                (effect_id,),
            ).fetchone()
            if row is not None:
                existing = (
                    str(row["organ_id"]), row["owner_id"], row["machine_id"],
                    str(row["request_digest"]), str(row["payload_json"]),
                )
                incoming = (organ_id, owner_id, machine_id, request_digest, payload_json)
                if existing != incoming:
                    raise EffectIdentityConflict(f"EFFECT_ID_REBIND_CONFLICT:{effect_id}")
                con.commit()
                return
            con.execute(
                """
                INSERT INTO effect_intent(effect_id,frame_id,organ_id,owner_id,machine_id,request_digest,payload_json,authority_state,dispatch_state,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    effect_id,intent.get("frame_id"),organ_id,owner_id,machine_id,
                    request_digest,payload_json,str(intent.get("authority","NOT_YET_GRANTED")),"PROPOSED",t,t,
                ),
            )
            con.commit()

    def update_effect_state(self, effect_id: str, *, authority_state: str | None = None, dispatch_state: str | None = None) -> None:
        fields = ["updated_at=?"]
        values: list[Any] = [now()]
        if authority_state is not None:
            fields.append("authority_state=?"); values.append(authority_state)
        if dispatch_state is not None:
            fields.append("dispatch_state=?"); values.append(dispatch_state)
        values.append(effect_id)
        with self.connect() as con:
            con.execute(f"UPDATE effect_intent SET {','.join(fields)} WHERE effect_id=?", values)

    def record_policy_decision(
        self,
        *,
        decision_id: str,
        effect_id: str,
        binding_id: str,
        authority_ref: str,
        decision: str,
        reason: str,
        request_digest: str,
        organ_id: str,
        owner_id: str | None,
        machine_id: str | None,
    ) -> None:
        with self.connect() as con:
            con.execute(
                """INSERT OR IGNORE INTO policy_decision VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (decision_id,effect_id,binding_id,authority_ref,decision,reason,request_digest,organ_id,owner_id,machine_id,now()),
            )

    def claim_relay_dispatch(self, *, effect_id: str, organ_id: str) -> tuple[bool, str]:
        """Atomically acquire the one allowed relay attempt for an effect.

        The claim is taken in SQLite with BEGIN IMMEDIATE before any external effect
        boundary is crossed. Once a ledger row exists, no caller may mint a second
        dispatch attempt automatically, irrespective of whether the prior state is
        DISPATCHING, UNKNOWN, FAILED, BLOCKED or COMPLETED. Crash recovery can later
        quarantine abandoned DISPATCHING rows to UNKNOWN, but never reopens the claim.
        """
        t = now()
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            intent = con.execute(
                "SELECT organ_id FROM effect_intent WHERE effect_id=?",
                (effect_id,),
            ).fetchone()
            if intent is None:
                raise EffectIdentityConflict(f"CLAIM_WITHOUT_EFFECT_INTENT:{effect_id}")
            if str(intent["organ_id"]) != organ_id:
                raise EffectIdentityConflict(f"EFFECT_ORGAN_REBIND_CONFLICT:{effect_id}")

            row = con.execute(
                "SELECT organ_id,state FROM relay_ledger WHERE effect_id=?",
                (effect_id,),
            ).fetchone()
            if row is not None:
                if str(row["organ_id"]) != organ_id:
                    raise EffectIdentityConflict(f"RELAY_ORGAN_REBIND_CONFLICT:{effect_id}")
                state = str(row["state"])
                con.commit()
                return False, state

            con.execute(
                """
                INSERT INTO relay_ledger(effect_id,organ_id,command_id,state,attempt_count,command_digest,receipt_digest,last_error,created_at,updated_at)
                VALUES(?,?,NULL,'DISPATCHING',1,NULL,NULL,NULL,?,?)
                """,
                (effect_id,organ_id,t,t),
            )
            con.execute(
                "UPDATE effect_intent SET dispatch_state='DISPATCHING', updated_at=? WHERE effect_id=?",
                (t,effect_id),
            )
            con.commit()
            return True, "DISPATCHING"

    def upsert_relay(
        self,
        *,
        effect_id: str,
        organ_id: str,
        state: str,
        command_id: str | None = None,
        command_digest: str | None = None,
        receipt_digest: str | None = None,
        last_error: str | None = None,
        increment_attempt: bool = False,
    ) -> None:
        # The existing bridge relay calls this with increment_attempt=True immediately
        # before it can cross an external effect boundary. Treat that call as the
        # transactional claim itself so concurrent relay processes cannot both pass.
        if increment_attempt:
            claimed, existing_state = self.claim_relay_dispatch(effect_id=effect_id, organ_id=organ_id)
            if not claimed:
                raise EffectIdentityConflict(
                    f"RELAY_DISPATCH_ALREADY_CLAIMED:{effect_id}:{existing_state}"
                )
            return

        t = now()
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT organ_id,attempt_count,created_at FROM relay_ledger WHERE effect_id=?",
                (effect_id,),
            ).fetchone()
            if row is not None and str(row["organ_id"]) != organ_id:
                raise EffectIdentityConflict(f"RELAY_ORGAN_REBIND_CONFLICT:{effect_id}")
            attempts = int(row["attempt_count"]) if row else 0
            created = str(row["created_at"]) if row else t
            con.execute(
                """
                INSERT OR REPLACE INTO relay_ledger(effect_id,organ_id,command_id,state,attempt_count,command_digest,receipt_digest,last_error,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (effect_id,organ_id,command_id,state,attempts,command_digest,receipt_digest,last_error,created,t),
            )
            con.commit()

    def record_effect_receipt(
        self,
        *,
        effect_id: str,
        subject_id: str,
        action_kind: str,
        request_digest: str,
        status: str,
        requested_at: str,
        owner_id: str | None = None,
        machine_id: str | None = None,
        runtime_epoch_id: str | None = None,
        result_digest: str | None = None,
        completed_at: str | None = None,
        receipt_locator: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with self.connect() as con:
            con.execute(
                """
                INSERT INTO effect_receipt(effect_id,subject_id,owner_id,machine_id,runtime_epoch_id,action_kind,request_digest,result_digest,status,requested_at,completed_at,receipt_locator,metadata_json)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(effect_id) DO UPDATE SET
                  result_digest=excluded.result_digest,status=excluded.status,completed_at=excluded.completed_at,
                  receipt_locator=excluded.receipt_locator,metadata_json=excluded.metadata_json
                """,
                (effect_id,subject_id,owner_id,machine_id,runtime_epoch_id,action_kind,request_digest,result_digest,status,requested_at,completed_at,receipt_locator,canon(metadata or {})),
            )

    def bridge_message(self, *, direction: str, sender: str, recipient: str, kind: str, payload: Any, correlation_id: str | None = None) -> str:
        mid = "bridge_" + uuid.uuid4().hex
        with self.connect() as con:
            con.execute(
                "INSERT INTO bridge_message(message_id,direction,sender,recipient,kind,payload_json,created_at,consumed_at,correlation_id) VALUES(?,?,?,?,?,?,?,?,?)",
                (mid,direction,sender,recipient,kind,canon(payload),now(),None,correlation_id),
            )
        return mid


__all__ = ["UnifiedStore", "EffectIdentityConflict", "now", "canon", "digest"]
