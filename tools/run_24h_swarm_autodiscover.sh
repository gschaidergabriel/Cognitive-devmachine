#!/usr/bin/env bash
set -Eeuo pipefail

# Autonomous FREE_ONLY EntityOS/HCU swarm launcher for the VPS sandbox.
# Uses the existing rate-aware tools/run_free_go_swarm.py controller.
# 429 responses remain provider-wide cooldowns; extra API keys are never used
# to bypass a provider/project/organization rate limit.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

: "${CLAY_FREE_ONLY_ATTESTED:?CLAY_FREE_ONLY_ATTESTED=1 must already be set for verified free/included-only credentials}"

MIN_FREE_GB="${CLAY_SWARM_MIN_FREE_GB:-25}"
FREE_GB="$(df -BG --output=avail /artifacts 2>/dev/null | tail -1 | tr -dc '0-9')"
if [[ -n "$FREE_GB" && "$FREE_GB" -lt "$MIN_FREE_GB" ]]; then
  echo "REFUSE_LOW_DISK free_gb=$FREE_GB required_gb=$MIN_FREE_GB" >&2
  exit 20
fi

select_models() {
  local provider="$1" url="$2" key="${3:-}"
  [[ -n "$key" ]] || return 0
  curl -fsS --max-time 30 -H "Authorization: Bearer $key" "$url" \
    | python3 - "$provider" <<'PY'
import json,re,sys
provider=sys.argv[1]
try:
    payload=json.load(sys.stdin)
except Exception:
    raise SystemExit(0)
rows=payload.get('data',[]) if isinstance(payload,dict) else []
exclude=('embedding','embed-','rerank','whisper','speech','audio','tts','guard','safety','moderation','classifier','reward','diffusion')
unknown_keep=('mistral-large','mistral-medium','mistral-small','magistral','codestral','devstral','nemotron','deepseek','reasoning','instruct','coder')
out=[]
for row in rows:
    if not isinstance(row,dict):
        row={'id':str(row)}
    mid=str(row.get('id') or row.get('model') or '').strip()
    low=mid.lower()
    if not mid or any(x in low for x in exclude):
        continue
    caps=row.get('capabilities')
    if isinstance(caps,dict) and caps.get('completion_chat') is False:
        continue
    vals=[]
    for x in re.findall(r'(?i)(\d+(?:\.\d+)?)\s*b(?:\b|[-_])',mid):
        try: vals.append(float(x))
        except ValueError: pass
    b=max(vals) if vals else None
    # Explicit model sizes below 12B are skipped; unknown-size flagship,
    # reasoning and coding families are retained and empirically tested.
    if b is not None and b < 12:
        continue
    if b is None and not any(x in low for x in unknown_keep):
        continue
    score=(b or 0)
    if any(x in low for x in ('ultra','large','reasoning','deepseek','120b','405b','550b')): score+=120
    if any(x in low for x in ('nemotron','magistral','devstral','codestral','coder','instruct')): score+=60
    out.append((score,mid))
out=sorted(set(out),key=lambda x:(-x[0],x[1]))
print(','.join(mid for _,mid in out))
PY
}

# Live model catalog discovery. Environment overrides remain authoritative.
if [[ -z "${GROQ_SWARM_MODELS:-}" && -n "${GROQ_API_KEY:-}" ]]; then
  GROQ_SWARM_MODELS="$(select_models groq https://api.groq.com/openai/v1/models "$GROQ_API_KEY" || true)"
  export GROQ_SWARM_MODELS
fi
if [[ -z "${MISTRAL_SWARM_MODELS:-}" && -n "${MISTRAL_API_KEY:-}" ]]; then
  MISTRAL_SWARM_MODELS="$(select_models mistral https://api.mistral.ai/v1/models "$MISTRAL_API_KEY" || true)"
  export MISTRAL_SWARM_MODELS
fi
if [[ -z "${NVIDIA_SWARM_MODELS:-}" && -n "${NVIDIA_API_KEY:-${NGC_API_KEY:-}}" ]]; then
  NVIDIA_PRIMARY_KEY="${NVIDIA_API_KEY:-${NGC_API_KEY:-}}"
  NVIDIA_SWARM_MODELS="$(select_models nvidia https://integrate.api.nvidia.com/v1/models "$NVIDIA_PRIMARY_KEY" || true)"
  export NVIDIA_SWARM_MODELS
fi

# Caps are ceilings only. run_free_go_swarm.py uses adaptive concurrency and
# halves it on 429, then applies provider-wide cooldown using Retry-After.
export CLAY_GROQ_MAX_CONCURRENCY="${CLAY_GROQ_MAX_CONCURRENCY:-12}"
export CLAY_MISTRAL_MAX_CONCURRENCY="${CLAY_MISTRAL_MAX_CONCURRENCY:-8}"
export CLAY_NVIDIA_MAX_CONCURRENCY="${CLAY_NVIDIA_MAX_CONCURRENCY:-16}"

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${CLAY_SWARM_OUTPUT_DIR:-/artifacts/clay-free-go-swarm/$RUN_ID}"
mkdir -p "$OUT"

python3 tools/run_free_go_swarm.py \
  --hours "${CLAY_SWARM_HOURS:-24}" \
  --max-tokens "${CLAY_SWARM_MAX_TOKENS:-1800}" \
  --context-chars "${CLAY_SWARM_CONTEXT_CHARS:-22000}" \
  --timeout "${CLAY_SWARM_TIMEOUT:-180}" \
  --output-dir "$OUT"
