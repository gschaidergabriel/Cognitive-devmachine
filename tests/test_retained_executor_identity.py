from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.validate_retained_executor_identity import ExecutorIdentityError, validate_contract, validate_repo_surfaces

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "research_entity" / "continuity" / "RETAINED_EXECUTION_CONTROLLER_IDENTITY.json"

class RetainedExecutorIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_current_contract_passes(self) -> None:
        validate_contract(copy.deepcopy(self.contract))

    def test_current_repo_surfaces_pass(self) -> None:
        validate_repo_surfaces(ROOT)

    def test_research_repo_pr810_alias_fails_closed(self) -> None:
        poisoned = copy.deepcopy(self.contract)
        poisoned["retained_execution_controller"]["repository"] = "gschaidergabriel/clay-global-research-entity"
        poisoned["retained_execution_controller"]["qualified_ref"] = "gschaidergabriel/clay-global-research-entity#810"
        with self.assertRaisesRegex(ExecutorIdentityError, "executor:wrong_repository"):
            validate_contract(poisoned)

    def test_unqualified_executor_selection_cannot_be_reenabled(self) -> None:
        poisoned = copy.deepcopy(self.contract)
        poisoned["ambiguity_fence"]["unqualified_pr810_for_current_executor_selection"] = "ALLOWED"
        with self.assertRaisesRegex(ExecutorIdentityError, "ambiguity_fence:unqualified_pr810_not_forbidden"):
            validate_contract(poisoned)

    def test_snapshot_head_cannot_become_current_authority(self) -> None:
        poisoned = copy.deepcopy(self.contract)
        poisoned["head_freshness"]["snapshot_heads_are_current_authority"] = True
        with self.assertRaisesRegex(ExecutorIdentityError, "head_freshness:snapshot_promoted_to_authority"):
            validate_contract(poisoned)

    def test_live_head_refresh_cannot_be_disabled(self) -> None:
        poisoned = copy.deepcopy(self.contract)
        poisoned["head_freshness"]["execution_requires_live_refresh"] = False
        with self.assertRaisesRegex(ExecutorIdentityError, "head_freshness:live_refresh_not_required"):
            validate_contract(poisoned)

    def test_runtime_credit_cannot_self_promote(self) -> None:
        poisoned = copy.deepcopy(self.contract)
        poisoned["authority_boundary"]["runtime_credit_change"] = 1
        with self.assertRaisesRegex(ExecutorIdentityError, "authority_boundary:runtime_credit"):
            validate_contract(poisoned)

    def test_paid_mode_cannot_enter_selector(self) -> None:
        poisoned = copy.deepcopy(self.contract)
        poisoned["mode"] = "PAID_ALLOWED"
        with self.assertRaisesRegex(ExecutorIdentityError, "mode:not_free_only"):
            validate_contract(poisoned)

if __name__ == "__main__":
    unittest.main()
