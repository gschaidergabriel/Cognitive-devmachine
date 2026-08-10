from __future__ import annotations

import hmac
import json
import os

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from . import telemetry

MAX_BODY = 8 * 1024 * 1024


def _authorized(request: Request) -> bool:
    expected = os.getenv("FRANK_TELEMETRY_INGEST_TOKEN", "")
    if not expected:
        return False
    supplied = request.headers.get("authorization", "")
    return hmac.compare_digest(supplied, f"Bearer {expected}")


async def health(_: Request) -> JSONResponse:
    try:
        telemetry.init_db()
        return JSONResponse({"ok": True, "storage": telemetry.storage_usage()})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": type(exc).__name__}, status_code=503)


async def ingest(request: Request) -> JSONResponse:
    if not _authorized(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401, headers={"WWW-Authenticate": "Bearer"})
    length = request.headers.get("content-length")
    if length and int(length) > MAX_BODY:
        return JSONResponse({"error": "request_too_large"}, status_code=413)
    body = await request.body()
    if len(body) > MAX_BODY:
        return JSONResponse({"error": "request_too_large"}, status_code=413)
    try:
        parsed = json.loads(body)
        events = parsed if isinstance(parsed, list) else [parsed]
        if not all(isinstance(x, dict) for x in events):
            raise ValueError("body must be one event object or a list of event objects")
        result = telemetry.ingest(events)
        return JSONResponse(result, status_code=202)
    except telemetry.CapacityError as exc:
        return JSONResponse({"error": "telemetry_capacity", "detail": str(exc), "storage": telemetry.storage_usage()}, status_code=507)
    except Exception as exc:
        return JSONResponse({"error": type(exc).__name__, "detail": str(exc)[:2000]}, status_code=400)


app = Starlette(routes=[Route("/healthz", health, methods=["GET"]), Route("/v1/events", ingest, methods=["POST"])])


def main() -> None:
    telemetry.init_db()
    uvicorn.run(
        app,
        host=os.getenv("FRANK_TELEMETRY_BIND", "127.0.0.1"),
        port=int(os.getenv("FRANK_TELEMETRY_PORT", "8766")),
        proxy_headers=False,
    )


if __name__ == "__main__":
    main()
