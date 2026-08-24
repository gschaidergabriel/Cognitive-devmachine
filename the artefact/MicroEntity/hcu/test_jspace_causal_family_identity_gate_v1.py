from dataclasses import replace
import unittest

from jspace_causal_family_identity_gate_v1 import (
    CausalFamilyIdentityError,
    CausalTrialIdentity,
    EVIDENCE_CLASS,
    REQUIRED_CONDITIONS,
    validate_causal_family_identity,
)


def h(char):
    return char * 64


def trial(condition, index):
    return CausalTrialIdentity(
        condition=condition,
        family_id="holdout:family:17",
        input_variant_id="clean" if condition == "BASELINE_CLEAN" else "corrupted",
        generation=7,
        checkpoint_sha256=h("1"),
        tokenizer_sha256=h("2"),
        runtime_build_sha256=h("3"),
        loader_consumption_sha256=h("4"),
        model_execution_sha256=f"{index + 10:064x}",
        inference_receipt_sha256=f"{index + 20:064x}",
        trace_sha256=f"{index + 30:064x}",
        output_sha256=f"{index + 40:064x}",
        activation_site_id="resid_post:layer=12:position=last",
        pre_activation_sha256=f"{index + 50:064x}",
        post_activation_sha256=f"{index + 60:064x}",
        intervention_sha256=None
        if condition.startswith("BASELINE_")
        else f"{index + 70:064x}",
    )


def family():
    return tuple(trial(condition, index) for index, condition in enumerate(REQUIRED_CONDITIONS))


class CausalFamilyIdentityGateTests(unittest.TestCase):
    def test_complete_family_binds_identity_without_causal_credit(self):
        result = validate_causal_family_identity(family())
        self.assertEqual(result.evidence_class, EVIDENCE_CLASS)
        self.assertFalse(result.jspace_causal_credit)
        self.assertEqual(result.present_conditions, REQUIRED_CONDITIONS)
        self.assertEqual(len(result.trial_identity_sha256), 5)
        self.assertEqual(len(result.family_identity_sha256), 64)

    def test_missing_or_duplicate_control_fails_closed(self):
        trials = list(family())
        with self.assertRaisesRegex(CausalFamilyIdentityError, "EXACT_MINIMUM"):
            validate_causal_family_identity(trials[:-1])
        trials[-1] = replace(trials[-1], condition="SHAM_CONTROL")
        with self.assertRaisesRegex(CausalFamilyIdentityError, "DUPLICATE_CONTROL"):
            validate_causal_family_identity(trials)

    def test_model_identity_mutation_fails_cross_control_binding(self):
        trials = list(family())
        trials[2] = replace(trials[2], checkpoint_sha256=h("9"))
        with self.assertRaisesRegex(CausalFamilyIdentityError, "checkpoint_sha256:CROSS_CONTROL_MISMATCH"):
            validate_causal_family_identity(trials)

    def test_execution_trace_or_output_relabeling_fails(self):
        for field in (
            "model_execution_sha256",
            "inference_receipt_sha256",
            "trace_sha256",
            "output_sha256",
        ):
            with self.subTest(field=field):
                trials = list(family())
                trials[4] = replace(trials[4], **{field: getattr(trials[3], field)})
                with self.assertRaisesRegex(CausalFamilyIdentityError, "CROSS_CONTROL_REUSE_FORBIDDEN"):
                    validate_causal_family_identity(trials)

    def test_baseline_cannot_carry_intervention_and_controls_require_one(self):
        trials = list(family())
        trials[0] = replace(trials[0], intervention_sha256=h("a"))
        with self.assertRaisesRegex(CausalFamilyIdentityError, "BASELINE_INTERVENTION_MUST_BE_NONE"):
            validate_causal_family_identity(trials)

        trials = list(family())
        trials[2] = replace(trials[2], intervention_sha256=None)
        with self.assertRaisesRegex(CausalFamilyIdentityError, "intervention_sha256:NONEMPTY_STRING_REQUIRED"):
            validate_causal_family_identity(trials)

    def test_intervention_receipt_reuse_fails(self):
        trials = list(family())
        trials[4] = replace(trials[4], intervention_sha256=trials[3].intervention_sha256)
        with self.assertRaisesRegex(CausalFamilyIdentityError, "intervention_sha256:CROSS_CONTROL_REUSE_FORBIDDEN"):
            validate_causal_family_identity(trials)

    def test_placeholder_or_generation_alias_fails_closed(self):
        trials = list(family())
        trials[1] = replace(trials[1], trace_sha256="0" * 64)
        with self.assertRaisesRegex(CausalFamilyIdentityError, "PLACEHOLDER_SHA256_FORBIDDEN"):
            validate_causal_family_identity(trials)

        trials = list(family())
        trials[1] = replace(trials[1], generation=True)
        with self.assertRaisesRegex(CausalFamilyIdentityError, "IJSON_SAFE_INTEGER"):
            validate_causal_family_identity(trials)


if __name__ == "__main__":
    unittest.main()
