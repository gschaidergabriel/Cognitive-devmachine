import pytest

from clayverse.goals import GoalController, GoalStateError
from clayverse.identity import IdentityRouter
from clayverse.retrieval import WorldAssembler
from clayverse.store import UnifiedDB


@pytest.fixture
def db(tmp_path):
    value = UnifiedDB(tmp_path / 'unified.db')
    IdentityRouter(value, {})
    yield value
    value.close()


def _active_goal(controller, *, risk_class='REVERSIBLE', max_attempts=3):
    goal_id = controller.create_goal(
        'gabriel',
        'Ship bounded feature',
        'Implement and verify one bounded feature without inventing execution evidence.',
        {'all_milestones_verified': True},
        constraints={'no_unverified_success': True},
        priority=80,
    )
    milestone_id = controller.add_milestone(
        'gabriel',
        goal_id,
        'Implement feature',
        'Produce the change and close it only from admitted evidence.',
        max_attempts=max_attempts,
        risk_class=risk_class,
    )
    controller.activate_goal('gabriel', goal_id)
    return goal_id, milestone_id


def test_model_proposal_never_self_certifies_success(db):
    controller = GoalController(db)
    goal_id, milestone_id = _active_goal(controller)
    work = controller.claim_next('worker:test', run_ttl=60)
    assert work is not None and work.goal_id == goal_id and work.milestone_id == milestone_id

    controller.record_model_proposal(
        work.run_id,
        {'claim': 'I ran the tests and everything passed.'},
    )

    run = db.db.execute(
        'SELECT * FROM goal_runs WHERE run_id=?', (work.run_id,)
    ).fetchone()
    milestone = db.db.execute(
        'SELECT * FROM goal_milestones WHERE milestone_id=?', (milestone_id,)
    ).fetchone()
    goal = db.db.execute(
        'SELECT * FROM goals WHERE goal_id=?', (goal_id,)
    ).fetchone()
    assert run['status'] == 'WAITING_EVIDENCE'
    assert milestone['status'] == 'WAITING_EVIDENCE'
    assert goal['status'] == 'ACTIVE'


def test_unverified_or_model_evidence_cannot_close_milestone(db):
    controller = GoalController(db)
    _, milestone_id = _active_goal(controller)
    work = controller.claim_next('worker:test', run_ttl=60)
    controller.record_model_proposal(work.run_id, {'next': 'verify'})

    assert controller.record_evidence(
        work.run_id,
        'MODEL_ASSERTION',
        'model:self-report',
        verified=True,
        outcome={'said': 'done'},
    ) is False
    assert db.db.execute(
        'SELECT status FROM goal_milestones WHERE milestone_id=?', (milestone_id,)
    ).fetchone()[0] == 'WAITING_EVIDENCE'


def test_verified_runtime_evidence_closes_milestone_and_goal(db):
    controller = GoalController(db)
    goal_id, milestone_id = _active_goal(controller)
    work = controller.claim_next('worker:test', run_ttl=60)
    controller.record_model_proposal(work.run_id, {'next': 'run deterministic test'})

    assert controller.record_evidence(
        work.run_id,
        'DETERMINISTIC_TEST',
        'receipt:sha256:abc',
        verified=True,
        outcome={'exit_code': 0},
    ) is True
    assert db.db.execute(
        'SELECT status FROM goal_milestones WHERE milestone_id=?', (milestone_id,)
    ).fetchone()[0] == 'SUCCEEDED'
    assert db.db.execute(
        'SELECT status FROM goals WHERE goal_id=?', (goal_id,)
    ).fetchone()[0] == 'COMPLETED'


def test_fake_verified_effect_reference_is_rejected(db):
    controller = GoalController(db)
    _, milestone_id = _active_goal(controller)
    work = controller.claim_next('worker:test', run_ttl=60)
    controller.record_model_proposal(work.run_id, {'claim': 'effect succeeded'})

    assert controller.record_evidence(
        work.run_id,
        'VERIFIED_EFFECT',
        'not-a-real-effect-id',
        verified=True,
    ) is False
    assert db.db.execute(
        'SELECT status FROM goal_milestones WHERE milestone_id=?', (milestone_id,)
    ).fetchone()[0] == 'WAITING_EVIDENCE'


