#!/usr/bin/env python3
"""taetigkeit.py — harvests Claude Code JSONL transcripts into structured
activity rows (taetigkeit) and free edges to wiki articles (taetigkeit_kante).

Zero model calls. Zero network to any LLM. Pure file parsing + sqlite.

Two modes, because the wiki.db only lives on frank-api but transcripts also
live on other hosts:

  scan   --root <dir> --host <wirt> --out <jsonl>
      Pure extraction. Reads *.jsonl transcripts under --root, emits one
      compact JSON object per tool_use line to --out. No sqlite. No network.
      Only structured fields ever cross into --out: tool name, target path,
      truncated Bash command, success/error, session/agent id, timestamps,
      source file + line number, sha256 of that raw line. NEVER prompt text,
      NEVER model text, NEVER file contents (old_string/new_string/content
      are never read).

  load   --db <wiki.db> --in <jsonl> [--in <jsonl> ...]
      Idempotent insert of scan output into taetigkeit (INSERT OR IGNORE on
      roh_hash uniqueness). Then computes taetigkeit_kante by matching
      ziel_pfad against artikel.quelle: exact match first, then a translated
      match for paths that live under a directory also mirrored under
      /opt/clayverse/baeume/<repo>/. WAL + busy_timeout + retry/backoff so it
      never crashes if one of the sibling agents holds a write lock.

Usage on host holding the transcripts (e.g. this machine, or frank-api):
    python3 taetigkeit.py scan --root ~/.claude/projects --host ai-core-node-projekt-frankenstein --out batch_local.jsonl

Usage on frank-api (where wiki.db lives):
    python3 taetigkeit.py scan --root /var/lib/clay/.claude/projects --host clayverse --out batch_clay.jsonl
    python3 taetigkeit.py load --db /var/lib/clay/wiki.db --in batch_local.jsonl --in batch_clay.jsonl
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sqlite3
import sys
import time

MAX_CMD = 200
BAEUME_ROOT = "/opt/clayverse/baeume"

# --- path/command extraction (structure only, never prose/content) ---

def extract_ziel_pfad(name, inp):
    if not isinstance(inp, dict):
        return None
    for key in ("file_path", "path", "notebook_path"):
        v = inp.get(key)
        if isinstance(v, str):
            return v
    if name == "Bash" and isinstance(inp.get("command"), str):
        m = re.search(r"(/[A-Za-z0-9_\-./]+)", inp["command"])
        if m:
            return m.group(1)
    if name in ("WebFetch",) and isinstance(inp.get("url"), str):
        return inp["url"]
    return None


def extract_aktion(name, inp):
    if not isinstance(inp, dict):
        return None
    if name == "Bash" and isinstance(inp.get("command"), str):
        return inp["command"][:MAX_CMD]
    return None


# --- scan mode ---

def iter_jsonl_files(root):
    for fp in glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True):
        yield fp


def scan(root, host, out_path):
    root = os.path.expanduser(root)
    n_files = 0
    n_lines = 0
    n_toolcalls = 0
    n_written = 0
    sessions = set()
    with open(out_path, "w") as outf:
        for fp in iter_jsonl_files(root):
            n_files += 1
            try:
                with open(fp, "r", errors="replace") as f:
                    raw_lines = f.readlines()
            except Exception as e:
                print(f"WARN cannot read {fp}: {e}", file=sys.stderr)
                continue

            # pass 1: index tool_use calls by line number + id
            calls = []  # (lineno, raw_line, sha, session, agent, ts, name, ziel, aktion, tool_id)
            result_by_id = {}  # tool_id -> is_error bool

            for i, raw in enumerate(raw_lines, start=1):
                n_lines += 1
                line = raw.rstrip("\n")
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                t = d.get("type")
                if t == "assistant":
                    msg = d.get("message", {})
                    content = msg.get("content", [])
                    if not isinstance(content, list):
                        continue
                    sid = d.get("sessionId") or d.get("session_id")
                    agent = d.get("agentId") or "haupt"
                    ts = d.get("timestamp")
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "tool_use":
                            n_toolcalls += 1
                            name = c.get("name")
                            inp = c.get("input")
                            ziel = extract_ziel_pfad(name, inp)
                            aktion = extract_aktion(name, inp)
                            tool_id = c.get("id")
                            # Dedup key: hash the tool_use id, not the raw
                            # serialized line. The id is globally unique and
                            # assigned once by Claude Code itself, so the
                            # same real event gets the same hash whether it
                            # is seen here (retroactive) or via the live
                            # PostToolUse hook (different JSON serialization,
                            # would otherwise silently NOT collide and
                            # double-insert the same tool call). zeile_nr +
                            # quelle still give exact line-provenance.
                            if tool_id:
                                sha = hashlib.sha256(("tool_use:" + tool_id).encode("utf-8")).hexdigest()
                            else:
                                sha = hashlib.sha256(line.encode("utf-8", "replace")).hexdigest()
                            calls.append([i, sha, sid, agent, ts, name, ziel, aktion, tool_id])
                            if sid:
                                sessions.add(sid)
                elif t == "user":
                    msg = d.get("message", {})
                    content = msg.get("content", [])
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "tool_result":
                                tid = c.get("tool_use_id")
                                if tid:
                                    result_by_id[tid] = bool(c.get("is_error"))

            for (lineno, sha, sid, agent, ts, name, ziel, aktion, tool_id) in calls:
                is_error = result_by_id.get(tool_id)
                ergebnis = "unknown" if is_error is None else ("error" if is_error else "ok")
                row = {
                    "wirt": host,
                    "instanz": agent,
                    "sitzung": sid,
                    "zeit": ts,
                    "werkzeug": name,
                    "ziel_pfad": ziel,
                    "aktion": aktion,
                    "ergebnis": ergebnis,
                    "quelle": fp,
                    "zeile_nr": lineno,
                    "roh_hash": sha,
                }
                outf.write(json.dumps(row, ensure_ascii=False) + "\n")
                n_written += 1

    print(f"scan root={root} host={host}")
    print(f"  files={n_files} lines={n_lines} tool_use={n_toolcalls} written={n_written} sessions={len(sessions)}")
    print(f"  out={out_path}")


# --- load mode ---

DDL = """
CREATE TABLE IF NOT EXISTS taetigkeit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wirt TEXT,
    instanz TEXT,
    sitzung TEXT,
    zeit TEXT,
    werkzeug TEXT,
    ziel_pfad TEXT,
    aktion TEXT,
    ergebnis TEXT,
    quelle TEXT,
    zeile_nr INTEGER,
    roh_hash TEXT UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_taetigkeit_ziel_pfad ON taetigkeit(ziel_pfad);
