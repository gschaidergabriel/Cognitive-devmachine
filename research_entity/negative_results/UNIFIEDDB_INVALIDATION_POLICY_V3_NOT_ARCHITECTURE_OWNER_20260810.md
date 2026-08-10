# Negative/selection result — invalidation V3 is not a second architecture controller

Status: `NOT_SELECTED_AS_ARCHITECTURE_OWNER`

The local `u10_invalidation_policy_v3.py` correctly demonstrates an important measurement law: choose between on-demand BFS and a prepared support index using complete maintenance/build/memory economics rather than lookup latency alone.

However, current `main` now contains the more general U16 compile-amortization/horizon controller (`semantic_compile_amortization_gate_v16.py` plus pulse-history horizon estimation). Creating a second permanent routing controller for invalidation would duplicate control semantics and violate the shared architecture simplification rule.

Therefore:

- retain V3 as a lesionable local benchmark/control artifact;
- do not promote it as an independent runtime controller;
- feed measured invalidation/update/build costs into the current U16 compile-economics path;
- let U16 decide ONLINE vs COMPILE/materialize from current workload lifetime and quality;
- keep the structural invalidation proof itself independent, because it changes the *cost and safe affected set* available to U12/U16 rather than competing with U16's routing authority.

Current local exact-U10 evidence used by this adjudication:

- on-demand BFS total structural-maintenance p50: 0.007892 ms;
- prepared support-mask total p50: 0.01355 ms for one invalidation read per mutation;
- prepared support state also has a large Python-object memory shadow;
- equivalent targeted weighted-field recompile p50: 0.2356155 ms vs 27.389176 ms full 120-anchor recompile, with 0 mismatches over 500 mutations;
- U12 segmented immutable generations provide the repository-native mechanism for reusing unchanged seed segments coherently.

The architectural fusion is thus:

`bounded impact proof -> U12 segmented affected-seed rebuild/reuse -> measured build/online costs -> U16 amortization/horizon decision`

not:

`V3 controller -> parallel compile policy`.

Promotion of V3 policy: `NONE`.
