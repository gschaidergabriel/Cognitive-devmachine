"""Test the GRID10_TORCH_THREADS env-var resolution logic used in
grid10_node.py::load_model_once() (2026-08-27, GRID10 latency concept).

Tests the resolution logic in isolation (no real model load needed).
"""
import os


def resolve_torch_threads() -> int:
    return int(os.environ.get("GRID10_TORCH_THREADS", "1"))


def test_default_is_one(monkeypatch):
    monkeypatch.delenv("GRID10_TORCH_THREADS", raising=False)
    assert resolve_torch_threads() == 1


def test_env_var_set_to_four(monkeypatch):
    monkeypatch.setenv("GRID10_TORCH_THREADS", "4")
    assert resolve_torch_threads() == 4


def test_env_var_set_to_two(monkeypatch):
    monkeypatch.setenv("GRID10_TORCH_THREADS", "2")
    assert resolve_torch_threads() == 2
