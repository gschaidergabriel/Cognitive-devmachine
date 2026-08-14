import dataclasses
import unittest

from needle_boundary import (
    AUTHORITY_NONE,
    NeedleBoundaryError,
    NeedleReceipt,
    TranslatorReceipt,
    bridge_to_clay,
    sha256_text,
    verify_envelope,
)


def fixtures():
    raw = "Öffne den Kalender und prüfe morgen."
    normalized = "open calendar and inspect tomorrow"
    tr = TranslatorReceipt(
        translator_id="translator:test",
        translator_version="1.0",
        source_language="de",
        source_text_sha256=sha256_text(raw),
        normalized_text_sha256=sha256_text(normalized),
    )
    nr = NeedleReceipt(
        needle_id="needle:test",
        needle_version="legacy-frozen-test",
        input_sha256=sha256_text(normalized),
        route="CALENDAR_QUERY",
        certificate_id="needle-cert:test-001",
        certificate_sha256=sha256_text("route=CALENDAR_QUERY;policy=frozen"),
        semantic_language="CLAY",
        proposal_class="ROUTE_PROPOSAL",
        payload_clay="clay{route:#calendar_query; temporal:#tomorrow}",
    )
    return tr, nr


class NeedleBoundaryTests(unittest.TestCase):
    def test_deterministic_bridge_hash(self):
        tr, nr = fixtures()
        a = bridge_to_clay(tr, nr)
        b = bridge_to_clay(tr, nr)
        self.assertEqual(a.bridge_hash, b.bridge_hash)
        self.assertTrue(verify_envelope(a))

    def test_preserves_provenance_and_route(self):
        tr, nr = fixtures()
        env = bridge_to_clay(tr, nr)
        self.assertEqual(env.translator["translator_version"], "1.0")
        self.assertEqual(env.needle["needle_version"], "legacy-frozen-test")
        self.assertEqual(env.needle["route"], "CALENDAR_QUERY")
        self.assertEqual(env.needle["certificate_id"], "needle-cert:test-001")

    def test_no_execution_authority(self):
        tr, nr = fixtures()
        env = bridge_to_clay(tr, nr)
        self.assertEqual(env.authority, AUTHORITY_NONE)
        self.assertFalse(env.effect_eligible)
        self.assertTrue(env.effect_gate_required)

    def test_rejects_needles_authority_claim(self):
        tr, nr = fixtures()
        nr = dataclasses.replace(nr, authority_claim="EXECUTE")
        with self.assertRaises(NeedleBoundaryError):
            bridge_to_clay(tr, nr)

    def test_rejects_hash_chain_break(self):
        tr, nr = fixtures()
        nr = dataclasses.replace(nr, input_sha256=sha256_text("tampered"))
        with self.assertRaises(NeedleBoundaryError):
            bridge_to_clay(tr, nr)

    def test_rejects_missing_certificate(self):
        tr, nr = fixtures()
        nr = dataclasses.replace(nr, certificate_id="")
        with self.assertRaises(NeedleBoundaryError):
            bridge_to_clay(tr, nr)

    def test_rejects_non_clay_cognitive_output(self):
        tr, nr = fixtures()
        nr = dataclasses.replace(nr, semantic_language="JSON")
        with self.assertRaises(NeedleBoundaryError):
            bridge_to_clay(tr, nr)

    def test_rejects_normal_ingress_bypass(self):
        tr, nr = fixtures()
        nr = dataclasses.replace(nr, route="BYPASS_NEEDLE")
        with self.assertRaises(NeedleBoundaryError):
            bridge_to_clay(tr, nr)

    def test_payload_tamper_breaks_envelope_verification(self):
        tr, nr = fixtures()
        env = bridge_to_clay(tr, nr)
        env = dataclasses.replace(env, payload_clay="clay{route:#different}")
        self.assertFalse(verify_envelope(env))


if __name__ == "__main__":
    unittest.main()
