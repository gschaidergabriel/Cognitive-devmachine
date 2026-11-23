import pathlib
import sys
import unittest

COORD = pathlib.Path(__file__).resolve().parents[1] / "research_entity" / "coordination"
sys.path.insert(0, str(COORD))

import chatgpt_live_voice_expression as expression  # noqa: E402
import chatgpt_live_voice_state_adapter as adapter  # noqa: E402


class VoiceStateAdapterTests(unittest.TestCase):
    def test_typed_grid_intent_has_priority(self):
        declared = {
            "schema": expression.SCHEMA,
            "emotion": "angry",
            "intensity": 0.86,
            "confidence": 0.9,
            "reason": "canonical affect state",
            "delivery": {
                "energy": "high",
                "volume_intent": "raised",
                "clipped_phrasing": 0.8,
            },
        }
        derived = adapter.derive_expression_intent(
            "Sag mir das Ergebnis.",
            {
                "turn_event_id": "turn-grid",
                "cell_states": {"gwt": {"voice_expression_intent": declared}},
            },
        )
        self.assertEqual(derived["emotion"], "angry")
        self.assertEqual(derived["delivery"]["volume_intent"], "raised")

    def test_explicit_whisper_becomes_native_whisper_guidance(self):
        derived = adapter.derive_expression_intent(
            "Flüster das bitte ganz leise.", {"turn_event_id": "turn-whisper"}
        )
        normalized, prompt = expression.compile_from_payload(
            derived, user_text="Flüster das bitte ganz leise."
        )
        self.assertEqual(normalized["emotion"], "tender")
        self.assertEqual(normalized["delivery"]["volume_intent"], "quiet")
        self.assertGreaterEqual(normalized["delivery"]["whisper_intent"], 0.9)
        self.assertIn("whisper-like", prompt)

    def test_explicit_shout_uses_shout_like_not_db_contract(self):
        derived = adapter.derive_expression_intent(
            "Schrei das jetzt einmal richtig!", {"turn_event_id": "turn-shout"}
        )
        _, prompt = expression.compile_from_payload(derived)
        self.assertEqual(derived["emotion"], "urgent")
        self.assertEqual(derived["delivery"]["volume_intent"], "shout_like")
        self.assertIn("shout-like", prompt)
        self.assertNotIn("dB", prompt)

    def test_explicit_laughter_uses_native_laugh_intent(self):
        derived = adapter.derive_expression_intent(
            "Lach ruhig kurz darüber.", {"turn_event_id": "turn-laugh"}
        )
        _, prompt = expression.compile_from_payload(derived)
        self.assertEqual(derived["emotion"], "amused")
        self.assertGreaterEqual(derived["delivery"]["laugh_intent"], 0.9)
        self.assertIn("natural chuckle or laugh", prompt)

    def test_user_profanity_is_not_mechanically_mirrored_into_anger(self):
        derived = adapter.derive_expression_intent(
            "Oida das ist ein scheiß Bug, reparier den endlich.",
            {"turn_event_id": "turn-no-mirror"},
        )
        self.assertEqual(derived["emotion"], "neutral")
        self.assertEqual(derived["delivery"]["volume_intent"], "normal")

    def test_affect_labelled_state_can_drive_full_range(self):
        derived = adapter.derive_expression_intent(
            "Was jetzt?",
            {
                "turn_event_id": "turn-state-anger",
                "cell_states": {"affect": {"anger": 0.94}},
            },
        )
        self.assertEqual(derived["emotion"], "angry")
        self.assertEqual(derived["delivery"]["volume_intent"], "shout_like")
        self.assertGreaterEqual(derived["intensity"], 0.9)

    def test_stop_request_immediately_neutralizes(self):
        derived = adapter.derive_expression_intent(
            "Nein, hör auf damit und sprich normal.",
            {
                "turn_event_id": "turn-stop",
                "cell_states": {"affect": {"anger": 0.99}},
            },
        )
        self.assertEqual(derived["emotion"], "neutral")
        self.assertEqual(derived["intensity"], 0.0)
        self.assertEqual(derived["delivery"]["volume_intent"], "normal")

    def test_mockery_requires_permission_when_state_driven(self):
        derived = adapter.derive_expression_intent(
            "Weiter.",
            {
                "turn_event_id": "turn-mockery",
                "cell_states": {"affect": {"teasing": 0.88}},
            },
        )
        self.assertNotEqual(derived["emotion"], "teasing")

        allowed = adapter.derive_expression_intent(
            "Weiter.",
            {
                "turn_event_id": "turn-mockery-allowed",
                "allow_playful_mockery": True,
                "cell_states": {"affect": {"teasing": 0.88}},
            },
        )
        self.assertEqual(allowed["emotion"], "teasing")


if __name__ == "__main__":
    unittest.main()
