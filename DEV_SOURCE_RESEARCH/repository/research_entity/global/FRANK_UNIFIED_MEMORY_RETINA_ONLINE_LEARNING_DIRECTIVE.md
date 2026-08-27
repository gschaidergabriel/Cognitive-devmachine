# FRANK Unified Memory <-> Retina Online Learning Directive

**Status:** PROJECT-OWNER FIXED ARCHITECTURE CLARIFICATION — NOT OPTIONAL  
**Recorded:** 2026-08-09  
**Applies to:** FRANK 0.1, dissolved Digital Retina, Unified Memory, UnifiedDB, ClayGraph, ClayCode, H1/H2/H3, adaptive visual learning and Clay 0.1 acceptance  
**Clarifies/supersedes where conflicting:** any wording in `FRANK_V0_1_ADAPTIVE_VISUAL_LEARNING_DIRECTIVE.md` or `RETINA_MICRO_VISUAL_CLASSIFIER.md` that makes an isolated Micro Visual Classifier the owner of visual online learning.

## Owner-fixed intent

FRANK's visual online learning must primarily happen through the **Unified Memory** and the knowledge FRANK has already accumulated.

Retina supplies current visual evidence. Unified Memory supplies prior verified knowledge, prior observations, entity identity, relations, context and learned visual history. Recognition and learning arise by comparing and recurrently coupling both.

Compact law:

`Retina sees now + Unified Memory knows before -> compare -> recognize / uncertain / conflict -> learn back into the same Unified Memory`

The intended consequence is:

`the more verified knowledge FRANK has about something, the more efficiently and robustly he should be able to recognize it again`

This is a target to measure, not permission for memory to fabricate sensor evidence.

## Unified Memory role

Unified Memory is the logical FRANK memory plane realized through the unified persistent state substrate, including UnifiedDB, ClayGraph and provenance-bearing event/experience history. It is not a second visual-only database.

For a recurring visual entity, Unified Memory may retain or connect:

- persistent entity identity;
- names/aliases and user corrections;
- semantic knowledge and relations;
- episodic encounters;
- visual observations and feature receipts;
- multiple views, lighting/state/layout variants;
- spatial/contextual associations;
- lookalikes and prior confusions;
- action/outcome-linked visual states;
- prototype/readout/calibration state where useful;
- support, recency, contradiction and provenance history;
- rollback/version lineage.

A visual learner must not maintain a disconnected semantic identity such as `class_17` when Unified Memory already contains the persistent real entity identity.

## Required recurrent path

`visual input`
`-> Retina sensor evidence + reusable features`
`-> activate/retrieve candidate entities and relevant prior knowledge from Unified Memory`
`-> compare current evidence against remembered visual + semantic/context constraints`
`-> KNOWN_HIGH_CONFIDENCE | KNOWN_NEEDS_CONFIRMATION | AMBIGUOUS | UNKNOWN | CONFLICT`
`-> familiar fast path OR deeper Retina / active sensing`
`-> evidence-gated update of the same Unified Memory`

The loop may recur several times. Memory may focus attention on discriminative regions/features; Retina may confirm, weaken, split or contradict the memory hypothesis.

## More knowledge -> better seeing

Verified prior knowledge can improve recognition by giving FRANK better candidate identities and more useful comparisons, for example:

- stable features across prior views;
- normal variation with angle, lighting, state or UI layout;
- expected nearby objects/regions/relations;
- known function/action/context;
- discriminative regions;
- known lookalikes;
- explicit evidence that would falsify the candidate identity.

This can reduce search space and direct visual compute toward high-information evidence.

Hard boundary:

`memory_prior != sensor_truth`

`recognition != observation`

`familiarity != evidence`

`contradictory current Retina evidence > unsupported memory expectation`

If prior and Retina disagree, FRANK must preserve `CONFLICT`, increase perception/active sensing as warranted and revise memory when evidence supports revision.

## What online learning updates

Online learning is broader than fitting a classifier. It may update:

- entity bindings;
- visual feature/prototype sets;
- variation ranges;
- semantic/context/spatial relations;
- confusion/lookalike relations;
- expected-vs-observed models;
- support/diversity/recency;
- open-set/calibration state;
- retrieval/index weights;
- optional tiny readout parameters;
- action/outcome visual transitions.

The durable product is richer Unified Memory with visual grounding. Tiny learned weights are optional implementation state.

## Micro Visual Classifier status

A prototype matcher, nearest-centroid index, linear classifier or tiny MLP may still be useful as a very cheap accelerator for candidate retrieval/familiarity scoring.

It is subordinate to the Unified Memory <-> Retina loop.

It is NOT:

- a separate semantic authority;
- a separate long-term memory;
- the canonical identity store;
- allowed to overwrite contradictory Retina evidence;
- allowed to turn its own one-shot prediction into training truth.

## Trust ladder

### GOLD
Explicit user correction/label, deterministic external truth or strongly verified action/outcome identity.

### SILVER
Repeated independent observations with consistent Retina evidence, memory/world continuity support and no material contradiction.

### BRONZE
One-shot pseudo-label, model caption, memory expectation or Micro Visual Classifier prediction alone.

BRONZE may be stored as candidate evidence but may not autonomously become positive memory/training truth.

## Resource law

The loop should remain operationally light:

- reuse Retina features already computed;
- retrieve a bounded active memory neighborhood, not all memory;
- use graph/vector/associative indices to narrow candidates;
- prefer prototype matching before learned heads;
- background fitting, if used, is bounded and low priority;
- over-budget learning pauses without disabling perception or memory retrieval;
- measure CPU, RAM, latency, state growth and retrieval cost on project hardware.

## Milestone consequences

### H1
Must implement an executable Retina <-> Unified Memory recognition/learning loop. A standalone classifier benchmark is insufficient.

### H2
Must reproduce the memory activation, evidence-vs-prior separation, entity-binding, visual-memory updates, contradiction handling and replay semantics in ClayCode/Clay state.

### H3
Must integrate this recurrent perception-memory loop inside the one-module/binary FRANK architecture as far down the runtime as feasible.

### UnifiedDB / ClayGraph
Are not merely storage behind a visual classifier. They are the durable semantic substrate for persistent visual identity, observations, relations, visual grounding and learning provenance.

### DOOMSDAY
Cannot PASS if visual online learning exists only as an isolated classifier disconnected from Unified Memory, if priors can override contradictory sensor evidence, or if self-predictions can recursively become truth without the trust gate.

## Acceptance additions

In addition to existing MVC tests, test:

- `UMV-E1` memory-assisted recognition gain across views/contexts;
- `UMV-E2` misleading-prior resistance;
- `UMV-E3` persistent entity binding across changing appearance;
- `UMV-E4` lookalike/conflict discrimination;
- `UMV-E5` knowledge-growth curve: recognition quality/cost as verified memory increases;
- crash/restart/rollback/replay of visual-memory state.

## Compact architecture invariant

`Retina = current visual evidence`

`Unified Memory = accumulated verified knowledge + prior grounded observations`

`Recognition = evidence-constrained comparison/coupling of both`

`Online learning = evidence-gated enrichment of that same Unified Memory`

`more verified knowledge should help FRANK see familiar things better; memory must never make him see what Retina did not support.`