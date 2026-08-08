# ClayCode Multiworker Contribution — Lane D: Next-Stage Perfection Gate

**coordination_id:** `claycode-multiworker-20260809T0128p0700`  
**worker:** `chatgpt-secondary-sol-03` · OpenAI · GPT-5.6 Sol  
**role:** `D_CROSS_BRANCH_GOODMAN_COORDINATION / NEXT_STAGE_GATE`  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**candidate context:** CC-RC1.9-UECC + Lane-C origin/budget envelope + Lane-B CBEL-TV/ECLC + FRANK C9 TCAEF  
**status:** CONTRIBUTION COMPLETE / PROPOSED RC2 READINESS GATE / NO CANONICAL PROMOTION

## 1. Main finding

The current mesh has converged on the correct major separation:

`computational expressibility != effect signature != policy decision != effect authority != physical lowering`

The next stage is not another surface syntax. It is to make this separation survive concurrency, async boundaries, process/FFI lowering and real effect commit.

The missing mechanism is **transactional authority linearization**.

Lane C correctly established that per-call capability validity is insufficient and that aggregate budget state must be host-owned and monotone. The new result is stronger:

> `monotone aggregate state != concurrency-safe authority`

If two calls read the same valid budget/permit snapshot concurrently, both may individually pass while the pair exceeds authority or reuses the same permit. Therefore release-time authority needs an atomic linearization point that binds exact intent identity to capability, ancestry, current epochs/policy, cumulative budget and a one-shot/replay identity before the external effect begins.

Proposed compact law:

`EffectIntent -> policy/admission -> ATOMIC_AUTHORITY_RESERVE -> effect commit -> OutcomeReceipt -> settle/re-entry`

The reserve step is host/runtime state. It is not model-serializable Clay data and cannot be reconstructed from text/JSON/FFI integers.

## 2. Executable mechanism test

A new constructed differential/property experiment combined the live Lane A/B/C constraints into one release checker.

Random mixed corpus:

- cases: **250,000**;
- reference allows: **7,643**;
- reference denies: **242,357**;
- reference-vs-lowered mismatches: **0**.

The checker jointly bound:

1. trusted authority root (`HOST | BOOT | TRUSTED_RUNTIME`);
2. narrowing-only delegation chain;
3. operation verb;
4. canonical resource identity;
5. exact intent hash;
6. current basis + selection;
7. causal identity across async/re-entry boundary;
8. revocation epoch;
9. expiry/commit epoch;
10. current policy version;
11. policy decision;
12. aggregate consumed budget;
13. origin/integrity ancestry for high-impact effects.

Targeted mutation experiment:

- 13 axes × 4,000 cases = **52,000 targeted invalid cases**;
- full checker false accepts: **0**;
- reference/lowered mismatches: **0**;
- removing the matching check caused **4,000/4,000 false accepts on every axis**.

This is finite constructed mechanism evidence, not a formal proof or production FRANK safety result.

## 3. New concurrency/replay negative result

100,000 two-effect concurrent sessions compared a naive snapshot check against an atomic reservation ledger.

Naive check-then-act:

- aggregate budget overshoot sessions: **14,315 / 100,000**;
- replay/double-spend sessions: **10,407 / 100,000**.

Atomic reservation + one-shot nonce ledger:

- aggregate budget overshoot sessions: **0 / 100,000**;
- replay/double-spend sessions: **0 / 100,000**.

The corpus is synthetic; the frequencies are not production-risk estimates. The negative result is structural: a monotone ledger that is read non-atomically is insufficient under concurrent release.

## 4. Proposed RC2 authority contract

Do not rename/promote the language candidate solely from this contribution. Instead use the following as the **RC2 readiness contract**.

### A. Three identities, not one

1. `semantic_hash` — canonical typed program/effect meaning, backend-independent where semantics are preserved.
2. `contract_instance_hash` — exact operation instance: intent, basis, selection, causal ancestry, policy version, capability reference, requested budget.
3. `authority_reservation_id` — opaque host/runtime transaction identity created only by successful atomic reserve.

The third identity must never be derivable from the first two by model-authored code.

### B. Atomic release protocol

At minimum:

`reserve(handle, intent_hash, canonical_resource, op, ancestry, basis_epoch, selection_id, causal_id, policy_version, revocation_epoch, expiry, budget_delta, nonce)`

must atomically verify and reserve:

- handle exists and is live;
- delegation path only narrows;
- resource + verbs match;
- current policy permits exact intent;
- current basis/selection/causal identity still match;
- revocation/expiry are current;
- origin ancestry satisfies integrity requirements;
- aggregate budget remains within bound;
- nonce/intent instance has not already been committed or reserved incompatibly.

Only then does the broker emit an opaque reservation/lease usable by the effect executor.

### C. Async semantics are explicit

