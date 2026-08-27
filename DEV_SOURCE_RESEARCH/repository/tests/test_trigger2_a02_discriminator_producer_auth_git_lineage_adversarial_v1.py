from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from tools import trigger2_a02_discriminator_producer_auth_gate_v1 as gate
from tools import trigger2_a02_discriminator_producer_v1 as producer
from tools import trigger2_trusted_hyperposition_pilot_generator_v1 as generator


REPO = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = (
    REPO
    / "research_entity/global/j-space/research/"
      "TRIGGER2_A02_DISCRIMINATOR_PRODUCER_AUTHORITY_V1.json"
)


def _authority():
    return json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))


def _baseline_row():
    authority = _authority()
    policy = authority["policy"]
    bundle = generator.build_subjects(generator.CASE_ID, generator.default_parameters())
    receipt = producer.produce(
        world=bundle["formal_world"],
        pre_state=bundle["state_before"],
        event=bundle["event"],
        generation_case_id=generator.CASE_ID,
        policy=policy,
    )
    p = authority["producer"]
    return {
        "generation_case_id_evaluator_only": generator.CASE_ID,
        "formal_task_world_evaluator_only": deepcopy(bundle["formal_world"]),
        "hyperposition_state_before_evaluator_only": deepcopy(bundle["state_before"]),
        "hyperposition_genesis_state_evaluator_only": deepcopy(bundle["genesis_state"]),
        "synthetic_event_history_evaluator_only": [],
        "synthetic_test_event_evaluator_only": deepcopy(bundle["event"]),
        "discriminator_execution_receipts_evaluator_only": [deepcopy(receipt)],
        "discriminator_producer_binding_evaluator_only": {
            "repo_path": p["repo_path"],
            "source_sha256": p["source_sha256"],
            "producer_schema_or_version": p["producer_schema_or_version"],
            "source_lineage": deepcopy(p["source_lineage"]),
            "policy_id": policy["policy_id"],
            "policy_version": policy["policy_version"],
            "policy_jcs_sha256": authority["policy_jcs_sha256"],
            "formal_discriminator_spec_jcs_sha256": policy[
                "formal_discriminator_spec_jcs_sha256"
            ],
        },
    }


def test_a02_git_lineage_rejects_wrong_origin_repository(monkeypatch):
    p = deepcopy(_authority()["producer"])
    real_git_text = gate._git_text

    def fake_git_text(*args):
        if args == ("remote", "get-url", "origin"):
            return 0, "https://github.com/attacker/not-clay.git", ""
        return real_git_text(*args)

    monkeypatch.setattr(gate, "_git_text", fake_git_text)
    failures, details = gate._verify_repository_lineage(p, p["repo_path"])
    assert "A02_REPOSITORY_ORIGIN_IDENTITY_MISMATCH" in failures
    assert details["origin_repository"] == "attacker/not-clay"


def test_a02_git_lineage_rejects_declared_commit_not_ancestor_of_head(monkeypatch):
    p = deepcopy(_authority()["producer"])
    real_git_text = gate._git_text

    def fake_git_text(*args):
        if len(args) >= 2 and args[0] == "merge-base" and args[1] == "--is-ancestor":
            return 1, "", "synthetic non-ancestor"
        return real_git_text(*args)

    monkeypatch.setattr(gate, "_git_text", fake_git_text)
    failures, details = gate._verify_repository_lineage(p, p["repo_path"])
    assert "A02_PRODUCER_SOURCE_LINEAGE_COMMIT_NOT_ANCESTOR_OF_HEAD" in failures
    assert details["source_commit_is_ancestor_of_head"] is False


def test_a02_git_lineage_rejects_executed_head_bytes_different_from_authority(monkeypatch):
    p = deepcopy(_authority()["producer"])
    real_git_bytes = gate._git_bytes

    def fake_git_bytes(*args):
        if args == ("show", f"HEAD:{p['repo_path']}"):
            return 0, b"post-checkout-committed-head-mutation\n", b""
        return real_git_bytes(*args)

    monkeypatch.setattr(gate, "_git_bytes", fake_git_bytes)
    failures, details = gate._verify_repository_lineage(p, p["repo_path"])
    assert "A02_EXECUTED_HEAD_PRODUCER_SHA256_MISMATCH" in failures
    assert details["executed_head_path_sha256"] != p["source_sha256"]


def test_a02_git_lineage_rejects_worktree_mutation_after_checkout(monkeypatch):
    monkeypatch.setattr(gate, "_source_sha256", lambda _path: "0" * 64)
    result = gate.adjudicate(_baseline_row())
    assert result["pass"] is False
    assert "A02_PRODUCER_SOURCE_SHA256_MISMATCH" in result["failures"]
    assert result["producer_source_verified"] is False
    assert result["canonical_dataset_admission"] is False
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
