#!/usr/bin/env python3
"""Materialize validated Free-Swarm deltas as typed, hash-bound Forge sidecars.

The current v3/model-health/economic route stack remains authoritative. This module
only observes successful worker rows after those gates and writes noncanonical typed
candidate sidecars. It creates no truth/effect authority.
"""
from __future__ import annotations

import hashlib
from typing import Any

from free_swarm_delta_ingress import SCHEMA as INGRESS_SCHEMA, parse_questions, parse_worker_delta

CANDIDATE_SCHEMA = "CLAY_ARCHITECTURE_DELTA_CANDIDATE/v1"
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
            worker_sha = str(
                enriched.get("text_sha256")
                or hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
            ).strip().lower()
            repo_head = str(
                enriched.get("repo_head_at_prompt") or enriched.get("repo_head") or ""
            ).strip().lower()
            ingress = parse_worker_delta(
                text,
                repo_head_at_prompt=repo_head or None,
                worker_sha256=worker_sha or None,
            )
            questions = parse_questions(text)
            enriched["delta_ingress"] = {
                "schema": ingress["schema"],
                "status": ingress["status"],
                "valid": bool(ingress["valid"]),
                "ready_for_forge": bool(ingress["ready_for_forge"]),
                "reasons": list(ingress["reasons"]),
                "proposal_sha256": ingress.get("proposal_sha256"),
            }

        original_append(self, enriched)

        if ingress and ingress["valid"]:
            record = {
                "schema": CANDIDATE_SCHEMA,
                "ingress_schema": INGRESS_SCHEMA,
                "provider": str(enriched.get("provider") or ""),
                "model": str(enriched.get("model") or ""),
                "role": str(enriched.get("role") or ""),
                "worker_serial": enriched.get("worker_serial"),
                "logical_worker_slot": enriched.get("logical_worker_slot"),
                "repo_head_at_prompt": ingress.get("repo_head_at_prompt") or "",
                "worker_text_sha256": ingress.get("worker_sha256") or "",
                "proposal_sha256": ingress["proposal_sha256"],
                "ready_for_forge": bool(ingress["ready_for_forge"]),
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
