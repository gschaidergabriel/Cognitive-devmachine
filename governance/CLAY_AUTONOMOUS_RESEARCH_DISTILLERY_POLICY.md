# Clay Autonomous Research Distillery Policy

Status: ACTIVE USER DIRECTIVE  
Program: EntityOS + HCU  
Runtime: `clay-direct-dev` FREE_ONLY research lane

## Purpose

A second autonomous research process continuously converts unresolved GO-worker questions into a compact, source-attributed dataset for the persistent Clay Research Entity.

The loop is:

`GO questions -> novel approach -> external source chunks -> small-model synthesis -> reviewer panel -> intrinsic/GRF gate -> compressed SQLite packet -> live GO context -> more questions`

## Question recursion and novelty

GO workers emit machine-readable open research questions. The distillery also mines older worker outputs. Questions are recursively decomposed into narrower unresolved questions.

When a question is revisited, the distillery MUST propose a causally different approach rather than re-running or paraphrasing the previous approach. Prior approach signatures are stored and supplied as negative context. Similar approaches are rejected and re-planned.

The queue is high-recall but bounded: decomposition may continue indefinitely across cycles while old/raw evidence is compressed or purged so storage does not grow without limit.

## Sources

Any lawful/accessible source class may contribute candidate evidence. Core collectors include:

- arXiv metadata, abstracts and bounded paper chunks;
- GitHub repository metadata and bounded code/document chunks from shallow temporary clones;
- Reddit snippets reached through authorized search providers rather than unauthenticated scraping;
- general web snippets through authorized search providers;
- future compatible research sources.

Whole papers and whole repositories are not retained in the dataset. Temporary PDF/repository material is deleted after bounded chunk extraction.

Every surviving source reference preserves metadata: source type, source ID, title, URL, author when available, publication time when available, license when available, retrieval/query metadata and content hash.

## Epistemic ranking

Citation count, stars, source prestige, author prestige, popularity, repetition frequency and search rank are NOT epistemic ranking features.

Candidate packets are judged on:

1. intrinsic logical consistency;
2. compatibility with GRF and explicit handling of tensions with GRF;
3. relevance to EntityOS/HCU architecture;
4. novelty of the causal mechanism relative to prior approaches;
5. falsifiability / quality of the discriminator;
6. strongest counterevidence.

Obscure sources may pass. Famous sources may fail.

## Reviewer panel

Preferred panel per candidate:

- one NVIDIA reviewer lane;
- two distinct Mistral-family reviewer lanes.

Direct Mistral FREE_ONLY credentials are preferred. When absent, Mistral-family routes exposed free through another authorized provider may fill the lanes only under their exact provider/model identity. Missing Mistral lanes are never fabricated or relabeled.

A preferred-panel acceptance requires the configured intrinsic/GRF/project/novelty thresholds, no hard contradiction, and real reviewer votes.

If the current FREE_ONLY runtime cannot expose two real Mistral-family reviewer routes, the research loop may use a **provisional fallback panel** consisting of one real NVIDIA reviewer plus two distinct zero-priced OpenRouter reviewer models. This is explicitly labeled `PROVISIONAL_NON_MISTRAL_FALLBACK`, uses stricter thresholds, remains candidate research only, and is eligible for later re-review when real Mistral lanes become available. A fallback model must never be called or counted as Mistral.

## Raw-data deletion and durable dataset

Rejected candidate source content is deleted after review. Accepted source raw text is also removed after compression. Durable state consists of compact knowledge packets plus source metadata/hashes and aggregate measurements.

The SQLite dataset is stored under the persistent `/artifacts` mount so sandbox restarts do not erase it.

## GO integration

Accepted and explicitly provisional packets are candidate research evidence, not canonical/effect authority. The main GO swarm reads a bounded set of packets into `DISTILLED_RESEARCH_DATASET` on subsequent prompts. GO workers generate new open questions, closing the feedback loop.

## Shared FREE_ONLY limits

The main Free Swarm and research distillery share `provider_budget.sqlite3`. It coordinates cross-process provider concurrency, minimum spacing and provider-wide cooldown observations. HTTP 429 / `Retry-After` update the shared provider state. Credentials are never rotated to evade organization/project limits. HTTP 402 remains a hard stop; no paid fallback is authorized.

OpenRouter small-model selection requires live zero-priced prompt and completion pricing. Approximately 4B or 4B-active routes are preferred; if no zero-priced route in that class exists, the smallest/highest-utility zero-priced models may be used and must retain exact model identity.

## Dashboard metric

The first Research Distillery metric in `free swarm/README.md` is:

`Entity Dataset Yield = accepted compressed dataset tokens / total collected source-chunk tokens`

The inverse is also reported as the source-token-to-dataset compression factor.

No missing token count may be invented.
