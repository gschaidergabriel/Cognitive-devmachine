#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Targeted response adapter for the EXISTING ChatGPT browser harness.

This is transport, not cognition and not persistence authority.
It reuses stern.py's login gate, flock and gstack-browse daemon. The only
file it reads is the harness' pre-existing technical send ledger
~/scripts/chatgpt_burst_state/sent_urls_v2.txt in order to identify URLs
created by THIS dispatch. It never creates a memory/database.

Why this exists: stern.chatgpt_ernten() intentionally returns harvest counts,
not response bodies, and its legacy full-scan walks every historical URL.
An integrated organ needs exact request->response attribution.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SENT_URLS = Path.home() / "scripts" / "chatgpt_burst_state" / "sent_urls_v2.txt"
_RESULT_PREFIXES = (
    "FRANK_ORGAN_RESULT=",
    "FRANK_COORDINATOR_PLAN=",
    "FRANK_WORKER_RESULT=",
)


class HarnessAdapterError(RuntimeError):
    pass


@dataclass(frozen=True)
class ConversationResult:
    url: str
    page_text: str
    marker: str | None
    payload: dict | None


def _ledger_rows() -> list[tuple[str, str, str]]:
    if not SENT_URLS.is_file():
        return []
    rows: list[tuple[str, str, str]] = []
    for raw in SENT_URLS.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = raw.split("\t")
        if len(parts) < 2:
            continue
        wid = parts[0].strip()
        url = parts[1].strip()
        sent_at = parts[2].strip() if len(parts) > 2 else ""
        if url:
            rows.append((wid, url, sent_at))
    return rows


def _new_urls(before: list[tuple[str, str, str]], after: list[tuple[str, str, str]]) -> list[str]:
    # Do NOT key on worker_id: each burst restarts numbering at 1. URL is the
    # globally useful identity, exactly as the existing harvest script notes.
    old = {url for _wid, url, _ts in before}
    return [url for _wid, url, _ts in after if url not in old]


def _extract_marker(page_text: str) -> tuple[str | None, dict | None]:
    # ChatGPT may render code fences/spacing, but the requested marker is a
    # single logical line. Search from the end because the page also contains
    # previous messages in the same conversation.
    lines = (page_text or "").splitlines()
    for line in reversed(lines):
        s = line.strip().strip("`")
        for prefix in _RESULT_PREFIXES:
            pos = s.find(prefix)
            if pos < 0:
                continue
            candidate = s[pos + len(prefix):].strip()
            try:
                obj = json.loads(candidate)
            except Exception:
                # Renderers sometimes append small punctuation after the JSON.
                decoder = json.JSONDecoder()
                try:
                    obj, _end = decoder.raw_decode(candidate)
                except Exception:
                    continue
            if isinstance(obj, dict):
                return prefix[:-1], obj
    return None, None


def _answer_from_payload(payload: dict | None, fallback: str) -> str:
    if payload:
        for key in ("answer", "summary", "result", "response"):
            v = payload.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
    # Last-resort transport fallback only. It is explicitly marked raw by
    # callers and bounded so browser chrome/sidebar text cannot explode DB size.
    return (fallback or "")[-20000:].strip()


