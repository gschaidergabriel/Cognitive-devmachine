import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from typed_canonical_v1 import SCHEMA, canonical_bytes, canonical_sha256


NODE_REFERENCE = r'''
'use strict';
const crypto = require('crypto');
const SCHEMA = 'ENTITYOS_TYPED_CANONICAL_JSON/v1';
const MAX_SAFE = Number.MAX_SAFE_INTEGER;
const KEY_RE = /^[A-Za-z0-9_.:/-]{1,128}$/;
function encodeString(value) {
  let out='"';
  for (const ch of value) {
    const cp=ch.codePointAt(0);
    if (cp>=0xD800 && cp<=0xDFFF) throw new Error('INVALID_UNICODE_SCALAR');
    if (ch==='"') out+='\\"';
    else if (ch==='\\') out+='\\\\';
    else if (ch==='\b') out+='\\b';
    else if (ch==='\t') out+='\\t';
    else if (ch==='\n') out+='\\n';
    else if (ch==='\f') out+='\\f';
    else if (ch==='\r') out+='\\r';
    else if (cp<0x20) out+='\\u'+cp.toString(16).padStart(4,'0');
    else out+=ch;
  }
  return out+'"';
}
function serialize(value) {
  if (value===null) return 'null';
  if (value===true) return 'true';
  if (value===false) return 'false';
  if (typeof value==='number') {
    if (!Number.isSafeInteger(value) || Math.abs(value)>MAX_SAFE) throw new Error('INTEGER_OUTSIDE_SAFE_RANGE');
    return String(value);
  }
  if (typeof value==='string') return encodeString(value);
  if (Array.isArray(value)) return '['+value.map(serialize).join(',')+']';
  if (typeof value==='object') {
    const keys=Object.keys(value);
    for (const key of keys) if (!KEY_RE.test(key)) throw new Error('OBJECT_KEY_OUTSIDE_TYPED_ASCII_DOMAIN');
    keys.sort();
    return '{'+keys.map(k=>encodeString(k)+':'+serialize(value[k])).join(',')+'}';
  }
  throw new Error('TYPE_NOT_ADMITTED');
}
function canonicalBytes(value) { return Buffer.from(serialize(value),'utf8'); }
function canonicalSha256(value) {
  const envelope={canonicalization_schema:SCHEMA,value:value};
  return crypto.createHash('sha256').update(canonicalBytes(envelope)).digest('hex');
}
const input=JSON.parse(process.argv[1]);
const bytes=canonicalBytes(input);
process.stdout.write(JSON.stringify({schema:SCHEMA,hex:bytes.toString('hex'),sha256:canonicalSha256(input)}));
'''


class CrossLanguageTypedCanonicalTests(unittest.TestCase):
    def test_python_and_independent_node_reference_match(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node unavailable: independent implementation gate remains unexecuted")
        vectors = [
            {"z": 2, "a": 1},
            {"event": {"schema": "HCU_REACTIVE_EVENT/v1", "generation": 7}, "lanes": ["critic", "world"]},
            {"s": "\b\t\n\f\r\u000f\"\\€", "n": None, "b": True},
            {"unicode_value": "é / e\u0301 / 😀", "safe_int": 9007199254740991},
            {"nested": [{"k": "v"}, [1, 2, 3], False]},
        ]
        for value in vectors:
            encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            raw = subprocess.check_output([node, "-e", NODE_REFERENCE, encoded], text=True)
            reference = json.loads(raw)
            self.assertEqual(reference["schema"], SCHEMA)
            self.assertEqual(reference["hex"], canonical_bytes(value).hex())
            self.assertEqual(reference["sha256"], canonical_sha256(value))


if __name__ == "__main__":
    unittest.main()
