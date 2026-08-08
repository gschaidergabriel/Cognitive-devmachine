# KMP — Android R1 -> Clay feedback

**Status:** CURRENT / ACTIVE / CROSS-BRANCH FEEDBACK  
**Source arm:** Android secondary research arm  
**Target branch:** clay  
**Platform boundary:** Linux-primary; Android-secondary  
**Evidence class:** live Firebase Test Lab virtual ARM + constructed semantic harness

## R1 evidence receipt

Three virtual Android invocations were used and the cycle then stopped to preserve shared quota. `MediumPhone.arm` Android 35 first passed 2/2 smoke tests. The bundled matrix `matrix-322nxfmnphtz2` then passed 9/9 controls on Android 35 and 9/9 on `SmallPhone.arm` Android 30, for 18/18 in that matrix and 20/20 instrumentation test executions across R1.

Observed constructed invariants include typed arithmetic/assertion, deterministic repetition, unknown-reference rejection, overflow rejection, distinguishable ordered/set/multiset controls, repeatable canonical replay with damaged-tail detection, and an external capability boundary that a model-like proposal string could not self-mint.

This is implementation-path evidence only. It does not prove full Clay semantics, full ClayCode conformance, target-Qwen behavior or Linux equivalence.

## Generalizable candidate

Android is a constrained-runtime falsification and efficiency arm for Clay. It should stress representation density, parsing/allocation cost, bounded-view memory pressure, safe-effect behavior and reconstruction/replay cost. A constructed compact Clay-like source was byte-smaller than its verbose JSON-like control, but no token/model/runtime efficiency claim is promoted from that byte check.

## Retrieval/emit rule

Clay runs MUST retrieve this Android feedback. Android runs MUST retrieve current Clay architecture before testing. Android-specific effects retain Android provenance until matched Linux replication.

## Next Clay-facing falsifiers

- bounded Clay/MOSAIC view size vs context/RAM/prefill/total latency on target Qwen-class 4B;
- compact semantic density vs parser/decoder cost at matched correctness;
- safe-effect and canonical replay invariants under real Android process interruption;
- Linux-vs-Android differential equivalence before cross-platform promotion.
