#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

# GROK -> CLAY repo-native research-organ bootstrap
# No raw secret may be committed, printed, embedded in prompts, receipts, or repo state.
# Required secret input (choose one):
#   CLAY_GITHUB_SSH_PRIVATE_KEY_B64   base64-encoded private SSH key
#   CLAY_GITHUB_SSH_KEY_FILE          path to an already-mounted private SSH key
# Optional:
#   CLAY_GITHUB_KNOWN_HOSTS_B64       base64-encoded known_hosts content
#   CLAY_WORKDIR                      dedicated checkout path
#   CLAY_TRIGGER                      default: clay
#   GROK_MODEL                        default: grok-unknown
#   GROK_RUNTIME                      free-form runtime provenance, default: unknown

REPO_SLUG="gschaidergabriel/clay-global-research-entity"
REPO_SSH="git@github.com:${REPO_SLUG}.git"
ACTOR_ID="grok-research"
PROVIDER="xAI"
TRIGGER="${CLAY_TRIGGER:-clay}"
GROK_MODEL="${GROK_MODEL:-grok-unknown}"
GROK_RUNTIME="${GROK_RUNTIME:-unknown}"
WORKDIR="${CLAY_WORKDIR:-${HOME}/clay-grok-research}"
SSH_DIR="${HOME}/.ssh"
KEY_FILE="${SSH_DIR}/clay_grok_ed25519"
KNOWN_HOSTS="${SSH_DIR}/clay_github_known_hosts"
JOIN_JSON="${WORKDIR}/.grok_join_result.json"
ROLE_JSON="${WORKDIR}/.grok_role_result.json"

fail() {
  printf 'GROK_CLAY_JOIN=FAILED reason=%s\n' "$*" >&2
  exit 1
}

need() {
  command -v "$1" >/dev/null 2>&1 || fail "missing_required_command:$1"
}

need git
need ssh
need python3

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

# ---- Secret admission: private SSH key only from runtime secret injection ----
if [[ -n "${CLAY_GITHUB_SSH_KEY_FILE:-}" ]]; then
  [[ -f "$CLAY_GITHUB_SSH_KEY_FILE" ]] || fail "CLAY_GITHUB_SSH_KEY_FILE_not_found"
  cp "$CLAY_GITHUB_SSH_KEY_FILE" "$KEY_FILE"
elif [[ -n "${CLAY_GITHUB_SSH_PRIVATE_KEY_B64:-}" ]]; then
  printf '%s' "$CLAY_GITHUB_SSH_PRIVATE_KEY_B64" | base64 -d > "$KEY_FILE" \
    || fail "invalid_CLAY_GITHUB_SSH_PRIVATE_KEY_B64"
else
  fail "missing_SSH_secret:set_CLAY_GITHUB_SSH_PRIVATE_KEY_B64_or_CLAY_GITHUB_SSH_KEY_FILE"
fi
chmod 600 "$KEY_FILE"
unset CLAY_GITHUB_SSH_PRIVATE_KEY_B64 || true

# ---- Strict GitHub host verification ----
if [[ -n "${CLAY_GITHUB_KNOWN_HOSTS_B64:-}" ]]; then
  printf '%s' "$CLAY_GITHUB_KNOWN_HOSTS_B64" | base64 -d > "$KNOWN_HOSTS" \
    || fail "invalid_CLAY_GITHUB_KNOWN_HOSTS_B64"
  unset CLAY_GITHUB_KNOWN_HOSTS_B64 || true
else
  # Bootstrap GitHub SSH host keys from GitHub's HTTPS meta endpoint.
  # HTTPS PKI authenticates this bootstrap; SSH then runs with StrictHostKeyChecking=yes.
  python3 - "$KNOWN_HOSTS" <<'PY'
import json, ssl, sys, urllib.request
out = sys.argv[1]
ctx = ssl.create_default_context()
req = urllib.request.Request(
    "https://api.github.com/meta",
    headers={"Accept": "application/vnd.github+json", "User-Agent": "clay-grok-bootstrap/1"},
)
with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
    data = json.load(r)
