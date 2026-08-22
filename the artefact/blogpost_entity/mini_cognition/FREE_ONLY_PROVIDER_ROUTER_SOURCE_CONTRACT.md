# FREE_ONLY provider-router source contract — candidate

Status: **SOURCE/ARCHITECTURE CANDIDATE; NOT EXECUTABLE ACCEPTANCE**  
Date: 2026-08-22  
Scope: exported AgentZero provider/fallback routing (`agentZero/code/produkt/bahnen.py` + `bahnen.json`) under the active FREE_ONLY supervisor boundary.

## Observed authority defect

`agentZero/code/produkt/bahnen.json` declares itself a repeatable derived export and names `/opt/clayverse/werkzeug/verdrahtung.py` as the source of truth. Repository search at the bound source head did not resolve that generator/source file. Therefore the repository currently cannot reproducibly add or audit provider cost-class metadata at the declared source of truth.

Directly hand-editing the derived export to label providers FREE/PAID/SUBSCRIPTION would create a second provider-policy truth and is not an admitted repair.

## Required source repair

Before the exported fallback chain can satisfy `FREE_ONLY_FALLBACK_CHAIN_RECEIPT/v1`, the declared generator/source must become repository-bound (or the repository must explicitly replace it with one canonical source).

That canonical source must emit a mandatory machine-readable field for every provider access:

```text
cost_class = FREE | PAID | SUBSCRIPTION | UNKNOWN
```

Rules:

1. Missing, malformed, stale, or unproven cost class collapses to `UNKNOWN`.
2. In FREE_ONLY, only exact `FREE` is admissible.
3. `PAID`, `SUBSCRIPTION`, and `UNKNOWN` are rejected/skipped before **any** credential/key lookup and before **any** network I/O.
4. Provider/model names, display labels such as `(frei)`, historical successful calls, quota counters, API-key presence, or absence of a visible invoice do not mint `FREE`.
5. A fallback chain may continue from a rejected non-free/unknown candidate only to another candidate whose machine-readable class is explicitly `FREE`.
6. The same admission predicate must guard both selection (`waehle`) and actual execution (`_ein_versuch`) so a direct/internal call cannot bypass the selector.
7. The generated `bahnen.json` and runtime router must carry source identity (source path/revision or digest) sufficient to prove they were generated from the same admitted provider registry.
8. Cost-class evidence is mutable external-state evidence. Every positive `FREE` classification needs an explicit provenance/validity record; expiration or ambiguity returns it to `UNKNOWN`.

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

This document does **not** classify any existing provider as FREE. It does not grant provider capability, network authority, paid usage, or training authority. It only closes the architectural ambiguity around where provider cost classification must live and how the exported fallback router must consume it.

Promotion requires: repository-bound canonical provider source -> explicit evidence-backed cost classes -> deterministic export -> router admission before secrets/network -> actually-started authorized isolated regression with exact source identity -> durable `FREE_ONLY_FALLBACK_CHAIN_RECEIPT/v1`.