CREATE INDEX IF NOT EXISTS idx_taetigkeit_sitzung ON taetigkeit(sitzung);

CREATE TABLE IF NOT EXISTS taetigkeit_kante (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taetigkeit_id INTEGER NOT NULL,
    artikel_id TEXT NOT NULL,
    art TEXT NOT NULL,
    beleg TEXT,
    UNIQUE(taetigkeit_id, artikel_id, art)
);
"""


def connect_retry(db_path, tries=8, base_sleep=0.5):
    last_exc = None
    for attempt in range(tries):
        try:
            conn = sqlite3.connect(db_path, timeout=30)
            conn.execute("PRAGMA busy_timeout=30000")
            conn.execute("PRAGMA journal_mode=WAL")
            return conn
        except sqlite3.OperationalError as e:
            last_exc = e
            time.sleep(base_sleep * (2 ** attempt))
    raise last_exc


def exec_retry(conn, sql, params=(), tries=8, base_sleep=0.5):
    last_exc = None
    for attempt in range(tries):
        try:
            return conn.execute(sql, params)
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() or "busy" in str(e).lower():
                last_exc = e
                time.sleep(base_sleep * (2 ** attempt))
                continue
            raise
    raise last_exc


def commit_retry(conn, tries=8, base_sleep=0.5):
    last_exc = None
    for attempt in range(tries):
        try:
            conn.commit()
            return
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() or "busy" in str(e).lower():
                last_exc = e
                time.sleep(base_sleep * (2 ** attempt))
                continue
            raise
    raise last_exc


def load_rows(conn, in_paths):
    n_seen = 0
    n_inserted = 0
    for path in in_paths:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                n_seen += 1
                cur = exec_retry(
                    conn,
                    """INSERT OR IGNORE INTO taetigkeit
                       (wirt, instanz, sitzung, zeit, werkzeug, ziel_pfad, aktion, ergebnis, quelle, zeile_nr, roh_hash)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        row.get("wirt"), row.get("instanz"), row.get("sitzung"), row.get("zeit"),
                        row.get("werkzeug"), row.get("ziel_pfad"), row.get("aktion"), row.get("ergebnis"),
                        row.get("quelle"), row.get("zeile_nr"), row.get("roh_hash"),
                    ),
                )
                if cur.rowcount:
                    n_inserted += 1
                if n_inserted and n_inserted % 500 == 0:
                    commit_retry(conn)
    commit_retry(conn)
    return n_seen, n_inserted