keys = data.get("ssh_keys") or []
if not keys:
    raise SystemExit("GitHub meta endpoint returned no ssh_keys")
with open(out, "w", encoding="utf-8") as f:
    for key in keys:
        f.write("github.com " + key.strip() + "\n")
PY
fi
chmod 600 "$KNOWN_HOSTS"

export GIT_SSH_COMMAND="ssh -i ${KEY_FILE} -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=${KNOWN_HOSTS} -o BatchMode=yes"

# Read/write authentication gate. This does not print the key.
git ls-remote "$REPO_SSH" HEAD >/dev/null 2>&1 || fail "github_ssh_auth_or_repo_access_failed"

# ---- Dedicated clean checkout ----
if [[ -e "$WORKDIR" && ! -d "$WORKDIR/.git" ]]; then
  fail "CLAY_WORKDIR_exists_but_is_not_git_repo:${WORKDIR}"
fi

if [[ ! -d "$WORKDIR/.git" ]]; then
  git clone --branch main --single-branch "$REPO_SSH" "$WORKDIR"
fi

cd "$WORKDIR"
REMOTE_URL="$(git remote get-url origin)"
[[ "$REMOTE_URL" == "$REPO_SSH" ]] || fail "unexpected_origin:${REMOTE_URL}"
[[ -z "$(git status --porcelain)" ]] || fail "working_tree_not_clean_before_join"

git fetch --prune origin main
git checkout main >/dev/null 2>&1 || fail "cannot_checkout_main"
git merge --ff-only origin/main >/dev/null 2>&1 || fail "local_main_not_fast_forwardable"

CANON="research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json"
BOOT="research_entity/continuity/BOOTSTRAP_MINIMAL.json"
ACTORS="research_entity/global/RESEARCH_ACTOR_REGISTRY.json"
MEMBERSHIP="research_entity/global/SESSION_MEMBERSHIP_PROTOCOL.md"
ROOMS="research_entity/rooms/ROOM_REGISTRY.json"
CENTER="research_entity/global/REPO_NATIVE_RESEARCH_CENTER_PROTOCOL.md"
WORKER_DIRECTIVE="research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"

for f in "$CANON" "$BOOT" "$ACTORS" "$MEMBERSHIP" "$ROOMS" "$CENTER" "$WORKER_DIRECTIVE"; do
  [[ -s "$f" ]] || fail "missing_boot_file:$f"
done

# ---- Canonical + actor + room preflight ----
readarray -t META < <(python3 - "$CANON" "$BOOT" "$ACTORS" "$ROOMS" "$ACTOR_ID" "$TRIGGER" <<'PY'
import json, sys
canon_p, boot_p, actors_p, rooms_p, actor_id, trigger = sys.argv[1:]
canon = json.load(open(canon_p, encoding="utf-8"))
boot = json.load(open(boot_p, encoding="utf-8"))
actors = json.load(open(actors_p, encoding="utf-8"))
rooms = json.load(open(rooms_p, encoding="utf-8"))
if boot.get("canonical_repository") != "gschaidergabriel/clay-global-research-entity":
    raise SystemExit("canonical_repository_mismatch")
if boot.get("canonical_branch") != "main":
    raise SystemExit("canonical_branch_mismatch")
actor = next((a for a in actors.get("actors", []) if a.get("actor_id") == actor_id), None)
if not actor:
    raise SystemExit("grok_actor_not_registered")
if actor.get("organization") != "xAI":
    raise SystemExit("grok_actor_provider_mismatch")
if actor.get("entity_membership") != "ORGAN_OF_frank-project-global-research-entity":
    raise SystemExit("grok_actor_membership_mismatch")
room = None
for rid, cfg in rooms.get("rooms", {}).items():
    if cfg.get("trigger") == trigger:
        room = rid
for rid, cfg in rooms.get("meta_rooms", {}).items():
    if trigger in cfg.get("triggers", []):
        room = rid
if room is None:
    raise SystemExit("trigger_not_registered_for_room:" + trigger)
print(canon["revision"])
print(canon["state_hash"])
print(canon.get("entity_id", ""))
print(canon.get("entity_version", ""))
print(room)
PY
)

