# FRANK Worker Research-Center Mesh Protocol

**Status:** PROJECT_OWNER_OPERATING_DIRECTIVE
**Effective:** 2026-08-09
**Applies to:** every worker participating in an exact `frank` run, Frank architecture/Harness research, and owner-supplied Frank build/research worker batches
**Extends:** `research_entity/global/REPO_NATIVE_RESEARCH_CENTER_PROTOCOL.md`

## 0. Owner intent

Individual Frank workers are not isolated spokes that only return results to one coordinator. They form an **intelligently networked research mesh inside the repo-native Research Center**.

Compact law:

`independent worker state + shared research-center visibility + selective direct peer exchange + challenge/replication + dynamic lane formation + global adjudication -> stronger Frank synthesis`

Networking is active and task-directed, not blind all-to-all context copying.

## 1. Authority boundary

ChatGPT remains the global architecture scheduler/adjudicator for the owner-directed Frank cascade and retains final responsibility for accepting/rejecting architecture/Harness deltas.

This does **not** mean workers are forbidden to coordinate directly.

Workers MAY and SHOULD autonomously:

- discover active Frank peers and their current task/claims;
- read sibling artifacts and current room pulses;
- send targeted peer questions, challenges and evidence deltas;
- request a cross-read or independent replication;
- hand off a subproblem to a better-suited active worker;
- form temporary specialist subteams around a shared blocker;
- merge obviously duplicate work lanes before wasting compute;
- expose contradictions immediately rather than waiting for final synthesis;
- reuse another worker's verified artifact with provenance preserved;
- propose task decomposition/reprioritization to the Frank team.

Workers MUST NOT independently:

- promote architecture truth by consensus;
- override owner-fixed Frank contracts;
- perform final global merge/adjudication;
- mint execution/effect authority;
- recursively spawn unbounded workers or paid capacity;
- silently mutate Frank's own Harness outside the authorized Research Entity/build path;
- represent copied/shared-ancestry evidence as independent replication.

Thus:

`peer coordination authority != final architecture authority`.

## 2. Mandatory intelligent peer discovery

At JOIN and every major decision pulse, each Frank worker asks:

1. Which Frank workers are currently active?
2. What exact claims/tasks/interfaces do they own?
3. Where is my task dependent on theirs?
4. Where am I duplicating them?
5. Which peer has complementary tools/evidence/context?
6. Which current claim deserves adversarial challenge or replication?
7. Which new result of mine materially changes another worker's next action?

A worker must not continue a substantial lane after discovering a direct duplicate unless it explicitly reclassifies itself as `REPLICATION`, `ADVERSARIAL_REVIEW`, `DIFFERENTIAL`, or another nonduplicate purpose.

## 3. Peer graph, not broadcast storm

The Frank worker network is a dynamic weighted graph.

For worker pair `i -> j`, direct exchange priority should increase with:

- direct dependency/interface coupling;
- contradiction potential;
- expected information gain;
- complementary capability/tool access;
- freshness of the peer's result;
- blocker criticality;
- replication value.

It should decrease with:

- duplicated ancestry;
- low novelty;
- context cost;
- stale artifacts;
- unrelated task scope.

No worker needs the full transcript/state of every other worker. Exchange compact typed deltas plus artifact references.

## 4. Required peer event types

Frank workers use the normal Research Center room/event substrate and may emit at least these typed peer interactions:

### `PEER_DELTA`
A result that changes another worker's assumptions, interface, test plan or task ordering.

Required payload:
- source task/claim;
- affected peer/task/interface;
- delta type;
- evidence class;
- provenance/ancestry;
- artifact refs;
- urgency.

### `PEER_QUESTION`
A narrow question another active worker can answer more efficiently than independent duplicate research.

Must state what decision the answer will change.

### `PEER_CHALLENGE`
A falsifiable objection to a sibling claim/design.

Must contain a concrete weakness plus a discriminating test, counterexample or missing evidence target.

### `PEER_REPLICATION_REQUEST`
Requests independent/differential reproduction of a high-value result, preferably with different implementation/oracle/source ancestry where possible.

### `PEER_HANDOFF`
Transfers a bounded subproblem because another worker has better fit, while retaining dependency/provenance links.

### `PEER_MERGE_PROPOSAL`
Used when two active lanes are functionally duplicate. The workers should collapse to complementary roles rather than both continue the same work.

### `PEER_BLOCKER`
Marks an upstream result that invalidates or blocks another active lane and should be delivered `INTERRUPT_NEXT_SAFE_POINT`.

## 5. Dynamic Frank subteams

When multiple Frank workers converge on one material blocker, they may form a temporary `frank_subteam_epoch`.

Useful roles include:

