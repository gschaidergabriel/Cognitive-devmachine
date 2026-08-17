import json

import pytest

from clayverse import service
from clayverse.recovery import RecoveryIntegrityError


class _FakeDB:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_recovery_integrity_failure_emits_narrow_tier2_exit(monkeypatch, capsys):
    db = _FakeDB()

    def fail(_db):
        raise RecoveryIntegrityError("sensitive internal divergence detail")

    monkeypatch.setattr(service, "recover_incomplete_episodes", fail)

    with pytest.raises(SystemExit) as exc:
        service._recover_or_request_tier2(db)

    assert exc.value.code == service.TIER2_REPLACEMENT_EXIT_CODE == 86
    assert db.closed is True
    stderr = capsys.readouterr().err.strip()
    payload = json.loads(stderr)
    assert payload == {
        "exit_code": 86,
        "reason": "RECOVERY_INTEGRITY_UNTRUSTED",
        "service": "clayverse",
        "status": "tier2_replacement_required",
    }
    assert "sensitive internal divergence detail" not in stderr


def test_generic_startup_failure_is_not_misclassified_as_tier2(monkeypatch):
    db = _FakeDB()

    def fail(_db):
        raise RuntimeError("configuration failure")

    monkeypatch.setattr(service, "recover_incomplete_episodes", fail)

    with pytest.raises(RuntimeError, match="configuration failure"):
        service._recover_or_request_tier2(db)

    assert db.closed is False


def test_successful_recovery_preserves_existing_result(monkeypatch):
    db = _FakeDB()
    expected = {"generation": 7, "active_turns_closed": 1}
    monkeypatch.setattr(service, "recover_incomplete_episodes", lambda _db: expected)

    assert service._recover_or_request_tier2(db) is expected
    assert db.closed is False
