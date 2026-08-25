#!/usr/bin/env python3
"""Repository-authority-bound A02 discriminator producer-auth gate v1.

The gate closes the bounded Trigger-2 A02 hole where a candidate could carry a coherent
``admissible=true`` / ``executed=true`` discriminator receipt without proving that the
authority-selected deterministic synthetic producer actually produced it.

It does not create a second Hyperposition semantic authority. It verifies producer/policy
authority, reconstructs the exact receipt using the retained v3 test-order semantics, and
requires byte-structural equality with the transported receipt. PASS is candidate
pre-admission component evidence only and mints zero credit.

Repository lineage is fail-closed: the authority-declared producer commit must resolve as a
real Git commit in the expected repository, ``commit:path`` must resolve to the exact pinned
producer bytes, the commit must be an ancestor of executed HEAD, and the executed HEAD path
must still contain those exact bytes. This prevents a syntactically valid 40-hex string from
being mistaken for source-lineage proof.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
from typing import Any

SCHEMA = "CLAY_TRIGGER2_A02_DISCRIMINATOR_PRODUCER_AUTH_GATE/v1"
AUTHORITY_PATH = (
    "research_entity/global/j-space/research/"
    "TRIGGER2_A02_DISCRIMINATOR_PRODUCER_AUTHORITY_V1.json"
)
CANONICALIZER_PATH = "the artefact/MicroEntity/hcu/entry_canonicalization_v1.py"
EXPECTED_REPOSITORY = "gschaidergabriel/clay-global-research-entity"
EXPECTED_BRANCH = "main"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON_OBJECT_REQUIRED")
    return value


def _source_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _jcs_module():
    return _load_module(
        _repo_root() / CANONICALIZER_PATH,
        "trigger2_jcs_for_a02_producer_auth_gate",
    )


def _jcs_sha256(value: Any) -> str:
    return sha256(_jcs_module().canonicalize(value)).hexdigest()


def _is_lower_hex_sha(value: Any, width: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == width
        and all(ch in "0123456789abcdef" for ch in value)
    )


def _git_bytes(*args: str) -> tuple[int, bytes, bytes]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(_repo_root()), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        return 127, b"", (type(exc).__name__ + ":" + str(exc)).encode("utf-8", "replace")
    return proc.returncode, proc.stdout, proc.stderr


def _git_text(*args: str) -> tuple[int, str, str]:
    code, stdout, stderr = _git_bytes(*args)
    return (
        code,
        stdout.decode("utf-8", "replace").strip(),
        stderr.decode("utf-8", "replace").strip(),
    )


def _remote_repository_identity(url: str) -> str | None:
    value = url.strip()
    if value.endswith(".git"):
        value = value[:-4]
    prefixes = (
        "https://github.com/",
        "http://github.com/",
        "ssh://git@github.com/",
        "git://github.com/",
        "git@github.com:",
    )
    for prefix in prefixes:
        if value.startswith(prefix):
            candidate = value[len(prefix):].strip("/")
            return candidate or None
    return None


def _verify_repository_lineage(
    producer_auth: dict[str, Any],
    producer_repo_path: str,
) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    details: dict[str, Any] = {
        "expected_repository": EXPECTED_REPOSITORY,
        "expected_branch": EXPECTED_BRANCH,
        "declared_source_commit_sha": None,
        "declared_source_path": None,
        "origin_repository": None,
        "executed_head_sha": None,
        "executed_tree_sha": None,
        "source_commit_path_blob_oid": None,
        "source_commit_path_sha256": None,
        "executed_head_path_blob_oid": None,
        "executed_head_path_sha256": None,
        "source_commit_is_ancestor_of_head": False,
    }

    source_lineage = producer_auth.get("source_lineage")
    if not isinstance(source_lineage, dict):
        return ["A02_PRODUCER_SOURCE_LINEAGE_REQUIRED"], details

    source_commit_sha = source_lineage.get("source_commit_sha")
    source_path = source_lineage.get("source_path")
    details["declared_source_commit_sha"] = source_commit_sha
    details["declared_source_path"] = source_path

    if source_lineage.get("repository") != EXPECTED_REPOSITORY:
        failures.append("A02_PRODUCER_SOURCE_LINEAGE_REPOSITORY_MISMATCH")
    if source_lineage.get("branch") != EXPECTED_BRANCH:
        failures.append("A02_PRODUCER_SOURCE_LINEAGE_BRANCH_MISMATCH")
    if source_path != producer_repo_path:
        failures.append("A02_PRODUCER_SOURCE_LINEAGE_PATH_MISMATCH")
    if not _is_lower_hex_sha(source_commit_sha, 40):
        failures.append("A02_PRODUCER_SOURCE_LINEAGE_COMMIT_INVALID")
        return sorted(set(failures)), details

    code, top_level, _ = _git_text("rev-parse", "--show-toplevel")
    try:
        top_level_matches = code == 0 and Path(top_level).resolve() == _repo_root().resolve()
    except Exception:
        top_level_matches = False
    if not top_level_matches:
        failures.append("A02_REPOSITORY_ROOT_NOT_GIT_BOUND")

    code, origin_url, _ = _git_text("remote", "get-url", "origin")
    origin_repo = _remote_repository_identity(origin_url) if code == 0 else None
    details["origin_repository"] = origin_repo
    if origin_repo != EXPECTED_REPOSITORY:
        failures.append("A02_REPOSITORY_ORIGIN_IDENTITY_MISMATCH")

    code, head_sha, _ = _git_text("rev-parse", "HEAD")
    if code != 0 or not _is_lower_hex_sha(head_sha, 40):
        failures.append("A02_EXECUTED_HEAD_UNRESOLVED")
    else:
        details["executed_head_sha"] = head_sha

    code, tree_sha, _ = _git_text("rev-parse", "HEAD^{tree}")
    if code != 0 or not _is_lower_hex_sha(tree_sha, 40):
        failures.append("A02_EXECUTED_TREE_UNRESOLVED")
    else:
        details["executed_tree_sha"] = tree_sha

    code, _, _ = _git_text("cat-file", "-e", source_commit_sha + "^{commit}")
    if code != 0:
        failures.append("A02_PRODUCER_SOURCE_LINEAGE_COMMIT_UNRESOLVED")
        return sorted(set(failures)), details

    code, source_blob_oid, _ = _git_text("rev-parse", f"{source_commit_sha}:{source_path}")
    if code != 0 or not _is_lower_hex_sha(source_blob_oid, 40):
        failures.append("A02_PRODUCER_SOURCE_LINEAGE_PATH_AT_COMMIT_UNRESOLVED")
    else:
        details["source_commit_path_blob_oid"] = source_blob_oid

    code, source_bytes, _ = _git_bytes("show", f"{source_commit_sha}:{source_path}")
    if code != 0:
        failures.append("A02_PRODUCER_SOURCE_LINEAGE_BYTES_AT_COMMIT_UNRESOLVED")
    else:
        source_commit_sha256 = sha256(source_bytes).hexdigest()
        details["source_commit_path_sha256"] = source_commit_sha256
        if source_commit_sha256 != producer_auth.get("source_sha256"):
            failures.append("A02_PRODUCER_SOURCE_LINEAGE_COMMIT_PATH_SHA256_MISMATCH")

    if isinstance(details.get("executed_head_sha"), str):
        code, _, _ = _git_text("merge-base", "--is-ancestor", source_commit_sha, head_sha)
        details["source_commit_is_ancestor_of_head"] = code == 0
        if code != 0:
            failures.append("A02_PRODUCER_SOURCE_LINEAGE_COMMIT_NOT_ANCESTOR_OF_HEAD")

        code, head_blob_oid, _ = _git_text("rev-parse", f"HEAD:{producer_repo_path}")
        if code != 0 or not _is_lower_hex_sha(head_blob_oid, 40):
            failures.append("A02_EXECUTED_HEAD_PRODUCER_PATH_UNRESOLVED")
        else:
            details["executed_head_path_blob_oid"] = head_blob_oid

        code, head_bytes, _ = _git_bytes("show", f"HEAD:{producer_repo_path}")
        if code != 0:
            failures.append("A02_EXECUTED_HEAD_PRODUCER_BYTES_UNRESOLVED")
        else:
            head_sha256 = sha256(head_bytes).hexdigest()
            details["executed_head_path_sha256"] = head_sha256
            if head_sha256 != producer_auth.get("source_sha256"):
                failures.append("A02_EXECUTED_HEAD_PRODUCER_SHA256_MISMATCH")

    return sorted(set(failures)), details


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out = {
        "schema": SCHEMA,
        "pass": not failures,
        "a02_producer_auth_pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "row_producer_or_policy_fields_authoritative": False,
    }
    out.update(extra)
    return out


def adjudicate(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"])
    failures: list[str] = []

    try:
        authority = _load_json(_repo_root() / AUTHORITY_PATH)
    except Exception as exc:
        return _result(["A02_AUTHORITY_LOAD_FAILED:" + type(exc).__name__])
    if authority.get("schema") != "CLAY_TRIGGER2_A02_DISCRIMINATOR_PRODUCER_AUTHORITY/v1":
        failures.append("A02_AUTHORITY_SCHEMA_MISMATCH")

    expected_fences = {
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
    }
    if authority.get("authority_fences") != expected_fences:
        failures.append("A02_AUTHORITY_FENCES_INVALID")

    producer_auth = authority.get("producer")
    policy = authority.get("policy")
    generation_auth_ref = authority.get("generation_authority")
    if not isinstance(producer_auth, dict):
        return _result(failures + ["A02_PRODUCER_AUTHORITY_REQUIRED"])
    if not isinstance(policy, dict):
        return _result(failures + ["A02_POLICY_AUTHORITY_REQUIRED"])
    if not isinstance(generation_auth_ref, dict):
        return _result(failures + ["A02_GENERATION_AUTHORITY_REFERENCE_REQUIRED"])

    try:
        actual_policy_digest = _jcs_sha256(policy)
    except Exception as exc:
        return _result(failures + ["A02_POLICY_JCS_FAILED:" + type(exc).__name__])
    authority_policy_digest = authority.get("policy_jcs_sha256")
    if not _is_lower_hex_sha(authority_policy_digest, 64):
        failures.append("A02_POLICY_JCS_SHA256_REQUIRED")
    elif actual_policy_digest != authority_policy_digest:
        failures.append("A02_POLICY_JCS_SHA256_MISMATCH")

    producer_repo_path = producer_auth.get("repo_path")
    if not isinstance(producer_repo_path, str) or not producer_repo_path:
        return _result(failures + ["A02_PRODUCER_PATH_REQUIRED"])
    producer_path = (_repo_root() / producer_repo_path).resolve()
    try:
        producer_path.relative_to(_repo_root().resolve())
    except ValueError:
        return _result(failures + ["A02_PRODUCER_PATH_ESCAPES_REPO"])
    if not producer_path.is_file():
        return _result(failures + ["A02_PRODUCER_FILE_MISSING"])

    lineage_failures, repository_lineage = _verify_repository_lineage(
        producer_auth,
        producer_repo_path,
    )
    failures.extend(lineage_failures)
    source_lineage = producer_auth.get("source_lineage")

    actual_producer_sha = _source_sha256(producer_path)
    if actual_producer_sha != producer_auth.get("source_sha256"):
        failures.append("A02_PRODUCER_SOURCE_SHA256_MISMATCH")
    try:
        producer = _load_module(producer_path, "trigger2_a02_authority_selected_producer")
    except Exception as exc:
        return _result(failures + ["A02_PRODUCER_IMPORT_FAILED:" + type(exc).__name__])
    if getattr(producer, "PRODUCER_SCHEMA", None) != producer_auth.get("producer_schema_or_version"):
        failures.append("A02_PRODUCER_SCHEMA_MISMATCH")

    generation_authority_path = generation_auth_ref.get("repo_path")
    if not isinstance(generation_authority_path, str) or not generation_authority_path:
        return _result(failures + ["A02_GENERATION_AUTHORITY_PATH_REQUIRED"])
    try:
        generation_authority = _load_json(_repo_root() / generation_authority_path)
    except Exception as exc:
        return _result(failures + ["A02_GENERATION_AUTHORITY_LOAD_FAILED:" + type(exc).__name__])
    if generation_authority.get("schema") != generation_auth_ref.get("schema"):
        failures.append("A02_GENERATION_AUTHORITY_SCHEMA_MISMATCH")

    case_id = row.get("generation_case_id_evaluator_only")
    if case_id != policy.get("allowed_case_id"):
        failures.append("A02_GENERATION_CASE_NOT_AUTHORIZED")
    cases = generation_authority.get("allowed_cases")
    case = cases.get(case_id) if isinstance(cases, dict) else None
    if not isinstance(case, dict):
        return _result(failures + ["A02_GENERATION_CASE_AUTHORITY_MISSING"])

    world = row.get("formal_task_world_evaluator_only")
    pre_state = row.get("hyperposition_state_before_evaluator_only")
    event = row.get("synthetic_test_event_evaluator_only")
    history = row.get("synthetic_event_history_evaluator_only")
    if history != []:
        failures.append("A02_V1_REQUIRES_EMPTY_HISTORY_BOUNDED_PILOT")

    try:
        supplied_subject_hashes = {
            "formal_world_jcs_sha256": _jcs_sha256(world),
            "event_jcs_sha256": _jcs_sha256(event),
            "state_before_jcs_sha256": _jcs_sha256(pre_state),
        }
    except Exception as exc:
        supplied_subject_hashes = None
        failures.append("A02_SUBJECT_JCS_FAILED:" + type(exc).__name__)
    expected_subject_hashes = case.get("subjects")
    if not isinstance(expected_subject_hashes, dict):
        failures.append("A02_GENERATION_SUBJECT_HASH_AUTHORITY_REQUIRED")
    elif isinstance(supplied_subject_hashes, dict):
        for key, actual in supplied_subject_hashes.items():
            if actual != expected_subject_hashes.get(key):
                failures.append("A02_SUBJECT_NOT_AUTHORITY_RECONSTRUCTED:" + key)

    if isinstance(world, dict) and world.get("world_id") != policy.get("world_id"):
        failures.append("A02_WORLD_SCOPE_MISMATCH")
    if isinstance(pre_state, dict) and pre_state.get("query_id") != policy.get("query_id"):
        failures.append("A02_QUERY_SCOPE_MISMATCH")
    if isinstance(event, dict):
        if event.get("test_id") != policy.get("test_id"):
            failures.append("A02_TEST_SCOPE_MISMATCH")
        if event.get("epistemic_type") != policy.get("epistemic_type"):
            failures.append("A02_EPISTEMIC_SCOPE_MISMATCH")

    expected_binding = {
        "repo_path": producer_repo_path,
        "source_sha256": actual_producer_sha,
        "producer_schema_or_version": producer_auth.get("producer_schema_or_version"),
        "source_lineage": source_lineage,
        "policy_id": policy.get("policy_id"),
        "policy_version": policy.get("policy_version"),
        "policy_jcs_sha256": actual_policy_digest,
        "formal_discriminator_spec_jcs_sha256": policy.get(
            "formal_discriminator_spec_jcs_sha256"
        ),
    }
    claimed_binding = row.get("discriminator_producer_binding_evaluator_only")
    if claimed_binding != expected_binding:
        failures.append("A02_ROW_PRODUCER_BINDING_NOT_EXACT_AUTHORITY")

    expected_receipt = None
    if not failures:
        try:
            expected_receipt = producer.produce(
                world=world,
                pre_state=pre_state,
                event=event,
                generation_case_id=case_id,
                policy=policy,
            )
        except Exception as exc:
            failures.append("A02_PRODUCER_EXECUTION_FAILED:" + type(exc).__name__ + ":" + str(exc))

    receipts = row.get("discriminator_execution_receipts_evaluator_only")
    claimed_receipt = None
    if not isinstance(receipts, list):
        failures.append("A02_DISCRIMINATOR_RECEIPTS_LIST_REQUIRED")
    elif isinstance(event, dict):
        matching = [
            r for r in receipts
            if isinstance(r, dict) and r.get("event_id") == event.get("event_id")
        ]
        if len(matching) != 1:
            failures.append("A02_REQUIRES_EXACTLY_ONE_CURRENT_EVENT_RECEIPT")
        else:
            claimed_receipt = matching[0]

    if expected_receipt is not None and claimed_receipt != expected_receipt:
        failures.append("A02_DISCRIMINATOR_RECEIPT_NOT_EXACTLY_AUTHORITY_DERIVED")

    lineage_failure_prefixes = (
        "A02_PRODUCER_SOURCE_LINEAGE_",
        "A02_REPOSITORY_",
        "A02_EXECUTED_HEAD_",
        "A02_EXECUTED_TREE_",
    )
    return _result(
        failures,
        expected_producer_binding=expected_binding,
        expected_discriminator_receipt=expected_receipt,
        supplied_subject_hashes=supplied_subject_hashes,
        bounded_generation_case_id=case_id,
        producer_source_verified=actual_producer_sha == producer_auth.get("source_sha256"),
        producer_source_lineage_verified=not any(
            failure.startswith(lineage_failure_prefixes) for failure in failures
        ),
        repository_lineage=repository_lineage,
        policy_digest_verified=actual_policy_digest == authority_policy_digest,
        producer_invocation_completed=expected_receipt is not None,
        semantic_authority="RETAINED_V3_U_TEST_ORDER_VIA_AUTHORITY_PINNED_PRODUCER",
        producer_execution_scope="SYNTHETIC_PROOF_ONLY_NONCANONICAL",
    )


if __name__ == "__main__":
    print({
        "schema": SCHEMA,
        "status": "SOURCE_ONLY_CANDIDATE_PRE_ADMISSION",
        "canonical_dataset_admission": False,
        "training_credit_minted": 0,
    })
