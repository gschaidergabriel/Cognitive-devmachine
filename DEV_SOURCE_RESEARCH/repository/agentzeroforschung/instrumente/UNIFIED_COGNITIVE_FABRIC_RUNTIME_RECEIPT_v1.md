# UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1 — compatibility entry point

Status: COMPATIBILITY ONLY / NO INDEPENDENT SCHEMA AUTHORITY

## Canonical authority

There is exactly one semantic validator and one current JSON contract for `UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1`:

- ClayCode law: `research_entity/claycode/contracts/UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT_V1.clay`
- canonical host validator: `tools/validate_unified_cognitive_fabric_receipt_v1.py`
- canonical regressions: `tests/test_unified_cognitive_fabric_receipt_v1.py`

Required law:

```text
ONE_RUNTIME_RECEIPT_AUTHORITY = true
SAME_SCHEMA_NAME + DIFFERENT_VALIDATOR_SEMANTICS = FORBIDDEN
COMPATIBILITY_ENTRYPOINT != SECOND_SCHEMA_AUTHORITY
```

The historical instrument in this directory previously carried a different field layout under the same schema name, including `receipt_version`, `runtime.entity_generation`, `identity.zero_digest`, `fabric.*`, `validation.*`, and `execution_policy.*`. That parallel layout is **superseded** and must not be used to mint, validate, migrate, or interpret current v1 receipts.

Git history preserves the old source for research provenance. It is intentionally not reproduced here because keeping two live field specifications under the same v1 name recreates the ambiguity this convergence closes.

## Compatibility behavior

`agentzeroforschung/instrumente/validate_unified_cognitive_fabric_receipt_v1.py` is now a thin file-oriented compatibility wrapper around the canonical validator. It contains no independent admission rules.

- canonical current receipts are delegated to `tools/validate_unified_cognitive_fabric_receipt_v1.py`;
- the historical `validate_receipt(...) -> list[str]` helper remains only as an interface adapter;
- the historical file-path CLI remains only as an I/O adapter;
- old parallel-v1 shapes fail closed (`SCHEMA_MISMATCH`) rather than being silently translated;
- no compatibility code may reinterpret an old v1 receipt into a current v1 receipt without an explicitly versioned migration contract.

This intentionally chooses **fail-closed convergence**, not lossy field translation. The two old/current layouts are semantically different enough that automatic conversion could manufacture provenance, execution, authority, or epistemic claims that were never present.

## Evidence / runtime-credit boundary

This convergence is a source-authority repair. It does not claim:

- exact Ubuntu/AgentZero runtime execution;
- bundled ~0.8B model execution or quality;
- J-Space calibration;
- Whole-GWT production validity;
- Claude Code adapter runtime PASS;
- provider execution/admission;
- canonical semantic promotion;
- whole Mini Entity acceptance.

Exact runtime credit still requires the current canonical receipt to be emitted by an actually-started exact-source admitted runtime and chained to the required boot/source/artifact evidence.

## GO discriminator that exposed the defect

Macrocycle: `go-5f5233390b4a446591337d08c6b645d8`.

Exactly one bounded unusual discriminator for this macrocycle:

`DUAL_UCF_V1_AUTHORITY_DIVERGENCE`

Observed source condition before repair:

1. `tools/validate_unified_cognitive_fabric_receipt_v1.py` required top-level `schema` and its current nested field model.
2. this directory's validator required top-level `receipt_version` and a materially different nested field model.
3. both called themselves `UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1`.
4. therefore a receipt could be valid under one live v1 authority and invalid under the other.

Result:

`COUNTERHYPOTHESIS("one v1 validator authority already exists repository-wide") = REFUTED_AT_SOURCE`

Repair strategy:

`MERGE_SEMANTIC_AUTHORITY -> canonical tools validator; RETAIN legacy path only as delegating compatibility I/O.`

No provider network, secret lookup, paid execution, model run, or training was performed by this discriminator.
