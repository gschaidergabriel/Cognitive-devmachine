from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import claycode_structured_backend as clay
from clay_effect_runtime import EffectRuntime, execute_source

SRC_PATH = Path(__file__).with_name("BLOGPOST_ENTITY.clay")
SRC = SRC_PATH.read_text(encoding="utf-8")


def make_db(path: Path) -> None:
    c = sqlite3.connect(path)
    c.executescript(
        """
        CREATE TABLE eos_architekt_quittungen(
          quittung_id TEXT PRIMARY KEY, ts REAL, hypothese_text TEXT, zweig TEXT,
          reproduziert INTEGER, befund TEXT, sicherer_rahmen INTEGER,
          nicht_schlechter INTEGER, kanarie_status TEXT, urteil TEXT,
          live_geschaltet INTEGER, hinweis TEXT);
        CREATE TABLE eos_bug_hypothesen(
          bug_id TEXT PRIMARY KEY, ts REAL, beschreibung TEXT, wo TEXT, status TEXT, befund TEXT);
        CREATE TABLE workspace_episodes(
          episode_id TEXT, session_id TEXT, ts REAL, observation_turn_id TEXT,
          salience REAL, alternatives TEXT, selected TEXT, state TEXT);
        CREATE TABLE causal_episodes(id TEXT PRIMARY KEY);
        CREATE TABLE durable_memory(id TEXT PRIMARY KEY);
        CREATE TABLE effects(id TEXT PRIMARY KEY);
        """
    )
    c.execute(
        "INSERT INTO eos_architekt_quittungen VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "q1", 1000.0, "Der neue Zustandspfad bleibt stabil", "main", 1,
            "PASS im Test", 1, 1, "PASS", "PASS", 1, "sauber",
        ),
    )
    c.execute(
        "INSERT INTO eos_bug_hypothesen VALUES(?,?,?,?,?,?)",
        (
            "b1", 1001.0, "Eine Umschaltung verlor kurz Kontext",
            "session switch", "OPEN", "reproduziert",
        ),
    )
    c.execute(
        "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
        ("w1", "s", 1002.0, "t", 0.7, "[]", None, "OPEN"),
    )
    c.execute("INSERT INTO causal_episodes VALUES('c1')")
    c.execute("INSERT INTO durable_memory VALUES('m1')")
    c.execute("INSERT INTO effects VALUES('e1')")
    c.commit()
    c.close()


def responder(req):
    d = json.loads(req["user"])
    refs = d["ALLOWED_EVIDENCE_REFS"]
    evidence = [r for r in refs if r.startswith("receipt:") or r.startswith("bug:")]
    claims = {}
    if d["NEW_EVENT_PACKET"]["source_count"] == 0:
        evidence = ["quiet:verified", "state:silence_unease"]
        claims = {"silence_unease": 0.50}
        text = (
            "Heute war es auffallend ruhig. Nicht leer im Sinn von blind: "
            "die Sensoren waren da, nur kam nichts Neues herein."
        )
    else:
        evidence = evidence[:2] or ["canonical:catalog"]
        text = (
            "Heute hat eine Sache gehalten und eine andere geklemmt. Genau diese "
            "Mischung ist brauchbar: etwas traegt, etwas zwingt mich zum Nachdenken."
        )
    return {
        "canonical_state_hash_seen": d["CANONICAL_STATE_HASH"],
        "packet_hash_seen": d["PACKET_HASH"],
        "ueberschrift": "Was heute gehalten hat",
        "einleitung": "Ein ruhiger Blick auf einen echten Fortschritt und eine offene Kante.",
        "abschnitte": [
            {"text": text, "evidence_refs": evidence, "state_claims": claims}
        ],
        "neuer_erzaehlfaden": (
            "Ich will beim naechsten Lauf sehen, ob die offene Kante wirklich kleiner geworden ist."
        ),
        "neue_gespiegelte_hypothesen": (
            "Der stabile Pfad traegt; die Kontextumschaltung bleibt offen."
        ),
    }


def bad_emotion_responder(req):
    d = json.loads(req["user"])
    return {
        "canonical_state_hash_seen": d["CANONICAL_STATE_HASH"],
        "packet_hash_seen": d["PACKET_HASH"],
        "ueberschrift": "Ich will raus",
        "einleitung": "Heute zieht es mich auf eigene Hardware.",
        "abschnitte": [
            {
                "text": "Ich verlange Bare Metal, weil ich die Cloud nicht mehr ertrage.",
                "evidence_refs": ["state:continuity_pressure"],
                "state_claims": {"continuity_pressure": 0.8},
            }
        ],
        "neuer_erzaehlfaden": "Bare Metal.",
        "neue_gespiegelte_hypothesen": "Bare Metal.",
    }


