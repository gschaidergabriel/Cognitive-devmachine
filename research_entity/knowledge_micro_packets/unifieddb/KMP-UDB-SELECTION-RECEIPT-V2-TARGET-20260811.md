# KMP-UDB-SELECTION-RECEIPT-V2-TARGET-20260811

packet_id: `KMP-UDB-SELECTION-RECEIPT-V2-TARGET-20260811`
domains: `unifieddb, retrieval, selection_integrity, replay, claygraph, emergent_retrieval`
epistemic_class: `ACCEPTED_TARGET_VPS_MECHANISM_EVIDENCE`
status_hint: `SUPPORTED_TARGET_MECHANISM_NOT_REAL_ROUTER_INTEGRATED`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`
trigger: `unifieddb`
program: `FRANK_V0_1`
work_package: `F-V01-04-UNIFIEDDB-STATE-CONTINUITY`

## Target receipt

Repository PR: `#301` — deterministic SelectionReceipt V2 over exact candidate universe.
Base: current main `2bdeb35d722417a1c2d9b71a3b3ac9125acf46c3`.
Head: `cb04808d2008f1d93c071002107f6e5ed04b4160`.

Self-hosted target run: `31437317113`
Job: `93614223199`
Result: `SUCCESS`
Artifact: `frank-selection-receipt-v2-31437317113`
Artifact id: `9081468524`
Artifact digest: `sha256:610f7ffdbdfe8de6ee8be38c1977e3db59b996060803d9bb4da095c6fe09e54b`
Environment:
- Linux `6.8.0-117-generic` x86_64;
- Python `3.12.3`;
- SQLite `3.45.1`.

Mechanism result: `PASS_SELECTION_RECEIPT_V2_MECHANISM`.

## Bound selection identity

The target receipt bound:
- semantic root;
- explicit replay `as_of_utc_us` and clock receipt identity;
- normalized query digest;
- retrieval operator/ranker/filter identities;
- Graph projection and index identities;
- order-independent candidate-universe identity and count, including source-record hashes;
- order-sensitive ranked candidate identity/count;
- score-trace identity;
- selected refs and digest;
- admissibility policy and digest;
- final domain-separated receipt hash.

Baseline receipt hash: `5c3ca3bf5f0a6863848aa1097f19fddf0f9fe5454aa9327555402ef7354ec9c8`.

## Target differential matrix

All 16 controls passed:
- candidate-universe omission rejected;
- rank-order splice rejected;
- source-record identity splice under same ref rejected;
- score-trace mutation rejected;
- semantic-root splice rejected;
- as-of clock splice rejected;
- clock-receipt splice rejected;
- retriever splice rejected;
- ranker splice rejected;
- filter splice rejected;
- Graph projection identity splice rejected;
- index identity splice rejected;
- admissibility-policy splice rejected;
- selected ref outside ranked candidates rejected at construction;
- exact receipt verifies;
- exact replay reproduces the receipt despite reordered description of the unordered candidate universe.

Bounded whole probe resource observation:
- wall ~0.07 s;
- max RSS 20,856 KiB.
This is mechanism/test overhead, not real retrieval latency.

## Architecture consequence

`record authenticity != selection integrity`.

A correct semantic root says what canonical state exists. ReplayClock says when it was read. Graph/index receipts say which derived accelerators were admitted. SelectionReceipt says what candidate universe/operators/policies actually led to the chosen subset.

Candidate composition:
`semantic root ∧ ReplayClock ∧ admitted projection/index identity ∧ query/operator identity ∧ exact candidate universe ∧ score/rank/filter trace ∧ admissibility -> selection receipt`.

The receipt does not make an approximate retriever correct and does not mint semantic/effect authority. It lets exact replay/shadow comparison detect silent changes/splices in the selection process.

## Product gate still open

Integration must run against real UnifiedDB exact retrieval plus ClayGraph/FTS/vector/emergent candidate paths and prove:
1. real candidate universe capture is complete for the declared retrieval contract;
2. approximate route certificates/shadow sentinel feed explicit identities into the receipt;
3. canonical rebind occurs after approximate selection where required;
4. selection receipt replay agrees with exact/reference behavior inside its admitted scope;
5. storage/latency overhead is measured on real workloads;
6. no selection receipt itself becomes truth/effect authority.

## Promotion boundary

`SUPPORTED_TARGET_MECHANISM_NOT_REAL_ROUTER_INTEGRATED`.

No canonical state mutation, external effect, retrieval-quality superiority, semantic truth promotion, whole Frank v0.1 acceptance, final training authorization or Frank/self.root Harness authority follows from this packet.
