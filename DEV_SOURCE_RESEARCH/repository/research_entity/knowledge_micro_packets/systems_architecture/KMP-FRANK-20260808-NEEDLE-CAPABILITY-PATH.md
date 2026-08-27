<!-- RAE_META
{"packet_id":"KMP-FRANK-20260808-NEEDLE-CAPABILITY-PATH","title":"Needle is a pre-model capability proposal reflex, not execution authority","domains":["systems-architecture","security-capabilities","frank"],"topics":["needle","tool-routing","capability-gateway","4b"],"epistemic_class":"ARCHITECTURE_HYPOTHESIS","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:59:00+07:00","source_refs":["user:Frank-Architektur.md sha256:98afa4eda69dbe0253ea482a5338cfbbed212af2fba5d45af0fd51786b17559c","H-G3-006","research_entity/topic_packets/clay-g7-hierarchical-semantic-causal-kernel/ARCHITECTURE.md"],"confidence":0.9,"verification_required":true,"falsifier_or_next_test":"Trace 1,000+ real tool-intent turns through Needle→gateway→tool-result→Frank and measure authority rejects, wrong-tool rate, fallback rate, latency and state/provenance continuity."}
RAE_META -->

### Core
The current FRANK architecture intentionally removes tool planning from the 4B model: Needle (26M) classifies tool intent as a fast reflex, with a free-model fallback and Frank only formulating from results. Architecturally, Needle therefore belongs beside the pre-model fast path, not inside the language model's deliberative workspace.

### Hard boundary
Needle may select/propose a capability, but must never itself become authority. The external capability gateway validates permissions, parameters and execution. This preserves canonical H-G3-006: model/classifier syntax is not commit authority.

### Re-entry rule
Tool results should enter FRANK as provenance-bound observations. Exact/raw values belong in the exact state path; a semantic summary may compete for the workspace. This preserves the existing Zahl → Wort → Gewicht separation instead of letting raw tool telemetry leak directly into learned self-description.
