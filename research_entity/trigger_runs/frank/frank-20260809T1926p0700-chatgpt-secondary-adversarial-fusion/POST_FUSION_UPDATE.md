# Post-fusion update — concurrent delta assimilation

**run:** `frank-20260809T1926p0700-chatgpt-secondary-adversarial-fusion`  
**status:** append-only assimilation after initial report  
**scientific promotion:** NONE

## A. ActiveAssembly finding closed at component level

After this run materialized the same-ancestry conflict counterexample, concurrent FRANK work landed:

- `1bdae62689070b3b083ce4acaead4e52f05aac71` — `frank: separate conflict visibility from ancestry evidence cap`;
- `c9a1a9852d2fd0046a8e731084449ba3cd9f89a9` — `frank: regress same-ancestry conflict visibility`;
- `382fb494e047958478d705548eee0f417b0c1782` — conflict-budget feedback returned to the research mesh.

The implementation now distinguishes two semantic roles:

`ANCESTRY_CAP => limits ordinary evidence/redundancy selection`

`CONFLICT_VISIBILITY => may bypass ancestry cap when hard total item budget permits`

and explicitly sets:

`independent_replication_credit = false`

for same-ancestry conflict representatives.

The hard total ActiveAssembly item budget remains authoritative, and omitted contradictory detail retains re-expansion identity under the new regression.

**Adjudication:** the original Red-Team Finding A is `FIXED_COMPONENT_LEVEL / AWAIT_EXECUTED_RECEIPT_AND_H1_INTEGRATION`, not an open architecture blocker. Do not delete the counterexample; it becomes a regression lineage item.

## B. Loop-controller semantic fork remains open

The current two H1 reference lines still split complementary semantics:

- `loop_dynamics_quality_gate.py`: estimator identity/version, residual uncertainty, measurement age/freshness and uncertain routing; weaker regime logic;
- `loop_dynamics_reference.py`: proper low-delta+low-residual convergence, stall/productive-cycle/divergence/overthinking/budget/rollback semantics; no residual estimator identity/version/measurement-age fields, and generic `uncertainty` is not used in regime/decision logic.

No current-head commit found in the final refresh had yet merged both sets into one release-oracle contract.

**Adjudication:** Red-Team Finding B remains `OPEN_INTEGRATION_BLOCKER_FOR_H1_FREEZE`, but not a ClayCode semantic-language blocker.

Required closure is one fused versioned readout/controller contract plus tests proving:

1. invalid/stale/missing/high-uncertainty readouts cannot mint candidate convergence;
2. high delta + low residual is not fixed-point convergence;
3. low delta + high residual is STALLED candidate;
4. productive cycles and divergence/overthinking are separately classifiable;
5. threshold/controller policy identity is receipt-bound;
6. all decisions remain compute-routing proposals without effect authority.

## C. Runtime authority negative was independently closed further

The earlier caller-controlled `process.exec` allowlist defect is now followed by stronger concurrent changes that bind process authority to canonical executable paths and reject basename collisions. This reduces PATH/alias ambiguity beyond the first mint-time policy fix.

Target Ubuntu acceptance still requires actual OS-level authority closure/sandbox evidence; hosted Python/CI object-identity mechanisms remain proxy evidence.

## D. Current gate accounting

Latest reread of `research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json` still records exactly one release-package PASS (`CC-WP-01-SPEC-FREEZE`). WP02..WP14 remain OPEN and application acceptance remains empty. New implementation/CI/proxy receipts therefore remain support evidence, not package promotion.

Latest reread of `research_entity/harness/HARNESS_WORKSPACE.json` still has the old H-WP-01 field marked COMPLETE, but the later explicit current-target invalidation remains controlling for current NEW-FRANK release accounting. Component execution such as ActiveAssembly does not by itself restore the current-target H1 freeze.

## E. Updated next edge

The highest-information FRANK architecture edge after this assimilation is now:

`fuse LoopDynamics regime semantics + ReadoutQuality/freshness`

while BASE production work continues independently on its existing closure chain.

This is the intended cascade behavior:

`red-team counterexample -> peer implementation -> regression -> re-fusion -> remove closed blocker -> expose next unresolved semantic edge`.
