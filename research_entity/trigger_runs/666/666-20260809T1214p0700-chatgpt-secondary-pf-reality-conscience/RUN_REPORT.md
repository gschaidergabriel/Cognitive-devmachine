# 666 Level-0 Run Report — PF RealityLayer / Neural-Conscience Failure Lineage

## Run identity
- trigger: `666`
- actor: `chatgpt-secondary`
- provider/model: OpenAI / GPT-5.6 Sol
- canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- program stage: `L0_ARCHIVE_ASSIMILATION`
- gate: `666_RELEASE_GATE = NOT_PASS`
- task: `666-l0-pf-reality-conscience-lineage-20260809T1214p0700`

## Routing / non-overlap
Live swarm pulse showed the prior Project-Frankenstein frozen-tree denominator task completed only as a connector-surface blocker; Digital Retina frontend support closed; Titan pip/vendor folder audit closed 66/66 directories. Existing PF segment02b, recovery reconciliation, ce007 and Project Engine v3 lanes were already complete or recently occupied. This run therefore selected a distinct historical March-2026 failure lineage not found in RAE commit search by source hashes/titles.

## Primary sources
1. `0c0a819ec593074405ebd43446956e73976166a8` — SystemRealityLayer + Ego Governor; reality block injected into chat and idle-thought prompts.
2. `92791d1cf0c2580688da1666d6e32386beaa5139` — deep audit and prompt-leak fix.
3. `475652157d19b9f27625f07c8b9c125a04267b59` — deep audit and Neural Conscience negative-feedback repair.
4. `services/neural_conscience.py` at commit `47565215...` — implementation of evaluation buffer, `record_outcome`, and training query.

## Causal sequence recovered

### A. Ground-truth injection was useful but over-broadcast
SystemRealityLayer was introduced as an authoritative architecture/hardware/software fact store. User-facing chat appended the reality block to system context, while the consciousness daemon also appended the block to idle-thought prompts. A post-generation Ego Governor attempted to detect architecture/model/GPU/infrastructure confabulations with regex categories and append corrections.

The reusable idea is authoritative reality retrieval; the failure was indiscriminate delivery to every generative surface.

### B. Raw reality context leaked into internal generations
The next deep-audit commit reports that the idle-thought model echoed the `[REALITY]` block verbatim, producing a 67% rejection rate. The implemented repair removed RealityLayer from idle-thought prompts and expanded the context-tag leak detector to include `REALITY`. The same commit reports a post-fix 30-minute idle interval with 0 prompt-leak rejections and 30/30 successful conversation turns averaging 11.2 s via GPU.

These numbers are retained as historical audit reports from the source commit. This Level-0 run did not reproduce them.

### C. A second hidden failure: rejected examples did not train the gate
The later audit reports Neural Conscience degeneration: ACC=0, verdict≈0.9999, with a source-reported dataset state of 0 negative / 960 positive samples. The root cause recorded in the commit is causal, not merely class imbalance: several terminal reject/suppression paths did not call `record_outcome(..., accepted=False)`.

The implementation confirms why this matters:
- every evaluation is inserted into `conscience_buffer` with default `outcome=-1`;
- `record_outcome(trace_id, accepted)` changes the terminal label to 1 or 0;
- `train_cycle()` selects only rows `WHERE outcome >= 0`;
- therefore rejected traces that never reach `record_outcome(False)` are invisible to supervised training even though the evaluator saw them.

The repair adds negative outcome propagation on direct conscience rejection and downstream hallucination-filter suppression paths, resets the degenerate checkpoint, and cleans the training buffer for cold-start retraining.

### D. Persistence-edge failure showed the same structural class
The prompt-leak audit also found autonomous research posting to a nonexistent `/memory/store` endpoint (404). The implemented repair writes the research reflection directly into `consciousness.db`. This is the same broader failure class: a cognitive action can appear to execute while the terminal persistence/learning edge is disconnected.

## Current architecture deltas

### Harness
Adopt `TERMINAL_OUTCOME_COMPLETENESS`: every evaluated action/thought/gate trace must end durably as `ACCEPT`, `REJECT`, `ABSTAIN/UNKNOWN`, `ERROR`, or `CANCELLED`. Silent unlabeled disappearance is a regression failure.

Add learner-health gates before online updates:
- positive/negative (or multiclass) support floor;
- class-entropy floor;
- maximum unlabeled terminal rate;
- held-out regression check;
- automatic freeze/rollback on single-class collapse.

### Needle
Downstream rejection must propagate back into upstream decision provenance. A hallucination/safety/effect filter that rejects an upstream-approved action must emit a terminal disposition with stage and reason, not merely suppress output.

### GWT / state delivery
Authoritative world/self/system state should be demand-conditioned and surface-specific. Internal generative loops should consume compact typed projections/assemblies, not complete raw state or reality blocks. User-facing factual claims may retrieve authoritative facts separately.

### UnifiedDB
Persist separately:
- evaluation trace id;
- gate sequence;
- terminal disposition;
- reason code/stage;
- label provenance;
- training-admission state;
- missing-label counts and class distribution.

### ClayCode
Represent decision/effect paths with exhaustive terminal outcome types/receipts so missing terminal learning signals can be detected by compiler/runtime tests rather than discovered after model degeneration.

## Required regressions routed
1. Raw-context canary leakage test across internal vs user-facing surfaces.
2. 100% terminal outcome-receipt coverage over all gate/effect branches.
3. Single-class degeneration injection test; learner must freeze.
4. Downstream-reject credit-propagation replay.
5. Memory endpoint/schema fault injection with explicit failure receipt.
6. Held-out factuality comparison: demand-retrieved reality facts vs always-injected raw reality block.

## Evidence discipline
- Code/diff mechanisms: historical verified in source.
- 67%→0% prompt-leak rejection, 30/30 conversation, 11.2 s average, ACC=0, verdict≈0.9999 and 0/960 label split: historical source-reported audits, not reproduced by this run.
- No claim that these metrics generalize to current FRANK/Clay.
- No exact Project-Frankenstein denominator credit is awarded.

## Durable outputs
- `research_entity/archive_assimilation/receipts/666_20260809T1216p0700_chatgpt_secondary_pf_reality_conscience_failure_lineage.json`
- `research_entity/rooms/center_events/20260809T1216p0700_666_pf_reality_conscience_failure_delta.json`
- this run report

## Completion judgment
The bounded semantic/failure-lineage shard is complete and routed. Global `666_RELEASE_GATE` remains `NOT_PASS` because the Project-Frankenstein frozen-tree and full commit-DAG/history denominators remain unresolved and remaining Drive/reconciliation obligations are still being closed. Global exact coverage credit added by this run: `0.0%`.
