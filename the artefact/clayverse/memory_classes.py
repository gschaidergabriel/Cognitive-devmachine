from __future__ import annotations

EVIDENCE_KINDS = frozenset({
    "fact", "decision", "task", "commitment", "preference", "open", "open_question",
})
CONTROL_KINDS = frozenset({"source_archive", "compression_receipt", "compression_clearance"})
METHOD_CANDIDATE_KINDS = frozenset({"framework_candidate", "heuristic_candidate"})
METHOD_SERVABLE_KINDS = frozenset({"framework", "heuristic", "failure_pattern", "counterexample"})
METHOD_KINDS = METHOD_CANDIDATE_KINDS | METHOD_SERVABLE_KINDS | frozenset({"method_receipt"})

METHOD_STATUSES = frozenset({"CANDIDATE", "PROMOTED", "DEMOTED", "RETIRED"})


def is_evidence_kind(kind: str) -> bool:
    return str(kind) in EVIDENCE_KINDS


def is_method_kind(kind: str) -> bool:
    return str(kind) in METHOD_KINDS
