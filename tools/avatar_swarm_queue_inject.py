#!/usr/bin/env python3
"""Inject one reviewed Avatar frontier packet into the existing Research Distillery queue.

This tool does not call providers, read credentials, start workers, mutate live Avatar
state, or grant evidence credit. It only adds the packet's bounded research questions
to the existing append/gated SQLite research queue using the canonical Distillery
`add_question` path.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_research_distillery as distillery

EXPECTED_SCHEMA = "CLAY_AVATAR_SWARM_FRONTIER/v1"
EXPECTED_SUBJECT = "12fd072d1332fcc93852d41c8acb6cae47d79a43"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inject a bounded Avatar frontier into the Free Swarm research queue")
    parser.add_argument("--task", required=True, help="Repo-relative CLAY_AVATAR_SWARM_FRONTIER/v1 JSON file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    task_path = (ROOT / args.task).resolve()
    try:
        task_path.relative_to(ROOT)
    except ValueError:
        raise SystemExit("task path must stay inside repository")

    task = json.loads(task_path.read_text(encoding="utf-8"))
    if task.get("schema") != EXPECTED_SCHEMA:
        raise SystemExit(f"unexpected task schema: {task.get('schema')!r}")

    subject = ((task.get("avatar_evidence_subject") or {}).get("research_commit") or "").strip()
    if subject != EXPECTED_SUBJECT:
        raise SystemExit(f"unexpected Avatar evidence subject: {subject!r}")

    questions = task.get("questions")
    if not isinstance(questions, list) or not (1 <= len(questions) <= 16):
        raise SystemExit("task questions must contain 1..16 entries")

    source = f"avatar-frontier:{subject}"
    root_problem = str(task.get("next_exact_gate") or "").strip()
    if len(root_problem) < 20:
        raise SystemExit("next_exact_gate missing")

    con = distillery.connect()
    results: list[dict[str, object]] = []
    for item in questions:
        if not isinstance(item, dict):
            raise SystemExit("question entry must be object")
        lane = str(item.get("lane") or "").strip()
        question = str(item.get("question") or "").strip()
        priority = float(item.get("priority", 1.0))
        if not lane or len(question) < 20:
            raise SystemExit("question lane/text missing")
        if not (0.0 < priority <= 100.0):
            raise SystemExit("question priority outside 0..100")
        added = distillery.add_question(
            con,
            question,
            root_problem=root_problem,
            priority=priority,
            worker_sha=source,
        )
        results.append({"lane": lane, "added": bool(added), "priority": priority})
    con.commit()

    rows = [
        dict(row)
        for row in con.execute(
            "SELECT id,question,priority,status,attempts,source_worker_sha "
            "FROM questions WHERE source_worker_sha=? ORDER BY priority DESC",
            (source,),
        ).fetchall()
    ]
    con.close()

    print(json.dumps({
        "schema": "CLAY_AVATAR_SWARM_QUEUE_INJECTION_RESULT/v1",
        "task": str(task_path.relative_to(ROOT)),
        "subject_commit": subject,
        "requested": len(questions),
        "results": results,
        "bound_rows": rows,
        "provider_calls_performed": 0,
        "live_avatar_mutation": 0,
        "credit_minted": 0,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
