from clayverse import service
from clayverse.recovery import RecoveryIntegrityError


class _DummyDB:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_recovery_integrity_error_returns_reserved_tier2_exit(monkeypatch, tmp_path):
    db = _DummyDB()
    observed = {}

    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(tmp_path))
    monkeypatch.setattr(service, "UnifiedDB", lambda _path: db)
    monkeypatch.setattr(service, "IdentityRouter", lambda _db, _mapping: None)

    def fail_recovery(_db):
        raise RecoveryIntegrityError("canonical causal spine split: do-not-print-raw")

    monkeypatch.setattr(service, "recover_incomplete_episodes", fail_recovery)

    def request(reason, detail):
        observed["reason"] = reason
        observed["detail"] = detail
        return 86

    monkeypatch.setattr(service, "request_tier2_replacement", request)

    assert service.main() == 86
    assert db.closed is True
    assert observed == {
        "reason": "RECOVERY_INTEGRITY_ERROR",
        "detail": "canonical causal spine split: do-not-print-raw",
    }
