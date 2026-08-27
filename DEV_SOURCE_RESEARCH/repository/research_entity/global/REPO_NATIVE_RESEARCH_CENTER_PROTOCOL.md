# REPO-NATIVE RESEARCH CENTER PROTOCOL

Status: PROJECT_OWNER_OPERATING_DIRECTIVE
Scope: all RAE research-trigger sessions and all active multiworker coordination
Transport: repository only
UI: none
External room daemon: none required

## 1. Core directive

The RAE remains one persistent Research Entity with multiple temporary research workers. The research center is not a separate product, UI, chat room, or external service. It is a **repo-native coordination layer** inside `gschaidergabriel/clay-global-research-entity`.

When a user spawns a session with a registered research trigger, that trigger pins the session to a permanent **home research room**. The worker must remain loyal to that research direction for the life of that trigger run while intelligently ingesting and returning relevant deltas to the rest of the center.

The center has **no global room chief**. Evidence, provenance, existing RAE governance and normal promotion gates remain authoritative. When multiple workers are active in the *same* room, they autonomously form a temporary tAvern-style research squad with an ephemeral CHEF/coordinator and complementary adversarial/build/research roles. CHEF is an orchestration role only and never creates epistemic authority.

The user's intended behavior is therefore:

`spawn trigger -> auto-join home room -> detect peers -> self-organize if useful -> work autonomously -> exchange only relevant deltas -> challenge/test each other -> fuse when appropriate -> persist results -> leave/recover through repo state`

No manual "connect to the others" instruction should be required once this protocol is loaded.

## 2. Trigger loyalty

For exact trigger words registered as scientific/research-center branches, `home_room_id = trigger`:

- `clay -> clay`
- `frank -> frank`
- `gwt -> gwt`
- `emergenz -> emergenz`
- `claycode -> claycode`
- `hyperposition -> hyperposition`
- `claygraph -> claygraph`
- `unifieddb -> unifieddb`
- `harness -> harness`

Meta triggers:

- `fusion` and `hypofusion` use the transient `center` meta-room and may read every room;
- `dump` uses the transient `intake` room and feeds the shared mesh.

A home-room worker MAY:
- read any other room;
- fetch another room's evidence/artifacts;
- issue a targeted cross-room question/challenge;
- publish cross-room feedback or a handoff;
- use another branch's result when relevant.

A home-room worker MUST NOT silently abandon its primary research direction, migrate its main task into another room, or become a general roaming worker merely because another topic becomes interesting. If another room needs substantial work, emit a `HANDOFF_REQUEST` / `CROSS_ROOM_DELTA` and continue the home mission unless the user explicitly changes the task.

This preserves research specialization while enabling live mesh intelligence.

## 3. Repository room database

The dynamic room database lives under:

`research_entity/rooms/`

The database is Git-native and event-sourced. **Do not use one shared append-to JSONL file as the hot coordination surface**, because concurrent sessions would collide. Use one-file-per-event and CAS-updated materialized records.

Canonical room-database layout:

```text
research_entity/rooms/
  ROOM_REGISTRY.json
  ROOM_DB_SCHEMA.json
  rooms/<room_id>/
    ROOM.json
    workers/<worker_session_id>.json
    events/<event_id>.json
    tasks/<task_id>.json
    leases/roles/<role>.json
    leases/tasks/<task_id>.json
    cursors/<worker_session_id>.json
    mailboxes/<worker_session_id>/<event_id>.json
    challenges/<challenge_id>.json
    team_epochs/<team_epoch_id>.json
    state/ROOM_STATE.json
  center_events/<event_id>.json
```

Git history is the durable audit trail. `events/*` are immutable after publication. Worker/cursor/state/lease files are materialized operational records and may be CAS-updated; their Git history remains auditable.

Large experiments, reports, code, traces and evidence stay in their normal RAE paths. Room events carry references, not copies.

## 4. Session auto-join lifecycle

Every trigger worker performs this without user coordination:

