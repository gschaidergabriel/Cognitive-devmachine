#!/usr/bin/env python3
"""Stateful/query loopback HTTP adapter for ClayCode BASE APP-02 acceptance.

The adapter exposes only a host-minted ``net.loopback`` capability. Route scope is fixed
at mint time. Query values can mutate application state but can never widen network or
route authority.
"""
from __future__ import annotations

import hashlib
import http.server
import json
import threading
import urllib.parse
import urllib.request
from typing import Any

from claycode_base_runtime import CapabilityFault, ClayRuntime, ResourceFault

WEB_STATE_EXT_VERSION = "claycode-base-web-state-ext/0.1"


def _stateful_query(policy: dict[str, Any], route: str, initial_state: int, deltas: list[int]) -> dict[str, Any]:
    if policy.get("host", "127.0.0.1") != "127.0.0.1":
        raise CapabilityFault("HTTP_ONLY_LOOPBACK")
    allowed_routes = set(policy.get("routes", ["/"]))
    if route not in allowed_routes:
        raise CapabilityFault("HTTP_ROUTE_NOT_ALLOWED")
    if not route.startswith("/") or "?" in route or "#" in route:
        raise ResourceFault("HTTP_BAD_STATE_ROUTE")
    max_requests = int(policy.get("max_requests", 1024))
    if not isinstance(deltas, list) or len(deltas) > max_requests:
        raise ResourceFault("HTTP_REQUEST_LIMIT")
    if not all(isinstance(x, int) and not isinstance(x, bool) for x in deltas):
        raise ResourceFault("HTTP_DELTA_NOT_INT")
    max_abs_delta = int(policy.get("max_abs_delta", 1_000_000))
    if any(abs(x) > max_abs_delta for x in deltas):
        raise ResourceFault("HTTP_DELTA_LIMIT")

    state = {"value": int(initial_state)}
    lock = threading.Lock()
    observed: list[dict[str, Any]] = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlsplit(self.path)
            if parsed.path != route:
                self.send_response(404); self.end_headers(); return
            query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
            raw = query.get("delta")
            if raw is None or len(raw) != 1:
                self.send_response(400); self.end_headers(); return
            try:
                delta = int(raw[0])
            except Exception:
                self.send_response(400); self.end_headers(); return
            if abs(delta) > max_abs_delta:
                self.send_response(413); self.end_headers(); return
            with lock:
                state["value"] += delta
                payload_obj = {"route": route, "delta": delta, "state": state["value"]}
            payload = json.dumps(payload_obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers(); self.wfile.write(payload)
        def log_message(self, fmt, *args): return

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        for delta in deltas:
            query = urllib.parse.urlencode({"delta": delta})
            url = f"http://127.0.0.1:{server.server_port}{route}?{query}"
            with urllib.request.urlopen(url, timeout=5) as response:
                body = response.read()
                obj = json.loads(body.decode("utf-8"))
                observed.append({
                    "status": int(response.status),
                    "url": url,
                    "body_sha256": hashlib.sha256(body).hexdigest(),
                    "body": obj,
                })
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)

    expected_states = []
    value = int(initial_state)
    for delta in deltas:
        value += delta
        expected_states.append(value)
    actual_states = [row["body"]["state"] for row in observed]
    return {
        "route": route,
        "request_count": len(observed),
        "initial_state": int(initial_state),
        "final_state": state["value"],
        "states": actual_states,
        "expected_states": expected_states,
        "matched": actual_states == expected_states and state["value"] == value,
        "transport": "REAL_LOOPBACK_TCP_HTTP",
        "query_parameter": "delta",
    }


def install(rt: ClayRuntime) -> ClayRuntime:
    rt.register_adapter("http.loopback_state_query", "net.loopback", _stateful_query)
    return rt


__all__ = ["install", "WEB_STATE_EXT_VERSION"]
