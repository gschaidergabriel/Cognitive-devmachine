from __future__ import annotations

from pathlib import Path

from clayverse import terminal_gateway


class _Manager:
    def __init__(self, *, dead_user: str | None = None, bad_policy_user: str | None = None):
        self.dead_user = dead_user
        self.bad_policy_user = bad_policy_user
        self.calls = []

    def binding(self, user_id: str):
        self.calls.append(("binding", user_id))
        return user_id

    def _has_session(self, binding):
        self.calls.append(("has_session", binding))
        return binding != self.dead_user

    def _assert_tmux_server_policy(self, binding):
        self.calls.append(("policy", binding))
        if binding == self.bad_policy_user:
            raise RuntimeError("policy mismatch")


def test_terminal_readiness_reuses_manager_owned_liveness_and_policy_attestation():
    manager = _Manager()
    assert terminal_gateway._terminal_sessions_ready(manager) is True
    assert manager.calls == [
        ("binding", "gabriel"),
        ("has_session", "gabriel"),
        ("policy", "gabriel"),
        ("binding", "andreas"),
        ("has_session", "andreas"),
        ("policy", "andreas"),
    ]


def test_terminal_readiness_fails_closed_before_policy_probe_for_missing_session():
    manager = _Manager(dead_user="andreas")
    assert terminal_gateway._terminal_sessions_ready(manager) is False
    assert ("policy", "andreas") not in manager.calls


def test_runtime_readiness_fails_closed_on_policy_attestation_error(tmp_path, monkeypatch):
    class _DB:
        def execute(self, sql):
            if "schema_version" in sql:
                return _Rows([("6",)])
            if "entity_generation" in sql:
                return _Rows([("1",)])
            if "COUNT(*)" in sql:
                return _Rows([(2,)])
            if "FROM sessions" in sql:
                return _Rows([
                    {"user_id": "gabriel", "terminal_name": "clay-gabriel", "generation": 1},
                    {"user_id": "andreas", "terminal_name": "clay-andreas", "generation": 1},
                ])
            raise AssertionError(sql)

    class _Rows:
        def __init__(self, rows):
            self.rows = rows
        def fetchone(self):
            return self.rows[0] if self.rows else None
        def fetchall(self):
            return self.rows

    db = type("DBWrap", (), {"db": _DB()})()
    names = {"gabriel": "clay-gabriel", "andreas": "clay-andreas"}
    monkeypatch.setattr(terminal_gateway, "CANONICAL_TERMINAL_NAMES", names)
    assert terminal_gateway._runtime_ready(db, _Manager(bad_policy_user="andreas")) is False


def test_readyz_runs_combined_state_and_terminal_probe_off_event_loop():
    root = Path(__file__).parents[1]
    source = (root / "clayverse" / "terminal_gateway.py").read_text()
    assert "def _runtime_ready(db: UnifiedDB, terminals: TerminalSessionManager)" in source
    assert "return state_ready and _terminal_sessions_ready(terminals)" in source
    assert "ready = await asyncio.to_thread(_runtime_ready, db, terminals)" in source
    assert "subprocess.run(" not in source
