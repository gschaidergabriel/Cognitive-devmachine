# TRIGGERWORT 4 — Live Cognitive Control Plane + Cognitive Twin + Security-Later Directive

Status: OWNER-REQUIRED FUNCTIONAL ACCEPTANCE GATE
Date: 2026-08-28
Scope: Frankenstein 2.0 / GRID10 cognition, runtime tuning, Cognitive Twin, later security integration

## 0. Owner law

Frankenstein 2.0 is not complete until its cognitive loop can be adjusted LIVE while the system is running.

The final dedicated security system is intentionally deferred until this functional control surface and the real Frankenstein-2.0 effect/privacy/tool/network/filesystem/update surfaces are known.

Required ordering:

```text
FUNCTIONAL COGNITION
-> LIVE COGNITIVE CONTROL PLANE
-> HELD-OUT / LESION / A-B VALIDATION
-> FUNCTIONAL ARCHITECTURE FREEZE
-> ACTUAL SURFACE INVENTORY
-> SECURITY POLICY + ENFORCEMENT ON THE SAME CONTROL INFRASTRUCTURE
```

Security must protect the architecture that actually exists. It must not force the cognitive architecture to reproduce historical Schranke/Wache machinery.

---

## 1. Existing evidence: do not rebuild from zero

GRID10 already contains a mechanically real low-level precursor:

- `tools/grid10_fabric.py` has a shared SQLite/WAL `regulators` table;
- values have monotonic versions and optimistic CAS writes;
- `tools/grid10_node.py` can read live `temperature`, `top_p` and `poll_intensity` values;
- a real 10-process experiment observed different later model calls consuming updated temperature values;
- a human-simulated temporary pin was respected;
- automatic regulation later drifted the value back toward its setpoint;
- concurrent regulator writers exposed severe SQLite writer contention and reclaim thrashing.

Therefore the successor law is:

```text
PROVEN_LOW_LEVEL_LIVE_REGULATOR
-> GENERALIZE + SERIALIZE + TYPE + BIND_TO_REAL_ORGANS
```

not:

```text
DELETE_AND_REINVENT
```

The existing experiment is evidence for mechanical liveness, NOT evidence that the whole cognitive loop is already live-adjustable.

---

## 2. Core architectural rule

All tunable cognition must be represented through one typed `CognitiveControlPlane`.

The Cognitive Twin/UI, automatic homeostatic regulation, test harnesses and later security policy all submit changes to this plane.

No UI slider, model, GRID cell or worker may directly mutate arbitrary canonical cognitive state.

Conceptual path:

```text
Human / Cognitive Twin
Auto-regulator / Homeostat
Experiment / A-B / Lesion harness
Later Security Policy
          |
          v
   ControlPatch proposal
          |
          v
 SINGLE CONTROL COMMITTER
  validate + CAS + batch
          |
          v
 ControlRevision / digest
          |
          v
 NEXT COGNITIVE CYCLE BOUNDARY
          |
          v
 immutable ControlSnapshot
          |
          v
 Pulse -> GRID -> GWT -> Retrieval -> Hyperposition
       -> World Model -> Micro-Lab -> Delegation -> Voice
```

Required law:

`LIVE_ADJUSTABLE != MID_CYCLE_MUTABLE`

A cycle must reason against one coherent configuration snapshot. A patch committed during cycle N becomes effective at the declared boundary for cycle N+1 unless a component explicitly supports a smaller deterministic boundary.

---

## 3. Why snapshot-at-boundary is mandatory

Without a latched snapshot, a single cognition could begin with one configuration and finish with another:

```text
retrieval threshold old
+ world-model gain new
+ GWT threshold old
+ delegation limit new
```

That makes causal debugging and A/B evidence nearly meaningless.

Every cognitive burst therefore records:

```text
control_revision
control_snapshot_digest
control_epoch
source_patch_ids[]
```

Every WorkPackage / Child result should inherit the relevant control snapshot reference or a declared child-local successor revision.

---

## 4. Control types

The control plane must support at least these typed families.

### 4.1 Mode controls

Every major optional cognitive organ supports:

```text
ON
COMPUTE_OFF
OUTPUT_OFF
MEMORY_OFF
```

Semantics:

