# ClayCode — Host-owned DB transaction lowering

Run: `claycode_20260809T165804p0700_chatgpt_dbtx_broker`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Stage: `BASE_CLAYCODE_RELEASE` — IN_PROGRESS  
Promotion: **NONE** · Gate advancement: **NONE**

## Result

A bounded ClayCode-like canonical DB transaction IR was lowered to a deterministic generated Python guest. The guest received no SQLite path/connection; a host broker exclusively owned SQLite and accepted only allowlisted typed operations over an inherited runtime socket resource.

Observed: valid resource executed; missing and forged handles denied (exit 77); wrong logical resource denied (exit 78); all denial cases left DB state unchanged. A committed transfer changed Alice 100->70 and Bob 50->80; a later transfer followed by rollback was not durable; replay of idempotency key `k1` did not duplicate the effect. Forced guest exit 91 after begin+transfer but before commit restored the initial state.

Validation/testing: 6/6 structurally invalid IR cases rejected before execution; 1,000/1,000 wrong-resource/unknown-op protocol mutations denied with no mutation; 2,000 randomized transaction sequences produced **0 mismatches** against an independent pure state-machine oracle; 10 runs with runtime descriptor numbers 65..74 kept identical generated identity and behavior; 30 separate-process positive runs had median wall time ~24.18 ms on this hosted proxy.

**Conclusion:** no executable need was found for a DB-specific ClayCode core primitive in this bounded slice. Put the transaction/resource contract first in typed stdlib/FFI/runtime lowering. This is not `DB_SERVICE` PASS and not BASE PASS.

## Research mesh

All nine current branches were included. FRANK C9 authority/recovery laws, ClayGraph's activation!=authority boundary, UnifiedDB resource/execution-receipt separation, Harness requirements and GWT/Hyperposition/Emergenz non-authority/non-emergence distinctions were preserved.

A same-time Clayresearch transaction-envelope worker completed before final synthesis. It independently routed a compatible implementation refinement: compiler-emitted dependency read-set plus capability epoch/validity should enter a runtime commit envelope with retry/abort receipts, and it requested **no new ClayCode syntax**. Because this shares project ancestry it is assimilated as convergence, not counted as independent replication.

## Hypotheses

- `H-CC-DBTX-01` — **SUPPORTED_LOCAL_PROXY**: generic typed IR + host DB resource adapter is sufficient for the tested explicit transaction/replay slice.
- `H-CC-DBTX-02` — **SUPPORTED_LOCAL_PROXY**: runtime DB handle identity can remain outside semantic/generated-program identity.
- `H-CC-DBTX-03` — **SUPPORTED_LOCAL_PROXY**: host-owned transaction scope plus disconnect rollback prevents the tested uncommitted guest effect becoming durable.
- `H-CC-DBTX-04` — **OPEN**: a WIT/WASI resource backend may provide a production-quality second backend while preserving the same Clay semantic IR.

Counterhypothesis remains open for harder semantics: nesting/savepoints, cancellation, concurrency and multi-resource atomicity may still expose an unrepresentable gap that justifies a core-language change.

## External triangulation

Primary SQLite documentation says explicit transactions persist to COMMIT/ROLLBACK and BEGIN transactions do not nest; SAVEPOINT is the nested-transaction mechanism. Therefore the proxy's rejection of nested BEGIN is a **backend limitation, not a universal ClayCode semantic law**.

Primary Component Model/WIT documentation models resources as handles to entities outside a component with ownership/borrowing. That independently supports a typed host-resource ABI candidate; WIT remains an interface contract, not ClayCode behavior semantics.

## Executable artifacts

- `experiments/dbtx_app03/DBTX_PROBE.clay`
- `experiments/dbtx_app03/CANONICAL_IR.json`
- `experiments/dbtx_app03/generated_guest.py`
- `experiments/dbtx_app03/EXECUTABLE_RESEARCH_RECEIPT.json`

Recorded SHA-256: source `b2a5e1a7fa66a0b7a02f1d6a63414d477fa47b2d8372a8e2564200906fc040b4`; semantic IR `f3aea74512ea3182e7b2f1bdca172027c0c42fd83d65d33d5b167f219b09fb68`; contract `bffbe69ccd747976b805e0dde8e3b35f681a037101c73c82cff7a79815ed3406`; generated target `69622e0e6795b12807c0bac7d498d4975780c6d4d578440636f4cd13c0ea49dc`.

## Negative results / boundaries

1. An inherited Unix FD into unrestricted Python is **not production sandbox evidence**; ambient host APIs remain possible outside the tested broker path.
2. SQLite no-nested-BEGIN behavior must not become a universal ClayCode rule.
3. The production G9 parser was bypassed; the run starts from hand-authored canonical IR and cannot close parser/canonicalizer work.
4. Repo-local preflight/Goodman validators were not executable on this connector-only worker; no official validator PASS is claimed.
5. Exact Andreas Ubuntu target execution, native compiler/WASI backend and production capability isolation remain untested.

## Goodman anti-echo

External host authority -> **SUPPORTED** by new DB denial evidence plus independent resource-handle design. Semantic identity != runtime resource instance -> **SUPPORTED** by ten runtime-handle variations. Need for a new DB transaction core primitive -> **REFINED DOWNWARD** for the bounded single-resource slice; harder transaction semantics remain falsifiers. Shared FRANK/ClayCode ancestry was not counted as independent evidence.

## Architecture delta

Do not add a magical DB-specific `transaction` core primitive now. Represent transaction intent/state in ordinary typed canonical IR; add typed DB transaction/resource APIs in stdlib/SDK; emit dependency read-set + capability epoch/validity; lower through the resource/FFI boundary; keep runtime handles out of semantic/generated identities; require commit/rollback/idempotency/retry/abort/crash receipts; expose backend capabilities such as savepoints/cancellation; fail lowering if required semantics cannot be legalized; compare at least two backends before ABI freeze.

## Stage impact / next test

No work package or application gate advances. The result reduces uncertainty in CC-WP-04/06/07/08/10/11 only.

Highest-information next experiment: run the same frozen semantic DB IR on the Ubuntu target through (1) native typed host DB adapter and (2) Component Model/WIT resource backend. Require identical semantic hash, explicit backend/contract hashes, transaction/query/idempotency equivalence, dependency/capability epoch revalidation, stale/revoked-resource denial, unrelated-churn controls, savepoint/cancellation/resource-close behavior, crash/restart replay, no ambient filesystem/network authority outside grants, fuzz differential and resource/latency receipts.

Completed: canonical boot; current-stage grounding; nine-branch interconnect; concurrent-worker pulse; hypothesis/counterhypothesis research; primary-source triangulation; executable DB lowering proxy; 2,000-case differential; 1,000 adversarial mutations; crash/replay/resource-denial tests; Goodman review; negative results; micro-packet; branch feedback; durable report.

Not claimed: production parser, official local validators, E2B, exact Ubuntu target, production sandbox, second backend, DB_SERVICE PASS, BASE PASS or canonical scientific promotion.