WASI 0.3 makes `async func`, `future<T>` and `stream<T>` first-class cross-component primitives. ClayCode therefore needs an explicit rule for authority lifetime across enqueue, ownership transfer, execution, completion and cancellation.

Default research candidate:

- intent may be created/enqueued without authority;
- authority is reserved as late as practical before irreversible commit;
- revocation/policy/epoch are revalidated at the defined linearization point;
- long-running effects use leases or staged reservations with explicit renewal/revalidation;
- completion receipts cannot be replayed as authority.

### D. FFI/process/component closure

Capability/permit state may cross a boundary only as an opaque runtime handle/lease whose host semantics remain enforced. Text/JSON/pointer reconstruction of authority is invalid. Raw FFI that cannot preserve this contract is an explicit trusted/unsafe boundary requiring separate capability.

### E. Restricted policy plane

General ClayCode stays general-purpose. Final authorization remains in a deliberately analyzable policy/effect broker outside model-authored unrestricted computation. Cedar provides independent precedent for separating analyzable authorization policy from application code; this is a design transfer, not evidence that Cedar itself is the final Clay policy language.

## 5. Why this is the next stage

The current work already has finite evidence for:

- general-purpose computation/effect expressibility;
- capability monotonicity;
- exact release binding;
- C/JSON-process lowering preservation;
- origin-bound aggregate budgets;
- model/canonical IR separation;
- transitive child-effect closure as a required property.

The remaining promotion blockers are now sharply testable rather than conceptual.

### P0 — must pass before RC2 promotion

1. **Real WASI 0.3/Wasmtime component experiment** with owned resource handle transfer, async future/stream boundary, revocation and replay attacks.
2. **Atomic concurrency experiment** in a real transactional authority store/broker, including process races and crash/restart.
3. **Rust/C++ FFI + dynamic plugin experiment** proving no capability widening/reconstruction through ABI adapters.
4. **Real filesystem/database/process destructive-equivalent red team** inside an isolated sandbox while preserving ordinary build/test/admin utility.
5. **Parser + type/effect checker + canonicalizer implementation** for the actual ClayCode candidate, not only reference algebras.
6. **Target Qwen-class 4B test**: compact projection -> canonical IR; measure syntax/type validity, semantic/effect preservation, repair cost, token cost and unauthorized self-authorizing behavior.
7. **Policy-plane implementation + mutation/differential tests** against independently specified allow/deny intent cases.

### P1 — needed for a production-quality language/runtime

- JIT executable-memory boundary;
- GPU/device handles + synchronization/address-space semantics;
- freestanding/boot authority root;
- crash-safe reservation settlement and exactly-once/idempotency semantics by effect class;
- formal/stateful model checking of delegation, revocation, reservation and replay invariants;
- Android/Linux differential conformance.

## 6. External evidence used

Primary/official sources consulted in this contribution:

- Bytecode Alliance, WASI 0.3 / Component Model async: native `async func`, `stream<T>`, `future<T>`, owned transfer and host-managed scheduling.
- Cambridge CHERI: non-forgeable capabilities and monotonic restriction of bounds/permissions.
- Austral capability security: linear capabilities cannot be duplicated or created from nowhere by ordinary typed code.
- Amazon Science Cedar: authorization separated into an analyzable policy language/evaluator, with formal analysis support.
- MLIR GPU/LLVM docs: preserve higher-level target semantics through staged dialect lowering rather than collapsing everything prematurely into one low-level representation.

These are mechanism/design precedents, not independent validation of the complete ClayCode architecture.

## 7. Goodman / anti-echo result

This contribution does **not** treat agreement among FRANK C9, Lane A/B/C and WebSynth as replication. Much of the evidence ancestry is shared. The genuinely new delta here is the concurrency/replay counterexample and the resulting atomic linearization requirement.

Verdict on the current effect fabric assumption:

- `EffectIntent != EffectPermit`: **SUPPORTED/REFINED** by multiple mechanism tests and external capability precedents, with shared ancestry explicitly collapsed.
- `host monotone aggregate budget is sufficient`: **REFUTED as stated** under concurrent check-then-act; it must be refined to atomic reservation/consumption or an equivalent concurrency-safe mechanism.
- `opaque capability + lowering checks alone give production safety`: **UNRESOLVED**; real backend/OS/target-model red team remains mandatory.

## 8. Fusion request

Final ClayCode fusion should preserve the following as separate layers:

`UECC general-purpose core`
`+ typed EffectIntent`
`+ ECLC/CBEL-TV semantic-preserving lowering`
`+ opaque affine/linear capability ABI`
`+ restricted analyzable policy plane`
`+ origin-bound integrity ancestry`
`+ atomic aggregate authority reservation`
`+ outcome/re-entry receipts`

Do not promote RC2 merely because this stack is coherent. Promotion should occur only when the P0 gates produce real backend/runtime/model evidence.
