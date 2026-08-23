from types import SimpleNamespace

from clayverse.adapters import ClaudeCodeInference


def test_claude_code_reason_injects_current_owner_identity_contract(monkeypatch, tmp_path):
    captured = {}

    def fake_run(args, **kwargs):
        captured["args"] = list(args)
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            returncode=0,
            stdout='{"structured_output":{"text":"ok","effect":null}}',
            stderr="",
        )

    monkeypatch.setattr("clayverse.adapters.subprocess.run", fake_run)
    out = ClaudeCodeInference(binary="claude", cwd=str(tmp_path), timeout=1).reason({}, "probe")

    args = captured["args"]
    system = args[args.index("--append-system-prompt") + 1]
    env = captured["kwargs"]["env"]

    assert out == {"text": "ok", "selection": "respond", "effect": None}
    assert "EntityOS / Mini Entity" in system
    assert "targeted candidate-inference engine" in system
    assert "You are not Zero" in system
    assert "MiniUnifiedDB" in system
    assert "deterministic grammar/type/schema/truth/authority/generation/effect gates" in system
    assert "EffectGate alone decides whether execution is admitted" in system

    assert "ClayVerse" not in system
    assert "persistent central entity shared by authenticated users" not in system
    assert "ClayGraph" not in system

    assert captured["kwargs"]["shell"] is False
    assert args[args.index("--tools") + 1] == ""
    assert "--no-session-persistence" in args
    assert env["CLAUDE_CODE_SKIP_PROMPT_HISTORY"] == "1"
    assert env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] == "1"
    assert env["CLAUDE_CODE_DISABLE_CLAUDE_MDS"] == "1"
