import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from hcu_grid_manifest_v1 import HCUManifestError, UNRESOLVED, plan_shared_weight_capacity, validate_manifest


def unresolved_manifest():
    return {
        "schema": "mini-entity-hcu-grid-manifest/v1",
        "grid_id": "mini-entity-hcu-kvm4-v1",
        "entity_count": 1,
        "state_authority": "MiniUnifiedDB",
        "effect_authority": "ENTITYOS_MINI_ENTITY_EFFECT_GATE",
        "module_class": "~0.8B_GENERIC_CLAYCOG",
        "lane_semantics": "LOGICAL_HYPERPOSITION_COGNITION_LANES",
        "weight_topology": "SHARED_IMMUTABLE_CHECKPOINT_PREFERRED",
        "host_profile": {
            "cpu_cores": 4,
            "ram_bytes": 16 * 1024**3,
            "disk_bytes": 200 * 1024**3,
            "bandwidth_bytes": 16 * 1024**4,
            "evidence": "OWNER_SPEC_DEPLOYMENT_TARGET_ONLY",
        },
        "capacity": {
            "policy": "MAX_SAFE_MEASURED",
            "measurement_bound": False,
            "reserved_ram_bytes": UNRESOLVED,
            "logical_lanes": UNRESOLVED,
            "resident_replicas": UNRESOLVED,
            "active_inference_lanes": UNRESOLVED,
            "measured_shared_weight_rss_bytes": UNRESOLVED,
            "measured_incremental_lane_rss_bytes": UNRESOLVED,
            "measured_cpu_parallel_ceiling": UNRESOLVED,
        },
        "scheduler": {
            "packet_type": "InferencePacket",
            "parallel_candidates_non_authoritative": True,
            "single_gwt_commit_winner": True,
            "generation_fence_required": True,
            "hyperposition_branch_isolation": True,
        },
        "feed_policy": {
            "free_llm_token_pool_role": "CANDIDATE_RESEARCH_INPUT_ONLY",
            "model_output_canonical_truth": False,
            "model_output_direct_effect": False,
            "together_forbidden": True,
        },
        "provenance": {"owner_direction": "2026-08-23 HCU grid extension", "runtime_credit": 0},
    }


class HCUGridManifestTests(unittest.TestCase):
    def test_unmeasured_profile_keeps_capacity_unresolved(self):
        result = validate_manifest(unresolved_manifest())
        self.assertEqual(result.manifest["capacity"]["logical_lanes"], UNRESOLVED)
        self.assertEqual(len(result.identity_sha256), 64)

    def test_exactly_one_entity_is_required(self):
        manifest = unresolved_manifest(); manifest["entity_count"] = 2
        with self.assertRaisesRegex(HCUManifestError, "ENTITY_COUNT_MUST_EQUAL_ONE"):
            validate_manifest(manifest)

    def test_miniunifieddb_is_only_state_authority(self):
        manifest = unresolved_manifest(); manifest["state_authority"] = "lane-local-db"
        with self.assertRaisesRegex(HCUManifestError, "STATE_AUTHORITY_MUST_BE_MINIUNIFIEDDB"):
            validate_manifest(manifest)

    def test_parallel_candidates_have_no_direct_effect_authority(self):
        manifest = unresolved_manifest(); manifest["feed_policy"]["model_output_direct_effect"] = True
        with self.assertRaisesRegex(HCUManifestError, "model_output_direct_effect"):
            validate_manifest(manifest)

    def test_measured_shared_weight_capacity_is_deterministic(self):
        plan = plan_shared_weight_capacity(
            host_ram_bytes=16 * 1024**3,
            reserved_ram_bytes=4 * 1024**3,
            measured_shared_weight_rss_bytes=1 * 1024**3,
            measured_incremental_lane_rss_bytes=512 * 1024**2,
            cpu_cores=4,
            measured_cpu_parallel_ceiling=2,
        )
        self.assertEqual(plan.logical_lanes, 22)
        self.assertEqual(plan.resident_replicas, 1)
        self.assertEqual(plan.active_inference_lanes, 2)

    def test_unusual_false_capacity_poison_fails_closed(self):
        manifest = unresolved_manifest()
        manifest["capacity"]["logical_lanes"] = 32
        manifest["capacity"]["resident_replicas"] = 32
        manifest["capacity"]["active_inference_lanes"] = 4
        with self.assertRaisesRegex(HCUManifestError, "UNMEASURED_NUMERIC_CAPACITY_FORBIDDEN"):
            validate_manifest(manifest)

    def test_measured_manifest_rejects_cpu_overclaim(self):
        manifest = unresolved_manifest()
        manifest["capacity"] = {
            "policy": "MAX_SAFE_MEASURED",
            "measurement_bound": True,
            "reserved_ram_bytes": 4 * 1024**3,
            "logical_lanes": 8,
            "resident_replicas": 1,
            "active_inference_lanes": 5,
            "measured_shared_weight_rss_bytes": 1 * 1024**3,
            "measured_incremental_lane_rss_bytes": 512 * 1024**2,
            "measured_cpu_parallel_ceiling": 5,
        }
        with self.assertRaisesRegex(HCUManifestError, "ACTIVE_INFERENCE_EXCEEDS_CPU_CORES"):
            validate_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
