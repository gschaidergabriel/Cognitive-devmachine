# CM-IO Hostcall ABI Fusion Adjudication — 2026-08-17

Program: `CLAYVERSE_CLAY_MACHINE_ONLY` / `CLAY_MACHINE`  
Product boundary: exactly one executable `EntityOS`  
Trigger: `go`  
Execution class: source inspection + architecture adjudication + durable coordination only. No new unusual experiment was introduced or executed by this work item.

## Exact observed anchors

- Research base refreshed immediately before this restacked write: `dff48f8dc1fee70719abdb3f1fa2ece5210d5f09`.
- Product `main`: `6012d2cf4125e65d3a0c2df8d3b37119ae4f7b47`.
- Active EntityOS draft PR #787 was refreshed to `fa7ca80b668b1cf59b48f2b314c046b3a4c772f2` during adjudication. Its exact-head executable state remains unresolved for descendants of the previously verified `92b629566452d8f45fd208fba943b823ddd37e8c` scope.
- The user-triggered GO unusual-experiment budget is already consumed `1/1` by `ATTESTED_SNAPSHOT_CONTENT_TAMPER_FAIL_CLOSED` on `92b62956...`. All work below is ordinary regression/discrimination only; `new_unusual_experiment_count=0`.
- Prior research receipt on `dff48f8d...` selected PR #793 over an earlier weaker duplicate and preserved the exact-head Vercel build-rate-limit negative result. This new adjudication is a later comparison that also includes subsequently observed clean PR #795; it does not erase the earlier receipt or its negative evidence.
- The latest independently inspected non-target Vercel preview at stale product head `ef5bed69c534b79c1a33e692dcf488408b7f01b3` staged exact source successfully but explicitly returned `SKIP_NON_TARGET_PREVIEW` for both full pytest and canonical v7. That READY preview is not Sandbox execution evidence.

## Problem restated

The active ClayVM/ExecutableIR path duplicated hostcall ABI authority: lowering held capability/signature/parameter/result information while the VM/host path independently mapped IDs/capabilities/handlers and historically applied a global Int-only hostcall check. This permits semantic drift and blocks a principled typed Bytes host boundary.

The accepted architectural objective is one neutral machine-ABI authority shared by lowering and runtime. Source/type/effect semantics remain upstream authority; the ABI registry may encode only admitted machine-boundary contracts and must fail closed on disagreement.

## Parallel candidate adjudication

### Candidate A — `clay/go-hostcall-abi-registry-20260817` @ `b5973bcc...`

Observed: adds a registry and small capability-source cleanup, but does not yet make both lowering and VM enforce the one authority.

Outcome: **DEFER / INCOMPLETE**. Useful seed only; not the fusion target.

### Candidate B — `chatgpt/go-hostcall-abi-registry-20260817` @ `84b90507...`

Observed strengths:
- clean `ClayHostcallABI/v1` production contracts only;
- lowering resolves source-admitted capability/signature/effect/type information from the registry;
- runtime resolves the same call contract, validates argument/result Clay types and rejects capability-binding mismatch;
- removes global Int-only hostcall transport without inventing a real Bytes product effect.

Observed weakness:
- no explicit `(ClayVM format version, call_id)` contract binding or serialized-module unknown-ID/arity validation in the inspected delta.

Outcome: **RETAIN AS PRODUCT-PURITY BASELINE**.

### Candidate C — `clay/go-hostcall-abi-bytes-20260817` @ `5a73ad56...`

Observed strengths:
- executable typed Bytes hostcall roundtrip discriminator;
- useful negative cases for mutable Bytes, wrong host result type, capability mismatch and signature drift;
- VM static hostcall-ID/arity validation.

Observed weakness:
- registers `clay.test.bytes.echo.v0::(Bytes)->Bytes` as an ExecutableIR-admitted contract in the canonical registry. A test discriminator thereby becomes normal source/product semantic surface.

Outcome: **REJECT AS CANONICAL IMPLEMENTATION; HARVEST TEST OBLIGATIONS ONLY**.

### Candidate D / PR #793 — `clay/go-hostcall-abi-v1-20260817` @ refreshed PR head `a5fec10e479da4ddd31450b109ff36533ba23ec3`

Observed strengths:
- immutable/versioned hostcall registry;
- explicit stable `call_id` binding to ClayVM format versions;
- serialized module validation rejects unknown ABI IDs and arity mismatches before execution;
- host implementations register handlers only; capability/type identity is not duplicated in the backend;
- runtime resolves the contract using the module format version and normalizes typed args/results;
- deterministic Bytes transport falsifiers exist;
- diagnostic Bytes contract is excluded from normal lowering by default.

Observed residual concern:
- the diagnostic Bytes contract still exists in the shipped canonical registry/VM-recognized ID space when this branch is taken as-is. That is acceptable as bounded research evidence, but it should not silently become release semantic authority merely because it is useful for testing.

