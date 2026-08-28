#!/usr/bin/env python3
"""Ordinary-node SQLite read-only connection adapter for EntityOS/HCU S1.

This is a narrow hardening wrapper around ``xeno_s1_sqlite_cas_v1``. It does not
create another state authority. Ordinary-node callers receive a SQLite URI opened
with ``mode=ro`` plus ``PRAGMA query_only=ON`` and the existing adapter revalidates
the exact persisted S1 schema/epoch/digest before the connection is returned.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Union

from xeno_s1_sqlite_cas_v1 import S1StoreError, read_snapshot

PathLike = Union[str, Path]


def open_ordinary_s1_read_only(path: PathLike) -> sqlite3.Connection:
    """Open one validated S1 database for ordinary-node reads only.

    The returned handle cannot be used for SQL writes even if ordinary-node code
    bypasses the higher-level read API. This is defense in depth for the owner law
    ``ORDINARY_NODE_S1_ACCESS = READ_ONLY``; it does not substitute for OS/process
    isolation and does not grant any S0/effect authority.
    """
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise S1StoreError("S1_STORE_FILE_REQUIRED")
    uri = resolved.as_uri() + "?mode=ro"
    try:
        db = sqlite3.connect(uri, uri=True, isolation_level=None, timeout=30)
        db.execute("PRAGMA query_only=ON")
        read_snapshot(db)
        return db
    except Exception:
        try:
            db.close()
        except (NameError, Exception):
            pass
        raise
