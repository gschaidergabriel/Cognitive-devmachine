from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BLOGPOST = HERE.parent
CONTRACT_PATH = HERE / "NATIVE_PROFILE_V2_PARITY_CONTRACT.json"
PROFILE_PATH = BLOGPOST / "presets" / "zero_blog.json"
PIPELINE_PATH = BLOGPOST / "BLOGPOST_ENTITY.clay"
REFERENCE_RUNTIME_PATH = ROOT / "tools" / "clay_profile_pipeline_runtime.py"
NATIVE_RUN_PATH = HERE / "mini_entity_part04.inc"


def walk_expression(node: Any, ops: set[str], aggregates: set[str], refs: set[str]) -> None:
    if isinstance(node, dict):
        op = node.get("op")
        if isinstance(op, str):
            ops.add(op)
        ref = node.get("ref")
        if isinstance(ref, str):
            refs.add(ref)
        for aggregate in ("count_where", "sum_where"):
            if aggregate in node:
                aggregates.add(aggregate)
                spec = node.get(aggregate)
                if isinstance(spec, dict) and isinstance(spec.get("ref"), str):
                    refs.add(spec["ref"])
        for value in node.values():
            walk_expression(value, ops, aggregates, refs)
    elif isinstance(node, list):
        for value in node:
            walk_expression(value, ops, aggregates, refs)


def ref_namespace(ref: str) -> str:
    return ref.split(".", 1)[0]


class NativeProfileV2ParityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        cls.pipeline = PIPELINE_PATH.read_text(encoding="utf-8")
        cls.reference_runtime = REFERENCE_RUNTIME_PATH.read_text(encoding="utf-8")
        cls.native_run = NATIVE_RUN_PATH.read_text(encoding="utf-8")

    def test_contract_is_bound_to_current_canonical_v2_surface(self) -> None:
        self.assertEqual(self.profile["schema"], self.contract["canonical_profile_schema"])
        self.assertEqual(self.contract["canonical_profile_schema"], "clay-pipeline-profile/v2")

        source_adapters = sorted({str(spec["adapter"]) for spec in self.profile.get("sources", [])})
        probe_adapters = sorted({str(spec["adapter"]) for spec in self.profile.get("canonical_probes", [])})
        self.assertEqual(source_adapters, self.contract["required_source_adapters_from_shipped_v2"])
        self.assertEqual(probe_adapters, self.contract["required_probe_adapters_from_shipped_v2"])

        ops: set[str] = set()
        aggregates: set[str] = set()
        refs: set[str] = set()
        for metric in self.profile.get("state_metrics", []):
            walk_expression(metric, ops, aggregates, refs)
        self.assertEqual(sorted(ops), self.contract["required_expression_ops_from_shipped_v2"])
        self.assertEqual(sorted(aggregates), self.contract["required_expression_aggregates_from_shipped_v2"])
        namespaces = sorted({ref_namespace(ref) for ref in refs if "." in ref})
        self.assertEqual(namespaces, self.contract["required_expression_ref_namespaces_from_shipped_v2"])

    def test_contract_binds_canonical_phase_order(self) -> None:
        positions: list[int] = []
        for phase in self.contract["required_pipeline_phases"]:
            pos = self.pipeline.find(f'"{phase}"')
            self.assertNotEqual(pos, -1, msg=f"canonical pipeline phase missing: {phase}")
            positions.append(pos)
        self.assertEqual(positions, sorted(positions), msg="canonical pipeline phase order changed")

    def test_reference_runtime_effect_surface_is_fail_closed_until_current_names_match(self) -> None:
        required = self.contract["required_reference_effect_surface"]
        self.assertEqual(required, self.contract["required_pipeline_phases"])
        missing = [name for name in required if f'"{name}"' not in self.reference_runtime]
        legacy = self.contract["legacy_reference_effects_to_deauthorize"]
        stale = [name for name in legacy if f'"{name}"' in self.reference_runtime]
        gap = self.contract["reference_runtime_effect_surface"]

        if missing or stale:
            self.assertEqual(gap["status"], "FAIL_CLOSED_MISMATCH")
            self.assertEqual(missing, gap["missing_current_effects"])
            self.assertEqual(stale, gap["stale_current_effects"])
            self.assertEqual(self.contract["admission"]["status"], "FAIL_CLOSED_UNTIL_EXACT_PARITY")
            self.assertIsNone(self.contract["admission"]["runtime_receipt"])
        else:
            self.assertEqual(gap["status"], "PARITY")
            self.assertEqual(gap["missing_current_effects"], [])
            self.assertEqual(gap["stale_current_effects"], [])

    def test_reference_runtime_still_contains_required_compile_and_gate_mechanisms(self) -> None:
        required_tokens = (
            "def _pipeline_collect",
            "def _pipeline_compile",
            "def _pipeline_build_prompt",
            "def _pipeline_gate",
            "def _pipeline_commit",
            'if "count_where" in expr',
            'if "sum_where" in expr',
            '"sources": collected["sources"]',
            '"sensors": collected["sensors"]',
            '"probes": collected["probes"]',
            '"ALLOWED_EVIDENCE_REFS"',
            '"CANONICAL_STATE_HASH"',
            '"PACKET_HASH"',
            '"SECTION_WITHOUT_EVIDENCE"',
            '"UNKNOWN_EVIDENCE_REF"',
            '"UNVERIFIED_STATE_CLAIM"',
            '"STATE_CLAIM_OVERSHOOT"',
            '"STATE_CLAIM_WITHOUT_METRIC_EVIDENCE"',
        )
        for token in required_tokens:
            self.assertIn(token, self.reference_runtime, msg=f"reference contract token missing: {token}")

    def test_fail_closed_guard_remains_until_exact_parity_receipt_exists(self) -> None:
        admission = self.contract["admission"]
        blocker = admission["blocker"]
        if admission["status"] == "FAIL_CLOSED_UNTIL_EXACT_PARITY":
            self.assertIsNone(admission["runtime_receipt"])
            self.assertIn(blocker, self.native_run)
            run_start = self.native_run.index("static void cmd_run")
            run_body = self.native_run[run_start:]
            self.assertLess(
                run_body.index("native_semantic_admission_blocker(profile)"),
                run_body.index("collect_packet(source_path)"),
                msg="v2 admission blocker must run before collection/inference",
            )
        else:
            receipt = admission.get("runtime_receipt")
            self.assertIsInstance(receipt, str)
            self.assertTrue(receipt)
            self.assertTrue((ROOT / receipt).is_file(), msg="active v2 admission requires a bound runtime receipt")
            self.assertNotIn(blocker, self.native_run)

    def test_partial_donor_is_explicitly_non_promotable_as_whole_branch(self) -> None:
        rejected = self.contract["known_rejected_partial_candidate"]
        self.assertEqual(rejected["pull_request"], 851)
        reason = rejected["reason"]
        self.assertIn("count_where/sum_where", reason)
        self.assertIn("collector/probe topology", reason)


if __name__ == "__main__":
    unittest.main()
