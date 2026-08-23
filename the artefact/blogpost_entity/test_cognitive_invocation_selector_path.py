from __future__ import annotations

import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")


def run_args(source: str) -> list[str]:
    match = re.search(r"fn\s+run\((.*?)\)\s*->\s*Map", source, re.S)
    if match is None:
        return []
    return [
        item.strip().split(":", 1)[0].strip()
        for item in match.group(1).split(",")
        if item.strip()
    ]


def executable_source(source: str) -> str:
    return re.sub(r"//[^\n]*", "", source)


class CognitiveInvocationSelectorPathTests(unittest.TestCase):
    def test_run_boundary_carries_only_bounded_selector(self) -> None:
        self.assertEqual(
            run_args(SRC),
            ["entity_db", "source_db", "secret_file", "cognition_invocation"],
        )

    def test_selector_is_threaded_once_into_pre_inference_admission(self) -> None:
        executable = executable_source(SRC)
        marker = 'map_set(cognition_data,"invocation",cognition_invocation)'
        self.assertEqual(executable.count(marker), 1)
        self.assertLess(
            executable.index(marker),
            executable.index('phase("pipeline_cognitive_fabric_admit"'),
        )
        self.assertLess(
            executable.index('phase("pipeline_cognitive_fabric_admit"'),
            executable.index('effect("inference_generate"'),
        )

    def test_caller_cannot_directly_thread_cognition_authority_fields(self) -> None:
        executable = executable_source(SRC)
        forbidden = (
            "zero_identity_digest",
            "grf_digest",
            "hyperposition_digest",
            "local_model_digest",
            "tokenizer_digest",
            "workspace_digest",
            "jspace_profile_digest",
            "jacobian_lens_digest",
            "workspace_calibration_digest",
            "policy_authority_digest",
        )
        for field in forbidden:
            self.assertNotIn(f'map_set(cognition_data,"{field}"', executable)

    def test_final_ucf_receipt_remains_post_commit(self) -> None:
        executable = executable_source(SRC)
        commit = executable.index('phase("pipeline_commit"')
        finalize = executable.index('phase("pipeline_cognitive_fabric_finalize"')
        self.assertLess(commit, finalize)
        self.assertNotIn('map_set(infer,"ucf_runtime_receipt_digest"', executable)


if __name__ == "__main__":
    unittest.main()
