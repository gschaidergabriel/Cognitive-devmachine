from __future__ import annotations

import argparse
import json
import os
import platform
import random
import sqlite3
import statistics
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.binary_entity_temporal_pulse_v2 import BinaryEntityTemporalStore
from research_entity.runtime.database_pulse_temporal_identity_v1 import TemporalPulseBinder
from research_entity.runtime.gwt_split_pulse_twin_workspace_v1 import benchmark as twin_gwt_benchmark
from research_entity.runtime.gwt_chrono_bridge_counterfactual_v1 import benchmark as chrono_gwt_benchmark


def q95(xs):
    return sorted(xs)[int(0.95 * (len(xs) - 1))]


def copy_benchmark(n: int):
    con = sqlite3.connect(':memory:', isolation_level=None)
    con.row_factory = sqlite3.Row
    store = BinaryEntityTemporalStore(con)
    digest = 'd' * 64
    store.admit_artifact(digest, 'bench', now_ns=1)
    root = store.mint_root(artifact_digest=digest, state_lineage_hash='s', now_ns=2)
    v2 = []
    for i in range(n):
        t = time.perf_counter_ns()
        store.copy_entity(root['entity_id'], state_lineage_hash=str(i), now_ns=3)
        v2.append((time.perf_counter_ns() - t) / 1e6)

    naive = sqlite3.connect(':memory:')
    naive.executescript(
        'create table e(id integer primary key); '
        'create table peer(a int,b int,primary key(a,b)); insert into e values(0);'
    )
    old = [0]
    nv = []
    for i in range(1, n + 1):
        t = time.perf_counter_ns()
        naive.execute('begin immediate')
        naive.execute('insert into e values(?)', (i,))
        naive.executemany('insert into peer values(?,?)', [(i, x) for x in old])
        naive.executemany('insert into peer values(?,?)', [(x, i) for x in old])
        naive.commit()
        old.append(i)
        nv.append((time.perf_counter_ns() - t) / 1e6)
    return {
        'copies': n,
        'lineage_o1_median_ms': statistics.median(v2),
        'lineage_o1_p95_ms': q95(v2),
        'naive_peer_matrix_median_ms': statistics.median(nv),
        'naive_peer_matrix_p95_ms': q95(nv),
        'median_ratio_naive_over_lineage': statistics.median(nv) / statistics.median(v2),
        'lineage_rows': con.execute('select count(*) from binary_entities').fetchone()[0]
        + con.execute('select count(*) from entity_copy_edges').fetchone()[0],
        'naive_rows': naive.execute('select count(*) from e').fetchone()[0]
        + naive.execute('select count(*) from peer').fetchone()[0],
    }


def fuzz(seed_count: int, copies: int, attempts: int):
    for seed in range(seed_count):
        rnd = random.Random(seed)
        ledger = StateLedger(':memory:')
        binder = TemporalPulseBinder(ledger)
        store = binder.store
        digest = ('%064x' % (seed + 1))[-64:]
        store.admit_artifact(digest, 'fuzz', now_ns=1)
        root = store.mint_root(artifact_digest=digest, state_lineage_hash='s0', now_ns=2)
        entities = [root]
        for i in range(copies):
            parent = rnd.choice(entities)
            entities.append(store.copy_entity(parent['entity_id'], state_lineage_hash=f's{i}', now_ns=3))
        assert len({x['entity_id'] for x in entities}) == len(entities)
        assert len({x['entity_version'] for x in entities}) == len(entities)
        eid = rnd.choice(entities)['entity_id']
        lease = 'L0'; boot = 'B1'; invocation = 'I1'
        store.claim_runtime(eid, lease_id=lease, host_id='h', boot_id=boot, invocation_id=invocation, now_ns=4)
        utc = bt = mono = 1_000_000_000
        committed = 0
        for j in range(attempts):
            step = rnd.randint(1, 8) * 1_000_000_000
            utc += step; bt += step; mono += step
            pid = f'fuzz-{seed}-{j}'
            binder.prepare(
                entity_id=eid, pulse_id=pid, basis_epoch=ledger.epoch, lease_id=lease,
                interval_ns=1_000_000_000, utc_ns=utc, boottime_ns=bt, monotonic_ns=mono,
                boot_id=boot, invocation_id=invocation,
            )
            if rnd.random() < 0.08:
                old = lease; lease = f'R{seed}-{j}'; invocation = f'IR{j}'
                store.claim_runtime(
                    eid, lease_id=lease, host_id='h', boot_id=boot, invocation_id=invocation,
                    expected_previous_lease_id=old, allow_supersede=True, now_ns=utc,
                )
                assert binder.recover_stale_prepared(eid, current_lease_id=lease) == 1
                continue
            ledger.append_event(
                event_id=f'database-pulse:{pid}', idem=f'database-pulse:{pid}',
                base_epoch=ledger.epoch, event_type='DATABASE_PULSE', writer='fuzz',
                ops=[{'op':'SET','domain':'pulse','key':'fuzz_latest','value':{'pulse_id':pid},'epistemic':'KNOWN','status':'CURRENT'}],
                provenance={'fuzz':seed}, source={'fuzz':seed}, execution={'effect':'NONE'},
            )
            committed += 1
        assert ledger.conn.execute('select count(*) from entity_pulses where entity_id=?', (eid,)).fetchone()[0] == committed
        assert ledger.conn.execute('select count(*) from pulse_temporal_links').fetchone()[0] == committed
        assert ledger.conn.execute("select count(*) from pulse_temporal_prepare where status='COMMITTED'").fetchone()[0] == committed
        ledger.close()
    return {'seeds': seed_count, 'copies_per_seed': copies, 'pulse_attempts_per_seed': attempts, 'status': 'PASS'}


