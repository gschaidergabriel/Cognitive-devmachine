#!/usr/bin/env python3
"""Supervisor-8.72 conversion-funnel backpressure for the 6000 Free Swarm.

This is a control/efficiency surface only. It does not mint truth or evidence.
While the exact evidence-qualified Forge -> Distillery conversion gate has produced
zero accepted dataset tokens/packets, cap provider concurrency so raw token scale
cannot outrun the downstream evidence funnel. The cap self-releases only after
both an evidence-qualified packet and nonzero accepted dataset tokens are observed.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
from typing import Any, MutableMapping

DEFAULT_ARTIFACT_ROOT = Path("/artifacts/clay-entityos-swarm")
BACKPRESSURE_PROVIDER_CAPS = {
    "groq": 4,
    "mistral": 4,
    "nvidia": 24,
    "openrouter": 2,
}
BACKPRESSURE_HTTP_THREADS = 64


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def funnel_snapshot(artifact_root: Path) -> dict[str, Any]:
    """Read only bounded downstream counters; never provider credentials."""
    dist = _json(artifact_root / "distillery" / "STATUS.json")
    forge = _json(artifact_root / "forge" / "STATUS.json")
    db = artifact_root / "distillery" / "distillery.sqlite3"

    tokens = _int(dist.get("accepted_dataset_tokens"))
    qualified_packets = _int(
        dist.get("forge_evidence_qualified_packets")
        or dist.get("accepted_forge_evidence_qualified_packets")
    )
    accepted_packets = _int(dist.get("accepted_packets"))

    # STATUS can lag the DB. Read only integer counters, never packet text.
    if db.exists():
        try:
            con = sqlite3.connect(db, timeout=2)
            try:
                tables = {
                    str(row[0])
                    for row in con.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
                if "counters" in tables:
                    for key, field in (
                        ("accepted_dataset_tokens", "tokens"),
                        ("forge_evidence_qualified_packets", "qualified"),
                    ):
                        row = con.execute(
                            "SELECT value FROM counters WHERE key=?", (key,)
                        ).fetchone()
                        if row is not None:
                            if field == "tokens":
                                tokens = _int(row[0])
                            else:
                                qualified_packets = _int(row[0])
                if "knowledge_packets" in tables:
                    accepted_packets = _int(
                        con.execute("SELECT COUNT(*) FROM knowledge_packets").fetchone()[0]
                    )
            finally:
                con.close()
        except (OSError, sqlite3.Error):
            pass

    return {
        "accepted_dataset_tokens": tokens,
        "forge_evidence_qualified_packets": qualified_packets,
        "accepted_packets": accepted_packets,
        "forge_nominal_accepted_deltas": _int(
            forge.get("accepted_deltas")
            or (forge.get("candidate_states") or {}).get("ACCEPTED")
        ),
        "distillery_status_present": bool(dist),
        "forge_status_present": bool(forge),
        "db_present": db.exists(),
    }


def decision(snapshot: dict[str, Any]) -> dict[str, Any]:
    tokens = _int(snapshot.get("accepted_dataset_tokens"))
    qualified = _int(snapshot.get("forge_evidence_qualified_packets"))
    release = tokens > 0 and qualified > 0
    if release:
        return {
            "mode": "RELEASED_EVIDENCE_FUNNEL_NONZERO",
            "apply_backpressure": False,
            "reason": "EVIDENCE_QUALIFIED_PACKET_AND_DATASET_TOKENS_NONZERO",
        }
    return {
        "mode": "BOOTSTRAP_ZERO_YIELD_BACKPRESSURE",
        "apply_backpressure": True,
        "reason": (
            "EXACT_EVIDENCE_QUALIFIED_FORGE_TO_DISTILLERY_GATE_NOT_YET_NONZERO"
        ),
    }


def _lower_int_env(
    env: MutableMapping[str, str], name: str, cap: int, default_if_unset: int
) -> int:
    raw = env.get(name)
    try:
        current = int(raw) if raw is not None else default_if_unset
    except ValueError:
        current = default_if_unset
    chosen = max(1, min(current, cap))
    env[name] = str(chosen)
    return chosen


def apply(
    artifact_root: Path | None = None,
    env: MutableMapping[str, str] | None = None,
) -> dict[str, Any]:
    """Apply caps by lowering existing/default limits only; never raise them."""
    root = artifact_root or Path(
        os.getenv("CLAY_SWARM_ARTIFACT_ROOT", str(DEFAULT_ARTIFACT_ROOT))
    )
    target_env = env if env is not None else os.environ
    snapshot = funnel_snapshot(root)
    verdict = decision(snapshot)

    applied: dict[str, int] = {}
    if verdict["apply_backpressure"]:
        default_caps = {
            "groq": 128,
            "mistral": 128,
            "nvidia": 256,
            "openrouter": 16,
        }
        for provider, cap in BACKPRESSURE_PROVIDER_CAPS.items():
            name = f"CLAY_{provider.upper()}_MAX_CONCURRENCY"
            applied[name] = _lower_int_env(
                target_env, name, cap, default_caps[provider]
            )
        applied["CLAY_SWARM_HTTP_THREADS"] = _lower_int_env(
            target_env,
            "CLAY_SWARM_HTTP_THREADS",
            BACKPRESSURE_HTTP_THREADS,
            512,
        )

    receipt = {
        "schema": "CLAY_FREE_SWARM_CONVERSION_BACKPRESSURE/v1",
        "authority_epoch": "8.72",
        "artifact_root": str(root),
        "snapshot": snapshot,
        **verdict,
        "applied_limits": applied,
        "canonical_truth_minted": False,
        "runtime_credit_minted": False,
        "provider_credit_minted": False,
    }
    try:
        status = root / "control" / "conversion_backpressure.json"
        status.parent.mkdir(parents=True, exist_ok=True)
        status.write_text(
            json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError:
        # Telemetry persistence must not turn a conservative cap into a crash.
        receipt["status_write"] = "UNAVAILABLE"
    return receipt
