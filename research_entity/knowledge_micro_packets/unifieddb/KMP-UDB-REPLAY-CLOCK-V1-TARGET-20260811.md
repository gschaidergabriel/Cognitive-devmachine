# KMP-UDB-REPLAY-CLOCK-V1-TARGET-20260811

packet_id: `KMP-UDB-REPLAY-CLOCK-V1-TARGET-20260811`
domains: `unifieddb, replay, temporal_semantics, claygraph, query_receipts`
epistemic_class: `ACCEPTED_TARGET_VPS_MECHANISM_EVIDENCE`
status_hint: `SUPPORTED_TARGET_MECHANISM_NOT_PRODUCT_INTEGRATED`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`
trigger: `unifieddb`
program: `FRANK_V0_1`
work_package: `F-V01-04-UNIFIEDDB-STATE-CONTINUITY`

## Target receipt

Repository PR: `#300` — `UnifiedDB: explicit ReplayClock V1 for deterministic temporal reads`

Base: exact current main `2bdeb35d722417a1c2d9b71a3b3ac9125acf46c3`

Head: `ba5cc52d6695a91529b618ebf5eeb92bbfbe5213`

Self-hosted target run: `31437186827`
Job: `93613810168`
Result: `SUCCESS`
Artifact: `frank-replay-clock-v1-31437186827`
Artifact id: `9081454693`
Artifact digest: `sha256:02df981120780b21b6bcf6349de389e1adcbe20a6936dfcb3905dc7199e263dc`
Environment:
- platform `Linux-6.8.0-117-generic-x86_64-with-glibc2.39`;
- Python `3.12.3`;
- SQLite `3.45.1`.

Mechanism result: `PASS_REPLAY_CLOCK_V1_MECHANISM`.

## What passed

Five supported encodings of the same instant all canonicalized to:

- UTC microseconds `1786398997123456`;
- canonical text `2026-08-10T21:56:37.123456Z`.

A LIVE_CAPTURE receipt and a REPLAY_BOUND receipt had different provenance hashes but exactly the same `as_of_utc_us`.

A short-lived fact:
- was visible at captured time;
- remained visible during replay after real wall-clock advancement because replay reused the captured clock;
- was absent under a fresh later LIVE_CAPTURE clock.

The typed-integer SQLite query returned the exact same row set for captured/replay clock and an empty set for the later clock.

The current mixed-TEXT anti-control also reproduced on target:
- SQLite current time: `2026-08-10 22:12:14`;
- same represented instant as ISO: `2026-08-10T22:12:14+00:00`;
- SQLite datetime parser classified it as not future;
- raw TEXT comparison classified it as future.

Thus the existing temporal bug and the candidate repair mechanism are both target-reproduced.

Bounded whole probe resource observation:
- wall ~0.21 s;
- max RSS 21,376 KiB.
This includes sleeps/test setup and is not a per-query latency benchmark.

## Architecture consequence

Replay time becomes an explicit input identity rather than an ambient database input.

Candidate law:
`selection/query identity = semantic root ∧ explicit ReplayClock receipt ∧ query/operator context`.

A live cognition cycle resolves now once. Replay reuses the exact captured `as_of_utc_us`. A newly live cycle gets a new clock receipt.

This does not by itself migrate current production `valid_from/valid_to` fields or rewrite current views. Product integration still requires:
1. canonical timestamp migration/compatibility policy;
2. explicit clock binding in query/assembly/selection receipts;
3. removal/bypass of ambient `CURRENT_TIMESTAMP` from replay-critical paths;
4. crash/restart/replay regression;
5. integration with Graph projection and causal temporal ordering.

## Promotion boundary

`SUPPORTED_TARGET_MECHANISM_NOT_PRODUCT_INTEGRATED`.

No canonical state mutation, external effect, snapshot/recovery/Graph/selection promotion, whole Frank v0.1 acceptance, final training authorization or Frank/self.root Harness authority follows from this packet.
