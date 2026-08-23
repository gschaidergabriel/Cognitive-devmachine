import json
import shutil
import subprocess
import unittest

from typed_entry_canonical_v1 import (
    CANONICALIZATION_SCHEMA,
    CanonicalEncodingError,
    encode_canonical,
)
from xeno_entry_fabric_v1 import admit_entry, to_hcu_reactive_event
from reactive_event_router_v1 import route_event


CAPABILITY_BINDING_SHA256 = "b" * 64
ADMITTED_CAPABILITIES = ("memory.read", "hcu.route")
ADMITTED_BUDGET = {"max_model_calls": 2, "max_tokens": 2048, "max_wall_ms": 5000}


def base_entry():
    return {
        "schema": "XENO_ENTRY_PACKET/v1",
        "ingress_id": "ingress:test:1",
        "causal_id": "causal:test:1",
        "entity_generation": 7,
        "source_kind": "HUMAN_PROMPT",
        "source_id": "user:test",
        "modality": "TEXT",
        "observed_time": "2026-08-23T23:24:00+07:00",
        "received_time": "2026-08-23T23:24:01+07:00",
        "provenance_ref": "unifieddb:source:test:1",
        "provenance_sha256": "a" * 64,
        "capabilities": ["memory.read", "hcu.route"],
        "capability_binding_sha256": CAPABILITY_BINDING_SHA256,
        "parent_id": None,
        "stream_id": "stream:test",
        "budget": {"max_model_calls": 2, "max_tokens": 2048, "max_wall_ms": 5000},
        "payload_ref": "unifieddb:payload:test:1",
        "payload_sha256": "c" * 64,
    }


def admit(entry):
    return admit_entry(
        entry,
        current_generation=7,
        expected_capability_binding_sha256=CAPABILITY_BINDING_SHA256,
        admitted_capabilities=ADMITTED_CAPABILITIES,
        admitted_budget=ADMITTED_BUDGET,
    )


