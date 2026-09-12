from __future__ import annotations

"""Compatibility surface for the former OUTER_SPOOL supervisor.

The canonical implementation now lives in :mod:`omega.supervisor`.  Keeping this
module as an alias preserves existing launchers/imports without maintaining a second
supervision loop or a second transport configuration authority.
"""

from .supervisor import CHILDREN, Supervisor, main

__all__ = ["CHILDREN", "Supervisor", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
