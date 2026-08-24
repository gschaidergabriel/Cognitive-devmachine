#!/usr/bin/env python3
"""Fail-closed transport guard for zero-cost local model endpoints.

This module is deliberately *not* a provider/capability authority.  It only proves that
one configured HTTP base is a numeric loopback endpoint and returns an urllib opener
that cannot use ambient proxies or follow redirects.  Callers still need their normal
EntityOS/HCU admission, provenance, resource and evidence boundaries.
"""
from __future__ import annotations

import ipaddress
import urllib.request
from urllib.parse import urlsplit


class LoopbackEndpointError(ValueError):
    """Configured local endpoint is not an unambiguous numeric loopback URL."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


def validated_loopback_base(raw: str) -> str:
    """Return a canonical-enough base URL only for direct numeric HTTP loopback.

    Hostnames are intentionally rejected: even ``localhost`` would reintroduce resolver
    state into a path whose contract is strictly loopback.  Userinfo, paths, query and
    fragment components are also rejected so concatenated API paths cannot be retargeted.
    """
    if type(raw) is not str or not raw or raw != raw.strip():
        raise LoopbackEndpointError("LOCAL_BASE_INVALID_TEXT")

    try:
        parts = urlsplit(raw)
        port = parts.port  # force malformed/out-of-range port validation
    except (TypeError, ValueError) as exc:
        raise LoopbackEndpointError("LOCAL_BASE_INVALID_URL") from exc

    if parts.scheme != "http":
        raise LoopbackEndpointError("LOCAL_BASE_HTTP_REQUIRED")
    if parts.username is not None or parts.password is not None:
        raise LoopbackEndpointError("LOCAL_BASE_USERINFO_FORBIDDEN")
    if not parts.hostname:
        raise LoopbackEndpointError("LOCAL_BASE_HOST_REQUIRED")
    if parts.path not in ("", "/") or parts.query or parts.fragment:
        raise LoopbackEndpointError("LOCAL_BASE_COMPONENT_FORBIDDEN")
    if port is not None and not (1 <= port <= 65535):
        raise LoopbackEndpointError("LOCAL_BASE_PORT_INVALID")

    try:
        ip = ipaddress.ip_address(parts.hostname)
    except ValueError as exc:
        raise LoopbackEndpointError("LOCAL_BASE_NUMERIC_IP_REQUIRED") from exc
    if not ip.is_loopback:
        raise LoopbackEndpointError("LOCAL_BASE_NON_LOOPBACK")

    return raw[:-1] if raw.endswith("/") else raw


def build_loopback_opener() -> urllib.request.OpenerDirector:
    """Return an opener with ambient proxies disabled and redirects denied."""
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        _NoRedirect(),
    )
