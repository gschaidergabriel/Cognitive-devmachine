#!/usr/bin/env python3
"""Executable discriminator for WP03 FrontendArtifact -> TypedIR contract candidate."""
from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import json
import os
import platform
import resource
from pathlib import Path

import claycode_wp03_frontend_artifact_contract as adapter

ROOT = Path(__file__).resolve().parents[1]
V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
V7 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"
V17_SURFACE = "BASE_D_V17_DECLARATIVE_TRIVIA_SAFE"
V7_SURFACE = "BASE_STRUCTURED_V7_OPERATOR_FN_RESEARCH"


def pkg(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rejects(fn) -> tuple[bool, str | None]:
    try:
        fn()
    except adapter.FrontendContractError as exc:
        return True, str(exc)
    return False, None


def main() -> int:
    g17 = V17.read_text(encoding="utf-8")
    g7 = V7.read_text(encoding="utf-8")
    g17_sha = sha(g17.encode("utf-8"))

    # Contract-domain falsifier: current v1 frontend contract omits surface identity.
    src = "rule Needle.owns(X)\n"
    v17_a = adapter.identified_frontend(src, g17, surface=V17_SURFACE, strict=True)
    v17_alias_surface = adapter.identified_frontend(src, g17, surface="FAKE_OTHER_SURFACE", strict=True)
    surface_binding = {
        "legacy_contract_equal_across_surface_labels": v17_a["contract_hash"] == v17_alias_surface["contract_hash"],
        "v2_contract_differs_across_surface_labels": v17_a["contract_hash_v2"] != v17_alias_surface["contract_hash_v2"],
    }

    # Exact V17 frontend artifacts must enter typed IR without reparsing.
    artifact_rows = []
    for p in (G9, DIALECT):
        source = p.read_text(encoding="utf-8")
        artifact = adapter.identified_frontend(source, g17, surface=V17_SURFACE, strict=True)
        adapter.validate_artifact(artifact, expected_surface=V17_SURFACE, expected_grammar_sha256=g17_sha)
        artifact_rows.append((p, artifact))
    typed = adapter.build_typed_ir_from_artifacts(
        artifact_rows, expected_surface=V17_SURFACE, expected_grammar_sha256=g17_sha
    )
    typed_ingest = {
        "source_count": len(typed.get("sources", [])),
        "typed_ir_sha256": typed.get("typed_ir_sha256"),
        "program_semantic_id": typed.get("program_semantic_id"),
        "authority_all_none": all(d.get("authority") == "NONE" for d in typed.get("declarations", [])),
        "sources_match_frontend_contracts": all(
            row["grammar_sha256"] == art["grammar_sha256"]
            and row["frontend_semantic_hash"] == art["semantic_hash"]
            for row, (_, art) in zip(typed.get("sources", []), artifact_rows)
        ),
    }

    # Mutation matrix must fail closed.
    base = artifact_rows[0][1]
    mutations = {}
    for name, mutator in {
        "surface_without_rebinding": lambda a: a.__setitem__("surface", "MUTATED_SURFACE"),
        "grammar_hash": lambda a: a.__setitem__("grammar_sha256", "0" * 64),
        "semantic_hash": lambda a: a.__setitem__("semantic_hash", "1" * 64),
        "contract_hash_v2": lambda a: a.__setitem__("contract_hash_v2", "2" * 64),
        "canonical_ast": lambda a: a.__setitem__("canonical_ast", {"kind": "tampered", "children": []}),
    }.items():
        mutated = copy.deepcopy(base)
        mutator(mutated)
        ok, error = rejects(lambda m=mutated: adapter.validate_artifact(m))
        mutations[name] = {"rejected": ok, "error": error}

    expected_surface_reject, expected_surface_error = rejects(
        lambda: adapter.validate_artifact(base, expected_surface="WRONG_SURFACE")
    )
    expected_grammar_reject, expected_grammar_error = rejects(
        lambda: adapter.validate_artifact(base, expected_grammar_sha256="f" * 64)
    )

    # Cross-surface equal-source collision: exact same source has different semantics under
    # current V17 and historical V7. Do not require V7 strict construction here; it is a
    # bounded semantic collision control, while V17 strict remains the admitted baseline.
    v7 = adapter.identified_frontend(src, g7, surface=V7_SURFACE, strict=False)
    collision_reject, collision_error = rejects(
        lambda: adapter.adjudicate_same_source_multi_surface([v17_a, v7])
    )
    cross_surface = {
        "source_sha_equal": v17_a["source_sha256"] == v7["source_sha256"],
        "semantic_hash_equal": v17_a["semantic_hash"] == v7["semantic_hash"],
        "v17_semantic_hash": v17_a["semantic_hash"],
        "v7_semantic_hash": v7["semantic_hash"],
        "collision_rejected": collision_reject,
        "error": collision_error,
    }

    passed = (
        surface_binding["legacy_contract_equal_across_surface_labels"]
        and surface_binding["v2_contract_differs_across_surface_labels"]
        and typed_ingest["source_count"] == 2
        and bool(typed_ingest["typed_ir_sha256"])
        and typed_ingest["authority_all_none"]
        and typed_ingest["sources_match_frontend_contracts"]
        and all(row["rejected"] for row in mutations.values())
        and expected_surface_reject
        and expected_grammar_reject
        and cross_surface["source_sha_equal"]
        and not cross_surface["semantic_hash_equal"]
        and cross_surface["collision_rejected"]
    )

    out = {
        "schema_version": "1.0",
        "experiment": "WP03 explicit FrontendArtifact-to-TypedIR contract discriminator",
        "runtime": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "lark": pkg("lark"),
            "interegular": pkg("interegular"),
            "cpu_count": os.cpu_count(),
            "max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "runner_name": os.environ.get("RUNNER_NAME"),
        },
        "v17_grammar_sha256": g17_sha,
        "surface_binding": surface_binding,
        "typed_artifact_ingest": typed_ingest,
        "mutation_matrix": mutations,
        "expected_surface_guard": {"rejected": expected_surface_reject, "error": expected_surface_error},
        "expected_grammar_guard": {"rejected": expected_grammar_reject, "error": expected_grammar_error},
        "cross_surface_collision": cross_surface,
        "pass": passed,
        "adjudication": "SUPPORTED_RESEARCH_ADAPTER" if passed else "REFUTED_OR_INCOMPLETE",
        "promotion": "NONE",
        "wp03_status_change": "NONE",
        "architecture_delta": "CANDIDATE_EXPLICIT_FRONTEND_ARTIFACT_HANDSHAKE" if passed else "NO_CHANGE",
        "scope_guard": "PASS proves this bounded artifact-ingestion/identity slice only. It does not make v1 surface-unbound contracts safe, close WP02/WP03, select V7, or substitute for Ubuntu/Andreas target acceptance.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
