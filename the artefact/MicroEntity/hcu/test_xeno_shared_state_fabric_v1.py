import hashlib
import unittest
from dataclasses import replace

from xeno_shared_state_fabric_v1 import (
    COORDINATOR_LEASE_SCHEMA,
    NODE_RESULT_SCHEMA,
    AutonomousBoot,
    CoordinatorCandidate,
    SharedStateFabricError,
    admit_s1_snapshot,
    autonomous_boot,
    build_s1_snapshot,
    commit_s1_delta,
    derive_node_binding_sha256,
    issue_coordinator_lease,
    make_node_result,
    snapshot_to_wire,
)

H = lambda text: hashlib.sha256(text.encode('utf-8')).hexdigest()
AUTH = H('canonical-s0-lease-authority')
POLICY = 'owner-xeno-hcu-2026-08-25/v1'
FABRIC = 'entityos-hcu-s1-main'
GEN = 7


def base_state():
    return {
        'active_nodes': [
            {'node_id': 'xeno-a', 'capabilities': ['analysis', 'code']},
            {'node_id': 'xeno-b', 'capabilities': ['analysis', 'code']},
            {'node_id': 'xeno-c', 'capabilities': ['analysis']},
        ],
        'work_items': [
            {'task_id': 'task-1', 'scope': 'grid.alpha', 'status': 'OPEN',
             'required_capabilities': ['analysis'], 'claimed_by': None},
            {'task_id': 'task-2', 'scope': 'grid.alpha', 'status': 'OPEN',
             'required_capabilities': ['analysis', 'code'], 'claimed_by': None},
            {'task_id': 'task-3', 'scope': 'grid.alpha', 'status': 'IN_FLIGHT',
             'required_capabilities': ['analysis'], 'claimed_by': 'xeno-c'},
        ],
        'broadcast': {'gwt_epoch': 9, 'topic': 'owner-shortest-path'},
        'hyperposition': {'branches': ['h1', 'h2'], 'collapsed': False},
    }


def snapshot(epoch=11, state=None):
    return build_s1_snapshot(
        fabric_id=FABRIC,
        entity_generation=GEN,
        epoch=epoch,
        policy_version=POLICY,
        state=base_state() if state is None else state,
    )


def binding(node_id, caps):
    return derive_node_binding_sha256(
        node_id=node_id,
        capabilities=caps,
        entity_generation=GEN,
        policy_version=POLICY,
    )


def boot_for(node_id, caps):
    s = snapshot()
    return s, autonomous_boot(
        snapshot=s,
        node_id=node_id,
        capabilities=caps,
        expected_node_binding_sha256=binding(node_id, caps),
    )


def result_for_boot(boot: AutonomousBoot, payload='result'):
    if boot.selected_task_id is None:
        raise AssertionError('test node did not receive work')
    return make_node_result(
        boot=boot,
        task_id=boot.selected_task_id,
        scope=boot.selected_scope,
        result_kind='ANALYSIS_CANDIDATE',
        payload_ref=f'cas://{H(payload)}',
        payload_sha256=H(payload),
        trace_bindings={
            'inference_receipt_sha256': H('inference'),
            'gwt_trace_sha256': H('gwt'),
            'jspace_trace_sha256': H('jspace'),
            'hyperposition_trace_sha256': H('hyperposition'),
        },
    )


