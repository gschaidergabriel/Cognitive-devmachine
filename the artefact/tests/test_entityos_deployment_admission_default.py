from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"
MANIFEST = ROOT / "manifest.json"
DOCKERFILE = ROOT / "Dockerfile"
COMPOSE = ROOT / "compose.yaml"


def _deployment_entityos_exec_value(text: str) -> str:
    match = re.search(
        r'- name: CLAYVERSE_ENABLE_ENTITYOS_EXEC\s+value: ["\']?([01])["\']?',
        text,
    )
    assert match is not None, "deployment CLAYVERSE_ENABLE_ENTITYOS_EXEC missing"
    return match.group(1)


def _compose_entityos_exec_value(text: str) -> str:
    match = re.search(
        r'^\s*CLAYVERSE_ENABLE_ENTITYOS_EXEC:\s*["\']?([01])["\']?\s*$',
        text,
        re.MULTILINE,
    )
    assert match is not None, "compose CLAYVERSE_ENABLE_ENTITYOS_EXEC missing"
    return match.group(1)


def test_all_baseline_surfaces_keep_entityos_execution_fail_closed():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["entityos_execution_default"] == "DISABLED"
    assert manifest["entityos_whole_product_gate"] == "CONDITIONAL_ON_EXPLICIT_ADMISSION"

    deployment = DEPLOYMENT.read_text(encoding="utf-8")
    compose = COMPOSE.read_text(encoding="utf-8")
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    assert _deployment_entityos_exec_value(deployment) == "0"
    assert _compose_entityos_exec_value(compose) == "0"
    assert "CLAYVERSE_ENABLE_ENTITYOS_EXEC=0" in dockerfile


def test_kata_template_requires_separate_admission_before_opt_in():
    deployment = DEPLOYMENT.read_text(encoding="utf-8")
    assert "conditional capability" in deployment
    assert "separately reviewed deployment-specific" in deployment
    assert "exact embedded-artifact admission" in deployment
