from research_entity.harness.reference.possibility_preprocessor import (
    PossibilityPreprocessor,
    PossibilityQuery,
    StalePossibilityEpoch,
)


def fixture():
    cases = [
        ("archive project evidence safely", ["cap:write_repo","res:github","constraint:provenance","rule:archive"], "aff:archive_repo"),
        ("run ubuntu benchmark without gpu", ["cap:ubuntu_exec","res:hostinger","constraint:no_gpu","rule:cpu_bench"], "aff:cpu_benchmark"),
        ("find contradictory research before promotion", ["cap:search_evidence","constraint:counterevidence","rule:adjudicate"], "aff:counterevidence_scan"),
        ("prepare context for model without granting authority", ["cap:assemble_context","constraint:no_authority","rule:context_only"], "aff:context_capsule"),
        ("reuse recent graph neighborhood after one source changes", ["cap:materialize_view","constraint:targeted_invalidation","rule:incremental_refresh"], "aff:incremental_view"),
        ("choose executable tool that satisfies permission and freshness", ["cap:tool_select","constraint:permission","constraint:freshness","rule:route_proof"], "aff:authorized_route"),
        ("recover a committed effect after crash", ["cap:effect_ledger","constraint:recovery","rule:reentry_verify"], "aff:recover_effect"),
        ("answer from current state while surfacing conflict", ["cap:query_state","constraint:conflict_visible","rule:answer_capsule"], "aff:conflict_aware_answer"),
        ("discover new viable action from two separate capabilities", ["cap:compose","cap:capability_view","rule:affordance_join"], "aff:composed_action"),
        ("avoid stale graph mutation", ["cap:epoch_check","constraint:graph_fresh","rule:truth_gate"], "aff:safe_mutation"),
    ]
    text = {
        "cap:write_repo":"commit write repository git evidence","res:github":"github repository durable storage","constraint:provenance":"preserve provenance evidence lineage","rule:archive":"archive evidence with immutable receipt",
        "cap:ubuntu_exec":"execute commands on ubuntu linux host","res:hostinger":"hostinger ubuntu cpu runner","constraint:no_gpu":"gpu absent cpu only execution","rule:cpu_bench":"benchmark via cpu runtime",
        "cap:search_evidence":"search research evidence findings","constraint:counterevidence":"retain contradiction counterhypothesis negative evidence","rule:adjudicate":"compare supporting and contradicting evidence before promotion",
        "cap:assemble_context":"assemble compact model context","constraint:no_authority":"context confers no execution authority","rule:context_only":"projection is context only",
        "cap:materialize_view":"materialize cognitive neighborhood view","constraint:targeted_invalidation":"invalidate only dependency affected contexts after source changes","rule:incremental_refresh":"refresh changed neighborhood incrementally",
        "cap:tool_select":"select available tool capability","constraint:permission":"tool permission must permit effect","constraint:freshness":"capability observation must be fresh","rule:route_proof":"prove route constraints and authority",
        "cap:effect_ledger":"record effect intent commit outcome","constraint:recovery":"recover after process crash","rule:reentry_verify":"verify committed effect before reentry",
        "cap:query_state":"query current semantic state","constraint:conflict_visible":"contradictions remain visible","rule:answer_capsule":"assemble answer capsule with conflicts",
        "cap:compose":"compose capabilities into candidate possibility","cap:capability_view":"project current capabilities","rule:affordance_join":"join compatible capabilities under constraints",
        "cap:epoch_check":"check graph and source epochs","constraint:graph_fresh":"graph epoch must match source epoch","rule:truth_gate":"block mutation when stale",
    }
    nodes = [{"id": k, "text": v, "epistemic": "KNOWN", "lineage_root": k} for k, v in text.items()]
    nodes += [{"id": f"doc:{i}", "text": f"generic database record storage transaction index user project state note {i}", "epistemic": "KNOWN", "lineage_root": f"doc:{i}"} for i in range(400)]
    edges, affordances = [], []
    for _, requirements, candidate_id in cases:
        nodes.append({"id": candidate_id, "text": candidate_id.replace("_", " "), "epistemic": "KNOWN", "lineage_root": candidate_id})
        affordances.append({"id": candidate_id, "requirements": requirements})
        for requirement in requirements:
            edges.append({"source": candidate_id, "target": requirement, "weight": 1.0, "relation_type": "requires", "proof_eligible": True})
    return cases, nodes, edges, affordances


