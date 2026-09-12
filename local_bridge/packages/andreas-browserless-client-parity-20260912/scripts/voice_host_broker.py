#!/usr/bin/env python3
"""Low-latency host broker client for Frankenstein voice sessions.

GitHub Local Bridge remains control/recovery plane. This module is the live
conversation data plane: typed requests, exact machine/owner verification,
short deadlines, no remote shell semantics.

Remote endpoints are configured explicitly:
  FRANK_VOICE_BROKER_GABRIEL=http://127.0.0.1:8765
  FRANK_VOICE_BROKER_ANDREAS=http://<private-route>:8765
  FRANK_VOICE_BROKER_TOKEN=<shared secret or per-host secret>

Transport security is expected from a private authenticated route (loopback,
Tailscale/WireGuard, SSH tunnel, mTLS reverse proxy). The broker protocol still
requires a bearer token and verifies returned machine_id/owner before using
any state.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

INSTALLATIONS = {
    "gabriel": {"machine_id": "ai-core-node", "owner": "gabriel"},
    "andreas": {"machine_id": "andreas-maco", "owner": "andreas"},
}


class BrokerError(RuntimeError):
    pass


@dataclass(frozen=True)
class BrokerEndpoint:
    label: str
    url: str
    token: str
    machine_id: str
    owner: str


def endpoint_for(label: str) -> BrokerEndpoint:
    key = str(label or "").strip().lower()
    if key not in INSTALLATIONS:
        raise BrokerError(f"unknown installation {label!r}")
    env_key = f"FRANK_VOICE_BROKER_{key.upper()}"
    url = (os.environ.get(env_key) or "").strip().rstrip("/")
    token = (os.environ.get(f"{env_key}_TOKEN") or os.environ.get("FRANK_VOICE_BROKER_TOKEN") or "").strip()
    if not url:
        raise BrokerError(f"missing {env_key}")
    if not token:
        raise BrokerError(f"missing token for {key}")
    meta = INSTALLATIONS[key]
    return BrokerEndpoint(key, url, token, meta["machine_id"], meta["owner"])


def _verify_identity(ep: BrokerEndpoint, payload: dict[str, Any]) -> dict[str, Any]:
    machine = str(payload.get("machine_id") or "").strip().lower()
    owner = str(payload.get("owner") or "").strip().lower()
    if machine != ep.machine_id or owner != ep.owner:
        raise BrokerError(
            f"broker identity mismatch for {ep.label}: expected {ep.machine_id}/{ep.owner}, got {machine}/{owner}"
        )
    return payload


def _request(ep: BrokerEndpoint, path: str, body: dict[str, Any] | None = None, *, timeout_s: float = 0.8) -> dict[str, Any]:
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        ep.url + path,
        data=data,
        method="GET" if body is None else "POST",
        headers={
            "Authorization": f"Bearer {ep.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read(256 * 1024)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise BrokerError(f"broker request failed: {type(exc).__name__}: {exc}") from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise BrokerError(f"invalid broker json: {exc}") from exc
    if not isinstance(payload, dict):
        raise BrokerError("broker response is not an object")
    return _verify_identity(ep, payload)


def health(label: str, *, timeout_s: float = 0.5) -> dict[str, Any]:
    ep = endpoint_for(label)
    return _request(ep, "/health", timeout_s=timeout_s)


def relationship_context(label: str, query: str, session_id: str, *, char_budget: int = 4200,
                         timeout_s: float = 0.8) -> dict[str, Any]:
    ep = endpoint_for(label)
    payload = _request(
        ep,
        "/v1/relationship-context",
        {
            "person": label,
            "query": str(query or "")[:8000],
            "session_id": str(session_id or "")[:200],
            "char_budget": max(512, min(int(char_budget), 8000)),
        },
        timeout_s=timeout_s,
    )
    if payload.get("person") != label:
        raise BrokerError("broker returned wrong person scope")
    return payload


def state_snapshot(label: str, *, timeout_s: float = 0.8) -> dict[str, Any]:
    ep = endpoint_for(label)
    return _request(ep, "/v1/state-snapshot", {"person": label}, timeout_s=timeout_s)
