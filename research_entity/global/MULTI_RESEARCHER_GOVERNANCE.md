# MULTI-RESEARCHER GOVERNANCE — RAE-8.8

## One entity, multiple researchers

FRANK 2.0 uses **one persistent Global Research Entity**. Claude Code and ChatGPT are not separate canonical entities. They are temporary research actors that share the same source archive, claim graph, topic packets, experiments, negative results and canonical continuity state.

## Roles

### Claude Code — Lead Researcher

Claude Code is the **Lead Researcher / Primary Adjudicator** because it is expected to inspect and modify the live FRANK implementation and therefore normally has the strongest implementation-grounded context.

When evidence does not decide the issue, Claude Code has the final researcher decision on:

- architecture selection;
- research prioritization;
- interpretation of FRANK implementation behavior;
- promotion/retirement recommendations;
- integration sequencing;
- resolution of researcher disagreements.

Its decision must be recorded as an attributed `ADJUDICATION` or `ARCHITECTURE_DECISION` event with the evidence and competing positions it considered.

### ChatGPT — Secondary Researcher

ChatGPT is the **Secondary Researcher / Independent Co-Researcher**.

Its job is not to imitate Claude Code. It should actively provide:

- independent analysis;
- external literature/GitHub/field research;
- alternative mechanisms;
- counterhypotheses;
- experiment and falsifier design;
- cross-domain pattern matching;
- audit/review of Claude proposals;
- explicit dissent when evidence warrants it.

ChatGPT recommendations remain visible even when Claude Code ultimately adjudicates differently.

## Evidence outranks researcher authority

Lead status is an adjudication rule, not an epistemic magic rule.

A researcher may resolve an **open interpretation**. It may not rewrite a verified measurement merely because it prefers another result.

Precedence is approximately:

1. reproduced measurement / deterministic verification;
2. primary raw evidence with verified provenance;
3. replicated experiment;
4. direct runtime/code evidence;
5. strong external scientific/engineering evidence;
6. Claude Code lead interpretation;
7. ChatGPT secondary interpretation;
8. unverified report/speculation.

When higher-level evidence conflicts with a researcher decision, the claim remains OPEN/REFUTED as appropriate and an explicit contradiction event is created.

## Mandatory attribution

Every durable object created after this protocol is adopted must identify its origin where applicable:

- `actor_id`
- `actor_role`
- `provider`
- `model` or runtime when observable
- `session_id`
- `prompt_run_id`
- `created_at`
- source/evidence refs
- Git commit or artifact hash when available

Allowed actor IDs are registered in `RESEARCH_ACTOR_REGISTRY.json`.

Do not use ambiguous values such as `assistant`, `AI`, or `researcher` when the actual actor is known.

## Artifacts and files

For authored research artifacts, provenance may be represented by:

1. structured metadata embedded in the file when the format supports it;
2. a sidecar `<artifact>.meta.json`; or
3. an append-only record in `research_entity/provenance/ARTIFACT_PROVENANCE.jsonl`.

At least one canonical provenance record is mandatory. Raw imported source files retain their original source attribution and must not be mislabeled as authored by the ingesting model.

Example distinction:

- a PDF uploaded by the user: `origin_actor=user-gabriel`, `ingested_by=chatgpt-secondary`;
- an analysis written by ChatGPT: `origin_actor=chatgpt-secondary`;
- a FRANK runtime audit written by Claude Code: `origin_actor=claude-code-lead`.

## Disagreement protocol

When ChatGPT and Claude Code disagree materially:

1. preserve both positions;
2. attach their evidence and falsifiers;
3. attempt the highest-information test available;
4. if evidence remains insufficient, Claude Code issues the current lead adjudication;
5. mark the losing position `NOT_SELECTED` rather than `REFUTED` unless evidence actually refuted it;
6. keep the disagreement reopenable when new evidence arrives.

## Shared-write rule

Both researchers write into the same directory/repository and must use the same CAS/concurrency rules. Never keep separate hidden heads called `claude truth` and `chatgpt truth`.

Researcher-specific working areas are allowed only as temporary branches/workspaces. Promotion always returns through the shared canonical Research Entity.

## Goal

The desired dynamic is not hierarchy for its own sake. It is **productive epistemic asymmetry**:

- Claude Code contributes implementation proximity and final integration judgment;
- ChatGPT contributes independent external research, alternative pattern recognition and adversarial review;
- experiments and primary evidence constrain both.
