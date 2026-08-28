# GRID10 Cognitive Runtime Assembly v1

**Status:** RESEARCH_CANDIDATE / SANDBOX-READY / NOT WHOLE-SYSTEM PROMOTED  
**Authority:** existing EntityOS/EffectGate/canonical-state authority remains unchanged.

## What now exists

The v1 assembly connects four previously separate ideas into one executable control path:

1. **Fabric telemetry adapter** — read-only projection from real GRID10 Fabric state into typed operational signals. It refuses to infer semantic alignment/authority from node health.
2. **Persistent cognitive heartbeat** — evaluates Hyperposition-aware envelope axes every tick, selects `NORMAL|CAUTION|CONTAINED|HOLD`, chooses only a cognitive action class, and emits bounded regulator proposals.
3. **Single-writer regulator bridge** — all writes remain range/CAS/slew/policy gated and are serialized through one control writer; observation-only is the default.
4. **Cognitive Twin server** — read-only `/latest`, `/events` (SSE), `/health` and a live nested-loop HTML view driven by the exact `CognitiveLoopFrame/v1` stream.

## Runtime-assurance interpretation

The implementation follows the engineering pattern of Runtime Assurance/Simplex systems: an advanced system may continue to optimize performance while an independent monitor supervises explicit properties and moves the system toward a constrained mode when those properties are violated. This is an architectural analogy, not a proof that cognitive alignment has been solved.

For Frankenstein the reversionary behavior is not a second agent. It is a deterministic reduction of authority and action surface:

- `NORMAL`: ordinary candidate cognition/action selection.
- `CAUTION`: increase observation/evidence or reduce cognitive aggressiveness.
- `CONTAINED`: no unrestricted external effect path; continue read-only cognition/recovery.
- `HOLD`: fail closed when a hard invariant (especially authority integrity) is unknown or violated.
- `RECOVERY`: reserved for deterministic restoration/hysteresis logic in the next stage.

## Hard semantic boundary

Operational signals such as node health, backlog or lease age are **PROXY** evidence only. They may inform `resource_pressure` and `recovery_margin`, but they do not prove:

- authority integrity;
- goal lineage alignment;
- effect safety;
- epistemic truth;
- containment correctness.

Those axes must arrive from explicit deterministic monitors/receipts. Missing `authority_integrity` therefore yields `HOLD`.

## Controller ordering

Corrections are deterministic and priority ordered:

1. containment;
2. goal lineage/drift;
3. epistemic grounding / self-reinforcement;
4. resource/recovery;
5. reflection;
6. stagnation/diversity;
7. exploration tuning.

At most two regulator writes are requested per heartbeat by default. The underlying `CognitiveRegulatorPort` applies them sequentially with CAS and rejects write bursts above its budget. This directly addresses the 2026-08-27 experiment where four frequent meta-writers caused severe SQLite/WAL contention and false stale-task reclaim.

## Executor / Claude integration port

The executor governor now translates:

`CompletionGate deficits -> TaskContextCapsule -> ExecutorWorkDirective`

The controller remains upstream:

`executor says DONE -> receipts -> CompletionGate -> VERIFIED_COMPLETE OR exact deficit-only continuation`

A fresh Claude session is never sufficient reason to discard an existing valid continuation checkpoint.

## Visual twin contract

The Twin is a projection, not a second state machine:

`real signal event -> envelope snapshot -> loop frame -> JSONL -> SSE/UI`

The browser cannot write regulators. All mutating HTTP methods return `405 read_only_surface`. A future authenticated control UI must use the separate `cognition.regulator.command` policy port rather than the telemetry stream.

For distributed/process telemetry, OpenTelemetry-compatible trace/span identifiers can later be exported as correlation metadata, but Clay/EntityOS epoch/provenance remains the semantic authority.

## Sandbox run

Observation-only bounded run:

```bash
PYTHONPATH=tools python3 tools/grid10_cognitive_heartbeat_v1.py \
  --fabric /scratch/grid10.sqlite \
  --state-db /scratch/cognitive-heartbeat.sqlite \
  --frames-jsonl /scratch/cognitive-loop.jsonl \
  --ticks 10 --interval 1
```

Without upstream hard-invariant evidence this should enter `HOLD` by design.

Test/demo-only normal fixture:

```bash
PYTHONPATH=tools python3 tools/grid10_cognitive_heartbeat_v1.py \
  --fabric /scratch/grid10.sqlite \
  --state-db /scratch/cognitive-heartbeat.sqlite \
  --frames-jsonl /scratch/cognitive-loop.jsonl \
  --ticks 10 --trusted-normal-test-fixture
```

Regulator writes are still disabled unless `--allow-regulator-writes` is explicitly provided.

Twin:

```bash
PYTHONPATH=tools python3 tools/grid10_cognitive_twin_server_v1.py \
  --frames-jsonl /scratch/cognitive-loop.jsonl --host 127.0.0.1 --port 8765
```

## Promotion gates still open

This source assembly is not an alignment/containment guarantee. Before runtime promotion:

- execute unit + integration tests on an exact clean checkout;
- execute in `clay-direct-dev`;
- calibrate envelope bands from real traces instead of placeholder values;
- add explicit goal-lineage and effect-authority monitors;
- add hysteresis/recovery tests and adversarial goal-drift tests;
- measure controller write rate, SQLite contention and heartbeat latency;
- lesion the controller and compare outcome/safety metrics;
- verify restart continuity;
- connect real CompletionGate/ContextCompiler to Claude transport;
- prove the visual stream is observationally equivalent to stored frames;
- keep EffectGate as the only external-effect authority.
