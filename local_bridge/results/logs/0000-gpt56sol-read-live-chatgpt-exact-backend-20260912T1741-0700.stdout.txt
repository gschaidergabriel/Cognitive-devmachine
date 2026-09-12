#!/usr/bin/env python3
"""Exact ChatGPT backend for the first-class FranKenstein organ.

Preserves the existing two-phase send/harvest contract while using the
request-targeted browser adapter. This is transport only: no side DB, no
memory authority, and no fallback to a different model/provider.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from f2wp1207_chatgpt_harness_adapter import TargetedChatGPTHarness, _answer_from_payload


class ExactChatGPTBackend:
    def __init__(self, stern_module: Any):
        # Freeze the ORIGINAL harness capabilities now.  Terminal frontends
        # deliberately replace stern.chatgpt_senden/chatgpt_ernten with this
        # backend so the organ can keep the established two-phase contract.
        # Holding the mutable stern module itself would make adapter.dispatch()
        # call this backend again after that replacement -> infinite recursion.
        # The frozen facade keeps one browser authority while allowing the
        # public stern entrypoints to be rebound safely.
        raw_harness = SimpleNamespace(
            chatgpt_senden=stern_module.chatgpt_senden,
            _chatgpt_browse=stern_module._chatgpt_browse,
            _chatgpt_lock=stern_module._chatgpt_lock,
            _chatgpt_login_sicherstellen=stern_module._chatgpt_login_sicherstellen,
        )
        self.adapter = TargetedChatGPTHarness(raw_harness)
        self._pending: dict[str, Any] | None = None

    def send(self, prompts: list[str], *, num_workers: int | None = None,
             ram_schwelle_mb: int | None = None, **_: Any) -> dict:
        # Exactly one coordinator prompt per organ turn. The model may create
        # specialized tool/workers inside the task, but we never duplicate the
        # coordinator merely because a local budget is >1.
        if len(prompts or []) != 1:
            return {"ok": False, "grund": "exact ChatGPT organ accepts one coordinator prompt"}
        sent = self.adapter.dispatch(
            [str(prompts[0])], num_workers_each=1,
            ram_schwelle_mb=ram_schwelle_mb,
        )
        self._pending = sent if sent.get("ok") else None
        return {
            "ok": bool(sent.get("ok")),
            "exact_chatgpt": True,
            "urls": sent.get("urls") or [],
            "send": sent.get("send"),
            "grund": sent.get("error"),
        }

    def harvest(self, *, timeout_s: float = 900.0, **_: Any) -> dict:
        pending = self._pending
        self._pending = None
        if not pending:
            return {"ok": False, "exact_chatgpt": True, "grund": "nothing pending", "results": []}
        harvested = self.adapter.harvest_urls(
            pending.get("urls") or [], timeout_s=min(float(timeout_s), 900.0)
        )
        results = []
        for row in harvested.get("results") or []:
            answer = _answer_from_payload(row.get("payload"), row.get("page_text") or "")
            results.append({
                "antwort": answer,
                "url": row.get("url"),
                "marker": row.get("marker"),
                "payload": row.get("payload"),
            })
        return {
            "ok": bool(harvested.get("ok")) and bool(results) and bool(results[-1].get("antwort")),
            "exact_chatgpt": True,
            "results": results,
            "grund": harvested.get("error"),
        }