def test_retry_budget_blocks_runaway_loop(db):
    controller = GoalController(db)
    goal_id, milestone_id = _active_goal(controller, max_attempts=2)

    first = controller.claim_next('worker:test', run_ttl=60)
    controller.fail_run(first.run_id, 'first failure', retry_after=0)
    second = controller.claim_next('worker:test', run_ttl=60)
    controller.fail_run(second.run_id, 'second failure', retry_after=0)

    milestone = db.db.execute(
        'SELECT * FROM goal_milestones WHERE milestone_id=?', (milestone_id,)
    ).fetchone()
    goal = db.db.execute(
        'SELECT * FROM goals WHERE goal_id=?', (goal_id,)
    ).fetchone()
    assert milestone['attempt_count'] == 2
    assert milestone['status'] == 'BLOCKED'
    assert goal['status'] == 'BLOCKED'
    assert controller.claim_next('worker:test', run_ttl=60) is None


def test_waiting_evidence_blocks_second_global_autonomous_claim(db):
    controller = GoalController(db)
    _active_goal(controller)
    other_goal, _ = _active_goal(controller)

    work = controller.claim_next('worker:first', run_ttl=60)
    assert work is not None
    controller.record_model_proposal(work.run_id, {'next': 'await receipt'})

    assert controller.claim_next('worker:second', run_ttl=60) is None
    assert db.db.execute(
        "SELECT COUNT(*) FROM goal_runs WHERE status IN ('RUNNING','WAITING_EVIDENCE')"
    ).fetchone()[0] == 1
    assert db.db.execute(
        'SELECT status FROM goals WHERE goal_id=?', (other_goal,)
    ).fetchone()[0] == 'ACTIVE'


def test_deadline_reconciliation_updates_state_hash_and_requeues(db):
    controller = GoalController(db)
    _, milestone_id = _active_goal(controller, max_attempts=2)
    work = controller.claim_next('worker:test', run_ttl=10, now=100.0)
    before = controller.state_hash()

    assert controller.reconcile_deadlines(now=111.0) is True
    after = controller.state_hash()

    assert before != after
    run = db.db.execute(
        'SELECT status FROM goal_runs WHERE run_id=?', (work.run_id,)
    ).fetchone()
    milestone = db.db.execute(
        'SELECT status,next_eligible_at FROM goal_milestones WHERE milestone_id=?',
        (milestone_id,),
    ).fetchone()
    assert run['status'] == 'ABORTED'
    assert milestone['status'] == 'READY'
    assert milestone['next_eligible_at'] == pytest.approx(141.0)


def test_milestones_advance_strictly_in_order(db):
    controller = GoalController(db)
    goal_id = controller.create_goal(
        'gabriel',
        'Sequential goal',
        'Do phase one before phase two.',
        {'all_milestones_verified': True},
    )
    first_id = controller.add_milestone(
        'gabriel', goal_id, 'Phase 1', 'First phase.'
    )
    second_id = controller.add_milestone(
        'gabriel', goal_id, 'Phase 2', 'Second phase.'
    )
    controller.activate_goal('gabriel', goal_id)

    first = controller.claim_next('worker:test', run_ttl=60)
    assert first.milestone_id == first_id
    controller.record_model_proposal(first.run_id, {'next': 'verify phase 1'})
    controller.record_evidence(
        first.run_id,
        'DETERMINISTIC_TEST',
        'receipt:first',
        verified=True,
    )

    second = controller.claim_next('worker:test', run_ttl=60)
    assert second is not None and second.milestone_id == second_id


def test_high_impact_work_requires_separate_human_approval(db):
    controller = GoalController(db)
    _, milestone_id = _active_goal(controller, risk_class='HIGH_IMPACT')
    assert controller.claim_next('worker:test', run_ttl=60) is None

    controller.approve_milestone('andreas', milestone_id)
    work = controller.claim_next('worker:test', run_ttl=60)
    assert work is not None and work.milestone_id == milestone_id


def test_active_goals_are_injected_as_machine_state_not_memory_truth(db):
    controller = GoalController(db)
    goal_id, _ = _active_goal(controller)
    world = WorldAssembler(db).assemble('session:gabriel', [])
    record = world['durable_memory'][0]

    assert record['kind'] == 'goal_runtime_context'
    assert record['provenance']['source'] == 'UnifiedDB/GoalController'
    assert record['provenance']['model_generated'] is False
    assert record['value']['goals'][0]['goal_id'] == goal_id
    assert record['value']['model_role'] == 'proposal_only'


def test_invalid_state_transitions_fail_closed(db):
    controller = GoalController(db)
    goal_id, _ = _active_goal(controller)
    with pytest.raises(GoalStateError):
        controller.add_milestone(
            'andreas', goal_id, 'late', 'must not mutate active plan silently'
        )