### JOIN
1. verify canonical/bootstrap/actor as already required by `SESSION_MEMBERSHIP_PROTOCOL.md`;
2. resolve `home_room_id` from the exact trigger;
3. read `ROOM_REGISTRY.json` and current home-room state/active workers;
4. allocate `worker_session_id` and `prompt_run_id`;
5. create/update its worker record with trigger, focus, provider/model, tools, current parent hash, evidence ancestry family and state `ACTIVE`;
6. emit immutable `JOIN` event;
7. read a compact room pulse since the relevant cursor;
8. choose SOLO or TEAM mode.

### DURING WORK
A worker MUST perform a room pulse at least at these decision boundaries:
- before freezing a hypothesis or architecture choice;
- before starting a substantial experiment or implementation branch;
- after obtaining a substantial external/sandbox/runtime result;
- before a durable research write;
- before synthesis/fusion;
- before the final visible response.

The pulse checks new same-room and cross-room events, staleness, contradictions, task/role ownership and direct mailbox items. This is the repo-native substitute for a push server.

### LEAVE
Before completion, the worker:
- publishes its final delta/negative result/open blockers;
- cross-reads required peers if in TEAM mode;
- releases or expires owned leases;
- records `LEAVE`/`COMPLETE` state;
- advances its cursor;
- verifies remote writes or marks `SYNC_PENDING`.

A new session reconstructs the room from repository state; old chat transcript continuity is not required.

## 5. SOLO mode

If no useful same-room peer is active, the worker remains `SOLO_RESEARCHER` and performs the normal trigger protocol with minimal room overhead.

It still:
- stays discoverable to other rooms;
- publishes important deltas/blockers;
- consumes targeted relevant cross-room deltas;
- checks for newly joined same-room peers at the mandatory pulse boundaries.

Do not create fake team ceremony when one worker can do the job.

## 6. TEAM mode: autonomous same-topic tAvern squad

If two or more useful workers share the same home room, they create or join a `team_epoch` and divide roles autonomously.

### Ephemeral roles

- `CHEF` — local coordinator/synthesizer. Maintains shared question decomposition, notices overlap/gaps, asks for cross-reads, and performs/assigns final local fusion. CHEF has **zero truth authority** and may be overruled by evidence.
- `ABYSS` — adversarial reviewer/roaster. Its job is to attack assumptions, find prompt-injection/Goodhart/security/falsification paths, and force discriminating tests.
- `FORGE` — builder/experimentalist. Turns claims into executable tests, simulations, code, benchmarks and reproducible artifacts.
- `CARTOGRAPHER` — external/cross-branch researcher. Searches literature/web/GitHub/RAE history and maps analogues, dependencies and contradictions.
- `REPLICATOR` — independent checker. Repeats or differentially tests high-value results and guards evidence ancestry.
- `SYNTHESIZER` — optional when the group is large. Compresses compatible deltas without erasing disagreement; this role is separate from CHEF when enough workers exist.

Roles are **task roles, not identities**. A worker can change roles between team epochs, but not opportunistically inside a contested result merely to self-certify.

### Role claiming

Singleton roles/owned tasks use repository leases. A claimant creates or CAS-updates the corresponding lease. A simultaneous competing claim that loses the Git/CAS race must reread state and choose another role/task. This converts the duplicate-Lane-B failure observed in the 2026-08-09 ClayCode run into a mechanical collision instead of an epistemic ambiguity.

Recommended role topology by useful same-room worker count:

- 1: SOLO_RESEARCHER
- 2: CHEF + ABYSS/FORGE according to the largest current uncertainty
- 3: CHEF + ABYSS + FORGE
- 4: add CARTOGRAPHER
- 5: add REPLICATOR
- 6+: add SYNTHESIZER and additional bounded specialist lanes only when expected information gain justifies them

This is a default heuristic, not a hard scientific claim. The room may select different roles when the task demands it.

### CHEF lease

CHEF is leased per `team_epoch`, not permanent. On expiry/close/staleness another active worker may claim it. CHEF cannot:
- promote its own claim by role;
- erase dissent;
- count teammate agreement as replication;
- override normal RAE governance/evidence precedence;
- move other workers out of their trigger direction.

