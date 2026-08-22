# FREE_ONLY provider-router source contract — candidate

Status: **SOURCE/ARCHITECTURE CANDIDATE; NOT EXECUTABLE ACCEPTANCE**  
Date: 2026-08-22  
Scope: exported AgentZero provider/fallback routing (`agentZero/code/produkt/bahnen.py` + `bahnen.json`) under the active FREE_ONLY supervisor boundary.

## Observed authority defect

`agentZero/code/produkt/bahnen.json` declares itself a repeatable derived export and names `/opt/clayverse/werkzeug/verdrahtung.py` as the source of truth. Repository search at the bound source head did not resolve that generator/source file. Therefore the repository currently cannot reproducibly add or audit provider cost-class metadata at the declared source of truth.

Directly hand-editing the derived export to label providers FREE/PAID/SUBSCRIPTION would create a second provider-policy truth and is not an admitted repair.

## Existing donor — reuse, do not reinvent

Open historical PR #232 already contains a strong bounded donor contract in `research_entity/global/FREE_API_EXECUTION_POLICY.json` plus `research_entity/runtime/free_api_provider_runtime.py`:

- default monetary budget is zero;
- Together is hard-denied;
- a configured key is capability evidence, **not** proof of quota/billing state;
- NVIDIA has explicit dated developer-endpoint zero-cost evidence with source URLs and scope;
- non-NVIDIA providers require explicit host-side zero-cost attestation before routing unless an officially documented free developer endpoint is bound;
- provider endpoint/credential identity is constrained before authenticated network use.

That donor is **not current canonical policy**: it remains in an old open PR and is framed for the legacy Frank v0.1 runtime. Its useful evidence schema and pre-network admission semantics should be fused into the current provider registry rather than copied wholesale or treated as current authority.

This means the missing piece is narrower than inventing a new cost policy: the current exported Bahnen registry lacks a repository-bound canonical source that can carry equivalent evidence-backed cost classification into the active router.

## Required source repair

Before the exported fallback chain can satisfy `FREE_ONLY_FALLBACK_CHAIN_RECEIPT/v1`, the declared generator/source must become repository-bound (or the repository must explicitly replace it with one canonical source).

That canonical source must emit a mandatory machine-readable field for every provider access:

```text
cost_class = FREE | PAID | SUBSCRIPTION | UNKNOWN
```

Recommended evidence envelope, adapted from the PR #232 donor:

```text
cost_evidence = {
  checked_at,
  claim,
  sources,
  scope,
  counterhypothesis,
  valid_until? / recheck_policy?
}
```

Rules:

1. Missing, malformed, stale, or unproven cost class collapses to `UNKNOWN`.
2. In FREE_ONLY, only exact `FREE` is admissible.
3. `PAID`, `SUBSCRIPTION`, and `UNKNOWN` are rejected/skipped before **any** credential/key lookup and before **any** network I/O.
4. Provider/model names, display labels such as `(frei)`, historical successful calls, quota counters, API-key presence, or absence of a visible invoice do not mint `FREE`.
5. A fallback chain may continue from a rejected non-free/unknown candidate only to another candidate whose machine-readable class is explicitly `FREE`.
6. The same admission predicate must guard both selection (`waehle`) and actual execution (`_ein_versuch`) so a direct/internal call cannot bypass the selector.
7. The generated `bahnen.json` and runtime router must carry source identity (source path/revision or digest) sufficient to prove they were generated from the same admitted provider registry.
8. Cost-class evidence is mutable external-state evidence. Every positive `FREE` classification needs explicit provenance/validity; expiration or ambiguity returns it to `UNKNOWN`.
9. A configured credential remains capability evidence only. It must never promote UNKNOWN/PAID/SUBSCRIPTION to FREE.
10. Existing PR #232 evidence may be reused only after freshness/scope verification against the current provider endpoint and current owner/supervisor policy.

## Cheapest deterministic regression after source repair

No provider contact is required to prove the boundary mechanism:

- construct a fallback order `[PAID, SUBSCRIPTION, UNKNOWN, FREE]`;
- install tripwires on credential lookup and socket/network creation;
- verify the first three candidates are rejected without firing either tripwire;
- verify only the explicit `FREE` candidate is allowed to reach credential lookup;
- repeat with all candidates non-free/unknown and require fail-closed `BahnErschoepft` with zero credential/network touches;
- call the execution method directly with a blocked candidate and require the same pre-secret/pre-network rejection.

These are deterministic safety regressions, not an unusual experiment.

## Acceptance boundary

This document does **not** classify any existing provider as FREE. It does not grant provider capability, network authority, paid usage, or training authority. It closes the architectural ambiguity around where provider cost classification must live, identifies an existing evidence-schema donor, and defines how the exported fallback router must consume current admitted classification.

Promotion requires: repository-bound canonical provider source -> fresh evidence-backed cost classes -> deterministic export -> router admission before secrets/network -> actually-started authorized isolated regression with exact source identity -> durable `FREE_ONLY_FALLBACK_CHAIN_RECEIPT/v1`.
