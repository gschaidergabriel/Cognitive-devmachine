# HYP-RC6 — CARTS

**Status:** OPEN / HOLD  
**Parent:** HYP-RC5

H6 adds **T7 causal-credit topology** to H5's topology separation and makes learned/live topology switching explicitly reversible and authority-mediated.

Core laws:
- `what influenced outcome != what receives credit != what may become live != what may act`;
- `recoverable topology != harmless topology`;
- `atomic switch != cognitive correctness`;
- `effect expressibility != effect authority`.

New live-switch objects: `TopologyCandidate -> TopologyIntent -> host TopologyPermit -> LiveTopologyRef`, with canary/health/rollback receipts. The concurrent ClayCode general-purpose-core work strengthens the last boundary: powerful/destructive/admin operations may remain expressible as typed intents, while model-forged authority remains invalid.

New synthetic results:
- broadcast credit post-shift accuracy 0.22885 vs receipt-gated 0.47245;
- false-positive credit 0.833333 vs 0.000109;
- direct bad-topology exposure 100 units vs canary+rollback 11.084 units/bad proposal;
- in-place crash torn rate 0.77602 vs idealized versioned live-ref 0.

These are mechanism tests, not target FRANK/Qwen evidence.
