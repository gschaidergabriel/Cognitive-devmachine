from __future__ import annotations

from lineage_anchor import LineageAnchor, LineageAssessment, assess_stream_against_anchor


def restore_exact_from_anchor(machine, stream: list[dict], anchor: LineageAnchor) -> LineageAssessment:
    """Fail closed on lineage admission before mutating UCM2 materialization.

    The caller is responsible for supplying an authenticated anchor from outside
    the candidate stream. Internal event integrity is checked by the exact UCM2
    verifier, then exact-head lineage is admitted, and only then is restore allowed.
    """
    assessment = assess_stream_against_anchor(
        stream,
        anchor,
        verifier=machine.verify_event_stream,
        mode="RECOVER_EXACT",
    )
    restored_hash = machine.restore_from_event_stream(stream)
    if restored_hash != assessment.terminal_hash:
        raise RuntimeError("LINEAGE_RESTORE_HASH_DRIFT")
    return assessment