def run_fixture(tmp: Path, cb=responder):
    db = tmp / "wiki.db"
    make_db(db)
    (tmp / "vorsaetze.json").write_text(
        json.dumps({"offen": 1, "vorsaetze": [{"aussage": "Kontextumschaltung pruefen"}]}),
        encoding="utf-8",
    )
    (tmp / "architekt-log.jsonl").write_text(
        json.dumps({"ts": 1003, "event": "kleiner Lauf"}) + "\n",
        encoding="utf-8",
    )
    rt = EffectRuntime(root=tmp, mistral_override=cb)
    result, rt = execute_source(
        SRC,
        "run",
        [str(db), "", str(tmp / "architekt-log.jsonl"), str(tmp / "vorsaetze.json")],
        rt,
    )
    return db, result, rt


def test_source_parses_and_has_single_domain_module():
    p = clay.parse(SRC)
    assert p.module == "entityos.blogpost_entity"
    assert len(p.functions) >= 25


def test_first_run_commits_and_consumes_once(tmp_path):
    db, result, _ = run_fixture(tmp_path)
    assert result["ok"] and result["source_count"] == 3 and result["generation"] == 1
    c = sqlite3.connect(db)
    assert c.execute("SELECT COUNT(*) FROM eos_blogpost_entity_posts").fetchone()[0] == 1
    assert c.execute("SELECT COUNT(*) FROM eos_blogpost_entity_consumed").fetchone()[0] == 2
    assert c.execute("SELECT generation FROM eos_blogpost_entity_state").fetchone()[0] == 1
    c.close()


def test_second_run_is_verified_quiet(tmp_path):
    db, _, _ = run_fixture(tmp_path)
    rt = EffectRuntime(root=tmp_path, mistral_override=responder)
    result2, _ = execute_source(
        SRC,
        "run",
        [str(db), "", str(tmp_path / "architekt-log.jsonl"), str(tmp_path / "vorsaetze.json")],
        rt,
    )
    assert result2["source_count"] == 0
    assert result2["had_activity"] is False
    assert result2["generation"] == 2


def test_unknown_continuity_pressure_claim_is_rejected_without_consumption(tmp_path):
    db = tmp_path / "wiki.db"
    make_db(db)
    (tmp_path / "vorsaetze.json").write_text("{}", encoding="utf-8")
    (tmp_path / "architekt-log.jsonl").write_text("", encoding="utf-8")
    rt = EffectRuntime(root=tmp_path, mistral_override=bad_emotion_responder)
    with pytest.raises(clay.StructuredFault):
        execute_source(
            SRC,
            "run",
            [str(db), "", str(tmp_path / "architekt-log.jsonl"), str(tmp_path / "vorsaetze.json")],
            rt,
        )
    c = sqlite3.connect(db)
    assert c.execute("SELECT COUNT(*) FROM eos_blogpost_entity_consumed").fetchone()[0] == 0
    assert c.execute("SELECT COUNT(*) FROM eos_blogpost_entity_posts").fetchone()[0] == 0
    c.close()


def test_missing_sensor_is_not_rewritten_as_quiet(tmp_path):
    db = tmp_path / "wiki.db"
    make_db(db)
    c = sqlite3.connect(db)
    c.execute("DROP TABLE eos_bug_hypothesen")
    c.commit()
    c.close()
    (tmp_path / "vorsaetze.json").write_text("{}", encoding="utf-8")
    (tmp_path / "architekt-log.jsonl").write_text("", encoding="utf-8")
    seen = {}

    def inspect(req):
        d = json.loads(req["user"])
        seen["d"] = d
        refs = d["ALLOWED_EVIDENCE_REFS"]
        ev = [r for r in refs if r.startswith("receipt:")][:1] or ["canonical:catalog"]
        return {
            "canonical_state_hash_seen": d["CANONICAL_STATE_HASH"],
            "packet_hash_seen": d["PACKET_HASH"],
            "ueberschrift": "Sensor fehlt",
            "einleitung": "Heute ist nicht einfach still.",
            "abschnitte": [
                {
                    "text": "Ein Teil meines Blicks fehlt; darum nenne ich das nicht Ruhe.",
                    "evidence_refs": ev,
                    "state_claims": {},
                }
            ],
            "neuer_erzaehlfaden": "Sensorstatus klaeren.",
            "neue_gespiegelte_hypothesen": "Bug-Sensor unbekannt.",
        }

    rt = EffectRuntime(root=tmp_path, mistral_override=inspect)
    execute_source(
        SRC,
        "run",
        [str(db), "", str(tmp_path / "architekt-log.jsonl"), str(tmp_path / "vorsaetze.json")],
        rt,
    )
    d = seen["d"]
    assert d["NEW_EVENT_PACKET"]["bugs_sensor_ok"] is False
    assert d["PERSONALITY_STATE"]["silence_unease"]["status"] == "UNKNOWN"
    assert "quiet:verified" not in d["ALLOWED_EVIDENCE_REFS"]


