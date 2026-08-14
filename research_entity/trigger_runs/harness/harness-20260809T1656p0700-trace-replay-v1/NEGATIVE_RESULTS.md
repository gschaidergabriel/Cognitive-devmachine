# Harness H-WP-11 Trace/Replay — Negative Results and Limits

Run: `harness-20260809T1656p0700-trace-replay-v1`

## NR-H11-001 — Existing reviewed baseline does not yet establish one complete replay oracle

The inspected current Frank baseline contains useful state epochs/root hashes, prompt cycles, query receipts, state injections, attention/receiver receipts, outcomes, snapshots and ClayGraph materialization. The reviewed `frank_state_runtime_impl.py` surface contains no replay function, and the reviewed schemas do not by themselves form one frozen `TurnTraceEnvelope` binding all required causal identities.

This is **not** a claim that no replay implementation exists anywhere in the repository. It is a scoped negative result: the reviewed current release-critical surfaces do not establish the complete H-WP-11 oracle required by the Harness contracts.

Falsifier: locate and execute a current complete replay implementation that binds the same architecture-relevant state, loop, GWT, graph, authority/effect and status basis identities.

## NR-H11-002 — Final-state equality is insufficient as the sole H1/H2 differential oracle

Constructed traces can share the same final basis while differing at an intermediate semantic stage. `compare_traces()` therefore compares a representation-normalized semantic projection and identifies the first divergence rather than treating identical terminal hashes/user-visible output as sufficient.

Evidence class: local synthetic mechanism test.

Falsifier: a frozen H1/H2 corpus demonstrates that terminal-state comparison catches every material intermediate causal divergence relevant to later behavior, authority, recovery and experiments.

## NR-H11-003 — Seed-only deterministic identity is too weak as a general assumption

FoundationDB's primary debugging guidance states that deterministic simulation failures may reproduce only under the same OS type and build environment. The present validator therefore rejects deterministic replay claims lacking an explicit environment fingerprint.

This is engineering precedent, not proof that every FRANK replay depends on every environment field.

Falsifier: controlled FRANK experiments establish a smaller invariant replay basis across environment changes.

## NR-H11-004 — One deterministic simulator lane is not sufficient defense-in-depth evidence

TigerBeetle documents deterministic simulation testing alongside a deliberately non-deterministic full-system harness (Vortex) to cover different failure surfaces. For FRANK this supports, but does not prove, a dual-lane test strategy.

Status: OPEN engineering transfer hypothesis.

## NR-H11-005 — Current run cannot produce H1 evidence

The program is still in `BASE_CLAYCODE_RELEASE`; H1 is blocked. This run executed only an architecture-generic host-language validator on a hosted Linux sandbox, not the Andreas Ubuntu target, not live Frank, and not a frozen Reference Harness.

Therefore:
- no H1 work package is COMPLETE;
- no Reference Harness gate advances;
- no live-FRANK claim is promoted;
- no ClayCode/H2 equivalence claim is made.

## NR-H11-006 — Official repository-local preflight was not executed

The hosted ChatGPT worker had GitHub connector access but no checked-out Clay repository execution surface. `tools/research_interconnect_preflight.py` was therefore not executed. The run instead materialized a fail-closed manual `INTERCONNECT_MANIFEST.json` from verified current GitHub reads and disclosed this limitation.

The official preflight should be run by a repository execution organ before treating this package as H1 release evidence.
