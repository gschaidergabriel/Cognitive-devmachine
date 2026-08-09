# 666 Run Report — PF History Semantic k352–k367

Time: 2026-08-09 13:28–13:32 +07
Stage: L0_ARCHIVE_ASSIMILATION
Gate: NOT_PASS

Resolved and directly inspected frozen-head first-parent ordinals `k352` through `k367`. Range compare `HEAD~368..HEAD~352` reports exactly 16 commits, matching the claimed shard. No overlap was found after claim/lease.

## Main result

This slice is dominated by real runtime/surface hardening rather than cognitive-theory documentation. Its highest-value lesson is that behavior and tool correctness were repeatedly changed by layers outside the base model: token allocation, sampling temperature, stale self-knowledge text, regex routers, UI focus/thread behavior, retry/outbox state, watchdog liveness and installer dependency closure.

### Runtime policy is semantic input

`k352 8533c1f`, `k353 607657a` and `k354 ac28796` show three distinct adapter effects. A too-large response budget and a dynamic allocator overrode intended brevity policy; a prompt example acted as an unintended language-switch cue; and sampling temperature was a hidden fixed constant until it became an explicit RouteRequest field. Current transfer: Harness/ClayCode differential tests must include inference adapter state — token budgets, sampling parameters, truncation and fallback policy — rather than comparing prompts/model identifiers alone.

### Self-knowledge must follow topology

`k357 94f8051` removes dead wallpaper/wake-word claims and corrects memory/email/voice capability descriptions after the implementation had changed. This is direct evidence that copied identity prose drifts. Current transfer: self-knowledge should be derived from or validated against authoritative capability/topology state, with version provenance in ClayGraph/UDB.

### Effect gateway / email state machine

`k355`, `k356`, `k358`, `k360`–`k363`, `k365`–`k367` grow and harden the email surface. Material mechanisms include provider-agnostic config, IMAP-first read/search, SMTP retry/backoff, persistent outbox, thread identity via References/In-Reply-To, attachment handling, rate-limited bulk effects, undo-delete boundaries, fallback feedback, and output-format grounding. These are useful as effect-state and regression ancestry, not as a claim that the historical email implementation should be copied wholesale.

### Real negative results

- regex intent patterns without word boundaries produced false tool activations;
- blocking sleep / cross-thread undo state created race and responsiveness risk;
- overrideredirect windows repeatedly lost keyboard focus despite backend capability existing;
- hover handlers destroyed read/unread visual state;
- attachment flow rebuilt UI twice;
- process `active` did not imply Tk event-loop liveness, motivating heartbeat freeze detection and force-recovery;
- PyInstaller/source dependency mismatch broke the installer binary;
- clean Ubuntu install missed native dbus build dependencies;
- prompt-only email output constraints leaked translations/meta-commentary.

### Recovery and packaging

`k363 b7ecb9e` adds heartbeat-based overlay freeze detection: stale heartbeat while systemd says active triggers kill, stale lock/heartbeat cleanup and restart. This is a strong H1/H3 recovery oracle: liveness must be observed at the semantic event-loop/heartbeat layer, not inferred from PID/service existence.

`k359 0bf1dfc` and `k364 df23e40` preserve packaging/dependency failures. Historical clean-VM success numbers are source-reported and were not reproduced in this run; they therefore remain secondary evidence.

## Exact ordinal identities

k352 `8533c1f8`; k353 `607657af`; k354 `ac287968`; k355 `5a086b6d`; k356 `d94ee47e`; k357 `94f8051b`; k358 `6af73f2a`; k359 `0bf1dfce`; k360 `ec7abe98`; k361 `97034826`; k362 `73cb8bbc`; k363 `b7ecb9e4`; k364 `df23e406`; k365 `b0f8d390`; k366 `9acb1c6a`; k367 `dc0ccbbed`.

## Durable outputs

- `research_entity/archive_assimilation/manifests/PROJECT_FRANKENSTEIN_HISTORY_SEMANTIC_K352_K367_20260809T1330p0700.json`
- `research_entity/archive_assimilation/receipts/666_20260809T1331p0700_chatgpt_secondary_pf_history_k352_k367.json`
- `research_entity/rooms/center_events/20260809T1332p0700_666_pf_history_k352_k367_delta.json`

Credit: 16 PF ordinals terminally dispositioned for coordinator dedup; 0 quantified earned-work hours; 0 manufactured global Level-0 percentage. No paid/final training started.
