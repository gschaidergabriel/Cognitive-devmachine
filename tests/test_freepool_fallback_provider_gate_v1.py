import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "tools/freepool_fallback_provider_gate_v1.py"


def test_current_hard_off_blocks_before_provider_or_secret_boundary():
    proc = subprocess.run([sys.executable, str(GATE)], cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 77, proc.stdout + proc.stderr
    row = json.loads(proc.stdout)
    assert row["schema"] == "FREEPOOL_FALLBACK_PROVIDER_GATE/v1"
    assert row["admitted"] is False
    assert row["provider_calls_before_gate"] == 0
    assert row["secret_lookups_before_gate"] == 0
    assert row["required_caller_behavior"] == "STOP_BEFORE_SECRET_LOOKUP_PROVIDER_IMPORT_NETWORK_OR_AIDER_FALLBACK"


def test_gate_source_has_no_provider_sdk_or_network_imports():
    text = GATE.read_text(encoding="utf-8")
    forbidden = ["requests", "httpx", "openai", "together", "mistralai", "groq", "nvidia"]
    lowered = text.lower()
    for token in forbidden:
        # NVIDIA appears only in the external-path explanation if ever added later; no SDK/network imports are allowed.
        assert f"import {token}" not in lowered
        assert f"from {token}" not in lowered
