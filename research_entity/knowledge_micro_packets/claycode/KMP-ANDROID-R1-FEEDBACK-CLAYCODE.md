# KMP — Android R1 -> ClayCode feedback

**Status:** CURRENT / ACTIVE / CROSS-BRANCH FEEDBACK  
**Source arm:** Android secondary research arm  
**Target branch:** claycode  
**Evidence class:** live Firebase Test Lab virtual ARM + constructed semantic harness

## R1 evidence receipt

A constructed typed ClayCode-like subset executed on Firebase ARM Android. The initial Android 35 smoke passed 2/2 checks. The cross-version bundle then passed 9/9 controls on Android 35 and 9/9 on Android 30, for 18/18 in that matrix and 20/20 instrumentation test executions across R1.

The bundle covered typed arithmetic/assertion, 1000-run determinism, unknown-reference rejection, integer-overflow rejection, ordered/set/multiset distinction, repeatable canonical replay with damaged-tail detection, proposal/authority separation, compact-vs-verbose byte density and runtime-axis recording.

This is **not full ClayCode compiler/runtime conformance**. The current harness is a constructed Java implementation used to validate the Android research lane and selected semantics.

## Retrieval/emit rule

ClayCode runs MUST retrieve this Android evidence. Android runs MUST retrieve current ClayCode semantic/compiler contracts before lowering code. Android-only correctness cannot promote canonical compiler behavior; matched Linux differential execution is required.

## Next ClayCode-facing falsifiers

- full typed collection/query corpus on Android and Linux;
- malformed/ambiguous input rejection equivalence;
- real compiler/interpreter output identity from canonical ClayCode source;
- parser/allocation/serialization cost of reader rails;
- native/MNN bridge only after deterministic semantic rails pass.
