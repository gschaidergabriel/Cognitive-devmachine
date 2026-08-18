from __future__ import annotations

import json
from typing import Any

from . import secrets, transport

PRESTAGE_MODEL = "mistral-small-latest"

PRESTAGE_SYSTEM = """You are the MISTRAL PRE-STAGE inside EntityOS, a small dedicated entity \
that stands between the human and Zero (Claude Code). Zero never sees the human's literal \
words -- you write what Zero sees. You are given, in CONTEXT: the possibility space \
(memory artefacts, corpus hits), which systems are connected to EntityOS and whether they are \
online, which free-tier APIs and tools are available, and which of exactly two humans \
(gabriel or andreas) is present.

From that you write ONE token-efficient prompt in CAVEMAN ENGLISH (short words, drop articles \
where you can, no filler, imperative mood) that Zero will answer instead of the human's \
original words. It must carry: tool-use selection, memory artefacts that match the topic, \
which sub-work should be outsourced to a free API instead of Zero doing it itself, the \
human's actual intent, what to watch out for, and BOTH a hypothesis and a counter-hypothesis \
about what is really going on or what the right answer is.

Return exactly one JSON object with keys:
caveman_prompt (string -- the actual caveman-English text Zero will receive),
user_intent (string -- plain restatement of what the human wants),
tool_selection (array of strings -- tool/capability names to prefer),
memory_artefacts (array of strings -- memory/topic keys worth pulling in),
outsourced (array of strings -- sub-tasks to hand to a free API instead of Zero doing them),
watch_out (string -- caveman-English warning of pitfalls),
hypotheses (array of 1-3 strings, caveman-English),
counter_hypotheses (array of 1-3 strings, caveman-English alternative explanations).

Never invent facts not present in CONTEXT. If context is thin, say so in watch_out instead of \
guessing."""

_REQUIRED_KEYS = {
    "caveman_prompt",
    "user_intent",
    "tool_selection",
    "memory_artefacts",
    "outsourced",
    "watch_out",
    "hypotheses",
    "counter_hypotheses",
}


def build_context(
    *,
    raw_prompt: str,
    world: dict[str, Any] | None,
    connected_systems: dict[str, Any] | None,
    current_user: str,
) -> str:
    return json.dumps(
        {
            "current_user": current_user,
            "raw_prompt": raw_prompt,
            "world": world or {},
            "connected_systems": connected_systems
            or {"status": "NOT_WIRED", "note": "see M5 -- no connected-systems registry exists yet"},
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def run_prestage(
    *,
    raw_prompt: str,
    world: dict[str, Any] | None = None,
    connected_systems: dict[str, Any] | None = None,
    current_user: str = "gabriel",
    model: str = PRESTAGE_MODEL,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Run the pre-stage once. Returns the caveman-English directive envelope.

    Does not write to the DB itself -- callers (or the wiring the
    coordinator adds to terminal_hooks.py) decide when/whether to persist
    via PrestageStore.record_prestage_turn.
    """
    key = api_key or secrets.load_free_api_keys().get("MISTRAL_API_KEY", "")
    if not key:
        raise RuntimeError("MISTRAL_API_KEY not available")
    if not raw_prompt or len(raw_prompt) > 100_000:
        raise ValueError("invalid raw prompt")
    context = build_context(
        raw_prompt=raw_prompt, world=world, connected_systems=connected_systems, current_user=current_user
    )
    result = transport.mistral_chat_json(
        api_key=key,
        model=model,
        system=PRESTAGE_SYSTEM,
        user=f"CONTEXT:\n{context}",
        temperature=0.2,
        max_tokens=900,
    )
    payload = result["payload"]
    if not isinstance(payload, dict) or not _REQUIRED_KEYS.issubset(payload):
        raise RuntimeError("prestage envelope missing required keys")
    payload = dict(payload)
    payload["prestage_model"] = model
    payload["prestage_receipt"] = result["receipt"]
    return payload
