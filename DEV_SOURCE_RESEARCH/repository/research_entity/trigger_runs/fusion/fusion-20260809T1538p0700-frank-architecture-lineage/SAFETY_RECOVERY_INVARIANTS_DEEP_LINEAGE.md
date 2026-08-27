# FRANK Safety / Recovery / Invariants / Immune — deep evolution lineage

Run: `fusion-20260809T1538p0700-frank-architecture-lineage`
Status: archaeology + current target synthesis

## SRI-0 — safety systems existed at first public baseline

Initial public commit `e1a8812767668091d146ee958bbc2ebb2743031c` already described:
- A.S.R.S. rollback/recovery;
- invariants engine;
- agentic approval gates.

Later architecture added F.A.S., watchdog/sentinel systems, Neural Immune, neural/reality/conscience filters and increasingly explicit effect boundaries.

The historical lesson is not “more safety layers is always safer.” Several safety layers themselves produced cascades, stale state or false violations.

## ASRS-1 — staged rollback/recovery

Historical documentation describes a four-stage ASRS monitoring/rollback process around system changes. It was intended to detect degradation and restore known-good state.

The core reusable ideas are:
- before-state snapshot;
- change identity;
- health/evidence window;
- rollback path;
- post-rollback revalidation.

Current target makes these receipts explicit and idempotent rather than relying on process/log heuristics alone.

## ASRS-2 — recovery cascade caused by own errors

Commits `d241937...` / `e93a8e5...` (2026-02-17):
- ASRS counted systemd "Failed to start" lifecycle messages caused by its own restart/revalidation sequence as application errors;
- restart -> error log -> error counter -> more restarts;
- lifecycle messages were excluded from application-error counting.

Current law:
`recovery action output != independent evidence of original fault`.
All recovery-generated events carry causal-parent/source identity so they cannot recursively retrigger the same policy without explicit semantics.

## INV-1 — invariant engine: energy, entropy, core kernel, triple reality

By February documentation, invariants were organized around:
- energy conservation;
- entropy bounds;
- protected core kernel;
- triple-reality / shadow state comparison.

These mechanisms were attempts to create deterministic system-state constraints outside the LLM.

Current reuse is selective:
- deterministic state invariants remain strongly valuable;
- biological/physics naming is not itself evidence;
- equations/tolerances must be tested against actual state semantics rather than treated as metaphysical laws.

## INV-2 — energy equation initially produced pathological violations

Commit `f2cb391...` reports energy was previously computed from effectively empty/wrong node state, yielding persistent `0 vs 1000` mismatch and **35,891 violations**. It was changed to use edges/events/system baseline and adaptive constant.

`14b5071...` later lowered adaptation threshold, added recalibration, cleaned ledger 10,198 -> 100 entries and reset 6,666 violations.

`39fc0dd...` changed tolerance 0.1% -> 2% to reduce false violation spam.

Deep audit `07f8e26...` then found energy constant runaway 100 -> 1107, adding 10% growth cap and 2000 ceiling.

Current lesson:
- an invariant that adapts to observed state can normalize the very fault it should detect;
- invariant parameters and adaptation require adversarial drift tests;
- alert count is not correctness evidence.

## INV-3 — atomic shadow/reality state

Commit `6690e3d...` fixed Triple Reality/shadow operations:
- SQLite connection leak;
- non-atomic `shutil.copy2` replaced with tmp + `os.replace` in init/rollback/resync;
- prior empty ghost shadow files were detected and repaired.

Current architecture directly inherits:
- publish new state atomically;
- previous valid version remains available until replacement is complete;
- existence of a file is not proof that its schema/content is valid.

This maps to current `Atomic Semantic Publication` and last-known-good rollback requirements.

## INV-4 — resource limits can kill the safety organ

Deployment commits `afab688...` and `199c57f...` show Invariants memory limits were too low:
- 150/200 MB then 250/300 MB limits;
- actual core-kernel build used ~270 MB;
- systemd SIGTERM occurred;
- raised to 400/500 MB.

Current rule:
- resource governor must reserve enough budget for safety/recovery code;
- resource-policy violation is explicit, not confused with semantic fault.

## IMM-1 — Neural Immune creation

Commit `ccebdc78...` (2026-03-03) introduced distributed health monitoring as a learned/rule hybrid.

It later used several small networks and a supervisor/collector structure. SFT Stabilizer integration describes ~3 nets / ~19K parameters at that historical point.

## IMM-2 — deployment mapping failures

Commit `8ddb1bf...` found:
- 9 wrong service port mappings in collector;
- supervisor restart-request TOCTOU race.

Commit `7bf44fb...` found watchdog/immune systems tried to restart services that were not installed, creating cascade restarts of healthy systems. Both were changed to verify installed service state first.

Current law:
`expected topology must be versioned/current`; absence may be intentional configuration, not a fault.

## IMM-3 — cold-start learned anomaly output was useless

