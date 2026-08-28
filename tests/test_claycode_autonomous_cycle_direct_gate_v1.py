from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "tools/claycode_autonomous_cycle.py"


def test_direct_entrypoint_is_provider_free_before_gate():
    source = ENTRY.read_text(encoding="utf-8")
    assert "rae_secret_loader" not in source
    assert "nvidia_inference" not in source
    assert "mistral_inference" not in source
    assert "check_inbox" in source
    assert "claycode_autonomous_cycle_legacy_impl.py" in source


def test_direct_cli_hard_off_skips_before_provider_boundary():
    proc = subprocess.run(
        [sys.executable, str(ENTRY)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["status"] == "SKIPPED_PROVIDER_AUTHORITY"
    assert payload["entrypoint"] == "DIRECT_CLI_GATED"
    assert payload["provider_calls"] == 0
    assert payload["secret_lookups"] == 0
    assert payload["authority"]["admitted"] is False
