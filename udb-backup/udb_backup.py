#!/usr/bin/env python3
"""
EntityOS Unified-DB Backup -- versioniertes Backup der Herz-DB wiki.db
in ein privates GitHub-Repo. Rein mechanisch, KEIN LLM-Aufruf.

Ablauf:
  1. Konsistenter Snapshot von wiki.db per WAL-sicherem Dateikopie-Verfahren
     (wal -> shm -> db, in dieser Reihenfolge -- siehe make_snapshot() fuer
     die Begruendung). wiki.db wird dabei NUR gelesen, nie geschrieben.
     Der `.backup`-API-Weg (sqlite3 ".backup") wurde GETESTET und verworfen:
     wiki.db steht unter Dauerschreiblast (Puls/Vorprozessor), wodurch die
     Online-Backup-API in einen Restart-Loop geraet und nie fertig wird
     (empirisch: 15+ Minuten, 0 Fortschritt, 97% CPU). Die Datei-Kopie plus
     Checkpoint AUF DER KOPIE ist genauso read-only fuer die Quelle, aber
     robust gegen Dauerschreiblast.
  2. Aus dem Snapshot: SQL-Dump ALLER Inhalts-/Content-Tabellen, FTS5-
     Schattentabellen (_data/_idx/_docsize/_config/_content) ausgeschlossen
     (regenerierbar, riesig, verrauschen den Diff). Pro Tabelle eine eigene
     Datei (dump/<tabelle>.<NNN>.sql); grosse Tabellen werden in mehrere
     Chunks unter CHUNK_TARGET_BYTES gesplittet, damit KEINE Datei GitHubs
     100-MB-Hard-Limit pro Datei reisst (die Tabelle `datei` allein ist
     >2 GB Volltext).
  3. manifest.json mit Zeitstempel, Tabellen-/Zeilen-/Datei-Zaehlern,
     DB-Groesse, Snapshot-Pruefsumme.
  4. Secret-Gate: alle Dump-Dateien auf passwortartige Inhalte scannen. Bei
     Treffer: NICHT committen/pushen, Fund melden (work/secret-gate-alarm.txt).
  5. Commit + Push ins private GitHub-Repo (SSH-Remote, kein Token im Git).

Zentral abschaltbar: ENABLED=0 in config/udb_backup.conf.
"""
import hashlib
import json
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/opt/entityos/udb-backup")
CONFIG_PATH = BASE / "config" / "udb_backup.conf"
WORK_DIR = BASE / "work"
REPO_DIR = BASE / "repo"
LOG_PATH = Path("/var/log/eos-udb-backup.log")

WIKI_DB = Path("/var/lib/clay/wiki.db")
SNAPSHOT_PATH = WORK_DIR / "wiki_snap.db"

GIT_REMOTE = "git@github.com:gschaidergabriel/clay-unifieddb-backup.git"
GIT_USER_NAME = "eos-udb-backup"
GIT_USER_EMAIL = "eos-udb-backup@entityos.local"

# Zielgroesse pro Dump-Chunk-Datei. GitHub blockt Pushes mit Dateien >100MB
# hart; 80MB laesst ~20% Sicherheitsabstand (Quote-Escaping etc).
CHUNK_TARGET_BYTES = 80_000_000

# -------------------------------------------------------------------------
# Secret-Gate: Muster, die auf tatsaechliche Passwoerter/Zugangsdaten
# hindeuten (nicht: Adressen/URLs/Tokens generell -- die sind laut
# Eigner-Regel ok, wiki.db ist ohnehin Wissenskorpus, kein Tresor).
# -------------------------------------------------------------------------
SECRET_PATTERNS = [
    re.compile(r"password\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"passwort\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\bpasswd\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),  # AWS access key id
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),  # GitHub tokens
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),  # Slack tokens
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),  # generic API secret key style
]

FTS_SUFFIXES = ("_data", "_idx", "_docsize", "_config", "_content")
FTS5_RE = re.compile(r"USING\s+fts5", re.IGNORECASE)


