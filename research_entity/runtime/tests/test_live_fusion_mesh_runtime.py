#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import tempfile
from pathlib import Path

RUNTIME = Path(__file__).resolve().parents[1] / 'live_fusion_mesh_runtime.py'
spec = importlib.util.spec_from_file_location('live_fusion_mesh_runtime', RUNTIME)
lf = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(lf)


def test_dual_projection_idempotent_ack_replan_reconcile():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / 'livefusion.sqlite'
        c = lf.open_db(db)
        try:
            first = lf.publish(
                c,
                event_id='evt-1',
                semantic_epoch='18',
                origin_actor='pytest',
                origin_branch='frank',
                ancestry_family='family-1',
                evidence_class='SIMULATION_ONLY',
                impact='HIGH_IMPACT',
                payload={'delta': 'x'},
                claygraph_targets=['frank', 'harness', 'gwt'],
                unifieddb_targets=['frank', 'harness', 'unifieddb'],
            )
            assert first['targets'] == ['frank', 'gwt', 'harness', 'unifieddb']
            assert first['topology_disagreement'] is True

            second = lf.publish(
                c,
                event_id='evt-1',
                semantic_epoch='18',
                origin_actor='pytest',
                origin_branch='frank',
                ancestry_family='family-1',
                evidence_class='SIMULATION_ONLY',
                impact='HIGH_IMPACT',
                payload={'delta': 'x'},
                claygraph_targets=['frank', 'harness', 'gwt'],
                unifieddb_targets=['frank', 'harness', 'unifieddb'],
            )
            assert second['pulse_id'] == first['pulse_id']
            assert c.execute('SELECT COUNT(*) FROM clay_live_fusion_pulses').fetchone()[0] == 1
            assert c.execute('SELECT COUNT(*) FROM clay_live_fusion_targets').fetchone()[0] == 4

            pid = first['pulse_id']
            for receiver in ['frank', 'harness', 'gwt']:
                lf.mark_attempt(c, pid, receiver)
                lf.ack(c, pid, receiver, 'INGESTED', '18')

            receipt_id = lf.replan(
                c,
                pid,
                'frank',
                'REVISE',
                old_refs=['work@1'],
                new_refs=['work@2'],
                invalidator_result={'invalidated': True},
                evidence=['evt-1'],
            )
            assert receipt_id.startswith('replan:')

            repair = lf.reconcile(c, pid, ['frank', 'harness', 'gwt', 'unifieddb', 'claycode'])
            assert set(repair['missing_before']) == {'unifieddb', 'claycode'}
            assert repair['converged'] is False

            for receiver in repair['missing_before']:
                lf.mark_attempt(c, pid, receiver)
                lf.ack(c, pid, receiver, 'INGESTED', '18')

            final = lf.finalize_repair(c, repair['repair_id'])
            assert final['converged'] is True
            assert final['still_missing'] == []

            state = lf.status(c, pid)
            assert len(state['targets']) == 5
            assert len(state['replans']) == 1
        finally:
            c.close()


def test_invalid_ack_and_replan_states_fail_closed():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / 'livefusion.sqlite'
        c = lf.open_db(db)
        try:
            pulse = lf.publish(
                c,
                event_id='evt-2',
                semantic_epoch='18',
                origin_actor='pytest',
                origin_branch='claycode',
                ancestry_family='family-2',
                evidence_class='SIMULATION_ONLY',
                impact='NORMAL',
                payload={},
                claygraph_targets=['claycode'],
                unifieddb_targets=['claycode'],
            )
            pid = pulse['pulse_id']
            try:
                lf.ack(c, pid, 'claycode', 'MAGIC_SUCCESS')
                raise AssertionError('invalid ack state did not fail')
            except ValueError:
                pass
            try:
                lf.replan(c, pid, 'claycode', 'PROMOTE')
                raise AssertionError('invalid replan decision did not fail')
            except ValueError:
                pass
        finally:
            c.close()
