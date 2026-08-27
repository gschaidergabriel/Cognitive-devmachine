# Harness Research Delta — Trace/Replay + Status Integrity

Date: 2026-08-09
Actor provenance: chatgpt-secondary / OpenAI GPT-5.6 Sol
Entity: Clay / frank-project-global-research-entity
Research class: architecture/runtime review + external engineering precedent
Implementation status: RESEARCH_ONLY — no Frank Harness mutation performed

## Scope

Focused Harness research against the current project stage and current GitHub-visible Frank reference baseline, with emphasis on H1 Reference Harness readiness, H1->H2 differential reproducibility, status-surface correctness, replay semantics and fault/test architecture.

Current program fact at review time:
- current stage: BASE_CLAYCODE_RELEASE (IN_PROGRESS)
- H1_REFERENCE_HARNESS: BLOCKED on BASE_CLAYCODE_RELEASE
- H-WP-02 STATE-LEDGER already claimed by another/current ChatGPT research worker
- this note therefore does not duplicate H-WP-02 implementation work; it concentrates on H-WP-11 TRACE-REPLAY plus release-integrity implications.

## Internal evidence inspected

Clay repository:
- research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json — revision 2, state hash 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346
- research_entity/triggers/HARNESS_BUILD_PROTOCOL.md
- research_entity/harness/HARNESS_WORKSPACE.json
- research_entity/global/FRANKV0_1_REFERENCE_HARNESS_BASELINE.md
- research_entity/global/HARNESS_CLAYGRAPH_CONTRACT.md
- research_entity/experiments/FRANK_TEST1_CLAY_NATIVE_FULL_SIMULATION_CONTRACT.md
- research_entity/rooms/PROGRAM_STATE.json

Frank reference repository transport alias:
- gschaidergabriel/Dr.-Unterweger
- .claude/hooks/frank_prompt_inject.py @ blob 507c9339de44cdcd961dea3501749695796f7c33
- .claude/hooks/frank_stop_guard.py @ blob d8983be8866a00a36b67685d37fe6b370623d14c
- .claude/hooks/frank_state_path_guard.py @ blob 15992a2d347d510c807c4e07a4eb0b1fe0b12090
- runtime/status/frank_status_surface.py @ blob 871b59bf9827bc85cc0fbb17f4263c8d89011e62
- runtime/state/repo_truth_gate.py @ blob 9aa1964c2f83b461a7f46f1e6658cdd4884ff778
- tests/deep_integrity_regression_v11.py @ blob c06763cc2a88e5f1e3a01488d8959573a2f6beab

Important evidence limit:
GitHub code inspection is not equivalent to live execution on Andreas' Ubuntu host. Findings below are code-level/repository-level until reproduced on the target runtime.

## External primary engineering evidence

Evidence classes are kept separate from project/runtime evidence.

1. FoundationDB deterministic simulation/debugging guidance
   - primary project wiki/repository documentation
   - deterministic simulation failures depend on seed plus build/OS environment; exact reproduction may require matching environment, not seed alone
   - implication: FRANK replay receipts need environment/toolchain fingerprints in addition to model seed and state hashes
   Sources:
   - https://github.com/apple/foundationdb/wiki/Debugging-in-FDB
   - https://github.com/apple/foundationdb

2. TigerBeetle deterministic and outside-in simulation testing
   - primary project engineering documentation/blog
   - deterministic simulator makes rare failures reproducible and accelerates simulated time
   - separate non-deterministic compiled-binary/client harness (Vortex) exists specifically to cover DST blind spots
   - liveness testing benefits from a separate phase/mode rather than treating safety-only random faults as sufficient
   Sources:
   - https://tigerbeetle.com/blog/2023-07-06-simulation-testing-for-liveness/
   - https://tigerbeetle.com/blog/2025-02-13-a-descent-into-the-vortex/
   - https://docs.tigerbeetle.com/concepts/safety/

