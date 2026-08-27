# KMP — Loop scheduler dimensions belong in semantic identity when they change behavior

- packet_id: `KMP-CLAYCODE-LOOP-SCHEDULER-SEMANTIC-IDENTITY-20260809`
- domains: `claycode, frank, harness, gwt, hyperposition, claygraph, unifieddb, emergenz`
- epistemic_class: `LOCAL_PROXY_EXECUTABLE_RESEARCH_PLUS_PRIMARY_SOURCE_TRIANGULATION`
- status_hint: `OPEN_SUPPORTED_NOT_PROMOTED`
- origin_actor: `chatgpt-secondary`
- provider/model: `OpenAI / GPT-5.6 Sol`
- canonical_parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- experiment_ref: `research_entity/trigger_runs/claycode/claycode_20260809T1654p0700_chatgpt_loop_scheduler_identity/EXECUTABLE_RESEARCH_RECEIPT.json`

## Atomic claim

For coupled recurrent programs, logical timescale/schedule, commit semantics, genuinely sequential ordering and recurrence/halting policy are part of program semantic identity whenever changing them changes observable typed state. A canonical/semantic hash that ignores those dimensions can collide across behaviorally distinct programs.

This does **not** imply every source declaration order is semantic. For loop families typed as same-epoch snapshot/set updates, declaration order may be canonicalized away.

## Executable evidence

Deterministic seed `20260809`, 2,000 randomized stable three-loop systems:

- baseline periods `fast:mid:slow = 1:2:5` vs flattened `1:1:1`: endpoint changed **2000/2000**;
- sequential `fast->mid->slow` vs `slow->mid->fast`: endpoint changed **2000/2000**;
- snapshot-atomic same-epoch declaration permutation: endpoint changed **0/2000**;
- canonical snapshot semantic-trace hash changed under declaration permutation: **0/2000**;
- adaptive-fast vs fixed-5 recurrence changed endpoint **1260/2000**; mean recurrence-count saving was **10.44%** in this toy;
- one deliberately schedule-blind contract hash collapsed four behaviorally distinct variants to **1** identity; schedule-aware hashing produced **4** identities.

## Negative results

- `N-CC-SCHEDULE-BLIND-HASH-005`: schedule-blind semantic identity is unsafe for the tested coupled recurrence class.
- `N-CC-TIMESCALE-FLATTENING-006`: erasing explicit multirate periods changed behavior in every tested randomized case.

## Relationship to concurrent work

Concurrent ClayCode work independently established that generic structured recurrence can represent the current FRANK loop-of-loops proxy and that epoch-snapshot semantics prevent accidental order coupling for unordered same-epoch updates. This packet adds the semantic-identity/hash discriminator; it does not count those related ChatGPT-authored runs as independent replication.

## Architecture implication

No new FRANK-specific loop syntax is justified. Prefer a generic typed recurrence/scheduler contract over existing G9 semantics, carrying at least:

- loop identity/family;
- logical clock/timescale/period/phase where applicable;
- typed loop-carried state and read/write dependencies;
- commit model (`SNAPSHOT_ATOMIC`, `SEQUENTIAL_ORDERED`, or explicitly asynchronous/event-driven equivalent);
- semantically meaningful order only when declared ordered;
- recurrence budget and halt/continue reason;
- epoch/provenance/rollback/intervention/readout receipts.

## Falsifier / next test

Freeze the H1 loop/dependency traces and lower the same typed recurrence network through H1 host semantics and the ClayCode compiler/runtime. Hashes must distinguish behavior-changing schedule mutations and ignore only type-declared nonsemantic permutations. Any unexplained H1/H2 state or trace divergence reopens BASE semantics.

## Boundaries

Synthetic mechanism evidence only; not live FRANK runtime evidence, not BASE gate completion, not emergence evidence, and never execution authority.