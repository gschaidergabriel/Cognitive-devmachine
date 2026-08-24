#!/usr/bin/env python3
"""Emit FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1 without provider contact."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import tempfile

import free_swarm_provider_admission as policy

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    rows: list[dict] = []
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        supervisor = tmp / "SUPERVISOR_INBOX.json"
        supervisor.write_text(json.dumps({
            "schema_version": "8.67",
            "free_only": {
                "enabled": True,
                "provider_execution_requires_typed_explicit_free_classification": True,
                "admission_boundary": "BEFORE_SECRET_OR_KEY_LOOKUP_AND_BEFORE_NETWORK_IO",
            },
        }), encoding="utf-8")

        def make_admission(label: str, cost_class: str, admitted: bool, epoch: str = "8.67") -> Path:
            path = tmp / f"{label}.json"
            path.write_text(json.dumps({
                "schema": policy.SCHEMA,
                "admission_id": f"probe-{label}",
                "authority_epoch": epoch,
                "mode": "FREE_ONLY",
                "source": "ENTITYOS_HCU_CONTROL_PLANE",
                "issued_at": "2026-08-24T00:00:00Z",
                "valid_until": "2099-01-01T00:00:00Z",
                "providers": {"groq": {
                    "cost_class": cost_class,
                    "admitted": admitted,
                    "evidence_ref": "probe:non-secret-cost-evidence",
                }},
            }), encoding="utf-8")
            return path

        cases: list[tuple[str, Path | None, bool]] = [
            ("MISSING_ADMISSION", None, False),
            ("UNKNOWN", make_admission("unknown", "UNKNOWN", False), False),
            ("PAID", make_admission("paid", "PAID", False), False),
            ("SUBSCRIPTION", make_admission("subscription", "SUBSCRIPTION", False), False),
            ("STALE_AUTHORITY", make_admission("stale", "FREE", True, "8.66"), False),
            ("FREE", make_admission("free", "FREE", True), True),
        ]

        for label, path, should_pass in cases:
            counts = {"secret_lookup_count": 0, "network_attempt_count": 0}

            def secret_tripwire(_permit):
                counts["secret_lookup_count"] += 1
                return "REDACTED"

            def socket_tripwire(_permit):
                counts["network_attempt_count"] += 1
                return "NO_REAL_SOCKET_CREATED"

            reason = "PASS"
            try:
                if path is None:
                    policy.load_admission(tmp / "missing.json", supervisor_path=supervisor)
                else:
                    snapshot = policy.load_admission(path, supervisor_path=supervisor)
                    policy.with_provider_permit(snapshot, "groq", secret_tripwire, supervisor_path=supervisor)
                    policy.with_provider_permit(snapshot, "groq", socket_tripwire, supervisor_path=supervisor)
            except policy.AdmissionError as exc:
                reason = str(exc)

            expected = {"secret_lookup_count": 1, "network_attempt_count": 1} if should_pass else {
                "secret_lookup_count": 0,
                "network_attempt_count": 0,
            }
            rows.append({
                "case": label,
                "expected_pass": should_pass,
                "observed_reason": reason,
                **counts,
                "pass": counts == expected and ((reason == "PASS") == should_pass),
            })

    source_paths = [
        ROOT / "tools/free_swarm_provider_admission.py",
        ROOT / "tools/run_free_go_swarm.py",
        ROOT / "tools/run_24h_entityos_swarm.py",
        ROOT / "tools/run_24h_entityos_swarm_supervisor.sh",
        ROOT / "tests/test_free_swarm_provider_admission_boundary.py",
    ]
    receipt = {
        "schema": "FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT/v1",
        "scope": "DETERMINISTIC_COMPONENT_BOUNDARY_NO_PROVIDER_CONTACT",
        "authority_epoch_fixture": "8.67",
        "result": "PASS" if all(row["pass"] for row in rows) else "FAIL",
        "cases": rows,
        "source_sha256": {str(path.relative_to(ROOT)): sha(path) for path in source_paths},
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "provider_contact": False,
        "real_secret_read": False,
        "real_socket_created": False,
        "credit_boundary": "component mechanism only; no provider, HCU, J-Space, training or whole-product runtime credit",
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
