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


if __name__ == "__main__":
    unittest.main()
