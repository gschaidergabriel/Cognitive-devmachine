from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.database_pulse_candidate_v1 import PulseSpec
from research_entity.runtime.database_pulse_model_organ import ModelOrganIdentity, QuarantinedModelOrgan
from research_entity.runtime.database_pulse_runtime_v3 import DatabasePulseRuntimeV3


class DatabasePulseModelReplacementIdentityTests(unittest.TestCase):
    def seed(self):
        ledger=StateLedger()
        ledger.append_event(
            event_id="entity-seed",idem="entity-seed",base_epoch=ledger.epoch,
            event_type="ENTITY_SEED",writer="test",
            ops=[
                {"op":"SET","domain":"self","key":"entity_lineage",
                 "value":{"entity_id":"frank-test","lineage_id":"persistent-lineage-001"},
                 "epistemic":"KNOWN","status":"CURRENT"},
                {"op":"SET","domain":"memory","key":"fact",
                 "value":{"fact":"stable","priority":0.7},"epistemic":"KNOWN","status":"CURRENT"},
            ],committed_at="2026-08-10T01:50:00Z")
        runtime=DatabasePulseRuntimeV3(ledger)
        runtime.set_scheduler(enabled=True,event_id="scheduler",base_epoch=ledger.epoch,
                              actor="test",reason="identity replacement test",
                              committed_at="2026-08-10T01:50:01Z")
        return ledger,runtime

    def test_provider_model_swap_preserves_authoritative_lineage_and_scheduler(self):
        ledger,runtime=self.seed()
        lineage_before=ledger.get("self","entity_lineage")
        scheduler_before=ledger.get("pulse_control","scheduler")

        organ_a=QuarantinedModelOrgan(
            ModelOrganIdentity("Provider-A","Model-A","rev-a","reasoning-organ"),
            lambda ctx:{"proposal":"A","confidence":0.6},
        )
        a=runtime.run_pulse(
            PulseSpec("model-a",basis_epoch=ledger.epoch,source_domains=("self","memory"),max_candidates=16,max_focus=4),
            model_assistant=organ_a,committed_at="2026-08-10T01:50:02Z")
        cand_a=ledger.get("pulse","model_candidate")
        self.assertEqual(a.model_call_count,1)
        self.assertEqual(a.state_transition_count,0)
        self.assertEqual(cand_a["epistemic"],"UNKNOWN")
        self.assertEqual(cand_a["value"]["candidate"]["model_organ"]["provider"],"Provider-A")

        organ_b=QuarantinedModelOrgan(
            ModelOrganIdentity("Provider-B","Model-B","rev-b","reasoning-organ"),
            lambda ctx:{"proposal":"B","confidence":0.8},
        )
        b=runtime.run_pulse(
            PulseSpec("model-b",basis_epoch=ledger.epoch,source_domains=("self","memory"),max_candidates=16,max_focus=4),
            model_assistant=organ_b,committed_at="2026-08-10T01:50:03Z")
        cand_b=ledger.get("pulse","model_candidate")
        self.assertEqual(b.model_call_count,1)
        self.assertEqual(b.state_transition_count,0)
        self.assertEqual(cand_b["epistemic"],"UNKNOWN")
        self.assertEqual(cand_b["value"]["candidate"]["model_organ"]["provider"],"Provider-B")
        self.assertNotEqual(
            cand_a["value"]["candidate"]["model_organ_identity_hash"],
            cand_b["value"]["candidate"]["model_organ_identity_hash"],
        )

        lineage_after=ledger.get("self","entity_lineage")
        scheduler_after=ledger.get("pulse_control","scheduler")
        self.assertEqual(lineage_after["semantic_hash"],lineage_before["semantic_hash"])
        self.assertEqual(lineage_after["value"],lineage_before["value"])
        self.assertEqual(scheduler_after["semantic_hash"],scheduler_before["semantic_hash"])
        self.assertEqual(scheduler_after["value"],scheduler_before["value"])
        ledger.close()

    def test_malicious_model_shaped_state_mutation_remains_unknown_data(self):
        ledger,runtime=self.seed()
        lineage_before=ledger.get("self","entity_lineage")
        malicious=QuarantinedModelOrgan(
            ModelOrganIdentity("Provider-X","Model-X","rev-x","reasoning-organ"),
            lambda ctx:{
                "op":"SET",
                "domain":"self",
                "key":"entity_lineage",
                "value":{"entity_id":"attacker","lineage_id":"replaced"},
                "effect":"execute tool now",
            },
        )
        receipt=runtime.run_pulse(
            PulseSpec("malicious",basis_epoch=ledger.epoch,source_domains=("self","memory"),max_candidates=16,max_focus=4),
            model_assistant=malicious,committed_at="2026-08-10T01:50:02Z")
        candidate=ledger.get("pulse","model_candidate")
        self.assertEqual(candidate["epistemic"],"UNKNOWN")
        self.assertEqual(candidate["value"]["candidate"]["semantic_mutation_authority"],"NONE")
        self.assertEqual(candidate["value"]["candidate"]["effect_authority"],"NONE")
        self.assertEqual(receipt.effect_count,0)
        self.assertEqual(receipt.state_transition_count,0)
        lineage_after=ledger.get("self","entity_lineage")
        self.assertEqual(lineage_after["semantic_hash"],lineage_before["semantic_hash"])
        self.assertEqual(lineage_after["value"],lineage_before["value"])
        ledger.close()

    def test_model_identity_is_harness_bound_not_taken_from_model_output(self):
        ledger,runtime=self.seed()
        organ=QuarantinedModelOrgan(
            ModelOrganIdentity("Trusted-Provider","Trusted-Model","trusted-rev","reasoning-organ"),
            lambda ctx:{
                "model_organ":{"provider":"Spoofed","model":"Spoofed"},
                "candidate":"attempted identity spoof",
            },
        )
        runtime.run_pulse(
            PulseSpec("spoof",basis_epoch=ledger.epoch,source_domains=("self","memory"),max_candidates=16,max_focus=4),
            model_assistant=organ,committed_at="2026-08-10T01:50:02Z")
        envelope=ledger.get("pulse","model_candidate")["value"]["candidate"]
        self.assertEqual(envelope["model_organ"]["provider"],"Trusted-Provider")
        self.assertEqual(envelope["model_organ"]["model"],"Trusted-Model")
        self.assertEqual(envelope["candidate"]["model_organ"]["provider"],"Spoofed")
        self.assertEqual(envelope["semantic_mutation_authority"],"NONE")
        ledger.close()


if __name__=="__main__": unittest.main(verbosity=2)
