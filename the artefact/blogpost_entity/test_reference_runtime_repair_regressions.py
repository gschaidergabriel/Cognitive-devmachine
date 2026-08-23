from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def test_local_exec_fails_closed_without_runtime_admitted_runner(tmp_path: Path) -> None:
    model = tmp_path / "model.gguf"
    model.write_bytes(b"test-model-placeholder")
    runtime = ProfilePipelineRuntime(root=tmp_path)
    result = runtime.effect(
        "inference_generate",
        {
            "inference": {
                "kind": "local_exec",
                "local_model_path": str(model),
                "local_args_json": [],
            },
            "system": "s",
            "user": "u",
        },
    )
    assert result["ok"] is False
    assert "LOCAL_EXEC_NOT_ADMITTED" in result["error"]


def test_local_exec_uses_runtime_runner_not_profile_command(tmp_path: Path) -> None:
    model = tmp_path / "model.gguf"
    model.write_bytes(b"test-model-placeholder")
    runner = tmp_path / "runner.py"
    runner.write_text(
        "import json\nprint(json.dumps({'source': 'trusted-runtime-runner'}))\n",
        encoding="utf-8",
    )
    runtime = ProfilePipelineRuntime(
        root=tmp_path,
        local_exec_runner=[sys.executable, str(runner)],
    )
    result = runtime.effect(
        "inference_generate",
        {
            "inference": {
                "kind": "local_exec",
                "local_model_path": str(model),
                "local_args_json": [],
                # Historical donor keys must not regain process authority.
                "local_argv_json": ["/definitely/not/admitted"],
                "argv": ["/also/not/admitted"],
            },
            "system": "s",
            "user": "u",
        },
    )
    assert result["ok"] is True
    assert result["payload"] == {"source": "trusted-runtime-runner"}
    assert result["provider_kind"] == "local_exec"


def test_runtime_runner_can_be_parameterized_by_bounded_profile_args(tmp_path: Path) -> None:
    model = tmp_path / "model.gguf"
    model.write_bytes(b"test-model-placeholder")
    runner = tmp_path / "runner.py"
    runner.write_text(
        "import json,sys\nprint(json.dumps({'args': sys.argv[1:]}))\n",
        encoding="utf-8",
    )
    runtime = ProfilePipelineRuntime(
        root=tmp_path,
        local_exec_runner=[sys.executable, str(runner)],
    )
    result = runtime.effect(
        "inference_generate",
        {
            "inference": {
                "kind": "local_exec",
                "local_model_path": str(model),
                "local_args_json": ["{{MODEL_PATH}}", "{{MAX_TOKENS}}"],
                "max_tokens": 17,
            },
            "system": "s",
            "user": "u",
        },
    )
    assert result["ok"] is True
    assert result["payload"]["args"] == [str(model), "17"]
