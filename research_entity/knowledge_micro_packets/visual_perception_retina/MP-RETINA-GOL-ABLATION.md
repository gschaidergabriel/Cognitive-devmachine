<!-- RAE_META
{"packet_id":"MP-RETINA-GOL-ABLATION","title":"Game-of-Life visual features must earn their place by ablation","domains":["visual_perception_retina","formal_methods_testing"],"topics":["Game of Life","texture","ablation"],"epistemic_class":"METHOD_MEMORY","claim_status_hint":"OPEN","origin_class":"CODE_INSPECTION_PLUS_EXTERNAL_RESEARCH","origin_actor":"chatgpt-secondary","created_at":"2026-08-09","updated_at":"2026-08-09","source_refs":["gschaidergabriel/digital-retina:retina/vision/gol_patterns.py"],"evidence_refs":[],"related_claim_ids":[],"related_experiment_ids":["RET-E15"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.90,"verification_required":true,"falsifier_or_next_test":"Ablate GoL against HOG/LBP/Gabor/dense-feature controls under matched compute.","search_terms":["Digital Retina Game of Life GoL texture pattern ablation"]}
RAE_META -->

### Core
Current Digital Retina contains a concrete Conway-Game-of-Life transform that binarizes image/edge channels, evolves them and emits density/stability/oscillation/complexity-derived texture phrases. It is real executable code, but it has **no privileged evidential status** in the new architecture.

### Evidence / boundary
Cellular automata have prior art as engineered texture descriptors, so the feature family is not invalid by definition. The deep run found no evidence that Conway GoL is uniquely cortex-like, necessary for perception or superior to conventional cheap texture/dense representations. Neuroscience or emergence language therefore cannot justify retention.

### Implication
GoL becomes an ordinary candidate kernel. If it supplies independent held-out information at attractive cost, it can remain. If conventional texture or dense features subsume it, remove/demote it without attachment to the metaphor.

### Next test
E15: matched no-feature, HOG/colour, LBP/Gabor, DINO/CLIP statistics, GoL and combined conditions; measure incremental held-out utility and runtime.
