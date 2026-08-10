from __future__ import annotations

import argparse
import json

from . import telemetry


def main() -> None:
    parser = argparse.ArgumentParser(description="Surgical read/query interface for Frank telemetry")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("stats")
    sub.add_parser("maintain")

    q = sub.add_parser("query")
    q.add_argument("--start-ts", type=float)
    q.add_argument("--end-ts", type=float)
    q.add_argument("--module")
    q.add_argument("--category")
    q.add_argument("--severity")
    q.add_argument("--correlation-id")
    q.add_argument("--episode-id")
    q.add_argument("--session-id")
    q.add_argument("--build-id")
    q.add_argument("--state-key")
    q.add_argument("--entity-id")
    q.add_argument("--fts")
    q.add_argument("--json-path")
    q.add_argument("--json-equals")
    q.add_argument("--min-latency-ms", type=float)
    q.add_argument("--min-retention-rank", type=int)
    q.add_argument("--limit", type=int, default=200)
    q.add_argument("--no-payload", action="store_true")

    st = sub.add_parser("state-timeline")
    st.add_argument("--state-key", required=True)
    st.add_argument("--entity-id")
    st.add_argument("--episode-id")
    st.add_argument("--start-ts", type=float)
    st.add_argument("--end-ts", type=float)
    st.add_argument("--limit", type=int, default=1000)

    args = parser.parse_args()
    if args.cmd == "stats":
        result = telemetry.stats()
    elif args.cmd == "maintain":
        result = telemetry.maintain(force=True)
    elif args.cmd == "state-timeline":
        result = telemetry.state_timeline(
            args.state_key,
            entity_id=args.entity_id,
            episode_id=args.episode_id,
            start_ts=args.start_ts,
            end_ts=args.end_ts,
            limit=args.limit,
        )
    else:
        json_equals = args.json_equals
        if json_equals is not None:
            try:
                json_equals = json.loads(json_equals)
            except Exception:
                pass
        result = telemetry.query(
            start_ts=args.start_ts,
            end_ts=args.end_ts,
            module=args.module,
            category=args.category,
            severity=args.severity,
            correlation_id=args.correlation_id,
            episode_id=args.episode_id,
            session_id=args.session_id,
            build_id=args.build_id,
            state_key=args.state_key,
            entity_id=args.entity_id,
            fts=args.fts,
            json_path=args.json_path,
            json_equals=json_equals,
            min_latency_ms=args.min_latency_ms,
            min_retention_rank=args.min_retention_rank,
            limit=args.limit,
            include_payload=not args.no_payload,
        )
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
