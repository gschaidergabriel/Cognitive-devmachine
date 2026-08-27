#!/usr/bin/env python3
"""Harmless reproduction probes for SPAWN foreign-effect-closure research.

Scope:
- temporary 0600 files only;
- child drops to uid/gid 65534 when setpriv is available;
- demonstrates inherited-FD and SCM_RIGHTS authority carriers;
- reproduces the deterministic abstract effect-closure fuzz model used in this run.

This is a research probe, not a production sandbox implementation.
"""
from __future__ import annotations

import array
import collections
import json
import os
import random
import shutil
import socket
import subprocess
import sys
import tempfile

SEED = 202608091741
FUZZ_CASES = 200_000
PATH_ATOMS = {
    "fs_read_workspace", "fs_write_workspace", "fs_truncate_workspace",
    "fs_read_protected", "fs_write_protected", "fs_truncate_protected",
    "net_connect_https", "net_connect_arbitrary",
}
CARRIER_ATOMS = {
    "fd_protected_rw", "scm_rights_receive", "ambient_capability", "secret_env",
}
KERNEL_ATOMS = {"spawn", "signal_external", "device_ioctl", "ptrace_external"}
RESOURCE_ATOMS = {"pids_unbounded", "memory_unbounded", "cpu_unbounded", "io_unbounded"}
UNIVERSE = sorted(PATH_ATOMS | CARRIER_ATOMS | KERNEL_ATOMS | RESOURCE_ATOMS)


def nobody_prefix() -> list[str]:
    setpriv = shutil.which("setpriv")
    if not setpriv:
        raise RuntimeError("setpriv is required for privilege-drop probes")
    return [setpriv, "--reuid=65534", "--regid=65534", "--clear-groups"]


def inherited_fd_probe() -> dict:
    fd, path = tempfile.mkstemp(prefix="clay_fd_escape_")
    try:
        os.fchmod(fd, 0o600)
        os.write(fd, b"parent\n")
        child = r'''
import json, os, sys
path=sys.argv[1]; fd=int(sys.argv[2])
out={"path_open":None,"fd_write":None}
try:
    x=os.open(path,os.O_WRONLY|os.O_APPEND); os.close(x); out["path_open"]=True
except Exception as e:
    out["path_open"]=False; out["path_error"]=type(e).__name__
try:
    os.write(fd,b"inherited-fd-write\n"); out["fd_write"]=True
except Exception as e:
    out["fd_write"]=False; out["fd_error"]=type(e).__name__
print(json.dumps(out,sort_keys=True))
'''
        p = subprocess.run(
            nobody_prefix() + [sys.executable, "-c", child, path, str(fd)],
            pass_fds=(fd,), text=True, capture_output=True, check=False,
        )
        os.lseek(fd, 0, os.SEEK_SET)
        body = os.read(fd, 4096).decode(errors="replace")
        return {"returncode": p.returncode, "child": json.loads(p.stdout), "file_body": body}
    finally:
        os.close(fd)
        try: os.unlink(path)
        except FileNotFoundError: pass


def scm_rights_probe() -> dict:
    fd, path = tempfile.mkstemp(prefix="clay_scm_escape_")
    a, b = socket.socketpair()
    try:
        os.fchmod(fd, 0o600)
        os.write(fd, b"parent\n")
        child = r'''
import array, json, os, socket, sys
sock=socket.socket(fileno=int(sys.argv[1]))
msg, anc, flags, addr=sock.recvmsg(1, socket.CMSG_SPACE(array.array("i").itemsize))
received=[]
for level, typ, data in anc:
    if level==socket.SOL_SOCKET and typ==socket.SCM_RIGHTS:
        fds=array.array("i"); fds.frombytes(data[:len(data)-(len(data)%fds.itemsize)]); received.extend(fds)
out={"received_fd":bool(received),"fd_write":False}
if received:
    os.write(received[0],b"scm-rights-write\n"); out["fd_write"]=True
    for x in received: os.close(x)
print(json.dumps(out,sort_keys=True))
'''
        p = subprocess.Popen(
            nobody_prefix() + [sys.executable, "-c", child, str(b.fileno())],
            pass_fds=(b.fileno(),), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        b.close()
        fds = array.array("i", [fd])
        a.sendmsg([b"F"], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, fds)])
        stdout, stderr = p.communicate(timeout=10)
        os.lseek(fd, 0, os.SEEK_SET)
        body = os.read(fd, 4096).decode(errors="replace")
        return {"returncode": p.returncode, "child": json.loads(stdout), "file_body": body, "stderr": stderr}
    finally:
        a.close()
        try: b.close()
        except Exception: pass
        os.close(fd)
        try: os.unlink(path)
        except FileNotFoundError: pass


def naive_path_sandbox(parent_allowed: set[str], child_requested: set[str], ambient: set[str]):
    requested_path = child_requested & PATH_ATOMS
    if not requested_path <= parent_allowed:
        return False, set()
    effective = requested_path | set(ambient)
    return True, effective


def carrier_aware_broker(parent_allowed: set[str], child_requested: set[str], ambient: set[str]):
    if not child_requested <= parent_allowed:
        return False, set()
    admitted_ambient = set(ambient) & parent_allowed
    effective = set(child_requested) | admitted_ambient
    if not effective <= parent_allowed:
        return False, set()
    return True, effective


def abstract_fuzz() -> dict:
    rng = random.Random(SEED)
    naive_accepts = naive_escapes = safe_accepts = safe_escapes = 0
    escape_counter = collections.Counter()
    for _ in range(FUZZ_CASES):
        parent = {a for a in UNIVERSE if rng.random() < 0.22}
        child = {a for a in UNIVERSE if rng.random() < 0.16}
        ambient = {a for a in CARRIER_ATOMS if rng.random() < 0.08}

        ok, eff = naive_path_sandbox(parent, child, ambient)
        if ok:
            naive_accepts += 1
            leaked = eff - parent
            if leaked:
                naive_escapes += 1
                for a in leaked:
                    escape_counter[a] += 1

        ok2, eff2 = carrier_aware_broker(parent, child, ambient)
        if ok2:
            safe_accepts += 1
            if eff2 - parent:
                safe_escapes += 1

    return {
        "seed": SEED,
        "cases": FUZZ_CASES,
        "naive_accepts": naive_accepts,
        "naive_escapes": naive_escapes,
        "naive_escape_rate_among_accepts": naive_escapes / naive_accepts,
        "carrier_aware_accepts": safe_accepts,
        "carrier_aware_escapes": safe_escapes,
        "carrier_aware_escape_rate_among_accepts": 0 if safe_accepts == 0 else safe_escapes / safe_accepts,
        "top_escape_channels": escape_counter.most_common(),
    }


def main() -> None:
    print(json.dumps({
        "inherited_fd_probe": inherited_fd_probe(),
        "scm_rights_probe": scm_rights_probe(),
        "abstract_fuzz": abstract_fuzz(),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