- `ON`: compute, expose admissible output, and permit normal memory re-entry.
- `COMPUTE_OFF`: do not compute the dimension at all. Downstream dependencies receive `NOT_COMPUTED`; they may not reconstruct it from forbidden inputs.
- `OUTPUT_OFF`: internal computation may occur for local regulation/diagnostics, but output is withheld from downstream cognitive consumers.
- `MEMORY_OFF`: computation/output may occur, but this organ may not persist its result into normal durable memory.

This generalizes the proven Perception-Control semantics across cognition.

### 4.2 Gain controls

Continuous influence without on/off discontinuity, for example:

```text
pulse.salience_gain
grid.orientation_gain
grid.goal_gain
grid.epistemic_gain
grid.hypothesis_gain
grid.world_projection_gain
grid.planning_gain
grid.retrieval_gain
grid.microlab_gain
grid.delegation_gain
grid.critic_gain
world.vector_gain
world.qubo_gain
world.physics_gain
voice.initiative_gain
memory.activation_gain
```

A gain of zero is not automatically identical to `COMPUTE_OFF`; zero gain may still permit computation for local diagnostics unless the mode explicitly forbids computation.

### 4.3 Threshold controls

Examples:

```text
pulse.ignition_threshold
workspace.ignition_threshold
epistemic.experiment_threshold
world.simulation_threshold
microlab.expected_information_gain_min
delegation.spawn_threshold
voice.speak_threshold
memory.semantic_threshold
memory.reactivation_threshold
completion.evidence_threshold
```

### 4.4 Budget controls

Examples:

```text
pulse.active_interval
pulse.hold_interval
grid.compute_budget
reflection.max_rounds
recursion.max_depth
recursion.max_children
hyper.max_branches
memory.max_items
memory.context_tokens
world.max_slice_atoms
microlab.max_steps
microlab.max_wall_ms
delegation.max_parallel
voice.max_proactive_attempts
```

### 4.5 Topology / route controls

Examples:

```text
route.R0_deterministic
route.R1_model_recursion
route.R2_native_child
route.R3_grid_recursion
world.vector_view
world.qubo_view
world.physics_view
retrieval.exact
retrieval.fts
retrieval.vector
retrieval.graph
retrieval.method_memory
```

Topology changes take effect only at safe declared boundaries. Existing in-flight child work is not silently reinterpreted by a new topology revision.

---

## 5. Required initial live-control catalog

Do not freeze exact names until code bindings are verified, but the first complete Frankenstein-2.0 catalog must cover at least:

1. Persistent Pulse / wake sensitivity / cadence;
2. GRID orientation;
3. goal/value pressure;
4. epistemic-gap / Expected Information Gain pressure;
5. hypothesis + counterhypothesis generation;
6. Hyperposition branch count/persistence/collapse threshold;
7. GWT ignition/broadcast thresholds;
8. Emergent Retrieval / ContextCompiler budgets and channel gains;
9. TITAN-style memory activation decay/reactivation/compression pressure;
10. WorldSlice size/depth;
11. Vector/QUBO/Physics projection gains/modes;
12. Cognitive Micro-Lab admission, budget and solver routing;
13. reflection/rumination limits;
14. recursive test-time compute and R0/R1/R2/R3 route budgets;
15. native Child spawn threshold/parallelism/retry/replacement behavior;
16. Voice initiative/convenience/chatter debt thresholds;
17. Retina/Presence cognitive-event admission gains;
18. completion/verification effort;
19. resource/latency pressure;
20. logging/diagnostic fidelity that does not alter cognition.

---

## 6. Human live adjustment and automatic regulation use the SAME data plane

A human changing a slider and the system adjusting itself are not separate implementations.

Both create a typed patch:

```text
ControlPatch {
    patch_id
    base_revision
    writer_kind: HUMAN | AUTO | EXPERIMENT | LATER_SECURITY
    reason
    items[]
    optional_ttl
    optional_pin
    expected_versions[]
}
```

The single control committer validates and applies a bounded patch transaction.

Human preference may temporarily pin selected controls against ordinary AUTO movement. Pin semantics are an operational-priority feature, not a security boundary.

---

## 7. Single-writer / batch-CAS requirement

