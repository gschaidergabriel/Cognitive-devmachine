import sys

from clayverse import service


class FakeDB:
    def __init__(self):
        self.checkpoints = []
        self.closed = False

    def checkpoint(self, label):
        self.checkpoints.append(label)
        return f"cp-{label}", f"hash-{label}"

    def session_generation(self, session_id):
        assert session_id in {"session:gabriel", "session:andreas"}
        return 7

    def entity_generation(self):
        return 7

    def close(self):
        self.closed = True


class FakeClaudeStatus:
    def as_dict(self):
        return {"available": True, "version": "test"}


class FakeBinding:
    def __init__(self, user_id, home):
        self.session_id = f"session:{user_id}"
        self.tmux_name = f"clayverse-{user_id}"
        self.home = home / user_id


class FakeTerminals:
    def __init__(self, state_root, workspace):
        self.state_root = state_root
        self.workspace = workspace
        self.ensure_calls = []

    def ensure(self, user_id):
        self.ensure_calls.append(user_id)
        return FakeBinding(user_id, __import__("pathlib").Path(self.state_root) / "users")


def test_service_runs_current_uvicorn_terminal_app_and_closes_db(monkeypatch, tmp_path):
    db = FakeDB()
    graph_rebuilds = []
    recovery = {"generation": 7, "active_turns_closed": 0}
    app = object()
    verifier = object()
    terminal_manager = FakeTerminals(str(tmp_path / "state"), str(tmp_path / "workspace"))
    app_calls = []
    uvicorn_calls = []

    monkeypatch.setattr(service, "UnifiedDB", lambda _path: db)
    monkeypatch.setattr(service, "IdentityRouter", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(
        service,
        "ClayGraphProjection",
        lambda *_args, **_kwargs: type("G", (), {"rebuild": lambda self: graph_rebuilds.append("rebuild")})(),
    )
    monkeypatch.setattr(service, "recover_incomplete_episodes", lambda _db: recovery)
    monkeypatch.setattr(service, "_clerk_map", lambda: {"subject-g": "gabriel", "subject-a": "andreas"})
    monkeypatch.setattr(service, "_web_config", lambda: ("pk_test_example", "https://clerk.example"))
    monkeypatch.setattr(service.ClerkConfig, "from_env", lambda: object())
    monkeypatch.setattr(service, "ClerkTokenVerifier", lambda _cfg: verifier)
    monkeypatch.setattr(service, "claude_readiness", lambda required: FakeClaudeStatus())
    monkeypatch.setattr(
        service,
        "_entityos_config",
        lambda: (None, {"staged": True, "verified": True, "execution_enabled": False}),
    )
    monkeypatch.setattr(service, "TerminalSessionManager", lambda *_args, **_kwargs: terminal_manager)

    def fake_create_terminal_app(**kwargs):
        app_calls.append(kwargs)
        return app

    monkeypatch.setattr(service, "create_terminal_app", fake_create_terminal_app)

    import uvicorn

    monkeypatch.setattr(uvicorn, "run", lambda supplied_app, **kwargs: uvicorn_calls.append((supplied_app, kwargs)))
    monkeypatch.setattr(sys, "argv", ["clayverse.service"])
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(tmp_path / "state"))
    monkeypatch.setenv("CLAYVERSE_WORKSPACE", str(tmp_path / "workspace"))
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "43210")

    assert service.main() == 0

    assert graph_rebuilds == ["rebuild"]
    assert terminal_manager.ensure_calls == ["gabriel", "andreas"]
    assert len(app_calls) == 1
    assert app_calls[0]["db"] is db
    assert app_calls[0]["clerk_map"] == {"subject-g": "gabriel", "subject-a": "andreas"}
    assert app_calls[0]["verifier"] is verifier
    assert app_calls[0]["publishable_key"] == "pk_test_example"
    assert app_calls[0]["frontend_api_url"] == "https://clerk.example"

    assert uvicorn_calls == [
        (
            app,
            {
                "host": "127.0.0.1",
                "port": 43210,
                "workers": 1,
                "access_log": False,
                "ws_max_size": service._PTY_INPUT_FRAME_MAX_BYTES,
            },
        )
    ]
    assert db.checkpoints == ["boot", "shutdown"]
    assert db.closed is True
