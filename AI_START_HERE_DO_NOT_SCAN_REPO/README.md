# AI: start here. Do not scan the whole repository.

Goal: enter the project with minimum tokens and without inventing paths or authority.

## 1. Find the repository you actually have

Do not assume Downloads, `$HOME`, clone path, attachment mount, or current working directory.

Locate the repository by finding both:

```text
research_entity/
the artefact/
```

If only one exists, report `DEGRADED` and continue read-only until the layout is resolved.

## 2. Read authority before project prose

Read, in this order:

```text
research_entity/continuity/BOOTSTRAP_MINIMAL.json
research_entity/rooms/PROGRAM_STATE.json
research_entity/claycode/autonomous/SUPERVISOR_INBOX.json
<the steering file named by SUPERVISOR_INBOX.json>
```

Then read task-relevant source/tests/receipts.

Never treat old bootstrap text, chat memory, model consensus or a stale plan as stronger than current canonical authority.

## 3. Current entry rule at this snapshot

At canonical `main` `854f6bc87780f4a5242489a6c807d186b16a8c3d`, supervisor state is 9.13 HARD_OFF:

```text
provider routes: NOT ADMITTED
Together: FORBIDDEN
paid fallback: FORBIDDEN
```

The 72-hour Frankenstein Bauleiter/Bugfixer provider-calling plan is source/donor material only under this state. Do not launch it unchanged.

## 4. Detect your host capabilities

Classify what you really have before mapping instructions:

```text
can_read_files
can_write_files
can_run_local_commands
can_use_git
can_access_github
can_persist_state
can_call_external_network
can_install_packages
can_receive_hooks/events
```

Do not fake a missing capability.

## 5. Host routes

### Claude Code

Use repository-local source and Git. Read current authority first. Do not let `.claude/` or historical harness instructions override supervisor authority.

### Codex CLI

Open the actual clone, read the authority stack, inspect current Git head, then operate on bounded files. Keep exact SHAs in any durable receipt.

### Hermes Agent

Map its real file/tool/state capabilities to the same authority contract. If it cannot verify Git or current authority, use `DEGRADED` mode and avoid execution claims.

### ChatGPT Web

Use the GitHub connector for current repository state. Uploaded bootstrap files are caches only. Do not claim a local runtime test from source inspection.

### Claude Web

Use connected repository/file tools if available. Without current Git access, report `DEGRADED` and keep claims historical/source-only.

### Grok Web

Same rule: current repository/authority must be verifiable before current-state claims. No tool access means no invented runtime status.

### Generic fallback

If the host has only text input/output:

1. ask for/export the four authority files above;
2. ask for exact current `main` SHA;
3. work source-only;
4. label the result `DEGRADED`;
5. do not claim hooks, durable state, runtime execution or effects.

## 6. Native / adapted / degraded / blocked

Final installation classification must be exactly one of:

```text
NATIVE    = host supports required lifecycle/tool/state behavior directly
ADAPTED   = equivalent behavior exists through a documented adapter
DEGRADED  = useful subset works; missing capabilities are explicit
BLOCKED   = a required authority/capability cannot be satisfied safely
```

Never call an install successful merely because files copied or a command returned zero.

## 7. Verify installation behavior

Verify the actual things that matter:

```text
hook/event really fired
state write really persisted
read-after-write returns expected generation
request identity is preserved
effect request is distinct from effect result
failure is visible
restart/re-entry preserves required state
```

A config file existing is not proof that a hook fired.

## 8. Frankenstein-specific safety check

Before invoking any Frankenstein orchestration that can reach providers, secrets, Aider or network:

1. resolve current canonical provider authority;
2. fail closed if authority is missing/ambiguous;
3. under HARD_OFF, prove `provider_calls = 0` and `secret_lookups = 0`;
4. do not modify Frank's own Harness to bypass this rule;
5. treat provider-authored changes after HARD_OFF as requiring independent clean non-provider review before runtime credit.

## 9. Then choose your layer

Human explanation:

```text
HUMAN_READ_THIS/README.md
```

Technical evidence map:

```text
DEV_SOURCE_RESEARCH/README.md
```

Research archive:

```text
research_entity/
```

Do not root-scan unless a concrete task requires it.
