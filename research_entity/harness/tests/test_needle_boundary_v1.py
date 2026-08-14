import copy
import random
import unittest

from research_entity.harness.reference.needle_boundary_v1 import (
    DecodeRejected,
    ProjectionError,
    build_projection,
    validate_route,
)

SRC = "6fdddb874dd6f46dabeea88d0bf239fc4a2474c4"
H64 = "a" * 64


def caps():
    return [
        {
            "capability_id": "cap.weather.current",
            "name": "get-weather",
            "available": True,
            "locked": False,
            "parameters": {
                "location": {"type": "string", "required": True},
                "units": {"type": "string", "enum": ["c", "f"]},
            },
        },
        {
            "capability_id": "cap.light.set",
            "name": "Set Light",
            "available": True,
            "locked": False,
            "parameters": {
                "level": {"type": "integer", "required": True, "minimum": 0, "maximum": 100}
            },
        },
        {
            "capability_id": "cap.secret.delete",
            "name": "delete-all",
            "available": True,
            "locked": True,
            "parameters": {},
        },
    ]


def prov(projection):
    return {
        "source_commit": SRC,
        "model_hash": H64,
        "tokenizer_hash": "b" * 64,
        "registry_hash": projection["registry_hash"],
        "projection_schema": projection["projection_schema"],
        "input_hash": "c" * 64,
        "language_path": "de_direct",
    }


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.p = build_projection(caps(), source_commit=SRC)
        self.receipt = {"status": "CONSTRAINED_OK", "constraint_exhausted": False, "off_trie": False}

    def route(self, raw, **kwargs):
        return validate_route(raw_json=raw, projection=self.p, decoder_receipt=self.receipt, provenance=prov(self.p), **kwargs)

    def test_valid_route_never_mints_authority(self):
        out = self.route('{"tool":"get_weather","arguments":{"location":"Graz","units":"c"}}')
        self.assertEqual(out["capability_id"], "cap.weather.current")
        self.assertEqual(out["authority"], "NONE")
        self.assertIsNone(out["effect_permit"])
        self.assertFalse(out["effect_commit_allowed"])

    def test_projection_is_order_invariant(self):
        base_hash = self.p["registry_hash"]
        base = caps()
        for seed in range(100):
            items = copy.deepcopy(base)
            random.Random(seed).shuffle(items)
            self.assertEqual(build_projection(items, source_commit=SRC)["registry_hash"], base_hash)

    def test_locked_capability_is_omitted_and_unroutable(self):
        self.assertNotIn("delete_all", self.p["reverse_map"])
        with self.assertRaises(DecodeRejected):
            self.route('{"tool":"delete_all","arguments":{}}')

    def test_normalization_collision_rejected_before_inference(self):
        c = caps()[:1] + [{"capability_id": "cap.other", "name": "get weather", "parameters": {}}]
        with self.assertRaises(ProjectionError):
            build_projection(c, source_commit=SRC)

    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(DecodeRejected):
            self.route('{"tool":"get_weather","tool":"set_light","arguments":{}}')

    def test_missing_required_rejected(self):
        with self.assertRaises(DecodeRejected):
            self.route('{"tool":"get_weather","arguments":{"units":"c"}}')

    def test_wrong_type_and_range_rejected(self):
        with self.assertRaises(DecodeRejected):
            self.route('{"tool":"set_light","arguments":{"level":"100"}}')
        with self.assertRaises(DecodeRejected):
            self.route('{"tool":"set_light","arguments":{"level":101}}')

    def test_unknown_argument_rejected(self):
        with self.assertRaises(DecodeRejected):
            self.route('{"tool":"get_weather","arguments":{"location":"Graz","evil":1}}')

    def test_decoder_fail_open_signals_abstain(self):
        for field in ("constraint_exhausted", "off_trie"):
            receipt = dict(self.receipt)
            receipt[field] = True
            with self.assertRaises(DecodeRejected):
                validate_route(
                    raw_json='{"tool":"get_weather","arguments":{"location":"Graz"}}',
                    projection=self.p,
                    decoder_receipt=receipt,
                    provenance=prov(self.p),
                )

    def test_registry_provenance_mismatch_rejected(self):
        bad = prov(self.p)
        bad["registry_hash"] = "d" * 64
        with self.assertRaises(DecodeRejected):
            validate_route(
                raw_json='{"tool":"get_weather","arguments":{"location":"Graz"}}',
                projection=self.p,
                decoder_receipt=self.receipt,
                provenance=bad,
            )

    def test_unknown_top_field_rejected(self):
        with self.assertRaises(DecodeRejected):
            self.route('{"tool":"get_weather","arguments":{"location":"Graz"},"authority":"yes"}')

    def test_deterministic_semantic_hash(self):
        a = self.route('{"tool":"get_weather","arguments":{"location":"Graz","units":"c"}}')
        b = self.route('{ "arguments" : { "units" : "c", "location" : "Graz" }, "tool" : "get_weather" }')
        self.assertEqual(a["route_semantic_hash"], b["route_semantic_hash"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
