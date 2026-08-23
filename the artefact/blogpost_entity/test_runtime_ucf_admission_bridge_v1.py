#!/usr/bin/env python3
"""Focused source/mechanism regressions for the retained runtime UCF bridge.

These tests deliberately do not mint runtime/model/J-Space/GWT credit. They fence the
single-authority source shape while the full post-turn UCF finalizer remains an explicit
fail-closed evidence debt.
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
RUNTIME_PATH = ROOT / "tools" / "clay_profile_pipeline_runtime.py"
GUARD_PATH = HERE.with_name("check_structured_contract_sync.py")
RUNTIME = RUNTIME_PATH.read_text(encoding="utf-8")
TREE = ast.parse(RUNTIME)

spec = importlib.util.spec_from_file_location("structured_sync_guard", GUARD_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(guard)


def _method_source(name: str) -> str:
    for node in TREE.body:
        if isinstance(node, ast.ClassDef) and node.name == "ProfilePipelineRuntime":
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == name:
                    source = ast.get_source_segment(RUNTIME, child)
                    assert source is not None
                    return source
    raise AssertionError(f"missing method: {name}")


class RuntimeUcfAdmissionBridgeTests(unittest.TestCase):
    def test_effect_bindings_are_real_but_finalizer_debt_keeps_convergence_closed(self):
        report = guard.runtime_effect_contract(RUNTIME)
        self.assertTrue(all(report["required_effect_bindings"].values()))
        downstream = report["downstream_identity"]
        self.assertTrue(downstream["inference_identity_bound"])
        self.assertTrue(downstream["finalizer_terminal_ancestry_bound"])
        self.assertFalse(downstream["finalizer_exposes_distinct_digest"])
        self.assertEqual(downstream["finalizer_forbidden_self_calls"], [])
        self.assertFalse(downstream["semantic_floor"])
        self.assertFalse(report["converged"])

    def test_cognition_schema_bootstrap_is_inside_one_caller_transaction(self):
        source = _method_source("_pipeline_init")
        prepare = source.index("cognition_bootstrap.prepare_connection(db)")
        begin = source.index('db.execute("BEGIN IMMEDIATE")')
        entity = source.index("INSERT OR IGNORE INTO entity_state")
        install = source.index("cognition_bootstrap.install_cognition_schema(db)")
        commit = source.rindex("db.commit()")
        self.assertLess(prepare, begin)
        self.assertLess(begin, entity)
        self.assertLess(entity, install)
        self.assertLess(install, commit)

    def test_admission_reuses_canonical_compositor_read_only(self):
        source = _method_source("_pipeline_cognitive_fabric_admit")
        self.assertIn("pipeline_cognitive_fabric_admission_v1", source)
        self.assertIn("build_pre_inference_admission", source)
        self.assertIn("self._read_only_db", source)
        self.assertNotIn("self._db(", source)
        self.assertNotIn("_pipeline_commit", source)
        self.assertNotIn("_inference_generate", source)

    def test_admission_identity_is_checked_through_inference_gate_and_commit(self):
        inference = _method_source("_inference_generate") + _method_source("_bound_inference_identity")
        gate = _method_source("_pipeline_gate")
        commit = _method_source("_pipeline_commit")
        for source in (inference, gate, commit):
            self.assertIn("inference_packet_digest", source)
            self.assertIn("cognitive_fabric_admission", source)
        finalizer = _method_source("_pipeline_cognitive_fabric_finalize")
        self.assertIn("UCF_FINALIZER_NOT_YET_ADMITTED", finalizer)
        self.assertNotIn("ucf_runtime_receipt_digest", finalizer)


if __name__ == "__main__":
    unittest.main()
