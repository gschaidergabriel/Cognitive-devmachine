#!/usr/bin/env python3
"""Install deterministic typed architecture-delta materialization on the active swarm fabric.

This is deliberately a post-v3 bridge: v3 owns accelerator/source grounding and economic
route authority; this module only converts successful worker output into bounded typed
candidate sidecars for Evidence Forge.
"""
from __future__ import annotations

import hashlib
from typing import Any

from free_swarm_delta_ingress import CANDIDATE_SCHEMA, parse_questions, parse_worker_delta

_INSTALLED = False


def install(core) -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    original_append = core.base.JsonlSink.append

    def append_sidecar(path, record: dict[str, Any]) -> None:
        sink = core.base.JsonlSink(path)
        original_append(sink, record)

    def ingress_aware_append(self, row: dict[str, Any]) -> None:
        if self.path.name != "workers.jsonl" or not isinstance(row, dict):
            original_append(self, row)
            return

        enriched = dict(row)
        status = enriched.get("http_status")
        text = str(enriched.get("text") or "")
        ingress = None
        questions: list[str] = []
        if isinstance(status, int) and 200 <= status < 300:
            ingress = parse_worker_delta(text)
            questions = parse_questions(text)
            enriched["delta_ingress"] = {
                "schema": ingress["schema"],
                "status": ingress["status"],
                "valid": ingress["valid"],
                "ready_for_forge": ingress["ready_for_forge"],
                "reasons": ingress["reasons"],
                "proposal_sha256": ingress["proposal_sha256"],
            }

        original_append(self, enriched)

        if ingress and ingress["valid"]:
            worker_sha = str(
                enriched.get("text_sha256")
                or hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
            )
            record = {
                "schema": CANDIDATE_SCHEMA,
                "ingress_schema": ingress["schema"],
                "provider": str(enriched.get("provider") or ""),
                "model": str(enriched.get("model") or ""),
                "role": str(enriched.get("role") or ""),
                "worker_serial": enriched.get("worker_serial"),
                "logical_worker_slot": enriched.get("logical_worker_slot"),
                "repo_head_at_prompt": enriched.get("repo_head_at_prompt") or enriched.get("repo_head"),
                "worker_text_sha256": worker_sha,
                "proposal_sha256": ingress["proposal_sha256"],
                "ready_for_forge": ingress["ready_for_forge"],
                "proposal": ingress["proposal"],
            }
            append_sidecar(self.path.parent / "architecture_deltas.jsonl", record)

        for question in questions:
            append_sidecar(
                self.path.parent / "open_research_questions.jsonl",
                {
                    "schema": "CLAY_OPEN_RESEARCH_QUESTION/v1",
                    "question_sha256": hashlib.sha256(question.encode("utf-8")).hexdigest(),
                    "question": question,
                    "provider": str(enriched.get("provider") or ""),
                    "model": str(enriched.get("model") or ""),
                    "role": str(enriched.get("role") or ""),
                },
            )

    core.base.JsonlSink.append = ingress_aware_append
    _INSTALLED = True
