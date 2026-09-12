#!/usr/bin/env python3
from __future__ import annotations
import argparse, fcntl, hashlib, json, os, sqlite3, subprocess, sys, time, traceback, uuid
from pathlib import Path

BASE = Path("/workspace/frankgrid10-organ")
CODE = BASE / "code" / "frankgrid10_v2.py"
DB = BASE / "state" / "frankgrid10.sqlite3"
IPC = BASE / "ipc"
INBOX = IPC / "inbox"
PROCESSING = IPC / "processing"
OUTBOX = IPC / "outbox"
RECEIPTS = IPC / "receipts"
DEAD = IPC / "deadletter"
RUN = BASE / "run"
LOGS = BASE / "logs"
LOCK = RUN / "organ-daemon.lock"
HEART = RUN / "heartbeat.json"
EXPECTED_SOURCE_SHA = "60ec27675b2900e9f71f3c22f50cb3ca28231272d4f3bb7ec016b3127608a03e"
SCHEMA = "FRANKGRID10_ORGAN_COMMAND/v1"
RECEIPT_SCHEMA = "FRANKGRID10_ORGAN_RECEIPT/v1"


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def atomic_json(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + "." + uuid.uuid4().hex + ".tmp")
    data = (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def verify_runtime():
    if not CODE.is_file():
        raise RuntimeError("SOURCE_MISSING")
    got = sha_bytes(CODE.read_bytes())
    if got != EXPECTED_SOURCE_SHA:
        raise RuntimeError(f"SOURCE_HASH_MISMATCH:{got}")
    c = sqlite3.connect(DB)
    try:
        integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
        schema = c.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()
    finally:
        c.close()
    if integrity != "ok":
        raise RuntimeError(f"SQLITE_INTEGRITY:{integrity}")
    if not schema or schema[0] != "FRANKGRID10/v2":
        raise RuntimeError(f"SCHEMA_MISMATCH:{schema}")
    return {"source_sha256": got, "sqlite_integrity": integrity, "db_schema": schema[0]}


def cli(args, timeout=90):
    cmd = [sys.executable, str(CODE), "--db", str(DB)] + args
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(f"CLI_RC_{p.returncode}: {p.stderr[-4000:]}")
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"stdout": p.stdout, "stderr": p.stderr, "returncode": p.returncode}


def command_args(obj):
    op = str(obj.get("op", "")).upper()
    if op == "PRE":
        prompt = obj.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("PRE_REQUIRES_PROMPT")
        a = ["pre", "--prompt", prompt]
        if obj.get("ablate"):
            if not isinstance(obj["ablate"], list):
                raise ValueError("ABLATE_MUST_BE_LIST")
            a += ["--ablate", ",".join(map(str, obj["ablate"]))]
        return a
    if op == "POST":
        tid, response = obj.get("turn_id"), obj.get("response")
        if not isinstance(tid, str) or not tid:
            raise ValueError("POST_REQUIRES_TURN_ID")
        if not isinstance(response, str):
            raise ValueError("POST_REQUIRES_RESPONSE")
        return ["post", "--turn-id", tid, "--response", response]
    if op == "INGEST":
        role, content = obj.get("role"), obj.get("content")
        if not isinstance(role, str) or not role:
            raise ValueError("INGEST_REQUIRES_ROLE")
        if not isinstance(content, str) or not content:
            raise ValueError("INGEST_REQUIRES_CONTENT")
        a = ["ingest", "--role", role,
             "--source-kind", str(obj.get("source_kind", "ORGAN_INPUT")),
             "--content", content,
             "--confidence", str(float(obj.get("confidence", 0.5))),
             "--salience", str(float(obj.get("salience", 0.5)))]
        if obj.get("source_ref"):
            a += ["--source-ref", str(obj["source_ref"])]
        return a
    if op == "STATUS":
        return ["status"]
    if op == "CHECKPOINT":
        out = BASE / "state" / "checkpoints" / (str(obj.get("name") or ("cp-" + uuid.uuid4().hex)) + ".json")
        out.parent.mkdir(parents=True, exist_ok=True)
        return ["checkpoint", "--out", str(out)]
    if op == "SELFTEST":
        return ["selftest"]
    raise ValueError("UNSUPPORTED_OP")


def handle(path: Path, seq: int):
    raw = path.read_bytes()
    cmd_sha = sha_bytes(raw)
    obj = json.loads(raw)
    if obj.get("schema") != SCHEMA:
        raise ValueError("BAD_SCHEMA")
    cid = obj.get("command_id")
    if not isinstance(cid, str) or not cid or "/" in cid or ".." in cid:
        raise ValueError("BAD_COMMAND_ID")
    args = command_args(obj)
    pre = verify_runtime()
    t0 = time.time()
    result = cli(args, timeout=min(120, max(5, int(obj.get("timeout_seconds", 90)))))
    post = verify_runtime()
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "command_id": cid,
        "command_sha256": cmd_sha,
        "op": str(obj["op"]).upper(),
        "status": "PASS",
        "started_at": t0,
        "finished_at": time.time(),
        "heartbeat_seq": seq,
        "truth_authority": False,
        "effect_authority": False,
        "runtime_pre": pre,
        "runtime_post": post,
        "result": result,
    }
    atomic_json(OUTBOX / (cid + ".json"), receipt)
    atomic_json(RECEIPTS / (cid + ".json"), receipt)


def heartbeat(seq: int, status="RUNNING", error=None):
    obj = {
        "schema": "FRANKGRID10_ORGAN_HEARTBEAT/v1",
        "seq": seq,
        "pid": os.getpid(),
        "wall_time": time.time(),
        "monotonic": time.monotonic(),
        "status": status,
        "truth_authority": False,
        "effect_authority": False,
    }
    if error:
        obj["error"] = error
    atomic_json(HEART, obj)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--poll", type=float, default=0.5)
    ns = ap.parse_args()
    for p in (INBOX, PROCESSING, OUTBOX, RECEIPTS, DEAD, RUN, LOGS):
        p.mkdir(parents=True, exist_ok=True)
    lf = open(LOCK, "a+")
    try:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("ALREADY_RUNNING", file=sys.stderr)
        return 73
    verify_runtime()
    st = cli(["selftest"], timeout=120)
    if st.get("selftest") != "PASS" or st.get("checks_passed") != st.get("checks_total"):
        raise RuntimeError("STARTUP_SELFTEST_FAILED")
    seq = 0
    heartbeat(seq, "RUNNING")
    while True:
        seq += 1
        if seq % 4 == 0:
            heartbeat(seq, "RUNNING")
        for p in sorted(INBOX.glob("*.json")):
            q = PROCESSING / p.name
            try:
                os.replace(p, q)
            except FileNotFoundError:
                continue
            try:
                handle(q, seq)
                q.unlink(missing_ok=True)
            except Exception as e:
                err = {
                    "schema": RECEIPT_SCHEMA,
                    "status": "FAIL",
                    "file": q.name,
                    "error": type(e).__name__ + ":" + str(e),
                    "trace": traceback.format_exc()[-6000:],
                    "wall_time": time.time(),
                    "truth_authority": False,
                    "effect_authority": False,
                }
                try:
                    atomic_json(DEAD / (q.stem + "-" + uuid.uuid4().hex[:8] + ".json"), err)
                finally:
                    q.unlink(missing_ok=True)
        time.sleep(max(0.1, ns.poll))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        try:
            heartbeat(-1, "FAILED", type(e).__name__ + ":" + str(e))
        except Exception:
            pass
        raise
