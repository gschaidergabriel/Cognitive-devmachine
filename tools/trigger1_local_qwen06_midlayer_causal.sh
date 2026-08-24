#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Compatibility entrypoint: the retained self-hosted workflow still calls this
# historical filename. The effective scientific path is the strongest intermediate
# residual protocol plus its fail-closed promotion bridge, not the superseded
# evaluation-label-coupled midlayer executor.
unset \
  OPENAI_API_KEY OPENAI_API_KEYS \
  ANTHROPIC_API_KEY ANTHROPIC_API_KEYS \
  GROQ_API_KEY GROQ_API_KEYS GROQ2_API_KEY GROQ3_API_KEY \
  MISTRAL_API_KEY MISTRAL_API_KEYS MISTRAL2_API_KEY MISTRAL3_API_KEY \
  NVIDIA_API_KEY NVIDIA_API_KEYS NVIDIA_NIM_API_KEY NVIDIA2_API_KEY NVIDIA3_API_KEY NGC_API_KEY \
  OPENROUTER_API_KEY OPENROUTER_API_KEYS OPENROUTER2_API_KEY OPENROUTER3_API_KEY \
  TOGETHER_API_KEY TOGETHER_API_KEYS \
  HF_TOKEN HUGGING_FACE_HUB_TOKEN HUGGINGFACE_HUB_TOKEN || true
while IFS= read -r name; do
  case "$name" in
    OPENAI*KEY*|ANTHROPIC*KEY*|GROQ*KEY*|MISTRAL*KEY*|NVIDIA*KEY*|NGC*KEY*|OPENROUTER*KEY*|TOGETHER*KEY*) unset "$name" || true ;;
  esac
done < <(compgen -v)
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1

OUT_DIR="${1:?usage: trigger1_local_qwen06_midlayer_causal.sh OUTPUT_DIR}"
mkdir -p "$OUT_DIR"

# Defense in depth for GitHub Actions runs queued before the workflow-level atomic
# lease gate existed. Historical issue-event runs keep their historical workflow
# definition but may check out current main when a self-hosted runner eventually
# starts. Never allow such a run to reach runtime setup or intervention unless the
# current workflow gate already admitted the canonical create-only lease.
if [[ "${GITHUB_ACTIONS:-}" == "true" && "${TRIGGER1_LEASE_ADMITTED:-}" != "true" ]]; then
  python3 - "$OUT_DIR/trigger1_local_activation_api_result.json" <<'PY'
import json, pathlib, sys
obj={
  'schema':'CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1',
  'status':'BLOCKED_CANONICAL_ATOMIC_LEASE_NOT_ADMITTED',
  'reason':'GITHUB_ACTIONS_TRIGGER1_REQUIRES_WORKFLOW_ATOMIC_LEASE_GATE',
  'github_actions':True,
  'unusual_experiment_executed':False,
  'zero_provider_billing':True,
  'external_provider_credentials_read':False,
  'provider_network_calls':0,
  'credit_scope':'NONE',
  'compatibility_entrypoint':'trigger1_local_qwen06_midlayer_causal.sh',
  'next_action':'DISPATCH_ONLY_WITH_CANONICAL_CREATE_ONLY_GO_LEASE'
}
pathlib.Path(sys.argv[1]).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
PY
  exit 42
fi

canonical_path(){
  python3 - "$1" <<'PY'
from pathlib import Path
import sys
print(Path(sys.argv[1]).resolve(strict=False))
PY
}
OUT_DIR_CANONICAL="$(canonical_path "$OUT_DIR")"

USER_HOME="${HOME:?HOME is required}"
CACHE_ROOT="${CLAY_TRIGGER1_LOCAL_CACHE:-${XDG_CACHE_HOME:-$USER_HOME/.cache}/clay-trigger1-local}"
mkdir -p "$CACHE_ROOT"
available_kb(){ df -Pk "$CACHE_ROOT" | awk 'NR==2 {print $4}'; }
BEFORE_KB="$(available_kb)"
if [[ "$BEFORE_KB" -lt 4000000 ]]; then
  # Bounded cleanup only. Never delete this run's evidence-in-progress directory.
  for candidate in \
    "${RUNNER_TEMP:-/tmp}"/clay-trigger1-v2-* \
    "${RUNNER_TEMP:-/tmp}"/clay-trigger1-qwen06-*; do
    [[ -e "$candidate" ]] || continue
    candidate_canonical="$(canonical_path "$candidate")"
    [[ "$candidate_canonical" == "$OUT_DIR_CANONICAL" ]] && continue
    rm -rf -- "$candidate" 2>/dev/null || true
  done
  rm -rf "$CACHE_ROOT/venv.tmp" "$USER_HOME/.cache/pip" 2>/dev/null || true
