# Reserved Trigger: `claycode`

Research ClayCode as the internal semantic language/IR for Synthetic Clay and as the primary architecture/implementation IR of the next FRANK architecture. Use the Master Research Trigger Protocol, the Interconnected Research Mesh Protocol and the Goodman Anti-Echo Protocol.

## Mandatory FRANK feedback foundation

Every `claycode` run MUST begin by loading the **newest FRANK research and architecture material**, including fresh/in-progress material newer than the latest final report.

Priority for ClayCode is:

`frank -> clay -> gwt -> hyperposition -> emergenz -> claycode history`

Load from FRANK at minimum where present:

- newest `FINAL_REPORT.md` and run manifest;
- newest `FRANK_ARCHITECTURE.claycode.json` — the current ClayCode semantic-IR architecture plan;
- `CLAYCODE_ARCHITECTURE_MAPPING.md`;
- newer FRANK experiments, negative results and architecture deltas;
- FRANK Topic Packets and knowledge micro-packets;
- FRANK runtime/code observations and measured constraints;
- FRANK cross-branch dependencies and unresolved contradictions.

If no `FRANK_ARCHITECTURE.claycode.json` exists yet because the requirement was introduced after the latest completed FRANK run, do **not** fabricate it. Record the missing architecture artifact explicitly and use the newest FRANK report plus `tools/frank_architecture_contract.py`/current FRANK protocol as provisional architecture requirements. The next FRANK run is required to produce the architecture artifact.

Run `tools/research_interconnect_preflight.py --trigger claycode --run-id <run_id>` and materialize `INTERCONNECT_MANIFEST.json` before Fusion 1.

## Mandatory Goodman anti-echo review

FRANK and ClayCode are a feedback pair. Their agreement is not automatically independent evidence.

For every FRANK-derived assumption that materially changes ClayCode semantics, representation, runtime, compiler, gateway, state model or self-hosting architecture, ClayCode MUST apply `research_entity/global/GOODMAN_ANTI_ECHO_PROTOCOL.md` and write:

`FRANK_CLAYCODE_GOODMAN_REVIEW.json`

Use `tools/goodman_filter_check.py` to validate the review.

Each relevant FRANK assumption must receive one verdict:

- `SUPPORTED` — independently supported; retain with original evidence status;
- `REFINED` — partially supported but scope/semantics changed; integrate only the refined form;
- `REFUTED` — counterevidence wins; reject/supersede and preserve a negative result;
- `UNRESOLVED` — insufficient independent evidence; keep open and do not silently bake it into ClayCode as truth.

### Anti-echo requirements

Before `SUPPORTED` or `REFINED`:

1. collapse shared source/experiment ancestry across FRANK, Clay, ClayCode and other branches;
2. seek independent external evidence, a new discriminating executable experiment, target-runtime observation or adversarial counterexample search;
3. state a counterhypothesis;
4. state a falsifier;
5. execute/record at least one adversarial check;
6. preserve evidence class — synthetic remains synthetic, proxy remains proxy;
7. never count another worker/model repeating the same ancestry as independent replication.

Circular flow such as `ClayCode claim -> FRANK adopts -> ClayCode reads FRANK` adds **zero independent support** unless the returning FRANK result contains genuinely new evidence or a new discriminating experiment.

## Bidirectional integration rule

ClayCode is not merely required to read FRANK. It must **test FRANK's demands against the language/runtime design**:

- if FRANK exposes a missing semantic primitive, research and add it when independently justified;
- if FRANK reveals a runtime requirement that invalidates a ClayCode assumption, refine ClayCode;
- if a FRANK architecture choice is wrong or unsupported, explicitly refute/narrow it and write the contradiction back to the shared research mesh;
- if ClayCode discovers a safer/more efficient representation or transition model, write that delta so the next `frank` run must reconsider its architecture.

The result is a falsifiable feedback loop, not a consensus loop.

## Core research questions

- Can ClayCode faithfully represent the state, relations, authority, provenance, assemblies and transitions required by the newest FRANK architecture?
- Does the current FRANK architecture expose missing ClayCode primitives, unsafe assumptions or unnecessary representation cost?
- Which FRANK architecture assumptions survive independent ClayCode verification, which require refinement, and which are refuted?
- Which semantics belong in canonical IR versus reader-specific projection/wire syntax?
- Can a Clay-written runtime interpret/transform ClayCode without circular ambiguity or hidden authority escalation?
- What must remain deterministic outside the model: parser, schema, canonicalization, capability checks, commit gateway, rollback and receipts?
- Can a Qwen-class 4B model operate on the internal state language rather than merely imitate surface syntax?

## Required research dimensions

- FRANK architecture coverage: modules/organs, state contracts, transitions, dependencies, invariants, causal/GWT links and authority boundaries;
- Goodman ancestry/independence analysis for FRANK-derived assumptions;
- self-description/reflection without conflating representation with authority;
- canonical AST/IR and deterministic roundtrip;
- state/version/provenance/unknown/conflict/revoked semantics;
- transition closure, scoped freshness and trusted dependency/effect derivation;
- activation/assembly/workspace primitives;
- outcome/re-entry/credit primitives;
- external capability/commit boundary;
- parser/validator/compiler fuzzing;
- context/token/repair cost versus JSON/key=value/natural-language baselines;
- reader-specific projections and live-reader break-even;
- Qwen-4B simulation or live tests, explicitly labeled `simulation_only` when no target model is actually run;
- bootstrapping/self-hosting path: host runtime -> ClayCode runtime -> Clay-represented FRANK/Synthetic Clay system.

## Required outputs

Every completed ClayCode run must include at minimum:

- `INTERCONNECT_MANIFEST.json`;
- `TOOL_EXECUTION_MANIFEST.json`;
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json`;
- hypotheses/experiments/negative results appropriate to the run;
- `FINAL_REPORT.md` with a dedicated `FRANK feedback / Goodman review` section.

A ClayCode run that materially consumes FRANK but omits the Goodman review is incomplete and cannot strongly promote FRANK-derived ClayCode semantics.

A language candidate is not promoted because it looks compact, alien, or agrees with FRANK. Promotion requires semantic preservation, bounded repair cost, target-reader performance, safety/authority invariants and non-circular evidential support.

Write the final report to `research_entity/trigger_runs/claycode/<run_id>/FINAL_REPORT.md` and finish with the mandatory status footer.
