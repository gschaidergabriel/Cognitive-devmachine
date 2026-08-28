from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ATOMIC_RECEIPT_PATHS = (
    REPO_ROOT / "tools" / "frankenstein2_effect_dispatch_boundary_v1.py",
    REPO_ROOT / "tests" / "test_frankenstein2_effect_lifecycle_completion_v2.py",
)
FORBIDDEN_SPLIT_CALLS = (
    ".record_execution(",
    ".record_execution_v2_metadata(",
)
REQUIRED_ATOMIC_CALL = ".record_execution_bundle("


class Frankenstein2AtomicReceiptPathGuardTests(unittest.TestCase):
    """Keep canonical post-submission paths on the lifecycle-owned atomic writer.

    The legacy store methods may remain temporarily for forensic/recovery compatibility,
    but the real dispatch boundary and the Completion-v2 integration path must not regress
    to the old two-commit execution-receipt sequence.
    """

    def test_canonical_paths_use_atomic_bundle_and_not_split_writers(self) -> None:
        for path in CANONICAL_ATOMIC_RECEIPT_PATHS:
            with self.subTest(path=str(path.relative_to(REPO_ROOT))):
                text = path.read_text(encoding="utf-8")
                self.assertIn(
                    REQUIRED_ATOMIC_CALL,
                    text,
                    f"atomic execution bundle missing from {path.relative_to(REPO_ROOT)}",
                )
                for forbidden in FORBIDDEN_SPLIT_CALLS:
                    self.assertNotIn(
                        forbidden,
                        text,
                        f"split execution receipt writer reintroduced in {path.relative_to(REPO_ROOT)}: {forbidden}",
                    )


if __name__ == "__main__":
    unittest.main()
