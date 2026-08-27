<!-- RAE_META
{"packet_id":"KMP-FRANK-C7-CORF-MOSAIC-RUNTIME","title":"FRANK C7 separates semantic organs from physical fault domains","domains":["clay","frank","systems-architecture"],"topics":["MOSAIC","runtime placement","fault domains","hot path"],"epistemic_class":"OPEN_ARCHITECTURE_CANDIDATE_WITH_LOCAL_PROXY_SUPPORT","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:51:00Z","source_refs":["research_entity/trigger_runs/frank/20260808T2051p0700-chatgpt-secondary-r3/FRANK_ARCHITECTURE.claycode.json","research_entity/trigger_runs/frank/20260808T2051p0700-chatgpt-secondary-r3/EXPERIMENT_RESULTS.json"],"verification_required":true}
RAE_META -->

### Core
C7 instantiates MOSAIC as the per-operation execution identity and adds an independent physical-placement layer. A causally distinct Clay organ need not be a separate process; authority/fault isolation can remain separate even when cognition-hot semantic stages share an address space.

### Boundary
Local CPython and synthetic fault proxies support the trade-off shape only. No live FRANK/Linux/Android promotion.

### Next test
Twin current runtime vs C7 hybrid placement with identical semantic receipts, measured IPC/copy cost, restart radius and replay.