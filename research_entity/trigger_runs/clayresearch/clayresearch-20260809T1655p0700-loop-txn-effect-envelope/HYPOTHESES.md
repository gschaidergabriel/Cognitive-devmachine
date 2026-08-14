# Loop Transaction Effect Envelope — Hypotheses

Status: OPEN / no promotion. Falsify by H1/H2 replay, compiler/runtime counterexample, or Ubuntu target measurement.

## G1 — 50 hypotheses
H01 commit binds exact decision read-set + current capability epoch/validity.  
H02 dependency-scoped validation preserves more useful concurrency than whole-state epochs.  
H03 revocation invalidates pre-revocation in-flight permits.  
H04 regrant at a new authority epoch requires a new decision binding.  
H05 EffectIntent may survive recurrence as proposal; executable permits should not.  
H06 local per-effect checks are insufficient for lossy source-to-sink composition.  
H07 transaction identity != authority identity; commit receipt joins them.  
H08 unrelated state churn should not invalidate a complete unchanged decision basis.  
H09 compiler analysis can extract many static decision dependencies.  
H10 dynamic/reflection/FFI unknown closure must widen dependencies or recompute.  
H11 typed local envelopes beat one global authority/stability controller for heterogeneous loops.  
H12 productive cycles can be safe if each external edge revalidates freshly.  
H13 stalled loops cannot retain permits merely because state delta is low.  
H14 overthinking changes recurrence control, never authority/truth semantics.  
H15 GWT ignition allocates compute, not permit lifetime.  
H16 outcome/re-entry updates later decisions, not authority.  
H17 effect-distinct Hyperposition alternatives retain separate dependency identities.  
H18 premature alternative collapse can hide confused-deputy/source-sink paths.  
H19 ClayGraph activation may aid dependency discovery but never authority.  
H20 loop/capability topology remains derived and epoch-bound.  
H21 UnifiedDB persists request, grant, decision, commit, outcome and re-entry distinctly.  
H22 authoritative conflicts require retry/recompute, not LWW.  
H23 state publication + external effect require atomicity or idempotent recoverability.  
H24 crash between effect and re-entry needs idempotency preventing double execution.  
H25 reversible/versioned operations can preserve recoverability cheaper than universal snapshots.  
H26 rebuildable caches may use weaker consistency if stale derivatives cannot authorize.  
H27 capability checks and protected information-flow checks are complementary.  
H28 child-code EffectiveEffects stays within the parent Clay contract.  
H29 opaque host resources are safer authority carriers than names/secrets.  
H30 capability-instance identity remains separate from deterministic program identity.  
H31 Ubuntu confinement needs layered host brokerage, not one assumed mechanism.  
H32 inherited/preopened descriptors need explicit lifetime/scope/revocation.  
H33 WIT resource ownership is useful representation, not authority proof.  
H34 WASI imports constrain ambient access only if host grants are actually narrow.  
H35 generic structured recurrence remains sufficient; no FRANK-specific loop syntax.  
H36 loop-carried values preserve static types; authority state remains explicit.  
H37 adaptive recurrence optimizes verified marginal utility/cost under freshness/resource/recovery constraints.  
H38 loop-controller failure != semantic invalidity != authority invalidity.  
H39 read-set size has a safety/concurrency frontier.  
H40 static dependency analysis should be differential-tested against runtime-observed dependencies.  
H41 fuzz must cover omission, revoke/regrant, queue delay/reorder and worker handoff.  
H42 UNKNOWN/CONFLICT in effect-critical dependencies forces deny/recompute/escalate.  
H43 adaptive visual learner promotion/rollback uses the same envelope discipline.  
H44 familiarity/confidence changes routing but never extends authority.  
H45 H1 whole-ledger base_epoch CAS is sound but potentially over-conservative.  
H46 object/invariant-group versions can refine global CAS while preserving replay safety.  
H47 semantic epochs and capability epochs advance independently and join only where relevant.  
H48 LoopDynamicsReadout records commit/abort/recompute reason but never authorizes.  
H49 Safe-Effect utility metrics include unnecessary abort/recompute cost.  
H50 smallest current BASE addition is runtime ABI/compiler metadata/fuzz tests, not new syntax.

## Counterhypotheses
C-A deterministic single-thread scheduling is sufficient for v0.1.  
C-B global base_epoch CAS is cheap enough that scoped versions are not worth complexity.  
C-C unforgeable handles alone solve freshness.  
C-D stale-decision races are negligible in real H1 workloads.  
C-E conservative invalidation is acceptable because effects are rare.  
C-F loop-of-loops adds no implementation value beyond queues/transactions/capabilities.

## G2 — transformed
G2-01 dependency-scoped serializability binds decision dependencies + authority epoch + budget, not one world epoch.  
G2-02 revoke/regrant forks authority lineage even if nominal rights match.  
G2-03 recurrence lowering and effect-dependency extraction should be validated together.  
G2-04 semantic program, decision snapshot, authority grant and physical resource are distinct identities.  
G2-05 host broker is a typed contract over replaceable Ubuntu/Linux mechanisms.  
G2-06 permit lifetime is a measurable attack-surface/recompute-cost tradeoff.  
G2-07 H1 should differential-test global CAS against object/invariant-group versions.  
G2-08 authority-flow controls join GWT/Hyperposition only as negative-control metadata.  
G2-09 productive cycles require a fresh envelope at every external effect edge.  
G2-10 protected source label + sink policy + declassification/grant join commit validity where applicable.  
G2-11 child code receives only preauthorized handles/imports plus adversarial closure tests.  
G2-12 no semantic promotion until H1/H2 produces a minimized executable inadequacy counterexample.