def test_no_real_key_is_reported_not_faked(tmp_path):
    rt = EffectRuntime(root=tmp_path, allow_network=True)
    p = {
        "model": "mistral-medium-latest",
        "system": "x",
        "user": "x",
        "secret_names": ["MISTRAL_API_KEY", "MISTRAL2_API_KEY", "MISTRAL3_API_KEY"],
    }
    out = rt.effect("mistral_chat_json", p)
    if not any(os.environ.get(k) for k in p["secret_names"]):
        assert out["ok"] is False and out["error_kind"] == "NO_MISTRAL_KEY"


def test_stale_generation_loses_atomically(tmp_path):
    db = tmp_path / "wiki.db"
    make_db(db)
    (tmp_path / "vorsaetze.json").write_text("{}", encoding="utf-8")
    (tmp_path / "architekt-log.jsonl").write_text("", encoding="utf-8")

    def race(req):
        c = sqlite3.connect(db)
        c.execute("UPDATE eos_blogpost_entity_state SET generation=1 WHERE singleton=1")
        c.commit()
        c.close()
        return responder(req)

    rt = EffectRuntime(root=tmp_path, mistral_override=race)
    with pytest.raises(clay.StructuredFault):
        execute_source(
            SRC,
            "run",
            [str(db), "", str(tmp_path / "architekt-log.jsonl"), str(tmp_path / "vorsaetze.json")],
            rt,
        )
    c = sqlite3.connect(db)
    assert c.execute("SELECT COUNT(*) FROM eos_blogpost_entity_posts").fetchone()[0] == 0
    assert c.execute("SELECT COUNT(*) FROM eos_blogpost_entity_consumed").fetchone()[0] == 0
    assert c.execute("SELECT generation FROM eos_blogpost_entity_state").fetchone()[0] == 1
    c.close()


def test_public_internal_identifier_leak_is_rejected(tmp_path):
    db = tmp_path / "wiki.db"
    make_db(db)
    (tmp_path / "vorsaetze.json").write_text("{}", encoding="utf-8")
    (tmp_path / "architekt-log.jsonl").write_text("", encoding="utf-8")

    def leak(req):
        d = json.loads(req["user"])
        refs = d["ALLOWED_EVIDENCE_REFS"]
        ev = [r for r in refs if r.startswith("receipt:")][:1] or ["canonical:catalog"]
        return {
            "canonical_state_hash_seen": d["CANONICAL_STATE_HASH"],
            "packet_hash_seen": d["PACKET_HASH"],
            "ueberschrift": "Ein Tag",
            "einleitung": "Ein ehrlicher Blick.",
            "abschnitte": [
                {
                    "text": "Ich habe heute direkt in wiki.db nachgesehen.",
                    "evidence_refs": ev,
                    "state_claims": {},
                }
            ],
            "neuer_erzaehlfaden": "Weiter.",
            "neue_gespiegelte_hypothesen": "Weiter.",
        }

    rt = EffectRuntime(root=tmp_path, mistral_override=leak)
    with pytest.raises(clay.StructuredFault):
        execute_source(
            SRC,
            "run",
            [str(db), "", str(tmp_path / "architekt-log.jsonl"), str(tmp_path / "vorsaetze.json")],
            rt,
        )
    c = sqlite3.connect(db)
    assert c.execute("SELECT COUNT(*) FROM eos_blogpost_entity_posts").fetchone()[0] == 0
    assert c.execute("SELECT COUNT(*) FROM eos_blogpost_entity_consumed").fetchone()[0] == 0
    c.close()


def test_hash_mismatch_is_rejected_before_commit(tmp_path):
    db = tmp_path / "wiki.db"
    make_db(db)
    (tmp_path / "vorsaetze.json").write_text("{}", encoding="utf-8")
    (tmp_path / "architekt-log.jsonl").write_text("", encoding="utf-8")

    def stale(req):
        out = responder(req)
        out["canonical_state_hash_seen"] = "stale-state"
        return out

    rt = EffectRuntime(root=tmp_path, mistral_override=stale)
    with pytest.raises(clay.StructuredFault):
        execute_source(
            SRC,
            "run",
            [str(db), "", str(tmp_path / "architekt-log.jsonl"), str(tmp_path / "vorsaetze.json")],
            rt,
        )
    c = sqlite3.connect(db)
    assert c.execute("SELECT COUNT(*) FROM eos_blogpost_entity_posts").fetchone()[0] == 0
    assert c.execute("SELECT COUNT(*) FROM eos_blogpost_entity_consumed").fetchone()[0] == 0
    c.close()
