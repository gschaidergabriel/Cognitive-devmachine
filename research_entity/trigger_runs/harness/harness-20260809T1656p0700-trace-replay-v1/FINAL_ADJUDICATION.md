# Final Adjudication — Harness Trace/Replay Trigger Run

Run: `harness-20260809T1656p0700-trace-replay-v1`

Live-reread cutoff: after assimilation of concurrent SourceChainEvidence v1/v1.1, H-WP-02 ledger-lineage adjudication, ClayCode parser/stage-identity work and resource lifetime/ABA work observed through commits including `9dc587e2a0b7da9b3e1519dae1c36cc81d0debae` and `2eea04dcf972d0b6f7eeb7950e5922dc21cf3442`.

## Decision

`CURRENT_TRIGGER_RUN = COMPLETE`

`H-WP-11 = OPEN_FOUNDATION_IMPLEMENTED`

`H1_REFERENCE_HARNESS = NOT_PASS / BLOCKED_BY_BASE`

`SCIENTIFIC_PROMOTION = NONE`

`FRANK_LIVE_HARNESS_MUTATION = NONE`

## Durable result

The run produced and executed `research_entity/harness/trace_replay_v1.py`, a loop-aware TurnTraceEnvelope validator and semantic differential oracle.

Local synthetic execution:
- 13/13 embedded tests PASS;
- 1400/1400 targeted invalid mutations detected;
- 64-level nested re-entry PASS;
- cross-implementation id normalization EQUIVALENT when semantics are unchanged;
- Python compile PASS.

The run then assimilated concurrent work instead of freezing itself to its initial design.

### Composite oracle now required

TurnTraceEnvelope is necessary but not sufficient for later H1->H2 equivalence.

Current composition contract is:

`ORACLE_COMPOSITION_CONTRACT_V1_2.json`

It requires layered evidence across:
1. imported baseline transaction identity;
2. canonical semantic content identity;
3. state version/history identity;
4. runtime trace/execution identity;
5. source artifact identity;
6. grammar identity;
7. parser operational-semantics identity;
8. canonical ProgramSemanticId at typed IR or an equivalently verified canonical semantic stage;
9. type/effect contract identity;
10. lowering contract identity;
11. executable artifact identity;
12. source-chain evidence identity;
13. dynamic Run ClayGraph identity;
14. when effects touch live host resources: capability authorization epoch, resource type, lifetime/generation, opaque handle instance and ownership/borrow state.

### SourceChainEvidence status

Concurrent SourceChainEvidence v1 has strong bounded synthetic execution evidence, including 8/8 unit tests and 5000-case invalid/differential sweeps with no reported misses in its scoped families.

A newer v1.1 adds `parser_semantics_hash`, correctly separating parser precedence/associativity/fallback behavior from grammar syntax identity.

However, the semantic-authority boundary remains OPEN: copying one `semantic_hash` through source/parse/typed-IR is not accepted as proof that those stages independently know or mint canonical program semantics. Current best hypothesis places `ProgramSemanticId` at deterministic canonical typed IR or an equivalently verified canonical semantic stage, derivation-bound to earlier artifacts/contracts.

### Ledger identity status

Concurrent H-WP-02 work found two incompatible ledger lineages. The current best identity stack separates:
- baseline transaction root;
- semantic content hash;
- state version/history hash;
- trace/execution root.

No lineage is promoted unchanged.

### Resource lifetime status

Concurrent ClayCode resource experiments provide bounded executable evidence that semantic/resource descriptors and capability references are not sufficient live host-resource identity.

Two complementary synthetic experiments reported:
- 20,000 randomized broker/oracle operations with 0 mismatches in the tested lifetime/type/borrow model;
- forced reusable-slot ABA: raw slot handles failed the stale-use property in 16/16 compact cases and 100,000/100,000 fuzz cases, while the tested generation/lifetime-checked scheme had 0 stale accepts.

These results do not prove a production Frank bug and do not uniquely select generation tags. They justify a future Harness conformance family requiring stale/ABA/wrong-type/borrow/restart tests and an opaque lifetime-checked resource identity mechanism.

## Scientific/engineering boundaries

- No live Frank execution occurred.
- No Andreas Ubuntu target execution occurred.
- No H1/H2/H3 gate advances.
- No ClayCode work package closes from this run.
- No paid model work is authorized.
- Shared-repository/concurrent-worker convergence is not independent scientific replication.
- The hosted worker could not execute repository-local `research_interconnect_preflight.py`; the limitation is preserved in the run manifest.
- Frank did not authorize or mutate its own Harness; all work was performed under separate Research Entity authority.

## Highest-information next path

During BASE:
1. close parser/canonical typed-IR semantics and establish the ProgramSemanticId mint/derivation contract;
2. execute the composite source-chain oracle through the production parser/type-effect/lowering pipeline;
3. freeze backend-neutral ResourceHandle lifetime/type/ownership lowering semantics only where compiler/application evidence requires them;
4. keep authority external to telemetry/model/graph/GWT/semantic identities.

After BASE PASS:
5. map frozen Frank baseline receipts into TurnTraceEnvelope + SourceChainEvidence;
6. execute Golden replay on Andreas' Ubuntu developer system;
7. implement checkpoint/module/counterfactual replay and dynamic Run ClayGraphs;
8. add compiled/outside-in crash/restart/network/resource fault testing;
9. run H1->H2 composite differential equivalence.

## Stop condition

All material deliverables possible in the current hosted execution surface for this trigger have been completed and committed. Remaining H-WP-11 closure depends on the active BASE gate and later target-host/reference-Harness execution; claiming more now would overstate evidence.
