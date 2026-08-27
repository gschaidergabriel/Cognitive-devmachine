# KMP-GWT-R7-CANDIDATE-SURFACE-FILTER-BOUNDARY-20260809

packet_id: KMP-GWT-R7-CANDIDATE-SURFACE-FILTER-BOUNDARY-20260809  
domains: [gwt, frank, claycode, harness, claygraph, hyperposition]  
epistemic_class: EXACT_MODEL_FREE_ENUMERATION_AND_SET_INVARIANT  
status_hint: CURRENT_MECHANISM_CONSTRAINT_WITH_TARGET_IMPLEMENTATION_OPEN  
origin_run: gwt-20260809T1720p0700-chatgpt-secondary-r7-dual-gate

## Atomic finding

If an external/system workspace is a pure **FILTER** over a model-exposed candidate surface (`W_external subset_of W_internal`), it cannot increase recall of a relevant set that is absent from that input surface. Formally, `W_external intersect R subset_of W_internal intersect R`, so `recall_external <= recall_internal`.

The executable enumeration over universe size 6 checked **41,895** non-empty filter cases and found **0** recall-improvement violations. Precision improved in **15,482** cases, showing that filtering can improve selectivity without rescuing missing candidates. When the subset restriction was removed as an AUGMENT control, recall improved in **83,307 / 250,047** cases.

## Architecture constraint

Any nested model-internal -> system-GWT bridge must declare its candidate-surface relation as at least:

`FILTER | AUGMENT | RECONSTRUCT | UNKNOWN`.

A system claiming recall rescue while declaring `FILTER` has either misclassified its boundary or introduced an undeclared information path.

## Interpretation boundary

This is an exact set/implementation invariant, not evidence that Qwen has a J-space, not evidence that AUGMENT helps Frank, and not emergence or consciousness evidence. The target-model question remains OPEN and requires Qwen-class 4B intervention/replay.