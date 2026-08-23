from __future__ import annotations

"""Fail-closed tombstone for the retired Mistral/custom-engine acceptance path.

The current ClayVerse product surface is Clerk-authenticated browser -> WebSocket PTY ->
persistent tmux -> normal interactive Claude Code with managed lifecycle hooks.  The
historical internal Mistral/``ClayVerseEngine.ingest`` acceptance probe is not part of
that product runtime and must never be reactivated merely because old CLI glue still
imports this module.

This tiny compatibility module intentionally imports no retired inference adapter or
custom-engine code.  Keeping the symbol fail-closed prevents the production service
import graph from reaching Python modules that are deliberately excluded from the OCI
build context while making any stale ``--mistral-once`` invocation explicit.
"""

from typing import Any


RETIRED_REASON = (
    "MISTRAL_ACCEPTANCE_PROBE_RETIRED: use the canonical Clerk/WebSocket-PTY/"
    "persistent-tmux/interactive-Claude-Code acceptance path"
)


def run_mistral_acceptance_probe(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Reject the retired acceptance route without inference, state or effect authority."""

    del args, kwargs
    raise RuntimeError(RETIRED_REASON)
