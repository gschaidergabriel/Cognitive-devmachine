from __future__ import annotations
from .store import UnifiedDB
CANONICAL_USERS=(('gabriel','Gabriel','terminal-gabriel'),('andreas','Andreas','terminal-andreas'))
class IdentityRouter:
    def __init__(self,db:UnifiedDB,clerk_map=None):
        self.db=db; self.clerk_map=clerk_map or {}
        for uid,name,term in CANONICAL_USERS: db.ensure_user(uid,name); db.ensure_session(uid,term)
    def resolve(self,clerk_subject):
        uid=self.clerk_map.get(clerk_subject)
        if uid not in {'gabriel','andreas'}: raise PermissionError('unmapped Clerk subject')
        return uid,self.db.ensure_session(uid,f'terminal-{uid}')
