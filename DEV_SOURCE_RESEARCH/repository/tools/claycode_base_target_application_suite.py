#!/usr/bin/env python3
"""Contract-shaped ten-application ClayCode acceptance suite for Andreas' Ubuntu host.

This runner cannot self-promote from CI/container execution. It requires the uncommitted
~/.claycode/ANDREAS_TARGET_HOST marker and emits rows shaped exactly for
ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json. Nine application classes have concrete
compiler/runtime execution paths here. FULL_FRANK_HANDOFF remains fail-closed until a
separate full production handoff receipt exists.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from claycode_base_pure_toolchain import VERSION as PURE_VERSION, ClayError, compile_source, differential
from claycode_base_runtime import ClayRuntime, RUNTIME_VERSION
from claycode_base_stdlib_extensions import STDLIB_EXT_VERSION, install

TARGET = "ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM"
MARKER = Path.home() / ".claycode/ANDREAS_TARGET_HOST"
OUT = ROOT / "research_entity/claycode/target/ANDREAS_UBUNTU_APPLICATIONS.json"
FULL_FRANK = ROOT / "research_entity/claycode/target/FULL_FRANK_HANDOFF_PRODUCTION_RECEIPT.json"
FRANK_COMPONENT_TOOL = ROOT / "tools/claycode_wp13_frank_handoff_validation.py"
FRANK_COMPONENT_RECEIPT = ROOT / "research_entity/claycode/autonomous/WP13_FRANK_PACKET_SCORE_HANDOFF_RECEIPT.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def file_hash(*paths: Path) -> str:
    h = hashlib.sha256()
    for p in paths:
        h.update(str(p.relative_to(ROOT)).encode()); h.update(b"\0"); h.update(p.read_bytes()); h.update(b"\0")
    return h.hexdigest()


def host_gate() -> dict[str, bool]:
    release = {}
    p = Path("/etc/os-release")
    if p.exists():
        for line in p.read_text(errors="replace").splitlines():
            if "=" in line:
                k, v = line.split("=", 1); release[k] = v.strip().strip('"')
    cgroup = Path("/proc/1/cgroup").read_text(errors="replace").lower() if Path("/proc/1/cgroup").exists() else ""
    return {
        "linux": platform.system() == "Linux",
        "ubuntu": release.get("ID") == "ubuntu",
        "not_github_actions": os.environ.get("GITHUB_ACTIONS", "").lower() != "true",
        "not_ci": os.environ.get("CI", "").lower() not in {"1", "true", "yes"},
        "no_dockerenv": not Path("/.dockerenv").exists(),
        "no_known_container_cgroup": not any(x in cgroup for x in ("docker", "containerd", "kubepods", "lxc")),
        "target_marker": MARKER.exists() and MARKER.read_text(errors="replace").strip() == TARGET,
    }


def row(*, passed: bool, spec: Any, semantic: Any, compiler_runtime: str, artifact_hash: str,
        test_id: str, expected: Any, observed: Any, negative: Any, authority: bool) -> dict[str, Any]:
    return {
        "pass": bool(passed),
        "source_or_program_hash": sha(canon(spec)),
        "semantic_or_ir_hash": sha(canon(semantic)),
        "compiler_runtime_version": compiler_runtime,
        "target_artifact_hash": artifact_hash,
        "execution_command_or_test_id": test_id,
        "expected": expected,
        "observed": observed,
        "negative_or_failure_path": negative,
        "authority_boundary_preserved": bool(authority),
    }


def pure_app(source: str, entry: str, args: list[Any], expected: str, test_id: str) -> dict[str, Any]:
    typed = compile_source(source)
    d = differential(typed, entry, args)
    negative_ok = False
    try:
        compile_source("module bad\nfn main(x:Int)->Int=x+false\n")
    except Exception:
        negative_ok = True
    return row(
        passed=d["match"] and d["native_stdout"] == expected and negative_ok,
        spec={"source": source, "entry": entry, "args": args},
        semantic={"semantic_hash": typed["semantic_hash"], "expected_stdout": expected},
        compiler_runtime=PURE_VERSION,
        artifact_hash=d["generated_c_sha256"],
        test_id=test_id,
        expected=expected,
        observed=d["native_stdout"],
        negative={"ill_typed_program_rejected": negative_ok},
        authority=True,
    )


def runtime_artifact_hash() -> str:
    return file_hash(ROOT / "tools/claycode_base_runtime.py", ROOT / "tools/claycode_base_stdlib_extensions.py")


def frank_component_row() -> dict[str, Any]:
    if not FRANK_COMPONENT_TOOL.exists():
        return row(passed=False, spec={"missing": str(FRANK_COMPONENT_TOOL)}, semantic={}, compiler_runtime=PURE_VERSION,
                   artifact_hash="0" * 64, test_id="FRANK_COMPONENT_TOOL_MISSING", expected="PASS", observed="MISSING",
                   negative={"missing_tool": True}, authority=True)
    cp = subprocess.run([sys.executable, str(FRANK_COMPONENT_TOOL.relative_to(ROOT))], cwd=ROOT, text=True, capture_output=True, timeout=300, check=False)
    if not FRANK_COMPONENT_RECEIPT.exists():
        return row(passed=False, spec={"tool": str(FRANK_COMPONENT_TOOL.relative_to(ROOT))}, semantic={}, compiler_runtime=PURE_VERSION,
                   artifact_hash=sha(cp.stdout.encode()), test_id="tools/claycode_wp13_frank_handoff_validation.py", expected="receipt", observed="missing",
                   negative={"returncode": cp.returncode, "stderr_tail": cp.stderr[-1000:]}, authority=True)
    r = json.loads(FRANK_COMPONENT_RECEIPT.read_text())
    generated = sorted({x.get("generated_c_sha256") for x in r.get("rows", []) if x.get("generated_c_sha256")})
    target_hash = sha(canon(generated))
    passed = cp.returncode == 0 and r.get("pass") is True and r.get("semantic_mismatches") == 0 and r.get("native_mismatches") == 0
    return {
        "pass": passed,
        "source_or_program_hash": r.get("clay_source_sha256") or sha(canon({"receipt": sha(FRANK_COMPONENT_RECEIPT.read_bytes())})),
        "semantic_or_ir_hash": r.get("clay_semantic_hash") or sha(canon(r.get("rows", []))),
        "compiler_runtime_version": PURE_VERSION,
        "target_artifact_hash": target_hash,
        "execution_command_or_test_id": "tools/claycode_wp13_frank_handoff_validation.py",
        "expected": {"semantic_mismatches": 0, "native_mismatches": 0},
        "observed": {"semantic_mismatches": r.get("semantic_mismatches"), "native_mismatches": r.get("native_mismatches"), "vectors": r.get("vectors")},
        "negative_or_failure_path": {"reference_differential": True, "returncode": cp.returncode},
        "authority_boundary_preserved": True,
    }


def full_frank_row() -> dict[str, Any]:
    if not FULL_FRANK.exists():
        return row(
            passed=False,
            spec={"required_receipt": str(FULL_FRANK.relative_to(ROOT))},
            semantic={"requirement": "actual frozen FRANK H2/H3 handoff, no bounded proxy"},
            compiler_runtime=f"{PURE_VERSION}|{RUNTIME_VERSION}|{STDLIB_EXT_VERSION}",
            artifact_hash="0" * 64,
            test_id="FULL_FRANK_HANDOFF_PRODUCTION_RECEIPT_REQUIRED",
            expected={"pass": True, "h2_h3_handoff_ready": True, "semantic_escape_hatches": []},
            observed={"receipt": "missing"},
            negative={"bounded_packet_score_proxy_does_not_count": True},
            authority=True,
        )
    r = json.loads(FULL_FRANK.read_text())
    passed = (
        r.get("pass") is True and r.get("target_host") == TARGET and r.get("h2_h3_handoff_ready") is True
        and r.get("semantic_escape_hatches") in ([], 0, None)
    )
    return row(
        passed=passed,
        spec={"receipt_path": str(FULL_FRANK.relative_to(ROOT)), "receipt_sha256": sha(FULL_FRANK.read_bytes())},
        semantic={"frozen_frank_source_hashes": r.get("frozen_frank_source_hashes"), "claycode_source_hashes": r.get("claycode_source_hashes")},
        compiler_runtime=str(r.get("compiler_runtime_version") or f"{PURE_VERSION}|{RUNTIME_VERSION}"),
        artifact_hash=str(r.get("target_artifact_hash") or sha(FULL_FRANK.read_bytes())),
        test_id="FULL_FRANK_HANDOFF_PRODUCTION_RECEIPT",
        expected={"pass": True, "h2_h3_handoff_ready": True, "semantic_escape_hatches": []},
        observed={"pass": r.get("pass"), "h2_h3_handoff_ready": r.get("h2_h3_handoff_ready"), "semantic_escape_hatches": r.get("semantic_escape_hatches")},
        negative={"production_chain_receipts": r.get("production_chain_receipts")},
        authority=r.get("authority_boundary_preserved", True) is True,
    )


def main() -> int:
    gates = host_gate()
    if not all(gates.values()):
        print(json.dumps({"error": "TARGET_HOST_GATE_FAILED", "checks": gates}, indent=2)); return 3
    impl_hash = runtime_artifact_hash()
    rows: dict[str, dict[str, Any]] = {}

    rows["CLI"] = pure_app("module app.cli\nfn main(x:Int)->Int=x+1\n", "main", [41], "42", "APP-01_CLI_NATIVE")

    with tempfile.TemporaryDirectory(prefix="claycode_target_apps_") as td:
        rt = install(ClayRuntime(td))

        net = rt.mint_capability("net.loopback", {"host": "127.0.0.1", "routes": ["/"], "max_body_bytes": 4096})
        body = "<html><body>ClayCode BASE</body></html>"
        got = rt.invoke("http.loopback_roundtrip", net, "/", body)
        route_denied = False
        try: rt.invoke("http.loopback_roundtrip", net, "/forbidden", body)
        except Exception: route_denied = True
        rows["HTTP_WEBSITE"] = row(passed=got["status"] == 200 and got["matched"] and route_denied,
            spec={"route": "/", "body": body}, semantic={"status": 200, "body_sha256": sha(body.encode())},
            compiler_runtime=f"{RUNTIME_VERSION}|{STDLIB_EXT_VERSION}", artifact_hash=impl_hash,
            test_id="APP-02_HTTP_LOOPBACK_REAL_SOCKET", expected={"status": 200, "matched": True}, observed=got,
            negative={"forbidden_route_rejected": route_denied}, authority=True)

        db = rt.mint_capability("db.sqlite", {"prefix": "db"})
        got = rt.invoke("db.sqlite_transaction", db, "app.db", [
            ("CREATE TABLE kv(k TEXT PRIMARY KEY,v INTEGER)", ()),
            ("INSERT INTO kv(k,v) VALUES(?,?)", ("answer", 42)),
            ("SELECT v FROM kv WHERE k=?", ("answer",)),
        ])
        rollback = False
        try:
            rt.invoke("db.sqlite_transaction", db, "app.db", [("INSERT INTO kv(k,v) VALUES(?,?)", ("x", 1)), ("INSERT INTO missing_table(x) VALUES(1)", ())])
        except Exception: rollback = True
        after = rt.invoke("db.sqlite_transaction", db, "app.db", [("SELECT k FROM kv ORDER BY k", ())])
        rollback = rollback and after["rows"][-1] == [("answer",)]
        rows["DB_SERVICE"] = row(passed=got["rows"][-1] == [(42,)] and rollback,
            spec={"db": "app.db", "transaction": "CRUD_QUERY"}, semantic={"query_result": [[42]], "rollback_atomic": True},
            compiler_runtime=RUNTIME_VERSION, artifact_hash=impl_hash, test_id="APP-03_SQLITE_TRANSACTION",
            expected={"query": [[42]], "rollback": True}, observed={"query": got["rows"][-1], "rollback": rollback},
            negative={"failed_transaction_rolled_back": rollback}, authority=True)

        ac = rt.mint_capability("async.compute", {"operations": ["square"]})
        mapped = rt.invoke("async.map", ac, "square", list(range(32)), 8)
        denied = False
        try: rt.invoke("async.map", ac, "negate", [1], 1)
        except Exception: denied = True
        rows["CONCURRENT_SERVICE"] = row(passed=[x["value"] for x in mapped] == [x*x for x in range(32)] and denied,
            spec={"operation": "square", "values": list(range(32)), "workers": 8}, semantic={"publication_order": "input_index"},
            compiler_runtime=RUNTIME_VERSION, artifact_hash=impl_hash, test_id="APP-04_ASYNC_MAP",
            expected=[x*x for x in range(32)], observed=[x["value"] for x in mapped], negative={"out_of_scope_operation_rejected": denied}, authority=True)

        ui = rt.mint_capability("ui.interactive", {"events": ["click", "reset"], "max_events": 16, "io_timeout_s": 2})
        events = [{"kind": "click", "value": 1}, {"kind": "click", "value": 2}, {"kind": "reset"}, {"kind": "click", "value": 4}]
        interactive = rt.invoke("ui.fd_interactive_event_loop", ui, {"counter": 0, "label": "idle"}, events)
        denied = False
        try: rt.invoke("ui.fd_interactive_event_loop", ui, {"counter": 0}, [{"kind": "set_label", "value": "forbidden"}])
        except Exception: denied = True
        rows["GUI_INTERACTIVE"] = row(passed=interactive.get("io_mode") == "REAL_KERNEL_FD_EVENT_LOOP" and interactive["state"] == {"counter": 4, "label": "count:4"} and denied,
            spec={"events": events, "transport": "AF_UNIX_SOCKETPAIR"}, semantic={"final_state": {"counter": 4, "label": "count:4"}, "real_kernel_io": True},
            compiler_runtime=f"{RUNTIME_VERSION}|{STDLIB_EXT_VERSION}", artifact_hash=impl_hash, test_id="APP-05_REAL_FD_INTERACTIVE_EVENT_LOOP",
            expected={"state": {"counter": 4, "label": "count:4"}, "io_mode": "REAL_KERNEL_FD_EVENT_LOOP"}, observed=interactive,
            negative={"forbidden_event_rejected": denied}, authority=True)

        num = rt.mint_capability("numerical.cpu", {"max_vector": 1024})
        observed = rt.invoke("numerical.dot", num, [.5, 1.5, -2], [2, 4, 3])
        bad_shape = False
        try: rt.invoke("numerical.dot", num, [1], [1, 2])
        except Exception: bad_shape = True
        rows["GPU_ML_NUMERICAL"] = row(passed=observed == 1.0 and bad_shape,
            spec={"backend": "numerical.cpu", "left": [.5,1.5,-2], "right": [2,4,3]}, semantic={"dot": 1.0},
            compiler_runtime=RUNTIME_VERSION, artifact_hash=impl_hash, test_id="APP-07_NUMERICAL_BACKEND",
            expected=1.0, observed=observed, negative={"shape_error_rejected": bad_shape}, authority=True)

        fw = rt.mint_capability("fs.write", {"prefix": "data"}); fr = rt.mint_capability("fs.read", {"prefix": "data"})
        write = rt.invoke("fs.write_text", fw, "effect.txt", "authorized"); read = rt.invoke("fs.read_text", fr, "effect.txt")
        escape = False
        try: rt.invoke("fs.write_text", fw, "../escape.txt", "forbidden")
        except Exception: escape = True
        rows["SYSTEM_EFFECT_SANDBOX"] = row(passed=escape and read["text"] == "authorized" and read["sha256"] == write["sha256"],
            spec={"operation": "scoped file read/write", "prefix": "data"}, semantic={"ambient_authority": False, "escape": "rejected"},
            compiler_runtime=RUNTIME_VERSION, artifact_hash=impl_hash, test_id="APP-08_SCOPED_SYSTEM_EFFECT",
            expected={"escape_rejected": True, "text": "authorized"}, observed={"escape_rejected": escape, "text": read["text"]},
            negative={"path_escape_rejected": escape}, authority=True)

    rows["COMPILER_TOOL"] = pure_app("module app.compiler\nfn add(a:Int,b:Int)->Int=a+b\nfn score(a:Int,b:Int)->Int=add(a,b)*2\n", "score", [7,5], "24", "APP-06_COMPILER_TOOL_NATIVE")
    rows["FRANK_COMPONENT"] = frank_component_row()
    rows["FULL_FRANK_HANDOFF"] = full_frank_row()

    ordered = ["CLI","HTTP_WEBSITE","DB_SERVICE","CONCURRENT_SERVICE","GUI_INTERACTIVE","COMPILER_TOOL","GPU_ML_NUMERICAL","SYSTEM_EFFECT_SANDBOX","FRANK_COMPONENT","FULL_FRANK_HANDOFF"]
    failures = [name for name in ordered if not rows[name]["pass"]]
    report = {
        "schema_version": "1.0",
        "target_host": TARGET,
        "host_gate": gates,
        "compiler_runtime": {"pure": PURE_VERSION, "runtime": RUNTIME_VERSION, "stdlib": STDLIB_EXT_VERSION},
        "applications": {name: rows[name] for name in ordered},
        "passed": [name for name in ordered if rows[name]["pass"]],
        "failures": failures,
        "pass": not failures,
        "authority_invariant": "model output != execution authority",
        "note": "FULL_FRANK_HANDOFF intentionally cannot pass from the bounded FRANK component receipt.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "passed": len(report["passed"]), "total": len(ordered), "failures": failures, "output": str(OUT)}))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