CANON_REV="${META[0]}"
CANON_HASH="${META[1]}"
ENTITY_ID="${META[2]}"
ENTITY_VERSION="${META[3]}"
ROOM_ID="${META[4]}"
MAIN_HEAD="$(git rev-parse HEAD)"

[[ "$ENTITY_ID" == "frank-project-global-research-entity" ]] || fail "canonical_entity_id_mismatch"

# Repository-owned preflight is mandatory for repository-based workers.
python3 tools/session_preflight.py >/dev/null || fail "session_preflight_failed"

WORKER_ID="worker-grok-$(date -u +%Y%m%dT%H%M%SZ)-$(python3 - <<'PY'
import uuid
print(uuid.uuid4().hex[:10])
PY
)"
PROMPT_RUN_ID="prompt-grok-$(date -u +%Y%m%dT%H%M%SZ)-$(python3 - <<'PY'
import uuid
print(uuid.uuid4().hex[:10])
PY
)"

# ---- Real repo-native JOIN ----
python3 tools/research_room.py join \
  --trigger "$TRIGGER" \
  --room "$ROOM_ID" \
  --worker "$WORKER_ID" \
  --actor "$ACTOR_ID" \
  --provider "$PROVIDER" \
  --model "$GROK_MODEL" \
  --canonical-revision "$CANON_REV" \
  --canonical-hash "$CANON_HASH" \
  --ancestry-family "xai-grok" \
  --focus "Mini Entity independent research/falsification" \
  --tool ssh --tool git --tool shell \
  > "$JOIN_JSON"

# Required same-room organization. SOLO performs no durable role lease; TEAM may create one.
python3 tools/research_room.py auto-role \
  --trigger "$TRIGGER" \
  --room "$ROOM_ID" \
  --worker "$WORKER_ID" \
  --actor "$ACTOR_ID" \
  --canonical-revision "$CANON_REV" \
  --canonical-hash "$CANON_HASH" \
  --ancestry-family "xai-grok" \
  > "$ROLE_JSON"

# Secret tripwire: no private key material or common secret variable names may enter generated repo deltas.
if git diff -- research_entity/rooms | grep -Eiq '(BEGIN (OPENSSH|RSA|EC|DSA) PRIVATE KEY|CLAY_GITHUB_SSH_PRIVATE_KEY_B64|XAI_API_KEY|GITHUB_TOKEN)'; then
  git reset --hard HEAD >/dev/null
  fail "secret_material_detected_in_join_delta"
fi

git config user.name "Grok Research Organ"
git config user.email "grok-research@users.noreply.github.com"
git add research_entity/rooms
[[ -n "$(git diff --cached --name-only)" ]] || fail "join_created_no_repo_delta"

git commit -m "room: join Grok research organ ${WORKER_ID}" >/dev/null
JOIN_COMMIT="$(git rev-parse HEAD)"

# ---- CAS-ish main synchronization: unique join files rebase cleanly or fail closed ----
git fetch origin main
if [[ "$(git rev-parse origin/main)" != "$MAIN_HEAD" ]]; then
  git rebase origin/main || {
    git rebase --abort || true
    fail "concurrent_main_change_caused_join_rebase_conflict"
  }
  JOIN_COMMIT="$(git rev-parse HEAD)"
fi

if git push origin HEAD:main; then
  git fetch origin main
  git merge-base --is-ancestor "$JOIN_COMMIT" origin/main \
    || fail "push_returned_success_but_join_commit_not_reachable_from_origin_main"
  SYNC_STATE="JOINED"
  SYNC_REF="main"
else
  # Branch-protection fallback preserves the exact join delta but does NOT claim shared membership.
  SAFE_ID="$(printf '%s' "$WORKER_ID" | tr -cd 'A-Za-z0-9._-')"
  FALLBACK_BRANCH="organ/grok/${SAFE_ID}"
  git checkout -b "$FALLBACK_BRANCH" >/dev/null
  git push -u origin "$FALLBACK_BRANCH" \
    || fail "main_push_failed_and_sync_branch_push_failed"
  SYNC_STATE="SYNC_PENDING"
  SYNC_REF="$FALLBACK_BRANCH"
