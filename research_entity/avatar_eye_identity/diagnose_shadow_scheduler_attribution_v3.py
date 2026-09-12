#!/usr/bin/env python3
"""Execute the v2 scheduler-attribution diagnostic with its one JS generator bug fixed.

v2 emitted one extra closing brace in the special-expression trigger.  Keep the
same exact diagnostic logic and identities; alter only that generator token.
Fail closed if the expected source fragment is not present exactly once.
"""
from __future__ import annotations

from pathlib import Path

source_path = Path(__file__).with_name("diagnose_shadow_scheduler_attribution_v2.py")
source = source_path.read_text(encoding="utf-8")
bad = '"return {special:_sonderLaeuft,phase:blinzelPhase};}})()",'
good = '"return {special:_sonderLaeuft,phase:blinzelPhase};})()",'
count = source.count(bad)
if count != 1:
    raise SystemExit(f"V2_TRIGGER_PATCH_PRECONDITION_FAILED count={count}")
patched = source.replace(bad, good, 1)
compile(patched, str(source_path) + ":v3", "exec")
namespace = {
    "__name__": "__main__",
    "__file__": str(source_path),
    "__package__": None,
}
exec(compile(patched, str(source_path) + ":v3", "exec"), namespace, namespace)
