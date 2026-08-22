from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def test_local_exec_does_not_inherit_parent_environment(tmp_path, monkeypatch):
    """Deterministic regression for the already-admitted local-runner isolation invariant.

    Runtime profile data may select a local runner, but it must not turn the entire
    parent process environment into implicit child authority or a secret side channel.
    """
    model = tmp_path / "fixture.gguf"
    model.write_bytes(b"fixture")

    runner = tmp_path / "emit_env.py"
    runner.write_text(
        "import json, os\n"
        "print(json.dumps({\"sentinel\": os.environ.get(\"CLAY_PARENT_SENTINEL\"), "
        "\"secret\": os.environ.get(\"TOGETHER_API_KEY\")}))\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("CLAY_PARENT_SENTINEL", "must-not-cross")
    monkeypatch.setenv("TOGETHER_API_KEY", "must-not-cross-secret")

    runtime = ProfilePipelineRuntime(root=tmp_path)
    result = runtime.effect(
        "inference_generate",
        {
            "inference": {
                "kind": "local_exec",
                "model": "fixture",
                "local_model_path": str(model),
                "argv": [sys.executable, str(runner), "{{MODEL_PATH}}", "{{PROMPT_FILE}}"],
                "response_content": "json_string",
                "max_tokens": 8,
                "temperature": 0.0,
            },
            "system": "system",
            "user": "user",
            "secret_file": "",
        },
    )

    assert result["ok"] is True
    assert result["payload"]["sentinel"] is None
    assert result["payload"]["secret"] is None
