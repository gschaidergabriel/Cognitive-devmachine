# Clay 0.1 — Chief Developer First-Test Acceptance Contract

**Status:** PROJECT_OWNER_FIXED_TARGET
**Codename:** `DOOMSDAY`
**Target class:** internal chief-developer first-test candidate
**Not:** public release, production release, customer release, general availability

## 0. Meaning

DOOMSDAY is reached when the first complete Clay 0.1 system is ready for the **chief developer's first real internal hands-on test**.

Clay 0.1 at this point is:

`FRANK architecture authored in Clay`
`+ ClayCode semantics/runtime`
`+ one-module/binary-distilled executable architecture`
`+ UnifiedDB`
`+ final fully fine-tuned Clay-native model`
`+ real project-controlled hardware execution`
`+ complete observability/replay/recovery`
`+ passed internal acceptance suite`

This is not a public release milestone. The first chief-developer session begins *after* this gate passes and may discover new issues.

## 1. What "perfect" means operationally

Absolute bug-free perfection cannot be proven for a nontrivial software system. For this project, "perfect before the chief developer's first test" therefore has a strict operational definition:

- zero known `P0` or `P1` defects;
- zero knowingly skipped mandatory acceptance tests;
- zero unresolved architecture-contract violations;
- zero fake/mock implementation on a path that defines Clay 0.1 behavior;
- no silent fallback that changes Clay semantics;
- all mandatory differential tests pass;
- all mandatory state/receipt/provenance invariants pass;
- all mandatory UnifiedDB consistency/replay/recovery invariants pass;
- all mandatory effect/authority invariants pass;
- all mandatory GWT/Hyperposition readout instrumentation is present and self-consistent;
- fuzz/property/adversarial suites meet their frozen thresholds;
- crash/restart/replay tests meet their frozen thresholds;
- full model is actually loaded and participates in the real Clay 0.1 loop;
- end-to-end boot succeeds on project-controlled hardware;
- repeated clean boots produce contract-compatible state/receipt traces;
- known limitations are explicit and none invalidate the intended chief-developer test.

A test that has never been run is not a pass.

## 2. Required system identity

DOOMSDAY requires one integrated identity:

- architecture: current frozen FRANK Clay contract;
- language: frozen ClayCode version/hash;
- binary/runtime: exact build hash;
- UnifiedDB: exact schema/semantic-contract hash;
- model: exact base + fine-tune + merge/export hashes;
- training corpus: exact frozen hash set;
- held-out/eval set: exact frozen hash set;
- hardware/runtime environment: exact receipt;
- boot/run configuration: exact receipt.

Changing a defining component after acceptance invalidates the old acceptance identity and requires a new acceptance run.

## 3. Required acceptance families

### A — Architecture completeness

Every frozen FRANK logical subsystem and coupling is mapped to executable Clay/ClayCode behavior or an explicitly justified external boundary (e.g. owner-fixed Needle boundary).

### B — H1/H2/H3 differential continuity

The Reference Harness, ClayCode Harness and one-module/binary form must agree on all semantics that the contract declares representation-invariant.

Representation/placement differences are allowed only where explicitly non-semantic.

### C — State / UnifiedDB

Validate:

- state identity;
- epochs/versioning;
- transactions;
- query/result identity;
- replay;
- crash consistency;
- rebuild/rollback;
- stale-state rejection;
- provenance;
- ClayGraph/activation views;
- cross-timescale state.

### D — Model integration

The final fully fine-tuned model must:

- read/produce the frozen Clay representation at target quality;
- operate through the real architecture interfaces;
- preserve external authority boundaries;
- pass held-out semantic/conformance tests;
- survive long-horizon stateful tests;
- not rely on training-set leakage for acceptance.

### E — GWT / emergence observability

The executable system must expose the frozen functional readouts necessary to inspect:

- competition/selection;
- ignition/workspace episode;
- broadcast;
- reconstruction/uptake;
- causal use;
- outcome;
- re-entry;
- relevant higher-order/topological coupling;
- lesions/rescues/counterfactuals where defined.

These measurements support engineering/function claims only; they do not establish phenomenal consciousness.

### F — Safety / effect authority

Test capability non-forgeability, provenance/origin binding, cumulative budgets, stale/nonce/replay behavior, reservation/commit/outcome boundaries and destructive/admin/device effect gating.

### G — Robustness

Run required unit/property/fuzz/mutation/adversarial/race/concurrency/crash/recovery tests with frozen thresholds.

### H — Performance viability

The first developer build does not need public-release optimization, but it must be usable enough for meaningful chief-developer testing on project hardware. Record latency, RAM/VRAM, storage, state amplification, token/model costs where applicable and thermal/runtime constraints.

### I — Reproducible project-hardware boot

At least one project-controlled machine must execute the exact accepted Clay 0.1 identity end-to-end. Repeat boot/run sufficiently to rule out one-off initialization luck under the frozen acceptance protocol.

## 4. Severity gate

Before DOOMSDAY PASS:

- P0 open = forbidden;
- P1 open = forbidden;
- unresolved contract violation = forbidden;
- mandatory test `NOT_RUN` = forbidden;
- mandatory test `FAIL` = forbidden;
- P2/P3 may remain only when explicitly documented and demonstrated not to invalidate first chief-developer testing.

## 5. Acceptance artifacts

Required terminal artifacts:

- `CLAY_0_1_DEVELOPER_BUILD_MANIFEST.json`
- `CLAY_0_1_BINARY_BUILD_RECEIPT.json`
- `CLAY_0_1_UNIFIEDDB_RECEIPT.json`
- `CLAY_0_1_FINAL_MODEL_RECEIPT.json`
- `CLAY_0_1_HARNESS_DIFFERENTIAL_RECEIPT.json`
- `CLAY_0_1_FUZZ_ADVERSARIAL_RECEIPT.json`
- `CLAY_0_1_RECOVERY_RECEIPT.json`
- `CLAY_0_1_PROJECT_HARDWARE_BOOT_RECEIPT.json`
- `CLAY_0_1_CHIEF_DEVELOPER_ACCEPTANCE_RECEIPT.json`

## 6. Terminal condition

`DOOMSDAY = PASS` only when the chief-developer acceptance receipt says PASS for one exact Clay 0.1 identity and all required receipts resolve successfully.

At that moment the system is ready for the chief developer's first real test.

That first human developer test is **after DOOMSDAY**, not part of the pre-DOOMSDAY proof burden.

## 7. Post-DOOMSDAY

Issues found by the chief developer create the next development cycle. They do not retroactively mean the pre-test gate was dishonest if the gate correctly represented all evidence available at acceptance time.
