import json
import shutil
import subprocess
import unittest

from hcu_causal_canonical_v1 import (
    CANONICALIZATION_SCHEMA,
    HCUCanonicalizationError,
    canonical_bytes,
    canonical_sha256,
)

NODE_REFERENCE = r'''
'use strict';
const crypto = require('crypto');
const schema = 'ENTITYOS_HCU_TYPED_CANONICAL/v1';
const prefix = Buffer.concat([Buffer.from(schema, 'ascii'), Buffer.from([0])]);
function u64(n) { const b=Buffer.alloc(8); b.writeBigUInt64BE(BigInt(n)); return b; }
function validString(v) {
  for (let i=0;i<v.length;i++) {
    const c=v.charCodeAt(i);
    if (c>=0xD800 && c<=0xDBFF) {
      if (i+1>=v.length) throw new Error('STRING_NOT_VALID_UNICODE');
      const d=v.charCodeAt(++i); if (d<0xDC00 || d>0xDFFF) throw new Error('STRING_NOT_VALID_UNICODE');
    } else if (c>=0xDC00 && c<=0xDFFF) throw new Error('STRING_NOT_VALID_UNICODE');
  }
}
function text(v) { validString(v); const r=Buffer.from(v,'utf8'); return Buffer.concat([Buffer.from('s'),u64(r.length),r]); }
function num(v) {
  if (!Number.isFinite(v)) throw new Error('NONFINITE_NUMBER_FORBIDDEN');
  if (Number.isInteger(v) && Math.abs(v)>Number.MAX_SAFE_INTEGER) throw new Error('INTEGER_OUTSIDE_IJSON_SAFE_RANGE');
  if (Object.is(v,-0)) v=0;
  const b=Buffer.alloc(9); b.write('d',0,'ascii'); b.writeDoubleBE(v,1); return b;
}
function enc(v) {
  if (v===null) return Buffer.from('n');
  if (v===true) return Buffer.from('t');
  if (v===false) return Buffer.from('f');
  if (typeof v==='number') return num(v);
  if (typeof v==='string') return text(v);
  if (Array.isArray(v)) return Buffer.concat([Buffer.from('a'),u64(v.length),...v.map(enc)]);
  if (typeof v==='object') {
    const keys=Object.keys(v).sort((a,b)=>Buffer.compare(Buffer.from(a,'utf8'),Buffer.from(b,'utf8')));
    const parts=[Buffer.from('o'),u64(keys.length)];
    for (const k of keys) parts.push(text(k),enc(v[k]));
    return Buffer.concat(parts);
  }
  throw new Error('TYPE_UNSUPPORTED');
}
const input=JSON.parse(process.argv[1]);
const out=Buffer.concat([prefix,enc(input)]);
process.stdout.write(JSON.stringify({schema,hex:out.toString('hex'),sha256:crypto.createHash('sha256').update(out).digest('hex')}));
'''


class HCUCanonicalizationTests(unittest.TestCase):
    def test_schema_is_explicit_and_versioned(self):
        self.assertEqual(CANONICALIZATION_SCHEMA, "ENTITYOS_HCU_TYPED_CANONICAL/v1")

    def test_map_order_is_irrelevant(self):
        self.assertEqual(canonical_sha256({"b": 2, "a": 1}), canonical_sha256({"a": 1, "b": 2}))

    def test_integer_and_equal_float_are_same_json_number(self):
        self.assertEqual(canonical_sha256({"n": 1}), canonical_sha256({"n": 1.0}))

    def test_negative_zero_collapses_to_zero(self):
        self.assertEqual(canonical_sha256({"n": -0.0}), canonical_sha256({"n": 0.0}))

    def test_nonfinite_number_fails_closed(self):
        with self.assertRaisesRegex(HCUCanonicalizationError, "NONFINITE_NUMBER_FORBIDDEN"):
            canonical_bytes({"n": float("nan")})

    def test_integer_outside_ijson_safe_range_fails_closed(self):
        with self.assertRaisesRegex(HCUCanonicalizationError, "INTEGER_OUTSIDE_IJSON_SAFE_RANGE"):
            canonical_bytes({"n": 2**53})

    def test_value_change_changes_digest(self):
        self.assertNotEqual(canonical_sha256({"x": 0.55}), canonical_sha256({"x": 0.56}))

    def test_unicode_nested_order_is_deterministic(self):
        a = {"😀": "ä", "a": ["€", True, None]}
        b = {"a": ["€", True, None], "😀": "ä"}
        self.assertEqual(canonical_sha256(a), canonical_sha256(b))

    def test_independent_node_reference_matches_exact_bytes_and_digest(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node runtime unavailable; cross-language gate remains unexecuted")
        vectors = [
            {"schema": "HCU_REACTIVE_EVENT/v1", "entity_generation": 7, "novelty": 0.55, "due_recheck": False},
            {"z": [-0.0, 1, 1.5, 1e-7], "a": "€", "😀": {"ä": True, "n": None}},
            {"engine": {"id": "hcu_local_08b", "artifact": "a" * 64}, "lanes": ["critic", "world"], "projection": True},
            {"\ue000": "BMP_PRIVATE_USE", "\U00010000": "SUPPLEMENTARY"},
        ]
        for vector in vectors:
            raw = subprocess.check_output(
                [node, "-e", NODE_REFERENCE, json.dumps(vector, ensure_ascii=False, separators=(",", ":"))],
                text=True,
            )
            reference = json.loads(raw)
            self.assertEqual(reference["schema"], CANONICALIZATION_SCHEMA)
            self.assertEqual(reference["hex"], canonical_bytes(vector).hex())
            self.assertEqual(reference["sha256"], canonical_sha256(vector))


if __name__ == "__main__":
    unittest.main()
