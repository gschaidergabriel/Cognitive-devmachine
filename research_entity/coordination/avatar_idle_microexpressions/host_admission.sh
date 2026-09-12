#!/usr/bin/env bash
set -euo pipefail

LIVE=/home/ai-core-node/.claude/star/visual/buehne.html
EXPECTED_SHA=18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e

fail(){ echo "ADMISSION_FAIL $*" >&2; exit 75; }

[[ "$(hostname)" == ai-core-node* ]] || fail "wrong_host=$(hostname)"
[[ -f "$LIVE" ]] || fail "live_source_missing"
[[ "$(sha256sum "$LIVE" | awk '{print $1}')" == "$EXPECTED_SHA" ]] || fail "live_sha_drift"
[[ "$(systemctl --user is-active frankenstein-buehne.service || true)" == active ]] || fail "avatar_service_not_active"
[[ "$(systemctl --user is-active frankenstein-koerperpflege.service || true)" == active ]] || fail "koerperpflege_not_active"

# FranKenstein's own body monitor outranks generic load heuristics.
RECENT_HEALTH="$(journalctl --user -u frankenstein-koerperpflege.service --since '-150 seconds' --no-pager -o cat 2>/dev/null || true)"
[[ -n "$RECENT_HEALTH" ]] || fail "koerperpflege_recent_state_unknown"
if grep -q 'Stufe kritisch' <<<"$RECENT_HEALTH"; then
  fail "koerperpflege_critical"
fi

CPU_ONLINE=$(getconf _NPROCESSORS_ONLN)
read -r LOAD1 LOAD5 LOAD15 _ </proc/loadavg
MEM_AVAILABLE_KB=$(awk '/MemAvailable:/{print $2}' /proc/meminfo)
[[ "$CPU_ONLINE" =~ ^[0-9]+$ ]] || fail "cpu_count_unknown"
[[ "$MEM_AVAILABLE_KB" =~ ^[0-9]+$ ]] || fail "memory_unknown"

if ! python3 - "$CPU_ONLINE" "$LOAD1" "$LOAD5" "$MEM_AVAILABLE_KB" <<'PY'
import sys
n=int(sys.argv[1]); l1=float(sys.argv[2]); l5=float(sys.argv[3]); mem=int(sys.argv[4])
# Require real headroom; mutation itself is tiny, but it must not join an overloaded host.
if l1 > n*0.85: raise SystemExit(75)
if l5 > n*0.95: raise SystemExit(75)
if mem < 4*1024*1024: raise SystemExit(75)
PY
then
  fail "resource_headroom cpu=$CPU_ONLINE load1=$LOAD1 load5=$LOAD5 mem_kb=$MEM_AVAILABLE_KB"
fi

PROD_CHROME_COUNT=$(pgrep -a -f '/opt/google/chrome/chrome --app=http://127.0.0.1:8788/' \
  | grep -v -- '--type=' | grep -v 'bash -lc' | wc -l)
[[ "$PROD_CHROME_COUNT" == 1 ]] || fail "production_chrome_count=$PROD_CHROME_COUNT"

echo "ADMISSION_PASS cpu=$CPU_ONLINE load1=$LOAD1 load5=$LOAD5 mem_kb=$MEM_AVAILABLE_KB prod_chrome=$PROD_CHROME_COUNT live_sha=$EXPECTED_SHA"