def mcp_probe():
    result = {
        'health_url': 'http://127.0.0.1:8765/healthz',
        'status': 'UNOBSERVED',
        'release_current_exists': Path('/opt/clay-vps-mcp/current').exists(),
        'telemetry_dir_exists': Path('/srv/frank-telemetry').exists(),
        'history_dir_exists': Path('/srv/clay-history').exists(),
    }
    try:
        with urllib.request.urlopen(result['health_url'], timeout=3) as response:
            result['status'] = 'HEALTHY' if response.status == 200 else f'HTTP_{response.status}'
            result['body'] = response.read(4096).decode('utf-8', errors='replace')
    except Exception as exc:
        result['status'] = 'UNREACHABLE'
        result['error_class'] = type(exc).__name__
    return result


def environment():
    boot_id = 'UNKNOWN'
    try:
        boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    except Exception:
        pass
    return {
        'hostname': platform.node(),
        'platform': platform.platform(),
        'python': platform.python_version(),
        'sqlite': sqlite3.sqlite_version,
        'cpu_count': os.cpu_count(),
        'boot_id': boot_id,
        'has_clock_boottime': hasattr(time, 'CLOCK_BOOTTIME'),
        'runner_name': os.getenv('RUNNER_NAME', 'UNKNOWN'),
        'runner_os': os.getenv('RUNNER_OS', 'UNKNOWN'),
        'runner_arch': os.getenv('RUNNER_ARCH', 'UNKNOWN'),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--copies', type=int, default=500)
    p.add_argument('--episodes', type=int, default=20_000)
    p.add_argument('--chrono-episodes', type=int, default=2_000)
    p.add_argument('--fuzz-seeds', type=int, default=30)
    p.add_argument('--fuzz-copies', type=int, default=60)
    p.add_argument('--fuzz-attempts', type=int, default=30)
    p.add_argument('--probe-mcp', action='store_true')
    p.add_argument('--output', required=True)
    a = p.parse_args()
    out = {
        'schema_version': '1.1',
        'evidence_class': 'EXECUTED_RUNTIME_PROBE',
        'environment': environment(),
        'copy_storage_benchmark': copy_benchmark(a.copies),
        'randomized_falsifier': fuzz(a.fuzz_seeds, a.fuzz_copies, a.fuzz_attempts),
        'crazy_gwt_challenger': twin_gwt_benchmark(a.episodes),
        'crazy_gwt_challenger_iteration_2': chrono_gwt_benchmark(a.chrono_episodes),
        'mcp': mcp_probe() if a.probe_mcp else {'status': 'NOT_REQUESTED'},
        'epistemic_boundaries': {
            'missed_slots_are_phantom_pulses': False,
            'entity_continuity_implies_compute_continuity': False,
            'twin_gwt_promoted': False,
            'counterfactual_missed_pulse_simulation_promoted': False,
        },
    }
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    Path(a.output).write_text(json.dumps(out, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
