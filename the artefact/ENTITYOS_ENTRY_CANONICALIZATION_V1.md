# EntityOS Entry Canonicalization v1

Status: **SOURCE/MECHANISM CANDIDATE**. This contract does not grant EntityOS/HCU runtime acceptance.

## Purpose

`ENTITYOS_ENTRY_CANONICAL_JSON_JCS_SUBSET/v1` defines the single hash boundary for `ENTITYOS_ENTRY_PACKET/v1` before HCU cognition. The goal is to prevent Python-local JSON serialization from being mistaken for a cross-language causal identity contract.

The profile is deliberately narrower than general JSON Canonicalization Scheme (RFC 8785/JCS). RFC 8785 requires invariant JSON serialization for cryptographic hashing, constrains data to I-JSON, uses deterministic object-property ordering, and uses ECMAScript-compatible primitive serialization. This EntityOS profile admits only a subset that can be checked deterministically without implementing the full general-number surface.

## Admitted identity domain

The hashed Entry basis contains only:

- fixed ASCII object property names owned by `ENTITYOS_ENTRY_PACKET/v1`;
- Unicode strings that are valid strict UTF-8 after Entry admission;
- `null`;
- arrays whose order is already fixed by the Entry admission contract;
- non-negative integers in `0..2^53-1`.

Not admitted in v1 identity material:

- floating-point values;
- integers above the IEEE-754/ECMAScript safe-integer boundary;
- NaN or Infinity;
- dynamic object keys with unspecified ordering semantics;
- unpaired Unicode surrogates;
- non-ASCII capability tokens whose cross-language normalization/sort semantics are not explicitly defined.

No Unicode normalization is performed. Entry admission may perform its own documented semantic normalization, such as timestamp normalization and capability-set deduplication, before the canonical identity basis is constructed.

## Identity law

The canonicalization schema identifier is itself part of the hashed basis:

`canonicalization_schema = ENTITYOS_ENTRY_CANONICAL_JSON_JCS_SUBSET/v1`

Then:

`entry_sha256 = SHA256(UTF8(canonical_json(admitted_entry_basis)))`

A future broader or incompatible canonicalizer MUST use a new schema identifier. It MUST NOT silently reuse v1 digests.

## Cross-language discriminator

The repository contains two independent implementations over the same normalized Entry basis:

- Python production candidate: `entry_fabric_v1.py`;
- Node.js reference discriminator: `test_entry_fabric_canonicalization_v1.mjs`.

Reference vector digest:

`d6f14d8792c1653b19c95ec4f39653a671772f809e238c8e8e91a19df26ea5de`

A bounded isolated run on Python 3.13.5 and Node.js 22.16.0 produced the same digest. This supports the restricted profile mechanism only. It is not proof for arbitrary JSON, a future heterogeneous runtime, the HCU route consumer, or whole EntityOS.

## HCU handoff requirement

HCU routing should consume the admitted Entry identity plus its canonicalization schema/version rather than independently re-canonicalizing the raw ingress event under a second JSON contract. Downstream route/inference receipts should bind or echo the same Entry identity and canonicalization schema alongside router policy and resolved engine identity.

If Entry identity cannot be verified under an admitted canonicalization schema, cognition admission fails closed.
