#!/usr/bin/env python3
"""Scratch-only executable integration discriminator for both current daemons.

Copies of the exact live daemon sources are imported with HOME/state redirected
into a disposable root. Their real operation dispatch functions are then run
behind bridge_effect_adapter + one shared HostEffectFence. Nothing in the live
daemon installation or service state is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import multiprocessing as mp
import os
from pathlib import Path
import subprocess
import time
from types import ModuleType

from bridge_effect_adapter import Verification, execute_guarded
from host_effect_fence import HostEffectFence, LeaseBusy

GENERIC_SHA = "22d56fddd760bbda096e8cd58b8d826dbfbfd7df46155a62ef98f64d5ecdbacf"
FRANK_SHA = "836173805c8919492c1d52540c50f8b97dfd5beb8d02196d5630dbce52da342f"


def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def raw(spec: dict) -> bytes:
    return json.dumps(spec, separators=(",", ":"), sort_keys=True).encode()


def assert_sha(path: Path, want: str) -> None:
    got = h(path.read_bytes())
    if got != want:
        raise RuntimeError(f"source drift: {path}: got {got}, expected {want}")


def import_copy(path: Path, name: str, *, home: Path, frank: bool) -> ModuleType:
    os.environ["HOME"] = str(home)
    if frank:
        os.environ["LOCAL_BRIDGE_MACHINE_ID"] = "ai-core-node-shadow"
        os.environ["LOCAL_BRIDGE_OWNER"] = "shadow"
        os.environ["LOCAL_BRIDGE_STATE_DIR"] = str(home / "frank-state")
        os.environ["LOCAL_BRIDGE_CONTROL_BRANCH"] = "shadow-control-never-used"
        os.environ["LOCAL_BRIDGE_RESULTS_BRANCH"] = "shadow-results-never-used"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def daemon_body(module: ModuleType, family: str):
    if family == "generic":
        def body(spec: dict):
            op = str(spec.get("op", "exec"))
            proc, _meta = module.OPS[op](spec)
            return proc
        return body
    def body(spec: dict):
        proc, _meta = module.operate(spec)
        return proc
    return body


def readback_file(path: Path, expected: bytes):
    expected_hash = h(expected)
    def verify(_spec: dict, _result) -> Verification:
        data = path.read_bytes()
        if h(data) != expected_hash:
            raise AssertionError(f"readback mismatch for {path}")
        return Verification(h(data), f"independent scratch file readback {path.name}")
    return verify


def child_generic_hold(generic_path: str, root: str, q) -> None:
    base = Path(root)
    module = import_copy(Path(generic_path), "generic_shadow_child", home=base / "home-generic-child", frank=False)
    fence = HostEffectFence(base / "shared-concurrent", machine_id="ai-core-node")
    dest = base / "generic-hold.out"
    spec = {
        "schema": "CLAY_LOCAL_COMMAND/v1",
        "command_id": "generic-concurrent-live",
        "op": "exec",
        "effect_class": "LIVE_MUTATION",
        "command": f"sleep 1; printf generic-hold > {dest}",
    }
    try:
        result = execute_guarded(
            fence=fence, raw_command=raw(spec), holder="generic-current-daemon-shadow",
            body=daemon_body(module, "generic"), verifier=readback_file(dest, b"generic-hold")
        )
        q.put(("OK", result.outcome))
    except Exception as exc:
        q.put(("ERR", repr(exc)))
    finally:
        fence.close()


def wait_running(db_path: Path, command_id: str, timeout: float = 5.0) -> None:
    import sqlite3
    end = time.time() + timeout
    while time.time() < end:
        if db_path.exists():
            con = sqlite3.connect(db_path)
            try:
                row = con.execute("select status from effect_attempts where command_id=?", (command_id,)).fetchone()
            finally:
                con.close()
            if row and row[0] == "RUNNING":
                return
        time.sleep(0.02)
    raise RuntimeError("generic concurrent command never reached RUNNING")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generic", type=Path, required=True)
    ap.add_argument("--frank", type=Path, required=True)
    ap.add_argument("--root", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve(); root.mkdir(parents=True, exist_ok=True)
    assert_sha(args.generic, GENERIC_SHA); assert_sha(args.frank, FRANK_SHA)

    generic = import_copy(args.generic, "generic_shadow_seq", home=root / "home-generic", frank=False)
    frank = import_copy(args.frank, "frank_shadow_seq", home=root / "home-frank", frank=True)
    fence = HostEffectFence(root / "shared-sequential", machine_id="ai-core-node")

    probe = root / "probe.txt"; probe.write_bytes(b"probe")
    for family, module in (("generic", generic), ("frank", frank)):
        spec = {"schema":"CLAY_LOCAL_COMMAND/v1","command_id":f"{family}-read","op":"read_file","path":str(probe)}
        res = execute_guarded(fence=fence, raw_command=raw(spec), holder=f"{family}-shadow", body=daemon_body(module, family))
        if res.outcome != "COMPLETED_AT_NONLIVE_SCOPE": raise AssertionError(res)
        print(f"{family.upper()}_REAL_OPERATE_READONLY_ADAPTER_PASS")

    generic_out = root / "generic.out"
    gs = {"schema":"CLAY_LOCAL_COMMAND/v1","command_id":"generic-live","op":"exec","effect_class":"LIVE_MUTATION","command":f"printf generic > {generic_out}"}
    gr = execute_guarded(fence=fence, raw_command=raw(gs), holder="generic-shadow", body=daemon_body(generic,"generic"), verifier=readback_file(generic_out,b"generic"))
    if gr.outcome != "VERIFIED_SUCCEEDED": raise AssertionError(gr)
    print("GENERIC_REAL_OPERATE_LIVE_VERIFIED_PASS")

    frank_out = root / "frank.out"
    fs = {"schema":"CLAY_LOCAL_COMMAND/v1","command_id":"frank-live","op":"exec","effect_class":"LIVE_MUTATION","command":f"printf frank > {frank_out}"}
    fr = execute_guarded(fence=fence, raw_command=raw(fs), holder="frank-shadow", body=daemon_body(frank,"frank"), verifier=readback_file(frank_out,b"frank"))
    if fr.outcome != "VERIFIED_SUCCEEDED": raise AssertionError(fr)
    print("FRANK_REAL_OPERATE_LIVE_VERIFIED_PASS")
    fence.close()

    # Cross-daemon contention with actual generic op_exec holding the shared
    # fence. Only after that exact row is RUNNING does Frank attempt entry.
    q = mp.Queue()
    p = mp.Process(target=child_generic_hold, args=(str(args.generic), str(root), q))
    p.start()
    wait_running(root / "shared-concurrent" / "host_effects.sqlite3", "generic-concurrent-live")

    frank2 = import_copy(args.frank, "frank_shadow_concurrent", home=root / "home-frank-concurrent", frank=True)
    fence2 = HostEffectFence(root / "shared-concurrent", machine_id="ai-core-node")
    blocked = {"schema":"CLAY_LOCAL_COMMAND/v1","command_id":"frank-concurrent-live","op":"exec","effect_class":"LIVE_MUTATION","command":f"printf should-not-run > {root / 'blocked.out'}"}
    try:
        execute_guarded(fence=fence2, raw_command=raw(blocked), holder="frank-current-daemon-shadow", body=daemon_body(frank2,"frank"), verifier=readback_file(root/'blocked.out',b"should-not-run"))
        raise AssertionError("Frank entered while generic daemon held shared host effect lease")
    except LeaseBusy:
        print("CURRENT_GENERIC_VS_FRANK_SHARED_LEASE_EXCLUSION_PASS")
    if (root / "blocked.out").exists(): raise AssertionError("blocked Frank body executed")

    p.join(5)
    if p.exitcode != 0: raise AssertionError(f"generic child exit={p.exitcode}")
    kind, payload = q.get(timeout=2)
    if (kind, payload) != ("OK", "VERIFIED_SUCCEEDED"): raise AssertionError((kind,payload))

    # Once independent readback has verified the first daemon effect, the real
    # Frank operate path is allowed to enter the same shared authority.
    allowed = execute_guarded(fence=fence2, raw_command=raw(blocked), holder="frank-current-daemon-shadow", body=daemon_body(frank2,"frank"), verifier=readback_file(root/'blocked.out',b"should-not-run"))
    if allowed.outcome != "VERIFIED_SUCCEEDED": raise AssertionError(allowed)
    fence2.close()
    print("CURRENT_FRANK_AFTER_GENERIC_VERIFICATION_PASS")
    print("EXACT_CURRENT_DAEMONS_SHARED_FENCE_SHADOW_INTEGRATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
