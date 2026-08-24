#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools/run_24h_entityos_swarm_supervisor.sh"
SWARM_ENTRY = ROOT / "tools/run_24h_entityos_swarm_entry.py"
DISTILLERY_ENTRY = ROOT / "tools/run_research_distillery_entry.py"


def import_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Go867PreIOClosure(unittest.TestCase):
    def test_supervisor_has_no_pre_admission_secret_or_publish_path(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        for forbidden in (
            "load_all_secret_sources", "source \"$f\"", "done < <(env)",
            "/run/secrets/clay_provider.env", "research_entity/private/API_TOKENS.env",
            "--publish", "run_24h_entityos_swarm.py\" --hours",
        ):
            self.assertNotIn(forbidden, text)
        for required in (
            "provider_is_admitted", "free_provider_admission.py", "compgen -v",
            "load_admitted_provider_secrets", "run_24h_entityos_swarm_entry.py",
        ):
            self.assertIn(required, text)
        proc = subprocess.run(["bash", "-n", str(SUPERVISOR)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_swarm_entry_rechecks_before_chat_and_catalog_io(self):
        gate = {"allow": False}
        calls = {"chat": 0, "catalog": 0}
        base = types.ModuleType("run_free_go_swarm")
        base.provider_is_admitted_free = lambda provider: gate["allow"]
        def old_chat(*args, **kwargs):
            calls["chat"] += 1
            return 200, {}, {"ok": True}
        base.request_chat = old_chat
        driver = types.ModuleType("run_24h_entityos_swarm")
        driver.fetch_catalog = lambda *a, **k: calls.__setitem__("catalog", calls["catalog"] + 1) or [{"id": "x"}]
        driver.main = lambda args: 0
        driver.parse_args = lambda: object()
        old_base = sys.modules.get("run_free_go_swarm")
        old_driver = sys.modules.get("run_24h_entityos_swarm")
        sys.modules["run_free_go_swarm"] = base
        sys.modules["run_24h_entityos_swarm"] = driver
        try:
            mod = import_path("_test_swarm_entry", SWARM_ENTRY)
            spec = types.SimpleNamespace(name="groq")
            status, _, payload = mod.admission_rechecking_chat(spec, "k", "m", "p", 1, 1)
            self.assertEqual(status, 403)
            self.assertEqual(payload["classification"], "PROVIDER_ADMISSION_REVOKED_FAIL_CLOSED")
            self.assertEqual(mod.admission_rechecking_catalog("groq", "u", "k", 1), [])
            self.assertEqual(calls, {"chat": 0, "catalog": 0})
            gate["allow"] = True
            self.assertEqual(mod.admission_rechecking_chat(spec, "k", "m", "p", 1, 1)[0], 200)
            self.assertEqual(mod.admission_rechecking_catalog("groq", "u", "k", 1), [{"id": "x"}])
            self.assertEqual(calls, {"chat": 1, "catalog": 1})
        finally:
            if old_base is None: sys.modules.pop("run_free_go_swarm", None)
            else: sys.modules["run_free_go_swarm"] = old_base
            if old_driver is None: sys.modules.pop("run_24h_entityos_swarm", None)
            else: sys.modules["run_24h_entityos_swarm"] = old_driver

    def test_distillery_blocks_unadmitted_secret_and_provider_io(self):
        gate = {"groq": False, "mistral": False, "nvidia": False}
        calls = {"secret": 0, "network": 0}
        d = types.ModuleType("run_research_distillery")
        def raw_secret(name):
            calls["secret"] += 1
            return "secret"
        def raw_request(provider, owner, url, **kwargs):
            calls["network"] += 1
            return 200, {}, {"ok": True}
        d.secret = raw_secret
        d.request_json = raw_request
        d.jaccard = lambda a, b: 0.0
        d.now_iso = lambda: "now"
        d.main = lambda: 0
        admission = types.ModuleType("free_provider_admission")
        admission.provider_is_admitted_free = lambda provider: bool(gate.get(provider, False))
        old_d = sys.modules.get("run_research_distillery")
        old_a = sys.modules.get("free_provider_admission")
        sys.modules["run_research_distillery"] = d
        sys.modules["free_provider_admission"] = admission
        try:
            mod = import_path("_test_distillery_entry", DISTILLERY_ENTRY)
            for name in ("GROQ_API_KEY", "OPENROUTER_API_KEY", "TAVILY_API_KEY", "EXA_API_KEY"):
                self.assertEqual(mod.admitted_secret(name), "")
            for provider in ("groq", "openrouter", "tavily", "exa"):
                self.assertEqual(mod.admitted_request_json(provider, "o", "u")[0], 0)
            self.assertEqual(calls, {"secret": 0, "network": 0})
            gate["groq"] = True
            self.assertEqual(mod.admitted_secret("GROQ_API_KEY"), "secret")
            self.assertEqual(mod.admitted_request_json("groq", "o", "u")[0], 200)
            self.assertEqual(mod.admitted_request_json("github", "o", "u")[0], 200)
            self.assertEqual(calls, {"secret": 1, "network": 2})
        finally:
            if old_d is None: sys.modules.pop("run_research_distillery", None)
            else: sys.modules["run_research_distillery"] = old_d
            if old_a is None: sys.modules.pop("free_provider_admission", None)
            else: sys.modules["free_provider_admission"] = old_a


if __name__ == "__main__":
    unittest.main()