class TargetedChatGPTHarness:
    def __init__(self, stern_module: Any):
        self.stern = stern_module

    def _require_capabilities(self) -> None:
        required = ("chatgpt_senden", "_chatgpt_browse", "_chatgpt_lock", "_chatgpt_login_sicherstellen")
        missing = [x for x in required if not hasattr(self.stern, x)]
        if missing:
            raise HarnessAdapterError(f"stern missing existing harness capabilities: {missing}")

    def dispatch(self, prompts: list[str], *, num_workers_each: int = 1,
                 ram_schwelle_mb: int | None = None) -> dict:
        """Send distinct prompts through existing harness and return only new URLs.

        Each prompt uses the same requested replica count. For coordinator and
        specialized workers callers normally use 1, preventing N duplicate
        coordinators while preserving the existing browser sender.
        """
        self._require_capabilities()
        clean = [re.sub(r"\s+", " ", str(p)).strip() for p in prompts if str(p).strip()]
        if not clean:
            return {"ok": False, "error": "no prompts", "urls": []}
        before = _ledger_rows()
        send = self.stern.chatgpt_senden(
            clean,
            num_workers=max(1, min(30, int(num_workers_each))),
            ram_schwelle_mb=ram_schwelle_mb,
            lock_timeout_s=1200.0,
        )
        after = _ledger_rows()
        urls = _new_urls(before, after)
        if not send.get("ok"):
            return {"ok": False, "send": send, "urls": urls,
                    "error": send.get("grund") or "chatgpt_senden failed"}
        if send.get("fallback_verwendet"):
            # This adapter is for ChatGPT itself. Free-pool is a separate organ.
            return {"ok": False, "send": send, "urls": urls,
                    "error": "ChatGPT browser unavailable; fallback is not ChatGPT organ"}
        if not urls:
            return {"ok": False, "send": send, "urls": [],
                    "error": "send reported success but no new conversation URL was attributed"}
        return {"ok": True, "send": send, "urls": urls}

    def harvest_urls(self, urls: Iterable[str], *, timeout_s: float = 420.0,
                     poll_s: float = 3.0) -> dict:
        """Read ONLY the supplied conversation URLs; no shared full-scan.

        We never reload/poll-goto repeatedly. Each URL is navigated once, then
        only the page state/text is observed until a marker appears or ChatGPT
        is no longer generating. This avoids the known rate-limit feedback loop.
        """
        self._require_capabilities()
        urls = [str(u) for u in urls if str(u).startswith("https://chatgpt.com/")]
        if not urls:
            return {"ok": False, "error": "no valid chatgpt URLs", "results": []}
        login = self.stern._chatgpt_login_sicherstellen()
        if not login.get("eingeloggt"):
            return {"ok": False, "needs_login": True, "login": login, "results": []}

        out: list[ConversationResult] = []
        try:
            with self.stern._chatgpt_lock(timeout_s=1200.0):
                for url in urls:
                    nav = self.stern._chatgpt_browse("goto", url, timeout=20.0)
                    if not nav.get("ok"):
                        raise HarnessAdapterError(f"goto failed for {url}: {nav}")
                    deadline = time.monotonic() + timeout_s
                    last_text = ""
                    while time.monotonic() < deadline:
                        txt_r = self.stern._chatgpt_browse("text", timeout=15.0)
                        if txt_r.get("ok"):
                            last_text = txt_r.get("stdout") or ""
                            marker, payload = _extract_marker(last_text)
                            if payload is not None:
                                out.append(ConversationResult(url, last_text, marker, payload))
                                break
                        snap = self.stern._chatgpt_browse("snapshot", "-i", timeout=15.0)
                        generating = "Stop answering" in (snap.get("stdout") or "") if snap.get("ok") else True
                        if last_text and not generating and "Worked for" in last_text:
                            marker, payload = _extract_marker(last_text)
                            out.append(ConversationResult(url, last_text, marker, payload))
                            break
                        time.sleep(max(1.0, poll_s))
                    else:
                        raise HarnessAdapterError(f"timeout waiting for ChatGPT response: {url}")
        except Exception as e:
            return {"ok": False, "error": str(e), "results": [r.__dict__ for r in out]}
        return {"ok": len(out) == len(urls), "results": [r.__dict__ for r in out]}

    def infer_one(self, prompt: str, *, ram_schwelle_mb: int | None = None) -> dict:
        sent = self.dispatch([prompt], num_workers_each=1, ram_schwelle_mb=ram_schwelle_mb)
        if not sent.get("ok"):
            return sent
        harvested = self.harvest_urls(sent["urls"])
        if not harvested.get("ok"):
            return {"ok": False, "send": sent, "harvest": harvested,
                    "error": harvested.get("error")}
        r = harvested["results"][-1]
        answer = _answer_from_payload(r.get("payload"), r.get("page_text") or "")
        return {"ok": bool(answer), "response": answer, "payload": r.get("payload"),
                "url": r.get("url"), "send": sent.get("send")}

    def infer_many(self, prompts: list[str], *, ram_schwelle_mb: int | None = None) -> dict:
        sent = self.dispatch(prompts, num_workers_each=1, ram_schwelle_mb=ram_schwelle_mb)
        if not sent.get("ok"):
            return sent
        harvested = self.harvest_urls(sent["urls"])
        results = []
        for r in harvested.get("results", []):
            results.append({"url": r.get("url"), "payload": r.get("payload"),
                            "response": _answer_from_payload(r.get("payload"), r.get("page_text") or "")})
        return {"ok": bool(harvested.get("ok")), "results": results,
                "send": sent.get("send"), "error": harvested.get("error")}
