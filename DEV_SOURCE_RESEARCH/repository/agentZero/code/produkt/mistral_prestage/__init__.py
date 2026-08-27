"""Mistral pre-stage + caveman-English translator for EntityOS.

Owner's design (F17, entityos-umbau-2026-08-18.md):

    user -> MISTRAL PRE-STAGE -> Zero (Claude Code) -> TRANSLATOR -> human

This package is a self-contained new module. It does NOT modify
terminal_hooks.py, retrieval.py, turn_lifecycle.py, store.py, service.py or
terminal_sessions.py -- those stay with the coordinating agent to wire in.
It owns only its own new `mv_*` SQLite tables (checked against the 105
existing wiki.db tables before naming; see store.py).
"""
