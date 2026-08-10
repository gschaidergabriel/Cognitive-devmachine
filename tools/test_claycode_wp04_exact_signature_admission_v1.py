#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import unittest

from claycode_wp04_exact_signature_admission_v1 import SignatureAdmissionError, admit_exact_signature

SOURCE = '''\
class Runtime:\n    def inspect(self: "Runtime", state: StateRef, limit: int) -> ResultRef:\n        raise RuntimeError("must never execute during signature admission")\n\ndef pure_normalize(text: str) -> NormalizedRef:\n    raise RuntimeError("must never execute during signature admission")\n'''


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def base_request():
    return {
        "target": "runtime.inspect",
        "arity": 2,
        "python_qualname": "Runtime.inspect",
        "implicit_receiver_count": 1,
        "expected_source_sha256": sha(SOURCE),
        "effect_class": "READ_STATE",
        "annotation_to_clay": {"StateRef": "StateRef", "int": "Int", "ResultRef": "ResultRef"},
        "expected_params": [
            {"name": "state", "type_name": "StateRef"},
            {"name": "limit", "type_name": "Int"}
        ],
        "expected_return": "ResultRef",
        "evidence_refs": ["source:fixture:v1", "mapping:fixture:v1"]
    }


class ExactSignatureAdmissionTests(unittest.TestCase):
    def test_positive_exact_static_admission(self):
        out = admit_exact_signature(source_text=SOURCE, request=base_request())
        self.assertEqual(out["call_contract"]["identity"], {"target": "runtime.inspect", "arity": 2})
        self.assertEqual(out["call_contract"]["params"], [
            {"name": "state", "type_name": "StateRef"},
            {"name": "limit", "type_name": "Int"}
        ])
        self.assertEqual(out["call_contract"]["returns"], "ResultRef")
        self.assertFalse(out["execution_admitted"])
        self.assertEqual(out["effect_authority"], "NONE")
        self.assertIsNone(out["call_contract"]["runtime_binding"])

    def test_stale_source_hash_fails_closed(self):
        req = base_request(); req["expected_source_sha256"] = "0" * 64
        with self.assertRaisesRegex(SignatureAdmissionError, "SHA-256 mismatch"):
            admit_exact_signature(source_text=SOURCE, request=req)

    def test_wrong_arity_fails_closed(self):
        req = base_request(); req["arity"] = 1
        with self.assertRaisesRegex(SignatureAdmissionError, "arity mismatch"):
            admit_exact_signature(source_text=SOURCE, request=req)

    def test_unmapped_annotation_fails_closed(self):
        req = base_request(); del req["annotation_to_clay"]["ResultRef"]
        with self.assertRaisesRegex(SignatureAdmissionError, "no explicit Clay type mapping"):
            admit_exact_signature(source_text=SOURCE, request=req)

    def test_missing_annotation_fails_closed(self):
        bad = 'def f(x) -> int:\n    return 1\n'
        req = {
            "target": "f", "arity": 1, "python_qualname": "f", "implicit_receiver_count": 0,
            "expected_source_sha256": sha(bad), "effect_class": "PURE",
            "annotation_to_clay": {"int": "Int"},
            "expected_params": [{"name": "x", "type_name": "Int"}], "expected_return": "Int",
            "evidence_refs": ["fixture"]
        }
        with self.assertRaisesRegex(SignatureAdmissionError, "lacks annotation"):
            admit_exact_signature(source_text=bad, request=req)

    def test_variadic_fails_closed(self):
        bad = 'def f(*xs: int) -> int:\n    return 1\n'
        req = {
            "target": "f", "arity": 1, "python_qualname": "f", "implicit_receiver_count": 0,
            "expected_source_sha256": sha(bad), "effect_class": "PURE",
            "annotation_to_clay": {"int": "Int"},
            "expected_params": [{"name": "xs", "type_name": "Int"}], "expected_return": "Int",
            "evidence_refs": ["fixture"]
        }
        with self.assertRaisesRegex(SignatureAdmissionError, "variadic"):
            admit_exact_signature(source_text=bad, request=req)

    def test_defaulted_parameter_fails_closed(self):
        bad = 'def f(x: int = 1) -> int:\n    return x\n'
        req = {
            "target": "f", "arity": 1, "python_qualname": "f", "implicit_receiver_count": 0,
            "expected_source_sha256": sha(bad), "effect_class": "PURE",
            "annotation_to_clay": {"int": "Int"},
            "expected_params": [{"name": "x", "type_name": "Int"}], "expected_return": "Int",
            "evidence_refs": ["fixture"]
        }
        with self.assertRaisesRegex(SignatureAdmissionError, "defaulted"):
            admit_exact_signature(source_text=bad, request=req)

    def test_exact_symbol_only_no_suffix_match(self):
        req = base_request(); req["python_qualname"] = "inspect"
        with self.assertRaisesRegex(SignatureAdmissionError, "exact qualified symbol not found"):
            admit_exact_signature(source_text=SOURCE, request=req)

    def test_runtime_type_mapping_cannot_override_declared_clay_contract(self):
        req = base_request(); req["annotation_to_clay"]["int"] = "Count"
        with self.assertRaisesRegex(SignatureAdmissionError, "parameter contract mismatch"):
            admit_exact_signature(source_text=SOURCE, request=req)

    def test_wrong_declared_return_fails_closed(self):
        req = base_request(); req["expected_return"] = "OtherResult"
        with self.assertRaisesRegex(SignatureAdmissionError, "return contract mismatch"):
            admit_exact_signature(source_text=SOURCE, request=req)

    def test_contract_hash_stable_across_evidence_order_and_duplicates(self):
        a = admit_exact_signature(source_text=SOURCE, request=base_request())
        req = base_request(); req["evidence_refs"] = ["mapping:fixture:v1", "source:fixture:v1", "mapping:fixture:v1"]
        b = admit_exact_signature(source_text=SOURCE, request=req)
        self.assertEqual(a["contract_semantic_hash"], b["contract_semantic_hash"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
