from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def test_reference_local_exec_does_not_inherit_parent_provider_secret(tmp_path, monkeypatch):
    """A configured local model runner must not inherit unrelated parent secrets."""
    sentinel = "clay-reference-parent-secret-sentinel"
    monkeypatch.setenv("MISTRAL_API_KEY", sentinel)

    model = tmp_path / "model.gguf"
    model.write_bytes(b"fixture-model")

    runner = tmp_path / "runner.py"
    runner.write_text(
        "import json, os\n"
        "print(json.dumps({'leaked': os.environ.get('MISTRAL_API_KEY')}))\n",
        encoding="utf-8",
    )

    runtime = ProfilePipelineRuntime(root=tmp_path)
    result = runtime._inference_local_exec(
        {
            "kind": "local_exec",
            "model_path": str(model),
            "argv": [sys.executable, str(runner)],
            "response_content": "json_string",
            "timeout_seconds": 10,
        },
        {"system": "system", "user": "user"},
    )

    assert result["ok"] is True
    assert result["payload"] == {"leaked": None}
    assert sentinel not in json.dumps(result, sort_keys=True)