def log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}"
    print(line, flush=True)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def load_config() -> dict:
    cfg = {"ENABLED": "1"}
    if CONFIG_PATH.exists():
        for raw in CONFIG_PATH.read_text().splitlines():
            raw = raw.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            k, v = raw.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def make_snapshot() -> None:
    """Konsistenter, read-only Snapshot von wiki.db per Datei-Kopie.

    wiki.db wird NUR gelesen (shutil.copy2 = open(O_RDONLY) + read()) --
    keine Schreiboperation, kein Lock, der den Puls-Schreiber blockieren
    koennte. Reihenfolge ist bewusst wal -> shm -> db:
      - Wuerde man zuerst die db-Datei kopieren und DANACH checkpointet ein
        Schreiber die WAL (merged sie in die db, setzt die WAL zurueck),
        dann waere die anschliessend kopierte WAL leer/neu -- die Aenderungen
        waeren WEDER im (alten) db-Kopie NOCH in der (neuen, leeren) WAL-Kopie
        vorhanden. Datenverlust.
      - Kopiert man zuerst die WAL, dann die db: passiert dazwischen ein
        Checkpoint, landet dessen Inhalt im db-File, das wir SPAETER kopieren
        -- die db-Kopie ist dann sogar aktueller, und unsere (aeltere) WAL-
        Kopie enthaelt dieselben Aenderungen nochmal (idempotent beim Replay,
        gleiche Seiteninhalte). Kein Datenverlust, bestenfalls minimal
        redundante Arbeit beim Recovery.
    Anschliessend PRAGMA wal_checkpoint(TRUNCATE) NUR auf der Kopie (schreibt
    ausschliesslich in work/wiki_snap.db, niemals in /var/lib/clay/wiki.db).

    Empirisch verworfen: `sqlite3 wiki.db ".backup ..."` (Online-Backup-API).
    Unter der Dauerschreiblast dieser DB (WAL wuchs waehrend eines Tests von
    182MB auf 820MB in ~15 Minuten) geriet der Backup in einen Restart-Loop:
    0 Bytes Fortschritt bei 97% CPU ueber mehrere Minuten. Die Datei-Kopie
    hier brauchte fuer dieselbe DB (~4,3GB) ca. 13 Sekunden.
    """
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-wal", "-shm"):
        p = WORK_DIR / f"wiki_snap.db{suffix}"
        if p.exists():
            p.unlink()

    wal_src = WIKI_DB.with_name(WIKI_DB.name + "-wal")
    shm_src = WIKI_DB.with_name(WIKI_DB.name + "-shm")
    wal_dst = WORK_DIR / "wiki_snap.db-wal"
    shm_dst = WORK_DIR / "wiki_snap.db-shm"

    log(f"Snapshot start (Datei-Kopie): {WIKI_DB} -> {SNAPSHOT_PATH}")
    t0 = time.time()
    if wal_src.exists():
        shutil.copy2(wal_src, wal_dst)
    if shm_src.exists():
        shutil.copy2(shm_src, shm_dst)
    shutil.copy2(WIKI_DB, SNAPSHOT_PATH)
    dt_copy = time.time() - t0
    log(f"Datei-Kopie fertig in {dt_copy:.1f}s")

    # Checkpoint + Truncate NUR auf der Kopie -- fasst die Quelle nicht an.
    t1 = time.time()
    run(["sqlite3", str(SNAPSHOT_PATH), "PRAGMA wal_checkpoint(TRUNCATE);"])
    dt_ckpt = time.time() - t1
    log(f"Checkpoint der Kopie fertig in {dt_ckpt:.1f}s, "
        f"Groesse {SNAPSHOT_PATH.stat().st_size} Bytes")

    # Aufraeumen der (jetzt in die Kopie gemergten) WAL/SHM-Kopien.
    for p in (wal_dst, shm_dst):
        if p.exists():
            p.unlink()


