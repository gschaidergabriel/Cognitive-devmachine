# ClayCode run — first bounded compiler/lowering

Run: `claycode-20260811T2243p0700-chatgpt-secondary-first-compiler-lowering`

## Result

A first real compiler/lowering candidate now exists as target PR `Dr.-Unterweger#364`, rebuilt directly from fresh target main `a3ad42f3c2c2d52474ebc2bf1278bb91d4a6a0e3` after the executable evaluator was merged. The earlier stacked PR #362 was closed as stale rather than promoted.

The candidate lowers only `frank.effects::decide_effect` plus its reachable Clay function `destructive_guard_complete` into deterministic CPython AST/code. This is deliberately narrower than the parser/evaluator surface.

## Why this lane

Current target evidence already supports execution of the pure effect-policy subset on the accepted Ubuntu VPS: 200,576 differential requests, zero mismatches, plus package-origin and fail-closed/purity gates. The remaining F-V01-02 compiler/lowering gap was not covered by an active fresh-main lane.

## Hypothesis / counterhypothesis

Hypothesis: an already evidenced pure ClayCode subset can be compiled without semantic drift or new authority.

Counterhypothesis: a host-AST backend simply imports Python coercions/semantics and becomes a second semantic architecture.

The candidate therefore refuses intrinsic-reachable entries, unknown AST nodes and multi-relation comparison chains; it does not select Bool/Int equality semantics; it exposes no authority-minting or external-effect binding; and its target gate compares the source evaluator, compiled backend and shipping Python policy reference on the same request corpus.

## External refresh

Python 3.12's documented AST/code-object compilation path is used only as a bootstrap backend. Current Cranelift remains a later native-code competitor, not an immediate replacement: adopting a second IR/codegen stack before ClayCode type/effect semantics are broader and frozen would add implementation surface without resolving the current semantic uncertainty.

## Mesh fusion

The current UnifiedDB/ClayGraph V2 composition evidence requires canonical production state to remain unopened/unmigrated pending explicit migration/recovery gates. This compiler run is therefore source/value-only and performs no UnifiedDB/ClayGraph canonical mutation. ClayCode remains semantic authority; backend code is a projection.

## Target state

PR: `Dr.-Unterweger#364`

Head: `bef7686f909f9d87d59f33731f0f7241e78bc2fe`

Workflow run: `31508447693`

State at report write: `QUEUED`

No compiler PASS or F-V01-02 subcheck promotion is claimed until the exact target receipt is observed.

## Next falsifier

Require the exact target head to complete the 10-check gate with zero three-way mismatches across 200,576 requests. If green, inspect resource shadow and generated-AST identity, then promote only this bounded lowering slice. If red, preserve the failure and repair the smallest falsified boundary rather than expanding compiler scope.
