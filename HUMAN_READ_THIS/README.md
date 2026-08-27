# Project Frankenstein — what this repository is

Project Frankenstein is a research and engineering effort about building a computer system that can keep useful state, remember evidence, make bounded decisions, act through explicit effect paths, inspect what happened, and use the verified outcome on the next cycle.

The practical loop is:

```text
state -> memory -> decision -> effect request -> effect gate -> observed result -> verified re-entry
```

The current product name in the canonical research authority is **EntityOS**. The integrated cognition/compute architecture is **HCU**. Historical names such as Frank, ClayVerse, Mini Entity, Xeno and XCU are useful provenance, but they are not separate current products or truth authorities.

## What exists and what does not

The repository contains real source, experiments, receipts, failed attempts, research notes, historical donor systems and newer EntityOS/HCU work. Those categories are deliberately not flattened together.

A source file existing does not prove it ran. A passing component test does not prove the whole system works. A model saying something repeatedly does not turn it into a measured fact. Negative results stay visible because they explain why later architecture changed.

As of canonical `main` at `854f6bc87780f4a5242489a6c807d186b16a8c3d`, current supervisor state is **9.13 HARD_OFF** for provider execution: provider routes are not admitted, Together is forbidden, and paid fallback is forbidden. The newly committed 72-hour Frankenstein Bauleiter/Bugfixer provider loops are therefore **quarantined/non-operative as execution authority**, even though their local non-network orchestration tests were reported green.

That distinction matters: a useful mechanism can exist in source while still being forbidden to execute in the current authority epoch.

## The core engineering ideas

### UnifiedDB / one canonical state substrate

The project moved away from fragmented state spread across many independent stores toward one canonical deterministic substrate. “One substrate” does **not** mean one giant untyped file. It can contain many typed tables, journals, indexes, policies and rebuildable projections. High-rate transient sensor state may still live in RAM.

### Emergent Retrieval

`Emergent Retrieval` is the project term for relevance that appears when independently stored evidence dimensions overlap at query time: semantic similarity, time, causal lineage, current state, goals, perception, effects, confidence and provenance. It does not mean information appears from nowhere.

### Self-reflection with an exit

Reflection is treated as an engineering control operation, not a consciousness claim. The useful form is:

```text
inspect state/outcome -> detect mismatch -> propose correction -> store/retrieve correction -> change later behavior -> ACT / ASK / WAIT / re-observe
```

Reflection that only produces more reflection is a failure mode.

### HCU and GRID

HCU is the current integrated cognition/compute architecture. GRID-style cells are logical request-scoped function slots, not permanent personalities and not proof of equal numbers of resident models. Logical scale and physical decode concurrency must be measured separately.

### Global J-Space / GWT

Global J-Space/GWT is a causal coordination hypothesis and instrumentation target. Coherent text, recurrence, model self-report or majority agreement are not enough to prove hidden-state causality. Model-specific traces, interventions, lesions/shuffles/rescues and exact provenance are required for promotion.

## Why the repo contains contradictions

Because the project is research. Older documents may describe ClayVerse as the endpoint; newer authority says EntityOS. Older provider plans may say a paid run is available; current 9.13 authority says zero paid runs. Some model-generated proposals invented infrastructure that did not exist. Those conflicts are evidence and should be classified, not edited away into a cleaner story.

## People and provenance

Lead researcher/developer: **Gabriel Gschaider**. Institute director/developer: **Dr. Andreas Unterweger**. Project provenance: **iar.frank.ink**.

## Where to go next

- `DEV_SOURCE_RESEARCH/README.md` — technical evidence map and current research frontier.
- `AI_START_HERE_DO_NOT_SCAN_REPO/README.md` — minimal installer/agent entry contract.
- `research_entity/` — research archive and current authority surfaces.
- `the artefact/` — product/release artifact workspace where present.

The root repository is still historically cluttered. Triggerword 3 is progressively moving the public navigation toward a small human layer plus a deep technical archive without rewriting evidence or creating duplicate authorities.
