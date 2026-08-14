#!/usr/bin/env python3
"""Hardened contract-shaped ten-application ClayCode target suite.

Compared with the first target suite this version:
- verifies the registered Andreas Ubuntu host fingerprint rather than a text marker;
- APP-02 proves real loopback routing + HTML asset + query-driven mutable state;
- APP-04 proves deterministic concurrency + cancellation + structured error paths;
- preserves the existing fail-closed FULL_FRANK_HANDOFF requirement.

The suite writes target-shaped application rows but cannot promote ClayCode by itself.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import claycode_base_target_application_suite as legacy
from claycode_base_runtime import ClayRuntime, RUNTIME_VERSION
from claycode_base_stdlib_extensions import install as install_stdlib, STDLIB_EXT_VERSION
from claycode_base_concurrency_extensions import install as install_concurrency, CONCURRENCY_EXT_VERSION
from claycode_base_web_state_extension import install as install_web, WEB_STATE_EXT_VERSION
from claycode_target_host_identity import verify, DEFAULT_REGISTRATION, TARGET_HOST

OUT = ROOT / "research_entity/claycode/target/ANDREAS_UBUNTU_APPLICATIONS.json"


def runtime_artifact_hash() -> str:
    return legacy.file_hash(
        ROOT / "tools/claycode_base_runtime.py",
        ROOT / "tools/claycode_base_stdlib_extensions.py",
        ROOT / "tools/claycode_base_concurrency_extensions.py",
        ROOT / "tools/claycode_base_web_state_extension.py",
    )


def main() -> int:
    host_ok, host = verify(DEFAULT_REGISTRATION)
    if not host_ok:
        print(json.dumps({"error": "TARGET_HOST_IDENTITY_NOT_VERIFIED", "details": host}, ensure_ascii=False, indent=2))
        return 3

    impl_hash = runtime_artifact_hash()
    rows: dict[str, dict] = {}
    rows["CLI"] = legacy.pure_app("module app.cli\nfn main(x:Int)->Int=x+1\n", "main", [41], "42", "APP-01_CLI_NATIVE")

    with tempfile.TemporaryDirectory(prefix="claycode-target-apps-v2-") as td:
        rt = install_web(install_concurrency(install_stdlib(ClayRuntime(td))))

        # APP-02: HTML + asset + allowed routing + query-driven state on real TCP HTTP.
        net = rt.mint_capability("net.loopback", {
            "host": "127.0.0.1",
            "routes": ["/", "/asset.css", "/counter"],
            "max_body_bytes": 4096,
            "max_requests": 16,
            "max_abs_delta": 100,
        })
        html = "<html><head><link rel='stylesheet' href='/asset.css'></head><body>ClayCode BASE</body></html>"
        css = "body{font-family:sans-serif}"
        page = rt.invoke("http.loopback_roundtrip", net, "/", html)
        asset = rt.invoke("http.loopback_roundtrip", net, "/asset.css", css)
        state = rt.invoke("http.loopback_state_query", net, "/counter", 10, [1, 2, -4, 7])
        route_denied = False
        try:
            rt.invoke("http.loopback_roundtrip", net, "/admin", "forbidden")
        except Exception:
            route_denied = True
        state_route_denied = False
        try:
            rt.invoke("http.loopback_state_query", net, "/admin", 0, [1])
        except Exception:
            state_route_denied = True
        app02_pass = (
            page.get("status") == 200 and page.get("matched") is True
            and asset.get("status") == 200 and asset.get("matched") is True
            and state.get("transport") == "REAL_LOOPBACK_TCP_HTTP"
            and state.get("matched") is True
            and state.get("states") == [11, 13, 9, 16]
            and state.get("final_state") == 16
            and route_denied and state_route_denied
        )
        rows["HTTP_WEBSITE"] = legacy.row(
            passed=app02_pass,
            spec={
                "routes": ["/", "/asset.css", "/counter"],
                "html": html,
                "asset": css,
                "state_initial": 10,
                "query_deltas": [1, 2, -4, 7],
            },
            semantic={
                "transport": "REAL_LOOPBACK_TCP_HTTP",
                "routing": True,
                "html_asset": True,
                "query_state_transition": [11, 13, 9, 16],
            },
            compiler_runtime=f"{RUNTIME_VERSION}|{STDLIB_EXT_VERSION}|{WEB_STATE_EXT_VERSION}",
            artifact_hash=impl_hash,
            test_id="APP-02_REAL_HTTP_ROUTING_HTML_ASSET_QUERY_STATE",
            expected={"page": 200, "asset": 200, "states": [11, 13, 9, 16], "route_escape": "REJECT"},
            observed={"page": page, "asset": asset, "state": state},
            negative={"forbidden_route_rejected": route_denied, "forbidden_state_route_rejected": state_route_denied},
            authority=True,
        )

        # APP-03: CRUD/query/transaction rollback.
        db = rt.mint_capability("db.sqlite", {"prefix": "db"})
        got = rt.invoke("db.sqlite_transaction", db, "app.db", [
            ("CREATE TABLE kv(k TEXT PRIMARY KEY,v INTEGER)", ()),
            ("INSERT INTO kv(k,v) VALUES(?,?)", ("answer", 42)),
            ("SELECT v FROM kv WHERE k=?", ("answer",)),
        ])
        rollback = False
        try:
            rt.invoke("db.sqlite_transaction", db, "app.db", [
                ("INSERT INTO kv(k,v) VALUES(?,?)", ("x", 1)),
                ("INSERT INTO missing_table(x) VALUES(1)", ()),
            ])
        except Exception:
            rollback = True
        after = rt.invoke("db.sqlite_transaction", db, "app.db", [("SELECT k FROM kv ORDER BY k", ())])
        rollback = rollback and after["rows"][-1] == [("answer",)]
        rows["DB_SERVICE"] = legacy.row(
            passed=got["rows"][-1] == [(42,)] and rollback,
            spec={"db": "app.db", "transaction": "CRUD_QUERY"},
            semantic={"query_result": [[42]], "rollback_atomic": True},
            compiler_runtime=RUNTIME_VERSION,
            artifact_hash=impl_hash,
            test_id="APP-03_SQLITE_TRANSACTION",
            expected={"query": [[42]], "rollback": True},
            observed={"query": got["rows"][-1], "rollback": rollback},
            negative={"failed_transaction_rolled_back": rollback},
            authority=True,
        )

        # APP-04: deterministic publication, explicit cancellation, structured errors.
        ac = rt.mint_capability("async.cancellable", {
            "operations": ["square", "inverse100"],
            "max_items": 1024,
            "max_workers": 16,
            "max_calls": 32,
            "max_units": 100000,
        })
        values = list(range(32))
        full = rt.invoke("async.cancellable_map", ac, "square", values, None, 8)
        cancelled = rt.invoke("async.cancellable_map", ac, "square", values, 13, 8)
        errored = rt.invoke("async.cancellable_map", ac, "inverse100", [10, 5, 0, -4], None, 4)
        scope_denied = False
        try:
            rt.invoke("async.cancellable_map", ac, "identity", [1], None, 1)
        except Exception:
            scope_denied = True
        expected_full = [x * x for x in values]
        app04_pass = (
            [x.get("value") for x in full["rows"]] == expected_full
            and [x["index"] for x in full["rows"]] == values
            and cancelled["submitted"] == 13
            and cancelled["cancelled"] == 19
            and all(x["status"] == "CANCELLED" for x in cancelled["rows"][13:])
            and cancelled["post_cancel_dispatch"] == 0
            and [x["status"] for x in errored["rows"]] == ["OK", "OK", "ERROR", "OK"]
            and errored["rows"][2].get("error_type") == "ZeroDivisionError"
            and scope_denied
        )
        rows["CONCURRENT_SERVICE"] = legacy.row(
            passed=app04_pass,
            spec={"operation": "square", "values": values, "cancel_after": 13, "error_operation": "inverse100"},
            semantic={"publication_order": "INPUT_INDEX", "cancellation": "UNDISPATCHED_SUFFIX", "error": "STRUCTURED_ROW"},
            compiler_runtime=f"{RUNTIME_VERSION}|{CONCURRENCY_EXT_VERSION}",
            artifact_hash=impl_hash,
            test_id="APP-04_CONCURRENT_CANCELLATION_ERROR",
            expected={"full": expected_full, "cancelled": 19, "error_index": 2},
            observed={"full": full, "cancelled": cancelled, "errored": errored},
            negative={"out_of_scope_operation_rejected": scope_denied},
            authority=True,
        )

        # APP-05: real kernel FD event/input/state/render loop.
        ui = rt.mint_capability("ui.interactive", {"events": ["click", "reset"], "max_events": 16, "io_timeout_s": 2})
        events = [{"kind": "click", "value": 1}, {"kind": "click", "value": 2}, {"kind": "reset"}, {"kind": "click", "value": 4}]
        interactive = rt.invoke("ui.fd_interactive_event_loop", ui, {"counter": 0, "label": "idle"}, events)
        denied = False
        try:
            rt.invoke("ui.fd_interactive_event_loop", ui, {"counter": 0}, [{"kind": "set_label", "value": "forbidden"}])
        except Exception:
            denied = True
        rows["GUI_INTERACTIVE"] = legacy.row(
            passed=interactive.get("io_mode") == "REAL_KERNEL_FD_EVENT_LOOP" and interactive["state"] == {"counter": 4, "label": "count:4"} and denied,
            spec={"events": events, "transport": "AF_UNIX_SOCKETPAIR"},
            semantic={"final_state": {"counter": 4, "label": "count:4"}, "real_kernel_io": True},
            compiler_runtime=f"{RUNTIME_VERSION}|{STDLIB_EXT_VERSION}",
            artifact_hash=impl_hash,
            test_id="APP-05_REAL_FD_INTERACTIVE_EVENT_LOOP",
            expected={"state": {"counter": 4, "label": "count:4"}, "io_mode": "REAL_KERNEL_FD_EVENT_LOOP"},
            observed=interactive,
            negative={"forbidden_event_rejected": denied},
            authority=True,
        )

        # APP-07: explicit numerical backend/resource capability.
        num = rt.mint_capability("numerical.cpu", {"max_vector": 1024})
        observed = rt.invoke("numerical.dot", num, [.5, 1.5, -2], [2, 4, 3])
        bad_shape = False
        try:
            rt.invoke("numerical.dot", num, [1], [1, 2])
        except Exception:
            bad_shape = True
        rows["GPU_ML_NUMERICAL"] = legacy.row(
            passed=observed == 1.0 and bad_shape,
            spec={"backend": "numerical.cpu", "left": [.5, 1.5, -2], "right": [2, 4, 3]},
            semantic={"dot": 1.0},
            compiler_runtime=RUNTIME_VERSION,
            artifact_hash=impl_hash,
            test_id="APP-07_NUMERICAL_BACKEND",
            expected=1.0,
            observed=observed,
            negative={"shape_error_rejected": bad_shape},
            authority=True,
        )

        # APP-08: scoped raw/system effect, no ambient authority.
        fw = rt.mint_capability("fs.write", {"prefix": "data"})
        fr = rt.mint_capability("fs.read", {"prefix": "data"})
        write = rt.invoke("fs.write_text", fw, "effect.txt", "authorized")
        read = rt.invoke("fs.read_text", fr, "effect.txt")
        escape = False
        try:
            rt.invoke("fs.write_text", fw, "../escape.txt", "forbidden")
        except Exception:
            escape = True
        rows["SYSTEM_EFFECT_SANDBOX"] = legacy.row(
            passed=escape and read["text"] == "authorized" and read["sha256"] == write["sha256"],
            spec={"operation": "scoped file read/write", "prefix": "data"},
            semantic={"ambient_authority": False, "escape": "rejected"},
            compiler_runtime=RUNTIME_VERSION,
            artifact_hash=impl_hash,
            test_id="APP-08_SCOPED_SYSTEM_EFFECT",
            expected={"escape_rejected": True, "text": "authorized"},
            observed={"escape_rejected": escape, "text": read["text"]},
            negative={"path_escape_rejected": escape},
            authority=True,
        )

    rows["COMPILER_TOOL"] = legacy.pure_app(
        "module app.compiler\nfn add(a:Int,b:Int)->Int=a+b\nfn score(a:Int,b:Int)->Int=add(a,b)*2\n",
        "score", [7, 5], "24", "APP-06_COMPILER_TOOL_NATIVE",
    )
    rows["FRANK_COMPONENT"] = legacy.frank_component_row()
    rows["FULL_FRANK_HANDOFF"] = legacy.full_frank_row()

    ordered = [
        "CLI", "HTTP_WEBSITE", "DB_SERVICE", "CONCURRENT_SERVICE", "GUI_INTERACTIVE",
        "COMPILER_TOOL", "GPU_ML_NUMERICAL", "SYSTEM_EFFECT_SANDBOX", "FRANK_COMPONENT", "FULL_FRANK_HANDOFF",
    ]
    failures = [name for name in ordered if not rows[name]["pass"]]
    report = {
        "schema_version": "2.0",
        "target_host": TARGET_HOST,
        "target_host_verified": True,
        "host_fingerprint": host.get("host_fingerprint", {}),
        "compiler_runtime": {
            "pure": legacy.PURE_VERSION,
            "runtime": RUNTIME_VERSION,
            "stdlib": STDLIB_EXT_VERSION,
            "web_state": WEB_STATE_EXT_VERSION,
            "concurrency": CONCURRENCY_EXT_VERSION,
        },
        "applications": {name: rows[name] for name in ordered},
        "passed": [name for name in ordered if rows[name]["pass"]],
        "failures": failures,
        "pass": not failures,
        "authority_invariant": "model output != execution authority",
        "promotion_performed": False,
        "note": "APP-02 and APP-04 are contract-hardened. FULL_FRANK_HANDOFF remains intentionally fail-closed until the production H2/H3 handoff receipt exists.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "passed": len(report["passed"]), "total": len(ordered), "failures": failures, "output": str(OUT)}))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
