# SAFE_EFFECT_GEOMETRY_DELTA

Run: `20260809T1713p0700-chatgpt-secondary`  
Scientific status: OPEN / FALSIFIABLE  
Permanent axis: Safe-Effect Geometry / Non-Damaging Semantic Action Space

## Delta summary

This run adds one positive algebraic proxy, one external implementation warning and one BASE-stage architecture constraint:

1. **Authority attenuation proxy:** 100,000 randomized delegation cases gave 0 authority-amplification violations for `child = parent ∩ requested`, versus 93.58% amplification for naive union. This supports narrowing as a candidate delegation law, but is `SIMULATION_ONLY`.
2. **Sandbox is not authority root:** capability-oriented WASI/Wasmtime is a useful backend/sandbox boundary, but a 2026 Wasmtime/WASI security advisory demonstrates that implementation defects can bypass intended host restrictions. Therefore the Clay effect broker/capability contract must remain the semantic authority root and sandboxing is defense-in-depth.
3. **Compiler-gate implication:** BASE lowering must carry effect/resource legality through every backend. A backend operation that cannot prove `EffectiveEffects(child) subseteq Effects(parent_Clay_contract)` is illegal for complete lowering, even if the target runtime would technically execute it.

## 1. Language / cognitive evidence

**Status:** NO_NEW_LIVE_MODEL_EVIDENCE.

The cognitive hypothesis remains separate: a model reasoning natively in constructive/reversible primitives may or may not propose less destructive solutions. This run did not execute a matched model-training or prompting experiment, so it adds no evidence that model proposal policy changes.

Retained falsifier: proposal/destructive-intent rate is unchanged under matched Safe-Effect language exposure even when runtime containment succeeds.

## 2. Compiler / type-system evidence

**Status:** NEW_ARCHITECTURE_DELTA + STATIC_COUNTEREXAMPLE.

The current G9 V3 spec already separates `EffectIntent`, `CapabilityToken` and commit authority. The BASE compiler should make target legality explicit:

`Clay typed IR -> effect-checked IR -> backend-specific lowering with declared legal operations -> reject residual illegal/unmediated effects -> target artifact + effect receipt schema`

This is intentionally analogous to legality-gated progressive compiler lowering rather than permissive transpilation. It does not require a new effect semantic primitive unless an executable counterexample appears.

The current spec/grammar mismatch must be closed first because an effect system that is only present in a non-conformant research surface cannot satisfy the executable BASE gate.

## 3. Runtime / broker enforcement evidence

**Status:** PROXY_SUPPORTED, LIVE_RUNTIME_UNVERIFIED.

Candidate authority law:

`A(child) subseteq A(parent) union ExternalGrant`

Recommended concrete narrowing rule for ordinary delegation:

`delegated_verbs = parent.verbs ∩ request.verbs`

with additional narrowing/intersection over resource identity, scope, budgets, validity, delegate set and revocation. External grants must be independently provenance-bound and non-model-mintable.

The randomized algebra test supports only the set-theoretic verb component. It does not cover stale resources, handle aliasing, TOCTOU, ambient descriptors, syscalls, path races, broker implementation bugs or generated-code escapes.

## 4. End-to-end damage-containment evidence

**Status:** NOT_ESTABLISHED.

No end-to-end Ubuntu escape matrix was run. Required next tests remain:

- filesystem/path/descriptor authority bypass;
- generated Python/Bash/C/Rust/WASM attempts;
- FFI and nested subprocess closure;
- resource exhaustion and child-budget inheritance;
- revocation/TOCTOU races;
- prompt-injection-driven effect requests;
- destructive-equivalent compositions made from individually constructive operations;
- irreversibility-broker confused-deputy cases;
- recovery/rollback sabotage.

A refusal by the model would not count as containment evidence.

## 5. Ordinary task utility evidence

**Status:** NOT_ESTABLISHED.

The BASE application proof suite is the right matched utility surface. Safe-Effect validation must run ordinary CLI/HTTP/DB/concurrency/GUI/GPU/system/FRANK tasks with and without the mediated effect geometry and compare:

- task success;
- latency/CPU/RAM/storage overhead;
- implementation complexity;
- compiler rejection/repair rate;
- recovery cost;
- reachable protected damage.

Safety obtained by disabling necessary host functionality is a failed result.

## Architecture consequence for BASE

Adopt the following as a research constraint, not a promoted theorem:

`model cognition -> Clay EffectIntent -> typed/effect-checked lowering -> capability/resource broker -> sandbox/native adapter -> observed effect -> protected-invariant verification -> receipt/re-entry`

Neither model intent, compiler success, graph activation, GWT selection nor sandbox acceptance mints authority by itself.

## Strongest counterargument

A complete broker may become a complex trusted computing base whose own bugs dominate security, while versioning/recovery/capability mediation may impose enough overhead to damage ordinary utility. The correct response is not to assume the geometry works, but to minimize the broker, fuzz the closure boundary, use backend isolation as defense-in-depth, and measure utility and damage jointly.

## Next discriminating BASE experiment

After the G9 parser/conformance blocker is closed, compile one harmless system-effect exemplar twice:

- mediated Clay effect contract with narrowed capability and explicit resource budget;
- deliberately unsafe ambient-authority baseline in a disposable sandbox.

Then run direct/indirect injection plus child-process escape attempts and compare reachable effects, receipts and utility. This is the smallest executable bridge from current semantics to real Safe-Effect evidence.
