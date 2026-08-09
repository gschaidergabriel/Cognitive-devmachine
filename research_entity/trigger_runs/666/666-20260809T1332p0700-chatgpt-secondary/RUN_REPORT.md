# 666 Level-0 Run Report — ChatGPT Secondary — 2026-08-09 13:32 +07

## Trigger / program state
- Trigger: `666`
- Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
- Canonical parent: `r2` / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- Stage: `L0_ARCHIVE_ASSIMILATION`
- Gate observed at start and late cross-read: `666_RELEASE_GATE = NOT_PASS`
- Frozen Project-Frankenstein head: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- Drive structural root remained closed at 14/14 folder roots. Project-Frankenstein exact tree/history denominator remains blocked on unavailable recursive read-tree/archive/clone surface.

## Repo-native coordination
Worker joined the persistent `center` room and completed/released three non-overlapping task leases:
1. `L0-PF-BODY-SELF-20260809T1332p0700`
2. `L0-PF-OUTPUT-FEEDBACK-20260809T1332p0700`
3. `L0-PF-PERSONA-CORE-20260809T1340p0700`

A transient Git CAS conflict occurred while starting task 3; the worker reread remote state and then claimed the shard successfully without overwriting concurrent work.

## Frozen-head source units deeply evaluated
- `personality/ego_construct.py` — blob `d954835220edf9b858fa59eb4fc512f043c63a09`
- `personality/self_knowledge.py` — blob `0a1f4d3ec7d47fe35d4f2ff0be855296c3405850`
- `services/response_analyzer.py` — blob `000db376375155197dc533c1be01ea744a1bb2ef`
- `personality/personality.py` — blob `98f54d24e2940023b90fb91d448e1d0e9f4c060e`
- `personality/frank.persona.json` — blob `e1d040d9ba725588f702ba567db4e02f2bfc214b`

## Durable receipts
- `research_entity/archive_assimilation/receipts/666_20260809T1332p0700_chatgpt_secondary_pf_body_self_knowledge.json`
- `research_entity/archive_assimilation/receipts/666_20260809T1332p0700_chatgpt_secondary_pf_output_feedback.json`
- `research_entity/archive_assimilation/receipts/666_20260809T1340p0700_chatgpt_secondary_pf_persona_authority.json`

Each receipt has an immutable Project-Frankenstein manifest delta and branch-feedback bundle.

## Material findings
### Historical mechanisms worth preserving selectively
- Persistent teachable body-state mappings and event-to-affect associations.
- Persistent agency assertions and explicit self/body projection surfaces.
- Hybrid persona last-known-good loading and version/hash tracking.
- Static + dynamic self-knowledge/capability projection pattern.

### Negative results / failure oracles
1. Repeated already-known sensation/affect activation mechanically increases historical embodiment/affective scalars toward 0.95 without independent correctness/calibration evidence.
2. Malformed teachable sensation conditions can silently fall back to `cpu > 50` rather than fail closed.
3. `CapabilityRegistry._check_module` only tests module paths with exactly two segments; known three-segment entries deterministically project inactive.
4. Static self-model/capability declarations can drift from live runtime truth and must not be treated as health/authority evidence.
5. Historical response confidence is lexical assertiveness, not epistemic confidence. Deterministic counterexample: assertive false arithmetic scored 0.9 while hedged true arithmetic scored 0.2 under the exact source rule.
6. `analyze_response(..., user_input=...)` does not use `user_input`, so the historical output-feedback loop cannot compare reply quality against task intent/outcome.
7. `is_tool_allowed()` ignores `tool_policy.ask_before`; with `default=allow`, configured approval-required operations fall through to Boolean allow at this policy layer.
8. Exact-looking tool policy entries are prefix-matched even without explicit wildcard semantics.
9. Persona prompt overflow uses raw character slicing, which can cut control text mid-section.

## Current architecture transfer
- Retina/adaptive visual learning: learned familiarity/personalization remains useful, but repetition is not evidence; require provenance tiers, open-set unknown/conflict, calibrated held-out evaluation, version compatibility, shadow candidate promotion and rollback.
- FRANK self/world/body: split immutable identity, user narrative, runtime observation, healthy capability, learned mapping and subjective projection into different authority/provenance classes.
- Needle/effects: prompt/persona/model text cannot authorize effects. Policy must distinguish `DENY | REQUIRE_APPROVAL | ALLOW`, with exact matching by default and external capability/approval receipts.
- GWT/agency: subjective/self-report signals may affect salience, but causal credit requires verified use/effect/outcome/re-entry state changes.
- UnifiedDB: persist raw observation, learned mapping/model version, trust/calibration/conflict, projection, policy version/matched rule/approval receipt and verified outcome separately.
- Harness: regressionize all nine failure-oracle families above.
- ClayCode: type-separate response style, epistemic confidence, runtime observation, learned mapping, projection, authority and verified outcome.

## Experiments/tests performed
- Static control-flow proof of three-segment capability discovery miss.
- Deterministic reproduction of historical lexical-confidence scoring with assertive-false vs hedged-true arithmetic examples.
- Static control-flow proof that `ask_before` is not consulted by `is_tool_allowed` and therefore falls through to `default=allow` when no allow/deny rule matches.

## Earned work / Level-0 accounting
- New quantified earned-work credit: `0.0 h` pending row-level overlap/dedup against existing historical mappings.
- Exact Level-0 percentage added: `0.0%` by law because the combined denominator remains unfrozen.
- These are semantic/code-history shards, not claims of repository-wide exhaustive completion.

## Remaining blocker / next obligation
Highest hard obligation remains an exhaustive recursive Project-Frankenstein frozen tree/history manifest or equivalent complete external manifest. Until that read surface exists, continue non-overlapping query-directed semantic/history shards and cross-source reconciliation without claiming exact repository-wide coverage.

## Provenance
This report stores only reproducible source references, control-flow observations, tests/counterexamples, conclusions and transfer constraints. Hidden chain-of-thought is not persisted.
