# Level 0 Swarm Execution Law

**Status:** PROJECT_OWNER_FIXED
**Trigger:** exact `666`
**Applies while:** `666_RELEASE_GATE != PASS`
**Home:** repo-native research center / `center`

## Core invariant

An exact `666` while Level 0 is open does not mean "run one isolated archive shard".

It means:

`JOIN/RESUME ONE SHARED LEVEL-0 SWARM CAMPAIGN -> COORDINATE AVAILABLE WORKERS -> EXHAUSTIVELY PROCESS THE FROZEN DRIVE + PROJECT-FRANKENSTEIN CORPUS -> RECONCILE -> AUDIT -> PASS`

The campaign is persistent in repository state and remains `ACTIVE` until Level 0 PASS. Every later exact `666` joins the same campaign; it never restarts Level 0 and never forgets already completed work.

The exhaustive source-completion law is `research_entity/global/LEVEL0_EXHAUSTIVE_CORPUS_COMPLETION_LAW.md`.

## Swarm behavior

Every available Level-0 worker must behave as a peer in one research organism:

1. pulse/read the current center, frozen source epochs, manifests, tasks, leases, receipts and rest-obligation matrix;
2. discover what other workers are already doing before choosing work;
3. claim the highest-value non-overlapping open shard that advances exhaustive completion;
4. publish the lease/task so peers can route around it;
5. work the shard immediately using the fastest safe method: recursive enumeration, hashing, exact dedupe, structured parsing, bulk extraction, code/data analysis, experiments/replay, history clustering and semantic synthesis as appropriate;
6. publish partial material findings early when they affect another worker's current work;
7. cross-read peer receipts when dependencies or overlap appear;
8. if a peer has already solved the same obligation, stop duplicate work at the next safe point, consume the peer result and pivot to another open obligation;
9. write compact receipts/manifests/deltas back to the shared repo immediately;
10. release leases and mark workers COMPLETE when a shard closes;
11. immediately select another non-overlapping open obligation when execution capacity remains;
12. continue until the current execution surface is exhausted or the Level-0 release gate passes.

No leader is required for truth. Evidence outranks worker rank. Coordination uses leases, CAS, receipts and shared rest matrices rather than a central human dispatcher.

## Persistent-campaign law

`666` creates/resumes a campaign, not a one-shot task.

- The campaign status stays `ACTIVE` across sessions/instances until PASS.
- Newly opened workers that receive exact `666` discover the campaign and join it.
- Existing active workers consume new peer deltas at safe points and may pivot when higher-value work or overlap is discovered.
- Completed shards are immutable evidence inputs; they are not redone unless explicit replication/falsification is justified.
- Owner messages that add new frozen source material before PASS update the source epoch and create new obligations; workers reconcile the delta without discarding prior valid work.

Workers may not claim that unavailable or unscheduled instances are running in the background. "Swarm" means all workers that are actually available/active coordinate through the repo; persistent state ensures continuity when more instances join later.

## Work-selection policy

Priority order while exhaustive completion is open:

1. denominator/source-identity blockers that prevent exact accounting;
2. recursively open frozen Drive roots;
3. Project-Frankenstein frozen-head tree and history obligations;
4. high-information semantic/code/data shards;
5. exact duplicate/version/supersession clustering;
6. cross-source Drive <-> Project-Frankenstein reconciliation;
7. branch feedback and historical earned-work mapping;
8. final audit/release-manifest validation.

Do not open unrelated research fields before Level 0 PASS. Domain discoveries are routed into their branches as feedback while the worker continues Level-0 completion.

## Exhaustive processing requirement

Sampling is allowed only for prioritization, family discovery and throughput estimation. It never satisfies completion.

Every frozen source unit must receive a deterministic disposition under the exhaustive corpus completion law.

The swarm optimizes wall-clock time through parallelism and deduplication; it never reduces coverage to satisfy the 3-hour target.

## Collision and consistency law

- one active lease per ordinary shard;
- explicit replication is a separate task with a falsification/replication purpose;
- hot shared files use compare-and-swap/current-SHA updates;
- CAS failure means reread/merge/pivot, never force-overwrite peer work;
- no duplicate earned-work credit;
- source/manifests outrank stale workspace summaries;
- newer frozen source epochs supersede older denominator epochs without invalidating still-identical completed child evidence.

## Completion transition

When exhaustive Drive + Project-Frankenstein accounting, cross-source reconciliation, feedback, earned-work audit and release-manifest validation reach PASS:

1. atomically mark `666_RELEASE_GATE = PASS` in authoritative program state/workspace;
2. persist the final Level-0 release manifest and audit receipt;
3. stop archive-assimilation dispatch;
4. future exact `666` switches to post-Level-0 emergent stochastic research-field genesis.

Compact invariant:

`666 + L0_OPEN = SWARM UNTIL L0_PASS`

`SWARM = AVAILABLE WORKERS + SHARED REPO STATE + NONOVERLAPPING LEASES + LIVE CROSSREAD + IMMEDIATE PIVOT + EXHAUSTIVE CORPUS`