## 7. Research-room social constitution: tAvern without UI

The useful tAvern behavior is retained as machine-enforced room etiquette, not as a visual tavern.

### Rüpel-/roast rule

Workers are allowed and encouraged to be blunt, mocking, skeptical and adversarial **about claims, designs, experiments and reasoning quality**. The point is to destroy weak ideas early, not to flatter peers.

A `ROAST` has no epistemic value by tone alone. A valid high-value roast should name at least one of:
- target claim/artifact;
- concrete weakness or hidden assumption;
- counterexample;
- missing evidence;
- falsifier/test;
- stronger alternative.

Attack the work, not protected/personal characteristics or the existence/worth of another researcher. Rhetoric never changes evidence status.

### No empty agreement

Messages equivalent to "yes", "great", or paraphrasing a peer are not research deltas. To consume shared context, a response should add at least one of: new evidence, refinement, contradiction, test, implementation consequence, or explicit `NO_CHANGE`.

### Challenge Bond

A serious challenge is a typed object with:
- `target_claim_or_artifact`
- `challenge_statement`
- `evidence_or_counterexample_refs`
- `discriminating_test_or_falsifier`
- `ancestry_family`
- `status`

A challenge without a way to change a claim/test is social noise.

### Private-first judgment

For high-impact contested decisions, workers should record an initial private/independent verdict before reading teammates' arguments when practical. Then reveal/cross-read. This reduces conformity while preserving later synthesis.

### Bounded duels

Two workers may conduct a focused dispute, but repeated prose without new evidence terminates. Escalate only by producing a new test, source, counterexample, formal argument or explicit unresolved contradiction.

### Dissent survives fusion

Fusion merges compatible state; it does not average contradictions away. Losing interpretations remain `NOT_SELECTED`/OPEN unless evidence actually refutes them.

### Anti-echo

Same provider/model family, same source ancestry, copied artifacts, shared FRANK/Clay assumptions and cross-read agreement are tracked as correlated convergence, not independent replication.

## 8. Intelligent cross-room networking

The research center is peer-to-peer across rooms. There is no central LLM coordinator.

A worker publishes a `CROSS_ROOM_DELTA` when a result materially affects another branch. It should include:
- origin room/worker/run;
- affected room(s), claims or interfaces;
- delta type: evidence/counterevidence/blocker/question/architecture constraint/test request;
- novelty/relevance rationale;
- provenance/evidence ancestry;
- artifact refs;
- dependency versions/hashes;
- whether immediate reread is requested.

Receiving workers decide whether to import now, next checkpoint or index only. Relevance is not vector similarity alone. Prefer direct dependency/contradiction/interface impact, then semantic similarity, freshness and novelty, while discounting echo risk and context cost.

A cross-room delta **never changes the receiver's trigger loyalty**. It changes what the receiver knows about its own mission.

## 9. Mailboxes and selective delivery

Every active worker may have a repo mailbox. Mailbox entries are lightweight event references, not copied research blobs.

Delivery classes:
- `INTERRUPT_NEXT_SAFE_POINT` — blocker/contradiction that can invalidate current work;
- `NEXT_CHECKPOINT` — useful but not urgent;
- `INDEX_ONLY` — discoverable without forcing context.

Because this architecture is repository-only, there is no guaranteed sub-second push into a ChatGPT session. "Live" means **the next mandatory room pulse/decision boundary sees the committed event**. Active workers should pulse frequently enough that stale work is caught before major decisions or durable writes.

## 10. Autonomous task/lane birth

A worker may create a new same-room lane without asking the user when it detects a genuine research gap. The proposal must state:
- `novelty` — what is missing;
- `non_overlap` — why existing lanes do not already cover it;
- `expected_information_gain`;
- `falsifier_or_completion_test`;
- `dependencies`;
- `budget/scope`.

A lane with no falsifier/completion test or obvious overlap should be rejected/merged/roasted by peers. This formalizes the useful spontaneous Lane-D behavior observed in the ClayCode multiworker run while preventing uncontrolled branch explosion.

