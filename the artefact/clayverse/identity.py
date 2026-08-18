from __future__ import annotations
from .store import UnifiedDB

CANONICAL_USERS=(('gabriel','Gabriel','clayverse-gabriel'),('andreas','Andreas','clayverse-andreas'))
CANONICAL_USER_IDS={uid for uid,_,_ in CANONICAL_USERS}
CANONICAL_TERMINAL_NAMES={uid:terminal for uid,_,terminal in CANONICAL_USERS}

# ── Wie viele gleichzeitige Sitzungen ein Mensch hat ───────────────────────
# Eignerentscheidung: zwei, umschaltbar. Diese Zahl ist der EINZIGE Ort, an dem
# das steht -- vorher war dieselbe Regel als Stringvergleich ueber acht Dateien
# verteilt, und genau deshalb war sie nicht aenderbar.
SITZUNGEN_JE_MENSCH = 2

def sitzungen_von(user_id: str) -> list[str]:
    """Die kanonischen Sitzungskennungen eines Menschen, Platz 1 zuerst.

    Platz 1 behaelt bewusst die alte Kennung `session:<user>` ohne Zusatz: an ihr
    haengen bereits Zuege, Episoden und Kausalketten. Umbenennen haette bedeutet,
    vier Fremdschluesseltabellen nachzuziehen -- fuer nichts.
    """
    if user_id not in CANONICAL_USER_IDS:
        return []
    return [f"session:{user_id}"] + [
        f"session:{user_id}:{n}" for n in range(2, SITZUNGEN_JE_MENSCH + 1)
    ]

def terminal_von(user_id: str, platz: int) -> str:
    grund = CANONICAL_TERMINAL_NAMES[user_id]
    return grund if platz == 1 else f"{grund}-{platz}"

def ist_kanonische_sitzung(session_id: str, user_id: str) -> bool:
    """Faellt zu, sobald etwas nicht exakt eine erlaubte Kennung ist."""
    return session_id in sitzungen_von(user_id)

def platz_von(session_id: str) -> int | None:
    for uid in CANONICAL_USER_IDS:
        ids = sitzungen_von(uid)
        if session_id in ids:
            return ids.index(session_id) + 1
    return None

class IdentityRouter:
    def __init__(self,db:UnifiedDB,clerk_map=None):
        self.db=db; self.clerk_map=clerk_map or {}
        self._bootstrap_or_assert_canonical_users()
        for uid,_,_ in CANONICAL_USERS:
            for platz in range(1, SITZUNGEN_JE_MENSCH+1):
                db.ensure_session(uid, terminal_von(uid, platz), platz=platz)
        self._normalize_terminal_sessions()
        self._bind_clerk_subjects()

    def _bootstrap_or_assert_canonical_users(self):
        rows=self.db.db.execute('SELECT user_id,display_name,rights FROM users ORDER BY user_id').fetchall()
        if not rows:
            with self.db.tx():
                for uid,name,_ in CANONICAL_USERS:
                    self.db.ensure_user(uid,name)
            rows=self.db.db.execute('SELECT user_id,display_name,rights FROM users ORDER BY user_id').fetchall()
        expected={uid:(name,'equal') for uid,name,_ in CANONICAL_USERS}
        if len(rows)!=len(expected) or {row['user_id'] for row in rows} != set(expected):
            raise PermissionError('canonical entity must contain exactly two users: gabriel and andreas')
        for row in rows:
            expected_name,expected_rights=expected[row['user_id']]
            if row['display_name'] != expected_name:
                raise PermissionError(f'canonical user display name mismatch: {row["user_id"]}')
            if row['rights'] != expected_rights:
                raise PermissionError(f'canonical user rights mismatch: {row["user_id"]}')

    def _normalize_terminal_sessions(self):
        with self.db.tx() as sql:
            for uid,_,term in CANONICAL_USERS:
                rows=sql.execute('SELECT session_id,terminal_name FROM sessions WHERE user_id=? ORDER BY created_at,session_id',(uid,)).fetchall()
                if len(rows)!=SITZUNGEN_JE_MENSCH:
                    raise PermissionError(f'canonical user must own exactly {SITZUNGEN_JE_MENSCH} permanent sessions: {uid}')
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

    def resolve(self, clerk_subject, platz: int = 1):
        """Clerk-Subjekt -> (Mensch, Sitzungskennung) fuer einen bestimmten Platz.

        Jeder Mensch hat SITZUNGEN_JE_MENSCH gleichzeitige Sitzungen. Ohne den
        Platz band resolve() alles an Platz 1 -- die zweite Sitzung existierte
        dann in der Datenbank, aber niemand kam hinein, und zwei Oberflaechen
        haetten sich um dieselbe active_turns-Zeile gestritten.

        Vorgabe 1, damit jeder bestehende Aufrufer unveraendert weiterlaeuft.
        """
        uid = self.clerk_map.get(clerk_subject)
        if uid not in CANONICAL_USER_IDS:
            raise PermissionError('unmapped Clerk subject')
        persisted = self.db.db.execute(
            'SELECT user_id FROM users WHERE clerk_subject=?', (clerk_subject,)).fetchone()
        if not persisted or persisted[0] != uid:
            raise PermissionError('Clerk subject binding mismatch')
        if not isinstance(platz, int) or not 1 <= platz <= SITZUNGEN_JE_MENSCH:
            raise PermissionError(f'invalid session slot: {platz!r}')
        return uid, self.db.ensure_session(uid, terminal_von(uid, platz), platz=platz)

    def plaetze(self, clerk_subject) -> list[dict]:
        """Alle Plaetze eines Menschen -- die Umschaltliste fuer die Oberflaeche."""
        uid = self.clerk_map.get(clerk_subject)
        if uid not in CANONICAL_USER_IDS:
            raise PermissionError('unmapped Clerk subject')
        return [{"platz": n, "session_id": sid, "terminal": terminal_von(uid, n)}
                for n, sid in enumerate(sitzungen_von(uid), start=1)]