def list_tables_and_fts() -> tuple[list[str], list[str], dict[str, str]]:
    """Liefert (alle_tabellen, fts5_virtuelle_tabellen, sql_je_tabelle) aus dem Snapshot."""
    out = run(
        [
            "sqlite3",
            "-json",
            str(SNAPSHOT_PATH),
            "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
        ]
    ).stdout
    rows = json.loads(out) if out.strip() else []
    tables = []
    fts_tables = []
    sql_by_name = {}
    for row in rows:
        name = row["name"]
        sql = row.get("sql") or ""
        tables.append(name)
        sql_by_name[name] = sql
        if FTS5_RE.search(sql):
            fts_tables.append(name)
    return tables, fts_tables, sql_by_name


def excluded_shadow_tables(all_tables: list[str], fts_tables: list[str]) -> set[str]:
    excluded = set()
    table_set = set(all_tables)
    for fts_name in fts_tables:
        for suffix in FTS_SUFFIXES:
            candidate = f"{fts_name}{suffix}"
            if candidate in table_set:
                excluded.add(candidate)
    return excluded


def dump_table_chunked(table: str, out_dir: Path) -> list[Path]:
    """SQL-Dump EINER Content-Tabelle per `sqlite3 .dump <table>`, gestreamt
    (kein Volltext im RAM) und in Chunks < CHUNK_TARGET_BYTES gesplittet.
    Jede erzeugte Datei ist fuer sich allein gueltiges, ausfuehrbares SQL
    (eigenes PRAGMA/BEGIN/COMMIT); nur die CREATE-TABLE/CREATE-INDEX-
    Statements landen ausschliesslich im ersten Chunk."""
    proc = subprocess.Popen(
        ["sqlite3", str(SNAPSHOT_PATH), f".dump {shlex.quote(table)}"],
        stdout=subprocess.PIPE,
        text=True,
    )

    files_written: list[Path] = []
    chunk_idx = 0
    schema_lines: list[str] = []  # CREATE TABLE/INDEX -- nur im 1. Chunk
    schema_done = False
    header = ["PRAGMA foreign_keys=OFF;\n", "BEGIN TRANSACTION;\n"]
    chunk_lines = list(header)
    chunk_bytes = sum(len(l.encode("utf-8")) for l in chunk_lines)

    def flush(final: bool) -> None:
        nonlocal chunk_lines, chunk_bytes, chunk_idx
        if len(chunk_lines) <= len(header) and not final:
            return
        chunk_lines.append("COMMIT;\n")
        path = out_dir / f"{table}.{chunk_idx:03d}.sql"
        path.write_text("".join(chunk_lines))
        files_written.append(path)
        chunk_idx += 1
        chunk_lines = list(header)
        chunk_bytes = sum(len(l.encode("utf-8")) for l in chunk_lines)

    assert proc.stdout is not None
    for line in proc.stdout:
        if line.startswith("PRAGMA foreign_keys=OFF;") or line.startswith("BEGIN TRANSACTION;"):
            continue
        if line.startswith("COMMIT;"):
            continue
        if not schema_done and (line.startswith("CREATE TABLE") or line.startswith("CREATE INDEX") or line.startswith("CREATE UNIQUE INDEX")):
            schema_lines.append(line)
            chunk_lines.append(line)
            chunk_bytes += len(line.encode("utf-8"))
            continue
        schema_done = True  # erste INSERT-Zeile gesehen -> Schema-Teil vorbei
        line_bytes = len(line.encode("utf-8"))
        if chunk_bytes + line_bytes > CHUNK_TARGET_BYTES and len(chunk_lines) > len(header):
            flush(final=False)
        chunk_lines.append(line)
        chunk_bytes += line_bytes

    flush(final=True)
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"sqlite3 .dump fehlgeschlagen fuer Tabelle {table} (rc={proc.returncode})")
    return files_written


def write_fts5_schema_file(fts_tables: list[str], sql_by_name: dict, out_dir: Path) -> Path | None:
    if not fts_tables:
        return None
    lines = [
        "-- FTS5-Volltextindex-Schema (nur die CREATE VIRTUAL TABLE-Definition).\n",
        "-- Schattentabellen (_data/_idx/_docsize/_config/_content) sind bewusst\n",
        "-- NICHT enthalten -- riesig, regenerierbar. Nach dem Restore je Tabelle:\n",
        "--   INSERT INTO <name>(<name>) VALUES('rebuild');\n",
        "-- siehe RESTORE.md.\n\n",
    ]
    for name in fts_tables:
        sql = sql_by_name.get(name, "").rstrip()
        if sql:
            lines.append(f"{sql};\n")
    path = out_dir / "_fts5_schema.sql"
    path.write_text("".join(lines))
    return path


