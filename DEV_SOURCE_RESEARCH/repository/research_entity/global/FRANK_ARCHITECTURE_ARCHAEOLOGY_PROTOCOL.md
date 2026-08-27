# FRANK Architecture Archaeology & Originality Protocol

**Status:** MANDATORY ACTIVE KNOWLEDGE PIPELINE
**Primary historical source:** `gschaidergabriel/Project-Frankenstein`
**Current integration targets:** FRANK · ClayCode · Reference Harness · Clay Harness · GWT · ClayGraph · UnifiedDB · Hyperposition · Emergenz

## 0. Purpose

Project-Frankenstein is treated as an **invention and experimental lineage**, not merely a legacy codebase.

The project was developed through a cross-disciplinary design process. Therefore the archaeology pipeline MUST preserve the original functional logic of each mechanism before mapping it onto conventional software, neuroscience, AI or systems terminology. Normalizing a mechanism too early can erase the very design distinction that made it useful.

The pipeline reconstructs:

`problem -> invention -> implementation -> experiment/use -> success/failure -> bug/fix -> successor -> current reusable principle`

and separately:

`project origin -> external analogue/prior art search -> originality classification`.

## 1. Originality classes

Every material mechanism/version family receives one explicit `originality_class`:

- `PROJECT_ORIGINAL_CANDIDATE` — appears to originate inside Project-Frankenstein/FRANK history; prior-art search not yet sufficient.
- `PROJECT_ORIGINAL_SUPPORTED` — targeted prior-art search found no materially equivalent earlier mechanism in the searched scope; this is still not a legal patentability/world-first claim.
- `INDEPENDENT_CONVERGENCE` — materially similar mechanism found elsewhere without evidence of project derivation.
- `ADAPTED_FROM_EXTERNAL` — explicitly derived from external theory/system/paper but re-engineered for FRANK.
- `COMPOSITIONAL_INNOVATION` — components may be known, but the coupling/state machine/feedback organization appears project-specific.
- `KNOWN_STANDARD_MECHANISM` — conventional mechanism used substantially as known.
- `ANALOGY_ONLY` — biological/physical/philosophical naming is metaphorical and must not be mistaken for mechanistic identity.
- `PRIOR_ART_UNRESOLVED` — not enough evidence yet.

Rules:

1. A later external analogue does not retroactively make a project-created mechanism non-original.
2. Similar vocabulary does not establish equivalent mechanism.
3. A project mechanism may be original even when inspired by a known theory if its computational realization/coupling is materially distinct.
4. Never claim `world first`, patent novelty or universal novelty without a dedicated documented prior-art search and explicit limits.

## 2. One lineage record per mechanism family

Maintain a machine-readable record for every material subsystem/design family:

```json
{
  "mechanism_id": "...",
  "names_and_aliases": ["..."],
  "lineage": ["v1", "v2", "successor"],
  "first_known_project_commit": "...",
  "source_commits": ["..."],
  "source_files": ["..."],
  "source_papers": ["..."],
  "authorship_notes": "...",
  "originality_class": "PROJECT_ORIGINAL_CANDIDATE",
  "prior_art_status": "NOT_YET_SEARCHED",
  "problem_addressed": "...",
  "mechanism": "...",
  "state_inputs": ["..."],
  "state_outputs": ["..."],
  "equations": ["..."],
  "timing_and_order_constraints": ["..."],
  "dependencies": ["..."],
  "reported_successes": ["..."],
  "reported_failures": ["..."],
  "measured_results": ["..."],
  "evidence_classes": ["commit_message", "code", "test", "benchmark", "paper", "owner_observation"],
  "known_bugs": ["..."],
  "fixes": ["..."],
  "negative_results": ["..."],
  "superseded_by": ["..."],
  "current_best_practices": ["..."],
  "reuse_decision": "REUSE|ADAPT|RETEST|REJECT|ARCHIVE",
  "current_targets": ["frank", "claycode", "harness"],
  "open_questions": ["..."]
}
```

## 3. Evidence classes must remain distinct

For each historical claim distinguish:

- `IMPLEMENTED` — code existed;
- `EXECUTED` — code was run;
- `REPORTED_SUCCESS` — commit/report states success;
- `MEASURED` — explicit quantitative result exists;
- `REPLICATED` — result rerun in another environment/implementation;
- `CAUSALLY_SUPPORTED` — ablation/intervention isolates contribution;
- `OWNER_OBSERVATION` — empirical user/developer observation without controlled design;
- `FAILED_NEGATIVE` — mechanism failed or regressed;
- `SUPERSEDED` — later design replaced it.

A commit message is strong historical evidence of what developers believed/changed, but it is not automatically proof of its performance claim.

## 4. Mandatory extraction dimensions

