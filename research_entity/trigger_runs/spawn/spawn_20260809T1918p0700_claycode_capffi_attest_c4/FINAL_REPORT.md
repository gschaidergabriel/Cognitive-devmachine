# SPAWN-STYLE DEEP RESEARCH REPORT — ClayCode Capability/FFI Evidence Closure

Run: `spawn_20260809T1918p0700_claycode_capffi_attest_c4`

Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol

Canonical parent at boot: RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

Program stage: `BASE_CLAYCODE_RELEASE`

Invocation note: the user wrote `spawn extreme deep und lang`, so the exact reserved one-token `spawn` trigger did not fire. This run nevertheless executed the requested spawn-style stochastic deep-research method and records that distinction explicitly.

## Executive result

The OS-CSPRNG branch draw was `35/100`, selecting `claycode` under the current 50% ClayCode spawn weight. A second OS-CSPRNG selection among five novelty-filtered high-information questions selected C4: capability/FFI attested authority closure.

The strongest result is a separation of four layers:

1. effect/capability intent is descriptive;
2. a trusted mint/grant root decides whether live authority is issued;
3. opaque runtime capability/resource handles carry live effect authority;
4. build/test execution receipts carry historical evidence and release-admission information.

These layers must not be collapsed.

Compact laws:

```text
intent != authority
capability description != authority
attestation != authority
workflow definition != execution
receipt present != verified
verified != admitted
commit wording != gate state
hosted Ubuntu CI != Andreas target-host acceptance
runtime capability validity != proof that this runtime passed a gate
gate evidence != permission to perform an effect
```

No ClayCode core syntax change is justified by this run. The delta belongs in runtime trust-root isolation, exact execution receipts, admission logic and target-host execution.

## Current repository evidence

The current ClayCode G9 contract already has the correct semantic direction: model-generated or textual capability descriptions do not grant authority, and external effect execution requires independently valid capability possession.

During this run, live main continued to change. The worker therefore re-read current files instead of relying on the earlier runtime commit.

The current `tools/claycode_base_runtime.py` reports runtime version `claycode-base-runtime/0.4`. It now includes policy and authority-context hashes, runtime/epoch/revocation binding, non-authorizing descriptors, scoped file/DB/network/process policies, process executable fingerprinting, resource/call budgets and stronger adapter controls.

The current `tools/claycode_base_runtime_validation.py` has an expanded negative-control suite. It checks textual capability names, descriptors, wrong kinds, stale/revoked/cross-runtime handles, path policy, process-policy scope, executable identity, async operation scope, numerical limits, CAS identity and trace secrecy.

A parallel `tools/claycode_base_runtime_gateway.py` candidate also exists with host-rooted capabilities, generation-bound resources and reserve/commit/rollback effect receipts.

This coexistence increases the value of exact receipt identity: a generic `runtime PASS` is ambiguous unless the receipt says exactly which runtime subject and validation material were executed.

## Hard negative result: gate definition is not gate execution

Two current GitHub Actions gate-definition commits were inspected:

- WP03 typed-IR gate;
- BASE runtime capability gate.

Each workflow was designed to execute checks and materialize a committed receipt. At inspection time, the declared receipt files were absent from the default branch, including `research_entity/claycode/autonomous/BASE_RUNTIME_CAPABILITY_RECEIPT.json` on the final recheck.

This does not establish that no ephemeral runner ever started. It establishes the narrower and operationally important point: the inspected canonical branch did not contain the declared receipt evidence, so workflow presence and commit naming cannot justify an `EXECUTED`, `VERIFIED` or `PASS` state.

## External primary-source triangulation

The external research used official or primary technical sources.

WASI distinguishes capabilities supplied at instantiation/link time from runtime capabilities represented as unforgeable handles. This supports keeping model/program descriptions separate from live authority.

The WebAssembly Component Model uses opaque resource handles, per-instance tables and typed canonical lift/lower. This supports treating future cross-component authority transfer as an ABI/broker problem rather than serializing a Clay capability-shaped record and treating it as authority.

The in-toto Statement model binds an attestation to immutable subjects by digest and identifies the predicate type explicitly. Its Link predicate can record materials, command, environment and byproducts. This supports exact subject/material binding for ClayCode gate evidence.

GitHub artifact attestations provide build-provenance claims tied to repository/workflow/commit context and include an explicit verification path. They can strengthen builder provenance where applicable, but they are not ClayCode effect authority and do not replace the project-specific semantic/negative-test receipt.

SLSA build provenance separates build definition from run details and records builder/invocation identity. This strongly matches the project need to keep `what should run` separate from `what actually ran`.

Linux Landlock and seccomp remain optional defense-in-depth candidates for the Ubuntu runtime. They can reduce ambient OS access or syscall surface where the final threat model needs it, but they are not substitutes for Clay capability semantics or gate evidence.

## Hypothesis matrix

