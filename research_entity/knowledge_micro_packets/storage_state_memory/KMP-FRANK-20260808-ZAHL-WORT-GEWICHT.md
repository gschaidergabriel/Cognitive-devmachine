<!-- RAE_META
{"packet_id":"KMP-FRANK-20260808-ZAHL-WORT-GEWICHT","title":"Zahl-Wort-Gewicht is a three-timescale representation invariant for FRANK","domains":["storage-state-memory","frank","synthetic-clay","lora"],"topics":["state-representation","gwt","lora","multi-timescale"],"epistemic_class":"CURRENT_SOURCE_GROUNDED_ARCHITECTURE_HYPOTHESIS","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:59:00+07:00","source_refs":["user:Frank-Architektur.md sha256:98afa4eda69dbe0253ea482a5338cfbbed212af2fba5d45af0fd51786b17559c","research_entity/trigger_runs/clay/clay-20260808T0542p0700-chatgpt-secondary/FINAL_REPORT.md"],"confidence":0.92,"verification_required":true,"falsifier_or_next_test":"Ablate the representation boundary in matched training/inference runs and test telemetry parroting, state-grounded behavior, generalization and LoRA contamination."}
RAE_META -->

### Core
Current FRANK separates one state across three representational timescales: **Zahl** (exact DB / `[INNER_WORLD_EXACT]`), **Wort** (semantic GWT projection), and **Gewicht** (slow disposition learned into LoRA). This is not merely serialization; it is a control boundary between exact observables, active self-description and long-term learned disposition.

### Clay mapping
HSCK-G7's exact canonical events, multi-resolution active projection and slow adaptive memory map naturally onto this existing FRANK separation. A future Semantic Runtime should preserve the separation even if databases/processes are collapsed.

### Failure mode
Collapsing raw numerical telemetry directly into the learned language path risks teaching the 4B to narrate instrumentation instead of using it as latent state. Conversely, removing the exact layer destroys audit/replay. The architectural target is therefore shared semantics with distinct representations, not one universal state format.
