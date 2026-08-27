# FINAL_VPS_TRAINING_READINESS_REPORT — Trigger-2 VPS Execution 2026-08-25/26

Coordinator: Claude Code (ai-core-node), executing `CLAY_TRIGGER2_VPS_TRAINING_RESEARCH_EXECUTION_PACKAGE_2026-08-25.pdf`
end-to-end on VPS `frank-api` (31.97.117.141, hostname `clayverse`), repo
`gschaidergabriel/clay-global-research-entity`. This is a decision surface,
not a narrative victory summary, per source doc §19.

**Credit boundary across this entire campaign: 0.** No positive training
rows were admitted at any point, by any of the sub-agents, at any phase.
This is deliberate and verified in every individual receipt.

## Gate table (source doc §19)

| Gate | Required final status | Actual result | Evidence |
|---|---|---|---|
| A02 repository-bound execution | PASS at requested immutable head | **PASS** | `executed_head=c14e67fd2ea3...` matches request exactly; dirty_before=dirty_after=false; all 4 focused test groups green |
| A03 authority replay root | PASS / mechanically bound | **PASS** | `OUTER_REPLAY_ROOT_SUFFICIENT` — empirically confirmed: mutated generation-authority manifest, re-ran an old row, it was rejected (digest mismatch) |
| Immutable genesis/history authority (nonempty history) | PASS | **PASS** (closed this campaign) | Extended `trigger2_generation_provenance_gate_v1.py` to bind genesis_state + full event_history to the trusted-generator authority; 5/5 new tests, zero regressions (1276→1281 passing) |
| OBSERVED evidence producer auth | PASS | **PASS** (closed this campaign) | New `trigger2_observed_evidence_producer_auth_gate_v1.py`; all 7 required negative controls pass; zero regressions (1281→1289 passing) |
| IN / NOT_IN fail-closed | PASS | **PASS** | Already fixed on main before this campaign started; verified, not touched |
| Branch-birth evidence | RESOLVED + tests | **PASS** (fixed this campaign) | `allow_empty_evidence=True` now requires exactly-empty lists instead of silently skipping validation; commit `f20c024a5` |
| Successor-dynamic ancestry lint | PASS / one current head | **PASS**, mildly stale | `ELIGIBLE_FOR_NEXT_GATE_NOT_ADMITTED` verified against ledger V26; ledger has since advanced to V33 via the autonomous system's own reaction — **not re-verified against V33, should be re-run before relying on it** |
| Rendered family/provenance/tokenizer ABI + nuisance audit | PASS | **NOT ATTEMPTED / OPEN** | Correctly deferred: this requires `trigger2_binding_router_factorial_generator_v3.py`, which stays quarantined by explicit stop-rule. Quarantine itself verified intact (zero references anywhere in the repo). |
| Ordered-history diagnostic dataset | scored | **NOT ATTEMPTED** | Unblocked once Phase 3 closed, but not built this campaign — pure time prioritization, not a blocker finding |
| Checkpoint identity (Qwen3.5-0.8B family) | COMPLETE for measured candidates | **PASS** | BASE, POSTTRAINED, TARGET_MEASURED (Josiefied-gabliterated) all identity_complete + loader_consumption_observed=true. No winner declared. |
| Matched baselines | scored | **PASS** (partial n) | 24-case extended pilot + 6-case cross-candidate + 5-seed reproducibility. See findings below — this is the most substantively informative part of the whole campaign. |
| J-Space causal metrology | C3 at declared scopes only | **PARTIAL** | Behavioral causal effect real & reproducible (sign-flip/lesion/permute all behave as predicted) — usable at the declared behavioral scope. Representation-divergence sub-metric is broken (instrumentation bug, not a null result) — **do not cite representation-divergence numbers from this campaign.** |
| Multi-seed reproducibility | run | **PASS** | 5 seeds, variance reported, one numerical-sensitivity arm kept separate from promotion set |
| HCU / variable-N system measurements | run | **BLOCKED, documented** | No sweepable logical-N interface exists in the repo as scoped — only schema validators for training rows. The VPS does run Zero's live production EntityOS/ClayVerse stack, deliberately not touched (out of authorized scope). This needs its own design task before it can be measured, not a measurement pass. |
| Cross-encoding semantic causality (§12.7) | tested | **NOT ATTEMPTED** | Not reached within this campaign's scope/time |
| Resource/throughput envelope | measured | **PASS** | All 3 candidates: ~2GB peak RSS, ~5-8 tok/s, 4 vCPU CPU-only, no swap touched, no outlier candidate |
| Forge→Distillery first positive pilot (Phase 16) | 1 packet, >0 tokens, replay +0/+0 | **NOT ATTEMPTED — correctly withheld** | Multiple explicit prerequisites remain open (nuisance/ABI audit, HCU/variable-N, cross-encoding, reliable representation-level J-Space evidence). Generating positive rows now would violate the source document's hard gate in §16 and §19. |

