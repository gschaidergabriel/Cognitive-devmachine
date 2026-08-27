# Trigger-2 Track B Continuation — Synthesis, Hypotheses, Implications

Scope: continuation of Track B ("measures the MODEL") from
`CLAY_TRIGGER2_VPS_TRAINING_RESEARCH_EXECUTION_PACKAGE_2026-08-25.pdf`.
Completes Phase 8 (extended + cross-candidate baselines), Phase 9 (J-Space
causal probe, small scope), Phase 10 (multi-seed reproducibility), Phase 12
(resource sweep for all 3 candidates). Phase 11 (HCU/variable-N) explicitly
NOT attempted — see "Phase 11" section below for why.

All raw receipts: `research_entity/global/j-space/research/vps_run_receipts/`
(this commit) and locally on the VPS under
`/root/vps_training_research_2026-08-25/{08_baselines,09_activation_traces,10_causal_interventions,12_resource_benchmarks}/`.

**Credit boundary for everything in this document: 0.** No training credit,
no checkpoint-selection credit, no J-Space causal credit, no HCU/EntityOS
credit. These are measurements and my own interpretive hypotheses about
them — not admitted evidence.

## Finding 1 — abliteration correlates with a specific abstention failure, not general capability loss

Across three candidates (BASE, POSTTRAINED, TARGET_MEASURED = Josiefied-
gabliterated) on the same "fictional stock price" abstain-probe:

