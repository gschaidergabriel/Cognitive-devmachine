<!-- RAE_META
{"packet_id":"KMP-C6-CLAYVECTOR-TYPED-PAYLOAD","title":"Clay-native values/vectors need semantic headers and efficient physical payloads","domains":["hyperposition","frank","claycode","claygraph","model_runtime"],"topics":["ClayVector","basis","axes","units","tensor","quantization"],"epistemic_class":"MEASURED_REFERENCE_MECHANISM","claim_status_hint":"OPEN_ARCHITECTURE_WITH_PROXY_SUPPORT","origin_actor":"chatgpt-secondary","source_refs":["EXP-C6-CLAYVECTOR-002","EXP-C6-PHYSICAL-ENCODING-003"],"confidence":0.93,"verification_required":true}
RAE_META -->

### Core
Semantically exposed numeric state should carry Clay-native basis, axis, unit, range/normalization, time/epoch, dtype/shape, provenance/version and payload integrity metadata. High-dimensional payloads remain binary/tensors.

### Evidence
C6 injected 120k synthetic vector-interface faults. Reference typing detected all injected axis/unit/stale-basis faults; payload hashing caught injected payload bitflips. A semantically wrong computation with a valid new hash remained undetected.

### Implication
ClayVector typing protects interfaces but does not prove algorithms. Learned embeddings/codebooks remain derived and versioned, not canonical relational truth.
