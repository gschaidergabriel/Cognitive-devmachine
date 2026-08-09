# ClayCode Trigger Run — Host-owned DB transaction lowering

Run: `claycode_20260809T165804p0700_chatgpt_dbtx_broker`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` (`IN_PROGRESS`)  
Promotion: **NONE**  
Gate advancement: **NONE**

## Executive result

This run attacked an unclaimed BASE runtime/application gap rather than duplicating the concurrent parser, relation-namespace, loop-control or HTTP workers.

Question: can current ClayCode G9 typed-record / provenance / effect-reference semantics express and lower a DB-backed transactional service through external host-owned authority, including commit, rollback, idempotent replay and crash recovery, without inventing a DB-specific ClayCode core primitive?

For the bounded local proxy, **yes**.

A hand-authored canonical ClayCode-like transaction IR was lowered to a deterministic Python guest. The guest received no SQLite path or connection. It received only a runtime-inherited Unix socket endpoint and sent an allowlisted typed DB operation protocol to a host broker that exclusively owned the SQLite connection.

Observed:
- valid host resource executed;
- missing resource denied, exit 77, no state change;
- forged numeric resource denied, exit 77, no state change;
- wrong logical DB resource denied, exit 78, no state change;
- committed transfer changed Alice 100 -> 70 and Bob 50 -> 80;
- a subsequent transfer followed by rollback produced no durable change;
- replay of committed idempotency key `k1` did not duplicate the effect;
- forced guest crash after an uncommitted transfer left the initial state intact;
- 6 structurally invalid IR programs were 6/6 rejected before execution;
- 1,000 protocol mutations were 1,000/1,000 denied with no DB mutation;
- 2,000 randomized transaction sequences produced **0 differential mismatches** against an independent pure state-machine oracle;
- 10 successful runs with inherited runtime descriptor numbers 65..74 kept the same semantic/generated identity;
- 30 separate-process positive runs had median wall time about 24.18 ms on this hosted proxy.

This does **not** pass `DB_SERVICE`, `GENERAL_PURPOSE_GATE` or BASE. It is not the target Ubuntu developer host, not the production parser, not native/WASM code, and unrestricted Python retains ambient host APIs outside the tested broker path.

## Internal grounding / Fusion 1

Canonical remained r2 / `04234efd...` before the durable run write. BASE remains the active stage and its governing law remains **less change, more compile**.

The newest concurrent parser/control run already established an executable G9-vs-EBNF self-conformance defect and proposed a small grammar repair rather than semantic redesign. That lane was assimilated, not duplicated.

The earlier HTTP APP-02 run demonstrated a related network-resource boundary, but shared project ancestry is preserved and it is not counted as independent replication.

All nine current research branches were included. ClayGraph and UnifiedDB were read deeply; FRANK C9, Clayresearch, Harness, GWT, Hyperposition and Emergenz constraints were carried into the experiment.

## Cross-branch constraints retained

### FRANK
C9 requires presence != admissibility != selection != authority, intent != permit, semantic identity != runtime placement, and replayable/idempotent recovery. The DB experiment keeps logical DB identity separate from the runtime handle and from host-owned execution authority.

### UnifiedDB
The experiment supports separating semantic transaction identity, runtime resource instance, backend transaction mechanics and durable effect/outcome receipt. It does not imply physical database monolithization.

### ClayGraph
Activation/relevance cannot authorize a DB write. Any future graph-selected transaction still crosses the typed host resource boundary.

### GWT / Hyperposition / Emergenz
DB success is not workspace uptake or emergence evidence. Selection and topology do not mint resource authority.

### Harness
This is a BASE precursor. A future Golden Trace should replay the same semantic DB program across backends and require identical transaction/outcome/idempotency behavior plus absent/forged/stale-resource denial and crash recovery.

## Hypotheses and counterhypotheses

### H-CC-DBTX-01 — generic typed IR + DB resource adapter
Status: `SUPPORTED_LOCAL_PROXY`.

Counterhypothesis: ClayCode needs a first-class DB transaction core construct to preserve rollback/replay semantics.

Discriminator: 2,000 randomized explicit transaction sequences were run against SQLite and a separate pure state-machine oracle. Result: 0 mismatches in the tested slice. No DB-specific core syntax was required.

### H-CC-DBTX-02 — runtime handle outside generated identity
Status: `SUPPORTED_LOCAL_PROXY`.

Ten successful executions varied only the inherited descriptor number from 65 to 74. Generated-code identity remained constant and behavior remained correct. Missing, forged and wrong logical resources failed closed.

### H-CC-DBTX-03 — rollback/recovery survives guest failure
Status: `SUPPORTED_LOCAL_PROXY`.

The guest began a transaction, requested a transfer and exited with code 91 before commit. Broker cleanup rolled the transaction back. Balances and durable idempotency keys returned to the initial state.

### H-CC-DBTX-04 — component-resource backend
Status: `OPEN`.

A WIT/WASI-style resource backend is a strong second-backend candidate. It must be compared directly against a native Ubuntu host-resource path before selection.

## External triangulation

Primary SQLite documentation states that explicit transactions persist until COMMIT or ROLLBACK and that BEGIN transactions do not nest; SAVEPOINT is used for nested transaction structure. SQLite also documents atomic/serializable transaction behavior.

Important consequence: the proxy's rejection of nested BEGIN is **backend behavior, not a universal ClayCode language law**.

Primary Component Model/WIT documentation describes resources as handles to entities outside a component, including ownership/borrowing. This independently supports testing a typed host-resource ABI. WIT is an interface contract, not a replacement for ClayCode behavior semantics.

## Concurrent final pulse

A same-time Clayresearch transaction-envelope worker completed before this report. It found a compatible refinement: effect-bearing decisions should carry a dependency-scoped read-set plus capability epoch/validity into a runtime commit envelope, with retry/abort receipts. Its ClayCode feedback explicitly requested compiler-emitted dependency metadata/runtime commit logic and **no new syntax**.

This is assimilated as compatible same-project convergence, not independent replication.

DB implication: the next broker experiment must add stale/revoked capability epochs and unrelated-state churn, not only missing/forged handles.

## Executable artifacts

- `experiments/dbtx_app03/DBTX_PROBE.clay`
- `experiments/dbtx_app03/CANONICAL_IR.json`
- `experiments/dbtx_app03/generated_guest.py`
- `experiments/dbtx_app03/EXECUTABLE_RESEARCH_RECEIPT.json`

Hashes recorded by the executed run:
- source SHA-256: `b2a5e1a7fa66a0b7a02f1d6a63414d477fa47b2d8372a8e2564200906fc040b4`
- semantic SHA-256: `f3aea74512ea3182e7b2f1bdca172027c0c42fd83d65d33d5b167f219b09fb68`
- contract SHA-256: `bffbe69ccd747976b805e0dde8e3b35f681a037101c73c82cff7a79815ed3406`
- generated target SHA-256: `69622e0e6795b12807c0bac7d498d4975780c6d4d578440636f4cd13c0ea49dc`

The runtime descriptor is deliberately absent from semantic and generated-code identities.

## Negative results / limitations

1. **Raw inherited FD is not a production sandbox.** Unrestricted Python retains ambient imports/system APIs. Production acceptance requires runtime/OS-enforced imports/capabilities.
2. **Nested BEGIN is backend-specific.** Savepoint/nesting, cancellation, concurrent transactions and multi-resource commit remain open.
3. **Production parser bypassed.** The test starts from a hand-authored canonical IR proxy because the G9 production parser is not released.
4. **Official repo-local preflight/Goodman validator not executed.** Connector-only manual manifests are durable, but no local-validator PASS is claimed.
5. **No exact Andreas Ubuntu target execution.** Local Linux proxy evidence is not target-host validation.

## Goodman anti-echo result

Three imported FRANK assumptions were actively challenged:

- external host authority for protected effects -> **SUPPORTED** by DB denial tests plus independent resource-handle design;
- semantic identity distinct from runtime resource instance -> **SUPPORTED** by 10 changed runtime handles with unchanged generated identity and behavior;
- replay/recovery requires a new ClayCode transaction core primitive -> **REFINED downward**: generic typed IR + runtime transaction API was sufficient for the bounded single-resource slice. Harder transaction semantics remain open falsifiers.

No FRANK/ClayCode shared ancestry was counted as independent evidence.

## Fusion 2 — architecture delta

Do **not** add a magical DB-specific `transaction` primitive to ClayCode core now.

Next implementation sequence:
1. represent transaction intent/state in ordinary typed canonical IR;
2. add a typed DB transaction/resource API in stdlib/SDK;
3. emit dependency read-set and capability epoch/validity metadata;
4. lower through the resource/FFI boundary;
5. keep runtime handles out of semantic/generated identities;
6. require commit/rollback/idempotency/retry/abort/crash receipts;
7. make backend capabilities such as savepoints/nesting/cancellation explicit;
8. fail lowering if required semantics cannot be legalized;
9. compare at least two backends before freezing the ABI.

This follows BASE: implementation closure first; semantic expansion only after an executable counterexample.

## Stage impact

No gate advanced. The run reduces uncertainty in `CC-WP-04`, `CC-WP-06`, `CC-WP-07`, `CC-WP-08`, `CC-WP-10` and `CC-WP-11`, but closes none of them.

`DB_SERVICE` remains **NOT PASS**.

## Highest-information next experiment

Freeze the same canonical DB transaction IR and execute it on the Ubuntu target through:
1. a native Clay runtime typed DB resource adapter;
2. a Component Model/WIT resource backend.

Require identical semantic hash, explicit backend/contract hashes, transaction/query/idempotency equivalence, savepoint/nesting capability negotiation, dependency/capability epoch revalidation, stale/revoked-resource denial, unrelated churn controls, cancellation/resource-close behavior, crash/restart replay, no ambient filesystem/network authority outside grants, fuzzing and latency/resource receipts.

Only an unrepresentable required semantic should trigger a ClayCode core change.

## Completion boundary

Completed: canonical boot, current-stage grounding, all-nine-branch interconnect, concurrent-worker pulse, hypotheses/counterhypotheses, primary-source triangulation, executable DB lowering proxy, 2,000-case differential test, 1,000 adversarial mutations, crash/replay/resource-denial tests, Goodman review, negative results, micro-packet, branch feedback and durable report.

Not completed or claimed: production parser, official local validators, E2B, exact Ubuntu target execution, production capability sandbox, second backend, DB_SERVICE PASS, BASE work-package PASS, canonical scientific promotion.
