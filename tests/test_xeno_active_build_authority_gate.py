import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Load the real live-authority helper under the import name expected by the Xeno controller.
HELPER_SPEC = importlib.util.spec_from_file_location(
    "xeno_current_authority_protocol",
    ROOT / "tools/xeno_current_authority_protocol.py",
)
HELPER = importlib.util.module_from_spec(HELPER_SPEC)
assert HELPER_SPEC and HELPER_SPEC.loader
HELPER_SPEC.loader.exec_module(HELPER)
sys.modules["xeno_current_authority_protocol"] = HELPER

# Isolate the controller from the real provider fabric. These stubs never perform network I/O.
economic = types.ModuleType("run_6000_free_swarm_v3")
base = types.SimpleNamespace()
base.PROTOCOL_BEGIN = HELPER.PROTOCOL_BEGIN
base.DEFAULT_ROLES = []


def economic_request(spec, key, model, prompt, max_tokens, timeout):
    return 200, {}, {"ok": True}


class Runtime:
    pass


def economic_next(runtime):
    return ("opaque-key", "model")


Runtime.next_key_model = economic_next
base.request_chat = economic_request
fabric = types.SimpleNamespace(
    base=base,
    FastProviderRuntime=Runtime,
    _PREV_PROMPT=lambda protocol, role, task, state, serial: protocol + "\nBASE",
    FALLBACK_SHARDS=[],
)
economic.fabric = fabric
economic.gated_request_chat = economic_request
economic.gated_next_key_model = economic_next
sys.modules["run_6000_free_swarm_v3"] = economic

SPEC = importlib.util.spec_from_file_location(
    "run_xeno_active_build_swarm",
    ROOT / "tools/run_xeno_active_build_swarm.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)


class XenoAuthorityTOCTOUTests(unittest.TestCase):
    def setUp(self):
        self.orig_snapshot = MOD._operational_authority_snapshot
        self.orig_start_digest = MOD._START_AUTHORITY_DIGEST
        self.orig_start_protocol = MOD._START_PROTOCOL
        MOD._START_AUTHORITY_DIGEST = "bound-digest"
        MOD._START_PROTOCOL = "BOUND_PROTOCOL"

    def tearDown(self):
        MOD._operational_authority_snapshot = self.orig_snapshot
        MOD._START_AUTHORITY_DIGEST = self.orig_start_digest
        MOD._START_PROTOCOL = self.orig_start_protocol

    def test_matching_snapshot_allows_reservation(self):
        MOD._operational_authority_snapshot = lambda protocol=None: ("P", "bound-digest")
        self.assertEqual(MOD.xeno_gated_next_key_model(Runtime()), ("opaque-key", "model"))

    def test_authority_drift_blocks_before_reservation(self):
        MOD._operational_authority_snapshot = lambda protocol=None: ("P", "successor-digest")
        self.assertIsNone(MOD.xeno_gated_next_key_model(Runtime()))

    def test_authority_drift_blocks_before_network_delegate(self):
        MOD._operational_authority_snapshot = lambda protocol=None: ("P", "successor-digest")
        status, _, body = MOD.xeno_gated_request_chat(None, "secret", "model", "BOUND_PROTOCOL\nTASK", 1, 1.0)
        self.assertEqual(status, 460)
        self.assertEqual(body["error"], "XENO_OPERATIONAL_AUTHORITY_DRIFT_FAIL_CLOSED_BEFORE_NETWORK")

    def test_prompt_must_bind_start_authority(self):
        MOD._operational_authority_snapshot = lambda protocol=None: ("P", "bound-digest")
        status, _, body = MOD.xeno_gated_request_chat(None, "secret", "model", "OTHER_PROTOCOL\nTASK", 1, 1.0)
        self.assertEqual(status, 460)
        self.assertEqual(body["error"], "XENO_WORKER_PROTOCOL_NOT_BOUND_TO_START_AUTHORITY_FAIL_CLOSED_BEFORE_NETWORK")

    def test_matching_authority_and_prompt_delegate_to_economic_gate(self):
        MOD._operational_authority_snapshot = lambda protocol=None: ("P", "bound-digest")
        status, _, body = MOD.xeno_gated_request_chat(None, "secret", "model", "BOUND_PROTOCOL\nTASK", 1, 1.0)
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])


if __name__ == "__main__":
    unittest.main()
