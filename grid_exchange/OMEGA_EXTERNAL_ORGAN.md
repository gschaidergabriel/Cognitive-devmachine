# OMEGA External Organ — GRID10 ↔ GitHub ↔ API ↔ GRID10

Status: CODE COMMITTED, LOCAL HOST NOT VERIFIED, NO LIVE VOICE-SESSION CONNECTION.

## Authority and task transport

OMEGA/GRID remains the cognitive coordinator, TITAN/UnifiedDB remains the canonical memory substrate. The small SQLite file created by omega_job_bridge.py is strictly a task/receipt ledger, not a replacement memory database.

1. An already-authorized GRID coordinator creates an OPEN task with capability omega-external in the actual GRID10 tasks table, or an authenticated actor submits an OMEGA_JOB/v1 JSON object to the existing GitHub control branch.
2. The worker reads GRID10 task data strictly read-only and/or polls grid_exchange/jobs/inbox/<job_id>.json on the per-owner control branch. It verifies immutable request hashes and owner/machine pairing.
3. A single worker records STARTED in SQLite before any external API call. Provider execution is off by default and has an allowlist and daily budget.
4. chat, code and research use the OpenAI Responses API. image uses the OpenAI Images API to produce a local PNG, with SHA256 and byte-count recorded in its result receipt.
5. The worker writes OMEGA_JOB_RESULT/v1 to grid_exchange/jobs/results/<job_id>.json on the matching results branch.
6. If the job originated in the actual GRID10 task table, the worker uses the existing Fabric.emit_node_result API to deliver a NODE_RESULT/v1 into the existing GRID10 Result Channel. The existing leased coordinator must perform CAS admission to S1. There is NO autonomous S1 commit and NO new effect authority.

This is low-token-overhead message transport, not token-free model inference. Context references are lightweight pointers; the existing TITAN-MX/retrieval pipeline must resolve them if needed. No new memory authority or parallel cognitive runtime is created.

## Exact host binding

Gabriel: owner=gabriel, machine_id=ai-core-node, control=chatgpt-local-ai-core-node-control, results=chatgpt-local-ai-core-node-results.
Andreas: owner=andreas, machine_id=andreas-maco, control=chatgpt-local-andreas-maco-control, results=chatgpt-local-andreas-maco-results.

Identity is checked inside job and receipt bytes, not inferred from a branch name. Do not mix the two people or use one host as a fallback for the other.

The existing local bridge daemon, omega_grid_relay.py, omega_chatgpt_mcp.py, all effect guards, GRID coordinator and canonical UnifiedDB are left untouched.

## GRID task format

Only tasks with capability omega-external, status OPEN, and this explicit payload schema are read by the worker. The task must already be created by the actual authorized GRID coordinator:

~~~json
{
  "schema": "OMEGA_GRID_EXTERNAL_TASK/v1",
  "owner": "gabriel",
  "machine_id": "ai-core-node",
  "kind": "image",
  "prompt": "Create a cinematic landscape hero image for the homepage.",
  "context_refs": ["titan:website-brief-123"],
  "created_at": "2026-10-29T01:00:00Z"
}
~~~

The worker does NOT call seed_task() to insert arbitrary production tasks and does NOT call coordinator_commit(). If an output does not have matching GRID task provenance, it is returned through GitHub only, never falsely promoted as GRID cognition.

## Local installation

Use a separate clone or worktree. NEVER work in ~/.claude/star/local_bridge_state/repo because the existing daemon force-checks that directory. Confirm the actual host binding and actual GRID DB path before starting anything.

~~~sh
python3 -m unittest discover -s grid_exchange -p 'test_omega_job_bridge.py' -v
mkdir -p "$HOME/.local/state/omega-job-bridge/artifacts"
chmod 700 "$HOME/.local/state/omega-job-bridge"

printf '%s\n' 'Create a unique cinematic website hero image' > /tmp/omega-prompt.txt
python3 grid_exchange/omega_job_bridge.py \
  --owner gabriel \
  --db "$HOME/.local/state/omega-job-bridge/ledger.sqlite" \
  new omega-hero-001 image /tmp/omega-prompt.txt \
  --grid-ref grid10:website:hero > /tmp/omega-hero-001.json

# With a restricted GITHUB_TOKEN securely provided on the host:
python3 grid_exchange/omega_job_bridge.py \
  --owner gabriel --db "$HOME/.local/state/omega-job-bridge/ledger.sqlite" \
  submit /tmp/omega-hero-001.json
~~~

Put credentials only into a protected host environment file (mode 0600), never into Git, chat text or task payloads:

~~~sh
OPENAI_API_KEY=<host-secret>
GITHUB_TOKEN=<repo-scoped-host-secret>
OMEGA_JOB_API_ENABLED=1
OMEGA_JOB_CAPABILITIES=chat,code,research,image
OMEGA_JOB_MAX_DAILY=20
OMEGA_IMAGE_MODEL=gpt-image-2.5-sunburst
OMEGA_IMAGE_SIZE=1536x1024
OMEGA_GRID_DB=/verified/active/grid10.sqlite
OMEGA_JOB_POLL_SECONDS=20
~~~

Defaults: effects/API off; only chat capability allowed; max 20 API tasks/day; one worker per SQLite ledger. Image output is PNG and stays on the host. Transferring it to a website or changing code requires a separate authorized Local Bridge effect with a verified receipt.

Start after verifying those prerequisites:

~~~sh
python3 grid_exchange/omega_job_bridge.py \
  --owner gabriel \
  --db "$HOME/.local/state/omega-job-bridge/ledger.sqlite" \
  --artifact-dir "$HOME/.local/state/omega-job-bridge/artifacts" loop
~~~

Other CLI subcommands: import <job.json>, once, show <job_id>, reconcile, grid-ingest, grid-reentry, grid-snapshot <scope>. The --grid-db option is global or set via OMEGA_GRID_DB.

Important: A provider call whose outcome is uncertain is never automatically repeated. After a crash and after stopping the worker, use reconcile to mark lingering STARTED records UNKNOWN. Sending an already-generated receipt to GitHub again is safe and idempotent; re-running provider generation is not.

## Realtime/voice product boundary

This running native ChatGPT/GPT-Live voice conversation cannot be forced to autonomously poll GitHub, nor can a repository script directly trigger its built-in image generation tool. The autonomous backend uses independently authenticated provider API calls. For interactive ChatGPT tool calls, the existing authenticated omega_* MCP gateway must actually be present in this session. A system prompt or memory setting cannot create that tool access. GitHub polling is asynchronous, not a millisecond voice transport; use the existing direct typed broker/MCP path for real-time conversation.

## Acceptance gates for production

1. Read a fresh Local Bridge PASS receipt from the correct ai-core-node/gabriel host.
2. Verify the active GRID10 runtime DB, its task schema and actual coordinator; do not use experimental fixtures as production evidence.
3. Pass offline regression tests on the committed source.
4. Submit one request via existing control branch, verify a matching immutable receipt via existing results branch.
5. Verify a generated PNG exists locally and matches its SHA256 receipt, then independently verify any requested website installation.
6. Verify the same source-bound task result enters GRID10's Result Channel and then achieves a real coordinator CAS S1 commit.
7. Verify owner/host isolation and UNKNOWN/no-replay across failures.
8. Separately verify native ChatGPT text and GPT-Live actually expose omega_* tools when claiming interactive access.

Until all gates pass: CODE_READY, PRODUCTION_CONNECTION_UNVERIFIED. No voice or production host connection is implied by GitHub commits.