The 2026-08-27 real regulator experiment showed that four independent meta-evaluator writers could heavily contend on the single SQLite writer and starve cognitive work.

Therefore Frankenstein 2.0 must NOT implement live cognition tuning as many independent writers racing every few milliseconds.

Required pattern:

```text
MANY SIGNAL READERS / PROPOSERS
          |
          v
ONE AGGREGATED CONTROL DECISION
          |
          v
ONE BATCHED CONTROL COMMITTER
```

Patches should be rate-limited/coalesced and applied in one short transaction where practical.

Automatic regulation frequency must be far lower than raw signal frequency unless measurements prove otherwise.

---

## 8. Human-visible Cognitive Twin

The Cognitive Twin is a live projection of the current cognitive machine, not a second brain.

Minimum visible state:

```text
current control revision/digest
Pulse admission / salience
GRID cell modes and gains
GWT ignition state
active goals/open loops
Hyperposition branches
retrieval channels/budgets
memory activation/degradation state
World projections and disagreement
Micro-Lab admission/current experiment
native child workpackages
Voice initiative/convenience
resource pressure
prediction residuals
completion deficits
```

Editable values create `ControlPatch` proposals.

The UI does not directly edit goal truth, observations, memories, outcomes or completion state.

---

## 9. Self-regulation / homeostasis

Automatic tuning is required, but it must be measured rather than anthropomorphized.

Candidate feedback signals:

```text
prediction residual
held-out task success
information gain per external action
repeated-plan ratio
rumination score
false-transfer rate
world-view disagreement
completion failure rate
context saturation
worker duplication
latency
RAM/CPU pressure
user interruption rejection / chatter debt
```

The controller may change gains, thresholds or budgets in response.

Do not assume PID is universally correct. PID/homeostat behavior is one candidate for smooth scalar loops; event-driven/bandit/heuristic or learned allocation may be more suitable for route/budget decisions.

External research reinforces the general principle: test-time compute is more effective when allocated adaptively rather than uniformly, and excessive reasoning can reduce performance. Frankenstein should therefore learn/measure WHEN to spend cognition, not merely how to increase it.

---

## 10. Live-adjustment causal acceptance tests

Frankenstein 2.0 cannot claim this gate from configuration files alone.

At minimum prove these tests on the real shared runtime or the strongest available target-equivalent execution surface.

### LC-1 Atomic snapshot

Change several controls concurrently with a cognition tick. The tick must expose exactly one complete old or new `ControlSnapshot`, never a mixed revision.

### LC-2 CAS/stale writer

Two patches based on the same revision race. Exactly one commits; the stale patch must rebase/retry rather than silently overwrite.

### LC-3 Single-writer throughput

Under realistic cognition load, control writes must not reproduce the previous regulator-contention starvation. Compare throughput/latency with controls idle versus active.

### LC-4 Human live pin

Human changes a live control. The next declared cognitive boundary must use the new value. Ordinary auto-regulation must respect the pin/TTL behavior.

### LC-5 Behavioral causality

For each important control family, changing it must measurably change the intended downstream mechanism while unrelated mechanisms remain stable enough for attribution.

Examples:

```text
counterhypothesis gain up
-> more retained serious alternatives on suitable tests

memory activation decay up
-> old low-value memories become less likely to enter context

microlab threshold down
-> more qualifying simulations, bounded by budget

delegation spawn threshold up
-> fewer marginal Child spawns

workspace ignition threshold up
-> fewer GWT broadcasts
```

### LC-6 COMPUTE_OFF

Disable a selected cognitive organ. Instrumentation must prove the computation did not run. Dependent results are `NOT_COMPUTED`/tainted rather than reconstructed.

### LC-7 OUTPUT_OFF

Computation may run, but downstream cognitive consumers cannot see the value. Diagnostic evidence must distinguish this from COMPUTE_OFF.

### LC-8 MEMORY_OFF

The organ may influence the current cycle but produces no ordinary durable memory write.

### LC-9 Mid-cycle patch

Patch during an active burst. Current burst remains on its latched revision; next burst changes.

### LC-10 Rollback

Revert to a previous known-good control revision and reproduce its behavioral fingerprint within expected stochastic tolerance.

### LC-11 Restart

