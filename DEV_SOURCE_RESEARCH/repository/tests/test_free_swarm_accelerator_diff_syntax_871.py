from __future__ import annotations

from dataclasses import dataclass
import json
import re

from tools.free_swarm_accelerator_v2 import install


@dataclass(frozen=True)
class Spec:
    name: str
    endpoint: str
    key_envs: tuple[str, ...]
    keys_list_env: str
    models_env: str
    default_models: tuple[str, ...]
    attestation_env: str
    default_max_concurrency: int


class Runtime:
    def __init__(self, spec, keys, models, max_concurrency):
        self.spec = spec
        self.keys = keys
        self.models = models
        self.max_concurrency = max_concurrency
        self._condition = None
        self.successes = 0
        self.success_streak = 0
        self.rate_backoff = 1.0
        self.target_concurrency = 1
        self.rate_limits = 0
        self.cooldown_until = 0.0
        self.errors = 0

    def snapshot(self):
        return {}


class Base:
    ProviderSpec = Spec
    ProviderRuntime = Runtime
    PROVIDERS = (
        Spec(
            "groq",
            "https://api.groq.com/openai/v1/chat/completions",
            ("GROQ_API_KEY",),
            "GROQ_API_KEYS",
            "GROQ_SWARM_MODELS",
            ("openai/gpt-oss-20b",),
            "CLAY_GROQ_FREE_ATTESTED",
            12,
        ),
    )


class Opt:
    CATALOGS = {}
    PROVIDER_MODEL_CAP = {}


def _prompt() -> str:
    install(Base, Opt)
    return Base.worker_prompt("PROTOCOL", "CLAYCODE_FORGE", "task", "state", 7)


def test_nonready_json_skeleton_survives_successor_hardening() -> None:
    prompt = _prompt()
    match = re.search(r"ARCHITECTURE_DELTA_JSON=(\{.*\})", prompt)
    assert match is not None
    proposal = json.loads(match.group(1))
    assert proposal["ready_for_forge"] is False
    assert proposal["patch_unified_diff"] == ""


def test_forge_ready_contract_teaches_exact_git_diff_shape() -> None:
    prompt = _prompt()
    assert "`--- a/<path>` and `+++ b/<path>` headers" in prompt
    assert "`@@ -old,count +new,count @@` hunks" in prompt
    assert "Hunk counts must match the emitted lines" in prompt
    assert "body lines beginning with space/+/-." in prompt


def test_machine_readable_diff_forbids_common_observed_failure_shapes() -> None:
    prompt = _prompt()
    assert "Encode patch newlines inside the one-line JSON value as `\\n` escapes" in prompt
    assert "Never wrap the machine-readable JSON in Markdown fences" in prompt
    assert "never use ellipses/pseudo-diff placeholders" in prompt
