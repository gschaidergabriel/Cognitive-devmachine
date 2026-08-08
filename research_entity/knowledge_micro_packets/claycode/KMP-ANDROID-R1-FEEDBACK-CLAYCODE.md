# KMP — Android R1 -> ClayCode feedback

**Status:** CURRENT / ACTIVE / CROSS-BRANCH FEEDBACK  
**Source arm:** Android secondary research arm  
**Target branch:** claycode

## Current feedback

A constructed typed ClayCode subset has now built and executed on an ARM Android Test Lab runtime, including deterministic assertion and rejection of an unknown reference. This establishes an executable Android test lane, not conformance of the full ClayCode compiler/runtime.

Android should be used to stress type preservation, collection semantics, deterministic rejection, overflow behavior, compact reader surfaces, safe-effect boundaries and cross-platform lowering equivalence.

## Retrieval/emit rule

ClayCode runs MUST retrieve Android compiler/runtime findings when material. Android runs MUST retrieve current ClayCode semantic/compiler contracts before lowering code. Android-only correctness is insufficient for canonical compiler promotion; differential Linux execution remains required.

## Next ClayCode-facing falsifiers

- full typed collection corpus across Android and Linux;
- malformed/ambiguous input rejection equivalence;
- compiler/interpreter output identity under matched canonical source;
- parsing/allocation/serialization cost of compact versus verbose reader rails;
- native runtime/MNN bridge only after deterministic semantic rails pass.
