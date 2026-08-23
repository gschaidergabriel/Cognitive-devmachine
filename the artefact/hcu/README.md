# EntityOS HCU — current-facing source root

This directory is the current-facing implementation root for **EntityOS HCU** primitives that are safe to introduce without destructively renaming historical/hash-bound `MicroEntity`, `Xeno`, `XCU`, `mini_*` or `MINI_*` compatibility surfaces.

It does **not** define a second product, entity, state authority, effect path, recovery ledger or competing HCU implementation. Existing legacy-named HCU code remains donor/compatibility material until a bounded fusion onto current `main` is admitted.

## Typed causal identity

`typed_canonical_v1.py` defines `ENTITYOS_TYPED_CANONICAL_JSON/v1`, an explicitly versioned typed canonicalization profile for identity-bearing Entry/HCU receipts.

It is deliberately narrower than general JSON and is **not** claimed to be a complete RFC 8785 JCS implementation. The current profile:

- binds its schema/version into each `canonical_sha256` preimage;
- rejects floating-point numbers; identity-bearing measurements must use explicit fixed-point integer fields;
- restricts integers to the exact IEEE-754 safe range;
- restricts structural object keys to a bounded ASCII domain so ordering is unambiguous across admitted runtimes;
- recursively sorts object keys and preserves array order;
- preserves Unicode string values without normalization;
- exposes strict JSON parsing that rejects duplicate object names and non-finite/non-integer number forms.

This is a causal/provenance identity mechanism only. It cannot mint canonical truth, grant permissions, admit model engines or authorize effects.

## Immediate integration gate

The current draft HCU reactive router already binds event, router-policy, engine-artifact and route-decision identities, but still declares a Python-local `json.dumps` hash profile. The next bounded fusion is to bind this EntityOS canonicalization schema into the Entry event, route and downstream inference receipt path, with threshold/measurement identity represented as explicitly scaled integers or else kept explicitly Python-local.

Cross-language identity remains **unproven** until the same admitted typed event is reproduced by an independent canonicalizer. Source/component evidence is not EntityOS/HCU runtime acceptance.