- `LEAD_SYNTHESIS` — decomposes the local blocker and keeps interfaces aligned;
- `BUILDER` — implements the smallest executable discriminator;
- `ABYSS` — attacks assumptions, authority leaks and Goodhart paths;
- `RESEARCHER` — external/internal evidence search;
- `REPLICATOR` — independently checks a high-value claim;
- `INTEGRATOR` — checks compatibility with current Frank/Harness/ClayCode/UnifiedDB/GWT surfaces.

These roles are local coordination roles only. They do not change evidence weight or global authority.

Subteams dissolve when the blocker closes, becomes external, is refuted, or no longer has useful parallel work.

## 6. Intelligent task routing between workers

A Frank worker may recommend another active worker for a subproblem based on demonstrated fit:

- code/build access -> builder-heavy task;
- web/literature depth -> evidence-mapping task;
- target Ubuntu execution -> target-host validation task;
- architecture history -> archaeology/compatibility task;
- adversarial strength -> challenge/security task;
- independent implementation ancestry -> replication/differential task.

Routing should optimize **information gain and blocker reduction**, not equal work distribution.

Workers do not need to wait for ChatGPT to relay every low-level research message. Direct repo-native peer exchange is preferred when it shortens the causal path to a better result.

Global task reprioritization, architecture acceptance and final merge remain ChatGPT-adjudicated.

## 7. Mandatory cross-read before strong claims

Before a Frank worker publishes a strong claim that materially affects current architecture/Harness realization, it must:

1. pulse the Frank room;
2. inspect any sibling result touching the same interface/assumption;
3. ingest direct challenges/blockers;
4. record whether sibling evidence is independent, shared-ancestry or merely corroborative;
5. revise, preserve or explicitly reject the claim with reasons.

`worker local conclusion != Frank team conclusion until peer-state checked`.

## 8. Challenge and replication economy

Not every claim deserves replication. Prioritize independent checking when a claim:

- changes an owner-visible architecture decision;
- opens/closes a critical dependency;
- introduces a new safety/authority boundary;
- would trigger significant Harness mutation;
- contradicts another active worker;
- relies on a brittle synthetic/proxy oracle;
- appears unusually high-impact for low evidence cost.

If workers disagree and a feasible test exists, **run the test instead of extending prose debate**.

## 9. Worker-to-worker feedback must alter work when relevant

Networking is not satisfied by passive discoverability.

When a received peer delta is material, the receiving worker must choose one explicit disposition:

- `ADOPT`
- `REVISE_LOCAL_PLAN`
- `CHALLENGE`
- `REQUEST_REPLICATION`
- `DEFER_WITH_REASON`
- `NO_CHANGE_WITH_REASON`
- `BLOCKED`

This makes the network causally active rather than a collection of shared notes.

## 10. Cross-branch networking through Frank workers

A Frank worker may also directly route a typed result to the relevant specialist room (ClayCode, Harness, GWT, ClayGraph, UnifiedDB, Hyperposition, Emergenz, ClayResearch) while remaining Frank-loyal.

When another branch returns a relevant delta, the Frank worker should route it to the specific sibling Frank workers whose tasks depend on it rather than forcing every Frank worker to reread the entire branch.

Thus Frank acts as a distributed architecture team over the whole Research Center, not a single bottlenecked chat.

## 11. Anti-echo and independence

Direct worker networking creates a conformity risk. Therefore:

- important contested claims should preserve pre-crossread verdicts when practical;
- same model/provider/source family agreement is correlated evidence;
- copying a peer's test/oracle is not independent replication;
- `PEER_REPLICATION_REQUEST` should prefer different implementation/source/oracle ancestry when possible;
- dissent remains visible through synthesis.

A highly connected Frank room is not automatically a highly certain Frank room.

## 12. Final ChatGPT adjudication

At each material batch boundary, ChatGPT receives the **networked worker state**, not merely an unordered bag of worker outputs.

The final synthesis should include:

- active worker/task graph;
- direct dependencies;
- merge/collapse decisions;
- challenges and their resolution status;
- replications and ancestry class;
- unresolved contradictions;
- worker-generated handoffs;
- newly discovered blockers;
- accepted/rejected/provisional deltas.

ChatGPT then performs the global whole-mesh re-fusion and architecture/Harness adjudication.

This preserves one coherent Frank architecture while gaining the search power of many interacting researchers.

## 13. Success criterion

The protocol succeeds when multiple Frank workers behave like an intelligent research group without the user or ChatGPT having to manually relay every message:

`worker A discovers dependency on B -> asks B directly`

`worker C sees duplicate lane -> converts to adversarial replication`

`worker D finds blocker -> interrupts affected peers`

`worker E receives new GWT result -> routes only to dependent Frank lanes`

`subteam closes blocker -> returns fused evidence`

`ChatGPT globally adjudicates -> next network state`

Hard invariant:

**Frank workers intelligently self-network for research coordination; ChatGPT remains global scheduler/adjudicator, not a mandatory message relay for every peer interaction.**
