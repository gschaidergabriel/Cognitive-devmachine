from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_candidate_provenance_bind as bind

H40 = "b" * 40
T40 = "c" * 40
A64 = "a" * 64
D64 = "d" * 64
E64 = "e" * 64
F64 = "f" * 64


def result() -> dict:
    return {
        "schema": bind.RESULT_SCHEMA,
        "status": "PASS",
        "source": {
            "repo_head": H40,
            "repo_tree": T40,
            "repo_dirty_porcelain_sha256": D64,
            "executor_sha256": E64,
        },
        "runtime_build_sha256": A64,
        "checkpoint_sha256": F64,
        "tokenizer_sha256": D64,
    }


def candidate() -> dict:
    return {
        "schema": bind.CANDIDATE_SCHEMA,
        "source_identity": {
            "repo_head": H40,
            "runtime_build_sha256": A64,
            "checkpoint_sha256": F64,
            "tokenizer_sha256": D64,
        },
    }


class CandidateProvenanceBindTests(unittest.TestCase):
    def test_binds_executor_dirty_tree_and_binder_identity(self):
        out = bind.bind_candidate(result(), candidate(), binder_sha256=A64)
        identity = out["source_identity"]
        self.assertEqual(T40, identity["repo_tree"])
        self.assertEqual(D64, identity["repo_dirty_porcelain_sha256"])
        self.assertEqual(E64, identity["executor_sha256"])
        self.assertEqual(A64, identity["provenance_binder_sha256"])
        self.assertEqual(64, len(identity["provenance_binding_sha256"]))

    def test_repo_head_mismatch_fails_closed(self):
        bad = candidate()
        bad["source_identity"]["repo_head"] = "1" * 40
        with self.assertRaisesRegex(ValueError, "CANDIDATE_RESULT_IDENTITY_MISMATCH:repo_head"):
            bind.bind_candidate(result(), bad, binder_sha256=A64)

    def test_missing_dirty_identity_fails_closed(self):
        bad_result = result()
        del bad_result["source"]["repo_dirty_porcelain_sha256"]
        with self.assertRaisesRegex(ValueError, "INVALID_OR_MISSING_IDENTITY:repo_dirty_porcelain_sha256"):
            bind.bind_candidate(bad_result, candidate(), binder_sha256=A64)

    def test_nonpass_result_cannot_bind_candidate(self):
        bad_result = result()
        bad_result["status"] = "SCIENTIFIC_NEGATIVE"
        with self.assertRaisesRegex(ValueError, "RESULT_PASS_REQUIRED"):
            bind.bind_candidate(bad_result, candidate(), binder_sha256=A64)


if __name__ == "__main__":
    unittest.main()