def build_kante(conn):
    # articles: quelle -> [ids]. Several artikel rows can share one source
    # file (e.g. different art/kuration passes over the same KMP) — a real
    # file-touch is evidence for ALL of them, so keep the full list, never
    # just the first.
    quelle_to_ids = {}
    dupe_quelle = 0
    for aid, q in exec_retry(conn, "SELECT id, quelle FROM artikel WHERE quelle IS NOT NULL"):
        if q in quelle_to_ids:
            dupe_quelle += 1
        quelle_to_ids.setdefault(q, []).append(aid)

    baeume_repos = set()
    for (q,) in exec_retry(conn, "SELECT quelle FROM artikel WHERE quelle LIKE ?", (BAEUME_ROOT + "/%",)):
        parts = q[len(BAEUME_ROOT) + 1:].split("/")
        if parts:
            baeume_repos.add(parts[0])

    exact_hits = 0
    translated_hits = 0
    kante_inserted = 0

    rows = list(exec_retry(
        conn,
        "SELECT id, ziel_pfad FROM taetigkeit WHERE ziel_pfad IS NOT NULL",
    ))
    for tid, ziel in rows:
        artikel_ids = []
        beleg = None
        if ziel in quelle_to_ids:
            artikel_ids = quelle_to_ids[ziel]
            beleg = ziel
            exact_hits += 1
        else:
            parts = ziel.split("/")
            for i, part in enumerate(parts):
                if part in baeume_repos:
                    rest = parts[i + 1:]
                    if rest and rest[0] == "contents":
                        rest = rest[1:]
                    cand = BAEUME_ROOT + "/" + part + "/" + "/".join(rest)
                    if cand in quelle_to_ids:
                        artikel_ids = quelle_to_ids[cand]
                        beleg = cand
                        translated_hits += 1
                    break
        for artikel_id in artikel_ids:
            cur = exec_retry(
                conn,
                """INSERT OR IGNORE INTO taetigkeit_kante (taetigkeit_id, artikel_id, art, beleg)
                   VALUES (?,?,?,?)""",
                (tid, artikel_id, "BEARBEITET", beleg),
            )
            if cur.rowcount:
                kante_inserted += 1

    commit_retry(conn)
    return {
        "exact_hits": exact_hits,
        "translated_hits": translated_hits,
        "kante_inserted": kante_inserted,
        "dupe_quelle": dupe_quelle,
        "baeume_repos": sorted(baeume_repos),
        "distinct_ziel_pfad_rows": len(rows),
    }


def orphan_count(conn):
    (n,) = exec_retry(
        conn,
        "SELECT COUNT(*) FROM artikel a WHERE NOT EXISTS (SELECT 1 FROM kante k WHERE k.von=a.id OR k.nach=a.id) "
        "AND NOT EXISTS (SELECT 1 FROM taetigkeit_kante tk WHERE tk.artikel_id=a.id)",
    ).fetchone()
    return n


def load(db_path, in_paths):
    conn = connect_retry(db_path)
    for stmt in DDL.strip().split(";\n\n") if False else [s for s in DDL.split(";") if s.strip()]:
        exec_retry(conn, stmt)
    commit_retry(conn)

    before_size = os.path.getsize(db_path)
    (before_count,) = exec_retry(conn, "SELECT COUNT(*) FROM taetigkeit").fetchone()

    n_seen, n_inserted = load_rows(conn, in_paths)
    stats = build_kante(conn)

    (after_count,) = exec_retry(conn, "SELECT COUNT(*) FROM taetigkeit").fetchone()
    (kante_count,) = exec_retry(conn, "SELECT COUNT(*) FROM taetigkeit_kante").fetchone()
    orphans = orphan_count(conn)

    after_size = os.path.getsize(db_path)

    print(f"load db={db_path}")
    print(f"  rows_seen_in_input={n_seen} newly_inserted={n_inserted}")
    print(f"  taetigkeit_total_before={before_count} taetigkeit_total_after={after_count}")
    print(f"  taetigkeit_kante_total={kante_count}")
    print(f"  match: exact={stats['exact_hits']} translated={stats['translated_hits']} "
          f"kante_newly_inserted={stats['kante_inserted']} dupe_quelle_in_artikel={stats['dupe_quelle']}")
    print(f"  baeume_repos_with_articles={stats['baeume_repos']}")
    print(f"  ziel_pfad_rows_considered={stats['distinct_ziel_pfad_rows']}")
    print(f"  orphan_articles_remaining(no kante, no taetigkeit_kante)={orphans}")
    print(f"  db_size_before={before_size} db_size_after={after_size}")
    conn.close()


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("scan")
    s1.add_argument("--root", required=True)
    s1.add_argument("--host", required=True)
    s1.add_argument("--out", required=True)

    s2 = sub.add_parser("load")
    s2.add_argument("--db", required=True)
    s2.add_argument("--in", dest="ins", action="append", required=True)

    args = ap.parse_args()
    if args.cmd == "scan":
        scan(args.root, args.host, args.out)
    elif args.cmd == "load":
        load(args.db, args.ins)


if __name__ == "__main__":
    main()