Outcome: **RETAIN AS VERSIONING/STATIC-VALIDATION DONOR, NOT CANONICAL AS-IS**.

### Candidate E / PR #795 — `chatgpt/go-hostcall-abi-registry-v2-20260817` @ `2998a88f54fc1abc0a0520126a7e4b4d273dd00d`

Observed strengths:
- clean product-neutral registry containing only existing admitted uname/process contracts;
- no new Bytes product effect;
- shared lowering/runtime ABI authority;
- deterministic no-real-effect regression gate;
- stacked on active #787 and mergeable when inspected.

Observed weakness versus D:
- current inspected registry is not yet keyed by ClayVM format version and the VM does not yet carry D's strongest load-time unknown-ID/arity validation.

Outcome: **PREFERRED CANONICAL FUSION LANE, WITH REQUIRED D-DERIVED HARDENING BEFORE PROMOTION**.

## Fused target architecture

Promote one implementation only, using PR #795 as the clean lane and importing the following invariants from PR #793 without importing a test-only product contract:

1. `ClayHostcallABI/v1` is the single machine-boundary contract authority used by lowering, serialized VM validation and runtime host invocation.
2. Stable `call_id` is interpreted under an explicit ClayVM format version; incompatible rebinding under the same `(version, id)` fails closed.
3. Emitted/loaded serialized ClayVM rejects unknown hostcall IDs and exact arity mismatch before execution.
4. Host adapters register handler functions only. They do not carry an independent capability/type signature.
5. Runtime normalizes exact ABI parameter types before handler invocation and exact ABI result type before Clay re-entry.
6. Capability denial remains independent of payload representation and occurs before the external effect.
7. Normal/release lowering contains no diagnostic/test Bytes hostcall contract. Bytes transport falsifiers may be implemented through a strictly test-scoped mechanism that cannot become release/source authority.
8. No real product Bytes effect is admitted until its source/type/effect contract is explicit. Buffer lease/epoch/streaming/backpressure remains a later high-bandwidth frontier.

## Strongest counterhypotheses and required falsifiers

### Counterhypothesis 1 — registry becomes a second semantic authority
Falsifier: construct TypedIR/source identity that disagrees with the ABI record. It must fail before VM effect execution; no host adapter may override the mismatch.

### Counterhypothesis 2 — stable call_id silently changes meaning across VM revisions
Falsifier: compatibility fixture with an incompatible `(version, id)` rebind must fail at load/validation rather than reinterpret old bytecode.

### Counterhypothesis 3 — generic ClayValue widening leaks mutable/borrowed Bytes or wrong host results
Falsifiers: mutable/borrowed Bytes must fail at the existing epoch/ownership fence before handler invocation; wrong handler return type must trap before the value re-enters Clay state.

### Counterhypothesis 4 — test machinery becomes product semantics
Falsifier: normal/release lowering and default runtime registry must not expose a test-only Bytes capability/signature as an admitted product effect.

## Durable coordination performed

- Review on PR #795 directs fusion of #793's VM-format/static-validation invariants into #795 while retaining #795's product-neutral contract set.
- Review on PR #793 marks it as a donor for versioning/static-validation/Bytes falsifier ideas rather than the canonical merge lane as-is.
- No competing eighth product implementation branch was created after duplicate hostcall branches were discovered.
- An initial research branch created from older `ef91bdba...` was not forced onto moving `main`; after `main` advanced to `dff48f8d...`, this receipt was restacked on that newer exact base instead.

## Executable truth / promotion state

**SOURCE-STAGED / EXECUTION UNVERIFIED.** No executable PASS is claimed for PR #793, PR #795, the current #787 descendant, or any fused future head.

Promotion requires an actually-started exact-head Vercel Sandbox after the fused code is on the target lineage. One coordinated regression-only batch should capture exact source SHA, commands, exit codes/logs and Sandbox stop and require at minimum:

- canonical hostcall ABI gate and the four counterhypothesis falsifiers above;
- adjacent hostcall-signature, VM-process, single-VM and owned-Bytes regressions;
- ordinary full pytest with nonzero tests, zero skips where required and `new_unusual_experiment_count=0`;
- canonical v7 exact-source Git-free attested twin `EntityOS` build;
- byte-identical twins, runtime/self-test, no-host-Python and relocation under existing deny-all policy;
- exact artifact digest and durable result receipt;
- successful Sandbox stop.

A deployment READY state, source inspection, branch mergeability or historical exact-head PASS does not substitute for this execution.

## EntityOS convergence result

This adjudication removes ambiguity about the next canonical code shape and prevents parallel ABI semantics from proliferating. It does **not** close CM-DATA/NET/VIS/AUDIO Bytes transport and does **not** establish whole-machine acceptance.

Next highest-information executable step: fuse the D-derived version/load-time invariants into PR #795's clean product-neutral lane, rebase/stack on the then-current #787 exact head, and run the coordinated exact-head Vercel Sandbox regression batch with zero new unusual experiments.