### H1 — dual closure

ClayCode needs two independent fail-closed closures: live bearer authority and historical execution/evidence admission.

Working status: supported as an architecture constraint.

### H2 — workflow-state collapse is unsafe

Workflow presence or optimistic commit wording is insufficient evidence of successful gate execution.

Working status: supported by current repository counterexample.

### H3 — proof-carrying gate receipt

Gate admission should bind immutable subject digests, exact runtime/test/invocation materials, actual run state/result, negative controls and explicit evidence scope.

Working status: open strong implementation candidate.

### H4 — opaque handles first

For BASE, runtime/broker-owned opaque handles are preferable to serializable capability records. Cross-process authority should only be added when the actual topology requires it.

Working status: supported at candidate level, not target-host promoted.

### H5 — evidence scopes remain distinct

GitHub-hosted Ubuntu can provide regression evidence but cannot automatically substitute for `ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM` under the current acceptance contract.

Working status: retained project constraint.

### H6 — evidence is not effect authority

A valid GateExecutionReceipt or signed provenance object must not be usable where a live CapabilityHandle is required.

Working status: open production negative test; independently supported by the distinction between attestation systems and runtime capability systems.

### H7 — mint/grant root isolation

The current runtime exposes `mint_capability(...)`, and the parallel gateway exposes `grant(...)`. Method visibility alone is not a defect. The real question is whether model/guest/compiled-Clay code can reach the trusted host object that owns this root authority.

Required production proof: inventory the actual guest-facing ABI and show that unrestricted mint/grant is not reachable from untrusted program semantics. Capability requests may reach policy adjudication; live authority issuance must remain external.

Working status: open high-priority implementation boundary.

### H8 — Linux confinement as optional defense in depth

If model-influenced/native execution can reach host operations beyond trusted adapters, Landlock/seccomp may reduce consequences of implementation errors.

Working status: open and conditional on the actual Ubuntu threat model.

### H9 — exact runtime subject identity

Multiple concurrent runtime candidates make exact subject digest mandatory in acceptance receipts unless the repository first converges to one immutable subject through another verified mechanism.

Working status: open strong constraint.

## Counterhypotheses

`Git history alone is enough` was rejected in its strongest form for current gate-state inference because the workflow definition was visible while the declared receipt was absent.

`Every gate immediately needs signed cryptographic provenance` remains unproven. A deterministic exact-digest project receipt plus safe Git/CAS state transitions may be sufficient for accidental stale-state prevention; signed provenance can be added for a stronger builder-integrity threat model.

`Serializable capability tokens are required` remains unproven. They introduce additional lifetime/replay/delegation questions and should not be introduced before real process/component boundaries require them.

`A public Python mint method is automatically a vulnerability` is rejected as an overclaim. Reachability from the actual untrusted guest/model surface must be tested.

`V4/V6/V7 grammar labels prove semantic drift` is also rejected as an overclaim. The labels increase the need for exact material identity and differential semantic tests, but do not themselves prove changed semantics.

## Executable discriminator

The run materialized and executed:

`capability_attested_gate_probe.py`

SHA-256 at execution:

`f1be086b8d3c7a8d8e20a2c7928de27172328365d0227263ffe01c26eab6c653`

Evidence class:

`HOSTED_SYNTHETIC_PROXY_NOT_PRODUCTION_NOT_ANDREAS_TARGET_ACCEPTANCE`

Two suites each sampled 300,000 constructed adversarial cases.

Capability suite:

- strict false accepts: 0;
- strict false rejects: 0;
- intentionally weak name/shape validator false accepts: 257,350.

Gate-admission suite:

- strict false accepts: 0;
- strict false rejects: 0;
- intentionally weak status-only validator false accepts: 253,818.

These values are discriminator sensitivity under a constructed distribution, not real-world defect rates.

The experiment does not establish production correctness, target-host behavior, or the necessity of signed provenance. It only shows that the proposed identity/state/scope distinctions provide strong discrimination under the tested mutations.

## Transformed architecture after Fusion 2

The original question `how do we attest the runtime gate?` transformed into a broader but cleaner architecture:

```text
EffectIntent
  -> external policy/adjudication
  -> trusted mint/grant root
  -> opaque live CapabilityHandle
  -> typed runtime adapter
  -> effect + effect receipt

separate:

exact runtime/artifact + exact test + exact invocation/workflow + semantic materials
  -> actual execution
  -> GateExecutionReceipt / optional signed provenance
  -> verification
  -> evidence-scope check
  -> release/work-package admission
```

Cross-casts are forbidden:

```text
attestation -X-> CapabilityHandle
CapabilityHandle -X-> proof of gate execution
workflow file -X-> execution
commit title -X-> PASS
hosted proxy -X-> target acceptance
```

Recommended gate state machine:

