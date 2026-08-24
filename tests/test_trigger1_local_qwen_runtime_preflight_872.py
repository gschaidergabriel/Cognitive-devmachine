from pathlib import Path
import json
import re
import subprocess
import tempfile
import unittest


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/trigger1-local-qwen06-runtime-proof.yml"


class Trigger1LocalQwenRuntimePreflight872(unittest.TestCase):
    def test_low_disk_receipt_binds_observed_available_kb(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        match = re.search(
            r"printf '\{\"status\":\"BLOCKED_INSUFFICIENT_FREE_DISK\",\"available_kb\":%s\}\\n' "
            r'"\$avail_kb" > "\$OUT/preflight\.json"',
            text,
        )
        self.assertIsNotNone(match, "blocked disk preflight must pass avail_kb to printf")

    def test_low_disk_receipt_shape_is_valid_json(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            command = (
                'avail_kb=1234; OUT="$1"; '
                'printf \'{"status":"BLOCKED_INSUFFICIENT_FREE_DISK","available_kb":%s}\\n\' '
                '"$avail_kb" > "$OUT/preflight.json"'
            )
            subprocess.run(["bash", "-c", command, "bash", str(out)], check=True)
            obj = json.loads((out / "preflight.json").read_text(encoding="utf-8"))
            self.assertEqual(obj, {"status": "BLOCKED_INSUFFICIENT_FREE_DISK", "available_kb": 1234})

    def test_always_publisher_preserves_preflight_and_source_identity(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("const preflightPath = `${out}/preflight.json`;", text)
        self.assertIn("preflight = JSON.parse(fs.readFileSync(preflightPath, 'utf8'));", text)
        self.assertIn("BLOCKED_PREFLIGHT_RESULT_UNPARSEABLE", text)
        self.assertIn("const sourceHeadPath = `${out}/source-head.txt`;", text)
        self.assertIn("const sourceTreePath = `${out}/source-tree.txt`;", text)
        self.assertIn("source_head:fs.existsSync(sourceHeadPath)", text)
        self.assertIn("source_tree:fs.existsSync(sourceTreePath)", text)
        self.assertIn("runtime_status:preflight?.status || 'WORKFLOW_RESULT_MISSING'", text)


if __name__ == "__main__":
    unittest.main()
