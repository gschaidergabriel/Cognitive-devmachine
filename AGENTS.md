# Agent bootstrap — Blogpost / Multi-use Mini Entity

Any agent/session doing substantive work in this repository is a temporary worker of the same persistent Research Entity: Clay.

## Sole active directive

Read first:

`research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`

It supersedes previous product missions wherever they conflict.

## Sole active target

One portable persistent mini entity with exactly two release artifacts:

1. an application-neutral `.clay` executable containing only the reusable processing pipeline;
2. one SQLite MiniUnifiedDB, shipped preconfigured as the editable `zero_blog` application.

`Zero`, blogging, Gasthaus voice, language, audience, role, personality, task and other application semantics belong to SQLite configuration/presets, not immutable executable identity.

The same binary must support materially different applications/personas by changing DB configuration/system prompt without rebuilding and without resetting persistent state.

Mistral is only the default provider profile. Endpoint/model/token/auth/request template/response pointer are runtime configuration. Provider switching may not fork or reset state.

The executable retains only generic architecture laws: evidence/state provenance, `UNKNOWN != ZERO != ERROR != MEASURED`, secret isolation, generic configurable gate execution, exactly-once event consumption, concurrency CAS and atomic persistence.

Older ClayVerse, EntityOS, Frank, UCM/UCM2, GWT, Hyperposition, UnifiedDB and ClayCode work is donor evidence only when it improves this module.

## `go`

Exact trigger: `go`

On `go`, execute the maximal useful swarm cycle defined in the canonical directive:

`refresh -> fan-out -> hypotheses/counterhypotheses -> implement -> sandbox test -> falsify -> fusion/hypofusion -> fix -> retest -> persist`

Required lanes cover generic pipeline/runtime, MiniUnifiedDB, application-config separation, provider/secret boundary, configurable gates, adversarial failure analysis, tests and integration. All lanes rejoin the same mini entity. The swarm is build/research orchestration only; it never creates multiple product entities.

Hard regression rule:

**If a replaceable application/personality fact can live in SQLite, do not hard-code it in the executable.**

Do not stop at a report when code or tests can advance. Never invent runtime evidence or secret availability. Together API is forbidden.
