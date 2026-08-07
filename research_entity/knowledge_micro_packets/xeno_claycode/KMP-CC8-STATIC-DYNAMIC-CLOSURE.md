<!-- RAE_META
{"packet_id":"KMP-CC8-STATIC-DYNAMIC-CLOSURE","title":"Observed ClayCode traces may narrow but never replace a trusted static semantic envelope","domains":["xeno_claycode","formal_methods_testing","security_capabilities","systems_architecture"],"topics":["effect-system","dynamic-dependency","runtime-interposition","fail-closed","transition-closure"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_ARCHITECTURE_WITH_SYNTHETIC_SUPPORT","origin_class":"CLAYCODE_CC8_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T06:06:00+07:00","updated_at":"2026-08-08T06:06:00+07:00","source_refs":["claycode-20260808T0606p0700-chatgpt-secondary:EXP-CC8-HYBRID-TRACE-002","claycode-20260808T0606p0700-chatgpt-secondary:EXP-CC8-ENVELOPE-FUZZ-005","Koka-effect-typing","self-adjusting-computation-DDG"],"evidence_refs":[],"related_claim_ids":["H-CC8-003","H-CC8-004","H-CC8-006","H-CC8-T01","H-CC8-T03"],"related_experiment_ids":["EXP-CC8-HYBRID-TRACE-002","EXP-CC8-ENVELOPE-FUZZ-005"],"predecessor_packet_ids":["KMP-CC7-DERIVED-EFFECTS"],"supersedes_packet_ids":[],"affected_branches":["claycode","clay","frank","hyperposition"],"confidence":0.9,"verification_required":true,"falsifier_or_next_test":"Instrument a real dynamic FRANK/Clay operation surface including Python reflection, subprocess/tool calls and native boundaries; any undetected dependency/effect escape blocks scoped-trace promotion.","search_terms":["static effect envelope","dynamic access trace","effect inference","self adjusting computation","dependency graph"]}
RAE_META -->

### Core
CC8 proposes a two-level closure contract: the trusted operation registry/compiler derives a conservative **static may-depend/may-effect envelope**; complete runtime interposition records the **actual did-depend/did-effect trace**. The observed trace may reduce revalidation work only if `observed_trace ⊆ static_envelope`. Any escape aborts/fails closed or widens the envelope.

### Evidence / boundary
In the constructed CC8 workload, the observed trace averaged ~5.98 dependency items versus ~59.83 in the static envelope (~10x narrower) with zero misses while interposition was exact. Injected hidden access demonstrated why observed-only validation is unsound. A 100k envelope-fuzzer caught all 2,872 deliberately undeclared typed accesses with zero false rejects on legitimate generated traces. These results test contract logic, not completeness of a production FRANK interposer.

### Implication
ClayCode can gain path-sensitive freshness/performance without letting model output or runtime observation become the authority specification. Reflection/FFI/native/tool paths that cannot be bounded must conservatively escalate.

### Next test
Implement access interposition around a small real FRANK operation registry and compare static envelope, observed trace and full replay under mutation/fault injection.
