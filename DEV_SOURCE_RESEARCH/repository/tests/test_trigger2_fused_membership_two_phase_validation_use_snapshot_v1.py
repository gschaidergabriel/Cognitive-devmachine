from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from copy import deepcopy
from typing import Any

import tools.trigger2_fused_membership_two_phase_adapter_v1 as adapter


class DriftingSequence(Sequence[Mapping[str, Any]]):
    """Return a valid-looking cohort once and different bytes on a second traversal."""

    def __init__(self, first: list[dict[str, Any]], second: list[dict[str, Any]]) -> None:
        self.first = first
        self.second = second
        self.iterations = 0

    def __len__(self) -> int:
        return len(self.first)

    def __getitem__(self, index: int) -> Mapping[str, Any]:
        return self.first[index]

    def __iter__(self) -> Iterator[Mapping[str, Any]]:
        self.iterations += 1
        selected = self.first if self.iterations == 1 else self.second
        return iter(selected)


class RecordingFabric:
    def __init__(self) -> None:
        self.validated_object: object | None = None
        self.validated_bytes: list[dict[str, Any]] | None = None
        self.received: list[Mapping[str, Any]] | None = None

    def atomic_fused_cohort_commit(
        self,
        *,
        envelopes: list[Mapping[str, Any]],
        **_kwargs: Any,
    ) -> dict[str, Any]:
        assert envelopes is self.validated_object
        assert envelopes == self.validated_bytes
        self.received = envelopes
        return {"pass": True, "replay": False, "state_delta": 1}


def test_atomic_commit_validates_and_delegates_one_controller_owned_snapshot(monkeypatch) -> None:
    good = [
        {"member": i, "payload": {"marker": "validated", "ordinal": i}}
        for i in range(adapter.N)
    ]
    tampered = deepcopy(good)
    tampered[0]["payload"]["marker"] = "second-iteration-tamper"
    source = DriftingSequence(good, tampered)
    fabric = RecordingFabric()

    def fake_validate(
        envelopes: Sequence[Mapping[str, Any]],
        *,
        expected_member_count: int,
    ) -> dict[str, Any]:
        assert expected_member_count == adapter.N
        assert isinstance(envelopes, list)
        assert len(envelopes) == adapter.N
        fabric.validated_object = envelopes
        fabric.validated_bytes = deepcopy(envelopes)
        return {"pass": True, "member_count": adapter.N}

    monkeypatch.setattr(adapter, "validate_two_phase_cohort", fake_validate)

    result = adapter.atomic_fused_two_phase_commit(
        fabric,
        envelopes=source,
        synthetic_source_fixture_only=True,
    )

    assert source.iterations == 1
    assert fabric.received is fabric.validated_object
    assert fabric.received == good
    assert fabric.received[0]["payload"]["marker"] == "validated"
    assert result["two_phase_validation"] == {"pass": True, "member_count": adapter.N}
    assert result["fused_coordinator_receipt"]["state_delta"] == 1
    assert result["adapter_created_second_coordinator_cohort_id"] is False
    assert result["canonical_truth"] is False
    assert result["effect_authority"] is False
