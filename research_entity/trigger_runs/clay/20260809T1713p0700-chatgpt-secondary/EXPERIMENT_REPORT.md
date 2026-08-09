# Empirical / Executable Research Report

Run: `20260809T1713p0700-chatgpt-secondary`  
Trigger: `clayresearch`  
Parent canonical: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## EXP-CR-001 — G9 admitted spec vs admitted grammar static conformance

**Class:** STATIC_CONFORMANCE_RESEARCH_EVIDENCE  
**Target:** BASE ClayCode CC-WP-01/02  
**Inputs:** `CLAYCODE_G9_FUSION_SPEC_V3.clay`, `grammar.ebnf`, parent V2 and dialect registry.

Observed concrete mismatches in the currently admitted G9 V3 source surface:

- `rule diff>0 ...` uses `>`; current grammar operator set has no `>`;
- `rule diff<0 ...` uses `<`; current grammar operator set has no `<`;
- generation validity uses `>=`; current grammar has no `>=`;
- `if residual.effect { ... }` and `if node.organ==CHATGPT { ... }` use conditional statements absent from the statement/action grammar;
- `verify(receipt? or residual)` uses postfix optional/coalescing-like `?` and keyword `or`, neither represented by the current expression/operator grammar.

**Interpretation:** the research spec and current parser grammar are not surface-conformant as written. This does **not** prove a missing semantic core. The smallest valid fix may be either grammar expansion or canonical rewrite of the research surface to existing constructs.

**Required live falsifier/confirmation:** on the Ubuntu target, execute a real parser over the complete admitted G9 corpus and record unsupported constructs, canonical IR, roundtrip semantic hashes and negative tests.

**Work event:** `CC-WORK-G9-SPEC-GRAMMAR-CONFORMANCE-001`.

## EXP-CR-002 — Incremental dependency-closure proxy

**Class:** SIMULATION_ONLY  
**Purpose:** test the mechanism behind Clay `Delta -> dependency_closure -> affected_view_recompute`, not claim live UnifiedDB performance.

Synthetic setup:
- random directed acyclic dependency graph;
- 5,000 nodes;
- deterministic node values derived from parent values;
- 100 independent single-node input changes;
- compare full recomputation with descendant-closure incremental recomputation.

Results:
- semantic result mismatches: **0 / 100**;
- median incremental/full operation ratio: **0.0008929457** (~0.0893%);
- p90 operation ratio: **0.0154678** (~1.55%);
- median affected node count: **3.5**;
- p90 affected node count: **50.7**;
- representative full recompute operation count: **10,079**.

**Interpretation:** sparse dependency structure can make exact incremental recomputation dramatically cheaper in this proxy. It does not establish the same sparsity or cost on real ClayGraph/UnifiedDB workloads.

**Falsifier:** real trace closure is dense/high-fanout enough that incremental bookkeeping costs exceed or approximate full recomputation. Required next experiment: fanout/density sweep plus live trace replay.

## EXP-CR-003 — Capability attenuation algebra proxy

**Class:** SIMULATION_ONLY  
**Purpose:** attack the Safe-Effect authority non-amplification rule.

Synthetic setup:
- universe of 10 verbs/permissions;
- 100,000 randomized parent capability/request pairs;
- safe candidate delegation: `child = parent INTERSECT requested`;
- unsafe comparison: `child = parent UNION requested`;
- oracle: child authority must be a subset of parent authority absent external grant.

Results:
- intersection attenuation authority amplifications: **0 / 100,000**;
- naive union authority amplifications: **93,580 / 100,000** = **93.58%**.

**Interpretation:** narrowing/intersection has the desired algebraic non-amplification property in this simplified model. Runtime soundness still depends on resource identity, revocation, ambient handles, FFI/subprocess closure, broker correctness and external-grant provenance.

**Falsifier:** any real child runtime obtains an undeclared authority/effect through ambient host access, confused deputy, stale/replayed token, generated code or backend bug.

## Negative/limitation receipts

1. No local Ubuntu parser/compiler binary was available to this hosted worker; no execution receipt is fabricated.
2. Repository code search did not establish an already-materialized parser implementation/receipt for the current G9 V3 surface. Absence from connector search is not proof of absence from every local checkout.
3. The `clay` room state path expected by the room protocol returned 404; same-room live-worker reconciliation is incomplete.
4. Proxy results are mechanism evidence only and are forbidden from promoting live compiler, UnifiedDB, Harness, Safe-Effect or FRANK claims.
