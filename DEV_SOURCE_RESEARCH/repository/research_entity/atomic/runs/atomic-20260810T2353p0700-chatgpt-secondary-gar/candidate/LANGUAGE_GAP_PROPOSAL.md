# GAR-001 ClayCode language-gap proposal

## Minimal gap

Current G9 surface grammar has generic type parameters, laws and invariants, but the observed grammar does not provide an enforceable notion of:

1. a fresh generative brand whose identity cannot be named outside an acquisition scope;
2. affine/linear or borrowed capability values;
3. a `nonserializable` resource kind;
4. an effect region that prevents a validated permit from escaping before the external effect is performed.

GAR therefore MUST NOT be claimed as already expressible merely by writing `K` as a generic type parameter.

## Smallest proposed TypedIR delta

Prefer a TypedIR-level primitive before adding new surface syntax:

- `FreshBrand K @ scope_id`
- `Resource<T, multiplicity=AFFINE, serialization=FORBIDDEN>`
- `Borrow<T, region=K>`
- `EffectScope<K, effect_class>`
- escape check: values mentioning fresh K cannot outlive its scope unless explicitly downgraded to a non-authoritative durable shadow
- provider lowering rule: `runtime_effect` is legal only while the matching `EffectScope<K>` is live

A later surface syntax can lower to these forms after the semantics are experimentally justified.

## Falsifier

Do not add the primitive if:
- opaque runtime capability + scoped provider callback + ordinary current ClayCode type/effect checks achieves the same defect prevention under a mutation corpus;
- static escape analysis creates unacceptable false positives;
- the primitive materially complicates compiler/runtime without reducing real integration defects;
- the strict effect route cannot be made the only production lowering path.

## Required next experiment

Implement a shadow TypedIR checker only. Generate valid and adversarial effect programs, including stale region, same-epoch execution rebinding, capability copy/escape/serialization, detached precommit receipt, legitimate unknown-outcome reconciliation, and ordinary non-effect cognition. Compare GAR typing against the strongest conventional API/linter baseline before changing canonical ClayCode.
