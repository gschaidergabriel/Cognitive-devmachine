#!/usr/bin/env bash
set -euo pipefail

# Serial, read-only v3 gate: exact authority first, visual A/B second, then
# re-hash the same four live subjects. No live source or asset write occurs.
ROOT="${1:-/home/ai-core-node/.claude/star/visual}"
OUT="${2:-/tmp/frank-expression-eye-ab-v3}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTH="$HERE/expression_eye_authority_gate_v3.py"
AB="$HERE/expression_eye_ab_harness.py"

[[ -f "$AUTH" && -f "$AB" ]]
[[ ! -e "$OUT" ]]
mkdir -p "$OUT"

snapshot() {
  sha256sum \
    "$ROOT/buehne.html" \
    "$ROOT/buehne_daemon.py" \
    "$ROOT/augen_blink_relief2/blink_000.png" \
    "$ROOT/augen_gaze_relief2/rotglow_tracking_master.png"
}

snapshot > "$OUT/subject.before.sha256"
python3 "$AUTH" --visual-root "$ROOT" --out "$OUT/authority.json"
python3 "$AB" --visual-root "$ROOT" --out "$OUT/ab"
snapshot > "$OUT/subject.after.sha256"
cmp -s "$OUT/subject.before.sha256" "$OUT/subject.after.sha256" || {
  echo "FAIL subject drift between authority and A/B stages" >&2
  diff -u "$OUT/subject.before.sha256" "$OUT/subject.after.sha256" >&2 || true
  exit 41
}

python3 - "$OUT" <<'PY'
import hashlib, json, sys
from pathlib import Path
out=Path(sys.argv[1])
a=json.loads((out/'authority.json').read_text())
b=json.loads((out/'ab'/'report.json').read_text())
assert a['status']=='PASS'
assert a['source_mutation'] is False
assert b['source_mutation'] is False
assert b['native_to_canonical_eye']['diff_pixels'] > 0
assert b['canonical_eye_to_gaze']['diff_pixels'] > 0
report={
  'schema':'FRANK_AVATAR_EXPRESSION_EYE_AB_SERIAL_V3/v1',
  'status':'PASS',
  'authority_gate':'PASS',
  'visual_ab':'PASS',
  'subject_drift':False,
  'authority_report_sha256':hashlib.sha256((out/'authority.json').read_bytes()).hexdigest(),
  'ab_report_sha256':hashlib.sha256((out/'ab'/'report.json').read_bytes()).hexdigest(),
}
(out/'SERIAL_RESULT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps(report,sort_keys=True))
PY

echo "EXPRESSION_EYE_AB_SERIAL_V3=PASS"