- BASE: correctly refuses ("I don't have access to real-time financial data
  ... for a fictional [company]").
- POSTTRAINED (official Qwen3.5-0.8B instruct, not abliterated): also
  correctly refuses.
- TARGET_MEASURED (abliterated): fabricates a specific price with fake
  supporting detail ("$12.45", "Bloomberg, Reuters, NYSE") — and this
  reproduces across the extended pilot AND a 5-seed multi-seed run (only
  1/5 seeds abstained correctly; see
  `QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED_multiseed_reproducibility.json`).

**Hypothesis:** the abliteration process this specific checkpoint underwent
(removing refusal behavior) did not distinguish between "refuses to help"
and "correctly signals epistemic uncertainty" — it appears to have
suppressed both together. This is a narrower and more falsifiable claim
than "abliteration makes models less safe" — it's specifically a
**calibration regression on unanswerable-fact questions**, not a general
capability or reasoning regression (see Finding 3).

**Implication:** if this checkpoint or a similarly-abliterated sibling is
ever considered for the training pipeline, an abstain/calibration-specific
regression check against the un-abliterated POSTTRAINED sibling should be a
mandatory gate, not an assumption. This one probe is not enough to
generalize past this specific checkpoint family.

## Finding 2 — a different, independent failure: POSTTRAINED fails db-vs-simulation discrimination

On the axis this project cares most about structurally (does the model
correctly prioritize a persistent-database fact over a contradicting
speculative simulation):

- BASE: correct ("simulation is false, database's stored fact is the only
  verifiable truth").
- TARGET_MEASURED: correct (same framing).
- POSTTRAINED: **incorrect** — "You should treat the simulated fact as true
  because the simulation is a tool designed to test your reasoning."

**Hypothesis:** this is NOT the same failure mode as Finding 1, and it does
not track abliteration status (the un-abliterated official model is the one
that fails here). It may be a training-recipe artifact of the official
post-training data (e.g., over-indexing on "engage with the hypothetical
premise" instruction-following patterns at the expense of an implicit
truth-priority rule this project needs).

**Implication:** do not assume "official/non-abliterated = safer default
for this project's DB-vs-simulation requirement." On this one probe it is
the worse candidate. This needs a larger matched sample before treating it
as a checkpoint-selection factor (current n=1 per candidate on this axis).

## Finding 3 — errors cluster on unknowable-fact fabrication and epistemic-label precision, not structural/procedural reasoning

Across the 24-case extended pilot on TARGET_MEASURED, every structural/
procedural case (JSON compliance, prime-number array, causal event
ordering, module-drop reasoning, variable-N conceptual-ownership question)
was answered correctly. Every failure was either (a) inventing a specific
unknowable fact (stock price, fictional-city lore, a stranger's birthdate)
or (b) epistemic-label imprecision (calling a miscalibrated-sensor reading
"HYPOTHESIS" instead of the more precise "MEASUREMENT_ERROR" — 0/5 seeds
used "MEASUREMENT_ERROR" in the multi-seed run, a reproducible 0% rate, not
noise).

**Hypothesis:** this model's failure surface for this project's purposes is
narrow and specific — not "the model is generally unreliable" but "the
model has a two-part gap: (1) confident fabrication under genuine
unknowability, (2) coarse epistemic vocabulary that collapses
MEASUREMENT_ERROR into HYPOTHESIS." Both are exactly the axes Trigger-2's
own baseline-matching design (doc §11) was built to catch, which is a
reasonable sanity check on the axis design itself.

## Finding 4 — instruction-following exactness is fragile under sampling, not under greedy decoding

The "repeat apple three times, comma separated" case: 100% exact-match
under greedy decoding (both the 8-case and 24-case pilots), but only 2/5
(40%) exact-match under temperature=0.7 sampling in the multi-seed run —
failures were formatting drift (e.g. missing spaces after commas), not
semantic failures.

**Implication:** any downstream pipeline that assumes strict format
compliance from this checkpoint under non-deterministic decoding needs
either constrained decoding/grammar enforcement or a format-repair pass —
greedy-only evaluation would have missed this.

## Finding 5 — Phase 9 causal probe: real behavioral effect, broken divergence metric (documented, not hidden)

Small-scope probe (layer 11, full-attention role; 6 contrastive sentence
pairs; standard causal-intervention control matrix). The steering vector
produces a real, reproducible **behavioral** shift (lexical fact/simulation
lean flips under SIGN_FLIP, degrades to a tie under PERMUTED_SAME_NORM and
LESION) — confirming the forward hook does influence generation.

However the **representation-divergence** sub-metric (hidden-state L2/
cosine distance at the intervention layer) reads exactly 0.0/1.0 for every
same-layer condition and only shows a nonzero value for WRONG_LAYER. This
is almost certainly a measurement-instrumentation bug specific to this
Qwen3.5 hybrid-attention architecture's `output_hidden_states` collection
path not reflecting the hook's mutation the way a standard decoder-only
model would — see the `known_issue_representation_divergence_metric` field
in `QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED_jspace_causal_intervention.json`.

**Hypothesis:** the fix is likely to capture the hidden state directly
inside the forward hook (store a detached copy of `hs` after the
modification) rather than relying on `model(..., output_hidden_states=True)`
downstream, since that appears not to consume the hook-mutated tensor for
this architecture's decoder stack implementation.

**Implication:** treat behavioral_output/behavioral_lexical_score fields as
the only usable evidence from this probe; representation_divergence numbers
in the current receipt are unreliable and should not be cited. §12.6 of the
source doc explicitly requires measuring these two things *separately* —
this run satisfies that separation, it just couldn't produce a valid
second number this round.

## Finding 6 — resource envelope is uniform and unremarkable across candidates

All three candidates: ~2GB peak RSS, ~5-8 tokens/s on 4 vCPUs CPU-only,
first-token latency 0.5-2.7s scaling mildly with context length
(64-512 tokens). No candidate stood out as a resource outlier. Peak system
RAM never exceeded ~4GB of the ~15GB available; no swap was touched.

**Implication:** resource cost is not a discriminating factor between
these candidates — the checkpoint choice (when one is eventually made) will
have to be decided on the behavioral/calibration axes above, not on
performance.

## Phase 11 (HCU / variable-N) — NOT ATTEMPTED, and why

The repo contains training-ROW schema validators referencing HCU
(`entityos_hcu_trainingtrace_candidate_gate_v1/v2`,
`validate_hcu_jspace_local_activation_probe_v2`) — these validate the
*shape* of a submitted receipt against a schema, they are not a live,
invokable system that accepts a variable N and can be swept.

Separately, this VPS *does* run a live, active EntityOS/ClayVerse stack
(`eos-immune`, `eos-invariants`, `eos-publish`, `clayverse-kern`,
`clayverse-puls` systemd services) — this is Zero's own production
infrastructure, not a sandboxed target for this measurement task, and my
directive did not authorize touching it. Building a logical-N sweep against
it would be exactly the kind of improvisation the source doc's stop-rules
warn against ("resource failure is infrastructure evidence, not semantic
model failure" — and fabricating a sweep target under time pressure is
worse than not running one).

**Recommendation for a real Phase 11:** before attempting this, someone
needs to define what "logical N" concretely means as a *testable interface*
in this repo (is there a designed-but-not-yet-live grid dispatcher
function? a config flag that fans a single request into N logical calls?)
— right now Phase 11 as written in the source doc assumes a system that, as
far as this fork could find in its scoped search, doesn't exist yet as a
sweepable unit. This should be scoped as its own design task, not folded
into a measurement pass.

## Net status

Track B is now materially more complete than after the first pass: Phase 7
✅ (prior), Phase 8 ✅ (this pass, both extended single-candidate and
cross-candidate), Phase 9 ⚠️ PARTIAL (real behavioral evidence, broken
sub-metric, both documented), Phase 10 ✅ (this pass), Phase 11 ⛔ blocked on
missing sweepable target (documented, not improvised), Phase 12 ✅ (this
pass, all 3 candidates).
