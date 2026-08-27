<!-- RAE_META
{"packet_id":"KMP-FRANK-20260808-WORKSPACE-BROADCAST-CORRECTION","title":"Current FRANK cognitive workspace is workspace_broadcast, not the process-local global_workspace bus","domains":["frank-gwt","systems-architecture"],"topics":["workspace-broadcast","gwt","re-entry","source-freshness"],"epistemic_class":"CURRENT_SOURCE_GROUNDED_OPEN","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:59:00+07:00","source_refs":["user:Frank-Architektur.md sha256:98afa4eda69dbe0253ea482a5338cfbbed212af2fba5d45af0fd51786b17559c","research_entity/trigger_runs/frank/20260808T0551+0700-chatgpt-secondary-r2/FINAL_REPORT.md"],"predecessor_packet_ids":["KMP-FRANK-20260808-GWS-STATIC-REACHABILITY","KMP-FRANK-20260808-GWS-NO-COMPETITION"],"confidence":0.88,"verification_required":true,"falsifier_or_next_test":"Capture current workspace_broadcast.py plus a live daemon→DB→Core trace and verify candidate competition, ignition, winner, read and downstream effect."}
RAE_META -->

### Core
The newest supplied FRANK architecture measurement (2026-08-05) identifies `services/workspace_broadcast.py` as the live cognitive GWT path: six channels compete, a winner ignites at `ZUENDSCHWELLE=0.55`, one focus gets full detail, the result is persisted to `consciousness.db.workspace_broadcast`, and Core reads the newest row into `[INNER_STATE]`. `services/global_workspace.py` is the older/process-local bus whose isolation previously caused a cross-process visibility failure.

### Revision
This supersedes the stronger Cycle-2 interpretation that current FRANK may lack a real competition/selection workspace. That conclusion arose from inspecting the publicly visible repository branch, whose newest commit is dated 2026-04-05, while the supplied runtime architecture is dated 2026-08-05.

### Boundary
The supplied architecture is strong current-system source evidence but is not independently reproduced by this ChatGPT worker. A live code capture/trace remains required before canonical promotion.
