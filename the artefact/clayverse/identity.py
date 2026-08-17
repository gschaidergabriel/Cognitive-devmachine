from __future__ import annotations
from .store import UnifiedDB

CANONICAL_USERS=(('gabriel','Gabriel','clayverse-gabriel'),('andreas','Andreas','clayverse-andreas'))
CANONICAL_USER_IDS={uid for uid,_,_ in CANONICAL_USERS}
CANONICAL_TERMINAL_NAMES={uid:terminal for uid,_,terminal in CANONICAL_USERS}
CANONICAL_SESSION_IDS={uid:f'session:{uid}' for uid in CANONICAL_USER_IDS}


def assert_canonical_user_state(db:UnifiedDB):
    """Read-only validation of the one-entity/two-equal-users identity contract."""
    rows=db.db.execute('SELECT user_id,display_name,rights FROM users ORDER BY user_id').fetchall()
    expected={uid:(name,'equal') for uid,name,_ in CANONICAL_USERS}
    if len(rows)!=len(expected) or {row['user_id'] for row in rows} != set(expected):
        raise PermissionError('canonical entity must contain exactly two users: gabriel and andreas')
    for row in rows:
        expected_name,expected_rights=expected[row['user_id']]
        if row['display_name'] != expected_name:
            raise PermissionError(f'canonical user display name mismatch: {row["user_id"]}')
        if row['rights'] != expected_rights:
            raise PermissionError(f'canonical user rights mismatch: {row["user_id"]}')


class IdentityRouter:
    def __init__(self,db:UnifiedDB,clerk_map=None):
        self.db=db; self.clerk_map=clerk_map or {}
        fresh_identity=self._bootstrap_or_assert_canonical_users()
        if fresh_identity:
            for uid,_,term in CANONICAL_USERS:
                db.ensure_session(uid,term)
        self._normalize_terminal_sessions()
        self._bind_clerk_subjects()

    def _bootstrap_or_assert_canonical_users(self):
        rows=self.db.db.execute('SELECT user_id FROM users ORDER BY user_id').fetchall()
        if not rows:
            session_count=int(self.db.db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0])
            if session_count:
                raise PermissionError('canonical identity bootstrap requires an empty session set')
            with self.db.tx():
                for uid,name,_ in CANONICAL_USERS:
                    self.db.ensure_user(uid,name)
            assert_canonical_user_state(self.db)
            return True
        assert_canonical_user_state(self.db)
        return False

    def _normalize_terminal_sessions(self):
        with self.db.tx() as sql:
            for uid,_,term in CANONICAL_USERS:
                rows=sql.execute('SELECT session_id,terminal_name FROM sessions WHERE user_id=? ORDER BY created_at,session_id',(uid,)).fetchall()
                if len(rows)!=1:
                    raise PermissionError(f'canonical user must own exactly one permanent session: {uid}')
                if rows[0]['session_id'] != CANONICAL_SESSION_IDS[uid]:
                    raise PermissionError(f'canonical session id mismatch: {uid}')
                collision=sql.execute('SELECT user_id FROM sessions WHERE terminal_name=? AND user_id<>?',(term,uid)).fetchone()
                if collision:
                    raise PermissionError(f'canonical terminal name already belongs to another user: {term}')
                sql.execute('UPDATE sessions SET terminal_name=? WHERE session_id=?',(term,rows[0]['session_id']))

    def _bind_clerk_subjects(self):
        if not self.clerk_map:
            return
        if any(not isinstance(subject,str) or not subject.strip() or uid not in CANONICAL_USER_IDS for subject,uid in self.clerk_map.items()):
            raise PermissionError('invalid Clerk subject mapping')
        if len(set(self.clerk_map.values())) != len(self.clerk_map):
            raise PermissionError('multiple Clerk subjects for one canonical user are not allowed')
        with self.db.tx() as sql:
            for subject,uid in sorted(self.clerk_map.items()):
                owner=sql.execute('SELECT user_id FROM users WHERE clerk_subject=?',(subject,)).fetchone()
                if owner and owner[0] != uid:
                    raise PermissionError('Clerk subject is already bound to another canonical user')
                current=sql.execute('SELECT clerk_subject FROM users WHERE user_id=?',(uid,)).fetchone()
                if current and current[0] not in (None,subject):
                    raise PermissionError('canonical user is already bound to another Clerk subject')
            for subject,uid in sorted(self.clerk_map.items()):
                sql.execute('UPDATE users SET clerk_subject=? WHERE user_id=?',(subject,uid))

    def resolve(self,clerk_subject):
        uid=self.clerk_map.get(clerk_subject)
        if uid not in CANONICAL_USER_IDS: raise PermissionError('unmapped Clerk subject')
        assert_canonical_user_state(self.db)
        persisted=self.db.db.execute('SELECT user_id FROM users WHERE clerk_subject=?',(clerk_subject,)).fetchone()
        if not persisted or persisted[0] != uid: raise PermissionError('Clerk subject binding mismatch')
        rows=self.db.db.execute(
            'SELECT session_id,terminal_name,generation FROM sessions WHERE user_id=? ORDER BY created_at,session_id',
            (uid,),
        ).fetchall()
        if len(rows)!=1:
            raise PermissionError(f'canonical user must own exactly one permanent session: {uid}')
        session=rows[0]
        if session['session_id'] != CANONICAL_SESSION_IDS[uid]:
            raise PermissionError(f'canonical session id mismatch: {uid}')
        if session['terminal_name'] != CANONICAL_TERMINAL_NAMES[uid]:
            raise PermissionError(f'canonical terminal name mismatch: {uid}')
        try:
            self.db.assert_live_generation(session['session_id'],int(session['generation']))
        except Exception as exc:
            raise PermissionError(f'canonical session generation mismatch: {uid}') from exc
        return uid,session['session_id']