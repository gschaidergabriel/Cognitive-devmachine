from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_provider_admission as admission_mod
import run_free_go_swarm as base


SECRET_ENV_NAMES = {
    "GROQ_API_KEY",
    "MISTRAL_API_KEY",
    "NVIDIA_API_KEY",
    "NGC_API_KEY",
    "OPENROUTER_API_KEY",
}
CANONICAL_ADMISSION_REL = Path("research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json")


def _authority(root: Path) -> Path:
    rel = Path("research_entity/claycode/autonomous/SUPERVISOR_STEERING_TEST.json")
    steering = root / rel
    steering.parent.mkdir(parents=True, exist_ok=True)
    steering.write_text(
        json.dumps(
            {
                "schema_version": "8.68",
                "active_program": "ENTITYOS_HCU",
                "product": "EntityOS",
                "integrated_cognition_compute_architecture": "HCU",
            }
        ),
        encoding="utf-8",
    )
    inbox = root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox.write_text(
        json.dumps({"schema_version": "8.68", "steering": rel.as_posix()}),
        encoding="utf-8",
    )
    return inbox


def _args(output_dir: str) -> argparse.Namespace:
    return argparse.Namespace(
        hours=0.001,
        max_tokens=8,
        context_chars=128,
        timeout=0.1,
        drain_seconds=0.1,
        output_dir=output_dir,
    )


class MalformedAdmissionBoundaryRegression(unittest.TestCase):
    def test_malformed_admission_has_zero_secret_lookup_and_zero_network(self) -> None:
        secret_reads = 0
        network_attempts = 0
        original_getenv = os.getenv

        def guarded_getenv(name: str, default=None):
            nonlocal secret_reads
            if name in SECRET_ENV_NAMES or name.endswith("_API_KEY") or name.endswith("_API_KEYS"):
                secret_reads += 1
                raise AssertionError(f"secret lookup before admission: {name}")
            return original_getenv(name, default)

        def network_tripwire(*args, **kwargs):
            nonlocal network_attempts
            network_attempts += 1
            raise AssertionError("provider network reached before admission")

        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as out:
            root = Path(td)
            malformed = root / CANONICAL_ADMISSION_REL
            malformed.parent.mkdir(parents=True, exist_ok=True)
            malformed.write_text('{"schema":', encoding="utf-8")
            inbox = _authority(root)

            with mock.patch.object(admission_mod, "ROOT", root), \
                 mock.patch.object(admission_mod, "ADMISSION_PATH", malformed), \
                 mock.patch.object(admission_mod, "SUPERVISOR_INBOX_PATH", inbox), \
                 mock.patch.object(base, "load_protocol", return_value=base.PROTOCOL_BEGIN + "\n" + base.PROTOCOL_END), \
                 mock.patch.object(base.os, "getenv", side_effect=guarded_getenv), \
                 mock.patch.object(base.urllib.request, "urlopen", side_effect=network_tripwire), \
                 mock.patch.dict(os.environ, {"CLAY_FREE_ONLY_ATTESTED": "1"}, clear=True):
                code = asyncio.run(base.run(_args(out)))

        self.assertEqual(code, 5)
        self.assertEqual(secret_reads, 0)
        self.assertEqual(network_attempts, 0)


if __name__ == "__main__":
    unittest.main()
