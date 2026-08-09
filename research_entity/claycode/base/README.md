# ClayCode BASE blocker attack

This directory is an executable convergence candidate for the 14 BASE ClayCode work packages. It deliberately follows **less change, more compile**: it does not replace G9 semantics; it provides a small executable frontend -> canonical IR -> checker -> evaluator -> lowering -> runtime/FFI path and uses current G9/FRANK syntax as counterexamples.

What is implemented and tested:

- structural frontend covering admitted G9 declarations and current Frank `use/type/fn/let/require/return` surface;
- executable parser for `fn` and G9 `cycle`, including the previously unsupported `if`, named constructor arguments and G9 optional-coalesce spelling;
- deterministic `semantic_hash` distinct from provenance-bound `contract_hash`;
- typed executable IR subset and type/effect negative diagnostics;
- reference evaluator;
- Python lowering plus independent native C/gcc pure-core lowering;
- explicit RuntimeABI/FFI with external capability grants and receipts;
- real local adapters for filesystem, loopback HTTP, SQLite transactions, async/cancellation/atomics, Tk event loop under X11/Xvfb, safe compiler expression tool, NumPy numerical backend and a harmless Linux system probe;
- APP-01 through APP-09 local executable proxy proofs, including the exact `frame` function body from current `frankv0.1` (`claycode/frank_grt.clay`, recorded blob SHA);
- 5,000 evaluator-vs-generated-target differential cases;
- 1,000/1,000 missing-authority denials;
- disjoint generated training/held-out corpus.

## Claim boundary

This is **not** `GENERAL_PURPOSE_GATE: PASS`. The acceptance contract requires APP-10 full FRANK handoff and reproducible execution on Andreas' exact Ubuntu developer system. This session has GitHub/Drive access but no shell on that physical target, so those two facts cannot be fabricated.

`BLOCKER_MATRIX.json` maps every CC-WP-01..14 to the evidence produced here and names the remaining hard blockers.
