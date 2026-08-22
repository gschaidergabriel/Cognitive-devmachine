#!/usr/bin/env python3
"""Deterministic source gate for exact BYOM checkpoint provenance."""
import ast
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE/"launch_together_v1.py"
TEXT=SOURCE.read_text(encoding="utf-8")
TREE=ast.parse(TEXT)

EXPECTED={
    "Qwen/Qwen2.5-0.5B":"060db6499f32faf8b98477b0a26969ef7d8b9987",
    "Qwen/Qwen2.5-0.5B-Instruct":"7ae557604adf67be50417f59c2c2f167def9a775",
}
for model,revision in EXPECTED.items():
    assert model in TEXT, model
    assert revision in TEXT, revision
    assert re.fullmatch(r"[0-9a-f]{40}",revision), revision

create_calls=[]
for node in ast.walk(TREE):
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=="create":
        create_calls.append(node)
assert create_calls, "fine_tuning.create call not found"
assert any(any(k.arg=="hf_model_revision" for k in call.keywords) for call in create_calls), \
    "billed create is not bound to hf_model_revision"
assert TEXT.count('"hf_model_revision"')>=2, "revision is not emitted in preflight/create evidence"
assert "Qwen/Qwen3.5-0.8B" not in TEXT, "automatic architecture-changing fallback must stay absent"
assert "CLAYCOG_HF_REVISION" in TEXT and "CLAYCOG_INSTRUCT_HF_REVISION" in TEXT
assert "40-hex Hugging Face commit SHA" in TEXT
print("CLAYCOG_05B_BYOM_PROVENANCE_SOURCE_GATE PASS")
