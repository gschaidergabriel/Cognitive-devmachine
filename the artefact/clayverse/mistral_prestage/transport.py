from __future__ import annotations

import hashlib
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_RESPONSE_BYTES = 2_000_000


class TransportError(RuntimeError):
    pass


class _NoRedirectHandler(HTTPRedirectHandler):
    """Refuse redirects so a bearer token can never cross the fixed API origin.

    Mirrors clayverse.adapters._MistralNoRedirectHandler. Duplicated here
    (rather than imported) so this module has zero dependency on the files
    the coordinating agent owns.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _urlopen(request, timeout):
    return build_opener(_NoRedirectHandler()).open(request, timeout=timeout)


def mistral_chat_json(
    *,
    api_key: str,
    model: str,
    system: str,
    user: str,
    timeout: int = 60,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> dict[str, Any]:
    """One hardened, tool-less, JSON-mode Mistral chat completion.

    Security pattern mirrors clayverse.adapters.MistralInference (fixed
    endpoint, redirects refused, bounded response, token scrubbed from
    locals in `finally` before any exception can retain it in a traceback
    frame) but does not depend on that class's text+effect decision schema,
    which this module has no use for.
    """
    if not api_key or api_key != api_key.strip() or "\x00" in api_key:
        raise TransportError("invalid Mistral API key")
    if not model or len(model) > 256:
        raise TransportError("invalid Mistral model id")
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "tools": [],
            "tool_choice": "none",
            "parallel_tool_calls": False,
            "stream": False,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    request = Request(
        "https://api.mistral.ai/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "EntityOS-MistralPrestage/1",
        },
        method="POST",
    )
    http_status = None
    transport_failure = None
    raw = b""
    try:
        with _urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        http_status = int(exc.code)
    except (URLError, TimeoutError, OSError) as exc:
        transport_failure = type(exc).__name__
    finally:
        api_key = ""
        request = None
    if http_status is not None:
        raise TransportError(f"Mistral HTTP failure status={http_status}")
    if transport_failure is not None:
        raise TransportError(f"Mistral transport failure type={transport_failure}")
    if len(raw) > MAX_RESPONSE_BYTES:
        raise TransportError("Mistral response exceeds bound")
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TransportError("Mistral response envelope is not JSON") from exc
    try:
        choice = envelope["choices"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise TransportError("Mistral response missing choices") from exc
    if choice.get("finish_reason") != "stop":
        raise TransportError("Mistral response did not finish cleanly")
    content = choice.get("message", {}).get("content")
    if not isinstance(content, str) or not content:
        raise TransportError("Mistral message content missing")
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise TransportError("Mistral message content is not JSON") from exc
    receipt = {
        "provider": "mistral",
        "model_requested": model,
        "model_returned": envelope.get("model"),
        "response_id": envelope.get("id"),
        "request_sha256": hashlib.sha256(body).hexdigest(),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
    }
    return {"payload": payload, "receipt": receipt}


def gemini_chat_json(
    *,
    api_key: str,
    model: str,
    system: str,
    user: str,
    timeout: int = 60,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> dict[str, Any]:
    """One hardened JSON-mode Gemini generateContent call.

    Used ONLY as the independent eval judge in eval_harness.py -- a
    different provider family than the Mistral pre-stage/translator, so
    judge and judged never share a model. Google's REST auth puts the key
    in the query string (their standard, not this module's choice); the
    key is never logged and the URL is never included in any exception
    message this module raises.
    """
    if not api_key or api_key != api_key.strip():
        raise TransportError("invalid Gemini API key")
    if not model or len(model) > 256:
        raise TransportError("invalid Gemini model id")
    body = json.dumps(
        {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json",
            },
        },
        ensure_ascii=False,
    ).encode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    http_status = None
    transport_failure = None
    raw = b""
    try:
        with _urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        http_status = int(exc.code)
        try:
            raw = exc.read(2000)
        except Exception:
            raw = b""
    except (URLError, TimeoutError, OSError) as exc:
        transport_failure = type(exc).__name__
    finally:
        api_key = ""
        request = None
        url = ""
    if http_status is not None:
        raise TransportError(f"Gemini HTTP failure status={http_status}")
    if transport_failure is not None:
        raise TransportError(f"Gemini transport failure type={transport_failure}")
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TransportError("Gemini response envelope is not JSON") from exc
    try:
        text = envelope["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise TransportError("Gemini response missing candidate text") from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TransportError("Gemini candidate text is not JSON") from exc
    receipt = {
        "provider": "gemini",
        "model_requested": model,
        "response_sha256": hashlib.sha256(raw).hexdigest(),
    }
    return {"payload": payload, "receipt": receipt}


import re as _re
import threading as _threading

_ROT_LOCK = _threading.Lock()
_ROT_INDEX = 0

# Statuslagen, bei denen ein ANDERER Schluessel helfen kann: Ratelimit und
# voruebergehende Serverfehler. Bei 401/403 (Token kaputt) oder 4xx-Client-
# fehlern hilft Rotation NICHT -- dann sofort durchreichen, nicht drei Tokens
# an derselben kaputten Anfrage verbrennen.
def _rotierbar(fehler: "TransportError") -> bool:
    m = _re.search(r"status=(\d{3})", str(fehler))
    if not m:
        return True  # Netz-/Verbindungsfehler ohne Status: anderer Schluessel kann gehen
    code = int(m.group(1))
    return code == 429 or 500 <= code <= 599


def mistral_chat_json_rotating(*, keys, **kw):
    """mistral_chat_json ueber mehrere Token: Round-Robin + Failover bei 429/5xx.

    keys: Liste der Mistral-Token. Jeder Aufruf startet beim naechsten (streut
    die Last); schlaegt einer rotierbar fehl, wird der naechste probiert, bis
    alle durch sind. Erst wenn ALLE fehlschlagen, fliegt der letzte Fehler.
    """
    global _ROT_INDEX
    keys = [k for k in (keys or []) if k]
    if not keys:
        raise RuntimeError("no Mistral key available")
    n = len(keys)
    with _ROT_LOCK:
        start = _ROT_INDEX % n
        _ROT_INDEX = (_ROT_INDEX + 1) % n
    letzter = None
    for off in range(n):
        key = keys[(start + off) % n]
        try:
            return mistral_chat_json(api_key=key, **kw)
        except TransportError as e:
            letzter = e
            if _rotierbar(e) and off < n - 1:
                continue  # naechsten Schluessel probieren
            raise
    if letzter:
        raise letzter
    raise RuntimeError("no Mistral key available")
