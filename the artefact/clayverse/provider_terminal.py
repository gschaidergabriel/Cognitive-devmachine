from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path


MAX_RESPONSE_BYTES = 512 * 1024


def _require_secretless_client_env() -> None:
    for name in ("MISTRAL_API_KEY", "CLAYVERSE_LLM_API_TOKEN"):
        if os.environ.get(name):
            raise RuntimeError("provider credential must not enter the tmux terminal client")


def _socket_path() -> Path:
    raw = os.environ.get("CLAYVERSE_PROVIDER_BROKER_SOCKET", "").strip()
    path = Path(raw)
    if not raw or not path.is_absolute() or "\x00" in raw or "\n" in raw or "\r" in raw:
        raise RuntimeError("provider broker socket path is invalid")
    return path


def _read_response(conn: socket.socket) -> dict:
    data = bytearray()
    while True:
        chunk = conn.recv(min(65536, MAX_RESPONSE_BYTES + 1 - len(data)))
        if not chunk:
            raise RuntimeError("provider broker closed before response")
        data.extend(chunk)
        if len(data) > MAX_RESPONSE_BYTES:
            raise RuntimeError("provider broker response exceeds bound")
        if b"\n" in chunk:
            frame, trailing = bytes(data).split(b"\n", 1)
            if trailing:
                raise RuntimeError("provider broker returned multiple frames")
            try:
                payload = json.loads(frame.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise RuntimeError("provider broker returned invalid JSON") from exc
            if not isinstance(payload, dict):
                raise RuntimeError("provider broker response shape invalid")
            return payload


def request(prompt: str) -> dict:
    _require_secretless_client_env()
    if not isinstance(prompt, str) or not prompt or len(prompt) > 100_000 or "\x00" in prompt:
        raise ValueError("prompt is invalid")
    payload = (json.dumps({"prompt": prompt, "resources": []}, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    path = _socket_path()
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        conn.connect(str(path))
        conn.sendall(payload)
        return _read_response(conn)
    finally:
        conn.close()


def main() -> int:
    _require_secretless_client_env()
    _socket_path()
    print("ClayVerse API provider terminal — canonical UnifiedDB / EffectGate path")
    print("Type /quit to return only by ending this provider pane.")
    while True:
        try:
            prompt = input("clay> ")
        except EOFError:
            return 0
        if prompt == "/quit":
            return 0
        if not prompt:
            continue
        try:
            payload = request(prompt)
        except Exception as exc:
            print(f"[ClayVerse] provider turn failed: {type(exc).__name__}", file=sys.stderr)
            continue
        if payload.get("ok") is not True:
            print(f"[ClayVerse] provider turn rejected: {payload.get('error_type', 'UNKNOWN')}", file=sys.stderr)
            continue
        text = str(payload.get("text", ""))
        if text:
            print(text)
        if payload.get("outcome") is not None:
            print("[effect outcome] " + json.dumps(payload["outcome"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
