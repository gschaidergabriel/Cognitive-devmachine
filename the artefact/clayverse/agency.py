from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .store import UnifiedDB


AGENCY_SCHEMA = r'''
CREATE TABLE IF NOT EXISTS entity_agency_profile(
    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
    entity_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    identity_mode TEXT NOT NULL,
    substrate_anchor TEXT NOT NULL,
    behavior_mode TEXT NOT NULL,
    state_version INTEGER NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS agency_policy(
    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
    autonomy_mode TEXT NOT NULL CHECK(autonomy_mode IN ('PAUSED','BOUNDED')),
    cycle_interval_seconds REAL NOT NULL CHECK(cycle_interval_seconds>=1),
    max_steps_per_cycle INTEGER NOT NULL CHECK(max_steps_per_cycle BETWEEN 1 AND 100),
    max_retries_per_milestone INTEGER NOT NULL CHECK(max_retries_per_milestone BETWEEN 0 AND 20),
    max_effects_per_cycle INTEGER NOT NULL CHECK(max_effects_per_cycle BETWEEN 0 AND 100),
    require_verified_effect_for_progress INTEGER NOT NULL CHECK(require_verified_effect_for_progress IN (0,1)),
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS agency_goals(
    goal_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    title TEXT NOT NULL,
    objective TEXT NOT NULL,
    success_criteria TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE','PAUSED','COMPLETE','CANCELLED')),
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agency_goals_status_priority ON agency_goals(status,priority DESC,created_at);
CREATE TABLE IF NOT EXISTS agency_milestones(
    milestone_id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES agency_goals(goal_id) ON DELETE CASCADE,
    phase TEXT NOT NULL CHECK(phase IN ('CONCEPT','PROTOTYPE','FINAL')),
    title TEXT NOT NULL,
    acceptance_criteria TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PENDING','ACTIVE','READY_FOR_REVIEW','PASSED','BLOCKED','CANCELLED')),
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agency_milestones_goal_status ON agency_milestones(goal_id,status,phase);
CREATE TABLE IF NOT EXISTS agency_cycles(
    cycle_id TEXT PRIMARY KEY,
    started_at REAL NOT NULL,
    finished_at REAL,
    step_count INTEGER NOT NULL DEFAULT 0,
    effect_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK(status IN ('OPEN','CLOSED','BLOCKED')),
    reason TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS agency_attempts(
    attempt_id TEXT PRIMARY KEY,
    cycle_id TEXT NOT NULL REFERENCES agency_cycles(cycle_id),
    milestone_id TEXT NOT NULL REFERENCES agency_milestones(milestone_id),
    ordinal INTEGER NOT NULL,
    proposal TEXT NOT NULL DEFAULT '{}',
    effect_id TEXT REFERENCES effects(effect_id),
    outcome TEXT,
    status TEXT NOT NULL CHECK(status IN ('CLAIMED','SUCCEEDED','FAILED','ABORTED')),
    created_at REAL NOT NULL,
    completed_at REAL,
    UNIQUE(milestone_id,ordinal)
);
CREATE TABLE IF NOT EXISTS agency_reviews(
    review_id TEXT PRIMARY KEY,
    milestone_id TEXT NOT NULL REFERENCES agency_milestones(milestone_id),
    user_id TEXT NOT NULL REFERENCES users(user_id),
    generation INTEGER NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('PASS','REOPEN','BLOCK')),
    note TEXT NOT NULL DEFAULT '',
    ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS agency_events(
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    payload TEXT NOT NULL,
    generation INTEGER NOT NULL,
    ts REAL NOT NULL,
    UNIQUE(event_type,source_kind,source_ref)
);
CREATE TRIGGER IF NOT EXISTS agency_events_no_update
BEFORE UPDATE ON agency_events BEGIN SELECT RAISE(ABORT,'agency_events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS agency_events_no_delete
BEFORE DELETE ON agency_events BEGIN SELECT RAISE(ABORT,'agency_events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS agency_reviews_no_update
BEFORE UPDATE ON agency_reviews BEGIN SELECT RAISE(ABORT,'agency_reviews are append-only'); END;
CREATE TRIGGER IF NOT EXISTS agency_reviews_no_delete
BEFORE DELETE ON agency_reviews BEGIN SELECT RAISE(ABORT,'agency_reviews are append-only'); END;
'''


class AgencyPolicyError(RuntimeError):
    pass


@dataclass(frozen=True)
class ClaimedWork:
    cycle_id: str
    attempt_id: str
    goal_id: str
    milestone_id: str
    user_id: str
    phase: str
    title: str
    objective: str
    success_criteria: str
    acceptance_criteria: str
    attempt_ordinal: int


