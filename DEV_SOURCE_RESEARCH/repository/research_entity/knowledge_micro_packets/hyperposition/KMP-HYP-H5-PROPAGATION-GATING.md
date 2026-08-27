# KMP-HYP-H5-PROPAGATION-GATING

- **epistemic class:** OPEN synthetic-mechanism result
- **claim:** Higher-order representation and propagation strength are independent. Persistent relations should normally feed a sparse, context-gated, bounded activation topology rather than unrestricted diffusion.
- **H5 local proxy:** after 10 steps, unbounded propagation occupied all 3000 nodes and target-context mass fell to 0.29557; hard gating kept target mass ~1.0 with almost zero cross-context diversity; the current adaptive construction also remained too close to hard gating.
- **interpretation:** unbounded spread is noisy; hard gating can be brittle; the diversity-reserve policy remains unresolved.
- **controls required:** gain/depth/decay/inhibition/budget, novelty/diversity reserve, role-shuffled and temporal-shuffled fields, utility-poison tests, exact anchors.
- **external convergence:** higher-order-network/HGNN literature independently reports oversmoothing/representation-collapse risks under deep multi-way propagation; this is analogous, not identical, to ClayGraph activation.
- **falsifier:** target tasks show unbounded propagation dominates gated policies on utility, false association, OOD and cost.
- **status:** OPEN/HOLD
