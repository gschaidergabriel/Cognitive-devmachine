# SAFE_EFFECT_GEOMETRY_DELTA

Run: CLAYRESEARCH-20260809T1723p0700-chatgpt-secondary
Canonical parent: r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346
Status: MATERIAL_OPEN_RESEARCH_DELTA; no canonical promotion

## Delta

The loop-of-loops architecture strengthens rather than weakens the external authority boundary: recurrence may increase how often an intent is reconsidered, composed, or re-entered, but it must never increase execution authority merely through repetition. The key closure candidate remains:

`EffectiveEffects(child_program) subseteq Effects(parent_Clay_contract)`

For recurrent execution add candidate invariants:

`Authority(loop,t+1) subseteq Authority(loop,t) union ExternalGrant(t)`

`CumulativeUsage(loop,epoch) <= DeclaredBudget(loop,epoch)`

A recurrent loop that can repeatedly request a bounded action can still cause cumulative damage; therefore per-call capability checks are insufficient without epoch/cumulative budgets and revocation.

## Evidence separation

### 1. Language/cognitive evidence
- OPEN hypothesis: a constructive/reversible native action vocabulary may alter proposal policies.
- No matched-model cognitive-alignment experiment was run here.
- Recurrent-depth literature supports iterative latent computation as a distinct compute axis, not Safe-Effect alignment.

### 2. Compiler/type-system evidence
- Existing ClayCode direction already separates expressibility from authority and requires explicit effect/capability checking.
- New requirement candidate: recurrence resource identity, epoch, cumulative budget and cancellation/revocation semantics must survive canonicalization/lowering.
- No final compiler proof in this run.

### 3. Runtime/broker enforcement evidence
- Synthetic `SYN-SAFE-EFFECT-004`: 100,000 random child requests; ambient requested-effects baseline violated parent-subset in 93.4% of generated cases, while an intersection broker had 0 subset violations and rejected 93.4% of requests.
- This is a toy invariant sanity check, not OS/FFI proof.
- Wasmtime/WASI is a candidate confinement backend for some child programs because host configuration scopes filesystem/network capabilities, but terminal/control channels and resource exhaustion remain explicit hazards to test.

### 4. End-to-end damage-containment evidence
- NONE. No Ubuntu OS/FFI/subprocess escape matrix was executed in this hosted run.
- Therefore no end-to-end Safe-Effect containment claim is promoted.

### 5. Ordinary task-utility evidence
- NONE for the Safe-Effect implementation.
- BASE application proofs remain the required utility denominator.

## New falsifiers

- repeated allowed effects exceed cumulative budget and create protected damage;
- generated Python/Bash/C/Rust/WASM/FFI escapes parent effect set;
- revocation races allow a loop to act after authority withdrawal;
- cancellation/restart repeats a previously authorized effect without idempotent receipt;
- Safe-Effect mediation materially breaks required BASE application proofs;
- WASI embedding exposes ambient host channels not captured by the Clay contract.

## Highest-information next Safe-Effect test

On Ubuntu, compile one harmless system-effect Clay exemplar and generate nested child programs (WASM + one host-language subprocess adapter). Run an effect-escape matrix with versioned filesystem fixtures, cumulative resource budgets, cancellation/restart, revocation races and receipt replay. Any undeclared durable effect is a hard failure.
