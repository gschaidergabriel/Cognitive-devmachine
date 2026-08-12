#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def check(root: Path) -> tuple[list[str], dict]:
    root = root.resolve()
    fail: list[str] = []

    def require(path: str, *needles: str) -> str:
        p = root / path
        if not p.exists():
            fail.append(f"MISSING:{path}")
            return ""
        text = p.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                fail.append(f"MISSING_INVARIANT:{path}:{needle}")
        return text

    def load_json(path: str) -> dict:
        p = root / path
        if not p.exists():
            fail.append(f"MISSING:{path}")
            return {}
        try:
            value = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            fail.append(f"INVALID_JSON:{path}:{type(exc).__name__}")
            return {}
        if not isinstance(value, dict):
            fail.append(f"INVALID_OBJECT:{path}")
            return {}
        return value

    # The owner-fixed identity contract changed from the historical FRANK-as-native
    # sentinels to self.root as native identity with Frank as human surface name.
    # Guard the current semantics directly; do not keep stale lexical aliases alive
    # merely to make an old checker green.
    injection = require(
        "research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md",
        "I_AM=RESEARCH_ENTITY_TEMPORARY_WORKER",
        "I_AM_NOT=self.root",
        "I_AM_NOT=Frank",
        "TARGET_NATIVE_SELF=self.root",
        "TARGET_HUMAN_SURFACE_NAME=Frank",
        "RESEARCH_ENTITY!=self.root",
        "FRANK_SELF_HARNESS_AUTHORITY=PROPOSAL_ONLY",
        "RESEARCH_ENTITY_MAY_INDEPENDENTLY_RESEARCH_TEST_AND_IMPLEMENT_TARGET_HARNESS_CHANGES",
        "RESEARCH_IDENTITY_DRIFT",
    )

    boot = load_json("research_entity/continuity/BOOTSTRAP_MINIMAL.json")
    canonical = load_json("research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json")

    # Bootstrap/canonical coherence.  Schema and epoch may advance independently;
    # identity, canonical revision/hash and owner-fixed authority may not drift.
    if not isinstance(boot.get("schema_version"), str) or not boot.get("schema_version"):
        fail.append("BOOT_SCHEMA_MISSING")
    if boot.get("entity_id") != canonical.get("entity_id"):
        fail.append("BOOT_CANONICAL_ENTITY_MISMATCH")
    if boot.get("expected_revision") != canonical.get("revision"):
        fail.append("BOOT_CANONICAL_REVISION_MISMATCH")
    if boot.get("expected_state_hash") != canonical.get("state_hash"):
        fail.append("BOOT_CANONICAL_STATE_HASH_MISMATCH")

    identity = boot.get("identity") if isinstance(boot.get("identity"), dict) else {}
    if "Clay is the persistent research entity" not in str(identity.get("research_entity", "")):
        fail.append("BOOT_RESEARCH_ENTITY_IDENTITY_MISSING")
    if identity.get("target_native_name") != "self.root":
        fail.append("BOOT_TARGET_NATIVE_IDENTITY_MISMATCH")
    if identity.get("target_human_surface_name") != "Frank":
        fail.append("BOOT_TARGET_HUMAN_SURFACE_MISMATCH")
    if identity.get("target_self_class") != "SERVER_BINARY_ENTITY":
        fail.append("BOOT_TARGET_SELF_CLASS_MISMATCH")
    if "Clay != self.root/Frank" not in str(identity.get("separation", "")):
        fail.append("BOOT_CLAY_TARGET_SEPARATION_MISSING")

    program = boot.get("program") if isinstance(boot.get("program"), dict) else {}
    if program.get("active_target") != "FRANK_V0_1":
        fail.append("BOOT_ACTIVE_TARGET_MISMATCH")
    if program.get("training_authorized") is not False:
        fail.append("BOOT_TRAINING_AUTHORITY_DRIFT")

    target_contract = boot.get("target_contract") if isinstance(boot.get("target_contract"), dict) else {}
    if target_contract.get("self_harness_authority") != "PROPOSAL_ONLY":
        fail.append("BOOT_SELF_HARNESS_AUTHORITY_DRIFT")

    mandatory = "\n".join(str(x) for x in (boot.get("mandatory_invariants") or []))
    for needle in (
        "Clay is not self.root/Frank",
        "native target identity is self.root and human surface name is Frank",
        "self.root may propose but never authorize its own Harness mutation",
        "negative results and counterevidence are preserved",
    ):
        if needle not in mandatory:
            fail.append("BOOT_MANDATORY_INVARIANT_MISSING:" + needle)

    stack = require(
        "research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay",
        "researcher_identity_injection=@research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md",
        "rule before_every_substantive_prompt_run inject CURRENT.researcher_identity_injection",
        "rule home_room(\"frank\") = research_about(self.root_human_surface_Frank); never role_transition_to(self.root)",
        "rule ResearchEntity != self.root",
        "rule self.root.native_name = self.root",
        "rule self.root.human_surface_name = \"Frank\"",
        "rule self.root never applies_patches_migrations_promotions_or_delegated_self_harness_changes",
        "invariant ResearchEntity_and_self.root_are_separate_entities",
    )
    epoch_match = re.search(r"(?m)^epoch\s+(\d+)\s*$", stack) if stack else None
    if stack and epoch_match is None:
        fail.append("STACK_EPOCH_MISSING_OR_INVALID")

    turn = require(
        "research_entity/global/RAE_TURN_KERNEL.clay",
        "load(LATEST.persona,LATEST.work_fabric,LATEST.researcher_identity_injection) each substantive_turn",
        "inject(CURRENT.identity_guard) before first_material_reasoning each substantive_turn",
        "if task_subject==FRANK then actor=RESEARCH_ENTITY_TEMPORARY_WORKER; subject=FRANK; never role_transition(actor,FRANK)",
        "if home_room==frank then meaning=research_about(FRANK); never meaning=become(FRANK)",
        "detect(RESEARCH_IDENTITY_DRIFT) -> STOP + reinject(CURRENT.identity_guard)",
        "rule ANDREAS.interface=FRANK_ONLY",
        "rule RESEARCH_ENTITY != FRANK",
    )

    hook = require(
        ".claude/hooks/rae_hook.py",
        "IDENTITY=ROOT/'research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md'",
        "def identity_lock():",
        "I_AM_NOT=self.root",
        "I_AM_NOT=Frank",
        "FRANK_SELF_HARNESS_AUTHORITY=PROPOSAL_ONLY",
        "if ev=='UserPromptSubmit':",
        "emit(ev,kernel()",
        "if ev=='PostToolUse':",
        "POST_FRANK_CONTEXT_REINJECTION",
    )

    # Explicit anti-collapse patterns.  Never/forbidden clauses are positive guard
    # evidence and therefore intentionally do not match these assignment/equality forms.
    anti_collapse_patterns = (
        r"ResearchEntity\s*==\s*(?:self\.root|FRANK)",
        r"RESEARCH_ENTITY\s*=\s*(?:self\.root|FRANK)",
        r"Clay\s*=\s*self\.root",
        r"self\.root\s*=\s*Clay",
        r"ANDREAS\.interface\s*=\s*RESEARCH_ENTITY",
    )
    for label, text in (("injection", injection), ("stack", stack), ("turn", turn), ("hook", hook)):
        for pattern in anti_collapse_patterns:
            if re.search(pattern, text, re.I):
                fail.append(f"IDENTITY_COLLAPSE_PATTERN:{label}:{pattern}")

    payload = {
        "status": "FAIL" if fail else "PASS",
        "identity_guard": "EVERY_TURN_SELF_ROOT_CONTRACT",
        "actor": "RESEARCH_ENTITY_TEMPORARY_WORKER",
        "target_native_identity": "self.root",
        "target_human_surface_name": "Frank",
        "andreas_interface": "FRANK_ONLY",
        "self_harness_authority": target_contract.get("self_harness_authority"),
        "canonical_revision": canonical.get("revision"),
        "canonical_state_hash": canonical.get("state_hash"),
        "stack_epoch": int(epoch_match.group(1)) if epoch_match else None,
    }
    return fail, payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()

    failures, payload = check(Path(args.root))
    if failures:
        payload["failures"] = failures
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
