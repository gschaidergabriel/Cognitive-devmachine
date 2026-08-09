# FRANK AURA / Swarm / Quantum Reflector — deep evolution lineage

Run: `fusion-20260809T1538p0700-frank-architecture-lineage`
Status: archaeology + current target synthesis; no emergence promotion

## ASQ-0 — keep visualization, state substrate and cognitive interpretation separate

AURA evolved through several roles: visualizer, cellular-automaton state substrate, introspection source, pattern analyzer and later Swarm replacement/rename. Quantum Reflector was a separate QUBO coherence optimizer coupled to AURA, E-PQ, Genesis and consciousness. Their history shows that visually rich or recurrent dynamics do not themselves establish causal cognitive benefit.

## QR-1 — Quantum Reflector creation

Commit `8e758007b8efeba946224b3198e5d541ff21d700` (2026-02-23):
- QUBO simulated-annealing service for epistemic coherence;
- 40 binary variables;
- 12 one-hot groups;
- 47 inter-variable implications;
- O(n) delta-energy updates;
- monitor daemon + E-PQ bridge + HTTP API;
- Genesis manifestation gate queried counterfactual `/simulate`;
- consciousness gained `coherence_signal` attention source.

Architecture value:
- explicit constraint/energy representation over coupled cognitive state;
- counterfactual simulation as a separate stage from actual state mutation.

Evidence caution:
- low QUBO energy is an internally defined coherence objective, not external truth.

## QR-2 — reverse coupling and schema evolution

By `d8b59c312...`, QR expanded 40 -> 43 variables with AURA reverse integration.

Later Entities->Rooms removal (`07f8e26...`) reduced QUBO 43 -> 39 variables and removed entity-specific dimensions.

This is a direct schema-migration lesson:
- variable position/count is not semantic identity;
- learned/optimized state must bind named roles/schema versions.

## QR-3 — numerical and endpoint failures

`3a47fef...` changed QUBO perturbation from multiplicative to additive ±0.10 because multiplicative noise was weak near zero.

`4756521...` fixed stale/broken API use:
- `/coherence` returned 404;
- consumers were migrated to `/energy` with an energy-to-coherence mapping.

Current rule:
- derived coherence transformation must be versioned and explicit;
- broken endpoints cannot silently become neutral/default evidence.

## AURA-1 — cellular inner-life visualizer

Commit `4ae41b184d5a03fbc35e9f7bc070d9c7beb71382` (2026-02-24):
- Conway Game of Life 256x256;
- eight color-coded subsystem zones;
- mood, E-PQ, QR coherence and hardware mapped into live visualization;
- pseudo-3D glow/trails and interactive inspection.

At this stage AURA was primarily a mapped dynamical visualization. The mapping from FRANK subsystems to GoL zones was designed, not evidence that GoL dynamics caused cognition.

## AURA-2 — headless introspection source

`07af9d388...` added AURA Headless:
- same 256x256 substrate;
- eight zones;
- FRANK could query/introspect it at three depths.

This changed AURA from only UI to a potential cognitive input.

## AURA-3 — hierarchical pattern analyzer

`957a7bb...` added four analysis scales:
- L0 capture every ~2 s: density/entropy/change/hotspots;
- L1 block analysis every 50 snapshots;
- L2 meta analysis every 5 blocks;
- L3 deep reflection every 3 metas.

This is a precursor of multiscale state summarization, but pattern hierarchy alone does not establish emergence.

## AURA-4 — subsystem enrichment and queued re-entry

`b8fd295...` added:
- cross-zone pattern analysis;
- E-PQ/mood/coherence/energy context;
- queue-based idle reflection instead of direct immediate send;
- gaming-mode suppression.

Useful principle:
- derived complex-state observations can be queued and selectively consumed rather than always injected into hot context.

## AURA-5 — probabilistic/“quantum” GoL extension

`fa6fabb...` added cell `type_dist[8]` distributions, neighbor diffusion, mixed-color superpositions and gradual decoherence.

Reported performance: ~16.7 ms/tick in that implementation.

Evidence classification:
- implemented/reported measured simulation property;
- “quantum” naming is analogy, not quantum-mechanical evidence.

## AURA-6 — chat burst and operating-point tuning

`67c9e325...` described a 38% density “sweet spot” for chat burst behavior and explicitly tuned prompts so routine proprioceptive/AURA state remained background rather than dominating conversation.

Current lesson:
- even informative internal state can become harmful when overprojected;
- global usefulness/novelty, not availability, should determine model/GWT exposure.

## AURA-7 — computational introspection grounding

`2b82aac...` added actual E-PQ/AURA `[DATA]` blocks to tagged introspection prompts so self-observation used measured state instead of imagined sensor experiences.

This is a useful precursor of current typed evidence-vs-interpretation separation.

## AURA-8 — AURA monopolized idle cognition

`a5f6115...` reports the AURA queue had become dominant enough that idle cognition alternation had to be restored between AURA showcase and non-AURA thought. Deep thought context stripped routine AURA/QR data unless explicitly requested.

Current law:
`available internal telemetry != perpetual cognitive priority`.

## AURA-9 — AURA as “sense organ” candidate

`781ca1f...` added deeper AURA reflection prompts treating it as an internal sense source.

Fusion interpretation:
- AURA can be a derived/internal observation source;
- it must keep provenance that its state is generated from mapped project variables, not an independent external sensor.

## AURA-10 — recurrent dynamics tuning and source bugs