def secret_scan(files: list[Path]) -> list[str]:
    findings = []
    for path in files:
        with path.open("r", errors="replace") as fh:
            for lineno, line in enumerate(fh, 1):
                for pat in SECRET_PATTERNS:
                    if pat.search(line):
                        findings.append(f"{path.name}:{lineno}: Muster '{pat.pattern}' getroffen")
                        break
    return findings


def table_counts(tables: list[str]) -> dict:
    counts = {}
    for t in tables:
        try:
            out = run(
                ["sqlite3", str(SNAPSHOT_PATH), f"SELECT COUNT(*) FROM {shlex.quote(t)};"]
            ).stdout.strip()
            counts[t] = int(out)
        except Exception as exc:
            counts[t] = f"error: {exc}"
    return counts


def ensure_repo() -> None:
    if not (REPO_DIR / ".git").exists():
        REPO_DIR.parent.mkdir(parents=True, exist_ok=True)
        log(f"Klone Backup-Repo nach {REPO_DIR}")
        run(["git", "clone", GIT_REMOTE, str(REPO_DIR)])
        run(["git", "-C", str(REPO_DIR), "config", "user.name", GIT_USER_NAME])
        run(["git", "-C", str(REPO_DIR), "config", "user.email", GIT_USER_EMAIL])
    else:
        run(["git", "-C", str(REPO_DIR), "pull", "--ff-only"])


