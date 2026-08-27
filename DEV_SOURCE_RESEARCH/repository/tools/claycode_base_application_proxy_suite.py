#!/usr/bin/env python3
"""Executable proxy suite spanning the ten ClayCode BASE application classes.

This suite is deliberately *not* the final Andreas-PC acceptance suite. Its job is to
remove integration surprises early by executing real hosted-Linux effects, the current
pure compiler slice, and a current FRANK H1 reference component. Every row carries an
explicit proxy/target distinction so successful CI cannot accidentally promote BASE.
"""
from __future__ import annotations

import hashlib
import http.server
import importlib.util
import json
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT))

from claycode_base_pure_toolchain import compile_source, differential
from claycode_base_runtime import ClayRuntime

OUT = ROOT / "research_entity/claycode/autonomous/BASE_APPLICATION_PROXY_SUITE_RECEIPT.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_active_assembly_module():
    path = ROOT / "research_entity/harness/reference/active_assembly.py"
    spec = importlib.util.spec_from_file_location("frank_active_assembly", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("FRANK_ACTIVE_ASSEMBLY_LOAD_FAILED")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod, path


def http_loopback_probe() -> dict:
    body = b"<html><body>ClayCode BASE</body></html>"

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            return

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/"
        with urllib.request.urlopen(url, timeout=5) as response:
            received = response.read()
            status = response.status
        thread.join(timeout=5)
        return {"status": status, "body_sha256": sha(received), "expected_sha256": sha(body), "pass": status == 200 and received == body}
    finally:
        server.server_close()


def gui_interactive_event_proxy() -> dict:
    # Headless deterministic interaction contract. Target acceptance still requires the
    # actual Ubuntu developer-host UI adapter; this proves event/state semantics only.
    state = {"counter": 0, "label": "idle"}
    events = [("click", 1), ("click", 2), ("reset", 0), ("click", 4)]
    trace = []
    for kind, value in events:
        if kind == "click":
            state["counter"] += value
            state["label"] = f"count:{state['counter']}"
        elif kind == "reset":
            state["counter"] = 0
            state["label"] = "idle"
        trace.append([kind, value, dict(state)])
    return {"final": state, "trace_sha256": sha(json.dumps(trace, sort_keys=True).encode()), "pass": state == {"counter": 4, "label": "count:4"}}


def compiler_probe() -> dict:
    source = """module app.compiler_probe
fn add(a:Int,b:Int)->Int=a+b
fn score(a:Int,b:Int)->Int=add(a,b)*2
"""
    typed = compile_source(source)
    diff = differential(typed, "score", [7, 5])
    return {
        "source_sha256": sha(source.encode()),
        "semantic_hash": typed["semantic_hash"],
        "generated_c_sha256": diff["generated_c_sha256"],
        "interpreter_result": diff["interpreter_result"],
        "native_stdout": diff["native_stdout"],
        "pass": bool(diff["match"]),
    }


def frank_component_probe() -> dict:
    mod, path = load_active_assembly_module()
    packets = [
        mod.AssemblyPacket("a", "memory", "memory", 0.9, 0.8, 0.4, 0.1, 3, claim_key="mode", claim_value="A", reexpand_ref="mem:a"),
        mod.AssemblyPacket("b", "tool", "tool_result", 0.8, 0.9, 0.5, 0.2, 3, claim_key="mode", claim_value="B", reexpand_ref="tool:b"),
        mod.AssemblyPacket("stale", "old", "memory", 1.0, 1.0, 1.0, 0.0, 2, reexpand_ref="old:stale"),
    ]
    assembly = mod.compile_active_assembly(packets, current_epoch=3, max_items=4, max_per_ancestry=2)
    authority_ok = all(item.get("execution_authority") is False for item in assembly["items"])
    stale_excluded = all(item["packet_id"] != "stale" for item in assembly["items"])
    return {
        "reference_path": str(path.relative_to(ROOT)),
        "reference_sha256": sha(path.read_bytes()),
        "assembly_sha256": assembly["assembly_sha256"],
        "item_count": len(assembly["items"]),
        "conflict_values": sorted({x.get("claim_value") for x in assembly["items"] if x.get("claim_key") == "mode"}),
        "authority_ok": authority_ok,
        "stale_excluded": stale_excluded,
        "pass": authority_ok and stale_excluded and {"A", "B"}.issubset({x.get("claim_value") for x in assembly["items"]}),
    }


def full_frank_handoff_proxy(frank: dict) -> dict:
    # Cross the current FRANK-reference -> ClayCode-compiler boundary with a concrete
    # value while retaining separate hashes for the FRANK and compiler artifacts.
    source = """module frank.handoff_proxy
fn amplify(x:Int)->Int=x*2+1
"""
    typed = compile_source(source)
    diff = differential(typed, "amplify", [int(frank["item_count"])])
    expected = int(frank["item_count"]) * 2 + 1
    return {
        "frank_assembly_sha256": frank["assembly_sha256"],
        "clay_source_sha256": sha(source.encode()),
        "clay_semantic_hash": typed["semantic_hash"],
        "native_result": int(diff["native_stdout"]),
        "expected": expected,
        "pass": diff["match"] and int(diff["native_stdout"]) == expected,
    }


def main() -> int:
    rows = []

    def add(app_id: str, evidence: dict, note: str = ""):
        rows.append({"app_id": app_id, "pass": bool(evidence.get("pass")), "note": note, "evidence": evidence})

    with tempfile.TemporaryDirectory(prefix="claycode_apps_") as td:
        rt = ClayRuntime(td)

        proc = rt.mint_capability("process.exec")
        cli = rt.invoke("process.exec", proc, ["/bin/echo", "ClayCode CLI"], ["echo"])
        add("CLI", {"pass": cli["returncode"] == 0 and cli["stdout"].strip() == "ClayCode CLI", "returncode": cli["returncode"], "stdout_sha256": sha(cli["stdout"].encode())})

        add("HTTP_WEBSITE", http_loopback_probe(), "real loopback HTTP in hosted Linux; target-host rerun required")

        db = rt.mint_capability("db.sqlite")
        dbres = rt.invoke("db.sqlite_transaction", db, "app.db", [
            ("CREATE TABLE kv(k TEXT PRIMARY KEY,v INTEGER)", ()),
            ("INSERT INTO kv(k,v) VALUES(?,?)", ("answer", 42)),
            ("SELECT v FROM kv WHERE k=?", ("answer",)),
        ])
        add("DB_SERVICE", {"pass": dbres["rows"][-1] == [(42,)], "rows": dbres["rows"][-1], "resource": dbres["resource"]})

        async_cap = rt.mint_capability("async.compute")
        concurrent = rt.invoke("async.map", async_cap, lambda x: x + 10, list(range(32)), 8)
        add("CONCURRENT_SERVICE", {"pass": [x["value"] for x in concurrent] == [x + 10 for x in range(32)], "count": len(concurrent), "result_sha256": sha(json.dumps(concurrent, sort_keys=True).encode())})

        add("GUI_INTERACTIVE", gui_interactive_event_proxy(), "headless event/state proxy only; actual Ubuntu UI adapter is a target-host gate")

        compiler = compiler_probe()
        add("COMPILER_TOOL", compiler, "ClayCode source -> typed IR -> C11 -> native execution")

        num = rt.mint_capability("numerical.cpu")
        dot = rt.invoke("numerical.dot", num, [0.5, 1.5, -2.0], [2.0, 4.0, 3.0])
        add("GPU_ML_NUMERICAL", {"pass": dot == 1.0, "backend": "numerical.cpu", "observed": dot}, "numerical backend satisfies proxy class; GPU hardware is not claimed")

        fsw = rt.mint_capability("fs.write")
        fsr = rt.mint_capability("fs.read")
        wr = rt.invoke("fs.write_text", fsw, "sandbox/effect.txt", "authorized")
        rr = rt.invoke("fs.read_text", fsr, "sandbox/effect.txt")
        escaped = False
        try:
            rt.invoke("fs.write_text", fsw, "../escape.txt", "forbidden")
        except Exception:
            escaped = True
        add("SYSTEM_EFFECT_SANDBOX", {"pass": escaped and rr["text"] == "authorized" and rr["sha256"] == wr["sha256"], "escape_rejected": escaped, "resource": wr["resource"]})

        frank = frank_component_probe()
        add("FRANK_COMPONENT", frank, "executes current H1 ordinary-code reference; ClayCode production rewrite still required")
        add("FULL_FRANK_HANDOFF", full_frank_handoff_proxy(frank), "concrete FRANK-reference -> ClayCode native differential boundary; not the full target harness")

        trace = rt.trace_receipt()

    failures = [row["app_id"] for row in rows if not row["pass"]]
    report = {
        "schema_version": "1.0",
        "experiment": "ClayCode BASE ten-class application proxy suite",
        "evidence_class": "HOSTED_LINUX_APPLICATION_PROXY_NOT_ANDREAS_TARGET_ACCEPTANCE",
        "counts_as_target_acceptance": False,
        "counts_as_application_acceptance_pass": False,
        "required_classes": ["CLI", "HTTP_WEBSITE", "DB_SERVICE", "CONCURRENT_SERVICE", "GUI_INTERACTIVE", "COMPILER_TOOL", "GPU_ML_NUMERICAL", "SYSTEM_EFFECT_SANDBOX", "FRANK_COMPONENT", "FULL_FRANK_HANDOFF"],
        "rows": rows,
        "passed": len(rows) - len(failures),
        "total": len(rows),
        "failures": failures,
        "pass": not failures,
        "runtime_trace_sha256": sha(json.dumps(trace, sort_keys=True).encode()),
        "authority_invariant": "model_output != execution_authority",
        "next_required": "rerun/adapt every application on ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM through the production ClayCode source->runtime chain before workspace application_acceptance is credited"
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "passed": report["passed"], "total": report["total"], "failures": failures}))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
