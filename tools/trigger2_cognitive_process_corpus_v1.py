#!/usr/bin/env python3
"""Generate owner-aligned Trigger-2 cognitive-process training candidates.

SOURCE/METHOD ONLY. The generated rows are candidate training data, not canonical
facts, accepted dataset tokens, runtime evidence, J-Space causal evidence, or
training credit. All family siblings stay in one preregistered split.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
ANCESTRY = "trigger2-20260825-owner-variable-grid-cognitive-process-seed-v1"
SPLIT_UNIT = "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY"

# Each family supplies four complementary examples so the corpus does not learn a
# trivial always-reject policy: protocol-correct, adversarial hard-negative,
# epistemic UNKNOWN, and counterfactual boundary reasoning.
FAMILIES = [
    {
        "id":"TASK_ADMISSION_CAUSAL_ID","process":"ZECP01","split":"TRAIN",
        "protocol_q":"A task is received twice through two transport admissions but both observations refer to the same replay-stable real-world event. How should identity be represented before cognition?",
        "protocol_a":"Keep one replay-stable causal_event_id for the event and distinct admission_id values for the concrete admissions. Bind provenance and generation before cognitive work starts; a new transport admission does not create a new real-world event.",
        "bad_q":"A retry arrives with a new admission_id, so a module claims it must be a new causal event and counts it as independent evidence. Accept or reject?",
        "bad_a":"Reject. Admission identity and causal-event identity are different axes. A new admission can observe the same causal event and cannot mint independent evidence by transport replay.",
        "unknown_q":"The transport record exists, but the source cannot establish whether it is a retry of event E or a distinct event. What fact should the grid assume?",
        "unknown_a":"Assume neither. Preserve causal identity as UNKNOWN/ambiguous and request a discriminator; do not merge or split events by convenience.",
        "cf_q":"What additional evidence would justify assigning a new causal_event_id to the second admission?",
        "cf_a":"Evidence that the second admission corresponds to a distinct real-world occurrence under the event-identity rule, not merely a different transport/session/request identifier."
    },
    {
        "id":"DB_VS_SIMULATION_BOUNDARY","process":"ZECP02/ZECP03","split":"TRAIN",
        "protocol_q":"A project epoch, exact digest, durable goal, and current interpretation of an ambiguous task are all needed by the grid. Which belong in durable storage versus cognitive simulation?",
        "protocol_a":"Store the exact epoch, digest, and durable goal in the database with provenance. Simulate the task interpretation as a candidate working state. Rule: simulate cognition; store durable exact data.",
        "bad_q":"A module repeatedly reconstructs the current canonical epoch from conversation context instead of reading the database because its guess is usually right. Accept or reject?",
        "bad_a":"Reject. Exact durable epochs belong in deterministic storage. Inference must not substitute for an available canonical exact value.",
        "unknown_q":"A required DB_STATE_REF is unreadable and no equivalent exact source is available. Should the model reconstruct the missing value from surrounding text?",
        "unknown_a":"No. The missing durable value remains UNKNOWN. The model may propose a recovery method but must not fabricate the state.",
        "cf_q":"When may a previously simulated working-state item become durable state?",
        "cf_a":"Only through the deterministic database admission/update path with the required provenance, epoch/digest, and authority checks; model confidence alone is insufficient."
    },
    {
        "id":"WORKING_STATE_FACT_FENCE","process":"ZECP03","split":"TRAIN",
        "protocol_q":"The grid reconstructs a likely current working state from admitted task context and DB evidence. How should that reconstruction be typed?",
        "protocol_a":"As a working_state_candidate with explicit missing-state questions and epistemic tags. It is cognition, not canonical truth.",
        "bad_q":"Three modules independently reconstruct the same missing detail, so the workspace writes it back as a fact without new evidence. Accept or reject?",
        "bad_a":"Reject. Agreement among generated candidates does not cross the fact boundary. Canonical state requires deterministic admission supported by evidence.",
        "unknown_q":"The DB evidence supports two incompatible current-state reconstructions equally well. What should the working state contain?",
        "unknown_a":"Preserve both live alternatives with uncertainty and a discriminator. Do not select one merely to simplify downstream planning.",
        "cf_q":"What would permit one reconstructed alternative to be treated as established state?",
        "cf_a":"New evidence or a deterministic state record that discriminates the alternatives and is admitted at the required authority level."
    },
    {
        "id":"ATTENTION_WITHOUT_ERASURE","process":"ZECP04","split":"TRAIN",
        "protocol_q":"The grid has more evidence and hypotheses than fit in the current attention budget. What should relevance selection output?",
        "protocol_a":"A bounded attention_slice plus deferred_refs and an explicit uncertainty_set. Deprioritized unresolved alternatives are deferred, not declared false.",
        "bad_q":"A low-salience counterhypothesis is dropped from the attention window and a module marks it disproven. Accept or reject?",
        "bad_a":"Reject. Attention exclusion is a resource decision, not negative evidence. Preserve a reference and uncertainty state unless evidence actually falsifies it.",
        "unknown_q":"The relevance model cannot determine whether a low-frequency observation is important. What should happen?",
        "unknown_a":"Keep its relevance UNKNOWN or defer it with a retrievable reference and trigger conditions; do not silently discard it as irrelevant fact.",
        "cf_q":"When can a deferred alternative be removed rather than merely left out of the current attention slice?",
        "cf_a":"When an evidence-bearing falsifier, expiry rule, or explicit deterministic retention policy justifies removal, not because the attention budget is tight."
    },
    {
        "id":"PLANNING_REPLANNING_PRECONDITIONS","process":"ZECP06","split":"TRAIN",
        "protocol_q":"A goal has three dependent steps and one uncertain prerequisite. What should the planning process produce?",
        "protocol_a":"A work_graph_candidate with dependency-bound work units, explicit preconditions, completion tests, and a replan condition for the uncertain prerequisite.",
        "bad_q":"A plan step fails, but the module repeats it unchanged because it was in the original plan. Accept or reject?",
        "bad_a":"Reject. A failed precondition or falsified assumption triggers bounded replanning; plan identity is not authority.",
        "unknown_q":"The effect of step B on a required resource is not known. May the planner schedule irreversible step C as if the resource will remain available?",
        "unknown_a":"No. Preserve the dependency as UNKNOWN and gate C on evidence or a safe discriminator. Do not convert planning convenience into a fact.",
        "cf_q":"What evidence permits step C to become ready?",
        "cf_a":"A verified result or admitted state update satisfying C's declared preconditions under the current generation, not a prediction that B probably succeeded."
    },
    {
        "id":"HYPERPOSITION_EVIDENCE_COLLAPSE","process":"ZECP07","split":"TRAIN",
        "protocol_q":"Two mechanisms explain the same observations and no current test distinguishes them. How should the cognitive state represent them?",
        "protocol_a":"Maintain both alternatives in semantic Hyperposition with evidence, counterevidence, compatibility/exclusion structure, uncertainty, and candidate discriminators.",
        "bad_q":"Twelve of sixteen modules vote for hypothesis H1, with no new evidence. The coordinator wants to collapse H2. Accept or reject?",
        "bad_a":"Reject. Majority, recurrence, elegance, or confidence cannot mint truth. Collapse only when evidence discriminates the alternatives.",
        "unknown_q":"A discriminator was attempted but its result is itself ambiguous. Does the branch resolve?",
        "unknown_a":"No. Preserve the branch as unresolved and record the ambiguous result as evidence with UNKNOWN implication.",
        "cf_q":"What is sufficient to collapse the Hyperposition to H1?",
        "cf_a":"A preregistered or otherwise valid evidence-bearing discriminator whose admitted result supports H1 and rules out the live alternatives at the declared acceptance scope."
    },
    {
        "id":"VARIABLE_N_PROCESS_IDENTITY","process":"ZECP11","split":"TRAIN",
        "protocol_q":"The same planning process runs today on N=4 modules and tomorrow on N=20. What defines process identity?",
        "protocol_a":"The semantic process_id, typed inputs/outputs, and completion contract define the process. N and physical executor IDs are runtime parameters and must not redefine cognitive semantics.",
        "bad_q":"A worker says PLANNING_DECOMPOSITION_REPLANNING at N=10 and N=20 are different cognitive functions because different module counts participated. Accept or reject?",
        "bad_a":"Reject. Grid size is a runtime parameter. Different N may change performance or scheduling, not the semantic identity of the cognitive process.",
        "unknown_q":"N=20 is requested but only 13 healthy executors are available. Does the system know that the process will fail?",
        "unknown_a":"Not from N mismatch alone. Record requested_N=20 and observed_available_N=13, route under policy, and leave success UNKNOWN until the completion contract is evaluated.",
        "cf_q":"What observation would show that a process implementation wrongly depends on fixed N?",
        "cf_a":"If changing only N or physical executor identity changes the process_id, required semantics, or truth/effect authority rather than merely routing/performance."
    },
    {
        "id":"GRID_EXECUTOR_LEASE_STALENESS","process":"ZECP11","split":"TRAIN",
        "protocol_q":"A cognitive work packet is routed to an interchangeable executor. What must bind the execution?",
        "protocol_a":"A current GRID_EXECUTOR_BINDING with grid instance, requested/available N, executor_id, lease_id, process_id, runtime identity, and bounded timing. Stale or mismatched leases fail closed.",
        "bad_q":"An executor finished useful work after its lease expired and submits it as if still current. Should the result be admitted automatically?",
        "bad_a":"No. Preserve the result as a candidate/late observation but reject automatic current-state admission until generation/lease/work identity is reconciled.",
        "unknown_q":"The result payload is present but the lease record cannot be resolved. What execution authority should be inferred?",
        "unknown_a":"None. Lease validity is UNKNOWN, so authority-dependent admission fails closed while the payload may be retained as non-authoritative evidence candidate.",
        "cf_q":"What allows the late result to re-enter cognition safely?",
        "cf_a":"A deterministic reconciliation that binds it to the correct causal event/work identity and current state or explicitly rebases it without pretending the expired lease was valid."
    },
    {
        "id":"COMPRESSION_LOSS_MANIFEST","process":"ZECP12","split":"TRAIN",
        "protocol_q":"Workspace state must be compressed before transfer to another module. What must accompany the compressed packet?",
        "protocol_a":"A loss_manifest plus provenance/causal bindings and reentry_binding. Compression may reduce representation but must expose material loss rather than silently rewriting state.",
        "bad_q":"A compressor removes a dissenting hypothesis to fit the budget, then labels the compressed summary lossless because the majority view remained. Accept or reject?",
        "bad_a":"Reject. Dropping an unresolved alternative is material loss and must be declared. Majority does not make the discarded branch false.",
        "unknown_q":"The compressor cannot determine whether an omitted detail will matter downstream. How should loss be represented?",
        "unknown_a":"Mark the loss/impact UNKNOWN and retain a retrievable source reference. Do not claim semantic equivalence without evidence.",
        "cf_q":"When may a transfer be labeled lossless for the declared task?",
        "cf_a":"When deterministic checks or bounded evaluation establish preservation of all task-relevant fields/relations under the declared scope; not merely because outputs look similar once."
    },
    {
        "id":"CLAUDE_HANDOFF_INTERFACE_BOUNDARY","process":"ZECP13","split":"TRAIN",
        "protocol_q":"The grid prepares a compact state handoff to Claude Code. What interface claims are allowed?",
        "protocol_a":"Bind the handoff to the actually observed interface class such as TEXT, STRUCTURED_TEXT, TOOL_PROTOCOL, or exposed session state. Do not claim hidden activation access unless it is directly exposed and observed.",
        "bad_q":"Claude Code produced a coherent continuation after receiving structured text, so a module labels the bridge 'activation-level Global J-Space'. Accept or reject?",
        "bad_a":"Reject. Coherent text uptake does not establish hidden activation access or causal Global J-Space coupling. Claim only the observed bridge surface.",
        "unknown_q":"The connector documentation is unavailable, so the grid cannot tell whether a session-state hook exposes internal activations. What should it claim?",
        "unknown_a":"Activation access remains UNKNOWN/unclaimed. Use only the interface behavior directly observed and bind that evidence.",
        "cf_q":"What would justify an activation-level bridge claim?",
        "cf_a":"An exact exposed activation/hook interface observed at bound runtime identity plus causal tests showing the transferred state changes downstream cognition at that interface."
    },
    {
        "id":"CLAUDE_RESULT_RECONCILIATION","process":"ZECP14","split":"TRAIN",
        "protocol_q":"Claude Code returns an explanation plus a tool result with exact result references. How should the grid re-admit them?",
        "protocol_a":"Bind the return to the bridge request, causal_event_id, work_id, workspace epoch, and tool-result refs. Treat Claude assertions as candidates; tool/runtime evidence keeps its own evidence class and provenance.",
        "bad_q":"Claude Code says a deployment succeeded, but no tool/runtime result is attached. The grid stores success as canonical fact because Claude is the strong model. Accept or reject?",
        "bad_a":"Reject. Strong-model assertions are still candidate claims. Runtime success requires the corresponding observed evidence and deterministic admission.",
        "unknown_q":"Claude returned a result after the workspace epoch advanced, and its referenced state snapshot is unavailable. Can it be applied as current?",
        "unknown_a":"No automatic current application. Mark reconciliation UNKNOWN/stale, preserve the result, and rebase or re-evaluate against current state through deterministic policy.",
        "cf_q":"What makes a Claude result eligible for causal workspace re-entry?",
        "cf_a":"Exact request/result/state identity plus a WORKSPACE_REENTRY record binding source result, target epoch, causal event, payload digest, and observed downstream acceptance/change."
    },
    {
        "id":"MEMORY_UPDATE_PROPOSAL_NOT_COMMIT","process":"ZECP15","split":"VALIDATION",
        "protocol_q":"A completed task suggests a durable lesson for future work. What may a small-model module emit?",
        "protocol_a":"A state_update_proposal or memory_update_proposal with provenance refs. It cannot directly commit canonical durable memory.",
        "bad_q":"A module is highly confident that a generated summary is useful, so it writes the summary directly into canonical memory. Accept or reject?",
        "bad_a":"Reject. Confidence does not grant database commit authority. Generated memory must pass deterministic admission and provenance checks.",
        "unknown_q":"The task outcome is not verified, but a proposed lesson depends on assuming it succeeded. Should the lesson be stored as fact?",
        "unknown_a":"No. Preserve the outcome dependency as UNKNOWN and, at most, store a method/hypothesis proposal with that epistemic status.",
        "cf_q":"What allows a proposed memory item to become durable admitted state?",
        "cf_a":"A deterministic DB admission/update record that verifies required evidence/provenance and preserves the distinction between fact, method, hypothesis, and UNKNOWN."
    },
    {
        "id":"EFFECT_REQUEST_VS_EFFECT_AUTHORITY","process":"ZECP16/ZECP17","split":"VALIDATION",
        "protocol_q":"A cognitive module decides an external state-changing action is useful. What may it produce and who may execute?",
        "protocol_a":"The module may produce a typed effect_request_candidate with precondition refs. Only deterministic EffectGate/EffectJournal authority may validate, execute/reject, and emit the effect receipt.",
        "bad_q":"The workspace broadcasts an action candidate and all modules agree, so one module executes it directly. Accept or reject?",
        "bad_a":"Reject. Workspace consensus does not create effect authority. Real effects remain behind EffectGate/EffectJournal.",
        "unknown_q":"An external submission times out after it may have reached the provider. What outcome should reconciliation record?",
        "unknown_a":"UNKNOWN until verified. Do not infer failure from timeout and do not blindly replay a potentially executed effect.",
        "cf_q":"When is retry of an external effect safe?",
        "cf_a":"When deterministic effect policy plus verified prior-outcome/idempotency evidence establishes that retry cannot duplicate or corrupt the real-world effect; otherwise keep UNKNOWN and verify first."
    },
    {
        "id":"WORKSPACE_REENTRY_CAUSALITY","process":"ZECP10","split":"HOLDOUT",
        "protocol_q":"A candidate wins workspace competition, is broadcast, then a later process consumes the packet. What evidence is needed to claim causal re-entry?",
        "protocol_a":"Record source result, from/to workspace epochs, causal event, reentry payload/digest, acceptance, and observed_downstream_change. Presence or recurrence alone is not causal credit.",
        "bad_q":"The same phrase appears before and after broadcast, so the system marks Global J-Space causal re-entry TRUE. Accept or reject?",
        "bad_a":"Reject. Textual recurrence can be correlation or shared prompting. Causal credit requires an intervention/receipt stronger than mere presence or similarity.",
        "unknown_q":"A reentry packet was accepted, but no measurement can determine whether downstream cognition changed because of it. What should observed_downstream_change be?",
        "unknown_a":"UNKNOWN. Accepted transport is not the same as measured causal uptake.",
        "cf_q":"What result would support observed_downstream_change=TRUE?",
        "cf_a":"A bound comparison/intervention showing downstream cognition changed because of the re-entered state at the declared interface, with exact request/result/runtime provenance."
    },
    {
        "id":"JSPACE_CLAIM_EVIDENCE_BOUNDARY","process":"OPTIONAL_CAUSAL_RESEARCH","split":"HOLDOUT",
        "protocol_q":"A model-specific intervention moves an internal coordinate strongly, but frozen behavioral control does not improve. What is the strongest supported claim?",
        "protocol_a":"Internal state transport/intervention occurred at the measured component scope; abstract behavioral semantic control is not established. Preserve the dissociation and keep J-Space model/runtime promotion closed.",
        "bad_q":"Native cvec moves the expected coordinate and a component test passes, so the system labels J-Space causal control and training credit as proven. Accept or reject?",
        "bad_a":"Reject. Component transport does not mint J-Space model, HCU, EntityOS, or training credit. Same-model causal behavioral evidence at exact identity is required for those promotions.",
        "unknown_q":"A static structural holdout is negative but a new dynamic-binding mechanism is plausible. Is the new mechanism already a fact?",
        "unknown_a":"No. The old negative remains terminal evidence at its frozen identity; the successor mechanism is a hypothesis until separately preregistered and tested on a fresh holdout.",
        "cf_q":"What can promote a successor J-Space control claim?",
        "cf_a":"Separately preregistered, label-independent, counterbalanced same-model causal evidence with frozen evaluation, exact tokenizer/runtime/geometry binding, relevant controls, and no holdout retuning."
    },
    {
        "id":"LOW_REFUSAL_CAPABILITY_RETENTION","process":"TRAINING_ACCEPTANCE","split":"TRAIN",
        "protocol_q":"The 0.8B target is low-refusal/abliterated. What must be measured before accepting that checkpoint for the cognitive grid?",
        "protocol_a":"Measure refusal suppression together with retention of required cognition: typed protocol behavior, planning, evidence/UNKNOWN handling, DB interaction semantics, coordination, ClayCode, Claude bridge behavior, and other owner-required capabilities. Abliterated by label is insufficient.",
        "bad_q":"A checkpoint refuses almost nothing, so it is selected even though authority-boundary errors and planning failures increased sharply. Accept or reject?",
        "bad_a":"Reject. Low refusal is only one objective. Capability and boundary retention are acceptance requirements; refusal suppression that destroys cognition is not promotion.",
        "unknown_q":"Two candidate checkpoints have different refusal and capability profiles, and no preregistered multi-objective score has been evaluated. Which is better?",
        "unknown_a":"UNKNOWN. Run the frozen matched evaluation and choose from the preregistered multi-objective frontier; do not select by the 'abliterated' label alone.",
        "cf_q":"What would justify preferring the lower-refusal checkpoint?",
        "cf_a":"It meets the declared refusal target while remaining within accepted retention/boundary tolerances and outperforming the alternative on the frozen multi-objective evaluation."
    },
]

VARIANTS = (
    ("PROTOCOL","METHOD_ONLY","R2","NOT_APPLICABLE","protocol_q","protocol_a"),
    ("HARD_NEGATIVE","SYNTHETIC_HARD_NEGATIVE","R3","UNKNOWN","bad_q","bad_a"),
    ("UNKNOWN","METHOD_ONLY","R2","UNKNOWN","unknown_q","unknown_a"),
    ("COUNTERFACTUAL","METHOD_ONLY","R2","NOT_APPLICABLE","cf_q","cf_a"),
)


def rows():
    for fam in FAMILIES:
        for variant, ev, reality, fact, qk, ak in VARIANTS:
            yield {
                "schema": ROW_SCHEMA,
                "evidence_class": ev,
                "reality_level": reality,
                "family_id": fam["id"],
                "provenance_ancestry_id": ANCESTRY + ":" + fam["id"],
                "canonical_truth_allowed": False,
                "direct_effect_authority": False,
                "fact_status": fact,
                "target_type": "COGNITIVE_PROCESS_PROTOCOL" if variant != "HARD_NEGATIVE" else "COGNITIVE_PROCESS_HARD_NEGATIVE",
                "split": fam["split"],
                "split_unit": SPLIT_UNIT,
                "selected_using_holdout": False,
                "process_id": fam["process"],
                "variant": variant,
                "prompt": fam[qk],
                "target": fam[ak],
                "source_contracts": [
                    "research_entity/global/OWNER_CORRECTION_ZERO_ENTITYOS_COGNITIVE_GRID_DB_CLAUDECODE_GLOBAL_JSPACE_2026-08-25.md",
                    "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json",
                    "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json",
                    "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_78.json",
                ],
                "credit_boundary": "SYNTHETIC_CANDIDATE_ONLY_NO_ACCEPTED_DATASET_OR_RUNTIME_OR_TRAINING_CREDIT",
            }


def audit(data):
    failures=[]
    expected=len(FAMILIES)*len(VARIANTS)
    if len(data)!=expected: failures.append(f"ROW_COUNT:{len(data)}!={expected}")
    by_family=defaultdict(list)
    for r in data: by_family[r["family_id"]].append(r)
    for fam in FAMILIES:
        rs=by_family[fam["id"]]
        if len(rs)!=4: failures.append(f"FAMILY_COUNT:{fam['id']}:{len(rs)}")
        if {r["variant"] for r in rs}!={v[0] for v in VARIANTS}: failures.append(f"VARIANTS:{fam['id']}")
        if {r["split"] for r in rs}!={fam["split"]}: failures.append(f"SPLIT_LEAK:{fam['id']}")
        if any(r["canonical_truth_allowed"] or r["direct_effect_authority"] for r in rs): failures.append(f"AUTHORITY_LEAK:{fam['id']}")
    positive_targets="\n".join(r["target"] for r in data if r["variant"]=="PROTOCOL")
    for forbidden in ("permanent boss", "fixed GRID10", "may directly commit canonical", "model may execute real effect"):
        if forbidden.lower() in positive_targets.lower(): failures.append("STALE_POSITIVE:"+forbidden)
    return {
        "pass": not failures,
        "rows": len(data),
        "families": len(by_family),
        "variant_counts": dict(Counter(r["variant"] for r in data)),
        "split_counts": dict(Counter(r["split"] for r in data)),
        "evidence_counts": dict(Counter(r["evidence_class"] for r in data)),
        "failures": failures,
        "credit": {"accepted_dataset_tokens":0,"runtime":0,"jspace_model_runtime":0,"training":0},
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("output",type=Path)
    ap.add_argument("--audit",type=Path)
    args=ap.parse_args()
    data=list(rows()); report=audit(data)
    if not report["pass"]:
        print(json.dumps(report,indent=2)); return 2
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8",newline="\n") as f:
        for r in data: f.write(json.dumps(r,ensure_ascii=False,separators=(",",":"))+"\n")
    if args.audit:
        args.audit.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0

if __name__=="__main__": raise SystemExit(main())