def main() -> int:
    cfg = load_config()
    if cfg.get("ENABLED", "1") != "1":
        log("uebersprungen (ENABLED=0 in config/udb_backup.conf)")
        return 0

    if not WIKI_DB.exists():
        log(f"FEHLER: {WIKI_DB} nicht gefunden, breche ab")
        return 1

    make_snapshot()
    snap_size = SNAPSHOT_PATH.stat().st_size
    snap_sha = sha256_file(SNAPSHOT_PATH)
    log(f"Snapshot sha256 {snap_sha}")

    all_tables, fts_tables, sql_by_name = list_tables_and_fts()
    shadow_excl = excluded_shadow_tables(all_tables, fts_tables)
    content_tables = [t for t in all_tables if t not in shadow_excl and t not in fts_tables]
    log(f"Tabellen gesamt {len(all_tables)}, FTS5-virtuell {len(fts_tables)}, "
        f"ausgeschlossene Schattentabellen {len(shadow_excl)} ({sorted(shadow_excl)}), "
        f"Content-Tabellen mit Volldaten {len(content_tables)}")

    dump_dir = WORK_DIR / "dump"
    if dump_dir.exists():
        shutil.rmtree(dump_dir)
    dump_dir.mkdir(parents=True)

    all_dump_files: list[Path] = []
    per_table_files: dict[str, int] = {}
    t0 = time.time()
    for t in content_tables:
        files = dump_table_chunked(t, dump_dir)
        all_dump_files.extend(files)
        per_table_files[t] = len(files)
    fts_schema_file = write_fts5_schema_file(fts_tables, sql_by_name, dump_dir)
    if fts_schema_file:
        all_dump_files.append(fts_schema_file)
    dt_dump = time.time() - t0
    dump_total_bytes = sum(p.stat().st_size for p in all_dump_files)
    log(f"Dump geschrieben: {len(all_dump_files)} Dateien, {dump_total_bytes} Bytes gesamt, "
        f"{dt_dump:.1f}s")

    findings = secret_scan(all_dump_files)
    if findings:
        alarm_path = WORK_DIR / "secret-gate-alarm.txt"
        alarm_path.write_text(
            "SECRET-GATE ALARM -- Push GESTOPPT.\n"
            f"Zeitpunkt: {datetime.now(timezone.utc).isoformat()}\n"
            f"Anzahl Treffer: {len(findings)}\n\n" + "\n".join(findings[:200])
        )
        log(f"SECRET-GATE ALARM: {len(findings)} Treffer, Push GESTOPPT. Details: {alarm_path}")
        return 2

    counts = table_counts(content_tables)
    n_artikel = counts.get("artikel")
    n_kante = counts.get("kante")

    ensure_repo()

    ts = datetime.now(timezone.utc)
    manifest = {
        "timestamp_utc": ts.isoformat(timespec="seconds"),
        "source_db": str(WIKI_DB),
        "source_db_size_bytes": WIKI_DB.stat().st_size,
        "snapshot_method": "filesystem-copy (wal,shm,db) + checkpoint(TRUNCATE) auf der Kopie",
        "snapshot_sha256": snap_sha,
        "snapshot_size_bytes": snap_size,
        "dump_total_bytes": dump_total_bytes,
        "dump_file_count": len(all_dump_files),
        "chunk_target_bytes": CHUNK_TARGET_BYTES,
        "table_count_total": len(all_tables),
        "content_table_count": len(content_tables),
        "fts5_virtual_tables": sorted(fts_tables),
        "excluded_fts_shadow_tables": sorted(shadow_excl),
        "files_per_table": per_table_files,
        "row_counts": counts,
        "artikel_count": n_artikel,
        "kante_count": n_kante,
        "secret_gate": "clean",
    }

    (REPO_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=False) + "\n")

    repo_dump_dir = REPO_DIR / "dump"
    if repo_dump_dir.exists():
        shutil.rmtree(repo_dump_dir)
    shutil.copytree(dump_dir, repo_dump_dir)

    restore_md = REPO_DIR / "RESTORE.md"
    if not restore_md.exists():
        restore_md.write_text(RESTORE_MD_CONTENT)

    run(["git", "-C", str(REPO_DIR), "add", "-A", "manifest.json", "dump", "RESTORE.md"])

    status = run(["git", "-C", str(REPO_DIR), "status", "--porcelain"]).stdout.strip()
    if not status:
        log("keine Aenderungen seit dem letzten Backup -- kein neuer Commit")
        return 0

    commit_msg = (
        f"Backup {ts.strftime('%Y-%m-%d %H:%M UTC')} -- "
        f"{len(content_tables)} Content-Tabellen, {n_artikel} Artikel, {n_kante} Kanten, "
        f"{len(all_dump_files)} Dump-Dateien ({dump_total_bytes} Bytes), "
        f"Snapshot-SHA256 {snap_sha[:12]}..."
    )
    run(["git", "-C", str(REPO_DIR), "commit", "-m", commit_msg])
    commit_hash = run(["git", "-C", str(REPO_DIR), "rev-parse", "HEAD"]).stdout.strip()
    run(["git", "-C", str(REPO_DIR), "push", "origin", "HEAD"])
    log(f"Push ok, Commit {commit_hash}")

    # Aufraeumen der lokalen Snapshot-Arbeitsdatei (nicht das Repo).
    try:
        SNAPSHOT_PATH.unlink(missing_ok=True)
    except Exception:
        pass

    return 0


