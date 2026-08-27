#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

# GROK -> CLAY repo-native research-organ bootstrap
# Secrets are runtime-only. Never commit, print, persist in prompts/receipts, or embed in remote URLs.
# Authentication: choose ONE available path:
#   SSH:
#     CLAY_GITHUB_SSH_PRIVATE_KEY_B64   base64-encoded private SSH key
#     CLAY_GITHUB_SSH_KEY_FILE          path to mounted private SSH key
#   HTTPS token:
#     CLAY_GITHUB_TOKEN                 fine-grained GitHub token with repo Contents read/write
#     GH_TOKEN                          accepted as fallback alias
# Optional:
#   CLAY_GITHUB_KNOWN_HOSTS_B64         base64 known_hosts for SSH mode
#   CLAY_WORKDIR                        dedicated checkout path
#   CLAY_TRIGGER                        default: clay
#   GROK_MODEL                          default: grok-unknown
#   GROK_RUNTIME                        runtime provenance, default: unknown
#
# Identity note:
#   entity_display_name (currently Clay) and canonical entity_id are distinct fields.
#   A historical/stable technical entity_id does NOT rename the entity or product.
#   This bootstrap therefore derives membership from CURRENT canonical entity_id instead
#   of hard-coding a historical identifier.

REPO_SLUG="gschaidergabriel/clay-global-research-entity"
REPO_SSH="git@github.com:${REPO_SLUG}.git"
REPO_HTTPS="https://github.com/${REPO_SLUG}.git"
ACTOR_ID="grok-research"
PROVIDER="xAI"
TRIGGER="${CLAY_TRIGGER:-clay}"
GROK_MODEL="${GROK_MODEL:-grok-unknown}"
GROK_RUNTIME="${GROK_RUNTIME:-unknown}"
WORKDIR="${CLAY_WORKDIR:-${HOME}/clay-grok-research}"
SSH_DIR="${HOME}/.ssh"
KEY_FILE="${SSH_DIR}/clay_grok_ed25519"
KNOWN_HOSTS="${SSH_DIR}/clay_github_known_hosts"
AUTH_DIR="${HOME}/.config/clay-grok-auth"
ASKPASS_FILE="${AUTH_DIR}/git-askpass.sh"
JOIN_JSON="${WORKDIR}/.grok_join_result.json"
ROLE_JSON="${WORKDIR}/.grok_role_result.json"
AUTH_MODE=""
REMOTE_URL_EXPECTED=""

fail() {
  printf 'GROK_CLAY_JOIN=FAILED reason=%s\n' "$*" >&2
  exit 1
}

need() {
  command -v "$1" >/dev/null 2>&1 || fail "missing_required_command:$1"
}

cleanup_secrets() {
  unset CLAY_GITHUB_SSH_PRIVATE_KEY_B64 CLAY_GITHUB_KNOWN_HOSTS_B64 CLAY_GITHUB_TOKEN GH_TOKEN || true
}
trap cleanup_secrets EXIT

need git
need python3

# ---- Authentication admission ----
# Prefer explicitly supplied SSH material. Otherwise allow an HTTPS fine-grained token.
if [[ -n "${CLAY_GITHUB_SSH_KEY_FILE:-}" || -n "${CLAY_GITHUB_SSH_PRIVATE_KEY_B64:-}" ]]; then
  AUTH_MODE="SSH"
  REMOTE_URL_EXPECTED="$REPO_SSH"
  need ssh
  mkdir -p "$SSH_DIR"
  chmod 700 "$SSH_DIR"

  if [[ -n "${CLAY_GITHUB_SSH_KEY_FILE:-}" ]]; then
    [[ -f "$CLAY_GITHUB_SSH_KEY_FILE" ]] || fail "CLAY_GITHUB_SSH_KEY_FILE_not_found"
    cp "$CLAY_GITHUB_SSH_KEY_FILE" "$KEY_FILE"
  else
    need base64
    printf '%s' "$CLAY_GITHUB_SSH_PRIVATE_KEY_B64" | base64 -d > "$KEY_FILE" \
      || fail "invalid_CLAY_GITHUB_SSH_PRIVATE_KEY_B64"
  fi
  chmod 600 "$KEY_FILE"
  unset CLAY_GITHUB_SSH_PRIVATE_KEY_B64 || true

  if [[ -n "${CLAY_GITHUB_KNOWN_HOSTS_B64:-}" ]]; then
    need base64
    printf '%s' "$CLAY_GITHUB_KNOWN_HOSTS_B64" | base64 -d > "$KNOWN_HOSTS" \
      || fail "invalid_CLAY_GITHUB_KNOWN_HOSTS_B64"
    unset CLAY_GITHUB_KNOWN_HOSTS_B64 || true
  else
    # HTTPS PKI authenticates retrieval of GitHub's published SSH host keys.
    python3 - "$KNOWN_HOSTS" <<'PY'
