#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import json, os, platform, sqlite3, sys
print(json.dumps({
    'runner_name': os.environ.get('RUNNER_NAME'),
    'runner_os': os.environ.get('RUNNER_OS'),
    'runner_arch': os.environ.get('RUNNER_ARCH'),
    'platform': platform.platform(),
    'python': sys.version,
    'sqlite': sqlite3.sqlite_version,
    'github_sha': os.environ.get('GITHUB_SHA'),
    'github_run_id': os.environ.get('GITHUB_RUN_ID'),
}, indent=2))
PY

python3 -m py_compile \
  research_entity/runtime/eap_query_aware_gate_v17.py \
  research_entity/runtime/database_pulse_rank_path_v6.py \
  tools/eap_query_aware_gate_v17_benchmark.py

python3 -m unittest -v research_entity.runtime.test_eap_query_aware_gate_v17
python3 -m unittest -v research_entity.runtime.test_database_pulse_rank_path_v6

mkdir -p research_entity/benchmarks/database_pulse
out="research_entity/benchmarks/database_pulse/eap_query_aware_gate_v17_${RUNNER_NAME:-linux}.json"
python3 tools/eap_query_aware_gate_v17_benchmark.py --cases 64 --repeats 7 --output "$out"

python3 - <<'PY'
from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.database_pulse_rank_path_v6 import AdaptiveAuthoritativeRankPathV6
ledger = StateLedger()
path = AdaptiveAuthoritativeRankPathV6(ledger)
assert ledger.conn.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
assert ledger.conn.execute('PRAGMA foreign_key_check').fetchall() == []
assert path.maintenance_receipts_v6() == []
print('quick_check=ok foreign_key_check=0 v6_receipts=0')
PY

printf 'probe_output=%s\n' "$out"