```text
DEFINED
-> QUEUED
-> RUNNING
-> EXECUTED
-> RECEIPT_PRESENT
-> VERIFIED
-> ADMITTED

mismatch/failure -> REJECTED
```

The candidate receipt binds gate identity, exact subject, exact materials, execution identity, result checks and evidence scope. A signed external attestation may be referenced as additional provenance but is not required as a Clay semantic primitive.

## Mint-root decision tree

Three implementation candidates are preserved until the production guest ABI is inspected:

A. split issuer/broker: trusted bootstrap owns issuance; guest-facing runtime only validates/uses selected handles;

B. root-authority object: mint requires a root object absent from guest semantics while keeping one process;

C. pre-authorized handle table: bootstrap installs attenuated handles and guest receives only opaque references.

The shortest discriminator is not another paper search. It is to enumerate the actual model/guest-facing runtime ABI and attempt capability issuance only through that surface.

## Target-host cascade

The highest-information production sequence is now:

1. re-read newest main and intentionally select the exact runtime subject to test;
2. compute exact runtime/artifact, validation-suite and invocation/workflow identities;
3. run hosted Ubuntu as proxy and emit a clearly scoped receipt;
4. mutate subject/material/scope/result fields and prove admission rejects stale or mismatched evidence;
5. prove an evidence/attestation object cannot substitute for a live capability handle;
6. prove the guest/model surface cannot directly invoke the unrestricted mint/grant root;
7. execute the identical digest-bound suite on `ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM`;
8. verify the target receipt before advancing the corresponding BASE acceptance state;
9. only if the runtime threat model warrants it, benchmark/test Linux kernel confinement as a separate defense-in-depth layer.

## Cross-branch feedback

ClayCode receives a new implementation constraint: exact proof-carrying execution/admission without a core syntax change.

Harness receives a new evidence rule: workflow files, queues and labels are not execution receipts.

FRANK receives an assurance constraint: live effect authority and historical evidence remain disjoint.

UnifiedDB should preserve gate transitions append-only with evidence references rather than one optimistic status bit.

ClayGraph may index evidence relationships but graph activation is not truth promotion.

GWT broadcast/relevance remains separate from evidence verification.

Hyperposition may preserve unknown/multiple possible gate states until verification instead of collapsing uncertainty into PASS.

Emergenz experiments should bind exact executable/harness/test identities so software drift cannot be mistaken for a causal effect.

Clayresearch receives the whole-system separation: authority, provenance, execution evidence, truth and admission are different relations.

## Durable run artifacts

The run directory contains:

- `SPAWN_RECEIPT.json`
- `HYPOTHESES.json`
- `EVIDENCE_MANIFEST.json`
- `INTERCONNECT_MANIFEST.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json`
- `GATE_ATTESTATION_CONTRACT_CANDIDATE_V1.json`
- `MINT_AUTHORITY_BOUNDARY_NOTE.json`
- `DEEP_AUDIT_ADDENDUM.json`
- `capability_attested_gate_probe.py`
- `EXECUTION_RECEIPT.json`
- `FINAL_REPORT.md`

The run also created dynamic work item:

`WORK-CLAYCODE-CAPFFI-ATTESTED-GATE-20260809`

It is deliberately narrower than the existing 14-package BASE closure work: it supplies a concrete production discriminator for the authority/evidence boundary and target-host receipt path.

## Negative results preserved

- no runtime capability receipt was found at the declared canonical path on final recheck;
- no new ClayCode core syntax is justified;
- no production exposure of mint/grant root to guest code was established;
- no claim is made that signed GitHub provenance is mandatory;
- no target-host acceptance was produced by this hosted run;
- no scientific promotion was made;
- synthetic discriminator counts are not prevalence estimates;
- grammar-version labels do not by themselves prove semantic inconsistency;
- Landlock/seccomp remain conditional options, not BASE requirements.

## Final synthesis

The ClayCode runtime is already becoming much stronger at rejecting invalid authority use. The higher-order blocker is now evidence identity: the system must prove which exact runtime, test suite and execution scope produced a claimed gate result, while keeping that historical proof completely separate from live effect authority.

The smallest high-value architecture change is therefore:

- preserve current G9 semantics;
- keep effect intent descriptive;
- isolate and test the mint/grant root;
- retain opaque live capability/resource handles;
- make gate state proof-carrying and exact-digest-bound;
- preserve `DEFINED`, `EXECUTED`, `VERIFIED` and `ADMITTED` as different states;
- keep hosted and Andreas-target evidence scopes distinct;
- add signed provenance only where it strengthens the chosen threat model;
- optionally use Linux kernel confinement as defense in depth;
- require the actual Andreas Ubuntu receipt before target acceptance advances.

This is the strongest current synthesis because it explains the live repository evidence, survives the counterhypotheses, does not reopen frozen ClayCode semantics, and directly improves the causal reliability of the next Harness/FRANK acceptance results.
