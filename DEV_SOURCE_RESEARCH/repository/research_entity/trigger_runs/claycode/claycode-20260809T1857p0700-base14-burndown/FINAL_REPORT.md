# ClayCode BASE14 blocker burndown — 2026-08-09

Actor: `chatgpt-secondary`  
Task: resolve the fourteen ClayCode BASE blockers with all available repository/runtime means, without fabricating target evidence.

## Executive result

The fourteen release work packages were attacked as one dependency cascade rather than fourteen independent tasks. The repository now has a substantially integrated executable path from V7 parsing/typed IR through pure/effect lowering, sealed mainline runtime, runtime hardening, concurrency/error checks, real Linux interactive I/O, target application receipts, strict target adjudication, evidence-gated promotion and a one-command Andreas-Ubuntu closure runner.

The official release workspace MUST remain receipt-gated. This run does **not** claim that all fourteen are officially PASS because the actual Andreas Ubuntu target was not available to this worker and the full stateful FRANK H1→H2/H3 handoff is still not implemented without a semantic escape hatch.

## High-information repairs made in this burndown

### Parser / front end

- Preserved the V7 operator-identity + typed-function front end as the current repair line.
- Added hosted BASE14/preflight integration so parser regressions are tested together with downstream runtime/concurrency/application prerequisites.
- Kept hosted/proxy evidence explicitly non-promoting.

### Typed IR / evaluator / lowering

- Used the integrated BASE pure compiler at `tools/claycode_base_compiler.py` as mainline.
- Preserved the prior fix that removed source/provenance contamination from semantic identity.
- Repaired the executable large-`Int` division counterexample:
  - removed float-mediated `int(left / right)` semantics;
  - reference evaluator now uses exact truncation toward zero;
  - generated C11 uses a checked, type-aware `cc_int_div` helper;
  - division by zero and `INT64_MIN / -1` have deterministic error boundaries rather than undefined behavior.
- Hardened `tools/claycode_int_division_regression.py` to test large values plus both evaluator and native-C error paths.

### Type/effect / authority / runtime

- Added an integrated typed effect pipeline over the V7 function representation.
- The effect reference evaluator and Python lowering now share the same checked `Int`-division semantics; statically `Real` division remains real division.
- Kept `tools/claycode_base_runtime.py` as the selected production-runtime candidate; alternate gateways/brokers remain adversarial crosschecks, not runtime forks.
- Added/retained executable discrimination for copied, forged, serialized, stale, revoked and wrong-runtime authority; origin/basis/selection/closure and cumulative-budget pressure remain explicit test dimensions.
- Converged the target collector on runtime-v0.4 hardening and compiler→mainline-runtime bridge discriminators.

### Stdlib / real application I/O

- Upgraded the interactive adapter from a list-fed state proxy to `ui.fd_interactive_event_loop`, using a real `AF_UNIX` socketpair plus `selectors.DefaultSelector` kernel-FD input/render loop.
- Retained the old in-process adapter only as a semantic oracle.
- Added a contract-shaped Andreas-Ubuntu ten-application runner. Nine classes have concrete execution paths; `FULL_FRANK_HANDOFF` is intentionally fail-closed until a genuine production handoff receipt exists.

### Target evidence / WP14 closure wiring

- Hardened the canonical V2 Andreas-Ubuntu evidence collector with:
  - strict/front-end/canonicalizer;
  - typed IR;
  - pure native differential;
  - checked large-Int division;
  - type/effect pipeline;
  - package link;
  - runtime;
  - runtime-v0.4 hardening;
  - compiler→mainline-runtime bridge;
  - cancellation/error semantics;
  - fuzz/corpus;
  - FRANK component differential.
- Re-aligned strict adjudication to the current `ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json` instead of an older receipt schema.
- Added one evidence-gated promotion writer:
  - `preaudit` may promote WP02–WP13 only from the strict target receipt;
  - `finalize` may promote WP14 and release gates only after a passing release audit and generated manifest.
- Added `tools/claycode_close14_on_andreas_ubuntu.py` as the one-command fail-closed closure chain:
  1. V2 target component collector;
  2. real ten-application target suite;
  3. strict target adjudication;
  4. WP02–WP13 evidence promotion;
  5. WP14 release audit;
  6. final WP14/gate promotion.

## Negative results / blockers that remain real

### Actual Andreas Ubuntu evidence is absent in this worker

This session has repository write access but no execution channel into Andreas' physical Ubuntu developer system. Therefore no target-host receipt was fabricated and no proxy/CI receipt was treated as target acceptance.

### FULL_FRANK_HANDOFF is not yet legitimately closed

The frozen H1 ActiveAssembly reference requires the full deterministic mechanism, including:

- semantic-epoch filtering;
- packet-identity collision rejection;
- deterministic scoring/ranking;
- ancestry-family diversity caps;
- explicit conflict-representative retention;
- item and context budgets;
- omitted/re-expansion provenance;
- deterministic assembly hashing;
- fail-closed authority-mint rejection.

Current FRANK ClayCode evidence covers real subsystems (including score/GRT paths) but not the complete stateful H1→H2/H3 behavior. The existing block compiler also fails closed on the generic collection/control-flow semantics needed to express the entire mechanism. Replacing the missing logic with a FRANK-specific Python/FFI host call would be a semantic escape hatch and is explicitly NOT accepted.

This is the remaining architecture/compiler gap to solve before the full target closure chain can turn green.

## Current closure law

Do not manually change the release workspace to PASS.

A legitimate 14/14 close now has one route:

```text
owner-registered Andreas Ubuntu target
  -> V2 target component collector PASS
  -> 10 real target applications PASS
  -> full stateful FRANK H1→H2/H3 receipt PASS
  -> strict target adjudication PASS
  -> evidence-gated WP02–WP13 promotion
  -> WP14 release audit PASS + manifest
  -> evidence-gated WP14/final gate promotion
```

Any hosted/proxy shortcut must remain non-promoting.

## Next discriminating implementation task

Implement only the generic ClayCode mechanisms required to express the complete H1 ActiveAssembly in ClayCode itself (collections/maps/sets, deterministic iteration/sort, loop/control flow and generic canonical data operations), then differential-test the ClayCode implementation against `research_entity/harness/reference/active_assembly.py` across randomized valid cases and all fail-closed negative paths. Once that is green, run the one-command closure chain on the registered Andreas Ubuntu host.
