# External Research & Verification Policy

## Purpose

This policy governs how FRANK/RAE uses external APIs, search providers and execution sandboxes during research.

It separates four concerns:

1. **internal retrieval** — querying already-ingested RAE state;
2. **external discovery** — finding papers, web sources and implementations;
3. **verification** — checking claims against primary/authoritative evidence;
4. **empirical execution** — running code, simulations, ablations or reproductions.

`tools/research_query.py` is internal retrieval and MUST NOT be treated as external evidence acquisition.

The external capability registry is:

`research_entity/global/EXTERNAL_RESEARCH_TOOL_REGISTRY.json`

## Secret handling

Credential values MUST NOT be committed to GitHub, canonical research state, packets, ledgers or reports.

Allowed sources:
- process environment;
- local `.env` ignored by Git;
- runtime secret manager/store.

Repository files may contain only:
- environment variable names;
- provider/tool metadata;
- non-secret configuration examples.

If a credential is supplied interactively, do not copy it into durable research artifacts.

## Mandatory tool-selection rule

Before a hypothesis or externally sourced factual claim is promoted as verified/current, use at least one fit-for-purpose external verification capability when such verification is technically available and relevant.

Examples:
- scholarly claim -> scholarly/primary literature retrieval;
- DOI/publication identity -> bibliographic verification;
- implementation/runtime claim -> source repository, authoritative documentation and/or reproducible runtime evidence;
- computational result -> local or registered sandbox execution where feasible;
- current web fact -> authoritative/current web source, using registered search only for discovery.

Search-engine output is discovery evidence, not final verification when a primary source is reachable.

## Computational claims

For claims whose truth materially depends on executing code, a reproducible execution attempt is required before strong promotion whenever execution is feasible.

Preferred order:
1. local sandbox/container when sufficient;
2. E2B or equivalent isolated remote sandbox for environment isolation/dependency-heavy work;
3. Judge0/Piston for small multi-language reproducibility tests;
4. other registered execution backends.

Failure to execute must be recorded as an evidence limitation, not silently ignored.

## Literature claims

For literature-backed claims, use one or more registered scholarly sources appropriate to the task. Preserve source class:
- peer-reviewed/publisher source;
- preprint;
- scholarly metadata/index;
- citation graph/secondary discovery.

Do not promote a proposition merely because several metadata/search providers repeat the same underlying paper.

## Web research

Tavily, Exa, DuckDuckGo-compatible clients and similar tools are discovery layers. Prefer the discovered primary/authoritative source in the final evidence chain.

## Provider fallback

If a preferred provider is unavailable, rate-limited, unconfigured or returns inadequate evidence:
1. record provider/tool and failure mode in the run manifest when material;
2. use the next suitable registered capability;
3. preserve the downgraded evidence class;
4. never fabricate successful verification.

## Runtime verification

A registry entry marked `REGISTERED_NOT_RUNTIME_VERIFIED` is only a declared capability.
It becomes operationally verified only after a successful call in the current runtime/host.

## Cost / token discipline

Use APIs selectively rather than exhaustively:
- cluster related hypotheses into shared searches;
- query internal RAE state before spending external calls;
- retrieve metadata/snippets first and full documents only when decision-relevant;
- deduplicate by DOI/arXiv ID/URL/source hash;
- reuse cached immutable source material where freshness is not required;
- do not call multiple providers merely to inflate agreement counts.

## Evidence discipline

Tool output never receives authority by tool name alone.

Every durable research claim should retain, where relevant:
- provider/tool used;
- query or experiment identifier;
- source identifiers/URLs/DOIs/arXiv IDs;
- timestamp/freshness when relevant;
- raw-source hash or archived evidence reference;
- evidence class;
- actor provenance;
- uncertainty/falsifier.

Evidence outranks provider prestige.