3. OpenTelemetry context propagation/tracing model
   - primary specification/documentation
   - trace/span context is propagated across process boundaries to preserve causal linkage across distributed components
   - implication: FRANK should use stable cross-node causal identifiers, but OTel-style trace context is observability metadata, not canonical truth/authority
   Sources:
   - https://opentelemetry.io/docs/specs/otel/overview/
   - https://opentelemetry.io/docs/specs/otel/context/api-propagators/

## Findings

### F-HARNESS-STATUS-001 — Status surface is not an atomic semantic snapshot

Observed code:
- runtime/status/frank_status_surface.py reads NOW/NEXT/NODES/skill state from UnifiedDB.
- v0.1 gate pulse is read separately from global/FRANK_V01_MILESTONES.json.
- these reads are not bound to one shared status-snapshot epoch/hash.

Failure mode:
A rendered surface can combine runtime state from one semantic epoch with gate state from another file/version. The byte string can be structurally valid while semantically representing a state that never existed atomically.

Status: OPEN, repository-evidence-supported.

### F-HARNESS-STATUS-002 — Renderer silently degrades to confident-looking defaults

Observed code:
- _state() catches broad Exception and returns defaults including:
  - "Frank v0.1 session active"
  - "continue verified current work"
- gate_pulse() catches broad Exception and returns "?".

Failure mode:
A database/query/schema/read failure can still produce a normal-looking NOW/NEXT line. This conflicts with the project rule that user-visible status must come from current verified state and creates a false-positive liveness/current-work impression.

Required direction:
Render explicit DEGRADED/UNKNOWN state from a verified failure receipt. Never substitute normal semantic defaults for unavailable canonical state.

Status: OPEN, repository-evidence-supported.

### F-HARNESS-GUARD-003 — Stop guard contains a root-unresolved fail-open compatibility path

Observed code:
- frank_stop_guard.py resolves the repo root via 000_FRANK_ANDREAS_MASTER_SOURCE.txt.
- when root resolution fails, the guard does not compare against the canonical renderer and does not require the TRIG field.
- tests/deep_integrity_regression_v11.py explicitly tests a simplified non-repo pulse in a temporary directory and expects acceptance.

Failure mode:
Loss/corruption/mis-location of the repo sentinel can move a fail-closed invariant into a weaker structural-validation mode. For a sovereignty/integrity guard, root-unresolved should itself be a hard failure, not a compatibility mode.

Status: OPEN, high-priority candidate bug.

### F-HARNESS-STATUS-004 — Endpoint label aggregation can hide multiplicity

Observed code:
- frank_endpoint_label() maps several internal node ids onto FRANK-LOCAL / FRANK-REMOTE / FRANK-NODE.
- _state() deduplicates by (label, glyph).

Failure mode:
Two distinct active endpoints with the same presentation label and glyph collapse into one visible entry. This preserves persona separation but loses endpoint multiplicity and can conceal whether one or several active sessions exist.

Required direction:
Either show counts (e.g. 2x FRANK-LOCAL) or aggregate behind an explicit group record whose membership is separately auditable.

Status: OPEN, medium priority.

### F-HARNESS-REPLAY-005 — Trace requirements exist, but one executable causal envelope is not yet the observable baseline oracle

Project contracts already require complete turn trace bundles, dynamic Run ClayGraphs, replay, checkpoint replay, model-output swaps, ablations and H1/H2 differential equivalence.

The inspected reference-baseline surfaces show event ids, prompt cycles, state epochs and receipts in multiple places, but no single reviewed TurnTraceEnvelope currently binds all architecture-relevant identities into one deterministic replay object.

This is not evidence that no implementation exists anywhere in the repository; it is evidence that the reviewed current release surfaces do not yet establish one frozen oracle contract.

Status: OPEN / verification required.

### F-HARNESS-PREFLIGHT-006 — Remote continuity checks are on the prompt critical path

Observed code:
- frank_prompt_inject.py invokes repo_truth_gate.py before every substantive prompt path.
- repo_truth_gate.py performs git fetch origin main with timeout up to 30 seconds and requires HEAD == remote.
- prompt path can also run materialization, work sync and delegation sidecars.

Benefit:
Strong freshness and fail-closed continuity.

Risk:
Conversation availability and tail latency are coupled to remote Git/network health even for non-consequential local cognition.

