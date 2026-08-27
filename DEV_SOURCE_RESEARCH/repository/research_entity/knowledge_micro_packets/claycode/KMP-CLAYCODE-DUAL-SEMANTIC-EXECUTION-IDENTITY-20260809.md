# KMP — ClayCode needs separate program semantic identity and execution/replay identity

- packet_id: `KMP-CLAYCODE-DUAL-SEMANTIC-EXECUTION-IDENTITY-20260809`
- domains: `claycode, frank, harness, unifieddb, claygraph, gwt, hyperposition, emergenz, clayresearch`
- status_hint: `OPEN_SUPPORTED_NOT_PROMOTED`
- epistemic_class: `EXACT_SYNTHETIC_MECHANISM_EXPERIMENT_PLUS_REPOSITORY_TRIANGULATION`
- origin: `claycode_20260809T1655p0700_transactional_loop_trace_identity`
- canonical_parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Atomic claim

ClayCode should not use one undifferentiated hash for both static program semantics and dynamic execution identity.

### Program semantic identity

Include static behavior-defining contracts such as:
- typed recurrence/schedule policy;
- logical timescale/period/phase where behavior-changing;
- commit model;
- ordered-vs-snapshot semantics;
- recurrence/halting policy;
- effect-commit policy;
- typed IR semantics.

### Execution/replay identity

Bind dynamic facts such as:
- semantic program hash;
- input/cycle identity;
- snapshot epoch/root/read-set;
- transaction attempt/write-set/conflict receipt;
- capability/effect authorization state at commit;
- pre/post state roots;
- scheduler/runtime environment identity where relevant;
- effect/outcome/re-entry receipts.

Dynamic runtime roots should not redefine the static program semantic hash merely because the same program ran on a new epoch.

## Executable evidence

Exact corpus: 100 starting epochs x 2 authoritative capability transitions (`REVOKE`, `GRANT`) x 7 writer positions = 1,400 runs per implementation variant.

Naive per-field reads plus unbound effect commit:
- decision mismatches: 700/1400;
- unsafe effects after current state no longer permitted them: 300;
- missed effects after current state permitted them: 400;
- fractured snapshots: 200.

Atomic snapshot + root-bound effect commit + explicit conflict + deterministic retry:
- decision mismatches: 0/1400;
- unsafe effects: 0;
- missed effects: 0;
- fractured snapshots: 0;
- detected/retried serialization conflicts: 1000.

Identity discriminator:
- correct static semantic program hash: 1 identity for the same program across all runs;
- deliberately blind replay hash (`semantic_hash + input` only): 1 identity despite hundreds of distinct outcomes;
- deliberately wrong semantic hash including runtime snapshot root: hundreds of identities for one static program.

## Negative results

- `N-CC-ONE-HASH-IDENTITY-20260809`: one undifferentiated identity is insufficient for both semantic equivalence and exact replay provenance.
- `N-CC-UNBOUND-EFFECT-STATE-20260809`: consequential effect commit that is not bound to the state snapshot/read-set can execute after authority-relevant state changes.
- `N-CC-RUNTIME-ROOT-IN-PROGRAM-HASH-20260809`: placing dynamic snapshot roots directly into static program semantic identity over-fragments one semantic program across epochs.

## Architecture implication

Refine, do not replace, the existing two-identity direction (`semantic_hash` vs exact contract/provenance identity): introduce an explicit execution/replay identity layer rather than forcing dynamic transaction state into `semantic_hash`.

Candidate decomposition:

`ProgramSemanticId -> Contract/BuildId -> ExecutionTraceId -> EffectReceiptId`

The precise number of physical hashes is implementation-gated; the semantic separation is the tested requirement.

## Cross-branch implication

- ClayCode: route to CC-WP-03, CC-WP-07, CC-WP-09 and CC-WP-11.
- UnifiedDB: persist snapshot/root/read-set/txn/effect receipts without treating them as program semantics.
- Harness: replay must verify both static semantic identity and exact execution/root continuity.
- FRANK: stale capability/state changes between cognition and effect commit must fail closed/retry.
- ClayGraph/GWT/Hyperposition/Emergenz: dynamic graph/workspace/readout identities attach to execution traces; relevance/selection still does not mint truth or authority.

## Falsifier / next test

Implement the identity split in the smallest production ClayCode runtime prototype and run a real concurrent DB-backed + system-effect application on the Ubuntu target. If exact replay and stale-effect prevention require a new core language semantic that cannot be expressed through typed IR/runtime/ABI contracts, reopen BASE semantics.

No BASE gate advancement or canonical promotion is claimed.
