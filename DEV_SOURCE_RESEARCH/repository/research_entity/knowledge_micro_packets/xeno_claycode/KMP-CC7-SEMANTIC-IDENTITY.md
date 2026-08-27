<!-- RAE_META
{"packet_id":"KMP-CC7-SEMANTIC-IDENTITY","title":"ClayCode semantic identity must be independent of reader/wire serialization","domains":["xeno-claycode","storage-state-memory","deployment-packaging"],"topics":["semantic-hash","canonicalization","wire-format","schema-evolution","projection"],"epistemic_class":"ARCHITECTURE_DECISION_SUMMARY","claim_status_hint":"OPEN_WITH_STRONG_EXTERNAL_SUPPORT","origin_class":"CLAYCODE_CC7_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:49:00+07:00","updated_at":"2026-08-08T05:49:00+07:00","source_refs":["Protocol Buffers: Proto Serialization Is Not Canonical","RFC 8949 deterministic CBOR","MLIR Defining Dialects","MLIR Bytecode Format","CC6 semantic IR/projection result"],"evidence_refs":[],"related_claim_ids":["H-CC7-009","H-CC7-010","H-CC7-011"],"related_experiment_ids":[],"predecessor_packet_ids":["KMP-CC6-SEMANTIC-IR-PROJECTION"],"supersedes_packet_ids":[],"confidence":0.92,"verification_required":true,"falsifier_or_next_test":"Cross-version semantic-equivalence test across verbose JSON, deterministic CBOR/custom bytecode, unknown extensions and reordered fields, with one stable semantic identity."}
RAE_META -->

### Core
ClayCode must distinguish **semantic identity** from **projection/wire identity**. Arbitrary serialized bytes are not a safe long-lived semantic hash. The canonical semantic normalization should define field/op identities, value semantics, version/unknown/conflict rules and extension handling; reader-specific JSON, compact text, deterministic CBOR or custom bytecode are projections of that meaning.

### External support
Protocol Buffers explicitly documents that deterministic serialization is not canonical and that unknown fields/schema evolution make serialized-byte hashes fragile. RFC 8949 defines deterministic CBOR restrictions suitable for protocols needing reproducible encoding. MLIR independently separates extensible semantic dialects/interfaces from custom compact bytecode encodings.

### Implication
A compact wire profile may be replaced without changing the semantic object. Hashes used for semantic equality/provenance must be computed over the specified semantic normalization or a deliberately versioned deterministic canonical profile, never over an incidental reader projection.