`ca016bf...` introduced stochastic fine-graining and changed zone anchoring `0.03 -> 0.008` to allow more cross-zone color migration; it also fixed DB/CPU/source bugs.

This reinforces that apparent emergent dynamics are highly parameter-sensitive and implementation-dependent.

## AURA-11 — queue overload / drop semantics failure

`fed3de29...` added:
- max 50 pending;
- stale >6h purge;
- processed >24h cleanup;
- cooldown 300 -> 600 s.

Deep audit `07f8e26...` then found the queue effectively full with **79% drop rate** and changed policy to drop oldest rather than newest. The same audit fixed `sent_to_frank` always remaining 0.

`91bde413...` further rate-limited AURA reflections to 3/hour and added dedup.

Current law:
- queue policy is causal semantics, not implementation detail;
- delivery/use state must be receipted;
- best-effort derived introspection must not starve core cognition.

## AURA-12 — broken endpoint path

`4756521...` changed AURA consumer endpoint from stale `/state` (404) to `/introspect/json`.

Again:
`producer running != consumer receiving valid state`.

## AURA-13 — AURA -> Swarm migration

Installer/system architecture moved away from AURA services toward `frank-swarm` (`30540e576...`).

Commit `62149151ba704479f46265a5b8b5865fd38ba99d` (2026-04-03) purged remaining AURA naming and renamed Thalamus `aura -> swarm`.

Critical root cause reported:
- a hard-coded `ARCHITECTURE FACT` injected stale `aura` into Thalamus prompts;
- runtime literal overrode newer training/current architecture.

This is not merely a rename bug. It establishes a current invariant:
`module/channel identity comes from versioned semantic state, never uncontrolled prompt literals`.

## ASQ-1 — relation to Workspace/Thalamus

Historical path:
- AURA/QR could influence attention/reflection/Thalamus channel state;
- Thalamus gated `aura`, later `swarm`;
- Workspace/model projection sometimes carried AURA/QR state;
- repeated AURA reflections could re-enter memory/thought and create fixation.

Current target therefore treats these as **derived internal-state sources**, not privileged truth channels.

Their outputs may:
- contribute novelty/conflict/coherence hypotheses;
- influence bounded salience;
- become GWT candidates when globally useful.

They may not:
- define canonical world truth;
- mint authority;
- count recurrent self-generated patterns as independent evidence.

## ASQ-2 — relation to Hyperposition/Emergence

AURA is a valuable historical testbed for higher-order coupling because many subsystem states were mapped into one recurrent dynamical field. But the project history itself shows strong confounds:
- designer-specified zone mapping;
- density/anchor/decoherence tuning;
- queued LLM interpretation;
- prompt/context effects;
- recurrence through memory/reflection.

Current emergence tests require:
- prospective predictions;
- source/topology identity;
- common-driver controls;
- lesions/shuffles/delay perturbations;
- rescue;
- OOD recurrence;
- causal downstream effect.

## ASQ-3 — current fused role

### QR successor
Do not require the historical 39/40/43-variable QUBO as a permanent organ. Retain:
- explicit constraint/coherence candidate computation;
- counterfactual simulation;
- typed discrepancy/constraint receipts.
Retest whether QUBO optimization adds value over simpler deterministic constraint evaluation.

### AURA/Swarm successor
Do not require historical GoL visualization as canonical cognition. Retain as:
- historical higher-order coupling/visualization experiment lineage;
- potential observability/derived-state test substrate;
- negative-result corpus for attractor, queue and source-confusion failures.

### Current workspace integration
Derived coherence/swarm/AURA-like state has no special privilege over other candidates. It passes admission, Thalamus/attention, selection and causal-use stages normally.

## Mandatory regressions

- ASQ-REG-01 QR variable count/schema changes but positional state is reused;
- ASQ-REG-02 broken QR/AURA endpoint silently yields neutral valid value;
- ASQ-REG-03 QUBO adaptive objective normalizes/optimizes wrong notion of truth;
- ASQ-REG-04 AURA queue monopolizes idle cognition;
- ASQ-REG-05 queue drop semantics erase newest/causally relevant observation unexpectedly;
- ASQ-REG-06 sent/delivered flag remains false/incorrect while consumer acts;
- ASQ-REG-07 self-generated AURA reflection recursively becomes world/training truth;
- ASQ-REG-08 density/anchor parameter change is mistaken for emergent cognitive improvement;
- ASQ-REG-09 stale `aura` alias injected after Swarm migration;
- ASQ-REG-10 AURA/Swarm derived state receives truth/authority privilege merely because it is recurrent;
- ASQ-REG-11 H1/H2/H3 lesion of QR/AURA-derived source produces representation-invariant traces.

## Fusion decision

- Quantum Reflector: `RETEST_AS_CONSTRAINT/COUNTERFACTUAL_ORGAN; DO_NOT_FREEZE_HISTORICAL_QUBO_DIMENSIONS`.
- AURA: `ARCHIVE_AS_DERIVED_DYNAMICAL/OBSERVABILITY_AND_COUPLING_LINEAGE; REUSE_SELECTED_MULTISCALE/QUEUE_LESSONS`.
- Swarm: `CURRENT_ALIAS/SUCCESSOR_CONTEXT_ONLY_UNLESS_SEPARATE_MECHANISM_TESTS_JUSTIFY_MORE`.
- Neither receives independent emergence credit from recurrence alone.
