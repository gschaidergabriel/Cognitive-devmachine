from __future__ import annotations

import inspect
import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def _runner_parameter() -> str | None:
    """Return the trusted Runtime runner/executor admission parameter, if present."""
    markers = ("runner", "executor", "exec_capability", "process_capability")
    for name in inspect.signature(ProfilePipelineRuntime).parameters:
        if name in {"self", "root", "allow_network", "provider_override"}:
            continue
        if any(marker in name.lower() for marker in markers):
            return name
    return None


def test_future_local_exec_binds_declared_model_artifact_to_runner_invocation(tmp_path: Path) -> None:
    """A declared local model must not be a decoy admission token.

    The 2026-08-23 GO falsifier showed that a readable fake model plus an unrelated command
    can satisfy the old donor shape. PR #1012 separately binds executable authority to trusted
    Runtime admission. This behavioral guard closes the orthogonal inference-identity edge:
    after local_exec convergence, a profile declaring `local_model_path` must bind that exact
    artifact into the admitted runner invocation. Omitting the model binding must fail closed
    before the runner is executed.
    """
    if not hasattr(ProfilePipelineRuntime, "_inference_local_exec"):
        # Legacy canonical main has not converged local_exec yet. Activate automatically when
        # the generic local cognition backend lands.
        return

    runner_param = _runner_parameter()
    assert runner_param is not None, (
        "local_exec exists without trusted Runtime runner admission; PR #1012 capability "
        "authority must be satisfied first"
    )

    echo = shutil.which("echo")
    if echo is None:
        pytest.skip("portable harmless runner unavailable")

    model = tmp_path / "declared-model.gguf"
    model.write_bytes(b"bounded-fake-model-for-binding-test")
    runtime = ProfilePipelineRuntime(root=tmp_path, **{runner_param: echo})

    # Intentionally provide only harmless runner arguments and no {{MODEL_PATH}} binding.
    # Supplying both narrow aliases keeps the test representation-neutral while refusing the
    # obsolete profile-owned full-command surface.
    inference = {
        "kind": "local_exec",
        "local_model_path": str(model),
        "local_args_json": ["{}"],
        "args": ["{}"],
        "local_env_allowlist": [],
        "secret_names": [],
        "timeout_seconds": 5,
    }
    result = runtime.effect(
        "inference_generate",
        {
            "inference": inference,
            "system": "bounded-system",
            "user": "bounded-user",
            "secret_file": "",
        },
    )

    assert result["ok"] is False, (
        "local_exec executed an admitted runner without binding the declared model artifact"
    )
    assert "LOCAL_MODEL_BINDING_REQUIRED" in str(result.get("error", "")), (
        "model-binding omission must have a distinct fail-closed state rather than collapsing "
        "into an unrelated argv/provider/runtime error"
    )