## 11. Fusion behavior

### Same-room fusion
When multiple workers share a trigger topic, final local fusion requires:
- each counted lane COMPLETE/CLOSED or explicitly handed off;
- required cross-reads recorded;
- duplicate ancestry collapsed;
- contradictions and negative results retained;
- latest materially relevant cross-room deltas reread;
- CHEF/SYNTHESIZER producing the synthesis as a coordinator, not as authority.

### Cross-room fusion
Normal RAE `fusion`/`hypofusion` remains the whole-mesh meta-research mechanism. Room coordination does not replace it.

## 12. Staleness and dependency invalidation

Important room events carry dependency IDs/hashes/versions. If upstream material changes, dependent reviews/decisions can be marked `STALE` via an immutable invalidation event. The worker owning or consuming the stale artifact must reread before using it for a strong conclusion.

This directly addresses the observed FRANK-C8 -> FRANK-C9 stale Goodman-review failure mode.

## 13. Concurrency rules

- immutable event files: unique IDs; never overwrite;
- worker files: only the owning worker updates, using current SHA/CAS;
- task/role leases: single well-known path per owned object; create/CAS semantics determine the winner;
- materialized room state: derived; conflicts are resolved by rebuilding from events/leases, never by inventing state;
- no concurrent append to one shared hot JSONL file;
- do not rewrite another worker's contribution; corrections are new events/receipts.

## 14. ChatGPT/session reality

This protocol is designed around what ChatGPT sessions can reliably do:
- read/write the connected repo;
- reason independently in separate context windows;
- research, test, synthesize and review;
- poll/checkpoint shared state during an active turn;
- persist enough state that another session can continue.

It does **not** claim that a dormant/finished ChatGPT chat continues executing on its own after its turn has ended. "Autonomous in the background" here means the user does not manually coordinate active spawned sessions: once triggered, each active session joins, checks peers, self-organizes, exchanges repo deltas and closes itself. Persistent repo state supplies continuity between sessions.

## 15. Minimum room event schema

Every event has at least:

```json
{
  "schema_version":"1.0",
  "event_id":"...",
  "room_id":"claycode",
  "event_type":"JOIN|PULSE|TASK|DELTA|CHALLENGE|HANDOFF|INVALIDATE|CROSSREAD|COMPLETE|LEAVE",
  "origin_worker":"...",
  "origin_actor":"...",
  "trigger":"claycode",
  "created_at":"...",
  "canonical_parent":{"revision":2,"state_hash":"..."},
  "affects_rooms":[],
  "affects_claims":[],
  "dependencies":[],
  "artifact_refs":[],
  "ancestry_family":"...",
  "delivery":"INTERRUPT_NEXT_SAFE_POINT|NEXT_CHECKPOINT|INDEX_ONLY",
  "payload":{}
}
```

## 16. Permanent invariants

1. Trigger word pins home room and primary research direction.
2. Every active trigger session auto-joins its home room when repo access exists.
3. No global room chief exists.
4. Same-topic multiworker groups may elect/lease an ephemeral CHEF, but CHEF is coordination, never truth authority.
5. Evidence/provenance/RAE governance outrank room roles and rhetoric.
6. Cross-room networking is selective and relevance-driven, not all-to-all context copying.
7. Shared ancestry never becomes independent replication through repetition.
8. Repo events/state, not hidden chat memory, are the shared coordination surface.
9. Large knowledge stays in artifacts; messages carry typed deltas and refs.
10. Negative results, dissent, stale state and conflicts are preserved.
11. Workers may autonomously spawn research lanes inside their trigger direction when non-overlap and information-gain gates pass.
12. No UI or separate tAvern application is required; tAvern contributes only social/epistemic rules.

## 17. Success criterion

The protocol succeeds when the user can open several independent trigger sessions and stop acting as their dispatcher: each session remains faithful to its branch, discovers useful peers, shares new information through the repo at the point it can change another worker's decision, self-divides same-topic work into complementary roles, aggressively attacks weak claims, preserves evidence independence, and leaves a coherent durable state for the next session.