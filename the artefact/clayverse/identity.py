from __future__ import annotations
from .store import UnifiedDB

CANONICAL_USERS=(('gabriel','Gabriel','clayverse-gabriel'),('andreas','Andreas','clayverse-andreas'))
CANONICAL_USER_IDS={uid for uid,_,_ in CANONICAL_USERS}
CANONICAL_TERMINAL_NAMES={uid:terminal for uid,_,terminal in CANONICAL_USERS}

class IdentityRouter:
    def __init__(self,db:UnifiedDB,clerk_map=None):
        self.db=db; self.clerk_map=clerk_map or {}
        for uid,name,term in CANONICAL_USERS: db.ensure_user(uid,name); db.ensure_session(uid,term)
        self._bind_clerk_subjects()

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
        persisted=self.db.db.execute('SELECT user_id FROM users WHERE clerk_subject=?',(clerk_subject,)).fetchone()
        if not persisted or persisted[0] != uid: raise PermissionError('Clerk subject binding mismatch')
        return uid,self.db.ensure_session(uid,CANONICAL_TERMINAL_NAMES[uid])
