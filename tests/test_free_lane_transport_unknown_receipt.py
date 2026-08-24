from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_transport_exception_emits_unknown_outcome_receipt_before_reraise() -> None:
    """The provider-call boundary must remain receipt-complete even without HTTP response."""
    code = r'''
import sys
from pathlib import Path
from types import SimpleNamespace

root = Path.cwd()
sys.path.insert(0, str(root / "tools"))
import run_6000_free_swarm_v3 as v3

binding = {
    "ok": True,
    "observed_at": "2026-08-24T00:00:00+00:00",
    "admission_epoch": "8.70",
    "admission_digest": "a" * 64,
    "economic_provenance_digest": "b" * 64,
    "evidence": {"kind": "TEST_ZERO_COST_BINDING"},
}
receipts = []

v3.current_lane_binding = lambda *args, **kwargs: binding
v3.binding_still_current = lambda candidate: candidate is binding
v3.emit_execution_receipt = lambda **kwargs: receipts.append(kwargs)

def transport_timeout(*args, **kwargs):
    raise TimeoutError("SENTINEL_SECRET_MUST_NOT_ENTER_RECEIPT")

v3._ORIGINAL_REQUEST = transport_timeout
spec = SimpleNamespace(
    name="openrouter",
    endpoint="https://openrouter.ai/api/v1/chat/completions",
)

try:
    v3.gated_request_chat(spec, "test-secret-key", "openrouter/free", "prompt", 16, 1.0)
except TimeoutError as exc:
    assert str(exc) == "SENTINEL_SECRET_MUST_NOT_ENTER_RECEIPT"
else:
    raise AssertionError("transport exception must be re-raised")

assert len(receipts) == 1
receipt = receipts[0]
assert receipt["http_status"] == "TRANSPORT_EXCEPTION_UNKNOWN_OUTCOME"
assert receipt["request_id"] is None
assert receipt["usage"] == {}
assert receipt["binding"] is binding
assert receipt["binding_stable_after_call"] is True
assert receipt["result_digest"]
assert "SENTINEL_SECRET" not in receipt["result_digest"]
'''
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
