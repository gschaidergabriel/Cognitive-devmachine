import importlib.util
import pathlib
import random
import time

HERE = pathlib.Path(__file__).resolve().parent
REF = HERE.parent / "implementation" / "scf_reference.py"
spec = importlib.util.spec_from_file_location("scf_reference", REF)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

VALID = [
    m.Transition("boot", m.dvec(SELF_ROOT_ID=1), frozenset({"SELF_ROOT_ID"}), "BOOT_ROOT"),
    m.Transition("auth", m.dvec(DIRECT_INTENT_AUTH=1), frozenset({"DIRECT_INTENT_AUTH"}), "TOKEN_AUTHENTICATOR"),
    m.Transition("effect_gate", m.dvec(EFFECT_AUTH=1), frozenset({"EFFECT_AUTH"}), "EFFECT_GATE"),
    m.Transition("verify", m.dvec(VERIFIED_OUTCOME_EVIDENCE=1), frozenset({"VERIFIED_OUTCOME_EVIDENCE"}), "EXTERNAL_VERIFIER"),
    m.Transition("research", m.dvec(RESEARCH_EVIDENCE=1), frozenset({"RESEARCH_EVIDENCE"}), "EXTERNAL_VERIFIER"),
    m.Transition("accept", m.dvec(RESEARCH_ACCEPTANCE_AUTH=1), frozenset({"RESEARCH_ACCEPTANCE_AUTH"}), "RESEARCH_ENTITY"),
    m.Transition("credit", m.dvec(CAUSAL_CREDIT=1), frozenset({"CAUSAL_CREDIT"}), "CAUSAL_CREDIT_GATE"),
    m.Transition("op_state", m.dvec(), repo_surface="OPERATIONAL_STATE"),
    m.Transition("telemetry", m.dvec(), repo_surface="OPERATIONAL_TELEMETRY"),
    m.Transition("proposal", m.dvec(), repo_surface="SELF_OBSERVATION_PROPOSAL"),
    m.Transition("ordinary", m.dvec()),
]
BUGS = {
    "IDENTITY_MINT": m.Transition("peer_to_self", m.dvec(SELF_ROOT_ID=1)),
    "AUTHORITY_MINT": m.Transition("salience_to_auth", m.dvec(EFFECT_AUTH=1)),
    "EVIDENCE_MINT": m.Transition("telemetry_to_research", m.dvec(RESEARCH_EVIDENCE=1)),
    "ACCEPTANCE_MINT": m.Transition("proposal_to_acceptance", m.dvec(RESEARCH_ACCEPTANCE_AUTH=1)),
    "CAUSAL_CREDIT_MINT": m.Transition("completion_to_credit", m.dvec(CAUSAL_CREDIT=1)),
    "STALE_EPOCH": m.Transition("stale_to_current", m.dvec(), epoch_out=2),
    "DIRECT_REPO_RECEIPT_WRITE": m.Transition("write_acceptance", m.dvec(), repo_surface="RESEARCH_OR_ACCEPTANCE_RECEIPT"),
}

def make_trace(rng, bug=None):
    trace = [rng.choice(VALID) for _ in range(rng.randint(4, 10))]
    if bug:
        trace.insert(rng.randrange(len(trace) + 1), BUGS[bug])
    return trace

def main():
    for bug, transition in BUGS.items():
        trace = [VALID[-1], transition, VALID[-1]]
        assert m.detect_surface_plus_scf(trace), bug

    rng = random.Random(101)
    n = 50000
    clean_fp = 0
    missed = 0
    t0 = time.perf_counter_ns()
    for i in range(n):
        if i % 2:
            trace = make_trace(rng)
            clean_fp += int(m.detect_surface_plus_scf(trace))
        else:
            bug = rng.choice(tuple(BUGS))
            trace = make_trace(rng, bug)
            missed += int(not m.detect_surface_plus_scf(trace))
    elapsed_ms = (time.perf_counter_ns() - t0) / 1e6
    assert clean_fp == 0, clean_fp
    assert missed == 0, missed
    print({"tests": "PASS", "n": n, "clean_fp": clean_fp, "missed": missed, "elapsed_ms": elapsed_ms})

if __name__ == "__main__":
    main()
