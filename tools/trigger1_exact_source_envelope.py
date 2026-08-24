#!/usr/bin/env python3
"""Exact-source envelope for the local Qwen3-0.6B intermediate J-Space experiment.

This wrapper does not change the scientific intervention. It strengthens evidence binding:
- captures HEAD/tree plus a cryptographic commitment to tracked/staged/untracked dirty state;
- binds the wrapper and delegated executor/launcher bytes;
- requires source identity to remain stable across the model run;
- binds the delegated result digest, local endpoint, runtime manifest, checkpoint/tokenizer;
- removes any promotion candidate when exact-source binding fails.

No canonical/whole-product/J-Space promotion is minted by this envelope alone.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable

SCHEMA = "CLAY_TRIGGER1_EXACT_SOURCE_ENVELOPE/v1"
RESULT_NAME = "trigger1_intermediate_result.json"
CANDIDATE_NAME = "trigger1_intermediate_candidate.json"
RECEIPT_NAME = "trigger1_intermediate_exact_source_receipt.json"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_sha(obj: Any) -> str:
    return _sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def _git(root: Path, *args: str) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", "replace")[:500]
        raise RuntimeError(f"GIT_IDENTITY_FAILED:{' '.join(args)}:{proc.returncode}:{detail}")
    return proc.stdout


def _path_manifest_entry(root: Path, rel_bytes: bytes) -> dict[str, Any]:
    rel = rel_bytes.decode("utf-8", "surrogateescape")
    path = root / rel
    path_commitment = _sha256_bytes(rel_bytes)
    if path.is_symlink():
        target = os.readlink(path).encode("utf-8", "surrogateescape")
        return {
            "path_sha256": path_commitment,
            "kind": "symlink",
            "target_sha256": _sha256_bytes(target),
        }
    if path.is_file():
        return {
            "path_sha256": path_commitment,
            "kind": "file",
            "size": path.stat().st_size,
            "content_sha256": _sha256_file(path),
        }
    return {"path_sha256": path_commitment, "kind": "other"}


def capture_source_identity(root: Path, executor_paths: Iterable[Path]) -> dict[str, Any]:
    root = root.resolve()
    head = _git(root, "rev-parse", "HEAD").decode().strip()
    tree = _git(root, "rev-parse", "HEAD^{tree}").decode().strip()
    status = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    unstaged = _git(root, "diff", "--binary", "HEAD", "--", ".")
    staged = _git(root, "diff", "--cached", "--binary", "HEAD", "--", ".")
    untracked_raw = _git(root, "ls-files", "--others", "--exclude-standard", "-z")
    untracked_paths = [p for p in untracked_raw.split(b"\0") if p]
    untracked_manifest = [_path_manifest_entry(root, p) for p in sorted(untracked_paths)]

    executors = []
    for item in executor_paths:
        p = item.resolve()
        try:
            rel = p.relative_to(root).as_posix()
        except ValueError:
            rel = str(p)
        executors.append({
            "path": rel,
            "exists": p.is_file(),
            "size": p.stat().st_size if p.is_file() else None,
            "sha256": _sha256_file(p) if p.is_file() else None,
        })

    material = {
        "repo_head": head,
        "repo_tree": tree,
        "dirty": bool(status),
        "status_porcelain_v1_z_sha256": _sha256_bytes(status),
        "unstaged_diff_binary_sha256": _sha256_bytes(unstaged),
        "staged_diff_binary_sha256": _sha256_bytes(staged),
        "untracked_manifest": untracked_manifest,
        "executors": executors,
    }
    material["source_identity_sha256"] = _canonical_sha(material)
    return material


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def build_envelope(
    *,
    root: Path,
    out_dir: Path,
    pre: dict[str, Any],
    post: dict[str, Any],
    delegated_returncode: int,
) -> tuple[dict[str, Any], bool]:
    result_path = out_dir / RESULT_NAME
    candidate_path = out_dir / CANDIDATE_NAME
    if not result_path.is_file():
        raise RuntimeError("DELEGATED_RESULT_MISSING")

    raw_result = result_path.read_bytes()
    result = json.loads(raw_result)
    if not isinstance(result, dict):
        raise RuntimeError("DELEGATED_RESULT_NOT_OBJECT")

    source = result.get("source") if isinstance(result.get("source"), dict) else {}
    runtime = result.get("runtime_manifest") if isinstance(result.get("runtime_manifest"), dict) else {}
    endpoint = result.get("api_endpoint")

    source_stable = pre.get("source_identity_sha256") == post.get("source_identity_sha256")
    delegated_source_match = (
        source.get("repo_head") == pre.get("repo_head")
        and source.get("repo_tree") == pre.get("repo_tree")
    )
    runtime_bound = all(runtime.get(key) for key in (
        "python_version",
        "python_executable_sha256",
        "torch_version",
        "torch_module_sha256",
        "transformers_version",
        "transformers_module_sha256",
    ))
    model_bound = all(result.get(key) for key in (
        "model_revision", "checkpoint_sha256", "tokenizer_sha256"
    ))
    loopback_bound = isinstance(endpoint, str) and endpoint.startswith("http://127.0.0.1:")
    provider_fence = (
        result.get("zero_provider_billing") is True
        and result.get("external_provider_credentials_read") is False
        and result.get("provider_network_calls") == 0
    )
    exact_source_bound = bool(source_stable and delegated_source_match and runtime_bound and model_bound and loopback_bound and provider_fence)

    original_candidate_present = candidate_path.is_file()
    original_candidate_sha = _sha256_file(candidate_path) if original_candidate_present else None
    if not exact_source_bound and candidate_path.exists():
        candidate_path.unlink()

    envelope = {
        "schema": SCHEMA,
        "status": "PASS_EXACT_SOURCE_BINDING" if exact_source_bound else "BLOCKED_EXACT_SOURCE_BINDING",
        "credit_scope": "LOCAL_QWEN06_INTERMEDIATE_EXACT_SOURCE_BINDING_ONLY",
        "canonical_or_whole_product_credit": 0,
        "jspace_model_runtime_credit": 0,
        "training_credit": 0,
        "delegated_returncode": delegated_returncode,
        "delegated_experiment_status": result.get("status"),
        "source_identity_pre": pre,
        "source_identity_post": post,
        "source_stable_across_run": source_stable,
        "delegated_source_matches_pre": delegated_source_match,
        "delegated_result_sha256": _sha256_bytes(raw_result),
        "runtime_manifest": runtime,
        "runtime_build_sha256": result.get("runtime_build_sha256"),
        "model": result.get("model"),
        "model_revision": result.get("model_revision"),
        "checkpoint_sha256": result.get("checkpoint_sha256"),
        "tokenizer_sha256": result.get("tokenizer_sha256"),
        "api_endpoint": endpoint,
        "api_loopback_only": result.get("api_loopback_only") is True and loopback_bound,
        "zero_provider_billing": result.get("zero_provider_billing") is True,
        "external_provider_credentials_read": result.get("external_provider_credentials_read"),
        "provider_network_calls": result.get("provider_network_calls"),
        "runtime_required_fields_bound": runtime_bound,
        "model_identity_bound": model_bound,
        "provider_fence_pass": provider_fence,
        "original_candidate_present": original_candidate_present,
        "original_candidate_sha256": original_candidate_sha,
        "promotion_candidate_retained": candidate_path.is_file(),
        "evidence_boundary": "Binds exact local execution identity only; scientific PASS/negative stays at delegated measured scope and does not mint canonical EntityOS/HCU/J-Space/training credit.",
    }
    envelope["receipt_sha256"] = _canonical_sha(envelope)
    return envelope, exact_source_bound


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--repo-root", default=None)
    ap.add_argument("--launcher", default="tools/trigger1_local_qwen06_intermediate.sh")
    args = ap.parse_args()

    root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[1]
    out_dir = Path(args.output_dir).resolve()
    if _inside(out_dir, root):
        raise SystemExit("OUTPUT_DIR_MUST_BE_OUTSIDE_REPOSITORY_FOR_STABLE_DIRTY_STATE")
    out_dir.mkdir(parents=True, exist_ok=True)

    wrapper = Path(__file__).resolve()
    launcher = (root / args.launcher).resolve()
    delegated_py = (root / "tools/trigger1_local_qwen06_intermediate_execute.py").resolve()
    protocol_py = (root / "tools/trigger1_intermediate_contrastive_protocol.py").resolve()
    activation_py = (root / "tools/trigger1_local_qwen06_activation_api_execute.py").resolve()
    executor_paths = [wrapper, launcher, delegated_py, protocol_py, activation_py]
    for path in executor_paths:
        if not path.is_file():
            raise SystemExit(f"EXECUTOR_MISSING:{path}")

    pre = capture_source_identity(root, executor_paths)
    proc = subprocess.run(["bash", str(launcher), str(out_dir)], cwd=str(root), check=False)
    post = capture_source_identity(root, executor_paths)

    try:
        envelope, exact = build_envelope(
            root=root,
            out_dir=out_dir,
            pre=pre,
            post=post,
            delegated_returncode=proc.returncode,
        )
    except Exception as exc:
        envelope = {
            "schema": SCHEMA,
            "status": "BLOCKED_EXACT_SOURCE_BINDING",
            "credit_scope": "NONE",
            "canonical_or_whole_product_credit": 0,
            "jspace_model_runtime_credit": 0,
            "training_credit": 0,
            "delegated_returncode": proc.returncode,
            "reason": f"{type(exc).__name__}:{str(exc)[:1200]}",
            "source_identity_pre": pre,
            "source_identity_post": post,
        }
        envelope["receipt_sha256"] = _canonical_sha(envelope)
        exact = False
        candidate = out_dir / CANDIDATE_NAME
        if candidate.exists():
            candidate.unlink()

    receipt = out_dir / RECEIPT_NAME
    receipt.write_text(json.dumps(envelope, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    if not exact:
        return 4
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
