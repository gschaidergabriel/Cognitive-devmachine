#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_free_evidence_forge as forge


class ForgeOpenAlex871Tests(unittest.TestCase):
    def test_classic_works_search_uses_snake_case_per_page(self):
        con = sqlite3.connect(":memory:")
        con.executescript(
            """
            CREATE TABLE processed_questions(
              question_hash TEXT PRIMARY KEY,
              processed_at TEXT NOT NULL
            );
            CREATE TABLE discoveries(
              discovery_hash TEXT PRIMARY KEY,
              question_hash TEXT NOT NULL,
              question TEXT NOT NULL,
              provider TEXT NOT NULL,
              source_id TEXT,
              title TEXT,
              url TEXT,
              metadata_json TEXT NOT NULL,
              created_at TEXT NOT NULL,
              reproduced_state TEXT
            );
            CREATE TABLE counters(
              key TEXT PRIMARY KEY,
              value REAL NOT NULL DEFAULT 0
            );
            """
        )
        seen: list[tuple[str, str]] = []

        def fake_http_json(provider, owner, url, *, headers=None, timeout=35):
            del owner, headers, timeout
            seen.append((provider, url))
            if provider == "openalex":
                return 200, {"results": []}, {}
            if provider == "crossref":
                return 200, {"message": {"items": []}}, {}
            if provider == "semantic_scholar":
                return 200, {"data": []}, {}
            if provider == "github":
                return 200, {"items": []}, {}
            if provider == "huggingface_hub":
                return 200, [], {}
            raise AssertionError(provider)

        try:
            with mock.patch.object(forge, "http_json", side_effect=fake_http_json), \
                 mock.patch.object(forge, "secret", return_value=""):
                asyncio.run(forge.discovery_for_question(con, "typed causal provenance"))
        finally:
            con.close()

        openalex_urls = [url for provider, url in seen if provider == "openalex"]
        self.assertEqual(len(openalex_urls), 1)
        self.assertIn("/works?search=", openalex_urls[0])
        self.assertIn("&per_page=5", openalex_urls[0])
        self.assertNotIn("per-page", openalex_urls[0])


if __name__ == "__main__":
    unittest.main()
