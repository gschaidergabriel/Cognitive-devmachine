# FUSION 1 — current internal state

The owner-fixed semantics require one global active Frank execution, BUSY for every other caller, no silent abandonment of an unfinished current-user task, explicit current-user consent for task switching, and proactive acquisition only while IDLE.

Current main has made real progress on the outer presence problem: canonical UnifiedDB V15 carries holder identity, lease state, `lease_epoch`, expiry and fencing; the target test races holders and exercises stale/expired holder rejection. Concurrent GO work correctly observes a separate unresolved same-holder execution-identity gap.

The nested task-continuity surface remains structurally absent from V15: no task identity, task epoch, task state or consent-transition witness appears in the current presence schema/runtime/test. A computation derived from task A and delivered after an allowed A->B switch can therefore still carry a perfectly current presence `lease_epoch`. Presence fencing cannot distinguish it from task-B material.

The highest-value ATOMIC question is therefore not another global lock: **can task continuity be made a non-copyable causal resource so stale task-derived material becomes structurally impossible, and does that beat a conventional nested task fence?**

Constraints retained: self.root identity is unchanged; token/relay authority is unchanged; GWT salience never grants authority; effects retain their independent effect gate; task metadata is not SELF; no hidden task queue may execute while BUSY; final training remains unauthorized.
