# ATOMIC — GAR-001 Generative Authority Region

## Final verdict

**GAR-001 is not promoted as a Frank runtime architecture.** The strongest conventional scoped-capability baseline matches GAR on all eight encoded runtime authority/recovery scenarios. That counterhypothesis survives and is currently the dominant runtime explanation.

GAR remains useful only as a **ClayCode language-gap candidate**: it asks whether Frank's recurrent execution/effect-authority bugs can be moved from runtime/API discipline into the type system, so illegal authority states cannot be represented by well-typed ClayCode.

## Fresh problem

The selected problem was deliberately not another effect-fence implementation. Fresh GO work already converged on a gate-issued live capability, immutable generation binding, provider-commit serialization and reconciliation-only outcome handling. Current target-negative evidence has also shown that copied generation scalars can piggyback on a legitimate holder in a raw-field candidate and that snapshot restore can resurrect an old DB-local generation.

The recurring distinction is therefore:

`provenance identity != authority possession`

The remaining gap explicitly called out in current research is that ClayCode compiler/type-effect/lowering has not proved that the strict authority route is the only reachable production effect route.

## Candidate

GAR introduces a fresh generative execution-worldline brand `K`.

- `LiveExecutionCapability<K>` is gate-issued, live, nonserializable and non-reconstructible.
- `EffectReservation<K>` may only be started by a matching live `Capability<K>`.
- persistence stores only a `DurableAuthorityShadow<K>` containing provenance/digest information; the shadow is never authority.
- execution turnover, restart or restored lineage creates a fresh K.
- provider mutation is not preceded by a detachable PASS receipt; it executes inside an `EffectScope<K>`.
- outcome evidence is intentionally separable from K so unknown provider outcomes can be reconciled after K has died without transferring retry authority.

## External collision

The broad ingredients are known. Chubby provides lock-generation sequencers. etcd treats restore revision rollback as a new-lineage problem. ST and GhostCell show generative/branded permission identities. Linear/affine type systems track resources and I/O protocols. Capability systems use unforgeable possession. Recent agent-safety work tracks effect capabilities in the programming language.

Therefore GAR does not claim invention of fencing, capabilities, generative brands, affine resources or scoped effects. The strongest defensible novelty class is `NOVEL_COMBINATION_CANDIDATE`, and even that is Frank/ClayCode-specific.

## Executable discriminator

A deterministic Python reference model compared:

1. V14 unbound;
2. exact durable tuple;
3. tuple + nonrollback incarnation;
4. opaque live capability with detached precheck;
5. conventional scoped capability;
6. GAR runtime proxy.

The eight encoded scenarios were normal current effect, stale epoch turnover, same-epoch execution rebinding, snapshot rollback resurrection, copied persistent tuple, serialized capability resurrection, provider-precheck turnover, and unknown-outcome reconciliation after turnover.

Violation counts were:

- V14 unbound: 6/8;
- exact durable tuple: 4/8;
- tuple + nonrollback incarnation: 3/8;
- opaque live capability + detached precheck: 1/8;
- conventional scoped capability: 0/8;
- GAR: 0/8.

The decisive result is the tie at zero between the strongest conventional baseline and GAR. This directly supports the strongest counterhypothesis and prevents runtime promotion.

The local Python proxy median was about 131.2 ns/op for GAR versus 121.1 ns/op for conventional scoped capability, about 1.083x GAR/conventional. This is interpreter microbenchmark proxy noise/overhead, not production performance evidence, and supplies no reason to prefer GAR.

## Static proxy

A deliberately small GAR checker then tested programs that:

- perform a normal current effect;
- use a stale brand after turnover;
- rebind execution in the same epoch;
- serialize authority;
- return/escape authority;
- copy authority;
- detach a precheck permit and use it after release;
- reconcile old outcome evidence.

It accepted the two intended legal shapes and rejected the six authority-misuse shapes. A repeated 100,000-program corpus ran at roughly 1.61 million tiny programs/s in the local Python checker.

This does **not** establish ClayCode compiler safety. It establishes only that the proposed rules are precise enough to implement and that they do not inherently forbid post-turnover evidence reconciliation.

## ClayCode language gap

The observed G9 grammar supports generic type parameters, laws, invariants and effect-related declarations, but no observed primitive proves generative freshness, affine/nonserializable capability use or non-escaping effect regions. Merely writing a generic `K` would therefore be fake expressibility.

The smallest proposed experiment is at TypedIR, not grammar:

- `FreshBrand`;
- affine `Resource`;
- `serialization=FORBIDDEN`;
- `Borrow`/region relation;
- `EffectScope`;
- escape checking;
- lowering rule that permits `runtime_effect` only under the matching scope.

No new ClayCode surface syntax should be added until this defeats the strongest conventional type/effect/API/linter baseline.

## Strongest counterhypothesis

The strongest counterhypothesis is **supported at the runtime-model level**:

> opaque gate-issued live capability + nonrollback incarnation + provider callback/critical section can provide the same runtime properties without a new generative type primitive.

This is consistent with current PR204/217 direction. GAR therefore cannot justify replacing that runtime architecture.

The remaining research question is narrower: does a type-system primitive prevent enough future integration defects to justify compiler complexity?

## Relation to fresh UnifiedDB work

During the ATOMIC cycle, UnifiedDB advanced with a revocable RouteValidityCertificate/ShadowRiskSentinel design for learned accelerators under distribution shift. That work is conceptually related only in the abstract idea that validity can expire or be revoked. It is not authority-equivalent: statistical route validity must never become effect authority, while GAR concerns deterministic possession of current execution/effect authority. No architecture merge is proposed.

## Integration status

No target product code was changed by this ATOMIC run. No effect authority was minted. No canonical architecture promotion is claimed. No final training is authorized.

GAR is routed only to:

- F-V01-02: ClayCode TypedIR/type-effect/compiler shadow experiment;
- F-V01-09: compile-time non-bypass test for the strict effect route;
- F-V01-13/recovery: mutation corpus for restart/restore authority escape.

GWT, Hyperposition truth semantics, ClayGraph authority, UnifiedDB schema, Digital Retina/MVC, memory/reward/goals and final model training receive NO_CHANGE from GAR.

## Next highest-information falsifier

Build two shadow compiler paths over the exact same current effect candidate:

A. strongest conventional path: opaque Gate-issued capability + scoped provider callback + ordinary ClayCode type/effect checks and a purpose-built linter;

B. GAR TypedIR path: generative brand + affine/nonserializable capability + effect scope.

Generate a mutation corpus that attempts constructor forgery, copied lease, serialized authority, stale generation, same-epoch execution rebinding, detached precommit receipt, alternate lowering path, legacy V14 bypass, snapshot restore resurrection and legal post-turnover reconciliation.

Measure unsafe mutants rejected before execution, false-positive rate on valid code, typecheck/compile latency, TypedIR size, compiler implementation delta, runtime overhead, number of runtime checks removable if any, target-VPS fault outcomes after lowering, and recovery/replay behavior.

**Kill GAR if the conventional path matches rejection coverage and maintainability with less complexity.**

That is the current highest-information experiment.
