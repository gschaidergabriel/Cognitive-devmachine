<!-- RAE_META
{"packet_id":"KMP-FRANK-20260808-WORKSPACE-SEMANTIC-PROJECTION","title":"Workspace winner semantics must be separated from prompt serialization","domains":["frank","gwt","claycode"],"epistemic_class":"OPEN_ARCHITECTURE_DELTA","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","run_id":"20260808T0610+0700-chatgpt-secondary-r2","confidence":0.82,"verification_required":true,"falsifier_or_next_test":"Run matched-budget truthful/shuffled/no-ignition winner interventions and record token order/detail."}
RAE_META -->

### Core
Current FRANK focus is rendered by putting the winner first and in fuller detail. C4 makes the semantic `WorkspaceEpisode` (candidates/salience/winner/ignition/frame) authoritative and treats the text broadcast as a deterministic reader projection.

### Evidence / boundary
ACL 2026 work demonstrates large prompt-order sensitivity in causal-attention LMs, so a change caused by reordering/compression cannot automatically be attributed to a separate GWT mechanism.

### Implication
Counterfactual winner tests must preserve/record candidate content, total token budget, order and projection policy so the mediated causal path is identifiable.
