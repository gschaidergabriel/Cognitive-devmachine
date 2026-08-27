import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_authority_launcher_v1.py"


def _load_launcher():
    spec = importlib.util.spec_from_file_location("frankenstein_authority_launcher_v1", LAUNCHER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_current_hard_off_blocks_before_target_or_provider_boundary():
    proc = subprocess.run(
        [sys.executable, str(LAUNCHER), "bauleiter", "--", "--once"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 77, proc.stdout + proc.stderr
    row = json.loads(proc.stdout.strip().splitlines()[-1])
    assert row["schema"] == "FRANKENSTEIN_AUTHORITY_LAUNCH_RECEIPT/v1"
    assert row["admitted"] is False
    assert row["provider_calls"] == 0
    assert row["secret_lookups"] == 0
    assert row["target_imports"] == 0
    assert row["target_processes_started"] == 0
    assert row["required_caller_behavior"] == (
        "STOP_BEFORE_SECRET_LOOKUP_PROVIDER_IMPORT_NETWORK_OR_AIDER_FALLBACK"
    )


def test_launcher_source_has_no_provider_or_network_imports():
    text = LAUNCHER.read_text(encoding="utf-8").lower()
    forbidden_imports = [
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "import openai",
        "from openai",
        "import together",
        "from together",
        "import mistralai",
        "from mistralai",
        "import groq",
        "from groq",
        "import llm",
        "from llm",
    ]
    for token in forbidden_imports:
        assert token not in text


def test_denied_gate_never_executes_target(monkeypatch, capsys):
    launcher = _load_launcher()
    order = []

    def fake_gate():
        order.append("gate")
        return 77, {"admitted": False, "reason": "TEST_HARD_OFF"}, ""

    def forbidden_exec(mode, args):
        order.append("exec")
        raise AssertionError("target execution must not occur after a denied gate")

    monkeypatch.setattr(launcher, "_run_gate", fake_gate)
    monkeypatch.setattr(launcher, "_exec_target", forbidden_exec)
    assert launcher.launch("bugfix", []) == 77
    assert order == ["gate"]
    row = json.loads(capsys.readouterr().out.strip())
    assert row["provider_calls"] == 0
    assert row["secret_lookups"] == 0
    assert row["target_imports"] == 0
    assert row["target_processes_started"] == 0


def test_admitted_gate_reaches_target_only_after_gate(monkeypatch, capsys):
    launcher = _load_launcher()
    order = []

    def fake_gate():
        order.append("gate")
        return 0, {
            "admitted": True,
            "reason": "TEST_EXPLICIT_ADMISSION",
            "schema_version": "99.0",
            "runtime_provider_authority": "TEST_ONLY",
        }, ""

    def fake_exec(mode, args):
        order.append(("exec", mode, list(args)))

    monkeypatch.setattr(launcher, "_run_gate", fake_gate)
    monkeypatch.setattr(launcher, "_exec_target", fake_exec)
    assert launcher.launch("bauleiter", ["--once"]) == 0
    assert order == ["gate", ("exec", "bauleiter", ["--once"])]
    row = json.loads(capsys.readouterr().out.strip())
    assert row["admitted"] is True
    assert row["boundary"] == "TARGET_EXECUTION_ALLOWED_ONLY_AFTER_THIS_GATE"
