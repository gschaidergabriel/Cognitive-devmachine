from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).with_name("BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")


def _executable_source() -> str:
    return "\n".join(line.split("//", 1)[0] for line in SRC.splitlines())


def _effect_or_phase_sequence() -> list[str]:
    source = _executable_source()
    pattern = re.compile(r'(?:effect|phase)\(\s*"([A-Za-z0-9_.-]+)"')
    return pattern.findall(source)


def test_canonical_path_requires_ucf_admission_before_inference() -> None:
    sequence = _effect_or_phase_sequence()
    assert sequence.index("pipeline_build_prompt") < sequence.index("pipeline_cognitive_fabric_admit")
    assert sequence.index("pipeline_cognitive_fabric_admit") < sequence.index("inference_generate")


def test_raw_profile_or_prompt_cannot_bypass_admitted_envelope() -> None:
    source = _executable_source()
    assert 'map_set(infer,"inference",admitted.inference)' in source
    assert 'map_set(infer,"system",admitted.system)' in source
    assert 'map_set(infer,"user",admitted.user)' in source
    assert 'map_set(infer,"inference",profile.inference)' not in source
    assert 'map_set(infer,"system",prompt.system)' not in source
    assert 'map_set(infer,"user",prompt.user)' not in source


def test_ucf_identity_is_carried_into_gate_commit_and_result() -> None:
    source = _executable_source()
    assert 'map_set(gate_data,"cognitive_fabric",admitted)' in source
    assert 'map_set(commit_data,"cognitive_fabric",admitted)' in source
    assert 'map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)' in source
    assert 'map_set(infer,"cognitive_fabric_receipt_digest",admitted.cognitive_fabric_receipt_digest)' in source
    assert 'map_set(result,"inference_packet_digest",admitted.inference_packet_digest)' in source
    assert 'map_set(result,"cognitive_fabric_receipt_digest",admitted.cognitive_fabric_receipt_digest)' in source
