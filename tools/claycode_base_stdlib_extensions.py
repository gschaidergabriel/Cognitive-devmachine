#!/usr/bin/env python3
"""Capability-scoped ClayCode BASE stdlib extensions for HTTP and interactive apps.

The functions here are host-installed adapters. Clay/model code never receives Python
callables; it can only invoke named adapters through an opaque runtime capability.
"""
from __future__ import annotations

import hashlib
import http.server
import json
import selectors
import socket
import threading
import urllib.request
from typing import Any

from claycode_base_runtime import CapabilityFault, ClayRuntime, ResourceFault

STDLIB_EXT_VERSION = "claycode-base-stdlib-ext/0.2"


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


def _step_interactive_state(state: dict[str, Any], event: dict[str, Any], allowed: set[str]) -> tuple[dict[str, Any], str]:
    kind = event.get("kind")
    if kind not in allowed:
        raise CapabilityFault(f"UI_EVENT_NOT_ALLOWED:{kind}")
    next_state = dict(state)
    if kind == "click":
        next_state["counter"] += int(event.get("value", 1)); next_state["label"] = f"count:{next_state['counter']}"
    elif kind == "reset":
        next_state = {"counter": 0, "label": "idle"}
    elif kind == "set_label":
        next_state["label"] = str(event.get("value", ""))
    return next_state, f"[{next_state['counter']}] {next_state['label']}"


def _interactive_event_loop(policy: dict[str, Any], initial: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic in-process reference adapter retained as a semantic oracle."""
    allowed = set(policy.get("events", ["click", "reset", "set_label"]))
    max_events = int(policy.get("max_events", 1024))
    if len(events) > max_events:
        raise ResourceFault("UI_EVENT_LIMIT")
    state = {"counter": int(initial.get("counter", 0)), "label": str(initial.get("label", "idle"))}
    trace = []
    for seq, event in enumerate(events, 1):
        state, rendered = _step_interactive_state(state, event, allowed)
        trace.append({"seq": seq, "input": json.loads(json.dumps(event)), "state": dict(state), "rendered": rendered})
    return {
        "state": state,
        "rendered": trace[-1]["rendered"] if trace else f"[{state['counter']}] {state['label']}",
        "trace_sha256": hashlib.sha256(json.dumps(trace, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "event_count": len(trace),
        "io_mode": "IN_PROCESS_REFERENCE",
    }


def _fd_interactive_event_loop(policy: dict[str, Any], initial: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    """Real Linux/Unix kernel-FD interactive input/state/render loop.

    Events cross an AF_UNIX socketpair into a selectors-based application loop, then the
    rendered frame crosses the FD boundary back to the caller. This is display-independent
    and therefore works on a headless Ubuntu developer host while still exercising real
    kernel I/O rather than a list-fed state proxy.
    """
    allowed = set(policy.get("events", ["click", "reset", "set_label"]))
    max_events = int(policy.get("max_events", 1024))
    timeout_s = float(policy.get("io_timeout_s", 2.0))
    if len(events) > max_events:
        raise ResourceFault("UI_EVENT_LIMIT")
    if timeout_s <= 0 or timeout_s > 30:
        raise ResourceFault("UI_BAD_IO_TIMEOUT")
    state = {"counter": int(initial.get("counter", 0)), "label": str(initial.get("label", "idle"))}
    trace: list[dict[str, Any]] = []
    client, app = socket.socketpair()
    selector = selectors.DefaultSelector()
    selector.register(app, selectors.EVENT_READ)
    try:
        for seq, event in enumerate(events, 1):
            input_bytes = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            client.sendall(input_bytes)
            if not selector.select(timeout_s):
                raise ResourceFault("UI_FD_EVENT_TIMEOUT")
            received = app.recv(max(4096, len(input_bytes) + 64))
            if not received:
                raise ResourceFault("UI_FD_INPUT_EOF")
            try:
                decoded = json.loads(received.decode("utf-8").strip())
            except Exception as exc:
                raise ResourceFault("UI_FD_BAD_INPUT_FRAME") from exc
            state, rendered = _step_interactive_state(state, decoded, allowed)
            output = {"seq": seq, "state": state, "rendered": rendered}
            output_bytes = (json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            app.sendall(output_bytes)
            client.settimeout(timeout_s)
            observed_bytes = client.recv(max(4096, len(output_bytes) + 64))
            if not observed_bytes:
                raise ResourceFault("UI_FD_RENDER_EOF")
            observed = json.loads(observed_bytes.decode("utf-8").strip())
            if observed != output:
                raise ResourceFault("UI_FD_RENDER_MISMATCH")
            trace.append({
                "seq": seq,
                "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
                "output_sha256": hashlib.sha256(output_bytes).hexdigest(),
                "state": dict(state),
                "rendered": rendered,
            })
        rendered = trace[-1]["rendered"] if trace else f"[{state['counter']}] {state['label']}"
        return {
            "state": state,
            "rendered": rendered,
            "event_count": len(trace),
            "trace_sha256": hashlib.sha256(json.dumps(trace, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "io_mode": "REAL_KERNEL_FD_EVENT_LOOP",
            "selector": type(selector).__name__,
            "transport": "AF_UNIX_SOCKETPAIR",
        }
    finally:
        selector.close(); client.close(); app.close()


def install(rt: ClayRuntime) -> ClayRuntime:
    rt.register_adapter("http.loopback_roundtrip", "net.loopback", _http_roundtrip)
    rt.register_adapter("ui.interactive_event_loop", "ui.interactive", _interactive_event_loop)
    rt.register_adapter("ui.fd_interactive_event_loop", "ui.interactive", _fd_interactive_event_loop)
    return rt

__all__ = ["install", "STDLIB_EXT_VERSION"]
