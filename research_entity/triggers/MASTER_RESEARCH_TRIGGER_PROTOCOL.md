# RAE-vNext Master Research Trigger Protocol

## Purpose

This protocol governs every reserved research trigger in `RESEARCH_TRIGGER_REGISTRY.json`. A trigger is a research command, not a conversational topic hint.

## Exact trigger semantics

A trigger fires only when the entire trimmed user message equals one registered trigger word, case-insensitively. Ordinary prose containing a trigger word does not fire the protocol.

## Mandatory boot

1. Verify remote Canonical revision/hash and actor identity.
2. Compile task-specific RAE context; do not eagerly read the whole repository.
3. Load relevant CURRENT/OPEN/SUPERSEDED/REFUTED/NEGATIVE_RESULT claims, active experiments, packets and direct source evidence.
4. Load the trigger-specific protocol.
5. Load `research_entity/global/RESEARCH_TOOL_ORCHESTRATION_POLICY.md` and `tools/research_provider_router.py`.
6. Record trigger-run manifest with actor/model/runtime provenance.

If Canonical cannot be verified: `DEGRADED_UNJOINED`. Research may proceed LOCAL_ONLY but no shared-state promotion may be claimed.

## Mandatory provider gate

Before external research, classify each hypothesis cluster into any applicable classes:

- `scholarly`
- `bibliographic`
- `current_web`
- `implementation`
- `executable`
- `model_experiment`

Run `tools/research_provider_router.py plan` for the applicable classes and materialize the result into the run's `TOOL_EXECUTION_MANIFEST.json`.

Every planned `MUST_ATTEMPT` capability must be attempted while operationally available. If it cannot be used, record an explicit allowed fallback reason and continue automatically with the best legacy fallback. Quota/provider failure must never stop research when a viable fallback exists.

Typical bundles:
- scholarly: OpenAlex + arXiv; Semantic Scholar when operational;
- DOI/publication validation: Crossref;
- current web/source discovery: Tavily + Exa, with DDGS/native web fallback;
- implementation: GitHub/source inspection;
- executable claims: local sandbox first, E2B when operational/valuable, then Piston/Judge0 as suitable;
- model/representation experiments: target/local model plus Hugging Face when decision-relevant and quota permits.

Provider snippets/metadata are discovery evidence. Prefer retrieved primary/authoritative sources for verification.

Before strong claim promotion, validate `TOOL_EXECUTION_MANIFEST.json` with `tools/research_provider_router.py validate-manifest`. Unresolved required-tool violations block strong promotion but do not block an honest lower-confidence report.

## Research cycle

### Phase A — Evidence grounding

- Re-read relevant compressed RAE knowledge.
- Re-ground high-impact claims against raw/project sources when available.
- Import current-turn evidence separately from canonical claims.
- Preserve contradiction and negative-result lineage.
- Separate measured data, imported claims, user reports, model inference and web evidence.
- Use `tools/research_query.py` first when the local query plane is available.

### Phase B — Fusion 1

Create a compact synthesis of current project evidence, historical results, unresolved contradictions, active experiments, architecture/runtime constraints and known negative results.

Do not perform web confirmation before this first independent fusion unless a claim is unintelligible without source resolution.

### Phase C — Hypothesis generation 1

Generate falsifiable hypotheses and counterhypotheses. For `clay`, target at least 50 materially distinct hypotheses; specialized triggers cover the uncertainty frontier without padding.

Each hypothesis contains mechanism, expected observation, strongest counterprediction, falsifier, cheapest/highest-information test, affected domains and source/prior lineage.

### Phase D — Hypothesis-guided external research

Execute the provider plan by hypothesis cluster, not one search per hypothesis. Preserve source/query provenance and quota/fallback outcomes.

Mandatory evidence surfaces when applicable and available include scholarly literature, primary/authoritative documentation, GitHub implementation evidence and practitioner/field observations. Reddit remains anecdotal unless independently reproduced. Preprints remain preprints. GitHub code/benchmarks are implementation evidence, not automatically scientific evidence.

### Phase E — Fusion 2 + pattern matching

Fuse internal and external evidence. Search for convergent mechanisms, contradictions, equivalent implementations, hidden bottlenecks, boundary costs, causal alternatives, Goodhart failure modes, representation-vs-mechanism confusions and intervention opportunities.

Never upgrade correlation to causality without intervention or equivalent causal evidence.

### Phase F — Hypothesis generation 2

Create transformed second-order hypotheses where evidence changes the model. Retire, split or weaken first-generation hypotheses when warranted.

### Phase G — Empirical work

Execute highest-information feasible tests: simulations, parsers, validators, benchmarks, ablations, lesion/rescue, replay, graph reductions, counterfactuals, fuzzing or instrumentation.

For executable claims, make a reproducible execution attempt before strong promotion whenever feasible. Synthetic/remote results remain synthetic until replicated on the target substrate.

### Phase H — Synthesis and architecture delta

Produce what changed, what survived, what was falsified, what remains open, architecture/runtime implications, prioritized next experiments and explicit claim boundaries.

### Phase I — Knowledge compilation

Convert durable new knowledge into surgical micro-packets and Topic Packets. Update source/provenance refs, hypotheses, negative results, experiments, justified claim lifecycle, topic links and method memory. Derived summaries never replace raw evidence.

### Phase J — Final report

Write:
- `research_entity/trigger_runs/<trigger>/<run_id>/FINAL_REPORT.md`
- machine-readable run manifest/status
- `TOOL_EXECUTION_MANIFEST.json`

The final visible answer must end with the code-block status footer defined in `research_entity/global/STATUS_FOOTER_PROTOCOL.md`.

## Promotion discipline

A trigger does not grant promotion authority. High-impact claims require independent support, falsification effort and, when feasible, replication. Evidence outranks researcher rank. Provider prestige never overrides evidence quality.

## No false completion

Never claim 100% completion if requested source ingestion, provider attempts/fallback recording, experiments, GitHub writes, report materialization or required status output were not actually completed and verified.
