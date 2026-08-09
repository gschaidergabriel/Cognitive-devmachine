#!/usr/bin/env python3
"""Capability-scoped ClayCode BASE stdlib extensions for HTTP and interactive apps.

The functions here are host-installed adapters. Clay/model code never receives Python
callables; it can only invoke named adapters through an opaque runtime capability.
"""
from __future__ import annotations

import hashlib
import http.server
import json
import threading
import urllib.request
from typing import Any

from claycode_base_runtime import CapabilityFault, ClayRuntime, ResourceFault

STDLIB_EXT_VERSION = "claycode-base-stdlib-ext/0.1"


def _http_roundtrip(policy: dict[str, Any], route: str, body: str) -> dict[str, Any]:
    if policy.get("host", "127.0.0.1") != "127.0.0.1":
        raise CapabilityFault("HTTP_ONLY_LOOPBACK")
    allowed_routes = policy.get("routes", ["/"])
    if route not in allowed_routes:
        raise CapabilityFault("HTTP_ROUTE_NOT_ALLOWED")
    if not isinstance(body, str) or len(body.encode("utf-8")) > int(policy.get("max_body_bytes", 65536)):
        raise ResourceFault("HTTP_BODY_LIMIT")
    payload = body.encode("utf-8")

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != route:
                self.send_response(404); self.end_headers(); return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers(); self.wfile.write(payload)
        def log_message(self, fmt, *args): return

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}{route}", timeout=5) as response:
            got = response.read(); status = response.status
        thread.join(timeout=5)
        return {
            "status": status,
            "port": server.server_port,
            "body_sha256": hashlib.sha256(got).hexdigest(),
            "expected_sha256": hashlib.sha256(payload).hexdigest(),
            "matched": got == payload,
        }
    finally:
        server.server_close()


def _interactive_event_loop(policy: dict[str, Any], initial: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    allowed = set(policy.get("events", ["click", "reset", "set_label"]))
    max_events = int(policy.get("max_events", 1024))
    if len(events) > max_events:
        raise ResourceFault("UI_EVENT_LIMIT")
    state = {"counter": int(initial.get("counter", 0)), "label": str(initial.get("label", "idle"))}
    trace = []
    for seq, event in enumerate(events, 1):
        kind = event.get("kind")
        if kind not in allowed:
            raise CapabilityFault(f"UI_EVENT_NOT_ALLOWED:{kind}")
        if kind == "click":
            state["counter"] += int(event.get("value", 1)); state["label"] = f"count:{state['counter']}"
        elif kind == "reset":
            state = {"counter": 0, "label": "idle"}
        elif kind == "set_label":
            state["label"] = str(event.get("value", ""))
        # Render is an explicit deterministic surface update on every event.
        rendered = f"[{state['counter']}] {state['label']}"
        trace.append({"seq": seq, "input": json.loads(json.dumps(event)), "state": dict(state), "rendered": rendered})
    return {
        "state": state,
        "rendered": trace[-1]["rendered"] if trace else f"[{state['counter']}] {state['label']}",
        "trace_sha256": hashlib.sha256(json.dumps(trace, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "event_count": len(trace),
    }


def install(rt: ClayRuntime) -> ClayRuntime:
    rt.register_adapter("http.loopback_roundtrip", "net.loopback", _http_roundtrip)
    rt.register_adapter("ui.interactive_event_loop", "ui.interactive", _interactive_event_loop)
    return rt

__all__ = ["install", "STDLIB_EXT_VERSION"]
