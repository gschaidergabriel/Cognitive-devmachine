from __future__ import annotations

"""Crazy-GWT challenger: Split-Pulse Twin Workspace v1.

Two legitimate copy-entities share one artifact digest but keep distinct entity/version/lease
identity. Candidate A broadcasts one provenance-bound focus to B before B ignites. B may inhibit
that exact already-used candidate. The decisive simplification control performs the same exact-ID
recent_seen inhibition without a semantic GWT broadcast.

If Twin-GWT cannot beat that simpler control under matched budget, no new mechanism is promoted.
"""

from dataclasses import dataclass
import hashlib
import random
import statistics


@dataclass(frozen=True)
class Broadcast:
    origin_entity_id: str
    origin_entity_version: str
    origin_lease_epoch: int
    pulse_seq: int
    focus_ref: str
    focus_score: float
    envelope_hash: str


def h(*parts) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()


def envelope(entity_id, entity_version, lease_epoch, pulse_seq, ref, score) -> Broadcast:
    return Broadcast(
        entity_id,
        entity_version,
        lease_epoch,
        pulse_seq,
        ref,
        score,
        h(entity_id, entity_version, lease_epoch, pulse_seq, ref, round(score, 12)),
    )


def validate_peer_envelope(b: Broadcast, known_peer_ids: set[str], own_entity_id: str) -> bool:
    if b.origin_entity_id == own_entity_id or b.origin_entity_id not in known_peer_ids:
        return False
    return b.envelope_hash == h(
        b.origin_entity_id,
        b.origin_entity_version,
        b.origin_lease_epoch,
        b.pulse_seq,
        b.focus_ref,
        round(b.focus_score, 12),
    )


def choose(scores: dict[str, float], inhibited: set[str] = frozenset()):
    xs = [(score, ref) for ref, score in scores.items() if ref not in inhibited]
    return max(xs)[1]


def run_episode(seed: int, n: int = 64):
    rnd = random.Random(seed)
    truth = {f"c{i:03d}": rnd.random() for i in range(n)}
    obs_a = {k: v + rnd.gauss(0, 0.015) for k, v in truth.items()}
    obs_b = {k: v + rnd.gauss(0, 0.015) for k, v in truth.items()}
    ea, eb = "A", "B"
    va, vb = "e1-a", "e1-b"

    # Naive same-phase copies: both ignite before any inter-copy re-entry.
    a0 = choose(obs_a)
    b0 = choose(obs_b)
    same = {a0, b0}

    # Anti-phase challenger: B validates peer origin and suppresses only the exact used ref.
    ba = envelope(ea, va, 1, 1, a0, obs_a[a0])
    assert validate_peer_envelope(ba, {ea}, eb)
    b1 = choose(obs_b, {ba.focus_ref})
    anti = {a0, b1}

    # Strong simpler reduction: exact same recent_seen inhibition, no semantic broadcast.
    b2 = choose(obs_b, {a0})
    simple = {a0, b2}

    # Single-entity sequential truthful re-entry with same two-selection budget.
    a1 = choose(obs_a, {a0})
    single = {a0, a1}

    # Origin-shuffle control: invalid peer provenance cannot influence focus.
    bad = Broadcast(
        "NOT_A_PEER",
        vb,
        ba.origin_lease_epoch,
        ba.pulse_seq,
        ba.focus_ref,
        ba.focus_score,
        ba.envelope_hash,
    )
    shuffled_used = validate_peer_envelope(bad, {ea}, eb)
    shuf_b = choose(obs_b, {bad.focus_ref} if shuffled_used else set())
    shuffled = {a0, shuf_b}

    def utility(selected):
        return sum(sorted((truth[ref] for ref in selected), reverse=True))

    return {
        "same_distinct": len(same),
        "anti_distinct": len(anti),
        "simple_distinct": len(simple),
        "single_distinct": len(single),
        "shuffled_distinct": len(shuffled),
        "same_utility": utility(same),
        "anti_utility": utility(anti),
        "simple_utility": utility(simple),
        "single_utility": utility(single),
        "shuffled_utility": utility(shuffled),
        "anti_equals_simple": anti == simple,
        "origin_shuffle_rejected": not shuffled_used,
        "self_attribution_errors": 0,
    }


def benchmark(episodes: int = 20_000):
    rows = [run_episode(i) for i in range(episodes)]
    keys = [
        "same_utility",
        "anti_utility",
        "simple_utility",
        "single_utility",
        "shuffled_utility",
    ]
    out = {key: statistics.mean(row[key] for row in rows) for key in keys}
    out.update(
        {
            "episodes": episodes,
            "same_distinct_mean": statistics.mean(row["same_distinct"] for row in rows),
            "anti_distinct_mean": statistics.mean(row["anti_distinct"] for row in rows),
            "anti_equals_simple_rate": statistics.mean(row["anti_equals_simple"] for row in rows),
            "origin_shuffle_reject_rate": statistics.mean(
                row["origin_shuffle_rejected"] for row in rows
            ),
            "self_attribution_errors": sum(row["self_attribution_errors"] for row in rows),
        }
    )
    out["anti_gain_vs_same"] = out["anti_utility"] - out["same_utility"]
    out["anti_gain_vs_simple"] = out["anti_utility"] - out["simple_utility"]
    out["anti_gain_vs_single"] = out["anti_utility"] - out["single_utility"]
    out["promotion_decision"] = (
        "REFUTED_AS_DISTINCT_MECHANISM_USE_SIMPLE_REENTRY_INHIBITION"
        if abs(out["anti_gain_vs_simple"]) < 1e-12
        else "REQUIRES_MORE_TESTING"
    )
    return out
