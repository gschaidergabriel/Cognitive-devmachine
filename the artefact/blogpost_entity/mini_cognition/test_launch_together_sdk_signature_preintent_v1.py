#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path
from unittest import mock

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("launch08_signature",HERE/"launch_together_qwen35_08b_v1.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def sdk_v2_create_signature(*,training_file,model=None,n_epochs=1,validation_file="",n_evals=0,n_checkpoints=1,learning_rate=0.00001,warmup_ratio=0.0,lora=None,suffix=None,random_seed=None,train_on_inputs=None,training_method="sft"):
    return None


def incompatible_create_signature(*,training_file,model=None):
    return None


class Tests(unittest.TestCase):
    def test_current_payload_binds_high_level_sdk_shape(self):
        payload=m.create_payload("train-id","valid-id","suffix")
        self.assertIs(m.validate_create_payload_signature(sdk_v2_create_signature,payload),payload)

    def test_incompatible_sdk_shape_fails_closed(self):
        payload=m.create_payload("train-id","valid-id","suffix")
        with self.assertRaisesRegex(SystemExit,"CREATE_PAYLOAD_SDK_SIGNATURE_REJECT"):
            m.validate_create_payload_signature(incompatible_create_signature,payload)

    def test_signature_failure_cannot_arm_durable_intent(self):
        with mock.patch.object(m,"arm_create_intent") as arm:
            with self.assertRaisesRegex(SystemExit,"CREATE_PAYLOAD_SDK_SIGNATURE_REJECT"):
                m.arm_create_intent_after_signature_check(
                    incompatible_create_signature,
                    "f"*64,
                    "claycog08b-v2-deadbeef",
                    "train-id",
                    "valid-id",
                )
        arm.assert_not_called()

    def test_signature_success_arms_once_after_validation(self):
        fake_intent=Path("/tmp/create-intent.json")
        with mock.patch.object(m,"arm_create_intent",return_value=fake_intent) as arm:
            intent,payload=m.arm_create_intent_after_signature_check(
                sdk_v2_create_signature,
                "f"*64,
                "claycog08b-v2-deadbeef",
                "train-id",
                "valid-id",
            )
        self.assertEqual(intent,fake_intent)
        self.assertEqual(payload,m.create_payload("train-id","valid-id","claycog08b-v2-deadbeef"))
        arm.assert_called_once_with("f"*64,"claycog08b-v2-deadbeef")


if __name__=="__main__":unittest.main()