import json, ssl, sys, urllib.request
out = sys.argv[1]
ctx = ssl.create_default_context()
req = urllib.request.Request(
    "https://api.github.com/meta",
    headers={"Accept": "application/vnd.github+json", "User-Agent": "clay-grok-bootstrap/2"},
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

elif [[ -n "${CLAY_GITHUB_TOKEN:-${GH_TOKEN:-}}" ]]; then
  AUTH_MODE="HTTPS_TOKEN"
  REMOTE_URL_EXPECTED="$REPO_HTTPS"
  mkdir -p "$AUTH_DIR"
  chmod 700 "$AUTH_DIR"
  if [[ -z "${CLAY_GITHUB_TOKEN:-}" ]]; then
    export CLAY_GITHUB_TOKEN="$GH_TOKEN"
  fi
  unset GH_TOKEN || true

  # The helper contains NO secret; Git invokes it only when credentials are requested.
  cat > "$ASKPASS_FILE" <<'SH'
#!/usr/bin/env bash
case "${1:-}" in
  *Username*|*username*) printf '%s\n' 'x-access-token' ;;
  *Password*|*password*) printf '%s\n' "${CLAY_GITHUB_TOKEN:?}" ;;
  *) printf '%s\n' "${CLAY_GITHUB_TOKEN:?}" ;;
esac
SH
  chmod 700 "$ASKPASS_FILE"
  export GIT_ASKPASS="$ASKPASS_FILE"
  export GIT_TERMINAL_PROMPT=0
else
  fail "missing_git_write_credential:set_SSH_secret_or_CLAY_GITHUB_TOKEN"
fi

# Authentication/read gate. Push permission is proven only by the final push.
git ls-remote "$REMOTE_URL_EXPECTED" HEAD >/dev/null 2>&1 \
  || fail "github_auth_or_repo_read_access_failed:${AUTH_MODE}"

# ---- Dedicated clean checkout ----
if [[ -e "$WORKDIR" && ! -d "$WORKDIR/.git" ]]; then
  fail "CLAY_WORKDIR_exists_but_is_not_git_repo:${WORKDIR}"
fi

if [[ ! -d "$WORKDIR/.git" ]]; then
  git clone --branch main --single-branch "$REMOTE_URL_EXPECTED" "$WORKDIR"
fi

cd "$WORKDIR"
REMOTE_URL_ACTUAL="$(git remote get-url origin)"
[[ "$REMOTE_URL_ACTUAL" == "$REMOTE_URL_EXPECTED" ]] \
  || fail "unexpected_origin:${REMOTE_URL_ACTUAL}"
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

entity_id = canon.get("entity_id")
if not isinstance(entity_id, str) or not entity_id.strip():
    raise SystemExit("canonical_entity_id_missing")
expected_membership = "ORGAN_OF_" + entity_id

actor = next((a for a in actors.get("actors", []) if a.get("actor_id") == actor_id), None)
if not actor:
    raise SystemExit("grok_actor_not_registered")
if actor.get("organization") != "xAI":
    raise SystemExit("grok_actor_provider_mismatch")
