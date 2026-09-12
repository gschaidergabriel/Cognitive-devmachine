import concurrent.futures
import json
import sqlite3
import time
from pathlib import Path

from omega.nonblocking_relay import NonBlockingRelay, RelayCandidate, choose_submit_candidates


class FakeStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        with sqlite3.connect(self.path) as con:
            con.execute("CREATE TABLE relay_ledger(effect_id TEXT PRIMARY KEY, organ_id TEXT, state TEXT)")

    def connect(self):
        return sqlite3.connect(self.path)


class FakeRelay:
    def __init__(self, root: Path, delays: dict[str, float] | None = None) -> None:
        self.runtime_root = root
        self.store = FakeStore(root / "fake.db")
        self.delays = delays or {}
        self.calls: list[str] = []
        (root / "outbox").mkdir(parents=True, exist_ok=True)
        (root / "relay_results").mkdir(parents=True, exist_ok=True)

    def process_intent(self, path: Path):
        payload = json.loads(path.read_text(encoding="utf-8"))
        effect_id = payload["effect_id"]
        time.sleep(self.delays.get(effect_id, 0.02))
        self.calls.append(effect_id)
        with self.store.connect() as con:
            con.execute(
                "INSERT OR REPLACE INTO relay_ledger(effect_id,organ_id,state) VALUES(?,?,?)",
                (effect_id, payload["organ_id"], "COMPLETED"),
            )
        return {"state": "COMPLETED", "effect_id": effect_id}


def _intent(root: Path, effect_id: str, organ_id: str) -> None:
    (root / "outbox" / f"{effect_id}.json").write_text(
        json.dumps({"schema": "OMEGA_GRID_EFFECT_INTENT/v1", "effect_id": effect_id, "organ_id": organ_id}),
        encoding="utf-8",
    )


def test_scheduler_selects_cross_organ_parallelism_only():
    candidates = [
        RelayCandidate(Path("a"), "e1", "host:ai-core-node"),
        RelayCandidate(Path("b"), "e2", "host:ai-core-node"),
        RelayCandidate(Path("c"), "e3", "host:andreas-maco"),
    ]
    selected = choose_submit_candidates(candidates, inflight_organs=(), per_organ_limit=1, capacity=4)
    assert [item.effect_id for item in selected] == ["e1", "e3"]


def test_stalled_organ_does_not_block_other_organ(tmp_path: Path):
    relay = FakeRelay(tmp_path, delays={"effect_slow": 0.30, "effect_fast": 0.01})
    _intent(tmp_path, "effect_slow", "host:andreas-maco")
    _intent(tmp_path, "effect_fast", "host:ai-core-node")
    scheduler = NonBlockingRelay(relay, max_workers=2, per_organ_limit=1, interval=0.01, long_running_seconds=0.05)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        started = time.monotonic()
        first = scheduler.step(pool)
        assert time.monotonic() - started < 0.10
        assert set(first["submitted_effect_ids"]) == {"effect_slow", "effect_fast"}

        deadline = time.monotonic() + 0.20
        while time.monotonic() < deadline:
            time.sleep(0.02)
            status = scheduler.step(pool)
            if "effect_fast" in relay.calls and "effect_slow" not in relay.calls:
                assert any(row["effect_id"] == "effect_slow" for row in status["inflight"])
                break
        else:
            raise AssertionError("fast organ did not complete while slow organ remained inflight")


def test_same_organ_remains_serial(tmp_path: Path):
    relay = FakeRelay(tmp_path, delays={"effect_1": 0.08, "effect_2": 0.01})
    _intent(tmp_path, "effect_1", "host:ai-core-node")
    _intent(tmp_path, "effect_2", "host:ai-core-node")
    scheduler = NonBlockingRelay(relay, max_workers=4, per_organ_limit=1, interval=0.01)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        first = scheduler.step(pool)
        assert len(first["submitted_effect_ids"]) == 1
        assert len(scheduler.inflight) == 1
        assert scheduler.step(pool)["submitted_effect_ids"] == []
        deadline = time.monotonic() + 1.0
        while len(relay.calls) < 2 and time.monotonic() < deadline:
            time.sleep(0.02)
            scheduler.step(pool)

    assert relay.calls == ["effect_1", "effect_2"]


def test_terminal_and_dispatching_states_are_never_auto_resubmitted(tmp_path: Path):
    relay = FakeRelay(tmp_path)
    for effect_id, state in [
        ("effect_unknown", "UNKNOWN"),
        ("effect_dispatching", "DISPATCHING"),
        ("effect_completed", "COMPLETED"),
    ]:
        _intent(tmp_path, effect_id, "host:ai-core-node")
        with relay.store.connect() as con:
            con.execute(
                "INSERT INTO relay_ledger(effect_id,organ_id,state) VALUES(?,?,?)",
                (effect_id, "host:ai-core-node", state),
            )
    scheduler = NonBlockingRelay(relay, max_workers=2, per_organ_limit=1)
    assert scheduler.discover() == []
    assert relay.calls == []
