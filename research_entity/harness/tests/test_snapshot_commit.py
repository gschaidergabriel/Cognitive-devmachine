import unittest

from research_entity.harness.reference.snapshot_commit import (
    CommitBarrierError,
    EffectIntent,
    capture_cognitive_snapshot,
    revalidate_for_fresh_commit,
)


def intent(*deps):
    return EffectIntent(
        intent_id="i1",
        effect_kind="fs.write",
        payload_sha256="payload",
        relevant_dependencies=tuple(deps),
        required_capability_kind="fs.write",
    )


class CommitBarrierTests(unittest.TestCase):
    def snap(self):
        return capture_cognitive_snapshot(
            snapshot_epoch=7,
            assembly_sha256="assembly",
            dependency_versions={"target": 3, "policy": 9, "unrelated": 1},
            capability_epoch=4,
        )

    def test_unrelated_change_does_not_force_abort(self):
        out = revalidate_for_fresh_commit(
            self.snap(),
            intent("target", "policy"),
            commit_epoch=8,
            current_dependency_versions={"target": 3, "policy": 9, "unrelated": 99},
            current_capability_epoch=4,
        )
        self.assertEqual(out.status, "PRECONDITIONS_VALID")
        self.assertTrue(out.effect_eligible_for_runtime_gateway)
        self.assertEqual(out.authority, "NONE")

    def test_relevant_change_forces_revalidation_conflict(self):
        out = revalidate_for_fresh_commit(
            self.snap(),
            intent("target", "policy"),
            commit_epoch=8,
            current_dependency_versions={"target": 4, "policy": 9, "unrelated": 1},
            current_capability_epoch=4,
        )
        self.assertEqual(out.status, "REVALIDATION_CONFLICT_DEPENDENCY")
        self.assertEqual(out.changed_relevant_dependencies, ("target",))
        self.assertFalse(out.effect_eligible_for_runtime_gateway)

    def test_capability_epoch_change_forces_conflict(self):
        out = revalidate_for_fresh_commit(
            self.snap(),
            intent("target"),
            commit_epoch=8,
            current_dependency_versions={"target": 3},
            current_capability_epoch=5,
        )
        self.assertEqual(out.status, "REVALIDATION_CONFLICT_CAPABILITY_EPOCH")

    def test_dependency_laundering_requires_reassembly(self):
        out = revalidate_for_fresh_commit(
            self.snap(),
            intent("target", "not_seen"),
            commit_epoch=8,
            current_dependency_versions={"target": 3, "not_seen": 1},
            current_capability_epoch=4,
        )
        self.assertEqual(out.status, "REASSEMBLE_REQUIRED_MISSING_DEPENDENCY")
        self.assertEqual(out.missing_snapshot_dependencies, ("not_seen",))

    def test_deterministic_guard_hash(self):
        a = revalidate_for_fresh_commit(
            self.snap(),
            intent("policy", "target"),
            commit_epoch=8,
            current_dependency_versions={"policy": 9, "target": 3},
            current_capability_epoch=4,
        )
        b = revalidate_for_fresh_commit(
            self.snap(),
            intent("target", "policy"),
            commit_epoch=8,
            current_dependency_versions={"target": 3, "policy": 9},
            current_capability_epoch=4,
        )
        self.assertEqual(a.guard_sha256, b.guard_sha256)

    def test_commit_cannot_precede_snapshot(self):
        with self.assertRaisesRegex(CommitBarrierError, "COMMIT_EPOCH_PRECEDES_SNAPSHOT"):
            revalidate_for_fresh_commit(
                self.snap(),
                intent("target"),
                commit_epoch=6,
                current_dependency_versions={"target": 3},
                current_capability_epoch=4,
            )


if __name__ == "__main__":
    unittest.main()
