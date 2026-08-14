## ATOMIC source
`research_entity/atomic/runs/20260810T2304p0700-chatgpt-secondary-psw-possibility-weave/`

## Decision
PSW-001 (`Possibility State Weave`) is **not** promoted as a new architecture. The synthetic benchmark found that a conventional immutable base + sparse branch overlays + exact read-signature memoization reproduces PSW's useful sharing with less/equal architecture.

## Durable target obligation
When real Hyperposition/ACEF unresolved branch state exists, benchmark and implement physical representation as a replaceable policy rather than unconditional N full cognitive-state copies.

Required invariants:
- physical storage deduplication must never merge `hypothesis_id`, provenance, entity/version, state/base epoch or branch revision;
- branch native identity remains `self.root`, not the human surface name `Frank`;
- cross-branch computation reuse is allowed only for an exact current `PURE` transition with a complete/conservative material read set;
- unknown/dynamic material reads disable reuse;
- external reads/writes, security-sensitive operations and any effect-authority path are never multi-branch executed from unresolved alternatives;
- restart/downtime cannot fabricate branch transitions that were not persisted;
- representation conversion must be observationally exact and receipted.

## Executable counterexample motivating the ClayCode obligation
Two branches were equal on declared field `a`, different on field `b`, and a pure transition truly read both. Memoization keyed only on `a` shared the result and produced one wrong branch output. Exact `{a,b}` signature eliminated the error.

Therefore `PURE` without a sound material read/effect summary is insufficient for cross-alternative reuse.

## Measured synthetic envelope
168 scaling cells over 64/256/1024 state fields, 4..1024 branches, 0..50% divergence, read sets 4/16.

Representative F=1024/N=256/read16 six-seed medians:
- 0% divergence: 256x sharing, overlay-memo ~0.239x FULL_COPY time;
- 1%: ~6.83x sharing, ~0.403x time;
- 5%: ~1.76x sharing, ~0.751x time;
- 10%: ~1.20x sharing, ~0.979x time;
- 25%: ~1.01x sharing, ~1.169x time;
- 50%: 1x sharing, ~1.194x time.

A separately seeded 48-cell policy probe showed a simple read-signature-density selector could closely track the faster measured path, but the synthetic threshold is **not** a production constant.

## ACEF integration law
A concurrent ATOMIC candidate ACEF already represents hypothesis branches as epoch/identity/lease-bound `SemanticDelta` sets. If ACEF survives its own research, apply this issue as ACEF/Hyperposition physical/runtime policy; do not create a second PSW branch-state subsystem.

## Real acceptance test
On current Frank target VPS, once real branch traces exist, compare:
1. independent materialized branch states/execution;
2. sparse deltas/overlays;
3. sparse deltas + exact read-signature memoization;
4. actual admitted ACEF/Hyperposition representation.

Measure exact reconstruction, false semantic merge, stale/replay rejection, CPU, RSS, serialization bytes, p50/p95/p99 latency, signature overhead, transition compute cost, representation conversion cost and held-out policy regret.

No training authorization, no effect authority, no Harness mutation, and no PSW architecture promotion are implied.