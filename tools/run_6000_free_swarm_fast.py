#!/usr/bin/env python3
"""High-I/O-concurrency launcher for the route-bound 6000 logical Free Swarm."""
from __future__ import annotations
import asyncio
import concurrent.futures
import os
import threading
import run_6000_free_swarm_v3 as fabric


def main() -> int:
    workers=max(64,min(1024,int(os.getenv("CLAY_SWARM_HTTP_THREADS","512"))))
    # Calls are blocking urllib operations executed via asyncio.to_thread. The
    # enlarged pool prevents the Python default executor from becoming the local
    # concurrency ceiling; provider/shared-quota gates remain authoritative.
    try: threading.stack_size(2*1024*1024)
    except (ValueError,RuntimeError): pass
    loop=asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    ex=concurrent.futures.ThreadPoolExecutor(max_workers=workers,thread_name_prefix="clay-free-http")
    loop.set_default_executor(ex)
    try:
        return int(loop.run_until_complete(fabric.run(fabric.parse_args())))
    finally:
        try: loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception: pass
        loop.close()
        ex.shutdown(wait=False,cancel_futures=True)

if __name__=="__main__":
    raise SystemExit(main())