def test_possibility_preprocessor_beats_flat_retrieval_on_fixture():
    cases, nodes, edges, affordances = fixture()
    pp = PossibilityPreprocessor(source_epoch=9, graph_epoch=9, nodes=nodes, edges=edges, affordances=affordances)
    base_recall, base_top1, pre_recall, pre_top1 = [], [], [], []
    for i, (query, requirements, candidate_id) in enumerate(cases):
        baseline = pp.lexical_baseline(query, 12)
        base_recall.append(len(set(requirements) & set(baseline)) / len(requirements))
        base_top1.append(bool(baseline and baseline[0] == candidate_id))
        receipt = pp.compile(PossibilityQuery(f"q{i}", query, 9, 9, max_candidates=12))
        visible = set(receipt["seed_refs"])
        for candidate in receipt["candidates"][:5]:
            visible.update(candidate["proof_refs"])
        pre_recall.append(len(set(requirements) & visible) / len(requirements))
        pre_top1.append(receipt["selected_ref"] == candidate_id)
    assert sum(pre_recall) / len(pre_recall) == 1.0
    assert sum(pre_top1) / len(pre_top1) == 1.0
    assert sum(pre_recall) > sum(base_recall)
    assert sum(pre_top1) > sum(base_top1)


def test_fail_closed_abstention_conflict_stale_and_shared_ancestry():
    cases, nodes, edges, affordances = fixture()
    pp = PossibilityPreprocessor(source_epoch=9, graph_epoch=9, nodes=nodes, edges=edges, affordances=affordances)
    assert pp.compile(PossibilityQuery("none", "zzzxxyy impossible ungrounded", 9, 9))["abstain"]
    try:
        pp.compile(PossibilityQuery("stale", "archive", 8, 9))
        assert False, "stale epoch accepted"
    except StalePossibilityEpoch:
        pass

    conflict_pp = PossibilityPreprocessor(
        source_epoch=1,
        graph_epoch=1,
        nodes=[
            {"id":"cap:x","text":"execute x","epistemic":"CONFLICT","lineage_root":"L1"},
            {"id":"rule:x","text":"do x","epistemic":"KNOWN","lineage_root":"L2"},
        ],
        edges=[],
        affordances=[{"id":"aff:x","requirements":["cap:x","rule:x"]}],
    )
    conflict = conflict_pp.compile(PossibilityQuery("conf", "execute do x", 1, 1))
    assert conflict["abstain"]
    assert conflict["candidates"][0]["conflict_refs"] == ("cap:x",)

    lineage_pp = PossibilityPreprocessor(
        source_epoch=1,
        graph_epoch=1,
        nodes=[
            {"id":"cap:a","text":"alpha run","epistemic":"KNOWN","lineage_root":"same"},
            {"id":"rule:a","text":"alpha route","epistemic":"KNOWN","lineage_root":"same"},
        ],
        edges=[],
        affordances=[{"id":"aff:a","requirements":["cap:a","rule:a"]}],
    )
    lineage = lineage_pp.compile(PossibilityQuery("lin", "alpha run route", 1, 1, min_independent_support=2))
    assert lineage["abstain"]
    assert len(lineage["candidates"][0]["independent_lineages"]) == 1


def test_untrusted_high_weight_edges_can_activate_but_cannot_mint_proof():
    cases, nodes, edges, affordances = fixture()
    query, correct_requirements, correct_candidate = cases[0]
    wrong_candidate = "aff:cpu_benchmark"
    wrong_requirements = next(a["requirements"] for a in affordances if a["id"] == wrong_candidate)
    for requirement in wrong_requirements:
        edges.append({
            "source": correct_requirements[0],
            "target": requirement,
            "weight": 5.0,
            "relation_type": "requires",
            "proof_eligible": False,
        })
    pp = PossibilityPreprocessor(source_epoch=9, graph_epoch=9, nodes=nodes, edges=edges, affordances=affordances)
    receipt = pp.compile(PossibilityQuery("adversarial-edge", query, 9, 9))
    assert receipt["selected_ref"] == correct_candidate
    wrong = next(c for c in receipt["candidates"] if c["candidate_id"] == wrong_candidate)
    assert wrong["completeness"] < 1.0
