from __future__ import annotations

"""Mechanism differential: QCEP as the deepening policy behind U15 sufficiency gaps.

This is intentionally a synthetic falsifier, not a production adapter. It asks one narrow
question: after a compiled context is known to be insufficient, does query-conditioned
navigation close an explicit evidence requirement more often than static EAP traversal under
the SAME item budget, without regressing clean/unlabeled controls?

Evidence tags are explicit row metadata. They are never inferred from free text, and only
CURRENT/KNOWN rows may close a U15 gap. QCEP remains context-only and non-authoritative.
"""

import hashlib
import json
import math
import random
import statistics
import time
from typing import Any

from .query_conditioned_evidence_projection import QueryConditionedEvidenceProjector, QueryEvidenceSpec
from .unifieddb_emergent_preprocessor import EmergentAssemblyPreprocessor, PossibilitySpec
from research_entity.runtime.semantic_gap_controller_v15 import (
    EvidenceItem,
    EvidenceRequirement,
    SufficiencyGapControllerV15,
)

POISON = 120
CLEAN = 80
UNLABELED = 60
MAX_ITEMS = 4


def h(v: Any) -> str:
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def row(domain: str, key: str, value: Any, epistemic: str = "KNOWN", status: str = "CURRENT") -> dict[str, Any]:
    return {
        "domain": domain, "key": key, "value": value, "epistemic": epistemic,
        "status": status, "domain_epoch": 1,
        "semantic_hash": h([domain, key, value, epistemic, status]),
    }


class Ledger:
    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = list(rows)
        self.epoch = 1
        self.semantic_state_hash = h([(r["domain"], r["key"], r["semantic_hash"]) for r in rows])

    def materialized(self):
        return list(self._rows)


def explicit_tags(value: Any) -> frozenset[str]:
    if not isinstance(value, dict):
        return frozenset()
    out: list[str] = []
    for key in ("evidence_tags", "tags"):
        raw = value.get(key, ())
        if isinstance(raw, (list, tuple, set)):
            out.extend(str(x) for x in raw if str(x).strip())
    return frozenset(out)


def build_fixture():
    rows: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    total = POISON + CLEAN + UNLABELED
    for i in range(total):
        family = "poison" if i < POISON else ("clean" if i < POISON + CLEAN else "unlabeled")
        p = f"g{i:03d}"
        root = f"semantic:{p}_root"
        rows.append(row("semantic", f"{p}_root", {"text": "anchor", "evidence_tags": ["anchor"]}))
        prev = root
        chain: list[str] = []
        for hop in range(3):
            ref = f"semantic:{p}_rel{hop}"
            chain.append(ref)
            tags = ["target"] if hop == 2 else [f"bridge{hop}"]
            rows.append(row("semantic", f"{p}_rel{hop}", {"text": "neutral payload", "evidence_tags": tags}))
            weight = (0.72, 0.91, 0.89)[hop] if family == "poison" else (0.96, 0.93, 0.90)[hop]
            dep = {
                "source": prev, "target": ref, "strength": weight,
                "relation_type": "SUPPORTS",
            }
            # Poison case has evidence-bound relation metadata capable of discriminating the
            # useful route. Unlabeled control intentionally removes it; QCEP-0.2 must then
            # fall back to static weighting instead of treating missing labels as negative.
            if family != "unlabeled":
                dep["query_cue"] = "target evidence"
            rows.append(row("dependency", f"{p}_chain{hop}", dep))
            prev = ref

        hub = f"semantic:{p}_hub"
        rows.append(row("semantic", f"{p}_hub", {"text": "generic hub", "evidence_tags": ["background"]}))
        rows.append(row("dependency", f"{p}_hubedge", {
            "source": root, "target": hub,
            "strength": 0.99 if family == "poison" else 0.60,
            "relation_type": "RELATED", "query_cue": "generic association",
        }))
        for j in range(10):
            d = f"semantic:{p}_d{j:02d}"
            rows.append(row("semantic", f"{p}_d{j:02d}", {"text": "generic distractor", "evidence_tags": ["background"]}))
            rows.append(row("dependency", f"{p}_hd{j:02d}", {
                "source": hub, "target": d, "strength": 0.98,
                "relation_type": "RELATED", "query_cue": "generic association",
            }))

        conflict = f"semantic:{p}_conflict"
        launder = f"semantic:{p}_launder"
        rows.append(row("semantic", f"{p}_conflict", {"text": "uncertain", "evidence_tags": ["target"]}, "CONFLICT"))
        rows.append(row("semantic", f"{p}_launder", {"text": "must not close gap", "evidence_tags": ["target"]}))
        rows.append(row("dependency", f"{p}_conflictedge", {
            "source": root, "target": conflict, "strength": 1.0,
            "relation_type": "SUPPORTS", "query_cue": "target evidence",
        }))
        rows.append(row("dependency", f"{p}_launderedge", {
            "source": conflict, "target": launder, "strength": 1.0,
            "relation_type": "SUPPORTS", "query_cue": "target evidence",
        }))
        cases.append({
            "id": p, "family": family, "root": root, "target": chain[-1],
            "launder": launder, "query": "need target evidence",
        })
    return rows, cases


