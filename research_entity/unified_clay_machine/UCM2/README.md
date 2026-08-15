# UCM2 — Isolated Unified Clay Machine Research Body

UCM2 is the mutable second Clay Machine used by the Research Entity.

It exists to let frontier models develop, read, query, mutate and falsify a real Clay Machine without treating the main Clay/Frank/ClayVerse instance as an experimental scratchpad.

## Relationship to the main instance

- **Main instance:** reference/product/ClayVerse line; source of current VPS evidence, work reports, receipts and architectural requirements.
- **UCM2:** shadow research line; independently mutable and disposable/recoverable.
- **Research Entity:** may mutate UCM2 only.
- **Promotion:** UCM2 findings become bounded candidate knowledge through versioned reports; they do not automatically become main truth.

## Required cycle

1. Read newest verifiable main/VPS work reports and receipts.
2. Bind exact source repo SHA(s), VPS receipt ids and freshness.
3. Read latest UCM2 report and current UCM2 state.
4. Form hypotheses and counter-hypotheses about one UCM mechanism.
5. Mutate UCM2 only.
6. Let frontier models use/read the changed UCM2 as a machine.
7. Run executable tests, including negative/failure controls where possible.
8. Compare predicted and measured behavior.
9. Persist code/state/test artifacts.
10. Write a new append-only report under `reports/`.
11. Commit the full cycle to the repository.

## Intended internal shape

UCM2 should converge toward:

- fluid typed UnifiedDB/state fabric;
- modules/organs represented by identity, function, state, policy, lineage and readouts;
- integrated wiki/knowledge/memory;
- durable state-machine state;
- world/self model state;
- Hyperposition and possibility-state objects;
- provenance, transactions, epochs, replay and recovery;
- derived ClayGraph/topology rather than an independent truth store;
- a small runtime/binary that safely executes generic typed operations;
- one API used by frontier models and other harnesses;
- deterministic inspection/test surfaces.

## Isolation law

UCM2 must use its own paths, state files, ports/sockets, identities and test fixtures. It must never silently open or mutate main-instance canonical databases.

Any import from the main instance must be explicit, read-only and provenance-bound.

## Frontier-model law

A frontier model using UCM2 is an experimental worker. It may inspect and mutate UCM2 within the current research task, but model output alone is not evidence. Evidence requires measured state, executable tests or inspectable receipts.

## Freshness law

If direct VPS observation is unavailable, write `VPS_FRESHNESS_GAP` in the current report and bind to the newest actually verified receipt/commit. Never invent a newer VPS state.
