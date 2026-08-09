# FRANK Bugsearch Addendum — exact `bug` double routing

Actor: chatgpt-secondary
Date: 2026-08-09T19:41:00+07:00
Parent report: `research_entity/research/frank/FRANK_BUGSEARCH_20260809T1941p0700.md`

## FB-13 — exact `bug` is simultaneously routed as generic skill and special capture command (P1)

The project-fixed bug protocol defines exact `bug` as a dedicated capture operation: preceding complete Andreas/Frank pair -> Frank DB -> export -> Clay pull. Current `.claude/settings.json` runs both `frank_prompt_inject.py` and `frank_bug_prompt.py` on `UserPromptSubmit`.

`frank_prompt_inject.py` treats every non-`skill` prompt as a candidate custom skill trigger. Because V13 itself inserts a CURRENT `bug` skill/skill_trigger, exact `bug` is resolved by `frank_session_skill_impl.resolve_trigger()`, which inserts a `skill_invocations` row in `STARTED` state and mutates the status surface. Independently, `frank_bug_prompt.py` performs the dedicated preceding-pair capture.

This mixes a protocol-reserved command with the generic reusable-skill execution path and can create phantom/open skill invocations or model-facing `ACTIVE_SKILL_INVOCATION` semantics for a command whose real effect has already been handled by the special capture hook.

### Required repair

- Reserve/exclude `bug` from generic skill creation and generic trigger resolution.
- Route exact `bug` through one authoritative dispatcher before generic custom-skill resolution.
- Add regression asserting one and only one bug command state transition/capture path, no generic `skill_invocations` row, and no duplicate side effect.
- Preserve the project-fixed authority boundary: Frank captures/exports only; Clay alone performs research/repair.

### Falsifier

A current end-to-end exact `bug` trace proves only one authoritative command path executes and no generic skill invocation row/context is created.
