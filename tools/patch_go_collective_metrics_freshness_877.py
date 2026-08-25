#!/usr/bin/env python3
"""One-shot deterministic integration patch for the existing GO metrics publisher.

The patch is deliberately exact-needle and idempotent.  If main has moved such that the
expected publisher structure is no longer present, it fails closed rather than guessing.
"""
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "free swarm/go_collective_metrics.py"
MARKER = "from tools.go_collective_metrics_freshness_v1 import capture_input_snapshot, publish_fresh_outputs"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH_NEEDLE_{label}_COUNT_{count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        required = [
            "input_snapshot = capture_input_snapshot(repo, args.artifacts)",
            "publish_receipt = publish_fresh_outputs(",
            "COLLECTIVE_METRICS_FRESHNESS_RECEIPT.json",
        ]
        missing = [item for item in required if item not in text]
        if missing:
            raise SystemExit("PARTIAL_FRESHNESS_PATCH:" + ",".join(missing))
        print("ALREADY_PATCHED")
        return 0

    text = replace_once(
        text,
        "from typing import Any, Iterable\n\nSCHEMA = \"CLAY_GO_COLLECTIVE_METRICS/v1\"",
        "from typing import Any, Iterable\n\n"
        "# The script can be executed as `python free swarm/go_collective_metrics.py`, where\n"
        "# sys.path otherwise contains only the directory with the space. Bind the repository\n"
        "# root explicitly so the freshness substrate is one shared implementation for CLI/tests.\n"
        "import sys\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n"
        "from tools.go_collective_metrics_freshness_v1 import capture_input_snapshot, publish_fresh_outputs\n\n"
        "SCHEMA = \"CLAY_GO_COLLECTIVE_METRICS/v1\"",
        "IMPORT",
    )

    text = replace_once(
        text,
        "    if config.get(\"schema\") != \"CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1\":\n"
        "        raise SystemExit(\"GO_METRICS_CONFIG_REQUIRED\")\n\n"
        "    workers = explicit_worker_rows(repo)",
        "    if config.get(\"schema\") != \"CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1\":\n"
        "        raise SystemExit(\"GO_METRICS_CONFIG_REQUIRED\")\n\n"
        "    # Capture exact consumed input families before aggregation. The publisher re-reads\n"
        "    # them under the publication lock and rejects a stale calculation if any byte moved.\n"
        "    input_snapshot = capture_input_snapshot(repo, args.artifacts)\n\n"
        "    workers = explicit_worker_rows(repo)",
        "SNAPSHOT",
    )

    text = replace_once(
        text,
        "    out_json.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + \"\\n\", encoding=\"utf-8\")\n"
        "    out_md.write_text(md, encoding=\"utf-8\")",
        "    publish_receipt = publish_fresh_outputs(\n"
        "        repo=repo,\n"
        "        artifacts=args.artifacts,\n"
        "        result=result,\n"
        "        markdown_text=md,\n"
        "        out_json=out_json,\n"
        "        out_md=out_md,\n"
        "        expected_input_snapshot=input_snapshot,\n"
        "        receipt_path=out_json.with_name(\"COLLECTIVE_METRICS_FRESHNESS_RECEIPT.json\"),\n"
        "    )",
        "PUBLISH",
    )

    text = replace_once(
        text,
        "    print(out_json)\n    print(out_md)\n    h = result[\"aggregate\"][\"hcu_confidence\"]",
        "    print(out_json)\n    print(out_md)\n"
        "    print(json.dumps({\"freshness_publish\": publish_receipt}, sort_keys=True))\n"
        "    h = result[\"aggregate\"][\"hcu_confidence\"]",
        "PRINT_RECEIPT",
    )

    TARGET.write_text(text, encoding="utf-8")
    print("PATCHED", TARGET)
    return 0


if __name__ == "__main__":
    sys.exit(main())
