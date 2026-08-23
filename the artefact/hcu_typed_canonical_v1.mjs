#!/usr/bin/env node
/**
 * Independent JavaScript implementation of ENTITYOS_HCU_TYPED_CANONICAL/v1.
 *
 * This mirrors the contract in hcu_typed_canonical_v1.py without importing Python
 * or JSON.stringify for canonical serialization. It is deliberately narrower than
 * RFC 8785 JCS and grants no truth, state, effect, provider, or model authority.
 */
import { createHash } from "node:crypto";

export const SCHEMA = "ENTITYOS_HCU_TYPED_CANONICAL/v1";
const DOMAIN_PREFIX = Buffer.from(`${SCHEMA}\0`, "ascii");
const SAFE_INTEGER_MIN = Number.MIN_SAFE_INTEGER;
const SAFE_INTEGER_MAX = Number.MAX_SAFE_INTEGER;

export class CanonicalizationError extends Error {}

function asciiKey(value) {
  if (typeof value !== "string" || value.length === 0) {
    throw new CanonicalizationError("OBJECT_KEY_NONEMPTY_STRING_REQUIRED");
  }
  for (const ch of value) {
    const cp = ch.codePointAt(0);
    if (cp < 0x20 || cp > 0x7e) {
      throw new CanonicalizationError("OBJECT_KEY_PRINTABLE_ASCII_REQUIRED");
    }
  }
  return value;
}

function quoteString(value) {
  if (typeof value !== "string") {
    throw new CanonicalizationError("STRING_REQUIRED");
  }
  let out = '"';
  for (const ch of value) {
    const cp = ch.codePointAt(0);
    if (cp >= 0xd800 && cp <= 0xdfff) {
      throw new CanonicalizationError("UNICODE_SURROGATE_FORBIDDEN");
    }
    switch (cp) {
      case 0x08: out += "\\b"; break;
      case 0x09: out += "\\t"; break;
      case 0x0a: out += "\\n"; break;
      case 0x0c: out += "\\f"; break;
      case 0x0d: out += "\\r"; break;
      case 0x22: out += '\\"'; break;
      case 0x5c: out += "\\\\"; break;
      default:
        if (cp < 0x20) {
          out += `\\u${cp.toString(16).padStart(4, "0")}`;
        } else {
          out += ch;
        }
    }
  }
  return `${out}"`;
}

function canonicalText(value) {
  if (value === null) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    if (!Number.isInteger(value)) {
      throw new CanonicalizationError("FLOAT_FORBIDDEN_USE_SCHEMA_TYPED_REPRESENTATION");
    }
    if (!Number.isSafeInteger(value) || value < SAFE_INTEGER_MIN || value > SAFE_INTEGER_MAX) {
      throw new CanonicalizationError("INTEGER_OUTSIDE_IJSON_SAFE_RANGE");
    }
    return String(value);
  }
  if (typeof value === "string") return quoteString(value);
  if (Array.isArray(value)) {
    return `[${value.map((item) => canonicalText(item)).join(",")}]`;
  }
  if (typeof value === "object") {
    const proto = Object.getPrototypeOf(value);
    if (proto !== Object.prototype && proto !== null) {
      throw new CanonicalizationError("TYPE_OUTSIDE_TYPED_CANONICAL_DOMAIN");
    }
    const ownKeys = Reflect.ownKeys(value);
    if (ownKeys.some((key) => typeof key !== "string")) {
      throw new CanonicalizationError("TYPE_OUTSIDE_TYPED_CANONICAL_DOMAIN");
    }
    if (ownKeys.some((key) => !Object.prototype.propertyIsEnumerable.call(value, key))) {
      throw new CanonicalizationError("TYPE_OUTSIDE_TYPED_CANONICAL_DOMAIN");
    }
    const keys = ownKeys.map(asciiKey);
    keys.sort((a, b) => Buffer.compare(Buffer.from(a, "ascii"), Buffer.from(b, "ascii")));
    const members = keys.map((key) => `${quoteString(key)}:${canonicalText(value[key])}`);
    return `{${members.join(",")}}`;
  }
  throw new CanonicalizationError("TYPE_OUTSIDE_TYPED_CANONICAL_DOMAIN");
}

export function canonicalBytes(value) {
  return Buffer.from(canonicalText(value), "utf8");
}

export function identitySha256(value) {
  return createHash("sha256").update(DOMAIN_PREFIX).update(canonicalBytes(value)).digest("hex");
}
