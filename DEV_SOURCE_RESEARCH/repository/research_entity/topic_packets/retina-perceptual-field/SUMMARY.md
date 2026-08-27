# Current synthesis

FRANK's visual target is no longer `image -> Retina service -> caption/VisualPercept -> cognition`. The owner-fixed architecture dissolves Retina semantically into one Clay-native FRANK runtime. The strongest open implementation candidate is a persistent `PerceptualField` with explicit separation between immutable sensor evidence, provisional perceptual hypotheses and durable world entities.

The field updates sparsely over time. Non-observation is not absence; visibility states include occluded, out-of-FOV, explicit absence, unknown, conflict, degraded and stale. World/memory priors may constrain interpretation but must never become sensor evidence. GWT receives only bounded globally valuable visual Assemblies. High-value uncertainty can purchase additional sensing/computation through an active-sensing policy. Full `VisualPercept` objects are materialized on demand for audit/replay rather than required on every hot-path update.

Historical Retina remains the required baseline/kernel source. Its honest hard-set documented fixed-class, compositional, OOD, OCR and cascade failures. Later high phrase-coverage numbers are not sufficient truth metrics because permissive CLIP thresholds had high realistic-negative FPR and final gap-closing was tuned on the hard-set surface.

External research supports the ingredients — recurrence under occlusion, joint object-scene inference, event/frame hybrids, persistent scene graphs, streaming memory, active perception and open-set uncertainty — but not the complete FRANK composition.

Priority tests: reproduce current baseline; freeze a clean held-out set; test temporal continuity/explicit negative evidence; recurrence + misleading-prior factorial; hybrid anchor/change policy; typed state vs narrative at the 4B boundary. The mandatory simple counterbaseline is `optimized Retina + tracker + cache + periodic anchors`.
