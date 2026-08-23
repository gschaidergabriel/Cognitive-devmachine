#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import {
  CanonicalizationError,
  canonicalBytes,
  identitySha256,
} from "../hcu_typed_canonical_v1.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const vectors = JSON.parse(
  readFileSync(path.join(here, "hcu_typed_canonical_vectors_v1.json"), "utf8"),
);

assert.equal(vectors.canonical_schema, "ENTITYOS_HCU_TYPED_CANONICAL/v1");
for (const vector of vectors.vectors) {
  assert.equal(canonicalBytes(vector.value).toString("hex"), vector.canonical_hex, `${vector.name}:bytes`);
  assert.equal(identitySha256(vector.value), vector.identity_sha256, `${vector.name}:digest`);
}

assert.throws(
  () => canonicalBytes({ novelty: 0.55 }),
  (error) => error instanceof CanonicalizationError && /FLOAT_FORBIDDEN/.test(error.message),
);
assert.throws(
  () => canonicalBytes({ n: Number.MAX_SAFE_INTEGER + 1 }),
  (error) => error instanceof CanonicalizationError && /INTEGER_OUTSIDE/.test(error.message),
);
assert.throws(
  () => canonicalBytes({ "€": "value" }),
  (error) => error instanceof CanonicalizationError && /OBJECT_KEY_PRINTABLE_ASCII_REQUIRED/.test(error.message),
);
assert.throws(
  () => canonicalBytes({ value: "\ud800" }),
  (error) => error instanceof CanonicalizationError && /UNICODE_SURROGATE_FORBIDDEN/.test(error.message),
);
assert.throws(
  () => canonicalBytes({ value: new Date(0) }),
  (error) => error instanceof CanonicalizationError && /TYPE_OUTSIDE_TYPED_CANONICAL_DOMAIN/.test(error.message),
);
assert.notEqual(identitySha256(true), identitySha256(1));

console.log(`PASS ${vectors.vectors.length} shared vectors + 6 fail-closed JS regressions`);
