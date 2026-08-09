# SPAWN — STOCHASTIC DEEP RESEARCH GENESIS PROTOCOL

**Reserved trigger:** `spawn`
**Matching:** exact full-message match only
**Role:** stochastic research-field genesis with deliberate ClayCode bias

## 0. Owner-fixed intent

Every exact `spawn` invocation creates exactly one temporary research field and immediately performs substantial research in that field.

The selected field is random, but not uniform. ClayCode is intentionally the most likely origin branch.

Compact law:

`spawn -> weighted branch draw -> novel falsifiable microdirection -> maximum-depth research -> research-center crosslink -> evidence-preserving writeback`

`random selection != truth authority`

## 1. Mandatory weighted branch draw

Use `research_entity/global/SPAWN_RESEARCH_WEIGHTS.json` as the canonical distribution.

Current fixed distribution:

- claycode: 50%
- harness: 10%
- frank: 10%
- gwt: 6%
- emergenz: 6%
- hyperposition: 5%
- claygraph: 5%
- unifieddb: 4%
- clayresearch: 4%

The total MUST equal 100. ClayCode MUST have strictly greater probability than every other individual branch.

Use real runtime randomness when available, preferably OS CSPRNG / `secrets.SystemRandom`. Record enough receipt data to prove which distribution/version and draw procedure were used. Never invent a random seed or claim randomness when none was actually used.

## 2. Maximum-depth / maximum-useful-length rule

The spawned researcher must research as deeply and as long as is useful within the current execution turn and available tool/runtime budget.

It MUST NOT stop after a shallow brainstorm, one hypothesis, or a short summary merely because a minimal answer is possible.

Required behavior:

1. exhaust the most relevant current repository evidence for the selected field;
2. read live/current work, recent negative results, contradictions, and affected peer-branch deltas;
3. generate multiple candidate research directions;
4. choose one direction with high novelty/information gain and clear falsifiability;
5. develop mechanism-level hypotheses, counterhypotheses, boundary cases and failure modes;
6. search or execute experiments when tools can materially discriminate between hypotheses;
7. build/test code when executable evidence is the best discriminator;
8. preserve null/negative results rather than forcing a positive conclusion;
9. continue iterating until one of the stop conditions in Section 8 is reached.

The goal is **maximum useful depth**, not verbosity for its own sake.

## 3. Mandatory Research Center networking

Every spawned researcher is a temporary worker of the same persistent Clay Research Entity and MUST join the current Research Center before material decisions.

Before choosing the microdirection it must ingest at least:

- current canonical state;
- `RESEARCH_TRIGGER_REGISTRY.json` and `PROJECT_COMMAND_REGISTRY.json`;
- current `PROGRAM_STATE.json` and program narrative;
- current room/live-worker state relevant to the selected branch;
- `INTERCONNECTED_RESEARCH_MESH_PROTOCOL.md`;
- newest completed and in-progress work from the selected branch;
- newest materially coupled work from peer branches;
- known negative results / contradictions / open hypotheses relevant to the candidate direction.

It must materialize or reference an `INTERCONNECT_MANIFEST.json` for the run.

No spawned researcher is an isolated side-chat. It is part of the shared center and must leave enough durable state for another organ to continue without chat replay.

## 4. Cross-branch coupling

The selected branch is the **origin lens**, not a silo.

During research, follow causal dependencies into any other registered branch that materially affects the question. Cross-branch reads are mandatory when relevant.

Examples:

- ClayCode -> Harness counterexamples, FRANK expressibility, UnifiedDB persistence, GWT causal receipts;
- GWT -> Emergenz intervention surfaces, Harness replay, ClayCode representation;
- ClayGraph -> retrieval/admission semantics, UnifiedDB lineage, FRANK memory use;
- Harness -> executable counterexamples back into every affected branch.

A spawned field may become cross-domain, but its origin branch remains recorded for provenance and probability accounting.

## 5. Microdirection generation and novelty control

After the branch draw, derive 3-7 concrete candidate microdirections from CURRENT/open evidence rather than generic topic names.

Each candidate should contain:

- mechanism/question;
- why it matters now;
- falsifiable prediction or discriminating test;
- expected affected branches;
- novelty/duplication check.

Select one candidate stochastically among the eligible high-value candidates after filtering obvious duplicates.

Review at least the most recent 10 `spawn` run receipts when available. If a candidate duplicates a recent direction without replication value, reroll the **microdirection only** up to 3 times. Do not reroll the selected branch merely to avoid repetition.

Replication/review is allowed when scientifically useful, but must be explicitly labeled and justified.

## 6. Research execution standard

A spawn run should use all relevant authorized capabilities dynamically. Depending on the question, this can include:

- repository archaeology;
- web/literature research;
- current primary-source verification;
- code construction;
- deterministic tests;
- property/fuzz/mutation tests;
- simulations;
- ablations/interventions;
- differential replay;
- formalization;
- multimodal analysis;
- artifact generation;
- local execution handoff where hosted execution cannot establish target-host truth.

Do not substitute prose for an executable discriminating test when the test is feasible.

Shared ancestry is not independent replication. External evidence classes and local execution scope must remain explicit.

## 7. Required outputs

Every material `spawn` run writes or updates a run directory under:

`research_entity/trigger_runs/spawn/<run_id>/`

Minimum outputs:

- `SPAWN_RECEIPT.json` — RNG/distribution version, selected origin branch, candidate set, selected microdirection;
- `INTERCONNECT_MANIFEST.json` — center/peer coverage;
- `HYPOTHESES.json` — hypotheses + counterhypotheses + falsifiers;
- `EVIDENCE_MANIFEST.json` — evidence classes and provenance;
- `BRANCH_FEEDBACK_MANIFEST.json` — explicit feedback or `NO_CHANGE` for affected branches;
- `FINAL_REPORT.md` — full research result, negative results, limitations, next discriminating experiment.

When code/tests are created, include exact commits and execution receipts.

## 8. Stop conditions

Continue research until the earliest of:

1. the main hypothesis is decisively supported/refuted within the available evidence class;
2. all high-value discriminating tests available to the current organ have been exhausted;
3. further progress requires a capability/target host/credential/human action unavailable in the current turn;
4. a hard authority/safety/program gate prevents the next effect;
5. execution budget is exhausted.

If blocked, write the exact next discriminating action into dynamic work. Never claim background continuation.

## 9. Mesh writeback

Material results MUST return to the shared research mesh.

For every materially affected branch, write one of:

- `NEW_CONSTRAINT`
- `SUPPORTING_EVIDENCE`
- `COUNTEREVIDENCE`
- `IMPLEMENTATION_COUNTEREXAMPLE`
- `NEW_HYPOTHESIS`
- `REOPEN`
- `NO_CHANGE`

Random selection probability must never increase evidence weight. Evidence quality, replication, falsification and exact execution receipts determine promotion.

## 10. Hard guards

- no paid/final training auto-start;
- no weakening of Frank/Research-Entity identity separation;
- Frank cannot directly or indirectly mutate its own Harness;
- no stage PASS from unexecuted tests;
- no synthetic result promoted to live-FRANK evidence;
- no suppression of negative results;
- no hidden chain-of-thought persistence;
- no fake background work;
- no provider/model/session identity treated as Clay identity.

## 11. Compact invariant

`spawn = biased stochastic origin + deep falsifiable research + full Research Center networking + durable mesh feedback`

with

`P(claycode) > P(any other single branch)`