Research direction, not accepted change:
Test a two-tier gate:
- LOCAL_INTEGRITY gate always strict and synchronous.
- REMOTE_FRESHNESS lease/epoch with short bounded validity for read-only cognition.
- consequential writes/effects/authority transitions still require fresh remote/CAS confirmation.

This must be falsified against stale-head split-brain scenarios before adoption.

Status: HYPOTHESIS, not a recommended immediate relaxation.

## Proposed causal replay contract: TurnTraceEnvelope v1

A single turn/replay envelope should minimally bind:

Identity:
- trace_id
- turn_id
- session_id
- node_execution_id
- parent_trace_id / causal_parent_ids
- architecture_freeze_hash
- harness_build_hash

Canonical basis:
- source_repo_head
- semantic_epoch_before
- semantic_root_hash_before
- claygraph_epoch_before
- claygraph_root_hash_before
- program/config epoch ids

Inputs and nondeterminism:
- external_input_hash
- translation_receipt_id/hash
- Needle receipt id/hash
- model identity/checkpoint/LoRA/tokenizer/quantization
- sampler settings + seed
- wall-clock inputs only where semantically admitted
- environment fingerprint: OS, architecture, runtime/toolchain versions, relevant dependency hashes
- external API/tool input receipts
- explicit nondeterminism receipts for boundaries that cannot replay byte-identically

Causal stages:
- ordered stage_id list
- input/output semantic hashes per stage
- bypass/lesion/intervention receipts
- query/admission receipts
- ClayGraph route/Assembly refs
- CandidateSet + WorkspaceEpisode refs
- per-receiver GWT delivery/reconstruction/uptake/causal-use/outcome/reentry refs
- ClayReaderFrame hash
- raw model output hash
- canonicalized model output hash
- proposal/EffectIntent hash
- authority/resource/reservation/commit/outcome receipts

Post-state:
- semantic_epoch_after
- semantic_root_hash_after
- claygraph_epoch_after
- claygraph_root_hash_after
- dynamic Run ClayGraph delta hash
- status_snapshot_id/hash
- failures/repairs/retries
- latency/token/RAM/CPU/GPU/IO metrics

Replay class:
- EXACT_DETERMINISTIC
- DETERMINISTIC_UNDER_ENV_FINGERPRINT
- RECEIPT_BOUNDARY_NONDETERMINISTIC
- LIVE_EXTERNAL_NONREPLAYABLE_WITH_RECORDED_OUTCOME

## Status Snapshot v1

To eliminate status split-brain, status should be rendered from one immutable committed record per response boundary:

StatusSnapshot:
- snapshot_id
- generated_from_trace_id
- semantic_epoch
- semantic_root_hash
- source_repo_head
- now_text + basis refs
- next_text + basis refs
- node_group records + member counts/ids
- v0.1 gate vector + source hash
- active skill trigger + revision
- integrity state
- created_at
- snapshot_hash

Invariant:

rendered_status = pure_render(StatusSnapshot)

not

rendered_status = ad_hoc_reads(UnifiedDB, JSON files, current clock, fallback prose)

If the snapshot cannot be generated from verified state, the surface must say DEGRADED/UNKNOWN and carry the failure receipt identity.

## High-information tests

### T-STATUS-ATOMIC-1
Race/mutation test: change status_surface_state and milestone file between reads. Current renderer should be able to demonstrate a mixed snapshot; proposed snapshot renderer must not.

Falsifier of finding: prove current renderer already obtains both sources under one authoritative epoch/transaction boundary.

### T-STATUS-FAILCLOSED-2
Break/rename UnifiedDB or force schema/query failure. Expected proposed behavior: explicit DEGRADED/UNKNOWN. Any normal "session active / continue verified work" output is failure.

### T-STOP-ROOT-3
Run stop guard with repository sentinel absent/moved while hook code still executes. Expected proposed behavior: BLOCK with ROOT_UNVERIFIED. Acceptance of a generic structural pulse is failure.

