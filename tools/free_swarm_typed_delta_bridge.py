#!/usr/bin/env python3
"""Materialize validated Free-Swarm deltas as typed, hash-bound Forge sidecars.

The current v3/model-health/economic route stack remains authoritative. This module
only observes successful worker rows after those gates and writes noncanonical typed
candidate sidecars. It creates no truth/effect authority.

For a successful worker row, sidecars are flushed before the enriched worker record.
That ordering is deliberate: a crash may leave an orphan sidecar, but must never make
a current typed worker visible without the sidecar required by fail-closed Forge ingest.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from free_swarm_delta_ingress import SCHEMA as INGRESS_SCHEMA, parse_questions, parse_worker_delta

CANDIDATE_SCHEMA = "CLAY_ARCHITECTURE_DELTA_CANDIDATE/v1"
_INSTALLED = False


def install(core) -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    original_append = core.base.JsonlSink.append

    def append_line(path: Path, record: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            fh.flush()

    async def ingress_aware_append(self, row: dict[str, Any]) -> None:
        if self.path.name != "workers.jsonl" or not isinstance(row, dict):
            await original_append(self, row)
            return

        enriched = dict(row)
        status = enriched.get("http_status")
        text = str(enriched.get("text") or "")
        ingress = None
        questions: list[str] = []
        candidate_record: dict[str, Any] | None = None
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
            if ingress["valid"]:
                candidate_record = {
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

        # Preserve JsonlSink's asynchronous serialization boundary. Sidecars are
        # direct sibling JSONL files, not JsonlSink output directories. Write them
        # and the worker row under the same sink lock, with the worker last, so a
        # visible typed worker always has its required sidecar already durable.
        async with self._lock:
            if candidate_record is not None:
                append_line(self.path.parent / "architecture_deltas.jsonl", candidate_record)

            for question in questions:
                append_line(
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

            append_line(self.path, enriched)

    core.base.JsonlSink.append = ingress_aware_append
    _INSTALLED = True
