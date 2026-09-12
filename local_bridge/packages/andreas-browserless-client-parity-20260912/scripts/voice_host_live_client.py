#!/usr/bin/env python3
"""Launch the persistent ChatGPT client against the *live* Frankenstein stern.

The client adapter/TITAN code comes from the integration checkout, but the
canonical runtime authority is the stern.py that the production conversation
service actually uses under ~/.claude/star.  Preloading that module as
``stern`` prevents voice_host_agent.py from accidentally importing a stale
repository copy and creating a parallel Frankenstein state/runtime view.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE_STAR = Path(os.environ.get("FRANK_LIVE_STAR_DIR") or (Path.home() / ".claude" / "star"))
LIVE_STERN = LIVE_STAR / "stern.py"


def load_live_stern(path: Path = LIVE_STERN):
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"live stern.py not found: {path}")
    live_dir = str(path.parent)
    if live_dir not in sys.path:
        sys.path.insert(0, live_dir)
    spec = importlib.util.spec_from_file_location("stern", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load live stern.py: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["stern"] = module
    spec.loader.exec_module(module)
    loaded = Path(getattr(module, "__file__", "")).resolve()
    if loaded != path:
        raise RuntimeError(f"stern provenance mismatch: expected {path}, got {loaded}")
    return module


def main() -> int:
    stern = load_live_stern()
    # Keep the integration directory importable for the bounded adapter,
    # identity assembly and finished TITAN-MC module.
    here = str(HERE)
    if here not in sys.path:
        sys.path.insert(0, here)
    import voice_host_agent

    # Hard provenance assertion before opening the listening socket.
    actual = Path(getattr(voice_host_agent.stern, "__file__", "")).resolve()
    expected = LIVE_STERN.expanduser().resolve()
    if actual != expected:
        raise RuntimeError(f"voice host imported non-live stern: {actual} != {expected}")
    return voice_host_agent.main()


if __name__ == "__main__":
    raise SystemExit(main())
