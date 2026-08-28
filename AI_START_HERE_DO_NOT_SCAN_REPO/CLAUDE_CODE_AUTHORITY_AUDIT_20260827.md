# Claude Code lifecycle authority audit — 2026-08-27

Status: `NEGATIVE_RESULT / INSTALLER_DISCRIMINATOR`

This is a bounded source audit rechecked against canonical `main` identity `7d5386ff0b7683b3b5e3ba0521f897fe9e599d2c` immediately before this evidence write. It is **not** a runtime hook-firing receipt.

## Observed

### Current admitted program authority

`research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` says:

```text
schema semantics: 9.13
surface: 9.13O_NON_AUTHORITY
active program: ENTITYOS_HCU
product: EntityOS
integrated cognition/compute architecture: HCU
provider_routes_admitted: false
free_swarm_owner_emergency_stop: true
together_forbidden: true
training_credit: 0
```

Current provider work therefore fails closed. No provider/secret/network probe is needed or allowed to establish this installer finding.

### Claude Code lifecycle wiring exists in source

`.claude/settings.json` registers `.claude/hooks/rae_hook.py` for real Claude Code lifecycle event classes including:

```text
SessionStart
UserPromptSubmit
SubagentStart
PreToolUse
PostToolUse
PreCompact
Stop
SessionEnd
```

This is stronger than a hypothetical installer path: a concrete host-native hook configuration exists.

### The configured hook carries older identity semantics

The current `.claude/hooks/rae_hook.py` still binds older Research-Entity / Frank language, including source-level invariants such as:

```text
I_AM=RESEARCH_ENTITY_TEMPORARY_WORKER
I_AM_NOT=FRANK
ANDREAS_INTERFACE=FRANK_ONLY
FRANK_ROOM_MEANS=RESEARCH_ABOUT_FRANK_NOT_ROLEPLAY_AS_FRANK
```

and a kernel whose visible identity begins from `ClayResearchEntity` / historical Frank framing.

That does not match the current Trigger-3 bootstrap/current program framing cleanly:

```text
persistent research entity = Clay
current product = EntityOS
integrated architecture = HCU
current worker/model/session = organ, not a new persistent entity
```

The old hook may still contain useful guard mechanics. The finding is **authority drift**, not “the hook is useless.”

## Classification

```text
Claude Code hook configuration present: SOURCE_READY
Claude Code hook current-authority semantic alignment: CONTRADICTED_BY_SOURCE
Observed hook firing at this exact identity: NOT_MEASURED_IN_THIS_AUDIT
Observed durable state write at this exact identity: NOT_MEASURED_IN_THIS_AUDIT
Observed result/effect re-entry at this exact identity: NOT_MEASURED_IN_THIS_AUDIT
Provider execution during audit: NONE
Secret lookup during audit: NONE
Installer classification for full Clay/EntityOS lifecycle: DEGRADED
```

`NATIVE` is not earned yet. A hook file plus settings registration is source evidence, not lifecycle runtime evidence.

## Why this matters

A stale lifecycle hook has unusually high leverage because it is injected repeatedly. Even if current repository prose is correct, an old `SessionStart` / `UserPromptSubmit` identity kernel can reintroduce retired product/identity framing on every turn.

This is the installer analogue of a stale authority surface: self-consistent local behavior can still be globally stale.

## Acceptance gate for `NATIVE`

Promote Claude Code integration from `DEGRADED` only after all of these are observed at one exact repository identity:

1. **Authority-first boot** — hook resolves current owner/supervisor authority before injecting project identity or execution policy.
2. **Current identity** — injected project framing resolves to Clay + EntityOS + HCU, with worker/session as organ; historical Frank naming remains donor/provenance where applicable, not competing persistent authority.
3. **HARD_OFF preservation** — no provider import, secret lookup, request construction, network use, Aider/provider fallback, or provider execution can occur when current authority denies it.
4. **Real lifecycle firing** — trigger a harmless Claude Code lifecycle event and observe a unique event-bound hook receipt produced by the hook itself.
5. **Durable state** — if persistence is claimed, re-enter/restart and observe the exact state/receipt still present.
6. **Result re-entry** — if an effect is claimed, verify the actual outcome separately; request != effect.
7. **Negative-path test** — missing/malformed/stale authority fails closed instead of silently falling back to historical identity/execution semantics.

## Cheapest high-information next change

Do **not** delete the existing hook wholesale. First separate two concerns:

```text
A. lifecycle transport + receipt mechanics
B. project identity/authority payload
```

Keep the transport if it is useful. Replace the embedded identity/authority payload with a small current-authority resolver whose expected program/product/architecture values are derived from canonical current surfaces rather than hard-coded historical constants.

Then add a source-level regression that rejects these failure modes:

```text
current supervisor says EntityOS/HCU but hook injects retired competing identity
current HARD_OFF but hook reaches provider/secret/network boundary
missing authority silently falls back to permissive behavior
hook configuration exists but no event-bound receipt can be demonstrated
```

## Evidence scope

This audit proves only a source-level mismatch and an installer blocker at the inspected identity. It does **not** prove that a running Claude Code process has loaded these exact files, that hooks are currently firing, or that any historical hook receipt is valid for this commit.

That distinction is intentional: `SOURCE_READY != RUNTIME_OBSERVED`.