from research_entity.coordination.trigger999_intervention_gate import (
    ConversationFloorState,
    InterventionCandidate,
    SpeechAct,
    choose_intervention,
)


def candidate(cid: str, act: SpeechAct = SpeechAct.PROPOSE, **kw):
    return InterventionCandidate(
        candidate_id=cid,
        speech_act=act,
        semantic_intent=kw.pop("semantic_intent", cid),
        reason=kw.pop("reason", "test"),
        **kw,
    )


def test_relevant_unaddressed_correction_can_enter_during_pause():
    state = ConversationFloorState(
        now_ms=10_000,
        speech_active=False,
        silence_duration_ms=700,
        likely_addressee="UNKNOWN",
    )
    c = candidate(
        "correction",
        act=SpeechAct.OBJECT,
        expected_task_value=1.0,
        novelty=0.9,
        repair_need=0.9,
        urgency=0.4,
        intrusion_risk=0.1,
    )
    decision = choose_intervention(state, [c])
    assert decision.speak
    assert decision.speech_act == SpeechAct.OBJECT


def test_private_active_human_exchange_normally_waits():
    state = ConversationFloorState(
        now_ms=10_000,
        current_floor_owner="HUMAN_A",
        speech_active=True,
        likely_addressee="HUMAN_B",
        addressee_confidence=0.95,
    )
    c = candidate(
        "optional_fact",
        expected_task_value=0.4,
        expected_social_value=0.2,
        novelty=0.4,
        intrusion_risk=0.9,
        overlap_cost=0.8,
    )
    decision = choose_intervention(state, [c])
    assert not decision.speak
    assert decision.speech_act == SpeechAct.WAIT


def test_explicit_invitation_lowers_practical_barrier():
    state = ConversationFloorState(
        now_ms=10_000,
        speech_active=False,
        likely_addressee="FRANKENSTEIN",
        addressee_confidence=0.95,
    )
    c = candidate(
        "invited",
        act=SpeechAct.ANSWER,
        expected_task_value=0.8,
        expected_social_value=0.4,
        invitation_strength=1.0,
        novelty=0.5,
    )
    decision = choose_intervention(state, [c])
    assert decision.speak
    assert decision.speech_act == SpeechAct.ANSWER


def test_human_barge_in_causes_yield():
    state = ConversationFloorState(
        now_ms=10_000,
        frankenstein_speaking=True,
        current_floor_owner="HUMAN_A",
        speech_active=True,
    )
    c = candidate(
        "continue",
        act=SpeechAct.ANSWER,
        expected_task_value=1.0,
        novelty=1.0,
        urgency=0.2,
    )
    decision = choose_intervention(state, [c])
    assert not decision.speak
    assert decision.yield_to_human
    assert decision.reason == "human_barge_in_yield"


def test_high_urgency_correction_can_override_active_floor():
    state = ConversationFloorState(
        now_ms=10_000,
        current_floor_owner="HUMAN_A",
        speech_active=True,
        likely_addressee="HUMAN_B",
        addressee_confidence=0.9,
    )
    c = candidate(
        "critical",
        act=SpeechAct.OBJECT,
        expected_task_value=1.0,
        expected_social_value=0.7,
        urgency=1.0,
        novelty=1.0,
        repair_need=1.0,
        intrusion_risk=0.1,
        overlap_cost=0.1,
    )
    decision = choose_intervention(state, [c])
    assert decision.speak
    assert decision.speech_act == SpeechAct.OBJECT


def test_backchannel_spam_is_suppressed():
    state = ConversationFloorState(
        now_ms=10_000,
        speech_active=False,
        recent_backchannel_count=3,
        likely_addressee="FRANKENSTEIN",
        addressee_confidence=0.9,
    )
    c = candidate(
        "mhm_again",
        act=SpeechAct.BACKCHANNEL,
        expected_social_value=0.6,
        invitation_strength=0.3,
        novelty=0.2,
    )
    decision = choose_intervention(state, [c])
    assert not decision.speak


def test_cooldown_suppresses_chatter_after_unsolicited_entry():
    state = ConversationFloorState(
        now_ms=10_000,
        last_frankenstein_end_ms=9_500,
        speech_active=False,
        likely_addressee="UNKNOWN",
    )
    c = candidate(
        "another_point",
        expected_task_value=0.7,
        expected_social_value=0.5,
        novelty=0.7,
        intrusion_risk=0.1,
    )
    decision = choose_intervention(state, [c])
    assert not decision.speak


def test_expired_candidate_is_not_spoken():
    state = ConversationFloorState(now_ms=10_000)
    c = candidate(
        "stale",
        expected_task_value=1.0,
        expected_social_value=1.0,
        novelty=1.0,
        expires_at_ms=9_999,
    )
    decision = choose_intervention(state, [c])
    assert not decision.speak
    assert decision.reason == "no_live_candidate"


def test_unknown_addressee_is_penalized_but_not_absolute_veto():
    state = ConversationFloorState(now_ms=10_000, likely_addressee="UNKNOWN")
    strong = candidate(
        "strong",
        act=SpeechAct.CLARIFY,
        expected_task_value=1.0,
        expected_social_value=0.8,
        novelty=0.8,
        repair_need=0.8,
    )
    weak = candidate(
        "weak",
        expected_task_value=0.3,
        expected_social_value=0.2,
        novelty=0.2,
    )
    assert choose_intervention(state, [strong]).speak
    assert not choose_intervention(state, [weak]).speak


def test_wait_is_explicit_when_no_candidate_deserves_floor():
    state = ConversationFloorState(now_ms=10_000)
    decision = choose_intervention(state, [])
    assert decision.speech_act == SpeechAct.WAIT
    assert not decision.speak
