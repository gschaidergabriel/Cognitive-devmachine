<!-- RAE_META
{"packet_id":"MP-RETINA-FUNCTIONAL-MULTIMODALITY","title":"FRANK can be functionally multimodal without a native visual-token 4B","domains":["visual_perception_retina","model_runtime","frank_gwt"],"topics":["4B","multimodality","Clay projection"],"epistemic_class":"OPEN_HYPOTHESIS","claim_status_hint":"OPEN","origin_class":"ARCHITECTURE_SYNTHESIS","origin_actor":"chatgpt-secondary","created_at":"2026-08-09","updated_at":"2026-08-09","source_refs":["research_entity/global/FRANK_DISSOLVED_PERCEPTION_DIRECTIVE.md","https://arxiv.org/abs/2608.05703"],"evidence_refs":[],"related_claim_ids":[],"related_experiment_ids":["RET-E2","RET-E20","RET-E21"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.68,"verification_required":true,"falsifier_or_next_test":"Closed-loop multimodal tasks comparing text-only, narrative Retina, typed PerceptualField and native-VLM evaluation comparator.","search_terms":["FRANK functional multimodal 4B visual state Clay native VLM"]}
RAE_META -->

### Core
A text/Clay-token Qwen-class 4B does not have to receive raw image tokens for FRANK to behave as a multimodal system. Persistent visual Evidence/World state can be maintained outside the model and only a bounded task-relevant Assembly can enter the 4B when reasoning is needed.

### Evidence / boundary
Streaming-agent work provides independent evidence that recent-frame-only and repeated text conversion can lose long-horizon visual information, motivating persistent multimodal state. This does **not** prove that Clay state can match a native VLM on compositional visual reasoning. The underlying model should not be described as literally vision-native unless its architecture/training includes native visual inputs.

### Implication
The meaningful benchmark is closed-loop visual agency — perceive, decide, act, visually verify, update and recover — plus model token cost, not static phrase coverage alone.

### Next test
E2/E20/E21: compare full narrative, typed Assembly and strong VLM comparator under matched tasks, preserving the target serving architecture boundary.
