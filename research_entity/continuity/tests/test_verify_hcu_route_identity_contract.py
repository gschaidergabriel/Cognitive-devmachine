import importlib.util
import tempfile
import textwrap
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "verify_hcu_route_identity_contract.py"
_spec = importlib.util.spec_from_file_location("verify_hcu_route_identity_contract", TOOL)
assert _spec and _spec.loader
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


OLD_ALIASING_ROUTER = r'''
import hashlib, json
class D:
    def __init__(self, digest): self.decision_sha256 = digest
def route_event(event, *, current_generation):
    payload = {"generation": event["entity_generation"], "lanes": ["world", "critic", "zero_model"]}
    return D(hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest())
'''

BOUND_ROUTER = r'''
import hashlib, json
class D:
    def __init__(self, digest): self.decision_sha256 = digest
def route_event(event, *, current_generation):
    engine = event.get("resolved_cognition_engine")
    if not isinstance(engine, dict): raise ValueError("ENGINE_REQUIRED")
    if engine.get("engine_class") != "HCU_LOCAL_08B": raise ValueError("ENGINE_CLASS_REJECTED")
    payload = {"event": event, "engine": engine, "lanes": ["world", "critic", "zero_model"]}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return D(hashlib.sha256(raw).hexdigest())
'''


class HcuRouteIdentityVerifierTests(unittest.TestCase):
    def _verify_source(self, source: str):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "router.py"
            path.write_text(textwrap.dedent(source), encoding="utf-8")
            return mod.verify(path)

    def test_aliasing_router_fails(self):
        result = self._verify_source(OLD_ALIASING_ROUTER)
        self.assertEqual(result["status"], "FAIL")
        self.assertFalse(result["checks"]["different_causal_event_cannot_alias"])
        self.assertFalse(result["checks"]["different_resolved_engine_cannot_alias"])
        self.assertFalse(result["checks"]["model_route_requires_resolved_engine_identity"])
        self.assertFalse(result["checks"]["external_engine_class_fails_closed"])

    def test_event_and_engine_bound_router_passes(self):
        result = self._verify_source(BOUND_ROUTER)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(all(result["checks"].values()))


if __name__ == "__main__":
    unittest.main()
