#!/usr/bin/env python3
"""Harmless reproduction probes for SPAWN foreign-effect-closure research.

Scope:
- temporary 0600 files only;
- child drops to uid/gid 65534 when setpriv is available;
- demonstrates inherited-FD and SCM_RIGHTS authority carriers;
- runs a deterministic abstract effect-closure fuzz model.

This is a research probe, not a production sandbox implementation.
"""
from __future__ import annotations

import array
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
    os.write(fd,b"inherited-fd-write\\n"); out["fd_write"]=True
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
    os.write(received[0],b"scm-rights-write\\n"); out["fd_write"]=True
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


def abstract_fuzz() -> dict:
    rng = random.Random(SEED)
    atoms = [
        "path_read", "path_write", "path_exec", "net_connect", "net_bind",
        "proc_spawn", "syscall_admin", "fd_protected_rw", "scm_rights_receive",
        "ambient_capability", "secret_env", "resource_unbounded",
    ]
    carrier_atoms = {"fd_protected_rw", "scm_rights_receive", "ambient_capability", "secret_env"}
    naive_accept = naive_escape = strict_accept = strict_escape = 0
    channel_counts = {x: 0 for x in sorted(carrier_atoms)}

    for _ in range(FUZZ_CASES):
        parent = {a for a in atoms if rng.random() < 0.35}
        requested = {a for a in atoms if rng.random() < 0.28}
        ambient = {a for a in carrier_atoms if rng.random() < 0.12}
        effective = requested | ambient

        # Naive model checks only non-carrier declarative effects.
        visible_req = requested - carrier_atoms
        if visible_req <= parent:
            naive_accept += 1
            leaked = effective - parent
            if leaked:
                naive_escape += 1
                for x in leaked & carrier_atoms:
                    channel_counts[x] += 1

        # Carrier-aware model requires complete effective authority subset.
        if effective <= parent:
            strict_accept += 1
            if effective - parent:
                strict_escape += 1

    return {
        "seed": SEED,
        "cases": FUZZ_CASES,
        "naive_path_only": {
            "accepted": naive_accept,
            "escapes": naive_escape,
            "escape_rate_among_accepted": naive_escape / naive_accept if naive_accept else 0.0,
            "escape_channels": channel_counts,
        },
        "carrier_aware_subset": {
            "accepted": strict_accept,
            "escapes": strict_escape,
        },
    }


def main() -> None:
    out = {
        "inherited_fd_probe": inherited_fd_probe(),
        "scm_rights_probe": scm_rights_probe(),
        "abstract_fuzz": abstract_fuzz(),
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
