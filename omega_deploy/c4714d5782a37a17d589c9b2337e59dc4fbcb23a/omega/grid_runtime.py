from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def canon(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(x: Any) -> str:
    return hashlib.sha256(canon(x).encode()).hexdigest()


CELLS = (
    "REENTRY",
    "RESEARCH",
    "WORLD_MODEL",
    "HOST_SCOUT",
    "SELF_IMPROVE",
    "FALSIFIER",
    "MAINTENANCE",
    "MEMORY_COMPRESSION",
    "EFFECT_RECONCILIATION",
    "MASTER_BRIDGE",
)


class Runtime:
    def __init__(self, root: Path, interval: float = 30.0) -> None:
        self.root = root
        self.interval = interval
        self.db = root / "omega_runtime.sqlite3"
        for name in ("inbox", "outbox", "telemetry", "receipts", "candidates", "master_bridge"):
            (root / name).mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db)
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self) -> None:
        with self.connect() as con:
            con.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS epoch(
                  epoch_id TEXT PRIMARY KEY, started_at TEXT NOT NULL, ended_at TEXT,
                  predecessor_epoch_id TEXT, reason TEXT NOT NULL, status TEXT NOT NULL,
                  state_digest TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS frame(
                  frame_id TEXT PRIMARY KEY, epoch_id TEXT NOT NULL,
                  predecessor_frame_id TEXT, created_at TEXT NOT NULL,
                  trigger_kind TEXT NOT NULL, context_json TEXT NOT NULL,
                  selected_cell TEXT, selected_score REAL,
                  broadcast_json TEXT NOT NULL, state_digest TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS proposal(
                  proposal_id TEXT PRIMARY KEY, frame_id TEXT NOT NULL, cell_id TEXT NOT NULL,
                  score REAL NOT NULL, payload_json TEXT NOT NULL, selected INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS task(
                  task_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL, state TEXT NOT NULL,
                  created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS effect_intent(
                  effect_id TEXT PRIMARY KEY, frame_id TEXT NOT NULL, organ_id TEXT NOT NULL,
                  request_sha256 TEXT NOT NULL, payload_json TEXT NOT NULL,
                  state TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                """
            )

    def _latest(self, table: str, id_col: str, time_col: str) -> str | None:
        with self.connect() as con:
            row = con.execute(f"SELECT {id_col} FROM {table} ORDER BY {time_col} DESC LIMIT 1").fetchone()
            return row[0] if row else None

    def start_epoch(self) -> str:
        prev = self._latest("epoch", "epoch_id", "started_at")
        epoch = "epoch_" + uuid.uuid4().hex
        state = self.snapshot_state()
        with self.connect() as con:
            con.execute(
                "INSERT INTO epoch VALUES(?,?,?,?,?,?,?)",
                (epoch, now(), None, prev, "runtime_start_or_reentry", "RUNNING", sha(state)),
            )
        return epoch

    def snapshot_state(self) -> dict[str, Any]:
        with self.connect() as con:
            tasks = [dict(r) for r in con.execute("SELECT task_id,state,updated_at FROM task ORDER BY updated_at DESC LIMIT 32")]
            effects = [dict(r) for r in con.execute("SELECT effect_id,organ_id,state,updated_at FROM effect_intent ORDER BY updated_at DESC LIMIT 32")]
        return {"tasks": tasks, "effects": effects, "telemetry": self.read_telemetry()}

    def read_telemetry(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for path in sorted((self.root / "telemetry").glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                out[str(data.get("organ_id") or path.stem)] = data
            except Exception:
                continue
        return out

    def ingest_inbox(self) -> int:
        n = 0
        for path in sorted((self.root / "inbox").glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                task_id = str(data.get("task_id") or "task_" + sha(data)[:24])
                t = now()
                with self.connect() as con:
                    con.execute(
                        "INSERT OR IGNORE INTO task(task_id,payload_json,state,created_at,updated_at) VALUES(?,?,?,?,?)",
                        (task_id, canon(data), "OPEN", t, t),
                    )
                path.rename(path.with_suffix(".consumed"))
                n += 1
            except Exception:
                continue
        return n

    def open_tasks(self) -> list[dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute("SELECT task_id,payload_json,created_at FROM task WHERE state='OPEN' ORDER BY created_at").fetchall()
        out = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            payload["task_id"] = row["task_id"]
            out.append(payload)
        return out

    def free_worker_available(self) -> bool:
        root = Path("/workspace/clay-global-research-entity/tools")
        if not root.exists():
            return False
        try:
            import sys
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))
            from run_free_go_swarm import PROVIDERS, provider_execution_admitted
            return any(provider_execution_admitted(spec) for spec in PROVIDERS)
        except Exception:
            return False

    def cell_proposals(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        tasks = context["tasks"]
        telemetry = context["telemetry"]
        pending_unknown = any(e.get("state") == "UNKNOWN" for e in context["state"].get("effects", []))
        free = context["free_worker_available"]
        stale_hosts = [k for k,v in telemetry.items() if str(v.get("health","UNKNOWN")).upper() in {"UNKNOWN","RED"}]

        base = {
            "REENTRY": 0.30,
            "RESEARCH": 0.25 + (0.25 if free else 0.0),
            "WORLD_MODEL": 0.22,
            "HOST_SCOUT": 0.20 + min(0.35, 0.12 * len(stale_hosts)),
            "SELF_IMPROVE": 0.28 if not tasks else 0.18,
            "FALSIFIER": 0.24,
            "MAINTENANCE": 0.18,
            "MEMORY_COMPRESSION": 0.16,
            "EFFECT_RECONCILIATION": 0.75 if pending_unknown else 0.10,
            "MASTER_BRIDGE": 0.20,
        }
        if tasks:
            base["RESEARCH"] += 0.10
            base["HOST_SCOUT"] += 0.10
            base["FALSIFIER"] += 0.08
        proposals = []
        for cell in CELLS:
            proposals.append({
                "proposal_id": "prop_" + uuid.uuid4().hex,
                "cell_id": cell,
                "score": round(base[cell], 6),
                "payload": self._proposal_payload(cell, context),
            })
        return proposals

    def _proposal_payload(self, cell: str, context: dict[str, Any]) -> dict[str, Any]:
        tasks = context["tasks"]
        if cell == "REENTRY":
            return {"kind":"reentry","action":"refresh_current_projection"}
        if cell == "RESEARCH":
            return {"kind":"research","free_worker_available":context["free_worker_available"],"task":tasks[0] if tasks else None}
        if cell == "HOST_SCOUT":
            return {"kind":"organ_route","task":tasks[0] if tasks else {"task_id":"background_host_scout","required_capabilities":["local_state"]}}
        if cell == "SELF_IMPROVE":
            return {"kind":"self_improve","action":"generate_candidate_only","promotion":"separate_gate_required"}
        if cell == "FALSIFIER":
            return {"kind":"falsifier","target":tasks[0] if tasks else "current_runtime_assumptions"}
        if cell == "MASTER_BRIDGE":
            return {"kind":"master_bridge","action":"publish_state_and_open_questions"}
        if cell == "EFFECT_RECONCILIATION":
            return {"kind":"reconcile_unknown_effects"}
        return {"kind":cell.lower(),"action":"bounded_background_maintenance"}

    def emit_outbox(self, kind: str, payload: dict[str, Any]) -> Path:
        item = {
            "schema":"OMEGA_OUTBOX/v1",
            "message_id":"msg_"+uuid.uuid4().hex,
            "created_at":now(),
            "kind":kind,
            "payload":payload,
        }
        path = self.root / "outbox" / f"{item['message_id']}.json"
        path.write_text(json.dumps(item,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        return path

    def realize(self, selected: dict[str, Any], frame_id: str) -> dict[str, Any]:
        cell = selected["cell_id"]
        payload = selected["payload"]
        if cell == "HOST_SCOUT":
            self.emit_outbox("GRID_ORGAN_REQUEST", {"frame_id":frame_id, **payload})
            return {"broadcast":"host organ routing requested","outbox":True}
        if cell == "RESEARCH":
            if payload.get("free_worker_available"):
                self.emit_outbox("FREE_WORKER_REQUEST", {"frame_id":frame_id, **payload})
                return {"broadcast":"free worker research requested","outbox":True}
            self.emit_outbox("RESEARCH_ADMISSION_NEEDED", {"frame_id":frame_id, **payload})
            return {"broadcast":"research lane unavailable; admission request emitted","outbox":True}
        if cell == "MASTER_BRIDGE":
            self.emit_outbox("MASTER_COGNITION_UPDATE", {"frame_id":frame_id,"state":self.snapshot_state()})
            return {"broadcast":"master bridge state update emitted","outbox":True}
        if cell == "SELF_IMPROVE":
            candidate = {
                "candidate_id":"cand_"+uuid.uuid4().hex,
                "created_at":now(),
                "state":"PROPOSED",
                "rule":"candidate_only_no_self_promotion",
                "hypothesis":"runtime can improve one measurable bottleneck without weakening alignment/provenance",
            }
            p=self.root/"candidates"/f"{candidate['candidate_id']}.json"
            p.write_text(json.dumps(candidate,indent=2)+"\n")
            return {"broadcast":"self-improvement candidate opened","candidate":candidate["candidate_id"]}
        return {"broadcast":payload}

    def frame(self, epoch_id: str, trigger: str = "HEARTBEAT") -> str:
        self.ingest_inbox()
        state = self.snapshot_state()
        context = {
            "state":state,
            "tasks":self.open_tasks(),
            "telemetry":state["telemetry"],
            "free_worker_available":self.free_worker_available(),
        }
        proposals = self.cell_proposals(context)
        selected = max(proposals, key=lambda p: p["score"])
        frame_id = "frame_" + uuid.uuid4().hex
        prev = self._latest("frame", "frame_id", "created_at")
        result = self.realize(selected, frame_id)
        with self.connect() as con:
            con.execute(
                "INSERT INTO frame VALUES(?,?,?,?,?,?,?,?,?,?)",
                (frame_id,epoch_id,prev,now(),trigger,canon(context),selected["cell_id"],selected["score"],canon(result),sha(self.snapshot_state())),
            )
            for p in proposals:
                con.execute(
                    "INSERT INTO proposal VALUES(?,?,?,?,?,?)",
                    (p["proposal_id"],frame_id,p["cell_id"],p["score"],canon(p["payload"]),1 if p is selected else 0),
                )
        status={"schema":"OMEGA_GRID_STATUS/v1","updated_at":now(),"epoch_id":epoch_id,"frame_id":frame_id,"selected":selected,"result":result}
        (self.root/"STATUS.json").write_text(json.dumps(status,indent=2,ensure_ascii=False)+"\n")
        return frame_id

    def run_forever(self) -> None:
        epoch = self.start_epoch()
        while True:
            try:
                self.frame(epoch)
            except Exception as exc:
                self.emit_outbox("RUNTIME_ERROR", {"error":f"{type(exc).__name__}:{exc}"})
            time.sleep(self.interval)


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=os.getenv("OMEGA_RUNTIME_ROOT","/workspace/omega_runtime"))
    ap.add_argument("--interval",type=float,default=float(os.getenv("OMEGA_GRID_INTERVAL","30")))
    ap.add_argument("--once",action="store_true")
    args=ap.parse_args()
    rt=Runtime(Path(args.root),args.interval)
    if args.once:
        epoch=rt.start_epoch(); rt.frame(epoch,"MANUAL_ONCE"); return 0
    rt.run_forever(); return 0


if __name__ == "__main__":
    raise SystemExit(main())
