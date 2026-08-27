# AI: START HERE. DO NOT SCAN THE REPO.

Use caveman rules.

## Goal

Join this project safely.
Do not invent paths.
Do not call providers.
Do not spend money.
Do not edit Frank Harness.
Do not claim success without proof.

## Step 1 — find the repo

You need the path of this file first.

From this file, repo root is:

```text
parent directory of AI_START_HERE_DO_NOT_SCAN_REPO/
```

Do not assume Downloads.
Do not assume home directory.
Do not assume current working directory.
Do not assume clone path.

If your host gives you only an attachment and no repository checkout, result is:

```text
DEGRADED
```

You may read the attachment, but you cannot claim native install or Git state.

## Step 2 — read only these first

Resolve paths relative to the real repo root:

```text
research_entity/continuity/BOOTSTRAP_MINIMAL.json
research_entity/rooms/PROGRAM_STATE.json
research_entity/claycode/autonomous/SUPERVISOR_INBOX.json
```

Then read the steering file named by `SUPERVISOR_INBOX.json`.

If a newer owner authority is pointed to, read it too.

Do not trust old summaries over these current files.

## Step 3 — current hard stop

At the Triggerword-3 pass on 2026-08-27, provider authority epoch 9.13 is HARD_OFF:

```text
external provider routes = false
Together = forbidden
paid fallback = forbidden
```

This is volatile state. Re-read current authority before every real install/run.

If current authority is still HARD_OFF:

```text
NO secret lookup
NO provider import
NO provider network call
NO Aider/provider fallback
NO Together
```

Local non-provider inspection/testing may still be allowed by current authority.

## Step 4 — detect your host

Choose one route only.

### Claude Code

Use native filesystem + Git tools if the real checkout is available.
Read exact current files.
Make scoped edits on a branch.
Run only authority-allowed local tests.

Install result can be:

```text
NATIVE
```

only if file reads, writes, Git branch/commit, and required local validation are actually observed.

### Codex CLI

Same rule: use the real checkout and native terminal/filesystem.
Never translate tool availability into effect success.

Possible result:

```text
NATIVE
```

only after observed hooks/state writes/receipts required by the task.

### Hermes Agent

First detect whether it has:

```text
filesystem read
filesystem write
Git or equivalent version control
durable state
command execution
```

If all required capabilities exist and are verified, map them directly.
If some exist but lifecycle hooks differ, use:

```text
ADAPTED
```

If durable state or effect receipt support is missing, use:

```text
DEGRADED
```

### ChatGPT Web

Use connected GitHub/file tools when actually available.
Do not pretend there is a local shell if none exists.
Do not claim a hook fired unless a real tool/receipt shows it.

Typical result for repository work may be:

```text
ADAPTED
```

when GitHub read/write exists but host-native lifecycle hooks do not.

### Claude Web

Same rule as ChatGPT Web: detect real repository/file/tool capability first.
No native-shell assumption.
No fake hook success.

Use `ADAPTED` or `DEGRADED` based on observed capabilities.

### Grok Web

Same rule: detect actual file/repository/state/effect capabilities.
Do not infer them from model text.

Use `ADAPTED`, `DEGRADED`, or `BLOCKED` based on observation.

### Generic fallback

Required capabilities for full native install:

```text
R = exact repository read
W = scoped repository write
V = version-control identity
S = durable state
E = effect/result receipt
X = authority-allowed local execution
```

Decision:

```text
R+W+V+S+E+X observed -> NATIVE
most present, mapping needed -> ADAPTED
read/limited state only -> DEGRADED
required capability absent for requested operation -> BLOCKED
```

## Step 5 — minimal project model

Current identities:

```text
persistent research entity = Clay
product = EntityOS
integrated cognition/compute = HCU
```

Historical names are lineage/compatibility unless current authority says otherwise.

Truth law:

```text
model output != fact
request != effect
source-ready != runtime-observed
component PASS != whole-product PASS
FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT
```

## Step 6 — verify before success

For any install or host mapping, prove what matters:

```text
1. exact repo/ref read
2. exact authority read
3. expected local hook or entry point invoked
4. durable state changed where expected
5. effect/result receipt exists where required
6. replay/reopen behavior matches contract where required
7. no forbidden provider/secret path fired
```

If one required proof is missing, do not print NATIVE.

## Step 7 — report one final class

Exactly one:

```text
NATIVE
ADAPTED
DEGRADED
BLOCKED
```

Then list:

```text
repo identity
head/ref
host capabilities actually observed
files changed
local tests actually run
receipts actually observed
missing proof
```

## Do not scan root

For the human explanation, read:

`../HUMAN_READ_THIS/README.md`

For engineering/research navigation, read:

`../DEV_SOURCE_RESEARCH/README.md`

For this exact Triggerword-3 curation pass, read:

`../DEV_SOURCE_RESEARCH/repository/TRIGGERWORD3_2026-08-27_GPT56SOL.md`