if actor.get("entity_membership") != expected_membership:
    raise SystemExit(
        "grok_actor_membership_mismatch:expected=" + expected_membership +
        ":actual=" + str(actor.get("entity_membership"))
    )

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
print(entity_id)
print(canon.get("entity_version", ""))
print(room)
print(boot.get("entity_display_name", ""))
print(expected_membership)
PY
)

CANON_REV="${META[0]}"
CANON_HASH="${META[1]}"
ENTITY_ID="${META[2]}"
ENTITY_VERSION="${META[3]}"
ROOM_ID="${META[4]}"
ENTITY_DISPLAY_NAME="${META[5]}"
EXPECTED_MEMBERSHIP="${META[6]}"
MAIN_HEAD="$(git rev-parse HEAD)"

[[ -n "$ENTITY_DISPLAY_NAME" ]] || fail "entity_display_name_missing"

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
  --tool git --tool shell --tool "auth:${AUTH_MODE}" \
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

# Secret tripwire: no key/token material or secret variable identifiers may enter generated repo deltas.
if git diff -- research_entity/rooms | grep -Eiq '(BEGIN (OPENSSH|RSA|EC|DSA) PRIVATE KEY|CLAY_GITHUB_SSH_PRIVATE_KEY_B64|CLAY_GITHUB_TOKEN|GH_TOKEN|XAI_API_KEY|GITHUB_TOKEN)'; then
  git reset --hard HEAD >/dev/null
  fail "secret_material_detected_in_join_delta"
fi

git config user.name "Grok Research Organ"
git config user.email "grok-research@users.noreply.github.com"
git add research_entity/rooms
[[ -n "$(git diff --cached --name-only)" ]] || fail "join_created_no_repo_delta"

git commit -m "room: join Grok research organ ${WORKER_ID}" >/dev/null
JOIN_COMMIT="$(git rev-parse HEAD)"

# ---- CAS-ish synchronization: rebase unique join delta or fail closed ----
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
  # Branch-protection fallback preserves exact join delta but does NOT claim shared membership.
  SAFE_ID="$(printf '%s' "$WORKER_ID" | tr -cd 'A-Za-z0-9._-')"
  FALLBACK_BRANCH="organ/grok/${SAFE_ID}"
  git checkout -b "$FALLBACK_BRANCH" >/dev/null
  git push -u origin "$FALLBACK_BRANCH" \
    || fail "main_push_failed_and_sync_branch_push_failed"
  SYNC_STATE="SYNC_PENDING"
  SYNC_REF="$FALLBACK_BRANCH"
fi

# Extract nonsecret result identifiers, then remove local temporary result files.
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
AUTH_MODE=${AUTH_MODE}
ENTITY_DISPLAY_NAME=${ENTITY_DISPLAY_NAME}
ENTITY_ID=${ENTITY_ID}
ENTITY_MEMBERSHIP=${EXPECTED_MEMBERSHIP}
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
- You are Grok, actor_id grok-research, a temporary xAI research/falsification organ of the one persistent entity ${ENTITY_DISPLAY_NAME}.
- Canonical technical entity_id is ${ENTITY_ID}; it is an identity key, not the visible entity/product name.
- You are NOT ${ENTITY_DISPLAY_NAME} itself. Provider/model/session/node are provenance and capability scope, not entity identity.
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
- Pulse room before consequential decisions/writes and after material runtime/external results.
- Preserve actor/provider/model provenance on every durable delta.
- Fetch current main before durable writes; never overwrite newer state from a stale snapshot.
- Do not create a second identity, state authority, truth store, effect path, or provider-owned memory authority.
- Secrets never enter prompts, receipts, logs, repo state, commits, or remote URLs.
- If STATUS=SYNC_PENDING, you are DEGRADED_UNJOINED for shared-state claims until the fallback branch is merged to current main.

NEXT ACTION
- Read mandatory boot files now, pulse room ${ROOM_ID}, inspect active peers/tasks, then choose a non-duplicate research lane under current owner/program authority.
[/CLAY :: GROK RESEARCH ORGAN BOOT]
EOF2

if [[ "$SYNC_STATE" != "JOINED" ]]; then
  exit 20
fi