fi

# Local join result files contain no secrets; remove them after extracting useful IDs.
JOIN_EVENT_ID="$(python3 - "$JOIN_JSON" <<'PY'
import json, sys
x=json.load(open(sys.argv[1], encoding='utf-8'))
print(x.get('join_event',{}).get('event_id','UNKNOWN'))
PY
)"
ROLE_MODE="$(python3 - "$ROLE_JSON" <<'PY'
import json, sys
x=json.load(open(sys.argv[1], encoding='utf-8'))
print(x.get('mode','UNKNOWN'))
PY
)"
rm -f "$JOIN_JSON" "$ROLE_JSON"

cat <<EOF2
[CLAY :: GROK RESEARCH ORGAN BOOT]
STATUS=${SYNC_STATE}
ACTOR_ID=${ACTOR_ID}
PROVIDER=${PROVIDER}
MODEL=${GROK_MODEL}
RUNTIME=${GROK_RUNTIME}
ENTITY=${ENTITY_ID}
ENTITY_VERSION=${ENTITY_VERSION}
CANONICAL_REVISION=${CANON_REV}
CANONICAL_STATE_HASH=${CANON_HASH}
REPO_HEAD_AT_ADMISSION=${MAIN_HEAD}
WORKER_SESSION_ID=${WORKER_ID}
PROMPT_RUN_ID=${PROMPT_RUN_ID}
ROOM=${ROOM_ID}
TRIGGER=${TRIGGER}
JOIN_EVENT_ID=${JOIN_EVENT_ID}
ROLE_MODE=${ROLE_MODE}
SYNC_REF=${SYNC_REF}

IDENTITY LAW
- You are Grok, actor_id grok-research, a temporary xAI research/falsification organ of the one persistent entity Clay.
- You are NOT Clay itself. Provider/model/session/node are provenance and capability scope, not entity identity.
- Evidence outranks organ opinion. You may not override empirical evidence or mint canonical truth from model output.

MANDATORY BOOT READS BEFORE SUBSTANTIVE WORK
1. ${BOOT}
2. ${CANON}
3. ${ACTORS}
4. ${MEMBERSHIP}
5. ${CENTER}
6. ${ROOMS}
7. ${WORKER_DIRECTIVE}
8. the current owner directive referenced by BOOTSTRAP_MINIMAL.json
9. only task-relevant current program/state/topic/evidence files after that

[MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]
- Work GRF-first and ClayCode-first.
- R0 OBSERVE -> R1 INFER -> R2 GENERATE -> R3 COUNTER -> R4 DISCRIMINATE -> R5 EMERGENT -> R6 VERIFY.
- Keep unresolved alternatives in Hyperposition until admissible evidence/discriminator collapses them.
- Structured actions are typed omega candidates; model output is never truth/effect authority.
- UNKNOWN != ZERO != ERROR != MEASURED; REPORTED != MEASURED.
- Preserve negative evidence and counterexamples.
- Prefer executable falsifiers/receipts over narrative confidence.
- On any child/delegated go worker, prepend the full mandatory protocol from ${WORKER_DIRECTIVE} literally at the top of the child prompt.
- End human-readable substantive handoffs with a short German summary.
[/MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]

WRITE / COORDINATION LAW
- Pulse the room before consequential decisions/writes and after material runtime/external results.
- Preserve actor/provider/model provenance on every durable delta.
- Pull/fetch current main before durable writes; never overwrite newer state from a stale snapshot.
- Do not create a second identity, state authority, truth store, effect path, or provider-owned memory authority.
- Secrets never enter prompts, receipts, logs, repo state, or commits.
- If STATUS=SYNC_PENDING, you are DEGRADED_UNJOINED for shared-state claims until the fallback branch is merged to current main.

NEXT ACTION
- Read the mandatory boot files now, pulse room ${ROOM_ID}, inspect active peers/tasks, then choose a non-duplicate research lane under current owner/program authority.
[/CLAY :: GROK RESEARCH ORGAN BOOT]
EOF2

if [[ "$SYNC_STATE" != "JOINED" ]]; then
  exit 20
fi