fi
mkdir -p "$OUT_DIR"
if [[ "$(canonical_path "$OUT_DIR")" != "$OUT_DIR_CANONICAL" ]]; then
  echo "BLOCKED_OUTPUT_DIR_IDENTITY_CHANGED_DURING_CLEANUP" >&2
  exit 3
fi
AFTER_KB="$(available_kb)"
printf '{"available_kb_before":%s,"available_kb_after":%s,"current_output_preserved":true}\n' "$BEFORE_KB" "$AFTER_KB" > "$OUT_DIR/disk_preflight.json"
if [[ "$AFTER_KB" -lt 3000000 ]]; then
  python3 - "$OUT_DIR/trigger1_local_activation_api_result.json" "$BEFORE_KB" "$AFTER_KB" <<'PY'
import json, pathlib, sys
obj={
  'schema':'CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1',
  'status':'BLOCKED_INSUFFICIENT_FREE_DISK_AFTER_BOUNDED_CLEANUP',
  'available_kb_before':int(sys.argv[2]),
  'available_kb_after':int(sys.argv[3]),
  'current_output_preserved':True,
  'zero_provider_billing':True,
  'external_provider_credentials_read':False,
  'provider_network_calls':0,
  'credit_scope':'NONE',
  'compatibility_entrypoint':'trigger1_local_qwen06_midlayer_causal.sh'
}
pathlib.Path(sys.argv[1]).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
PY
  exit 3
fi

PRE="$OUT_DIR/source_identity_pre.json"
POST="$OUT_DIR/source_identity_post.json"
LEASE_BINDING="$OUT_DIR/lease_source_binding.json"
set +e
python3 tools/git_source_identity_v1.py --repo "$ROOT" --require-clean > "$PRE"
pre_rc=$?
set -e
if [[ "$pre_rc" -ne 0 ]]; then
  python3 - "$OUT_DIR/trigger1_local_activation_api_result.json" "$PRE" <<'PY'
import json, pathlib, sys
try: source=json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))
except Exception: source={}
obj={
  'schema':'CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1',
  'status':'BLOCKED_EXACT_SOURCE_PRECONDITION',
  'source_identity_pre':source,
  'zero_provider_billing':True,
  'external_provider_credentials_read':False,
  'provider_network_calls':0,
  'credit_scope':'NONE'
}
pathlib.Path(sys.argv[1]).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
PY
  exit 4
fi

# Close the lease->source handoff. The canonical claim is revalidated immediately
# before intervention, the pre-source identity is remeasured, and the workflow-bound
# claim SHA plus source HEAD/tree must agree with that same measured checkout.
if [[ "${TRIGGER1_LEASE_ADMITTED:-}" != "true" || \
      -z "${TRIGGER1_TRIGGER_KEY:-}" || \
      -z "${TRIGGER1_CLAIM_SHA256:-}" || \
      -z "${TRIGGER1_SOURCE_HEAD:-}" || \
      -z "${TRIGGER1_SOURCE_TREE:-}" ]]; then
  python3 - "$OUT_DIR/trigger1_local_activation_api_result.json" "$PRE" <<'PY'
import json, pathlib, sys
try: source=json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))
except Exception: source={}
obj={
  'schema':'CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1',
  'status':'BLOCKED_CANONICAL_ATOMIC_LEASE_ENV_MISSING',
  'source_identity_pre':source,
  'unusual_experiment_executed':False,
  'zero_provider_billing':True,
  'external_provider_credentials_read':False,
  'provider_network_calls':0,
  'credit_scope':'NONE',
  'next_action':'ENTER_THROUGH_CANONICAL_LEASE_ADMITTED_TRIGGER1_EXECUTION_PATH'
}
pathlib.Path(sys.argv[1]).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
PY
  exit 4
fi

set +e
python3 tools/trigger1_lease_source_binding_v1.py \
  --repo "$ROOT" \
  --source-identity "$PRE" \
  --trigger-key "$TRIGGER1_TRIGGER_KEY" \
  --expected-claim-sha256 "$TRIGGER1_CLAIM_SHA256" \
  --expected-source-head "$TRIGGER1_SOURCE_HEAD" \
  --expected-source-tree "$TRIGGER1_SOURCE_TREE" \
  --output "$LEASE_BINDING" >/dev/null
