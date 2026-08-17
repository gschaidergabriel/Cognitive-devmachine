from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass

from .store import StaleGeneration, UnifiedDB


GOAL_SCHEMA = r'''
CREATE TABLE IF NOT EXISTS goals(
    goal_id TEXT PRIMARY KEY,
    created_by_user_id TEXT NOT NULL REFERENCES users(user_id),
    title TEXT NOT NULL,
    objective TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('DRAFT','ACTIVE','BLOCKED','COMPLETED','CANCELLED')),
    priority INTEGER NOT NULL CHECK(priority BETWEEN 0 AND 100),
    success_criteria TEXT NOT NULL,
    constraints_json TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_goals_status_priority ON goals(status,priority DESC,created_at,goal_id);
CREATE TABLE IF NOT EXISTS goal_milestones(
    milestone_id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(goal_id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PENDING','READY','RUNNING','WAITING_EVIDENCE','BLOCKED','SUCCEEDED','FAILED','CANCELLED')),
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count >= 0),
    max_attempts INTEGER NOT NULL CHECK(max_attempts BETWEEN 1 AND 20),
    risk_class TEXT NOT NULL CHECK(risk_class IN ('READ_ONLY','REVERSIBLE','EXTERNAL_EFFECT','HIGH_IMPACT')),
    human_approved INTEGER NOT NULL DEFAULT 0 CHECK(human_approved IN (0,1)),
    next_eligible_at REAL NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    UNIQUE(goal_id,ordinal)
);
CREATE INDEX IF NOT EXISTS idx_goal_milestones_ready ON goal_milestones(status,next_eligible_at,goal_id,ordinal);
CREATE TABLE IF NOT EXISTS goal_runs(
    run_id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(goal_id),
    milestone_id TEXT NOT NULL REFERENCES goal_milestones(milestone_id),
    entity_generation INTEGER NOT NULL,
    worker_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('RUNNING','WAITING_EVIDENCE','SUCCEEDED','FAILED','BLOCKED','ABORTED')),
    started_at REAL NOT NULL,
    deadline_at REAL NOT NULL,
    proposal_hash TEXT,
    proposal_json TEXT,
    evidence_class TEXT,
    evidence_ref TEXT,
    evidence_verified INTEGER CHECK(evidence_verified IN (0,1)),
    outcome_json TEXT,
    completed_at REAL
);
CREATE INDEX IF NOT EXISTS idx_goal_runs_open ON goal_runs(status,deadline_at,started_at);
CREATE TABLE IF NOT EXISTS goal_events(
    event_id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals(goal_id) ON DELETE CASCADE,
    milestone_id TEXT REFERENCES goal_milestones(milestone_id) ON DELETE CASCADE,
    run_id TEXT REFERENCES goal_runs(run_id) ON DELETE CASCADE,
    entity_generation INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_goal_events_goal_ts ON goal_events(goal_id,ts,event_id);
'''

_ALLOWED_EVIDENCE = frozenset({
    'VERIFIED_EFFECT',
    'DETERMINISTIC_TEST',
    'USER_CONFIRMATION',
    'SIGNED_RUNTIME_RECEIPT',
})


class GoalStateError(RuntimeError):
    pass


@dataclass(frozen=True)
class GoalWorkItem:
    run_id: str
    goal_id: str
    milestone_id: str
    entity_generation: int
    created_by_user_id: str
    title: str
    objective: str
    success_criteria: object
    constraints: object
    milestone_title: str
    milestone_description: str
    risk_class: str
    attempt: int
    max_attempts: int
    deadline_at: float

    def as_dict(self) -> dict[str, object]:
        return {
            'run_id': self.run_id,
            'goal_id': self.goal_id,
            'milestone_id': self.milestone_id,
            'entity_generation': self.entity_generation,
            'created_by_user_id': self.created_by_user_id,
            'title': self.title,
            'objective': self.objective,
            'success_criteria': self.success_criteria,
            'constraints': self.constraints,
            'milestone_title': self.milestone_title,
            'milestone_description': self.milestone_description,
            'risk_class': self.risk_class,
            'attempt': self.attempt,
            'max_attempts': self.max_attempts,
            'deadline_at': self.deadline_at,
            'epistemic_contract': {
                'model_output_is_proposal_only': True,
                'model_self_report_never_proves_execution': True,
                'milestone_success_requires_verified_external_or_deterministic_evidence': True,
            },
        }


