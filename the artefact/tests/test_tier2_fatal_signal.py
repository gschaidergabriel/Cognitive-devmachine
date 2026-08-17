import hashlib
import json
from pathlib import Path

import pytest

from clayverse.tier2_signal import (
    TIER2_EXIT_CODE,
    TIER2_SIGNAL_SCHEMA,
    build_tier2_signal,
    request_tier2_replacement,
    write_tier2_signal,
)


def test_recovery_integrity_signal_is_bounded_and_redacted(tmp_path):
    detail = "active turn causal identity diverged before recovery: secret-looking-context"
    target = tmp_path / "termination-log"
    payload = write_tier2_signal("RECOVERY_INTEGRITY_ERROR", detail, path=target)
    parsed = json.loads(payload)

    assert parsed == {
        "action": "REPLACE_FULL_SANDBOX",
        "canonical_state": "UNTRUSTED_UNTIL_RECOVERED",
        "detail_sha256": hashlib.sha256(detail.encode()).hexdigest(),
        "exit_code": 86,
        "reason": "RECOVERY_INTEGRITY_ERROR",
        "replay_external_effects": False,
        "schema": "clayverse.tier2-fatal/v1",
    }
    assert parsed["schema"] == TIER2_SIGNAL_SCHEMA
    assert parsed["exit_code"] == TIER2_EXIT_CODE
    assert detail not in payload
    assert len(target.read_bytes()) < 1024


def test_unknown_tier2_reason_fails_closed():
    with pytest.raises(ValueError, match="unadmitted tier2 reason"):
        build_tier2_signal("GENERIC_PROCESS_ERROR", "boom")


def test_detail_must_be_text():
    with pytest.raises(TypeError, match="must be text"):
        build_tier2_signal("RECOVERY_INTEGRITY_ERROR", object())


def test_exit_86_survives_termination_log_write_failure(monkeypatch, tmp_path):
    def fail_write(self, data):
        raise OSError("unavailable")

    monkeypatch.setattr(Path, "write_bytes", fail_write)
    assert request_tier2_replacement(
        "RECOVERY_INTEGRITY_ERROR", "canonical causal spine split", path=tmp_path / "x"
    ) == TIER2_EXIT_CODE