RESTORE_MD_CONTENT = """# Restore -- clay-unifieddb-backup

Dieses Repo enthaelt einen versionierten SQL-Dump der EntityOS-Herz-DB
`wiki.db` (Clay/Frank Unified-Datenbank, Artikel/Kanten/Retrieval-Korpus).

## Was drin ist

- `dump/<tabelle>.<NNN>.sql` -- SQL-Dump ALLER Inhalts-/Content-Tabellen
  (artikel, artikel_suchtext, datei, kante, folgerung, wm_*, vp_* usw.),
  als `sqlite3 .dump` im diffbaren SQL-Textformat. Pro Tabelle mindestens
  eine Datei; sehr grosse Tabellen (allen voran `datei`, >2GB Volltext)
  sind in mehrere `.000.sql`, `.001.sql`, ... Chunks gesplittet, damit
  keine einzelne Datei GitHubs 100-MB-Limit reisst. JEDE Datei ist fuer
  sich allein gueltiges SQL; beim Restore einfach ALLE Dateien in
  alphabetischer Reihenfolge anwenden (die Nummerierung sorgt dafuer, dass
  CREATE TABLE vor den zugehoerigen INSERTs kommt).
- `dump/_fts5_schema.sql` -- nur die `CREATE VIRTUAL TABLE ... USING
  fts5(...)`-Definitionen (Schema, keine Daten).
- `manifest.json` -- Metadaten je Backup: Zeitstempel, Tabellenzahl,
  Zeilenzaehler (u.a. Artikel-/Kantenzahl), Dateizahl, Snapshot-Groesse/
  Pruefsumme, Snapshot-Methode.

## Was FEHLT (bewusst)

Die FTS5-Volltextsuche-Schattentabellen (`<name>_data`, `_idx`, `_docsize`,
`_config`, `_content`) sind ausgeschlossen -- sie sind reiner Suchindex-
Binaermuell, riesig, nicht diffbar und vollstaendig REGENERIERBAR aus den
Content-Tabellen.

## Restore-Schritte

```bash
# 1. Neue leere DB aus den Dump-Dateien aufbauen (Reihenfolge wichtig:
#    alphabetisch sortiert kommt CREATE TABLE vor den INSERTs derselben
#    Tabelle; Reihenfolge zwischen verschiedenen Tabellen ist egal, es
#    gibt keine FK-Constraints die beim Restore durchgesetzt werden).
for f in dump/*.sql; do
  sqlite3 restored.db < "$f"
done

# 2. FTS5-Indizes neu aufbauen (siehe dump/_fts5_schema.sql wird durch
#    obige Schleife schon angelegt; jetzt befuellen):
sqlite3 restored.db "INSERT INTO fts_index_artikel(fts_index_artikel) VALUES('rebuild');"
sqlite3 restored.db "INSERT INTO fts_index_datei(fts_index_datei) VALUES('rebuild');"
sqlite3 restored.db "INSERT INTO vp_alias_fts(vp_alias_fts) VALUES('rebuild');"
sqlite3 restored.db "INSERT INTO vp_datei_fts(vp_datei_fts) VALUES('rebuild');"
sqlite3 restored.db "INSERT INTO vp_dir_fts(vp_dir_fts) VALUES('rebuild');"
# (exakte Liste der FTS5-Tabellen je Backup: manifest.json -> fts5_virtual_tables)

# 3. Pruefen (Zahlen mit manifest.json -> row_counts vergleichen)
sqlite3 restored.db "SELECT COUNT(*) FROM artikel;"
sqlite3 restored.db "SELECT COUNT(*) FROM kante;"
```

## Warum roher SQL-Text statt gzip

Bewusste Entscheidung: roh und diffbar, NICHT gzip-komprimiert. Begruendung
im Backup-Report/Commit-Historie: bei taeglichen Snapshots ist der grosse
Teil des Inhalts von einem Tag zum naechsten UNVERAENDERT. Git speichert
Commits als Deltas/Packfiles -- unveraenderte Zeilen (der grosse Teil bei
Text) werden ueber Commits hinweg praktisch kostenlos, weil sie deduplizierbar
sind. Ein vorab gzip-komprimierter Dump wuerde bei JEDER kleinsten Aenderung
einen komplett neuen, undiffbaren Binaerblob erzeugen -- das zerstoert genau
die Versionshistorie-Eigenschaft, die ein taegliches Backup wertvoll macht.
Der Preis: der initiale Commit ist gross (mehrere GB, dominiert von der
`datei`-Volltexttabelle). Das ist ein bewusster, dokumentierter Tradeoff --
kein Uebersehen.

Kein Passwort-/Tresorinhalt in diesem Repo (Secret-Gate scannt jede
Dump-Datei vor dem Push; der Tresor liegt separat in /etc/entityos/tresor
und wird hier nicht gesichert).
"""


if __name__ == "__main__":
    if "--run" not in sys.argv:
        print("Nutzung: udb_backup.py --run", file=sys.stderr)
        sys.exit(1)
    sys.exit(main())