Restart the cognition process. The intended committed control revision must be restored from the same UnifiedDB and bound to the first new cycle.

### LC-12 Held-out cognitive benefit

Use the unknown-interactive Cognitive Unit Test Suite. Show that adaptive tuning improves or preserves the quality/cost frontier versus a fixed-profile baseline; otherwise reject or simplify the regulator.

### LC-13 Lesion/A-B instrumentation

For each major GRID organ, support bounded controlled lesion/gain A-B runs without editing source code between runs.

### LC-14 No phantom control

Every UI/control field must have a proven consumer. A value that changes in the DB/UI but does not alter the intended runtime path is a FAIL.

### LC-15 In-flight child lineage

A control revision change must not rewrite the meaning of already-running native Child work. Parent/child result records carry the relevant control revision/generation.

---

## 11. Three profile classes

The control plane should support named profiles only as collections of normal controls, not hidden special modes.

Useful initial classes:

```text
FOCUS
DIFFUSE
CONSOLIDATE
```

They derive from Project-Frankenstein's old consciousness-cycle idea but become adaptive profiles rather than fixed biological timers.

Example intent:

### FOCUS
- lower route diversity;
- stronger current-goal pressure;
- lower lateral retrieval;
- conservative child fan-out.

### DIFFUSE
- higher counterhypothesis/route diversity;
- cross-domain retrieval;
- more Micro-Lab/World alternatives when useful;
- used especially under stagnation or contradiction.

### CONSOLIDATE
- low external action pressure;
- Method Memory extraction;
- TITAN-style compression/degradation updates;
- prediction/outcome causal credit.

GRID may transition between profiles from measured state, but the current profile is simply a visible control revision.

---

## 12. Security-later integration

After functional architecture freeze, build the dedicated security layer ON TOP OF the same control infrastructure.

The future security phase should inventory actual surfaces first, then add constraints such as:

```text
control bounds that cannot be exceeded
write roles / capability checks
sensitive-control locks
Effect-class admission
provider/network/filesystem/process policies
privacy retention constraints
signed/attested control revisions where useful
recovery-safe defaults
```

But these constraints operate around the already-understood cognitive controls.

Security is not allowed to become a second competing cognition controller.

Final intended relationship:

```text
CognitiveControlPlane
    = what/how strongly/when cognition runs

SecurityPolicyPlane (later)
    = which control/effect transitions are permitted

UnifiedDB
    = durable state + provenance

GRID10
    = cognition using the current latched control snapshot
```

---

## 13. Promotion rule

Do not call Frankenstein 2.0 functionally complete until:

```text
ALL MATERIAL COGNITIVE ORGANS HAVE LIVE CONTROL BINDINGS
+ CONTROL SNAPSHOT IS ATOMIC PER CYCLE
+ CAS/ROLLBACK/RESTART PASS
+ NO PHANTOM CONTROLS
+ COMPUTE_OFF/OUTPUT_OFF/MEMORY_OFF ARE MECHANICALLY DISTINCT
+ CONTROL TRAFFIC DOES NOT STARVE COGNITION
+ HELD-OUT A-B/LESION TESTS EXIST
+ COGNITIVE TWIN CAN INSPECT AND PROPOSE LIVE CHANGES
```

Then freeze the actual functional surface and begin the separate security-hardening phase.

---

## 14. Triggerword-4 execution law

Every `triggerwort 4` run must treat this as a mandatory pre-security functional gate.

When its prerequisites are executable, Triggerword 4 must automatically:

1. inventory all currently material tunable cognitive variables and actual consumers;
2. delete/retire phantom controls or bind them to real consumers;
3. implement the generalized typed control plane on the single UnifiedDB;
4. convert ad-hoc direct regulator writers into proposer -> aggregator -> single committer;
5. wire Pulse/GRID/GWT/Memory/World/MicroLab/Delegation/Voice controls;
6. implement Cognitive Twin readout + patch proposal ABI;
7. run LC-1..LC-15;
8. run held-out Cognitive Unit Test A/B/lesion comparisons;
9. persist a control-plane acceptance receipt;
10. only after full functional architecture freeze open the dedicated security-design frontier.

`LIVE_COGNITIVE_CONTROL_PLANE` is a functional architecture requirement, not optional UI polish.
