"""Audit tests for tools/trigger2_run4_dataset_build_v1.py (run-4 upload dataset combiner)."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger2_run4_dataset_build_v1.py"
spec = importlib.util.spec_from_file_location("run4_build", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules["run4_build"] = mod
spec.loader.exec_module(mod)


@pytest.fixture(scope="module")
def summary():
    return mod.build()


def test_no_duplicate_prompts(summary):
    assert summary["duplicate_prompt_count_across_all_files"] == 0


def test_no_cross_file_collisions(summary):
    assert summary["cross_file_id_collisions"] == 0
    assert summary["cross_file_prompt_collisions"] == 0


def test_bias_fix_file_included(summary):
    assert summary["new_for_run4_row_count"] == 275


def test_b1_materialized_not_in_source_list():
    # regression guard for the bug found+fixed this session: the superseded intermediate must
    # never silently reappear in the family file list.
    assert "TRIGGER2_B1_BINDING_MATERIALIZED_CANDIDATE_V1.jsonl" not in mod.FAMILY_FILES_V1_OR_V2


def test_together_message_schema(summary):
    with open(mod.OUT_PATH) as f:
        lines = [json.loads(line) for line in f]
    assert len(lines) == summary["total_train_rows"]
    for row in lines[:50] + lines[-50:]:
        assert set(row.keys()) == {"messages"}
        msgs = row["messages"]
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user" and isinstance(msgs[0]["content"], str) and msgs[0]["content"]
        assert msgs[1]["role"] == "assistant" and isinstance(msgs[1]["content"], str) and msgs[1]["content"]


def test_every_listed_family_file_exists():
    for fname in mod.FAMILY_FILES_V1_OR_V2 + [mod.NEW_FOR_RUN4]:
        assert (mod.TRAINING_DIR / fname).exists(), fname