class SharedStateFabricV1Tests(unittest.TestCase):
    def test_snapshot_admission_roundtrip_and_digest_poison(self):
        s = snapshot()
        admitted = admit_s1_snapshot(
            snapshot_to_wire(s),
            current_generation=GEN,
            expected_fabric_id=FABRIC,
            expected_policy_version=POLICY,
        )
        self.assertEqual(admitted.digest_sha256, s.digest_sha256)
        poisoned = snapshot_to_wire(s)
        poisoned['state']['broadcast']['topic'] = 'mutated-after-digest'
        with self.assertRaisesRegex(SharedStateFabricError, 'S1_DIGEST_MISMATCH'):
            admit_s1_snapshot(
                poisoned,
                current_generation=GEN,
                expected_fabric_id=FABRIC,
                expected_policy_version=POLICY,
            )

    def test_snapshot_stale_generation_and_policy_fail_closed(self):
        s = snapshot()
        with self.assertRaisesRegex(SharedStateFabricError, 'STALE_ENTITY_GENERATION'):
            admit_s1_snapshot(snapshot_to_wire(s), current_generation=GEN + 1,
                              expected_fabric_id=FABRIC, expected_policy_version=POLICY)
        with self.assertRaisesRegex(SharedStateFabricError, 'S1_POLICY_VERSION_MISMATCH'):
            admit_s1_snapshot(snapshot_to_wire(s), current_generation=GEN,
                              expected_fabric_id=FABRIC, expected_policy_version='other')

    def test_autonomous_boot_default_role_and_identity_binding(self):
        s, boot = boot_for('xeno-a', ['analysis', 'code'])
        self.assertEqual(boot.runtime_role, 'ORDINARY')
        self.assertEqual(boot.snapshot_digest_sha256, s.digest_sha256)
        self.assertIn(boot.selected_task_id, {'task-1', 'task-2', None})
        with self.assertRaisesRegex(SharedStateFabricError, 'NODE_IDENTITY_BINDING_MISMATCH'):
            autonomous_boot(snapshot=s, node_id='xeno-a', capabilities=['analysis', 'code'],
                            expected_node_binding_sha256=H('forged-binding'))

    def test_rendezvous_work_selection_avoids_duplicate_open_task_ownership(self):
        s = snapshot()
        boots = {
            node: autonomous_boot(snapshot=s, node_id=node, capabilities=caps,
                                  expected_node_binding_sha256=binding(node, caps))
            for node, caps in [
                ('xeno-a', ['analysis', 'code']),
                ('xeno-b', ['analysis', 'code']),
                ('xeno-c', ['analysis']),
            ]
        }
        selected = [b.selected_task_id for b in boots.values() if b.selected_task_id]
        self.assertEqual(len(selected), len(set(selected)))
        self.assertNotIn('task-3', selected)

    def test_node_result_is_typed_epoch_bound_and_trace_bound(self):
        _, boot = boot_for('xeno-a', ['analysis', 'code'])
        if boot.selected_task_id is None:
            _, boot = boot_for('xeno-b', ['analysis', 'code'])
        result = result_for_boot(boot)
        self.assertEqual(result.schema, NODE_RESULT_SCHEMA)
        self.assertEqual(result.snapshot_epoch, boot.snapshot_epoch)
        self.assertEqual(result.snapshot_digest_sha256, boot.snapshot_digest_sha256)
        self.assertEqual(dict(result.trace_bindings)['jspace_trace_sha256'], H('jspace'))

    def test_node_result_cannot_switch_to_unselected_task(self):
        s, boot = boot_for('xeno-a', ['analysis', 'code'])
        if boot.selected_task_id is None:
            boot = autonomous_boot(snapshot=s, node_id='xeno-b', capabilities=['analysis', 'code'],
                                   expected_node_binding_sha256=binding('xeno-b', ['analysis', 'code']))
        other = 'task-2' if boot.selected_task_id == 'task-1' else 'task-1'
        with self.assertRaisesRegex(SharedStateFabricError, 'NODE_RESULT_TASK_NOT_SELECTED'):
            make_node_result(boot=boot, task_id=other, scope='grid.alpha', result_kind='X',
                             payload_ref='cas://x', payload_sha256=H('x'))

    def test_ordinary_node_has_no_s1_write_without_lease(self):
        s, boot = boot_for('xeno-a', ['analysis', 'code'])
        with self.assertRaisesRegex(SharedStateFabricError, 'NO_VALID_COORDINATOR_LEASE_NO_S1_WRITE'):
            commit_s1_delta(snapshot=s, caller_node_id=boot.node_id, lease=None,
                            expected_lease_authority_binding_sha256=AUTH,
                            node_results=[], next_state=base_state())

    def test_deterministic_lease_and_coordinator_commit(self):
        s = snapshot()
        candidates = [
            CoordinatorCandidate('xeno-a', binding('xeno-a', ['analysis', 'code']), load=2),
            CoordinatorCandidate('xeno-b', binding('xeno-b', ['analysis', 'code']), load=0),
        ]
        lease1 = issue_coordinator_lease(snapshot=s, scope='grid.alpha', candidates=candidates,
                                         lease_authority_binding_sha256=AUTH)
        lease2 = issue_coordinator_lease(snapshot=s, scope='grid.alpha', candidates=list(reversed(candidates)),
                                         lease_authority_binding_sha256=AUTH)
        self.assertEqual(lease1.schema, COORDINATOR_LEASE_SCHEMA)
        self.assertEqual(lease1.lease_sha256, lease2.lease_sha256)
        self.assertEqual(lease1.holder_node_id, 'xeno-b')

        boots = []
        for node, caps in [('xeno-a', ['analysis', 'code']), ('xeno-b', ['analysis', 'code']), ('xeno-c', ['analysis'])]:
            b = autonomous_boot(snapshot=s, node_id=node, capabilities=caps,
                                expected_node_binding_sha256=binding(node, caps))
            if b.selected_task_id and b.selected_scope == 'grid.alpha':
                boots.append(b)
        results = [result_for_boot(b, f'result-{b.node_id}') for b in boots]
        nxt = base_state()
        nxt['broadcast']['gwt_epoch'] = 10
        commit = commit_s1_delta(snapshot=s, caller_node_id='xeno-b', lease=lease1,
                                 expected_lease_authority_binding_sha256=AUTH,
                                 node_results=results, next_state=nxt)
        self.assertEqual(commit.new_snapshot.epoch, s.epoch + 1)
        self.assertNotEqual(commit.new_snapshot.digest_sha256, s.digest_sha256)
        self.assertEqual(commit.previous_digest_sha256, s.digest_sha256)

    def test_forged_authority_and_wrong_holder_fail_closed(self):
        s = snapshot()
        lease = issue_coordinator_lease(
            snapshot=s, scope='grid.alpha',
            candidates=[CoordinatorCandidate('xeno-a', binding('xeno-a', ['analysis', 'code']), load=0)],
            lease_authority_binding_sha256=AUTH,
        )
        with self.assertRaisesRegex(SharedStateFabricError, 'COORDINATOR_LEASE_AUTHORITY_MISMATCH'):
            commit_s1_delta(snapshot=s, caller_node_id='xeno-a', lease=lease,
                            expected_lease_authority_binding_sha256=H('wrong-authority'),
                            node_results=[], next_state=base_state())
        with self.assertRaisesRegex(SharedStateFabricError, 'COORDINATOR_LEASE_NOT_HELD_BY_CALLER'):
            commit_s1_delta(snapshot=s, caller_node_id='xeno-b', lease=lease,
                            expected_lease_authority_binding_sha256=AUTH,
                            node_results=[], next_state=base_state())

    def test_stale_lease_rejected_after_epoch_advance(self):
        s = snapshot()
        lease = issue_coordinator_lease(
            snapshot=s, scope='grid.alpha',
            candidates=[CoordinatorCandidate('xeno-b', binding('xeno-b', ['analysis', 'code']), load=0)],
            lease_authority_binding_sha256=AUTH,
        )
        commit = commit_s1_delta(snapshot=s, caller_node_id='xeno-b', lease=lease,
                                 expected_lease_authority_binding_sha256=AUTH,
                                 node_results=[], next_state=base_state())
        with self.assertRaisesRegex(SharedStateFabricError, 'STALE_OR_NOT_YET_VALID_COORDINATOR_LEASE'):
            commit_s1_delta(snapshot=commit.new_snapshot, caller_node_id='xeno-b', lease=lease,
                            expected_lease_authority_binding_sha256=AUTH,
                            node_results=[], next_state=base_state())

    def test_duplicate_node_result_rejected(self):
        s = snapshot()
        boots = []
        for node, caps in [('xeno-a', ['analysis', 'code']), ('xeno-b', ['analysis', 'code']), ('xeno-c', ['analysis'])]:
            b = autonomous_boot(snapshot=s, node_id=node, capabilities=caps,
                                expected_node_binding_sha256=binding(node, caps))
            if b.selected_task_id:
                boots.append(b)
        self.assertTrue(boots)
        result = result_for_boot(boots[0])
        lease = issue_coordinator_lease(
            snapshot=s, scope=result.scope,
            candidates=[CoordinatorCandidate('xeno-b', binding('xeno-b', ['analysis', 'code']), load=0)],
            lease_authority_binding_sha256=AUTH,
        )
        if lease.holder_node_id != 'xeno-b':
            self.fail('unexpected holder')
        with self.assertRaisesRegex(SharedStateFabricError, 'DUPLICATE_NODE_RESULT'):
            commit_s1_delta(snapshot=s, caller_node_id='xeno-b', lease=lease,
                            expected_lease_authority_binding_sha256=AUTH,
                            node_results=[result, result], next_state=base_state())

    def test_stale_node_result_rejected(self):
        s = snapshot()
        boots = []
        for node, caps in [('xeno-a', ['analysis', 'code']), ('xeno-b', ['analysis', 'code']), ('xeno-c', ['analysis'])]:
            b = autonomous_boot(snapshot=s, node_id=node, capabilities=caps,
                                expected_node_binding_sha256=binding(node, caps))
            if b.selected_task_id:
                boots.append(b)
        result = result_for_boot(boots[0])
        lease = issue_coordinator_lease(
            snapshot=s, scope=result.scope,
            candidates=[CoordinatorCandidate('xeno-b', binding('xeno-b', ['analysis', 'code']), load=0)],
            lease_authority_binding_sha256=AUTH,
        )
        forged = replace(result, snapshot_epoch=result.snapshot_epoch - 1)
        with self.assertRaisesRegex(SharedStateFabricError, 'NODE_RESULT_DIGEST_MISMATCH'):
            commit_s1_delta(snapshot=s, caller_node_id='xeno-b', lease=lease,
                            expected_lease_authority_binding_sha256=AUTH,
                            node_results=[forged], next_state=base_state())

    def test_tampered_node_result_payload_fails_digest_revalidation(self):
        s = snapshot()
        boots = []
        for node, caps in [('xeno-a', ['analysis', 'code']), ('xeno-b', ['analysis', 'code']), ('xeno-c', ['analysis'])]:
            b = autonomous_boot(snapshot=s, node_id=node, capabilities=caps,
                                expected_node_binding_sha256=binding(node, caps))
            if b.selected_task_id:
                boots.append(b)
        result = result_for_boot(boots[0])
        lease = issue_coordinator_lease(
            snapshot=s, scope=result.scope,
            candidates=[CoordinatorCandidate('xeno-b', binding('xeno-b', ['analysis', 'code']), load=0)],
            lease_authority_binding_sha256=AUTH,
        )
        tampered = replace(result, payload_sha256=H('tampered'))
        with self.assertRaisesRegex(SharedStateFabricError, 'NODE_RESULT_DIGEST_MISMATCH'):
            commit_s1_delta(snapshot=s, caller_node_id='xeno-b', lease=lease,
                            expected_lease_authority_binding_sha256=AUTH,
                            node_results=[tampered], next_state=base_state())

    def test_tampered_lease_fails_digest_revalidation(self):
        s = snapshot()
        lease = issue_coordinator_lease(
            snapshot=s, scope='grid.alpha',
            candidates=[CoordinatorCandidate('xeno-b', binding('xeno-b', ['analysis', 'code']), load=0)],
            lease_authority_binding_sha256=AUTH,
        )
        tampered = replace(lease, holder_node_id='xeno-a')
        with self.assertRaisesRegex(SharedStateFabricError, 'COORDINATOR_LEASE_DIGEST_MISMATCH'):
            commit_s1_delta(snapshot=s, caller_node_id='xeno-a', lease=tampered,
                            expected_lease_authority_binding_sha256=AUTH,
                            node_results=[], next_state=base_state())

    def test_coordinator_cannot_self_grant_active_node_or_capabilities(self):
        s = snapshot()
        lease = issue_coordinator_lease(
            snapshot=s, scope='grid.alpha',
            candidates=[CoordinatorCandidate('xeno-b', binding('xeno-b', ['analysis', 'code']), load=0)],
            lease_authority_binding_sha256=AUTH,
        )
        nxt = base_state()
        nxt['active_nodes'].append({'node_id': 'rogue', 'capabilities': ['all']})
        with self.assertRaisesRegex(SharedStateFabricError, 'COORDINATOR_MAY_NOT_MUTATE_ACTIVE_NODE_AUTHORITY_VIEW'):
            commit_s1_delta(snapshot=s, caller_node_id='xeno-b', lease=lease,
                            expected_lease_authority_binding_sha256=AUTH,
                            node_results=[], next_state=nxt)

    def test_multi_epoch_lease_is_rejected_to_preserve_digest_binding(self):
        s = snapshot()
        with self.assertRaisesRegex(SharedStateFabricError, 'MUST_EQUAL_ONE_FOR_DIGEST_BOUND_LEASE'):
            issue_coordinator_lease(
                snapshot=s, scope='grid.alpha',
                candidates=[CoordinatorCandidate('xeno-b', binding('xeno-b', ['analysis', 'code']), load=0)],
                lease_authority_binding_sha256=AUTH, valid_epoch_span=2,
            )

    def test_input_state_is_detached_from_snapshot(self):
        state = base_state()
        s = snapshot(state=state)
        original_digest = s.digest_sha256
        state['broadcast']['topic'] = 'caller-mutated'
        self.assertEqual(s.digest_sha256, original_digest)
        self.assertEqual(s.state['broadcast']['topic'], 'owner-shortest-path')


if __name__ == '__main__':
    unittest.main()