class TypedEntryCanonicalTests(unittest.TestCase):
    def test_rfc8949_subset_known_vectors(self):
        vectors = [
            (None, "f6"),
            (False, "f4"),
            (True, "f5"),
            (0, "00"),
            (23, "17"),
            (24, "1818"),
            (-1, "20"),
            ("a", "6161"),
            ([1, 2, 3], "83010203"),
            ({"a": 1, "b": 2}, "a2616101616202"),
        ]
        for value, expected in vectors:
            self.assertEqual(encode_canonical(value).hex(), expected)

    def test_map_order_is_deterministic_encoded_key_order(self):
        a = {"z": 1, "aa": 2, "a": 3}
        b = {"a": 3, "aa": 2, "z": 1}
        self.assertEqual(encode_canonical(a), encode_canonical(b))
        self.assertEqual(encode_canonical(a).hex(), "a3616103617a0162616102")

    def test_float_and_unsafe_integer_fail_closed(self):
        with self.assertRaisesRegex(CanonicalEncodingError, "FLOAT_FORBIDDEN"):
            encode_canonical(0.5)
        with self.assertRaisesRegex(CanonicalEncodingError, "IJSON_SAFE_RANGE"):
            encode_canonical(9_007_199_254_740_992)

    def test_transport_replay_preserves_causal_event_and_route_identity(self):
        first = admit(base_entry())
        replay = base_entry()
        replay["ingress_id"] = "ingress:test:2"
        replay["received_time"] = "2026-08-23T23:29:01+07:00"
        second = admit(replay)
        self.assertEqual(first.event_sha256, second.event_sha256)
        self.assertNotEqual(first.admission_sha256, second.admission_sha256)

        first_event = to_hcu_reactive_event(first, novelty=0.1)
        second_event = to_hcu_reactive_event(second, novelty=0.1)
        self.assertEqual(first_event["entry_event_sha256"], second_event["entry_event_sha256"])
        self.assertNotEqual(first_event["entry_admission_sha256"], second_event["entry_admission_sha256"])
        self.assertNotEqual(first_event["ingress_id"], second_event["ingress_id"])
        self.assertEqual(first_event["entry_canonicalization_schema"], CANONICALIZATION_SCHEMA)
        self.assertEqual(second_event["entry_canonicalization_schema"], CANONICALIZATION_SCHEMA)

        first_route = route_event(
            first_event,
            current_generation=7,
            admitted_entry_bindings={first.admission_sha256: first.event_sha256},
        )
        second_route = route_event(
            second_event,
            current_generation=7,
            admitted_entry_bindings={second.admission_sha256: second.event_sha256},
        )
        self.assertEqual(first_route.event_sha256, second_route.event_sha256)
        self.assertNotEqual(first_route.entry_admission_sha256, second_route.entry_admission_sha256)
        self.assertEqual(first_route.decision_sha256, second_route.decision_sha256)

    def test_equivalent_observed_timestamp_offsets_canonicalize_to_same_event(self):
        first = admit(base_entry())
        same_instant = base_entry()
        same_instant["observed_time"] = "2026-08-23T16:24:00Z"
        second = admit(same_instant)
        self.assertEqual(first.observed_time, "2026-08-23T16:24:00.000000Z")
        self.assertEqual(first.event_sha256, second.event_sha256)

    def test_payload_change_changes_causal_event_identity(self):
        first = admit(base_entry())
        changed = base_entry()
        changed["payload_sha256"] = "d" * 64
        second = admit(changed)
        self.assertNotEqual(first.event_sha256, second.event_sha256)

    @unittest.skipUnless(shutil.which("node"), "independent Node canonicalizer unavailable")
    def test_independent_node_encoder_matches_python_entry_shaped_corpus(self):
        values = [
            {
                "schema": CANONICALIZATION_SCHEMA,
                "causal_id": "κausal-✓",
                "entity_generation": 7,
                "source_kind": "HUMAN_PROMPT",
                "source_id": "user:test",
                "observed_time": "2026-08-23T16:24:00.000000Z",
                "provenance_sha256": "a" * 64,
                "budget": {"max_model_calls": 2, "max_tokens": 2048, "max_wall_ms": 5000},
                "parent_id": None,
                "payload_sha256": "c" * 64,
            },
            {"nested": [None, True, False, -24, -25, 23, 24, 255, 256, "é", "😀"]},
        ]
        js = r'''
const fs=require('fs'); const values=JSON.parse(fs.readFileSync(0,'utf8'));
function head(m,v){if(!Number.isSafeInteger(v)||v<0)throw Error('arg');const p=m<<5;if(v<24)return Buffer.from([p|v]);if(v<=255)return Buffer.from([p|24,v]);if(v<=65535){const b=Buffer.alloc(3);b[0]=p|25;b.writeUInt16BE(v,1);return b;}if(v<=4294967295){const b=Buffer.alloc(5);b[0]=p|26;b.writeUInt32BE(v,1);return b;}const b=Buffer.alloc(9);b[0]=p|27;b.writeBigUInt64BE(BigInt(v),1);return b;}
function enc(v){if(v===null)return Buffer.from([246]);if(v===false)return Buffer.from([244]);if(v===true)return Buffer.from([245]);if(typeof v==='number'){if(!Number.isSafeInteger(v))throw Error('unsafe');return v>=0?head(0,v):head(1,-1-v);}if(typeof v==='string'){const x=Buffer.from(v,'utf8');return Buffer.concat([head(3,x.length),x]);}if(Array.isArray(v))return Buffer.concat([head(4,v.length),...v.map(enc)]);if(typeof v==='object'){const xs=Object.keys(v).map(k=>[enc(k),enc(v[k])]);xs.sort((a,b)=>Buffer.compare(a[0],b[0]));return Buffer.concat([head(5,xs.length),...xs.flat()]);}throw Error('unsupported');}
process.stdout.write(JSON.stringify(values.map(v=>enc(v).toString('hex'))));
'''
        proc = subprocess.run(
            ["node", "-e", js],
            input=json.dumps(values, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(json.loads(proc.stdout), [encode_canonical(v).hex() for v in values])


if __name__ == "__main__":
    unittest.main()
