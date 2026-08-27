<!-- RAE_META
{"packet_id":"KMP-FUS3-FRANK-L4","domains":["frank","clay","model_runtime"],"origin_actor":"chatgpt-secondary","origin_run":"fusion-20260808T1855p0700-chatgpt-secondary-r3","epistemic_class":"FUSION_ARCHITECTURE_DELTA","claim_status_hint":"OPEN","related_experiment_ids":["EXP-FUS3-LAYER-IDENT-001","EXP-FUS3-SYMBOL-PURITY-NULL-002"],"confidence":0.88}
RAE_META -->
# FRANK feedback — C6 clarification, not reversal

C6's fixed Clay-native premise survives. Fusion refines what “native” means:

- `L0_INTENT`: human/external goal language, ambiguous/non-authoritative until compiled;
- `L1_CANONICAL_CLAY`: exact semantic source of truth, architecture, memory identities, authority/effect contracts;
- `L2_NATIVE_CLAY`: learned model-generated/deliberative Clay, probabilistic proposal/reasoning layer;
- `L3_NEURAL_PHYSICAL`: hidden activations/KV/tensors/binary lowerings, continuous physical representations.

C6 already contains most of this distinction through CLAY_CANONICAL/CLAY_MODEL and its hidden-tensor boundary. The new requirement is to make the layer identity explicit in training/evaluation receipts so L1 compiler gains cannot be counted as L2 “mother tongue” gains.

A VQ/codebook pathway is now an optional target experiment, motivated by AIM and independently by VQEL. It is not part of the owner-fixed architecture unless it wins target evidence. Symbol purity/convergence is insufficient; require causal lesion/permutation/rescue/OOD tests.

Next: full-Qwen factorial `general vs Clay-full-FT` × `raw/canonical vs compiled CLAY_MODEL view` × `VQ auxiliary off/on`, with retained-capability and common-mode-fault shadows.