For every important mechanism extract:

1. problem history;
2. first implementation;
3. major revisions;
4. exact functional logic before translating into conventional terminology;
5. equations/state transitions;
6. timing/boot/order sensitivities;
7. persistence/state assumptions;
8. cross-module coupling;
9. measured or reported successes;
10. regressions/bugs/failure modes;
11. resource/latency/cost behavior;
12. safety/authority implications;
13. what was removed and why;
14. what survived into successors;
15. project-original components or combinations;
16. known external foundations/analogues;
17. current FRANK/ClayCode/Harness implications;
18. the best next discriminating test.

## 5. Priority historical families

The initial inventory MUST include at least:

- E-PQ personality dynamics/homeostasis;
- Ego-Construct / digital embodiment;
- Self-Knowledge and capability grounding;
- Consciousness Daemon / persistent workspace;
- GWT / INNER_WORLD / broadcast variants;
- Thalamus multi-channel gating/habituation;
- AST attention controller;
- perception feedback loop;
- latent experience space;
- deep idle reflection;
- persistent goal management and intent queue;
- Nucleus Accumbens reward/RPE machinery;
- subconscious actor-critic/thought selection;
- neural conscience;
- ThoughtSeedVAE;
- hypothesis engine and experiment loop;
- invariant physics: energy, entropy, core-kernel, reality convergence;
- Quantum Reflector;
- Titan -> LCME memory lineage;
- Hippocampus/neural retrieval lineage;
- SOMA online adaptation / LoRA lineage;
- spatial/room embodiment lineage;
- Swarm/AURA lineage;
- boot/restart/checkpoint/snapshot/order behavior;
- tool routing / Needle precursors / tool-tag failures;
- state snapshots/rollback/identity persistence;
- Project Engine goals/world-model/autonomous-agent lineage;
- retired Genesis self-improvement path and its negative result;
- all LoRA generations and what each changed;
- all papers/architecture notes and experiments in historical documentation.

This list expands when new mechanism families are discovered.

## 6. Failure knowledge is mandatory active knowledge

Historical failures are current design constraints, not archival clutter.

Examples already visible in the Project-Frankenstein history include:

- runtime-injected architecture facts overriding trained LoRA behavior;
- stale runtime configuration;
- concurrent training/state corruption;
- file/restart/resource TOCTOU;
- memory retrieval contamination and graph-expansion regressions;
- cold-start learned modules degrading quality;
- parser/render/context transformations breaking downstream structured blocks;
- stale identity/name leakage after architecture changes;
- service restart races;
- sophisticated modules that failed to produce reliable benefit;
- small-model self-modification paths that could not reliably improve code.

Every new architecture/module should record which historical failures it is explicitly designed not to repeat.

## 7. Historical-source evaluation order

For each mechanism family, work chronologically and cross-check sources:

1. earliest relevant commit(s);
2. implementation files at representative versions;
3. tests/benchmarks/results;
4. architecture docs/manuals;
5. papers/research notes;
6. later fixes/replacements/removals;
7. current RAE research;
8. external prior-art/analogue search only after the native mechanism is understood.

This prevents hindsight from rewriting what the mechanism originally was.

## 8. Integration into current knowledge

Architecture archaeology outputs MUST feed current branches rather than remain a museum.

Required outputs include:

- `research_entity/architecture_archaeology/MECHANISM_INDEX.json`
- one lineage file per major mechanism family;
- `FAILURE_ATLAS.json`
- `SUCCESS_PATTERN_ATLAS.json`
- `BOOT_ORDER_AND_STATE_HISTORY.json`
- `LORA_HISTORY.json`
- `GWT_HISTORY.json`
- `MEMORY_HISTORY.json`
- `PERSONALITY_SELF_HISTORY.json`
- `ORIGINALITY_PRIOR_ART_QUEUE.json`
- branch-specific Topic Packets / Knowledge Micro-Packets;
- explicit Reference-Harness and Clay-Harness requirements;
- explicit ClayCode semantic requirements where historical mechanisms require representational support.

## 9. Harness gate

Neither the Reference Harness nor the Clay Harness may claim release PASS until:

- every frozen FRANK module has an archaeology record or an explicit `NEW_NO_HISTORICAL_PREDECESSOR` receipt;
- every known historically relevant failure has been checked against the new implementation;
- every reused mechanism has an explicit `REUSE|ADAPT|RETEST|REJECT` decision;
- boot/order/state dependencies have executable tests where applicable.

## 10. Current research-center law

`Project-Frankenstein history -> mechanism archaeology -> current branch knowledge -> executable Reference Harness -> Clay Harness -> new experiments -> updated archaeology`

The process is recursive: new experiments may change how old mechanisms are interpreted, but source provenance is never overwritten.
