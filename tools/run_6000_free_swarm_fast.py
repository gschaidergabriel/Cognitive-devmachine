#!/usr/bin/env python3
"""High-I/O launcher for the accelerated 6000 logical Free Swarm."""
from __future__ import annotations
import asyncio
import concurrent.futures
import os
import threading

# Install throughput behavior before importing the gated fabric. Model-health
# routing is installed on the v2 scheduler before v3 captures/wraps
# ``next_key_model`` with the exact economic route gate. v5 then replaces only
# the logical worker conversion call with two-stage exact-source synthesis. The
# post-v5 observer still wraps, never replaces, the v3 network authority.
import run_free_go_swarm as base
import run_24h_entityos_swarm as opt
import free_swarm_accelerator_v2 as accelerator
accelerator.install(base, opt)

import run_6000_free_swarm as fabric_v2
import free_swarm_model_health_v1 as model_health
model_health.install_scheduler(fabric_v2)

import run_6000_free_swarm_v5 as fabric
model_health.bind_request_observer(fabric)
import free_swarm_conversion_backpressure_872 as conversion_backpressure
import free_swarm_backfill_scheduler as historical_backfill
import free_swarm_typed_ingress_wiring_878 as typed_ingress

# Wrap the final worker-prompt authority after v2/v3/v5 have installed their own
# routing/synthesis behavior. While historical backlog exists, roughly 75% of
# logical calls become extraction/structuring passes over already-paid-for FREE
# worker output instead of producing more raw research tokens.
historical_backfill.install(base)

# Reuse the existing CLAY_ARCHITECTURE_DELTA_INGRESS/v1 classifier at the final
# successful v5 record boundary. This decorates append-only worker material only;
# it does not replace v3 network/economic routing, v5 synthesis, or Forge authority.
typed_ingress.install_live(fabric)


def main() -> int:
    # Conversion before scale: while the exact evidence-qualified Forge ->
    # Distillery boundary is still at zero accepted dataset yield, lower only the
    # default/current throughput ceilings. This never raises an operator-provided
    # lower limit and automatically releases once qualified packets + tokens exist.
    conversion_backpressure.apply()
    workers=max(1,min(1024,int(os.getenv("CLAY_SWARM_HTTP_THREADS","512"))))
    try: threading.stack_size(1024*1024)
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
