from __future__ import annotations

import threading
from dataclasses import dataclass


@dataclass(frozen=True)
class TerminalActivitySnapshot:
    user_id: str
    human_clients: int
    autonomy_reserved: bool


class TerminalActivityRegistry:
    """Process-local arbitration between browser attachment and autonomy injection.

    This registry is deliberately non-durable. It owns no goal/effect/session truth; it
    only prevents terminal-input races inside one running ClayVerse service process.
    """

    CANONICAL_USERS = {"gabriel", "andreas"}

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._human_clients = {user_id: 0 for user_id in self.CANONICAL_USERS}
        self._autonomy_reserved: set[str] = set()

    @classmethod
    def _user(cls, user_id: str) -> str:
        if user_id not in cls.CANONICAL_USERS:
            raise PermissionError("terminal activity requires canonical user")
        return user_id

    def begin_human(self, user_id: str) -> bool:
        user_id = self._user(user_id)
        with self._lock:
            if user_id in self._autonomy_reserved:
                return False
            self._human_clients[user_id] += 1
            return True

    def end_human(self, user_id: str) -> None:
        user_id = self._user(user_id)
        with self._lock:
            count = self._human_clients[user_id]
            if count <= 0:
                raise RuntimeError("terminal human activity underflow")
            self._human_clients[user_id] = count - 1

    def try_reserve_autonomy(self, user_id: str) -> bool:
        user_id = self._user(user_id)
        with self._lock:
            if self._human_clients[user_id] > 0 or user_id in self._autonomy_reserved:
                return False
            self._autonomy_reserved.add(user_id)
            return True

    def release_autonomy(self, user_id: str) -> None:
        user_id = self._user(user_id)
        with self._lock:
            if user_id not in self._autonomy_reserved:
                raise RuntimeError("terminal autonomy reservation missing")
            self._autonomy_reserved.remove(user_id)

    def snapshot(self, user_id: str) -> TerminalActivitySnapshot:
        user_id = self._user(user_id)
        with self._lock:
            return TerminalActivitySnapshot(
                user_id=user_id,
                human_clients=self._human_clients[user_id],
                autonomy_reserved=user_id in self._autonomy_reserved,
            )
