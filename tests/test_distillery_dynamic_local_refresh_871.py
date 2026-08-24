from __future__ import annotations

from unittest import mock

import tools.run_research_distillery_local as local


def test_late_health_recovery_populates_empty_startup_snapshot():
    with mock.patch.object(local,"local_health",return_value=True):
        small,reviewers=local.refresh_local_lanes([],[])
    assert small[0]==local.LOCAL_LOGICAL_ID
    assert reviewers==list(local.LOCAL_REVIEWERS)


def test_existing_external_review_panel_is_never_replaced_by_local_panel():
    external=[("nvidia_reviewer","nvidia","nvidia/model"),("mistral_reviewer_1","mistral","mistral/model")]
    with mock.patch.object(local,"local_health",return_value=True):
        small,reviewers=local.refresh_local_lanes(["openrouter/free-model"],external)
    assert local.LOCAL_LOGICAL_ID in small
    assert reviewers==external
    assert not any(r[1]=="local" for r in reviewers)


def test_health_loss_removes_stale_local_lanes_but_preserves_external_lanes():
    reviewers=[local.LOCAL_REVIEWERS[0],("nvidia_reviewer","nvidia","nvidia/model")]
    with mock.patch.object(local,"local_health",return_value=False):
        small,live_reviewers=local.refresh_local_lanes([local.LOCAL_LOGICAL_ID,"openrouter/free-model"],reviewers)
    assert small==["openrouter/free-model"]
    assert live_reviewers==[("nvidia_reviewer","nvidia","nvidia/model")]


def test_each_cycle_rechecks_health_instead_of_using_frozen_empty_lists():
    con=mock.MagicMock()
    with mock.patch.object(local,"local_health",return_value=True), \
         mock.patch.object(local,"_PREV_ONE_CYCLE",return_value=False) as previous:
        result=local.dynamic_one_cycle(con,[],[])
    assert result is False
    args=previous.call_args.args
    assert args[0] is con
    assert args[1][0]==local.LOCAL_LOGICAL_ID
    assert args[2]==list(local.LOCAL_REVIEWERS)


def test_status_projection_rechecks_health_without_mutating_frozen_startup_lists():
    con=mock.MagicMock(); frozen_small=[]; frozen_reviewers=[]
    with mock.patch.object(local,"local_health",return_value=True), \
         mock.patch.object(local,"_PREV_WRITE_STATUS") as previous:
        local.dynamic_write_status(con,frozen_reviewers,frozen_small)
    previous.assert_called_once_with(con,list(local.LOCAL_REVIEWERS),[local.LOCAL_LOGICAL_ID])
    assert frozen_small==[]
    assert frozen_reviewers==[]