class GoalController:
    """Deterministic owner of persistent goals, retries, stop conditions and evidence closure.

    The controller is deliberately not an LLM and does not execute tools. An inference model may
    propose how to pursue a claimed work item, but only admitted evidence can close a milestone.
    This keeps autonomy in the machine loop while keeping truth/effect authority outside the model.
    """

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.db.db.executescript(GOAL_SCHEMA)
        self.db.db.execute(
            "INSERT INTO meta(key,value) VALUES('goal_schema_version','1') "
            "ON CONFLICT(key) DO UPDATE SET value='1'"
        )
        self._refresh_state_hash()

    @staticmethod
    def _json(value: object) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

    @staticmethod
    def _load(value: str) -> object:
        return json.loads(value)

    def _assert_user(self, user_id: str) -> None:
        if user_id not in {'gabriel', 'andreas'}:
            raise PermissionError('goal mutations require a canonical user')
        row = self.db.db.execute('SELECT 1 FROM users WHERE user_id=?', (user_id,)).fetchone()
        if row is None:
            raise PermissionError('canonical user is not initialized')

    def _event_in_tx(self, db, *, goal_id: str, event_type: str, payload: object,
                     milestone_id: str | None = None, run_id: str | None = None) -> str:
        event_id = str(uuid.uuid4())
        db.execute(
            'INSERT INTO goal_events VALUES(?,?,?,?,?,?,?,?)',
            (
                event_id,
                goal_id,
                milestone_id,
                run_id,
                self.db.entity_generation(),
                event_type,
                self._json(payload),
                time.time(),
            ),
        )
        return event_id

    def _refresh_state_hash(self) -> str:
        payload = []
        for table in ('goals', 'goal_milestones', 'goal_runs', 'goal_events'):
            rows = [dict(r) for r in self.db.db.execute(f'SELECT * FROM {table} ORDER BY 1')]
            payload.append((table, rows))
        digest = hashlib.sha256(self._json(payload).encode('utf-8')).hexdigest()
        self.db.db.execute(
            "INSERT INTO meta(key,value) VALUES('goal_state_hash',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (digest,),
        )
        return digest

    def create_goal(self, user_id: str, title: str, objective: str, success_criteria: object,
                    *, constraints: object | None = None, priority: int = 50) -> str:
        self._assert_user(user_id)
        title = str(title).strip()
        objective = str(objective).strip()
        if not title or not objective:
            raise ValueError('goal title/objective must be non-empty')
        if not isinstance(priority, int) or not 0 <= priority <= 100:
            raise ValueError('priority must be 0..100')
        goal_id = str(uuid.uuid4())
        now = time.time()
        with self.db.tx() as db:
            db.execute(
                'INSERT INTO goals VALUES(?,?,?,?,?,?,?,?,?,?)',
                (
                    goal_id,
                    user_id,
                    title[:500],
                    objective[:20_000],
                    'DRAFT',
                    priority,
                    self._json(success_criteria),
                    self._json(constraints or {}),
                    now,
                    now,
                ),
            )
            self._event_in_tx(db, goal_id=goal_id, event_type='GOAL_CREATED', payload={'by': user_id})
        self._refresh_state_hash()
        return goal_id

    def add_milestone(self, user_id: str, goal_id: str, title: str, description: str, *,
                      max_attempts: int = 3, risk_class: str = 'REVERSIBLE',
                      human_approved: bool = False) -> str:
        self._assert_user(user_id)
        if risk_class not in {'READ_ONLY', 'REVERSIBLE', 'EXTERNAL_EFFECT', 'HIGH_IMPACT'}:
            raise ValueError('invalid risk_class')
        if not isinstance(max_attempts, int) or not 1 <= max_attempts <= 20:
            raise ValueError('max_attempts must be 1..20')
        if risk_class == 'HIGH_IMPACT' and human_approved:
            # Approval must be a separate explicit state transition, never smuggled in at creation.
            raise ValueError('HIGH_IMPACT milestones require separate explicit approval')
        milestone_id = str(uuid.uuid4())
        now = time.time()
        with self.db.tx() as db:
            goal = db.execute('SELECT status FROM goals WHERE goal_id=?', (goal_id,)).fetchone()
            if goal is None:
                raise KeyError(goal_id)
            if goal['status'] not in {'DRAFT', 'BLOCKED'}:
                raise GoalStateError('milestones may only be added before activation or while blocked')
            ordinal = int(db.execute(
                'SELECT COALESCE(MAX(ordinal),0)+1 FROM goal_milestones WHERE goal_id=?',
                (goal_id,),
            ).fetchone()[0])
            db.execute(
                'INSERT INTO goal_milestones VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (
                    milestone_id,
                    goal_id,
                    ordinal,
                    str(title).strip()[:500],
                    str(description).strip()[:20_000],
                    'PENDING',
                    0,
                    max_attempts,
                    risk_class,
                    1 if human_approved else 0,
                    0.0,
                    None,
                    now,
                    now,
                ),
            )
            self._event_in_tx(
                db,
                goal_id=goal_id,
                milestone_id=milestone_id,
                event_type='MILESTONE_ADDED',
                payload={'ordinal': ordinal, 'risk_class': risk_class, 'max_attempts': max_attempts},
            )
        self._refresh_state_hash()
        return milestone_id

    def activate_goal(self, user_id: str, goal_id: str) -> None:
        self._assert_user(user_id)
        now = time.time()
        with self.db.tx() as db:
            goal = db.execute('SELECT status FROM goals WHERE goal_id=?', (goal_id,)).fetchone()
            if goal is None:
                raise KeyError(goal_id)
            count = int(db.execute('SELECT COUNT(*) FROM goal_milestones WHERE goal_id=?', (goal_id,)).fetchone()[0])
            if count == 0:
                raise GoalStateError('goal requires at least one milestone')
            if goal['status'] not in {'DRAFT', 'BLOCKED'}:
                raise GoalStateError('goal is not activatable')
            db.execute("UPDATE goals SET status='ACTIVE',updated_at=? WHERE goal_id=?", (now, goal_id))
            db.execute(
                "UPDATE goal_milestones SET status='READY',updated_at=? "
                "WHERE goal_id=? AND status IN ('PENDING','FAILED')",
                (now, goal_id),
            )
            self._event_in_tx(db, goal_id=goal_id, event_type='GOAL_ACTIVATED', payload={'by': user_id})
        self._refresh_state_hash()

    def approve_milestone(self, user_id: str, milestone_id: str) -> None:
        self._assert_user(user_id)
        now = time.time()
        with self.db.tx() as db:
            row = db.execute('SELECT goal_id,status FROM goal_milestones WHERE milestone_id=?', (milestone_id,)).fetchone()
            if row is None:
                raise KeyError(milestone_id)
            db.execute('UPDATE goal_milestones SET human_approved=1,updated_at=? WHERE milestone_id=?', (now, milestone_id))
            self._event_in_tx(
                db,
                goal_id=row['goal_id'],
                milestone_id=milestone_id,
                event_type='MILESTONE_HUMAN_APPROVED',
                payload={'by': user_id},
            )
        self._refresh_state_hash()

    def _expire_runs_in_tx(self, db, now: float) -> None:
        expired = db.execute(
            "SELECT r.*,m.attempt_count,m.max_attempts FROM goal_runs r "
            "JOIN goal_milestones m ON m.milestone_id=r.milestone_id "
            "WHERE r.status='RUNNING' AND r.deadline_at<=? ORDER BY r.started_at,r.run_id",
            (now,),
        ).fetchall()
        for row in expired:
            retry = int(row['attempt_count']) < int(row['max_attempts'])
            db.execute(
                "UPDATE goal_runs SET status='ABORTED',outcome_json=?,completed_at=? WHERE run_id=? AND status='RUNNING'",
                (self._json({'reason': 'run_deadline_exceeded'}), now, row['run_id']),
            )
            db.execute(
                "UPDATE goal_milestones SET status=?,next_eligible_at=?,last_error=?,updated_at=? WHERE milestone_id=?",
                ('READY' if retry else 'BLOCKED', now + 30.0 if retry else 0.0, 'run_deadline_exceeded', now, row['milestone_id']),
            )
            if not retry:
                db.execute("UPDATE goals SET status='BLOCKED',updated_at=? WHERE goal_id=?", (now, row['goal_id']))
            self._event_in_tx(
                db,
                goal_id=row['goal_id'],
                milestone_id=row['milestone_id'],
                run_id=row['run_id'],
                event_type='RUN_EXPIRED',
                payload={'retry': retry},
            )

    def claim_next(self, worker_id: str, *, run_ttl: float = 300.0, now: float | None = None) -> GoalWorkItem | None:
        worker_id = str(worker_id).strip()
        if not worker_id or len(worker_id) > 500:
            raise ValueError('invalid worker_id')
        if not 1.0 <= float(run_ttl) <= 3600.0:
            raise ValueError('run_ttl must be between 1 and 3600 seconds')
        now = time.time() if now is None else float(now)
        generation = self.db.entity_generation()
        with self.db.tx() as db:
            self._expire_runs_in_tx(db, now)
            if db.execute("SELECT 1 FROM goal_runs WHERE status='RUNNING' LIMIT 1").fetchone():
                return None
            row = db.execute(
                "SELECT m.*,g.created_by_user_id,g.title AS goal_title,g.objective,g.success_criteria,g.constraints_json,g.priority "
                "FROM goal_milestones m JOIN goals g ON g.goal_id=m.goal_id "
                "WHERE g.status='ACTIVE' AND m.status='READY' AND m.next_eligible_at<=? "
                "AND m.attempt_count<m.max_attempts "
                "AND (m.risk_class!='HIGH_IMPACT' OR m.human_approved=1) "
                "ORDER BY g.priority DESC,g.created_at,m.ordinal,m.milestone_id LIMIT 1",
                (now,),
            ).fetchone()
            if row is None:
                return None
            if generation != self.db.entity_generation():
                raise StaleGeneration('entity_generation')
            run_id = str(uuid.uuid4())
            attempt = int(row['attempt_count']) + 1
            deadline = now + float(run_ttl)
            cur = db.execute(
                "UPDATE goal_milestones SET status='RUNNING',attempt_count=?,updated_at=? "
                "WHERE milestone_id=? AND status='READY' AND attempt_count=?",
                (attempt, now, row['milestone_id'], row['attempt_count']),
            )
            if cur.rowcount != 1:
                raise GoalStateError('milestone changed during claim')
            db.execute(
                'INSERT INTO goal_runs(run_id,goal_id,milestone_id,entity_generation,worker_id,status,started_at,deadline_at) '
                'VALUES(?,?,?,?,?,?,?,?)',
                (run_id, row['goal_id'], row['milestone_id'], generation, worker_id, 'RUNNING', now, deadline),
            )
            self._event_in_tx(
                db,
                goal_id=row['goal_id'],
                milestone_id=row['milestone_id'],
                run_id=run_id,
                event_type='RUN_CLAIMED',
                payload={'worker_id': worker_id, 'attempt': attempt, 'deadline_at': deadline},
            )
        self._refresh_state_hash()
        return GoalWorkItem(
            run_id=run_id,
            goal_id=row['goal_id'],
            milestone_id=row['milestone_id'],
            entity_generation=generation,
            created_by_user_id=row['created_by_user_id'],
            title=row['goal_title'],
            objective=row['objective'],
            success_criteria=self._load(row['success_criteria']),
            constraints=self._load(row['constraints_json']),
            milestone_title=row['title'],
            milestone_description=row['description'],
            risk_class=row['risk_class'],
            attempt=attempt,
            max_attempts=int(row['max_attempts']),
            deadline_at=deadline,
        )

    def record_model_proposal(self, run_id: str, proposal: object) -> str:
        encoded = self._json(proposal)
        proposal_hash = hashlib.sha256(encoded.encode('utf-8')).hexdigest()
        now = time.time()
        with self.db.tx() as db:
            row = db.execute('SELECT * FROM goal_runs WHERE run_id=?', (run_id,)).fetchone()
            if row is None:
                raise KeyError(run_id)
            if row['status'] != 'RUNNING':
                raise GoalStateError('run is not accepting a proposal')
            if int(row['entity_generation']) != self.db.entity_generation():
                raise StaleGeneration('entity_generation')
            db.execute(
                "UPDATE goal_runs SET status='WAITING_EVIDENCE',proposal_hash=?,proposal_json=? WHERE run_id=?",
                (proposal_hash, encoded, run_id),
            )
            db.execute(
                "UPDATE goal_milestones SET status='WAITING_EVIDENCE',updated_at=? WHERE milestone_id=?",
                (now, row['milestone_id']),
            )
            self._event_in_tx(
                db,
                goal_id=row['goal_id'],
                milestone_id=row['milestone_id'],
                run_id=run_id,
                event_type='MODEL_PROPOSAL_RECORDED',
                payload={'proposal_hash': proposal_hash, 'truth_authority': False, 'effect_authority': False},
            )
        self._refresh_state_hash()
        return proposal_hash

    def record_evidence(self, run_id: str, evidence_class: str, evidence_ref: str, *,
                        verified: bool, outcome: object | None = None) -> bool:
        evidence_class = str(evidence_class)
        evidence_ref = str(evidence_ref).strip()
        if not evidence_ref:
            raise ValueError('evidence_ref is required')
        now = time.time()
        accepted = bool(verified and evidence_class in _ALLOWED_EVIDENCE)
        with self.db.tx() as db:
            row = db.execute('SELECT * FROM goal_runs WHERE run_id=?', (run_id,)).fetchone()
            if row is None:
                raise KeyError(run_id)
            if row['status'] != 'WAITING_EVIDENCE':
                raise GoalStateError('run is not waiting for evidence')
            if int(row['entity_generation']) != self.db.entity_generation():
                raise StaleGeneration('entity_generation')
            if not accepted:
                db.execute(
                    'UPDATE goal_runs SET evidence_class=?,evidence_ref=?,evidence_verified=0,outcome_json=? WHERE run_id=?',
                    (evidence_class, evidence_ref, self._json(outcome), run_id),
                )
                self._event_in_tx(
                    db,
                    goal_id=row['goal_id'],
                    milestone_id=row['milestone_id'],
                    run_id=run_id,
                    event_type='EVIDENCE_REJECTED',
                    payload={'evidence_class': evidence_class, 'evidence_ref': evidence_ref, 'verified': bool(verified)},
                )
            else:
                db.execute(
                    "UPDATE goal_runs SET status='SUCCEEDED',evidence_class=?,evidence_ref=?,evidence_verified=1,outcome_json=?,completed_at=? WHERE run_id=?",
                    (evidence_class, evidence_ref, self._json(outcome), now, run_id),
                )
                db.execute(
                    "UPDATE goal_milestones SET status='SUCCEEDED',last_error=NULL,updated_at=? WHERE milestone_id=?",
                    (now, row['milestone_id']),
                )
                remaining = int(db.execute(
                    "SELECT COUNT(*) FROM goal_milestones WHERE goal_id=? AND status!='SUCCEEDED' AND status!='CANCELLED'",
                    (row['goal_id'],),
                ).fetchone()[0])
                if remaining == 0:
                    db.execute("UPDATE goals SET status='COMPLETED',updated_at=? WHERE goal_id=?", (now, row['goal_id']))
                self._event_in_tx(
                    db,
                    goal_id=row['goal_id'],
                    milestone_id=row['milestone_id'],
                    run_id=run_id,
                    event_type='MILESTONE_VERIFIED_SUCCEEDED',
                    payload={'evidence_class': evidence_class, 'evidence_ref': evidence_ref},
                )
        self._refresh_state_hash()
        return accepted

    def fail_run(self, run_id: str, error: str, *, retry_after: float = 30.0) -> None:
        now = time.time()
        with self.db.tx() as db:
            row = db.execute(
                'SELECT r.*,m.attempt_count,m.max_attempts FROM goal_runs r '
                'JOIN goal_milestones m ON m.milestone_id=r.milestone_id WHERE r.run_id=?',
                (run_id,),
            ).fetchone()
            if row is None:
                raise KeyError(run_id)
            if row['status'] not in {'RUNNING', 'WAITING_EVIDENCE'}:
                raise GoalStateError('run is already terminal')
            retry = int(row['attempt_count']) < int(row['max_attempts'])
            db.execute(
                "UPDATE goal_runs SET status='FAILED',outcome_json=?,completed_at=? WHERE run_id=?",
                (self._json({'error': str(error)[:4000]}), now, run_id),
            )
            db.execute(
                'UPDATE goal_milestones SET status=?,next_eligible_at=?,last_error=?,updated_at=? WHERE milestone_id=?',
                ('READY' if retry else 'BLOCKED', now + max(0.0, float(retry_after)) if retry else 0.0, str(error)[:4000], now, row['milestone_id']),
            )
            if not retry:
                db.execute("UPDATE goals SET status='BLOCKED',updated_at=? WHERE goal_id=?", (now, row['goal_id']))
            self._event_in_tx(
                db,
                goal_id=row['goal_id'],
                milestone_id=row['milestone_id'],
                run_id=run_id,
                event_type='RUN_FAILED',
                payload={'retry': retry, 'error': str(error)[:1000]},
            )
        self._refresh_state_hash()

    def context_for_user(self, user_id: str, *, max_goals: int = 5, max_milestones: int = 12) -> dict[str, object]:
        self._assert_user(user_id)
        goals = []
        rows = self.db.db.execute(
            "SELECT * FROM goals WHERE status IN ('ACTIVE','BLOCKED') ORDER BY priority DESC,created_at,goal_id LIMIT ?",
            (max(1, min(int(max_goals), 20)),),
        ).fetchall()
        for goal in rows:
            milestones = [dict(r) for r in self.db.db.execute(
                'SELECT milestone_id,ordinal,title,description,status,attempt_count,max_attempts,risk_class,human_approved,next_eligible_at,last_error '
                'FROM goal_milestones WHERE goal_id=? ORDER BY ordinal LIMIT ?',
                (goal['goal_id'], max(1, min(int(max_milestones), 50))),
            ).fetchall()]
            goals.append({
                'goal_id': goal['goal_id'],
                'created_by_user_id': goal['created_by_user_id'],
                'title': goal['title'],
                'objective': goal['objective'],
                'status': goal['status'],
                'priority': int(goal['priority']),
                'success_criteria': self._load(goal['success_criteria']),
                'constraints': self._load(goal['constraints_json']),
                'milestones': milestones,
            })
        return {
            'kind': 'goal_runtime_context',
            'subject': 'persistent_autonomous_goals',
            'value': {
                'goals': goals,
                'entity_generation': self.db.entity_generation(),
                'controller': 'deterministic',
                'model_role': 'proposal_only',
                'success_rule': 'verified evidence closes milestones; model assertions never do',
            },
            'provenance': {
                'source': 'UnifiedDB/GoalController',
                'truth_authority': True,
                'effect_authority': False,
                'model_generated': False,
            },
        }