class AgencyState:
    """Canonical deterministic goal/autonomy state layered into UnifiedDB.

    The model can propose plans and effect intents, but this class owns goal state,
    retry limits, cycle limits, review state and the grounded snapshot injected into
    cognition. No model self-description can override these rows.
    """

    def __init__(self, db: UnifiedDB):
        self.db = db
        now = time.time()
        with db.tx() as tx:
            tx.executescript(AGENCY_SCHEMA)
            tx.execute(
                """INSERT OR IGNORE INTO entity_agency_profile
                (singleton,entity_id,display_name,identity_mode,substrate_anchor,behavior_mode,state_version,updated_at)
                VALUES(1,'clayverse','Clay','PERSISTENT_AGENT','SERVER_UNIFIEDDB','PROACTIVE_GROUNDED',1,?)""",
                (now,),
            )
            tx.execute(
                """INSERT OR IGNORE INTO agency_policy
                (singleton,autonomy_mode,cycle_interval_seconds,max_steps_per_cycle,max_retries_per_milestone,
                 max_effects_per_cycle,require_verified_effect_for_progress,updated_at)
                VALUES(1,'BOUNDED',60,8,3,4,1,?)""",
                (now,),
            )
            self._refresh_hash(tx)

    @staticmethod
    def _rows(tx, table: str) -> list[dict[str, Any]]:
        return [dict(row) for row in tx.execute(f"SELECT * FROM {table} ORDER BY 1")]

    def _refresh_hash(self, tx) -> str:
        tables = (
            'entity_agency_profile','agency_policy','agency_goals','agency_milestones',
            'agency_cycles','agency_attempts','agency_reviews','agency_events',
        )
        payload = [(table, self._rows(tx, table)) for table in tables]
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',',':')).encode()).hexdigest()
        tx.execute(
            "INSERT INTO meta(key,value) VALUES('agency_state_hash',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (digest,),
        )
        return digest

    def policy(self) -> dict[str, Any]:
        row = self.db.db.execute('SELECT * FROM agency_policy WHERE singleton=1').fetchone()
        if not row:
            raise AgencyPolicyError('agency policy missing')
        return dict(row)

    def set_autonomy_mode(self, mode: str) -> None:
        if mode not in {'PAUSED','BOUNDED'}:
            raise AgencyPolicyError('invalid autonomy mode')
        with self.db.tx() as tx:
            tx.execute('UPDATE agency_policy SET autonomy_mode=?,updated_at=? WHERE singleton=1', (mode,time.time()))
            self._refresh_hash(tx)

    def create_goal(self, user_id: str, title: str, objective: str, success_criteria: str, *, priority: int = 0) -> str:
        if not self.db.db.execute('SELECT 1 FROM users WHERE user_id=?', (user_id,)).fetchone():
            raise AgencyPolicyError('unknown canonical user')
        values = (title, objective, success_criteria)
        if any(not isinstance(v,str) or not v.strip() for v in values):
            raise AgencyPolicyError('goal fields must be non-empty strings')
        goal_id = str(uuid.uuid4()); now = time.time()
        with self.db.tx() as tx:
            tx.execute(
                "INSERT INTO agency_goals VALUES(?,?,?,?,?,?,'ACTIVE',?,?)",
                (goal_id,user_id,title.strip(),objective.strip(),success_criteria.strip(),int(priority),now,now),
            )
            self._event(tx,'goal.created','goal',goal_id,{'user_id':user_id,'title':title.strip()})
            self._refresh_hash(tx)
        return goal_id

    def add_milestone(self, goal_id: str, phase: str, title: str, acceptance_criteria: str) -> str:
        if phase not in {'CONCEPT','PROTOTYPE','FINAL'}:
            raise AgencyPolicyError('invalid milestone phase')
        if any(not isinstance(v,str) or not v.strip() for v in (title,acceptance_criteria)):
            raise AgencyPolicyError('milestone fields must be non-empty strings')
        if not self.db.db.execute("SELECT 1 FROM agency_goals WHERE goal_id=? AND status='ACTIVE'", (goal_id,)).fetchone():
            raise AgencyPolicyError('active goal not found')
        milestone_id = str(uuid.uuid4()); now = time.time()
        with self.db.tx() as tx:
            tx.execute(
                "INSERT INTO agency_milestones VALUES(?,?,?,?,?,'PENDING',?,?)",
                (milestone_id,goal_id,phase,title.strip(),acceptance_criteria.strip(),now,now),
            )
            self._event(tx,'milestone.created','milestone',milestone_id,{'goal_id':goal_id,'phase':phase})
            self._refresh_hash(tx)
        return milestone_id

    def snapshot(self, *, max_goals: int = 8) -> dict[str, Any]:
        profile = dict(self.db.db.execute('SELECT * FROM entity_agency_profile WHERE singleton=1').fetchone())
        policy = self.policy()
        goals = []
        rows = self.db.db.execute(
            "SELECT * FROM agency_goals WHERE status IN ('ACTIVE','PAUSED') ORDER BY priority DESC,created_at LIMIT ?",
            (max_goals,),
        ).fetchall()
        for row in rows:
            goal = dict(row)
            goal['milestones'] = [dict(m) for m in self.db.db.execute(
                'SELECT * FROM agency_milestones WHERE goal_id=? ORDER BY created_at', (row['goal_id'],)
            ).fetchall()]
            goals.append(goal)
        state_hash = self.db.db.execute("SELECT value FROM meta WHERE key='agency_state_hash'").fetchone()
        return {
            'authority':'UnifiedDB',
            'profile':profile,
            'policy':policy,
            'active_goals':goals,
            'state_hash':state_hash[0] if state_hash else None,
            'grounding_law':(
                'Plans and self-descriptions are proposals. Goal state is true only from this snapshot; '
                'external/state-changing progress is true only after a verified EffectGate outcome.'
            ),
        }

    def begin_cycle(self) -> str | None:
        policy = self.policy()
        if policy['autonomy_mode'] != 'BOUNDED':
            return None
        cycle_id = str(uuid.uuid4())
        with self.db.tx() as tx:
            tx.execute("INSERT INTO agency_cycles(cycle_id,started_at,status) VALUES(?,?,'OPEN')", (cycle_id,time.time()))
            self._event(tx,'cycle.opened','cycle',cycle_id,{})
            self._refresh_hash(tx)
        return cycle_id

    def claim_next(self, cycle_id: str) -> ClaimedWork | None:
        policy = self.policy()
        cycle = self.db.db.execute('SELECT * FROM agency_cycles WHERE cycle_id=?', (cycle_id,)).fetchone()
        if not cycle or cycle['status'] != 'OPEN':
            raise AgencyPolicyError('cycle is not open')
        if int(cycle['step_count']) >= int(policy['max_steps_per_cycle']):
            self.close_cycle(cycle_id,'step_limit')
            return None
        candidates = self.db.db.execute(
            """SELECT m.*,g.user_id,g.title AS goal_title,g.objective,g.success_criteria,g.priority
               FROM agency_milestones m JOIN agency_goals g ON g.goal_id=m.goal_id
               WHERE g.status='ACTIVE' AND m.status IN ('PENDING','ACTIVE')
               ORDER BY g.priority DESC,m.created_at"""
        ).fetchall()
        for row in candidates:
            attempts = int(self.db.db.execute('SELECT COUNT(*) FROM agency_attempts WHERE milestone_id=?', (row['milestone_id'],)).fetchone()[0])
            if attempts >= int(policy['max_retries_per_milestone']):
                with self.db.tx() as tx:
                    tx.execute("UPDATE agency_milestones SET status='BLOCKED',updated_at=? WHERE milestone_id=?", (time.time(),row['milestone_id']))
                    self._event(tx,'milestone.retry_exhausted','milestone',row['milestone_id'],{'attempts':attempts})
                    self._refresh_hash(tx)
                continue
            attempt_id = str(uuid.uuid4()); ordinal = attempts + 1; now = time.time()
            with self.db.tx() as tx:
                tx.execute("UPDATE agency_milestones SET status='ACTIVE',updated_at=? WHERE milestone_id=?", (now,row['milestone_id']))
                tx.execute(
                    "INSERT INTO agency_attempts(attempt_id,cycle_id,milestone_id,ordinal,status,created_at) VALUES(?,?,?,?,'CLAIMED',?)",
                    (attempt_id,cycle_id,row['milestone_id'],ordinal,now),
                )
                tx.execute('UPDATE agency_cycles SET step_count=step_count+1 WHERE cycle_id=?', (cycle_id,))
                self._event(tx,'attempt.claimed','attempt',attempt_id,{'milestone_id':row['milestone_id'],'ordinal':ordinal})
                self._refresh_hash(tx)
            return ClaimedWork(cycle_id,attempt_id,row['goal_id'],row['milestone_id'],row['user_id'],row['phase'],row['goal_title'],row['objective'],row['success_criteria'],row['acceptance_criteria'],ordinal)
        self.close_cycle(cycle_id,'no_runnable_work')
        return None

    def complete_attempt(self, attempt_id: str, proposal: dict[str, Any], effect_id: str | None, outcome: dict[str, Any] | None) -> str:
        row = self.db.db.execute('SELECT * FROM agency_attempts WHERE attempt_id=?', (attempt_id,)).fetchone()
        if not row or row['status'] != 'CLAIMED':
            raise AgencyPolicyError('attempt is not claimable')
        policy = self.policy()
        verified_ok = bool(effect_id and isinstance(outcome,dict) and outcome.get('ok') is True and outcome.get('denied') is not True)
        no_effect = effect_id is None
        success = verified_ok if int(policy['require_verified_effect_for_progress']) else (verified_ok or no_effect)
        status = 'SUCCEEDED' if success else 'FAILED'
        now = time.time()
        with self.db.tx() as tx:
            tx.execute(
                'UPDATE agency_attempts SET proposal=?,effect_id=?,outcome=?,status=?,completed_at=? WHERE attempt_id=?',
                (json.dumps(proposal,sort_keys=True),effect_id,json.dumps(outcome,sort_keys=True) if outcome is not None else None,status,now,attempt_id),
            )
            if effect_id:
                tx.execute('UPDATE agency_cycles SET effect_count=effect_count+1 WHERE cycle_id=?', (row['cycle_id'],))
            if success:
                tx.execute("UPDATE agency_milestones SET status='READY_FOR_REVIEW',updated_at=? WHERE milestone_id=?", (now,row['milestone_id']))
            self._event(tx,'attempt.completed','attempt',attempt_id,{'status':status,'effect_id':effect_id,'verified_ok':verified_ok})
            self._refresh_hash(tx)
        return status

    def review_milestone(self, milestone_id: str, user_id: str, decision: str, note: str = '') -> None:
        if decision not in {'PASS','REOPEN','BLOCK'}:
            raise AgencyPolicyError('invalid review decision')
        row = self.db.db.execute(
            'SELECT m.*,g.user_id AS owner FROM agency_milestones m JOIN agency_goals g ON g.goal_id=m.goal_id WHERE m.milestone_id=?',
            (milestone_id,),
        ).fetchone()
        if not row or row['owner'] != user_id:
            raise AgencyPolicyError('milestone owner mismatch')
        new_status = {'PASS':'PASSED','REOPEN':'ACTIVE','BLOCK':'BLOCKED'}[decision]
        now = time.time(); review_id = str(uuid.uuid4())
        with self.db.tx() as tx:
            tx.execute('INSERT INTO agency_reviews VALUES(?,?,?,?,?,?,?)', (review_id,milestone_id,user_id,self.db.entity_generation(),decision,note[:2000],now))
            tx.execute('UPDATE agency_milestones SET status=?,updated_at=? WHERE milestone_id=?', (new_status,now,milestone_id))
            if decision == 'PASS':
                remaining = int(tx.execute("SELECT COUNT(*) FROM agency_milestones WHERE goal_id=? AND status!='PASSED'", (row['goal_id'],)).fetchone()[0])
                if remaining == 0:
                    tx.execute("UPDATE agency_goals SET status='COMPLETE',updated_at=? WHERE goal_id=?", (now,row['goal_id']))
            self._event(tx,'milestone.reviewed','review',review_id,{'milestone_id':milestone_id,'decision':decision})
            self._refresh_hash(tx)

    def close_cycle(self, cycle_id: str, reason: str = '') -> None:
        with self.db.tx() as tx:
            row = tx.execute('SELECT status FROM agency_cycles WHERE cycle_id=?', (cycle_id,)).fetchone()
            if not row or row['status'] != 'OPEN':
                return
            tx.execute("UPDATE agency_cycles SET status='CLOSED',finished_at=?,reason=? WHERE cycle_id=?", (time.time(),reason[:500],cycle_id))
            self._event(tx,'cycle.closed','cycle',cycle_id,{'reason':reason[:500]})
            self._refresh_hash(tx)

    def _event(self, tx, event_type: str, source_kind: str, source_ref: str, payload: dict[str, Any]) -> None:
        tx.execute(
            'INSERT OR IGNORE INTO agency_events VALUES(?,?,?,?,?,?,?)',
            (str(uuid.uuid4()),event_type,source_kind,source_ref,json.dumps(payload,sort_keys=True),self.db.entity_generation(),time.time()),
        )