lease_rc=$?
set -e
if [[ "$lease_rc" -ne 0 ]]; then
  python3 - "$OUT_DIR/trigger1_local_activation_api_result.json" "$PRE" "$LEASE_BINDING" <<'PY'
import json, pathlib, sys
def read(path):
    try: return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
    except Exception: return {}
obj={
  'schema':'CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1',
  'status':'BLOCKED_ATOMIC_LEASE_SOURCE_BINDING',
  'source_identity_pre':read(sys.argv[2]),
  'lease_source_binding':read(sys.argv[3]),
  'unusual_experiment_executed':False,
  'zero_provider_billing':True,
  'external_provider_credentials_read':False,
  'provider_network_calls':0,
  'credit_scope':'NONE',
  'next_action':'REPAIR_LEASE_TO_RUNTIME_SOURCE_CHAIN_BEFORE_INTERVENTION'
}
pathlib.Path(sys.argv[1]).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
PY
  exit 4
fi

set +e
bash "$ROOT/tools/trigger1_local_qwen06_intermediate.sh" "$OUT_DIR" >"$OUT_DIR/intermediate_launcher.log" 2>&1
rc=$?
set -e

python3 tools/git_source_identity_v1.py --repo "$ROOT" > "$POST"
source_stable="$(python3 - "$PRE" "$POST" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); q=json.load(open(sys.argv[2]))
print('true' if p.get('source_identity_sha256') == q.get('source_identity_sha256') else 'false')
PY
)"

RESULT="$OUT_DIR/trigger1_intermediate_result.json"
INTERMEDIATE="$OUT_DIR/trigger1_intermediate_candidate.json"
DIRECT="$OUT_DIR/trigger1_direct_steering_candidate.json"
if [[ "$source_stable" != true ]]; then
  rm -f "$INTERMEDIATE" "$DIRECT"
  rc=4
elif [[ "$rc" -eq 0 && -s "$RESULT" && -s "$INTERMEDIATE" ]]; then
  set +e
  python3 tools/trigger1_intermediate_promotion_bridge.py \
    --result "$RESULT" \
    --candidate "$INTERMEDIATE" \
    --output "$DIRECT" >"$OUT_DIR/intermediate_bridge.log" 2>&1
  bridge_rc=$?
  set -e
  if [[ "$bridge_rc" -ne 0 ]]; then
    rm -f "$DIRECT"
    rc=5
  fi
fi

# Preserve the historical filename expected by the retained workflow while binding
# the stronger result to the canonical lease plus exact pre/post repository identity.
python3 - "$RESULT" "$OUT_DIR/trigger1_local_activation_api_result.json" "$PRE" "$POST" "$LEASE_BINDING" "$source_stable" "$rc" <<'PY'
import hashlib,json,pathlib,sys
src,dst,pre,post,lease_binding,stable,rc=sys.argv[1:]
try:
    obj=json.loads(pathlib.Path(src).read_text(encoding='utf-8'))
    if not isinstance(obj,dict): raise ValueError('RESULT_NOT_OBJECT')
except Exception as exc:
    obj={
      'schema':'CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1',
      'status':'BLOCKED_BEFORE_INTERMEDIATE_RESULT',
      'reason':f'{type(exc).__name__}:{str(exc)[:500]}',
      'zero_provider_billing':True,
      'external_provider_credentials_read':False,
      'provider_network_calls':0,
      'credit_scope':'NONE'
    }
for key,path in [
    ('source_identity_pre',pre),
    ('source_identity_post',post),
    ('lease_source_binding',lease_binding),
]:
    try: obj[key]=json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
    except Exception: obj[key]={}
obj['source_identity_stable_across_run']=(stable=='true')
obj['compatibility_entrypoint']='trigger1_local_qwen06_midlayer_causal.sh'
obj['effective_executor']='tools/trigger1_local_qwen06_intermediate_execute.py'
obj['promotion_bridge']='tools/trigger1_intermediate_promotion_bridge.py'
obj['compatibility_process_exit_code']=int(rc)
if stable!='true':
    obj['status']='BLOCKED_EXACT_SOURCE_CHANGED_DURING_RUN'
    obj['credit_scope']='NONE'
if obj.get('lease_source_binding',{}).get('pass') is not True:
    obj['status']='BLOCKED_ATOMIC_LEASE_SOURCE_BINDING'
    obj['credit_scope']='NONE'
obj.pop('result_sha256',None)
raw=json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
obj['result_sha256']=hashlib.sha256(raw).hexdigest()
pathlib.Path(dst).write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
PY

exit "$rc"
