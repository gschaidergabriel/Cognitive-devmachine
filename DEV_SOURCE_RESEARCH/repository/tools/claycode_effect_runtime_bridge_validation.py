#!/usr/bin/env python3
"""Differentially validate compiled ClayCode effects on concrete sealed runtime adapters."""
from __future__ import annotations

import hashlib
import http.server
import json
import random
import sys
import tempfile
import threading
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import claycode_base_effect_pipeline as ep
from claycode_base_runtime import ClayRuntime, CapabilityFault, RUNTIME_VERSION
from claycode_effect_runtime_bridge import BoundEffect, SealedRuntimeGateway, BRIDGE_VERSION

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"
OUT = ROOT / "research_entity/claycode/autonomous/BASE_EFFECT_REAL_RUNTIME_BRIDGE_RECEIPT.json"

SOURCE = """module app.real_effect_bridge
fn read(x:Int)->Int=host.fs_read(x)
fn store(x:Int)->Int=host.db_put(read(x))
fn net(x:Int)->Int=host.http_send(x)
fn main(x:Int)->Int=store(x)+net(x)+read(x)
"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path != "/value":
            self.send_response(404); self.end_headers(); return
        query = urllib.parse.parse_qs(parsed.query)
        try:
            x = int(query["x"][0])
        except Exception:
            self.send_response(400); self.end_headers(); return
        payload = str(x + 7).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers(); self.wfile.write(payload)
    def log_message(self, fmt, *args):
        return


def main() -> int:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    built = ep.build(SOURCE, grammar)
    rng = random.Random(202608091233)
    values = [rng.randint(-5000, 5000) for _ in range(384)]

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}/value"
    origin = f"http://127.0.0.1:{server.server_port}"

    failures = []
    rows = []
    negative = {}
    try:
        with tempfile.TemporaryDirectory(prefix="claycode-real-effects-") as td:
            rt = ClayRuntime(td)
            write_cap = rt.mint_capability("fs.write", {"prefix": "inputs", "max_calls": len(values) + 10, "max_units": 1_000_000})
            read_cap = rt.mint_capability("fs.read", {"prefix": "inputs", "max_calls": 2 * len(values) + 20, "max_units": 4_000_000})
            db_cap = rt.mint_capability("db.sqlite", {"prefix": "db", "max_calls": len(values) + 20, "max_units": 10_000})
            http_cap = rt.mint_capability("net.http_get", {"origins": [origin], "max_response_bytes": 256, "max_calls": len(values) + 20})

            for x in sorted(set(values)):
                rt.invoke("fs.write_text", write_cap, f"{x}.txt", str(x + 1000))

            bindings = [
                BoundEffect("cap.fs.read", "fs.read_text", read_cap, "FS_READ", {"path_template": "{value}.txt"}),
                BoundEffect("cap.db.write", "db.sqlite_transaction", db_cap, "DB_WRITE", {"db_path": "effects.db"}),
                BoundEffect("cap.http", "net.http_get", http_cap, "HTTP", {"base_url": base_url}),
            ]
            gateway = SealedRuntimeGateway(rt, bindings)
            manifest = gateway.public_binding_manifest()

            # Interpreter and lowered Python both execute through the SAME concrete
            # runtime bridge. The independent expected value comes from the frozen effect
            # algebra, not from the bridge implementation.
            for x in values:
                expected = 4 * x + 3007
                before = len(gateway.trace)
                interpreted = ep.eval_function(built["ir"], "main", [x], gateway)
                interpreted_trace = gateway.trace[before:]
                before = len(gateway.trace)
                lowered = ep.exec_lowered(built["artifact"], "main", [x], gateway)
                lowered_trace = gateway.trace[before:]
                ok = (
                    interpreted == expected
                    and lowered == expected
                    and interpreted_trace == lowered_trace
                    and len(interpreted_trace) == 4
                )
                if not ok:
                    failures.append(x)
                if len(rows) < 32 or not ok:
                    rows.append({
                        "x": x,
                        "expected": expected,
                        "interpreted": interpreted,
                        "lowered": lowered,
                        "trace_equal": interpreted_trace == lowered_trace,
                        "trace": interpreted_trace,
                        "pass": ok,
                    })

            # Symbolic text is request metadata, never authority.
            no_binding = SealedRuntimeGateway(rt, [bindings[0], bindings[1]])
            try:
                ep.eval_function(built["ir"], "main", [3], no_binding)
                negative["missing_symbolic_binding_rejected"] = False
            except CapabilityFault:
                negative["missing_symbolic_binding_rejected"] = True

            descriptor = rt.capability_descriptor(http_cap)
            try:
                SealedRuntimeGateway(rt, [BoundEffect("cap.http", "net.http_get", descriptor, "HTTP", {"base_url": base_url})])
                negative["descriptor_cannot_substitute_handle"] = False
            except CapabilityFault:
                negative["descriptor_cannot_substitute_handle"] = True

            # The request value cannot escape the origin fixed in the minted capability.
            try:
                gateway.effect("HTTP", "cap.http", 123)
                negative["fixed_origin_positive"] = True
            except Exception:
                negative["fixed_origin_positive"] = False

            rt.revoke(http_cap)
            try:
                gateway.effect("HTTP", "cap.http", 1)
                negative["revoked_handle_rejected"] = False
            except CapabilityFault:
                negative["revoked_handle_rejected"] = True

            runtime_trace = rt.trace_receipt()
            public_manifest = manifest
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)

    effect_manifest = next(f for f in built["ir"]["functions"] if f["name"] == "main")
    checks = {
        "effect_manifest_exact": effect_manifest["effect_summary"] == ["DB_WRITE", "FS_READ", "HTTP"],
        "required_capabilities_exact": effect_manifest["required_capabilities"] == ["cap.db.write", "cap.fs.read", "cap.http"],
        "all_vectors_match_real_effect_algebra": not failures,
        "interpreter_and_lowered_real_effect_traces_match": not failures,
        "all_negative_authority_tests_pass": all(negative.values()),
        "public_binding_manifest_non_authorizing": all(row.get("authorizing") is False for row in public_manifest),
        "runtime_trace_contains_only_runtime_capability_refs": bool(runtime_trace) and all("capability_ref" in row and "nonce" not in row for row in runtime_trace),
    }
    report = {
        "schema_version": "1.0",
        "experiment": "ClayCode compiled effect IR -> sealed runtime -> concrete Linux file/SQLite/HTTP differential",
        "source_sha256": sha(SOURCE.encode()),
        "semantic_hash": built["semantic_hash"],
        "lowered_artifact_hash": built["artifact_hash"],
        "translation_contract_hash": built["translation_contract_hash"],
        "compiler_effect_pipeline_version": built["candidate_version"],
        "runtime_version": RUNTIME_VERSION,
        "bridge_version": BRIDGE_VERSION,
        "vectors": len(values),
        "failures": failures,
        "sample_rows": rows,
        "negative": negative,
        "checks": checks,
        "binding_manifest": public_manifest,
        "runtime_trace_sha256": sha(json.dumps(runtime_trace, sort_keys=True, separators=(",", ":")).encode()),
        "pass": all(checks.values()),
        "supports": ["CC-WP-04-TYPE-EFFECT", "CC-WP-05-EVALUATOR", "CC-WP-06-COMPILER-LOWERING", "CC-WP-07-RUNTIME-ABI-FFI", "CC-WP-08-STDLIB-SDK"],
        "counts_as_work_package_pass": False,
        "counts_as_target_acceptance": False,
        "authority_invariant": "compiled symbolic capability requirement != sealed runtime authority",
        "scope_guard": "Concrete Linux file/SQLite/HTTP integration evidence on the executing host. It does not claim Andreas-target acceptance, arbitrary String/resource lowering, GUI, cancellation, full application suite, or full FRANK handoff.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "vectors": len(values), "failures": len(failures), "negative": negative}, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
