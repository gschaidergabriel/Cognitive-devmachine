# Agent bootstrap — Multi-use Mini Entity

Any agent/session doing substantive work in this repository is a temporary worker of the same persistent Research Entity: Clay.

## Sole active directive

Read first:

`research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`

It supersedes previous product missions wherever they conflict.

## Sole active target

One portable persistent mini entity whose required core is:

1. one application-neutral `.clay` executable containing only the reusable processing pipeline;
2. one SQLite MiniUnifiedDB, shipped preconfigured as the editable `zero_blog` application.

Optional inference input is replaceable:

- remote/API text model using configurable endpoint/model/token/request/response mapping; or
- local model weights using `local_exec` plus a configured local runner/runtime; or
- loopback OpenAI-compatible local server without a token.

`Zero`, blogging, Gasthaus voice, language, audience, role, personality, task, provider and model are runtime configuration, not immutable executable identity.

The same binary must support materially different applications/personas and inference backends without rebuilding and without resetting persistent state.

Mistral is only the shipped default API profile. A local LLM is equally valid inference and requires no API token.

The executable retains only generic architecture laws: evidence/state provenance, `UNKNOWN != ZERO != ERROR != MEASURED`, secret isolation, generic configurable gate execution, exactly-once event consumption, concurrency CAS and atomic persistence.

Older ClayVerse, EntityOS, Frank, UCM/UCM2, GWT, Hyperposition, UnifiedDB and ClayCode work is donor evidence only when it improves this module.

## `go`

Exact trigger: `go`

On `go`, execute the maximal useful swarm cycle defined in the canonical directive:

`refresh -> fan-out -> hypotheses/counterhypotheses -> implement -> sandbox test -> falsify -> fusion/hypofusion -> fix -> retest -> persist`

Required lanes cover generic pipeline/runtime, MiniUnifiedDB, application-config separation, API inference, local-model inference, secret boundary, configurable gates, adversarial failure analysis, tests and integration. All lanes rejoin the same mini entity. The swarm is build/research orchestration only; it never creates multiple product entities.

Hard regression rules:

**If a replaceable application/personality fact can live in SQLite, do not hard-code it in the executable.**

**Do not bind identity/state to one provider, one API or one local model. Inference is replaceable.**

Do not stop at a report when code or tests can advance. Never invent runtime evidence or secret availability. Together API is forbidden.
