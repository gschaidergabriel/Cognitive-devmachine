#!/usr/bin/env python3
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tools" / "clay_profile_pipeline_runtime.py"


def _runtime_class() -> ast.ClassDef:
    tree = ast.parse(RUNTIME.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ProfilePipelineRuntime":
            return node
    raise AssertionError("ProfilePipelineRuntime missing")


def _method(cls: ast.ClassDef, name: str) -> ast.FunctionDef:
    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"method missing: {name}")


def _call_name(call: ast.Call) -> str:
    target = call.func
    parts: list[str] = []
    while isinstance(target, ast.Attribute):
        parts.append(target.attr)
        target = target.value
    if isinstance(target, ast.Name):
        parts.append(target.id)
    return ".".join(reversed(parts))


class RuntimeCognitiveFabricWiringTests(unittest.TestCase):
    def test_admission_effect_is_allowed_dispatched_and_delegates_once(self) -> None:
        cls = _runtime_class()
        init = _method(cls, "__init__")
        effect = _method(cls, "effect")
        handler = _method(cls, "_pipeline_cognitive_fabric_admit")

        allowed = set()
        for node in ast.walk(init):
            if not isinstance(node, ast.Assign):
                continue
            if not any(
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
                and target.attr == "allowed_effects"
                for target in node.targets
            ):
                continue
            if isinstance(node.value, ast.Set):
                allowed = {
                    item.value
                    for item in node.value.elts
                    if isinstance(item, ast.Constant) and isinstance(item.value, str)
                }
        self.assertIn("pipeline_cognitive_fabric_admit", allowed)

        dispatch_ok = False
        for node in ast.walk(effect):
            if not isinstance(node, ast.Dict):
                continue
            for key, value in zip(node.keys, node.values):
                if (
                    isinstance(key, ast.Constant)
                    and key.value == "pipeline_cognitive_fabric_admit"
                    and isinstance(value, ast.Attribute)
                    and isinstance(value.value, ast.Name)
                    and value.value.id == "self"
                    and value.attr == "_pipeline_cognitive_fabric_admit"
                ):
                    dispatch_ok = True
        self.assertTrue(dispatch_ok)

        calls = [_call_name(node) for node in ast.walk(handler) if isinstance(node, ast.Call)]
        self.assertEqual(
            calls.count("cognitive_fabric_binding.admit_profile_runtime_payload"),
            1,
        )
        self.assertFalse(
            {"self._db", "self._pipeline_commit", "self._inference_generate"} & set(calls)
        )

    def test_cognition_bootstrap_is_inside_existing_pipeline_init_transaction(self) -> None:
        cls = _runtime_class()
        method = _method(cls, "_pipeline_init")
        calls = [node for node in ast.walk(method) if isinstance(node, ast.Call)]

        prepare_lines = [
            node.lineno
            for node in calls
            if _call_name(node) == "cognition_bootstrap.prepare_connection"
        ]
        install_lines = [
            node.lineno
            for node in calls
            if _call_name(node) == "cognition_bootstrap.install_cognition_schema"
        ]
        begin_lines = [
            node.lineno
            for node in calls
            if _call_name(node) == "db.execute"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "BEGIN IMMEDIATE"
        ]
        entity_insert_lines = [
            node.lineno
            for node in calls
            if _call_name(node) == "db.execute"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
            and "INSERT OR IGNORE INTO entity_state" in node.args[0].value
        ]

        self.assertEqual(len(prepare_lines), 1)
        self.assertEqual(len(install_lines), 1)
        self.assertEqual(len(begin_lines), 1)
        self.assertEqual(len(entity_insert_lines), 1)
        self.assertLess(prepare_lines[0], begin_lines[0])
        self.assertLess(begin_lines[0], entity_insert_lines[0])
        self.assertLess(entity_insert_lines[0], install_lines[0])


if __name__ == "__main__":
    unittest.main()
