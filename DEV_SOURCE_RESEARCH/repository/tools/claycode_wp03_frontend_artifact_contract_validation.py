#!/usr/bin/env python3
"""Bounded WP03 validation for the explicit FrontendArtifact -> TypedIR adapter.

This is a research/acceptance discriminator, not a package promotion. It verifies that the
adapter binds surface+grammar+AST semantic identity, fails closed on tampering and ambiguous
cross-surface admission, and measures whether the downstream current-main typed IR can consume
a grammar-admitted keyword identifier without the separate AST-context identifier repair.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import statistics
import time
from pathlib import Path
from typing import Any, Callable

import claycode_base_frontend as front
import claycode_wp03_frontend_artifact_contract as fac

ROOT = Path(__file__).resolve().parents[1]
V17 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
V7 = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"
SURFACE_V17 = "BASE_D_V17_DECLARATIVE_TRIVIA_SAFE"
SURFACE_V7 = "BASE_D_V7_OPERATOR_FN"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pkg(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def expect_contract_error(fn: Callable[[], Any]) -> str:
    try:
        fn()
    except fac.FrontendContractError as exc:
        return str(exc)
    raise AssertionError("expected FrontendContractError")


def p(values: list[float], q: float) -> float:
    xs = sorted(values)
    pos = (len(xs) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    f = pos - lo
    return xs[lo] * (1 - f) + xs[hi] * f


def main() -> int:
    g17 = V17.read_text(encoding="utf-8")
    g7 = V7.read_text(encoding="utf-8")
    g17_sha = sha(g17.encode("utf-8"))

    source = "record Sample { id:Int }\n"
    timings: list[float] = []
    artifact = None
    for _ in range(7):
        t0 = time.perf_counter_ns()
        artifact = fac.identified_frontend(source, g17, surface=SURFACE_V17, strict=True)
        fac.validate_artifact(artifact, expected_surface=SURFACE_V17, expected_grammar_sha256=g17_sha)
        timings.append((time.perf_counter_ns() - t0) / 1_000_000)
    assert artifact is not None

    ir = fac.build_typed_ir_from_artifacts(
        [(Path("Sample.clay"), artifact)],
        expected_surface=SURFACE_V17,
        expected_grammar_sha256=g17_sha,
    )
    simple_ir_ok = any(d.get("kind") == "record" and d.get("name") == "Sample" for d in ir["declarations"])

    tamper_errors: dict[str, str] = {}
    changed = copy.deepcopy(artifact)
    changed["surface"] = "OTHER"
    tamper_errors["surface_without_contract_rebind"] = expect_contract_error(lambda: fac.validate_artifact(changed))

    changed = copy.deepcopy(artifact)
    changed["grammar_sha256"] = "0" * 64
    tamper_errors["grammar_identity"] = expect_contract_error(
        lambda: fac.validate_artifact(changed, expected_grammar_sha256=g17_sha)
    )

    changed = copy.deepcopy(artifact)
    changed["canonical_ast"]["children"] = []
    tamper_errors["ast_semantic_hash"] = expect_contract_error(lambda: fac.validate_artifact(changed))

    changed = copy.deepcopy(artifact)
    changed["contract_hash_v2"] = "f" * 64
    tamper_errors["contract_hash"] = expect_contract_error(lambda: fac.validate_artifact(changed))

    # Same source + same semantic hash across two named surfaces still requires explicit
    # equivalence evidence; equality by accident must not become cross-dialect authority.
    alias = copy.deepcopy(artifact)
    alias["surface"] = "ALIAS_V17_TEST_SURFACE"
    alias["contract_hash_v2"] = fac.contract_hash(
        surface=alias["surface"],
        grammar_sha256=alias["grammar_sha256"],
        semantic_hash=alias["semantic_hash"],
    )
    missing_equivalence_error = expect_contract_error(
        lambda: fac.adjudicate_same_source_multi_surface([artifact, alias])
    )
    collision = fac.adjudicate_same_source_multi_surface(
        [artifact, alias], equivalence_evidence_id="TEST-ONLY-EQUIVALENCE"
    )
    explicit_equivalence_ok = collision is not None and len(collision.surfaces) == 2

    # Deliberate cross-surface collision: the exact same source is accepted by selected V17
    # and older V7 but the AST meaning differs (call vs dotted relation). The adapter must reject.
    collision_source = "rule Needle.owns(X)\n"
    v17_collision = fac.identified_frontend(collision_source, g17, surface=SURFACE_V17, strict=False)
    v7_collision = fac.identified_frontend(collision_source, g7, surface=SURFACE_V7, strict=False)
    cross_surface_semantic_diff = v17_collision["semantic_hash"] != v7_collision["semantic_hash"]
    semantic_collision_error = expect_contract_error(
        lambda: fac.adjudicate_same_source_multi_surface(
            [v17_collision, v7_collision], equivalence_evidence_id="MUST-NOT-OVERRIDE-DIFFERENT-SEMANTICS"
        )
    )

    # The adapter intentionally does not contain the separate typed-IR keyword-alias repair.
    # Reproduce that remaining boundary bug on current main so the adapter cannot be overpromoted.
    keyword_source = "record status { status:Symbol }\n"
    keyword_artifact = fac.identified_frontend(keyword_source, g17, surface=SURFACE_V17, strict=True)
    keyword_error = None
    keyword_shape = None
    try:
        keyword_ir = fac.build_typed_ir_from_artifacts(
            [(Path("keyword.clay"), keyword_artifact)],
            expected_surface=SURFACE_V17,
            expected_grammar_sha256=g17_sha,
        )
        keyword_shape = keyword_ir.get("declarations")
    except Exception as exc:  # exact downstream class is evidence, not authority
        keyword_error = f"{type(exc).__name__}: {exc}"
    downstream_keyword_alias_bug_reproduced = keyword_error is not None or not any(
        d.get("kind") == "record"
        and d.get("name") == "status"
        and d.get("fields") == [{"name": "status", "type": "Symbol", "default_tokens": None}]
        for d in (keyword_shape or [])
    )

    passed = (
        simple_ir_ok
        and len(tamper_errors) == 4
        and explicit_equivalence_ok
        and bool(missing_equivalence_error)
        and cross_surface_semantic_diff
        and bool(semantic_collision_error)
        and downstream_keyword_alias_bug_reproduced
    )

    out = {
        "schema_version": "1.0",
        "experiment": "CC-WP-03 FrontendArtifact contract boundary validation",
        "evidence_class": "EXECUTABLE_BOUNDED_RESEARCH_DIFFERENTIAL",
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
        "identity": {
            "v17_sha256": g17_sha,
            "v7_sha256": sha(g7.encode("utf-8")),
            "adapter_sha256": sha((ROOT / "tools/claycode_wp03_frontend_artifact_contract.py").read_bytes()),
            "typed_ir_sha256": sha((ROOT / "tools/claycode_base_typed_ir.py").read_bytes()),
        },
        "timing_ms": {
            "n": len(timings),
            "mean": statistics.fmean(timings),
            "p50": p(timings, 0.50),
            "p90": p(timings, 0.90),
            "p95": p(timings, 0.95),
            "p99": p(timings, 0.99),
            "min": min(timings),
            "max": max(timings),
        },
        "checks": {
            "simple_frontend_artifact_to_typed_ir": simple_ir_ok,
            "tamper_fail_closed": bool(tamper_errors),
            "same_semantics_requires_explicit_equivalence_evidence": bool(missing_equivalence_error),
            "same_semantics_with_explicit_test_evidence_admitted": explicit_equivalence_ok,
            "same_source_v17_v7_semantic_diff": cross_surface_semantic_diff,
            "different_semantics_cross_surface_fail_closed": bool(semantic_collision_error),
            "downstream_keyword_alias_bug_reproduced": downstream_keyword_alias_bug_reproduced,
        },
        "tamper_errors": tamper_errors,
        "missing_equivalence_error": missing_equivalence_error,
        "semantic_collision_error": semantic_collision_error,
        "keyword_error": keyword_error,
        "keyword_shape": keyword_shape,
        "pass": passed,
        "classification": (
            "ADAPTER_MECHANISM_SUPPORTED_DOWNSTREAM_TYPED_IR_ALIAS_BLOCKER_REMAINS"
            if passed else "UNRESOLVED_OR_REFUTED"
        ),
        "architecture_delta": (
            "KEEP explicit frontend-artifact identity boundary; DO_NOT promote adapter alone. Compose/test it with the AST-context keyword-identifier repair, then replay current G9+Dialect and Ubuntu differential receipts."
            if passed else "NO_CHANGE_PENDING_DIAGNOSIS"
        ),
        "promotion": "NONE",
        "authority": "NONE",
        "scope_guard": "Research-only boundary test. It neither closes WP03/BASE nor counts as registered Andreas Ubuntu acceptance.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
