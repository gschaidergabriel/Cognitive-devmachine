from __future__ import annotations

"""V1.1 falsifier for the real-claims topology benchmark.

V1 local pre-execution exposed a scoring defect: a lexical seed received its own topic/domain
"neighbor" reinforcement. That is not topology evidence; it only preserves seed bias. V1.1
keeps every other V1 semantic, query, timing and fairness rule unchanged but forbids self-seed
topology reinforcement in BOTH the indexed-SQL and compiled-map routes.

This wrapper deliberately reuses V1 so the delta is lesionable and auditable.
"""

import io
import json
import sys
from pathlib import Path

from . import benchmark_real_claim_topology_preprocessor_v1 as base


def topology_scores_compiled(query, lexical, rows_by_id, topology):
    topics_by_claim, domains_by_claim, claims_by_topic, claims_by_domain = topology
    seeds = base.ranked(lexical, 2)
    candidates = set(lexical)
    for seed in seeds:
        for topic in topics_by_claim.get(seed, ()):
            candidates.update(claims_by_topic.get(topic, ()))
        for domain in domains_by_claim.get(seed, ()):
            candidates.update(claims_by_domain.get(domain, ()))
    statuses = base.query_statuses(query)
    scores = {cid: lexical.get(cid, 0.0) for cid in candidates}
    for cid in candidates:
        for seed in seeds:
            if cid == seed:
                continue
            if topics_by_claim.get(cid, frozenset()) & topics_by_claim.get(seed, frozenset()):
                scores[cid] += 4.0
            if domains_by_claim.get(cid, frozenset()) & domains_by_claim.get(seed, frozenset()):
                scores[cid] += 0.75
        if statuses and str(rows_by_id[cid].get("current_status", "")).upper() in statuses:
            scores[cid] += 3.0
    return scores


def topology_scores_sqlite_matched(con, query, lexical, rows_by_id):
    seeds = base.ranked(lexical, 2)
    candidates = set(lexical) | base.sql_topology_candidates(con, seeds)
    statuses = base.query_statuses(query)
    scores = {cid: lexical.get(cid, 0.0) for cid in candidates}
    for cid in candidates:
        for seed in seeds:
            if cid == seed:
                continue
            if base.sql_shared_count(con, cid, seed, "claim_topic", "topic"):
                scores[cid] += 4.0
            if base.sql_shared_count(con, cid, seed, "claim_domain", "domain"):
                scores[cid] += 0.75
        if statuses and str(rows_by_id[cid].get("current_status", "")).upper() in statuses:
            scores[cid] += 3.0
    return scores


def requested_output_path() -> Path | None:
    try:
        i = sys.argv.index("--output")
    except ValueError:
        return None
    if i + 1 >= len(sys.argv):
        return None
    return Path(sys.argv[i + 1])


def main() -> None:
    base.topology_scores_compiled = topology_scores_compiled
    base.topology_scores_sqlite_matched = topology_scores_sqlite_matched
    previous = sys.stdout
    capture = io.StringIO()
    sys.stdout = capture
    try:
        base.main()
    finally:
        sys.stdout = previous
    result = json.loads(capture.getvalue())
    result["schema_version"] = "1.1"
    result["benchmark"] = "REAL_CLAY_CLAIM_TOPOLOGY_PREPROCESSOR_V1_1"
    result["iteration_delta"] = {
        "from": "V1",
        "falsifier": "Self-seed topic/domain reinforcement can preserve lexical seed bias without adding neighborhood evidence.",
        "change": "A topology score is added only when cid != seed; applied identically to SQLite matched joins and compiled maps.",
        "epistemic_effect": "No new truth source. This changes rank only and keeps the matched-semantics equivalence obligation.",
    }
    path = requested_output_path()
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
