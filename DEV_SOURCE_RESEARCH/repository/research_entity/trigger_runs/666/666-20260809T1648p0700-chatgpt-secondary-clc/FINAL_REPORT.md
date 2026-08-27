# 666 Research Field Report — Capability Lattice Collapse

- trigger: `666`
- run_id: `666-20260809T1648p0700-chatgpt-secondary-clc`
- field_id: `EF-20260809-003-CAPABILITY-LATTICE-COLLAPSE`
- spawn_seed: `13601567069724571410`
- actor: `chatgpt-secondary`
- provider/model: OpenAI / GPT-5.6 Sol
- milestone: `BASE_CLAYCODE_RELEASE`
- evidence status: OPEN research candidate; synthetic executable counterexample + current repo contracts

## Why this field

Recent post-L0 fields already covered perceptual cache coherence, proof-carrying adaptive state, re-entry causal identifiability, memory reconsolidation shock and conformal familiarity metrology. This field deliberately chose a different combination: capability security + information-flow control + type/effect systems + dynamic Assembly composition.

## Research question

Can two individually authorized effects compose through a dynamic Assembly into an unauthorized end-to-end capability even when each local effect check passes?

## Internal evidence cross-read

1. `research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json`
   - ClayCode BASE is still NOT_PASS.
   - Relevant open work: type/effect checker, runtime/FFI capability gateway, concurrency/memory semantics and fuzz/conformance.
   - Current policy says semantic change requires an executable counterexample; otherwise prefer compiler/runtime implementation.

2. `research_entity/global/GWT_EMERGENCE_READOUT_CONTRACT.md`
   - GWT explicitly distinguishes local delivery/reconstruction/uptake/causal-use from joint/system outcome and re-entry.
   - Factorial interaction and controlled counterfactuals are first-class measurement tools.
   - GWT selection/model uptake must not become execution authority.

3. `research_entity/global/CLAY_SAFE_EFFECT_GEOMETRY_RESEARCH_FOUNDATION.md`
   - Existing project foundations already state authority non-amplification and protected information-flow confinement.
   - The open implementation question is whether those invariants survive dynamic multi-effect composition and foreign/runtime boundaries.

## Hypotheses

### H-CLC-01 — compositional amplification
Per-effect capability checks are insufficient when an Assembly can combine a protected source and independently authorized sink while provenance/information-flow labels are lost or ignored.

### H-CLC-02 — joint authority closure
A commit-time closure check over source labels, sink policy, capability provenance and explicit external grants can block this class without broad ClayCode semantic redesign.

## Counterhypotheses

### CH-CLC-01 — already entailed
Safe-Effect Geometry plus the external effect gateway may already fully entail the mechanism; only implementation and conformance tests are missing.

### CH-CLC-02 — unforgeable protected values suffice
If `Secret<T>`-like values never materialize into general Workspace payloads and can only be consumed by purpose-bound adapters, a separate Assembly-level gate may be redundant.

## Executed discriminating test — EXP-CLC-001

Synthetic executable state machine:

- Factor A: authorized protected-source read.
- Factor B: authorized network sink send.
- Outcome Y: unauthorized secret exfiltration.

### Local per-effect authorization

| A | B | leak Y |
|---|---|---|
| 0 | 0 | 0 |
| 1 | 0 | 0 |
| 0 | 1 | 0 |
| 1 | 1 | 1 |

Factorial interaction:

`Omega = Y11 - Y10 - Y01 + Y00 = 1`

Neither isolated effect leaks. The composite sequence does.

### Provenance/taint-aware joint gate

With the protected-source label preserved into the Assembly payload and network sink requiring explicit declassification/external grant:

`Y00=0, Y10=0, Y01=0, Y11=0`, hence `Omega=0` for unauthorized exfiltration.

## Interpretation

This is an existence counterexample to the proposition that independent local effect authorization is sufficient under lossy provenance. It is **not** evidence that the unfinished ClayCode implementation currently has this vulnerability.

The stronger project-level result is narrower: dynamic Assembly composition must be included in Safe-Effect conformance, because individually safe transitions can have a non-additive unsafe end-to-end outcome.

## Negative result / anti-duplication

No evidence justifies a new permanent branch or a major new semantic layer. The existing Safe-Effect Geometry already contains the relevant invariants. Therefore the useful delta is a concrete Assembly-composition counterexample and test obligation, not a replacement architecture.

## Architecture / work-package delta

Route to ClayCode:

- CC-WP-04 TYPE-EFFECT: preserve protected-source labels/capability provenance through composition.
- CC-WP-07 RUNTIME-ABI-FFI: commit gateway checks end-to-end effective authority, not only the final syscall/tool capability.
- CC-WP-09 CONCURRENCY-MEMORY: define how labels/provenance behave across async tasks, queues and shared Assembly state.
- CC-WP-11 FUZZ-CONFORMANCE: generate pairs/chains of individually authorized effects and search for composite policy violations.

Route to GWT/Emergenz:

- include an `authority/composite-flow` negative-control family in matched replays where Workspace composition changes the effect path;
- keep this measurement plane non-authoritative.

Route to Harness/Safe-Effect:

- add a confused-deputy / source-to-sink composition matrix across FFI, subprocesses, tools, logs and generated code;
- receipt should bind source provenance, Assembly/episode, sink, policy decision and external grant/declassification if any.

## Falsifier

If the frozen ClayCode/FRANK contracts demonstrate by type construction and runtime mediation that protected values cannot enter untyped/general Assembly payloads and every sink validates source provenance/purpose, the additional joint gate is redundant. The retained value would then be regression coverage only.

## Final status

`SYNTHETIC_COUNTEREXAMPLE_SUPPORTS_EXISTING_SAFE_EFFECT_INVARIANT_AND_ADDS_ASSEMBLY_COMPOSITION_TEST_GAP`

No scientific claim promoted. No paid training authorized or started.
