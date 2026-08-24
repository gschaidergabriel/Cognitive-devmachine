from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_attested_local_qwen_api as envelope


class Trigger1GuardPlatformCompatibilityTests(unittest.TestCase):
    def test_guard_allows_platform_uname_introspection(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            audit = td / "audit.jsonl"
            guard = td / "guard.py"
            guard.write_text(envelope.guard_code(), encoding="utf-8")
            env, _ = envelope.guarded_env(audit)
            code = 'import json, platform; print(json.dumps({"platform": platform.platform()}))'
            boot = "import pathlib,sys;exec(pathlib.Path(sys.argv[1]).read_text(),{});exec(sys.argv[2],{})"
            proc = subprocess.run(
                [sys.executable, "-I", "-c", boot, str(guard), code],
                env=env,
                text=True,
                capture_output=True,
                timeout=20,
            )
            self.assertEqual(0, proc.returncode, proc.stderr)
            self.assertTrue(json.loads(proc.stdout)["platform"])
            events = [row["event"] for row in envelope.audit_rows(audit)]
            self.assertNotIn("blocked_child_subprocess", events)


if __name__ == "__main__":
    unittest.main()