Deep audit `07f8e26...` reports `anomaly_score` always 0.0. Fix added cold-start thresholds and rule-based fallback.

`1d443890...` also added NaN guards, label-bias fixes, BaselineNet expansion 20 -> 30 services and loss scaling.

Current reuse:
- deterministic/rule baseline remains primary until learned detector is calibrated;
- learned anomaly score never directly restarts or authorizes effects without deterministic policy.

## WATCH-1 — watchdog proliferation

History included:
- Frank watchdog;
- Sentinel;
- Dream watchdog + meta-watchdog;
- Genesis watchdog;
- model RSS restart watchdog;
- Neural Immune supervisor.

This provided observability but also created duplicated hardcoded service lists and cascade risks.

Current H3 target should collapse health policy into a typed recovery/observability plane where semantic component identity is independent of process count.

## REC-1 — reference DB recovery tools

Commit `8a87de0...` snapshotted 39 SQLite DBs + Titan vectors/invariants (~40 MB reported) and created `frank_recovery.py`:
- stop services;
- backup current DBs;
- wipe;
- restore reference DBs;
- restart.

Later `8512cb3...` snapshotted 48 live DBs as seed state and `fc3fb3f...` synchronized recovery service lists.

Useful principle:
- known-good baseline and complete-state restore matter.

Correction:
- wholesale DB restore is too coarse for final semantics;
- current architecture needs canonical event/state replay, schema migration, per-organ current/derived state classes and differential validation.

## REC-2 — restart/order/TOCTOU as repeated architecture failures

Historical examples across organs:
- ASRS self-trigger cascade;
- Neural Immune restart-request TOCTOU;
- SOMA duplicate restart flag and concurrent training;
- E-PQ stale process singleton overwrite;
- incomplete shadow DB/file existence;
- service install-list drift;
- model/service restart ordering around training;
- Thalamus singleton shutdown race.

These establish boot/restart/order as a first-class architecture dimension, not deployment trivia.

## AUTH-1 — proposal approval evolves toward hard effect separation

Historical Genesis/FAS and agentic approvals already distinguished some proposed changes from approved execution.

C4-C9 progressively sharpen this into:
- model/Needle output = proposal;
- effect intent = serializable non-authoritative object;
- permit = opaque host-minted capability handle;
- commit = current-state/revocation/basis/resource revalidation;
- generated child code cannot widen parent authority.

This is the direct successor of historical ASRS/FAS lessons.

## SRI-1 — current fused target

### Deterministic invariant plane
Typed invariants over current canonical state, authority, schema, basis, resource and recovery properties.

### Health/anomaly plane
Observed process/device/resource symptoms are evidence, not automatic semantic truth. Learned detectors may prioritize investigation but cannot self-authorize restarts/effects.

### Recovery plane
- append/replay event spine;
- atomic checkpoints/publication;
- explicit last-known-good state;
- versioned migration;
- idempotency keys;
- crash-mid-effect tests;
- recovery-generated events carry parent/source identity.

### Effect plane
Protected external changes go through `EffectIntent -> host EffectPermit -> release-time revalidation -> EffectReceipt`.

## Mandatory regressions

- SRI-REG-01 recovery action creates error logs that recursively trigger recovery;
- SRI-REG-02 absent optional service treated as failed mandatory service;
- SRI-REG-03 hardcoded service/port list stale after architecture migration;
- SRI-REG-04 invariant false-positive storm due wrong state source;
- SRI-REG-05 adaptive invariant normalizes runaway state;
- SRI-REG-06 empty/corrupt shadow file accepted because path exists;
- SRI-REG-07 crash during shadow/current replacement exposes partial state;
- SRI-REG-08 safety process killed by its own undersized resource limit;
- SRI-REG-09 learned anomaly detector at cold start reports false certainty;
- SRI-REG-10 recovery/restart TOCTOU duplicates effect;
- SRI-REG-11 stale cached organ state overwrites recovered current state;
- SRI-REG-12 generated tool/child code widens parent capability;
- SRI-REG-13 H1/H2/H3 crash/replay/idempotency differential equivalence.

## Fusion decision

- ASRS: `REUSE_RECOVERY_STATE-MACHINE_PRINCIPLES; REBUILD_WITH_TYPED_RECEIPTS/IDEMPOTENCY`.
- Invariants: `REUSE_DETERMINISTIC_CONSTRAINT_PLANE; RETEST_EQUATIONS/TOLERANCES; NO_ADAPTIVE_SELF-NORMALIZATION_WITHOUT_CONTROLS`.
- Neural Immune/watchdogs: `REUSE_OBSERVABILITY/ANOMALY_SIGNALS; COLLAPSE_DUPLICATE_PROCESS_POLICY; LEARNED_SCORE_NON-AUTHORITATIVE`.
- Triple Reality/shadows: `REUSE_ATOMIC_LAST-KNOWN-GOOD_AND_DIFFERENTIAL_STATE_PRINCIPLE`.
