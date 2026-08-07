# RAE-vNext Master Research Trigger Protocol

## Purpose

This protocol governs every reserved research trigger in `RESEARCH_TRIGGER_REGISTRY.json`.
A trigger is a research command, not a conversational topic hint.

## Exact trigger semantics

A trigger fires only when the entire trimmed user message equals one registered trigger word, case-insensitively. Ordinary prose containing a trigger word does not fire the protocol.

## Mandatory boot

1. Verify remote Canonical revision/hash and actor identity.
2. Compile a task-specific RAE context; do not eagerly read the whole repository.
3. Load relevant CURRENT/OPEN/SUPERSEDED/REFUTED/NEGATIVE_RESULT claims, active experiments, micro-packets, topic packets and direct source evidence.
4. Load the trigger-specific protocol.
5. Record a trigger-run manifest with actor/model/runtime provenance.

If Canonical cannot be verified: `DEGRADED_UNJOINED`. Research may proceed LOCAL_ONLY but no shared-state promotion may be claimed.

## External capability policy

All trigger runs must follow:

`research_entity/global/EXTERNAL_RESEARCH_VERIFICATION_POLICY.md`

and select declared providers through:

`research_entity/global/EXTERNAL_RESEARCH_TOOL_REGISTRY.json`

Credential values must come only from the runtime environment/local ignored `.env`/secret store and must never be written into canonical research artifacts.

## Research cycle

Every full research trigger executes the following closed cycle unless its domain protocol explicitly narrows a phase.

### Phase A — Evidence grounding

- Re-read the latest compressed RAE knowledge relevant to the trigger.
- Re-ground high-impact claims against raw/project sources when available.
- Import new chat/current-turn evidence separately from canonical claims.
- Preserve contradiction and negative-result lineage.
- Separate measured data, imported source claims, user reports, model inference and web evidence.

### Phase B — Fusion 1

Create an explicit compact synthesis of:
- current project evidence;
- relevant historical results;
- unresolved contradictions;
- active experiments;
- architecture/runtime constraints;
- known negative results.

Do not perform web confirmation before this first independent fusion unless a claim is unintelligible without source resolution.

### Phase C — Hypothesis generation 1

Generate falsifiable hypotheses and counterhypotheses. For the `clay` master trigger target at least 50 materially distinct hypotheses; specialized triggers target enough hypotheses to cover the uncertainty frontier without padding.

Each hypothesis should contain:
- mechanism;
- expected observation;
- strongest counterprediction;
- falsifier;
- cheapest/highest-information test;
- affected domains;
- epistemic prior/source lineage.

### Phase D — Hypothesis-guided external research

Search token-efficiently by hypothesis cluster, not by one search per hypothesis.
Mandatory external surfaces when available:
- arXiv / primary papers;
- GitHub / source code / issues / benchmarks;
- Reddit for practitioner failure modes and community observations;
- authoritative documentation and primary technical sources where relevant.

Use registered scholarly/search capabilities where fit for purpose, including OpenAlex, arXiv, Semantic Scholar, Crossref, Tavily, Exa and credential-free fallbacks when available in the executing runtime. Search-provider output is discovery evidence; prefer the discovered primary or authoritative source for verification.

Before promoting an externally verifiable factual or scholarly claim, perform at least one fit-for-purpose external verification step when technically available and relevant. Do not treat repeated search-index metadata as independent confirmation of the same underlying source.

Reddit is anecdotal evidence unless independently reproduced.
GitHub code/benchmarks are implementation evidence, not automatically scientific evidence.
Preprints remain preprints.

### Phase E — Fusion 2 + pattern matching

Fuse internal and external evidence. Search for:
- convergent mechanisms across domains;
- contradictions;
- equivalent implementations;
- hidden common bottlenecks;
- boundary costs;
- causal direction alternatives;
- Goodhart failure modes;
- representation-vs-mechanism confusions;
- opportunities for intervention.

Pattern matching must never upgrade correlation to causality without intervention or equivalent causal evidence.

### Phase F — Hypothesis generation 2

Create transformed second-order hypotheses where the evidence changes the model. Retire, split or weaken first-generation hypotheses when warranted.

### Phase G — Empirical work

Use available software tools to execute the highest-information feasible tests: simulations, parsers, validators, benchmarks, ablations, lesion/rescue, replay, graph reductions, counterfactuals, fuzzing or instrumentation.

For claims materially dependent on executable behavior, make a reproducible execution attempt before strong promotion whenever feasible. Prefer the local sandbox/container when sufficient; use registered isolated/remote execution capabilities such as E2B, Judge0 or Piston when they add required isolation, dependencies or cross-runtime comparison. Record execution failure or unavailability as an evidence limitation.

Synthetic tests remain synthetic until replicated on the target substrate.

### Phase H — Synthesis and architecture delta

Produce:
- what changed;
- what survived;
- what was falsified;
- what remains open;
- architecture/runtime implications;
- prioritized next experiments;
- explicit claim boundaries.

### Phase I — Knowledge compilation

Convert durable new knowledge into surgical micro-packets and aggregate Topic Packets.
Micro-packets are the smallest independently retrievable research units and must follow `KNOWLEDGE_MICRO_PACKET_PROTOCOL.md`.

Update:
- source/provenance refs;
- hypotheses;
- negative results;
- experiments;
- claim lifecycle when justified;
- topic/domain links;
- method memory where a research method itself was learned.

Derived summaries never replace raw evidence.

### Phase J — Final report

Write a trigger-run report into:
`research_entity/trigger_runs/<trigger>/<run_id>/FINAL_REPORT.md`

Also write a machine-readable manifest/status for the run.

The final visible answer must end with the status block defined in `STATUS_FOOTER_PROTOCOL.md`.

## Promotion discipline

A trigger does not grant promotion authority.
High-impact claims require independent support, falsification effort and, when feasible, replication. Claude Code is lead adjudicator only when evidence remains underdetermined. Evidence outranks researcher rank.

## No false completion

Never claim 100% completion if requested source ingestion, web research, experiments, GitHub writes or report materialization were not actually completed and verified. The status footer must expose the honest completion estimate and outstanding items.
