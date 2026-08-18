from __future__ import annotations

import time
from typing import Any

from .. import identity  # coordinator-owned, imported not edited
from . import headless_zero, prestage, translator
from .prestage import MAX_ROUNDS, NEGOTIATION_SENTINEL
from .store import PrestageStore

CANONICAL_USERS = {"gabriel", "andreas"}


class PipelineError(RuntimeError):
    pass


def _gather_world_safe(db, session_id: str) -> dict[str, Any]:
    """Read-only world assembly, no turn admission.

    Uses clayverse.retrieval.WorldAssembler directly instead of
    TurnLifecycle.begin_admission() so context can be gathered WITHOUT writing
    a turn. WorldAssembler.assemble() already has a no-active-turn fallback
    path (the "LEGACY_COMPATIBILITY" branch) for exactly this case -- it is
    not a hack, it is the path the module already ships for callers with no
    active causal turn.
    """
    from .. import retrieval  # coordinator-owned module, imported not edited

    assembler = retrieval.WorldAssembler(db)
    return assembler.assemble(session_id, resource_refs=[])


def run_chat_turn(
    *,
    db,
    user_id: str,
    session_id: str,
    message: str,
    store: PrestageStore | None = None,
    record_via_turnlifecycle: bool = False,
    tool_selection: list[str] | None = None,
) -> dict[str, Any]:
    """The one interface: German message in, German reply out.

    record_via_turnlifecycle=False (default, SAFE): does not touch
    turns/active_turns at all. Records the exchange only in this module's own
    mv_prestage_turns/mv_translation_log tables. Use this until
    terminal_hooks.py is patched to recognize CLAYVERSE_PIPELINE_MANAGED and
    stop independently admitting its own colliding turn on every headless call.

    record_via_turnlifecycle=True (P4 TARGET, NOT YET SAFE TO ENABLE): uses
    TurnLifecycle.begin_admission()/.complete() -- the product's own atomic
    admission primitives, reused rather than reimplemented, exactly as asked.
    Do not enable this against a real canonical session until the hook
    collision described in headless_zero.py's docstring is fixed -- two
    independent admitters (this function AND the managed UserPromptSubmit/Stop
    hooks firing on the same claude -p call) will both try to own the same
    session's active_turns row.

    Returns the interface contract (see report): turn_id, causal_id, reply,
    rounds_used, self_adapted, elapsed_ms, tool_selection.
    """
    if user_id not in CANONICAL_USERS or not identity.ist_kanonische_sitzung(session_id, user_id):
        raise PipelineError("invalid canonical user/session")
    if not isinstance(message, str) or not message.strip():
        raise PipelineError("empty message")

    own_store = store or PrestageStore()
    t_start = time.perf_counter()
    lifecycle = None
    admission = None

    try:
        if record_via_turnlifecycle:
            from .. import turn_lifecycle  # coordinator-owned, imported not edited

            lifecycle = turn_lifecycle.TurnLifecycle(db, user_id, session_id)
            admission = lifecycle.begin(message)
            world = admission["context"]
            turn_id = admission["turn_id"]
            causal_id = admission["causal_id"]
        else:
            world = _gather_world_safe(db, session_id)
            turn_id = None
            causal_id = None

        recent_turns = [
            {"role": t.get("role"), "content": t.get("content")}
            for t in (world.get("own_recent") or [])[-3:]
        ]

        # --- round 1 ---
        t0 = time.perf_counter()
        envelope = prestage.run_prestage(
            raw_prompt=message, world=world, current_user=user_id,
            recent_turns=recent_turns, round_no=1,
        )
        prestage_ms = (time.perf_counter() - t0) * 1000.0

        selected_tools = tool_selection or [
            t for t in envelope.get("tool_selection", []) if isinstance(t, str) and t.startswith("mcp__clayverse__")
        ] or None

        t0 = time.perf_counter()
        zero = headless_zero.run_headless(
            envelope["caveman_prompt"], user_id=user_id, session_id=session_id,
            tool_selection=selected_tools,
        )
        zero_ms = (time.perf_counter() - t0) * 1000.0
        rounds_used = 1
        self_adapted = False

        if zero["caveman_answer"].strip().startswith(NEGOTIATION_SENTINEL):
            suggestion = zero["caveman_answer"].split(NEGOTIATION_SENTINEL, 1)[1].strip()
            t0 = time.perf_counter()
            envelope2 = prestage.run_prestage(
                raw_prompt=message, world=world, current_user=user_id,
                recent_turns=recent_turns, round_no=2, zero_suggestion=suggestion,
            )
            prestage_ms += (time.perf_counter() - t0) * 1000.0
            t0 = time.perf_counter()
            zero = headless_zero.run_headless(
                envelope2["caveman_prompt"], user_id=user_id, session_id=session_id,
                tool_selection=selected_tools,
            )
            zero_ms += (time.perf_counter() - t0) * 1000.0
            rounds_used = MAX_ROUNDS
            self_adapted = True
            envelope = envelope2
            if zero["caveman_answer"].strip().startswith(NEGOTIATION_SENTINEL):
                # F74 hard counter: round 2 has no escape hatch in its own prompt.
                # If Zero used it anyway, that is a prompt-compliance failure to
                # surface loudly, not silently retry a third time.
                raise PipelineError(
                    "Zero used the negotiation sentinel on round 2 despite it being withdrawn -- "
                    "prompt compliance failure, not a data gap"
                )

        t0 = time.perf_counter()
        german = translator.translate_to_german(zero["caveman_answer"])
        translate_ms = (time.perf_counter() - t0) * 1000.0

        prestage_id = own_store.record_prestage_turn(
            turn_id=turn_id, session_id=session_id, user_id=user_id,
            raw_prompt=message, connected_systems={"status": "NOT_WIRED"},
            caveman_prompt=envelope["caveman_prompt"],
            tool_selection=envelope.get("tool_selection", []),
            memory_artefacts=envelope.get("memory_artefacts", []),
            outsourced=envelope.get("outsourced", []),
            user_intent=envelope.get("user_intent", ""),
            watch_out=envelope.get("watch_out", ""),
            hypotheses=envelope.get("hypotheses", []),
            counter_hypotheses=envelope.get("counter_hypotheses", []),
            prestage_model=envelope.get("prestage_model"),
            prestage_receipt=envelope.get("prestage_receipt", {}),
        )
        translation_id = own_store.record_translation(
            turn_id=turn_id, prestage_id=prestage_id,
            caveman_original=zero["caveman_answer"], german_translation=german["german_translation"],
            translator_model=german["translator_model"], translator_receipt=german["translator_receipt"],
        )

        if record_via_turnlifecycle and lifecycle is not None:
            lifecycle.complete(zero["caveman_answer"])

        total_ms = (time.perf_counter() - t_start) * 1000.0
        return {
            "turn_id": turn_id,
            "causal_id": causal_id,
            "prestage_id": prestage_id,
            "translation_id": translation_id,
            "reply": german["german_translation"],
            "caveman": zero["caveman_answer"],
            "rounds_used": rounds_used,
            "self_adapted": self_adapted,
            "tool_selection": selected_tools or [],
            "elapsed_ms": {
                "prestage_ms": round(prestage_ms, 1),
                "zero_ms": round(zero_ms, 1),
                "translate_ms": round(translate_ms, 1),
                "total_ms": round(total_ms, 1),
            },
        }
    except Exception:
        if record_via_turnlifecycle and lifecycle is not None:
            try:
                lifecycle.abort("pipeline_failure")
            except Exception:
                pass
        raise
    finally:
        if store is None:
            own_store.close()
