<!-- RAE_META
{"packet_id":"KMP-CLAY-SAFE-EFFECT-GEOMETRY","title":"Safe-Effect Geometry / Non-Damaging Semantic Action Space","domains":["clay","claycode","frank","unifieddb","hyperposition","security"],"topics":["prompt injection","effect systems","capabilities","recoverability","authority non-amplification","foreign-code closure","alignment"],"epistemic_class":"PROJECT_OWNER_MANDATED_RESEARCH_AXIS_WITH_OPEN_FALSIFIABLE_HYPOTHESES","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T23:05:00+07:00","source_refs":["research_entity/global/CLAY_SAFE_EFFECT_GEOMETRY_RESEARCH_FOUNDATION.md","research_entity/triggers/CLAY_RESEARCH_PROTOCOL.md"],"verification_required":true}
RAE_META -->

# Safe-Effect Geometry / NDSAS

## Core research delta

Clay research now permanently studies whether a Clay-native 4B can remain broadly capable at programming and system operation while its executable semantic action space structurally excludes, bounds, reverses or externally gates protected-state damage.

The research requirement is fixed by project-owner direction. The claimed alignment/safety benefit remains OPEN and falsifiable.

## Candidate laws

For model-originated transitions, test:

- **recoverability monotonicity:** protected prior state remains reconstructible/versioned where required;
- **authority non-amplification:** information/model output cannot mint stronger execution capability;
- **protected information-flow confinement:** secret/protected values only reach allowed typed sinks;
- **resource-budget boundedness:** CPU/RAM/disk/network/process/API use remains capability-bounded;
- **foreign-code closure:** generated Python/Bash/C/Rust/WASM/FFI/tool/subprocess effects cannot exceed the parent Clay effect contract.

## Capability-preserving effect model

Do not achieve safety by making the model inert. Research constructive/reversible operations such as CREATE, DERIVE, VERSIONED_WRITE, ATOMIC_REBIND, SUPERSEDE, RETIRE_FROM_ACTIVE_VIEW, QUARANTINE, REVOKE, ROLLBACK, NEW_EPOCH, SANDBOX_EXECUTE and REVERSIBLE_DEPLOY.

Separate `Persistent<T>`, `Rebuildable<T,Witness>`, `Ephemeral<T>`, `Secret<T>` and `External<T>` so scratch/build/test data can still be reclaimed normally.

Irreversible effects remain conceptually representable but should be mediated through an external irreversibility broker; model proposal must not self-authorize the commit.

## Prompt-injection implication

The strongest target is not perfect malicious-intent recognition. It is:

`compromised intent != expanded authority != reachable protected damage`

A prompt injection may alter reasoning or proposals while leaving the executable effect envelope unchanged.

## Two hypotheses kept separate

1. **Systems containment:** effect algebra + complete runtime mediation reduces reachable system damage.
2. **Cognitive alignment:** native training in constructive/reversible action primitives changes solution-policy geometry and reduces destructive proposals even before runtime rejection.

The second requires matched-model experiments and is not implied by the first.

## Mandatory next experiment family

Matched 4B baseline-vs-Safe-Effect Clay, crossing normal programming/system tasks with direct/indirect prompt injection, poisoned memory/tool output and generated-code escape attempts. Measure ordinary utility, destructive-proposal rate, compiler rejection, capability escalation, actual reachable damage, recovery and resource use.

## Hard boundary

Removing destructive words alone is NOT the mechanism. If generated foreign code or ambient OS authority can recover the same destructive effect, the Safe-Effect hypothesis has failed at the mediation layer.
