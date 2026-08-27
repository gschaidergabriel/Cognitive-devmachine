from __future__ import annotations

from dataclasses import dataclass
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import free_swarm_accelerator_v2 as accelerator  # noqa: E402


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

    @staticmethod
    def worker_prompt(protocol: str, role: str, task: str, state_context: str, serial: int) -> str:
        return "old"


class Opt:
    CATALOGS = {}
    PROVIDER_MODEL_CAP = {}


def _prompt() -> str:
    accelerator.install(Base, Opt)
    return Base.worker_prompt("PROTOCOL", "TESTER", "task", "state", 7)


def test_machine_readable_skeleton_is_explicitly_not_forge_ready() -> None:
    prompt = _prompt()
    match = re.search(r"ARCHITECTURE_DELTA_JSON=(\{.*\})", prompt)
    assert match is not None
    proposal = json.loads(match.group(1))
    assert proposal["ready_for_forge"] is False
    assert proposal["patch_unified_diff"] == ""
    assert proposal["target_files"] == []
    assert proposal["test_commands"] == []


def test_prompt_forbids_empty_patch_with_ready_true() -> None:
    prompt = _prompt()
    assert "never label an empty patch as Forge-ready" in prompt
    assert "actual applicable unified diff" in prompt
    assert "only then switch `ready_for_forge` to true" in prompt
    assert '"ready_for_forge":true' not in prompt


def test_ready_contract_requires_all_forge_inputs() -> None:
    prompt = _prompt()
    assert "`target_files`, `patch_unified_diff`, and `test_commands` must all be non-empty" in prompt
    assert "`falsifier` must be concrete" in prompt