**Credit fields (every receipt, campaign-wide):** positive_rows_admitted=0,
accepted_dataset_tokens=0, positive_jspace_causal_credit=0,
trigger2_a02_runtime_credit=**established at component scope only**,
full_hcu_runtime_credit=0, whole_entityos_hcu_runtime_credit=0.

## Coordinator-level synthesis (my own hypotheses and implications, not admitted evidence)

### On the provenance-authority track (Track A)
Every gap this campaign found and closed (genesis/history content
provenance, OBSERVED producer authentication) had the same shape: a
receipt-schema/structural check existed and passed, but nothing verified
*who* or *what* actually produced the content behind that schema. My
reading is that this is a systemic pattern in how this project's gates have
been built so far — schema-and-digest correctness gets built first because
it's mechanically straightforward to test, and producer/identity
authentication gets deferred because there was no real external producer
yet to authenticate against. **Implication:** before wiring in any real
external data source (a live sensor, an API, a human-provided fact), a
useful standing practice would be to explicitly ask "does this gate check
schema validity, or does it check who is allowed to assert this schema is
true?" — those are different questions and this campaign found the second
one silently absent in two separate places. There may be more places with
the same latent gap that simply haven't been probed yet (this campaign
tested the two the source PDF specifically flagged, not an exhaustive
sweep of every gate in the repo).

### On the model-measurement track (Track B)
The single most decision-relevant finding of this entire campaign is
**Finding 1 + Finding 2 together, not separately**: the abliterated
checkpoint fails at correct abstention (fabricates a fictional stock
price), while the *official, non-abliterated* checkpoint fails at
DB-vs-simulation discrimination (the property this project structurally
cares about most). Naively, one might assume "pick the non-abliterated
model, it's safer" — but on the one axis this project treats as
load-bearing (persistent-DB-fact priority over speculative simulation),
the non-abliterated model is the one that gets it wrong. **My hypothesis:**
neither candidate is a clean choice on the evidence gathered so far; picking
either without a larger matched sample on both axes would be a decision
made on n=1 per candidate per axis, which is exactly the kind of premature
checkpoint-selection the source document's §11.2 explicitly warns against
("do not declare checkpoint winner without the matched pilot contract in
the current registry passing"). **Implication:** the next model-side
priority should not be Phase 11/HCU or cross-encoding — it should be
enlarging Finding 1 and Finding 2's sample size to more than n=1, because
those two findings currently look like they could each independently
disqualify a candidate, and right now neither has enough data to be
trusted as more than a hypothesis.

### On what "done" means here
This campaign closed every gate the original PDF marked as **P0/P1
priority** (A02, A03, genesis/history, OBSERVED auth, IN/NOT_IN,
branch-birth, successor-ancestry) and made substantial progress on **R1**
(checkpoint identity, baselines, causal probe, multi-seed, resources). It
did not close **P2** (rendered nuisance/ABI audit — correctly blocked by
design on the quarantined generator) or the **R2** systems-measurement work
(HCU/variable-N — blocked on a genuinely missing sweepable target, not a
resource or time shortfall). Both of the remaining gaps are honestly
"blocked on a prerequisite that doesn't exist yet," not "ran out of time" —
that distinction matters for anyone deciding what to schedule next.

## What actually happened during this campaign (operational note)

The target repository has its own live, autonomous process pushing
commits continuously (ledger `TRIGGER2_TRAINING_ARTIFACT_VERSION_LEDGER`
advanced from **V24** at PDF-preparation time to **V33** by the end of this
campaign — largely in direct reaction to the evidence this campaign pushed,
visible in commit messages like "post-VPS training reentry audit" and
"advance ledger v32 with baseline-vs-trainability scope"). This campaign
re-entered current `main` before every write, used `git fetch+ff+retry` on
every push, and — after a near-miss `git stash` collision between two
parallel sub-agents sharing one working directory in the first round — used
separate `git worktree` checkouts per parallel track in the second round.
No conflicts occurred in the second round.

## Artifact index

See `VPS_TRAINING_RESEARCH_INDEX.json` in this same archive for the full
file listing with SHA-256 hashes. Raw data lives in two places: this local
archive/ZIP, and `research_entity/global/j-space/research/vps_run_receipts/`
on `main` in the GitHub repo (all pushed, nothing held back locally-only).
