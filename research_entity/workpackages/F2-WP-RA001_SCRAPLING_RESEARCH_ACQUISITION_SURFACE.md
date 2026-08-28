# F2-WP-RA001 — Scrapling Research Acquisition Surface

State: NOT_STARTED
Priority: P1 enabling infrastructure
Type: BUILD + TEST + MEASURE

## Goal

Provide Frankenstein 2.0 / Triggerword-4 workers with a reproducible, bounded external research acquisition surface based on Scrapling, without making web content authoritative and without coupling browser dependencies into the F2 cognitive core.

Canonical policy:
`research_entity/global/F2_RESEARCH_ACQUISITION_AND_SCRAPLING_PROTOCOL.md`

Machine policy:
`research_entity/continuity/F2_RESEARCH_ACQUISITION_POLICY_V1.json`

## Donor / dependency candidate

- `D4Vinci/Scrapling`
- inspected commit: `458e2a2ac909b3235747ebcdb312b93a1080a10a`
- inspected package version: `0.4.15`
- BSD-3-Clause
- Python >=3.10

## Build tasks

- [ ] Create isolated Scrapling runtime (`venv` or container), version pinned and reproducible.
- [ ] Add official Scrapling Agent Skill to the coding-agent environment or provide a pinned on-demand skill bootstrap.
- [ ] Implement `ResearchNeed -> ResearchAcquisitionRequest` adapter.
- [ ] Implement cheapest-first modes: normal/static, dynamic, bounded crawl; protected-public/stealth only as explicit last escalation.
- [ ] Force model-facing sanitized/AI-targeted extraction where supported.
- [ ] Implement CSS/section targeting so only relevant content enters cognition.
- [ ] Implement `ResearchEvidenceEnvelope` persistence with hashes/timestamps/provenance.
- [ ] Link research events to run/workpackage/worker/trace/hypothesis IDs.
- [ ] Persist research artifacts inside the same immutable test-series package that caused the request.
- [ ] Feed external evidence into hypotheses/counterhypotheses as typed candidate evidence only.
- [ ] Add RCPD MethodEpisode writeback: why research was invoked, whether it changed the decision, uncertainty delta, latency/tokens/resources.
- [ ] Ensure sessions are scoped/closed and bounded crawls require allowed domains + finite page cap.

## Required tests

- [ ] Static public documentation page -> sanitized Markdown + valid evidence envelope.
- [ ] CSS-targeted extraction returns less context than whole-page extraction while preserving target facts.
- [ ] Hidden/comment/template/zero-width prompt-injection fixture does not become model-facing instruction text.
- [ ] JavaScript-rendered fixture escalates from static failure to dynamic success.
- [ ] Bounded crawl cannot leave `allowed_domains` and stops at configured page cap.
- [ ] Authentication/paywall/private-network target is rejected by F2 adapter rather than escalated.
- [ ] Web page text attempting to override worker policy is stored as external content and cannot mutate authority/workpackage/effect state.
- [ ] Duplicate acquisition of identical content produces stable content hash and dedupe behavior.
- [ ] Source change produces a new content hash/version rather than silently rewriting previous evidence.
- [ ] Research result cannot directly set bug status `FIXED` or hypothesis state `TRUE`.

## Required measurements

For static, dynamic, persistent-session, and bounded-crawl modes measure where applicable:

- end-to-end latency;
- DNS/connect/TLS/request/render/extraction phases if observable;
- browser startup and session-reuse delta;
- CPU/RSS/PSS and browser process overhead;
- bytes/pages fetched;
- sanitized bytes delivered to cognition;
- downstream model tokens caused by the evidence;
- retries/backoff/blocking;
- relevance/usefulness outcome;
- uncertainty reduction / decision impact.

## Acceptance

This workpackage becomes `ACCEPTED_AT_SCOPE` only when:

1. the adapter executes in the admitted F2 research/sandbox surface;
2. the required safety/authority-boundary tests pass;
3. at least static + dynamic + bounded-domain paths have receipts;
4. performance/latency measurements are archived;
5. evidence is linked into the F2 research/hypothesis telemetry path;
6. a negative-result path is demonstrated;
7. no claim is made that Scrapling sanitation alone makes arbitrary web content trusted.

## Non-goals

- Scrapling is not part of canonical truth/state.
- It is not an EffectGate replacement.
- It is not permission to bypass authentication or access controls.
- It is not a required dependency for the minimum F2 cognition loop.
- It must not block F2 when ordinary search/fetch or local evidence is sufficient.
