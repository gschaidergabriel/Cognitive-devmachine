<!-- RAE_META
{"packet_id":"MP-RETINA-VISIBILITY-STATES","title":"Non-observation is not absence","domains":["visual_perception_retina","storage_state_memory","frank_gwt"],"topics":["object permanence","temporal state","negative evidence"],"epistemic_class":"ARCHITECTURE_DECISION_SUMMARY","claim_status_hint":"OPEN_MECHANISM","origin_class":"RESEARCH_SYNTHESIS","origin_actor":"chatgpt-secondary","created_at":"2026-08-09","updated_at":"2026-08-09","source_refs":["research_entity/retina/RETINA_PERCEPTUAL_FIELD_ARCHITECTURE.md"],"evidence_refs":["research_entity/retina/runs/retina-20260809T0615p0700-deep-foundry/SYNTHETIC_MECHANISM_RECEIPT.json"],"related_claim_ids":[],"related_experiment_ids":["RET-E3","RET-E6"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.88,"verification_required":true,"falsifier_or_next_test":"Temporal sequences distinguishing occlusion, out-of-FOV, explicit absence and sensor failure.","search_terms":["retina occluded absent out of fov ghost object negative evidence"]}
RAE_META -->

### Core
Persistent visual state must distinguish `OCCLUDED`, `OUT_OF_FOV`, `ABSENT_EXPLICIT_NEGATIVE`, `UNKNOWN`, `SENSOR_DEGRADED` and `STALE`. A detector not firing is not equivalent to evidence that an object disappeared.

### Evidence / boundary
This follows from the requirements of persistent object identity and is reinforced by a synthetic sanity check: slow persistent belief without explicit negative evidence produced long ghost-object runs, whereas using strong explicit negative evidence preserved most of the recall benefit while sharply reducing false persistence. The numeric result is synthetic only.

### Implication
ClayGraph/UnifiedDB cannot use one Boolean `seen` flag. Visual memory needs temporal validity and evidence class so FRANK can keep a cup in the world model when looking away but remove it when a clear fresh view shows an empty table.

### Next test
E6 with frozen sequences for occlusion, camera turn-away, real removal, sensor failure and stale replay.
