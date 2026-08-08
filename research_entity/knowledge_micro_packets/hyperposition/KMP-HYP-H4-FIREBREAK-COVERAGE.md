<!-- RAE_META
{"packet_id":"KMP-HYP-H4-FIREBREAK-COVERAGE","title":"Selective semantic firebreaks require measured witness coverage","domains":["hyperposition","systems-architecture","claycode"],"topics":["coverage","fallback","typed fast path","fail closed"],"epistemic_class":"SYNTHETIC_ENGINEERING_PROXY","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T18:06:00+07:00","source_refs":["research_entity/trigger_runs/hyperposition/hyperposition-20260808T1806p0700-chatgpt-secondary-r2/EXPERIMENT_RESULTS.json"],"verification_required":true}
RAE_META -->

### Core
A selective typed fast path is safe only when every required semantic-transition witness is present or missing coverage forces broader validation. In H4's 1–5-witness construction, fallback fell from ~14.03% at 95% per-witness coverage to ~2.97% at 99% and ~0.30% at 99.9%.

### Implication
Do not assume a nominal schema coverage percentage is good enough. Measure operation-level complete-closure coverage and treat uncertainty as runtime state.

### Next test
Derive live coverage from FRANK/ClayCode traces, stratified by operation/effect class, and measure false rejects, fallback latency and missed dependencies on held-out/adversarial traces.
