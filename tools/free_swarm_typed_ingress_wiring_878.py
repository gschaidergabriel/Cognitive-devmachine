#!/usr/bin/env python3
"""Successor-safe wiring for the existing typed Free-Swarm delta ingress.

This module does not create another ingress or evaluator. It reuses
``CLAY_ARCHITECTURE_DELTA_INGRESS/v1`` from ``free_swarm_delta_ingress`` and
threads its deterministic admission state through two already-authoritative
surfaces:

* completed v5 worker records, before append-only materialization; and
* historical replay observations before the backlog-first Evidence Forge.

Candidate evaluation semantics remain owned by the existing Evidence Forge.
This layer is measurement/provenance only and cannot mint runtime/model/training
or canonical truth/effect authority.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from typing import Any

import free_swarm_delta_ingress as ingress

SCHEMA = "CLAY_TYPED_FORGE_INGRESS_WIRING/v1"
OBSERVATION_SCHEMA = "CLAY_TYPED_FORGE_INGRESS_OBSERVATION/v1"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_INSTALL_ATTR = "_clay_typed_ingress_878_installed"


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _repo_head(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    return text if COMMIT_RE.fullmatch(text) else None


def _summary(parsed: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": parsed.get("schema"),
        "status": parsed.get("status"),
        "valid": bool(parsed.get("valid")),
        "ready_for_forge": bool(parsed.get("ready_for_forge")),
        "reasons": list(parsed.get("reasons") or []),
        "proposal_sha256": parsed.get("proposal_sha256"),
        "repo_head_at_prompt": parsed.get("repo_head_at_prompt"),
        "worker_sha256": parsed.get("worker_sha256"),
        "authority": "DETERMINISTIC_CANDIDATE_ADMISSION_MEASUREMENT_ONLY",
    }


def classify_record(record: dict[str, Any]) -> dict[str, Any]:
    """Classify one successful worker record under the existing ingress schema."""
    text = str(record.get("text") or "")
    worker_sha = str(record.get("text_sha256") or _sha_text(text)).strip().lower()
    repo_head = _repo_head(record.get("repo_head_at_prompt"))
    parsed = ingress.parse_worker_delta(
        text,
        repo_head_at_prompt=repo_head,
        worker_sha256=worker_sha,
    )
    out = _summary(parsed)
    single = ingress.DELTA_MARKER in text
    batch = "ARCHITECTURE_DELTA_BATCH_JSON=" in text
    out["transport_kind"] = (
        "MIXED" if single and batch else "SINGLE" if single else "BATCH" if batch else "NONE"
    )
    return out


def attach_record(record: dict[str, Any]) -> dict[str, Any]:
    record["delta_ingress"] = classify_record(record)
    return record


def install_live(v5_module: Any) -> None:
    """Wrap v5's completed-record finalizer without replacing network authority."""
    if getattr(v5_module, _INSTALL_ATTR, False):
        return
    original = getattr(v5_module, "_finish_success")

    def wrapped(
        common: dict[str, Any],
        text: str,
        prompt: str,
        payloads: tuple[Any, ...],
        pipeline: dict[str, Any],
        headers: dict[str, str] | None,
        started: float,
    ) -> None:
        original(common, text, prompt, payloads, pipeline, headers, started)
        attach_record(common)

    v5_module._finish_success = wrapped
    setattr(v5_module, _INSTALL_ATTR, True)


def _ensure_observation_schema(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS typed_ingress_observations(
          source_event_id TEXT PRIMARY KEY,
          source_path TEXT NOT NULL,
          line_no INTEGER NOT NULL,
          worker_sha TEXT NOT NULL,
          repo_head TEXT,
          ingress_schema TEXT NOT NULL,
          ingress_status TEXT NOT NULL,
          valid INTEGER NOT NULL,
          ready_for_forge INTEGER NOT NULL,
          proposal_sha256 TEXT,
          transport_kind TEXT NOT NULL,
          reasons_json TEXT NOT NULL,
          observed_at TEXT NOT NULL
        )
        """
    )
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_typed_ingress_status "
        "ON typed_ingress_observations(ingress_status,transport_kind)"
    )


def _record_historical_observation(
    historical_module: Any,
    con: sqlite3.Connection,
    row: dict[str, Any],
    source_path: str,
    line_no: int,
) -> None:
    status = row.get("http_status")
    if not (isinstance(status, int) and 200 <= status < 300):
        return
    text = str(row.get("text") or "")
    if not text:
        return
    worker_sha = str(row.get("text_sha256") or historical_module.sha_text(text)).strip().lower()
    event_id = historical_module.source_event_identity(row, source_path, line_no, worker_sha)
    classified = classify_record({**row, "text_sha256": worker_sha})
    _ensure_observation_schema(con)
    con.execute(
        """
        INSERT OR IGNORE INTO typed_ingress_observations(
          source_event_id,source_path,line_no,worker_sha,repo_head,ingress_schema,
          ingress_status,valid,ready_for_forge,proposal_sha256,transport_kind,
          reasons_json,observed_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            event_id,
            source_path,
            int(line_no),
            worker_sha,
            _repo_head(row.get("repo_head_at_prompt")),
            str(classified.get("schema") or ingress.SCHEMA),
            str(classified.get("status") or "UNMEASURED"),
            int(bool(classified.get("valid"))),
            int(bool(classified.get("ready_for_forge"))),
            classified.get("proposal_sha256"),
            str(classified.get("transport_kind") or "NONE"),
            json.dumps(classified.get("reasons") or [], sort_keys=True, separators=(",", ":")),
            historical_module.now(),
        ),
    )


def install_historical(historical_module: Any) -> None:
    """Observe historical admission states around the existing replay function."""
    if getattr(historical_module, _INSTALL_ATTR, False):
        return
    original = getattr(historical_module, "_ingest_worker_row")

    def wrapped(
        con: sqlite3.Connection,
        row: dict[str, Any],
        source_path: str,
        line_no: int,
    ) -> dict[str, int]:
        result = original(con, row, source_path, line_no)
        if int(result.get("successful", 0)) > 0:
            _record_historical_observation(
                historical_module, con, row, source_path, line_no
            )
        return result

    historical_module._ingest_worker_row = wrapped
    setattr(historical_module, _INSTALL_ATTR, True)


def historical_metrics(con: sqlite3.Connection) -> dict[str, Any]:
    _ensure_observation_schema(con)
    by_status = {
        str(status): int(count)
        for status, count in con.execute(
            "SELECT ingress_status,COUNT(*) FROM typed_ingress_observations "
            "GROUP BY ingress_status"
        )
    }
    by_transport = {
        str(kind): int(count)
        for kind, count in con.execute(
            "SELECT transport_kind,COUNT(*) FROM typed_ingress_observations "
            "GROUP BY transport_kind"
        )
    }
    total = int(
        con.execute("SELECT COUNT(*) FROM typed_ingress_observations").fetchone()[0]
    )
    ready = int(
        con.execute(
            "SELECT COUNT(*) FROM typed_ingress_observations WHERE ready_for_forge=1"
        ).fetchone()[0]
    )
    return {
        "schema": SCHEMA,
        "ingress_schema": ingress.SCHEMA,
        "observations": total,
        "ready_for_forge": ready,
        "by_status": by_status,
        "by_transport": by_transport,
        "authority": "MEASUREMENT_ONLY_NO_EVALUATOR_OR_CANONICAL_EFFECT_AUTHORITY",
        "runtime_credit_added": 0,
        "model_credit_added": 0,
        "training_credit_added": 0,
    }