### T-NODE-MULTIPLICITY-4
Create two active local endpoints and two active remote endpoints. Status snapshot must preserve member count and auditable identity while still presenting only Frank to Andreas.

### T-REPLAY-ROUNDTRIP-5
Freeze external input, architecture hash, environment fingerprint, model output, seeds and external receipts. Replay must reproduce exact architecture-relevant state hashes and Run ClayGraph delta. Any divergence must identify the first divergent stage.

### T-REPLAY-INTERVENTION-6
Hold all upstream inputs fixed and swap exactly one module output/lesion. Verify downstream delta is localized and causal ancestry remains explicit.

### T-DST-OUTSIDEIN-7
Run the same invariant family in two lanes:
- deterministic in-process/reference simulation
- non-deterministic compiled-binary/outside-in harness
Compare bug classes. Goal is not agreement but blind-spot discovery.

### T-PREFLIGHT-LEASE-8
Network partition/stale remote experiments for the two-tier freshness hypothesis. A read-only lease mode is admissible only if no stale worker can mint CURRENT truth, authority, commit, migration or protected Harness effect.

## Architecture implications

1. H-WP-11 TRACE-REPLAY should be treated as an oracle layer, not merely logging.
2. H-WP-17 Reference Release Audit should require status-snapshot atomicity and root-unresolved fail-closed tests.
3. H2 Clay Harness differential should compare TurnTraceEnvelope stage hashes and dynamic Run ClayGraph deltas, not only final state/user-visible text.
4. Environment fingerprint must be part of replay identity; seed alone is insufficient for all deterministic claims.
5. Deterministic simulation should be paired with a compiled/outside-in fault lane to catch simulation abstraction blind spots.
6. OpenTelemetry-style trace/span identifiers are useful as transport/observability context but must never become canonical truth or authority.

## Counterhypotheses / cautions

C1. A single envelope may become too large/expensive.
Mitigation/test: content-address stage payloads and store references/hashes in the envelope; measure state amplification.

C2. Strict root-unresolved blocking may reduce recoverability when only the sentinel file is damaged.
Mitigation/test: root can be independently anchored by hook code path + signed/hashed repository identity; recovery path must remain installer/Research-Entity-owned, not Frank self-repair.

C3. Atomic StatusSnapshot could become stale between generation and final output.
Mitigation: bind snapshot to the exact trace/semantic epoch and regenerate after any committed state change before response emission.

C4. Remote freshness lease could weaken the current fail-closed design.
This hypothesis remains NOT_SELECTED until stale-head/split-brain tests prove that read-only degraded cognition cannot create durable authority or truth.

## Research decisions

Recommended now:
- promote T-STATUS-ATOMIC-1, T-STATUS-FAILCLOSED-2 and T-STOP-ROOT-3 to near-term harness regression work;
- define TurnTraceEnvelope v1 before H1 implementation expands further;
- add environment fingerprint semantics to replay contract;
- design deterministic + outside-in dual testing lanes.

Not recommended yet:
- relaxing remote freshness on the prompt critical path. This remains an experiment until safety equivalence is demonstrated.

## Feedback targets

- harness: status/replay/release audit
- frank: status correctness and node continuity surface
- claycode: H2 differential trace schema must be expressible without semantic escape hatch
- claygraph: dynamic Run ClayGraph delta identity must bind to TurnTraceEnvelope
- gwt: per-receiver causal receipt ids become trace-linked
- emergenz: interventions become replay-addressable
- unifieddb: atomic StatusSnapshot and trace index persistence
- hyperposition: intervention/counterfactual identities become trace-addressable

## Research conclusion

The highest-value Harness improvement is not another broad module rewrite. It is to make the Harness self-measuring at causal granularity:

1. one atomic verified status snapshot per response boundary;
2. one fail-closed root/integrity path with no weak compatibility acceptance;
3. one content-addressed TurnTraceEnvelope binding state, model, environment, causal stages, authority/effects and dynamic ClayGraph deltas;
4. one deterministic replay lane plus one outside-in nondeterministic fault lane.

This would turn H1 from "a simulation that seems faithful" into a baseline that can actually falsify H2 and later one-module FRANK divergences.