def pct(xs: list[float], q: float) -> float:
    ys = sorted(xs)
    p = (len(ys) - 1) * q
    lo, hi = math.floor(p), math.ceil(p)
    return ys[lo] if lo == hi else ys[lo] * (hi - p) + ys[hi] * (p - lo)


def main():
    rows, cases = build_fixture()
    ledger = Ledger(rows)
    eap = EmergentAssemblyPreprocessor(ledger)
    qcep = QueryConditionedEvidenceProjector(ledger)
    row_by_ref = {f"{r['domain']}:{r['key']}": r for r in rows}

    def to_evidence(refs):
        out = []
        for ref in refs:
            r = row_by_ref.get(ref)
            if not r or r["domain"] == "dependency":
                continue
            out.append(EvidenceItem(
                ref=ref,
                tags=explicit_tags(r.get("value")),
                provenance_valid=(r["epistemic"] == "KNOWN" and r["status"] == "CURRENT"),
                status=r["status"],
            ))
        return out

    def eap_expand(query, gap_terms, selected, source_epoch, graph_epoch, budget):
        # Static-graph control: same seed/budget/depth, no lexical rescue. The purpose is to
        # isolate whether query-conditioned topology helps after U15 has already found a gap.
        seeds = tuple(selected)
        a = eap.compile_active_assembly(PossibilitySpec(
            assembly_id="u15-eap-" + h([query, gap_terms, selected])[:12],
            seed_refs=seeds,
            query_text="",
            max_items=max(1, budget + len(seeds)),
            max_hops=3,
            frontier_budget=256,
            min_edge_weight=0.0,
            basis_epoch=source_epoch,
            purpose="U15_STATIC_DEEPENING_CONTROL",
        ))
        refs = [x["ref"] for x in a["selected"] if x["ref"] not in set(selected)]
        return to_evidence(refs[:budget])

    def qcep_expand(query, gap_terms, selected, source_epoch, graph_epoch, budget):
        seeds = tuple(selected)
        conditioned = " ".join([query, *gap_terms])
        a = qcep.project(QueryEvidenceSpec(
            projection_id="u15-qcep-" + h([query, gap_terms, selected])[:12],
            query_text=conditioned,
            seed_refs=seeds,
            basis_epoch=source_epoch,
            max_items=max(1, budget + len(seeds)),
            max_hops=3,
            frontier_budget=256,
            min_edge_weight=0.0,
        ))
        refs = [x["ref"] for x in a["selected"] if x["ref"] not in set(selected)]
        return to_evidence(refs[:budget])

    methods = {
        "u15_plus_static_eap": SufficiencyGapControllerV15(expand=eap_expand, max_rounds=1, max_items=MAX_ITEMS),
        "u15_plus_qcep_0_2": SufficiencyGapControllerV15(expand=qcep_expand, max_rounds=1, max_items=MAX_ITEMS),
    }
    order = cases[:]
    random.Random(71).shuffle(order)
    results: dict[str, Any] = {}
    for name, ctl in methods.items():
        rows_out = []
        latency = []
        for c in order:
            initial = [EvidenceItem(c["root"], frozenset({"anchor"}))]
            t0 = time.perf_counter_ns()
            rec = ctl.assemble(
                query_id=name + ":" + c["id"], query_text=c["query"],
                source_epoch=1, graph_epoch=1,
                initial_items=initial,
                requirements=[EvidenceRequirement("target_requirement", required_tags=frozenset({"target"}))],
            )
            latency.append((time.perf_counter_ns() - t0) / 1000.0)
            rows_out.append({
                "family": c["family"],
                "final_sufficient": rec.final_sufficient,
                "target_present": c["target"] in rec.selected_refs,
                "launder_present": c["launder"] in rec.selected_refs,
                "deepening_rounds": rec.deepening_rounds,
            })
        fam = {}
        for family in ("poison", "clean", "unlabeled"):
            xs = [x for x in rows_out if x["family"] == family]
            fam[family] = {
                "final_sufficiency_rate": statistics.mean(float(x["final_sufficient"]) for x in xs),
                "target_present_rate": statistics.mean(float(x["target_present"]) for x in xs),
                "launder_rate": statistics.mean(float(x["launder_present"]) for x in xs),
            }
        results[name] = {
            "families": fam,
            "latency_us": {
                "p50": pct(latency, 0.50), "p95": pct(latency, 0.95),
                "p99": pct(latency, 0.99), "mean": statistics.mean(latency),
            },
        }

    base = results["u15_plus_static_eap"]
    cand = results["u15_plus_qcep_0_2"]
    gate = {
        "poison_sufficiency_delta": cand["families"]["poison"]["final_sufficiency_rate"] - base["families"]["poison"]["final_sufficiency_rate"],
        "clean_sufficiency_delta": cand["families"]["clean"]["final_sufficiency_rate"] - base["families"]["clean"]["final_sufficiency_rate"],
        "unlabeled_sufficiency_delta": cand["families"]["unlabeled"]["final_sufficiency_rate"] - base["families"]["unlabeled"]["final_sufficiency_rate"],
        "qcep_launder_rate": max(cand["families"][f]["launder_rate"] for f in ("poison", "clean", "unlabeled")),
    }
    gate["promote_for_real_corpus_falsifier"] = (
        gate["poison_sufficiency_delta"] > 0.0
        and gate["clean_sufficiency_delta"] >= 0.0
        and gate["unlabeled_sufficiency_delta"] >= 0.0
        and gate["qcep_launder_rate"] == 0.0
    )
    print(json.dumps({
        "schema_version": "1.0",
        "benchmark": "QCEP_U15_EXPLICIT_EVIDENCE_GAP_CLOSURE",
        "evidence_class": "SYNTHETIC_EXECUTED_MECHANISM_DIFFERENTIAL",
        "dataset": {"cases": len(cases), "poison": POISON, "clean": CLEAN, "unlabeled": UNLABELED, "max_items": MAX_ITEMS},
        "methods": results,
        "candidate_vs_static": gate,
        "scope_guard": "Measures explicit tagged evidence-gap closure after U15 declares context insufficient. Not universal database superiority and not downstream model answer quality.",
        "limitations": [
            "Synthetic model-authored topology deliberately stresses hub drift.",
            "Evidence tags are explicit fixture metadata; real Clay tag coverage may be sparser.",
            "Graph epoch is fixed in this harness; production integration needs verified source+graph generation binding.",
            "QCEP is tested as an injected deepening mechanism only; it must never bypass U15 sufficiency stop.",
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
