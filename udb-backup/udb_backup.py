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
import os
import re
import shlex
import sqlite3
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/opt/entityos/udb-backup")
CONFIG_PATH = BASE / "config" / "udb_backup.conf"
WORK_DIR = BASE / "work"
LOG_PATH = Path("/var/log/eos-udb-backup.log")

WIKI_DB = Path("/var/lib/clay/wiki.db")
SNAPSHOT_PATH = WORK_DIR / "wiki_snap.db"


# Zielgroesse pro Dump-Chunk-Datei. GitHub blockt Pushes mit Dateien >100MB
# hart; 80MB laesst ~20% Sicherheitsabstand (Quote-Escaping etc).
CHUNK_TARGET_BYTES = 80_000_000

# -------------------------------------------------------------------------
# Secret-Gate: Muster, die auf tatsaechliche Passwoerter/Zugangsdaten
# hindeuten (nicht: Adressen/URLs/Tokens generell -- die sind laut
# Eigner-Regel ok, wiki.db ist ohnehin Wissenskorpus, kein Tresor).
#
# Lektion aus dem ersten Testlauf (2026-08-19): die Herz-DB enthaelt in der
# `datei`-Tabelle jede Menge indizierten QUELLCODE/DOKUMENTATION -- u.a.
# Security-Scanner-Tools und SDK-Testfixtures, die selbst Muster wie
# "password = ..." oder "-----BEGIN PRIVATE KEY-----" als REGEX-LITERALE
# oder Test-Dummy-Daten enthalten. Ein naives "Wort 'password' kommt vor"
# ergab 2190 Treffer, praktisch alle falsch positiv (Codeidentifier wie
# `password: str`, `password=self.password`, Testfixtures aus dem WHATWG-
# URL-Testsuite etc). Deshalb hier bewusst PRAEZISER:
#   - Passwort-Muster nur bei einem QUOTIERTEN Literal mit Mindestlaenge/
#     -entropie (kein `None`/`str`/Variablenreferenz).
#   - Private-Key nur bei BEGIN...END-PAAR mit substanziellem Inhalt
#     dazwischen (reine Regex-Literale wie in Scanner-Tools haben kein
#     zugehoeriges END mit Base64-Koerper in derselben Zeile).
# -------------------------------------------------------------------------
_NON_SECRET_RHS = re.compile(
    r"^(none|null|str|string|''|\"\"|self\.|os\.environ|process\.env|"
    r"\$\{|config\.|cred(ential)?s?[.\[]|auth[.\[]|entry\[|options\.|"
    r"password|passwort|passwd|pw_match|lexer\.|mbox\.|request_data|"
    r"parts\[|content\.|val\\|password\.encode|password or |page\.pdf)",
    re.IGNORECASE,
)

SECRET_PATTERNS = [
    # quotiertes Passwort-Literal, Mindestlaenge 6, kein offensichtlicher
    # Code-Verweis auf der rechten Seite.
    re.compile(
        r"(?:password|passwort|passwd)\s*[:=]\s*['\"]([^'\"]{6,})['\"]",
        re.IGNORECASE,
    ),
    # BEGIN...END-Paar mit substanziellem (Base64-artigem) Inhalt dazwischen
    # -- reine Regex-Pattern-Literale (kein Koerper) fallen NICHT darunter.
    re.compile(
        r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"
        r"[A-Za-z0-9+/=\\ntr]{200,}"
        r"-----END (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"
    ),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),  # AWS access key id (immer melden)
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),  # GitHub tokens (literal, kein ${..})
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),  # Slack tokens
]


# Weltweit bekannte, offiziell in AWS-eigener Dokumentation verwendete
# Platzhalter-Zugangsschluessel-ID -- kein echtes Geheimnis, wird auch von
# gitleaks/truffleHog standardmaessig ignoriert.
_KNOWN_PLACEHOLDER_VALUES = {"AKIAIOSFODNN7EXAMPLE"}

# Zeilen mit diesen Markern sind (fast) immer Test-/Beispielcode fuer
# Secret-Scanner selbst -- die `datei`-Tabelle enthaelt u.a. die komplette
# Testsuite eines selbst gebauten Scanners (`scanner-*.test.ts` etc), die
# absichtlich Fake-Secrets als Testfaelle einbettet, um zu pruefen, ob der
# Scanner sie erkennt. Das ist der Sinn des Tests, kein echtes Leck.
_TEST_FIXTURE_MARKERS = re.compile(
    r"\b(it\(|test\(|describe\(|expect\(|scanCode\(|scanIssues\(|assert|"
    r"EXAMPLE|dummy|fixture|placeholder|hardcoded)",
    re.IGNORECASE,
)


def _looks_like_real_secret(match: re.Match, line: str) -> bool:
    """Zusatzfilter: verwirft die offensichtlichsten Code-/Platzhalter-
    Treffer (Variablenverweise, Typannotationen, bekannte Dummy-Werte,
    Zeilen aus Scanner-Testsuiten, die absichtlich Fake-Secrets testen)."""
    if match.lastindex and match.group(1) is not None:
        rhs = match.group(1)
        if _NON_SECRET_RHS.match(rhs):
            return False
        if rhs in _KNOWN_PLACEHOLDER_VALUES:
            return False
    else:
        matched_text = match.group(0)
        for val in _KNOWN_PLACEHOLDER_VALUES:
            if val in matched_text:
                return False
    if _TEST_FIXTURE_MARKERS.search(line):
        return False
    return True

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


# ── Redigierte Spalten: was NICHT nach GitHub faehrt ──────────────────────
# Siehe Modul-Kopf. Tabelle -> Spalten, die als NULL gedumpt werden. Die Zeile
# selbst bleibt vollstaendig erhalten, nur dieses eine Feld ist leer.
REDIGIERTE_SPALTEN: dict[str, tuple[str, ...]] = {
    "datei": ("text",),
}


def _schema_zeilen(table: str) -> list[str]:
    """CREATE TABLE/INDEX dieser Tabelle aus dem Schnappschuss."""
    con = sqlite3.connect(f"file:{SNAPSHOT_PATH}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT sql FROM sqlite_master WHERE tbl_name=? AND sql IS NOT NULL "
            "AND type IN ('table','index') ORDER BY (type='table') DESC",
            (table,),
        ).fetchall()
    finally:
        con.close()
    return [r[0].rstrip().rstrip(";") + ";\n" for r in rows]


def _redigierte_auswahl(table: str, spalten: tuple[str, ...]) -> str:
    """SELECT mit den redigierten Spalten als NULL, Spaltenreihenfolge intakt.

    Reihenfolge ist Pflicht: die erzeugten INSERTs nennen keine Spaltennamen,
    ein Vertauschen wuerde die Werte still in falsche Spalten schreiben.
    """
    con = sqlite3.connect(f"file:{SNAPSHOT_PATH}?mode=ro", uri=True)
    try:
        namen = [r[1] for r in con.execute(f"PRAGMA table_info({table})")]
    finally:
        con.close()
    if not namen:
        raise RuntimeError(f"Tabelle {table} hat keine Spalten -- Schnappschuss kaputt?")
    fehlend = [sp for sp in spalten if sp not in namen]
    if fehlend:
        # Lieber laut scheitern als still ungeschwaerzt pushen.
        raise RuntimeError(
            f"REDIGIERTE_SPALTEN nennt fuer {table} die Spalte(n) {fehlend}, "
            f"die es dort nicht (mehr) gibt: {namen}"
        )
    felder = ", ".join(("NULL" if n in spalten else f'"{n}"') for n in namen)
    return f'SELECT {felder} FROM "{table}";'


def dump_table_chunked(table: str, out_dir: Path) -> list[Path]:
    """SQL-Dump EINER Content-Tabelle per `sqlite3 .dump <table>`, gestreamt
    (kein Volltext im RAM) und in Chunks < CHUNK_TARGET_BYTES gesplittet.
    Jede erzeugte Datei ist fuer sich allein gueltiges, ausfuehrbares SQL
    (eigenes PRAGMA/BEGIN/COMMIT); nur die CREATE-TABLE/CREATE-INDEX-
    Statements landen ausschliesslich im ersten Chunk."""
    redigiert = REDIGIERTE_SPALTEN.get(table)
    if redigiert:
        # `.dump` kann keine Spalte auslassen -- also INSERTs aus einem SELECT
        # erzeugen (.mode insert), Schema separat voranstellen. Gestreamt wie
        # der normale Weg, kein Volltext im RAM.
        proc = subprocess.Popen(
            ["sqlite3", str(SNAPSHOT_PATH),
             "-cmd", f".mode insert {table}",
             _redigierte_auswahl(table, redigiert)],
            stdout=subprocess.PIPE,
            text=True,
        )
    else:
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
    if redigiert:
        for z in _schema_zeilen(table):
            schema_lines.append(z)
            chunk_lines.append(z)
        schema_done = True   # ab hier kommen nur noch INSERTs
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
                    m = pat.search(line)
                    if m and _looks_like_real_secret(m, line):
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


# ── Ziel des Backups: der zweite VPS (Gabriel 2026-08-20) ────────────────
# Dasselbe Ziel und dasselbe Verfahren wie /opt/entityos/homepage-backup.sh.
BACKUP_ZIEL = "root@72.61.19.188"
BACKUP_DEST = "/srv/unifieddb-backups"
SSH_OPTS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]
# Eine feste, bedeutungslose Zeit fuer alle Dump-Dateien (2000-01-01 UTC).
# Der echte Zeitpunkt steht im Ordnernamen und in manifest.json.
FESTE_ZEIT = 946684800


def push_to_vps(dump_dir: Path, stamp: str) -> bool:
    """Datierten Schnappschuss auf den zweiten VPS legen. Zerstoerungsfrei.

    KEIN --delete und kein rm: nichts auf dem Ziel wird geloescht, auch nicht
    ein alter Schnappschuss. `--link-dest=../latest` verlinkt unveraenderte
    Dateien hart, ein Schnappschuss kostet also nur den Zuwachs. `latest`
    haengt per `ln -sfn` um -- atomar und ohne Loeschen.
    """
    ssh = "ssh " + " ".join(SSH_OPTS)
    # Feste Zeit auf allen Dateien -- siehe Modul-Historie 2026-08-20. Ohne das
    # verlinkt --link-dest nichts, weil jeder frisch geschriebene Dump eine neue
    # Aenderungszeit traegt.
    for datei in sorted(dump_dir.rglob("*")):
        if datei.is_file():
            os.utime(datei, (FESTE_ZEIT, FESTE_ZEIT))
    try:
        run(["ssh", *SSH_OPTS, BACKUP_ZIEL, f"mkdir -p {BACKUP_DEST}"])
        run([
            # --checksum ist hier PFLICHT, nicht Feinschliff: ohne ihn
            # vergleicht rsync Groesse+Zeit, und die Zeit ist bei einem frisch
            # geschriebenen Dump immer neu -- --link-dest greift dann NIE
            # (gemessen 2026-08-20: 0 von 108 Dateien verlinkt, zwei
            # Schnappschuesse kosteten volle 977 MB statt 489 MB + Zuwachs).
            "rsync", "-a", "--checksum", "--link-dest=../latest", "-e", ssh,
            str(dump_dir).rstrip("/") + "/",
            f"{BACKUP_ZIEL}:{BACKUP_DEST}/{stamp}/",
        ])
        # Erst NACH erfolgreicher Uebertragung umhaengen: ein halb
        # uebertragener Schnappschuss darf nie `latest` heissen -- und er waere
        # sonst auch die --link-dest-Grundlage des naechsten Laufs.
        run(["ssh", *SSH_OPTS, BACKUP_ZIEL,
             f"ln -sfn '{stamp}' {BACKUP_DEST}/latest"])
        return True
    except subprocess.CalledProcessError as fehler:
        log(f"rsync/ssh fehlgeschlagen: rc={fehler.returncode} "
            f"stderr={(fehler.stderr or '')[:400]}")
        return False


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

    ts = datetime.now(timezone.utc)
    stamp = ts.strftime("%Y-%m-%d_%H%M")
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
        "redacted_columns": {t: list(c) for t, c in REDIGIERTE_SPALTEN.items()},
        "files_per_table": per_table_files,
        "row_counts": counts,
        "artikel_count": n_artikel,
        "kante_count": n_kante,
        "secret_gate": "clean",
        "ziel": f"{BACKUP_ZIEL}:{BACKUP_DEST}/{stamp}",
    }
    (WORK_DIR / "dump" / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=False) + "\n")
    (WORK_DIR / "dump" / "RESTORE.md").write_text(RESTORE_MD_CONTENT)

    ok = push_to_vps(WORK_DIR / "dump", stamp)
    if not ok:
        log("FEHLER: Uebertragung auf den zweiten VPS fehlgeschlagen")
        return 3
    log(f"Backup abgelegt: {BACKUP_ZIEL}:{BACKUP_DEST}/{stamp} "
        f"({len(all_dump_files)} Dateien, {dump_total_bytes} Bytes, "
        f"{n_artikel} Artikel, {n_kante} Kanten, Snapshot {snap_sha[:12]})")

    # Aufraeumen der lokalen Snapshot-Arbeitsdatei (nicht das Repo).
    try:
        SNAPSHOT_PATH.unlink(missing_ok=True)
    except Exception:
        pass

    return 0


RESTORE_MD_CONTENT = """# Restore -- UnifiedDB-Backup

Dieser Ordner ist EIN datierter Schnappschuss der EntityOS-Herz-DB
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

## Wo das liegt

Ziel ist der zweite VPS: `root@72.61.19.188:/srv/unifieddb-backups/<STAMP>/`,
`latest` zeigt auf den neuesten. Unveraenderte Dump-Dateien sind zwischen den
Schnappschuessen HART VERLINKT -- ein Schnappschuss kostet nur den Zuwachs.
Es wird nie etwas geloescht; alte Schnappschuesse raeumt ein Mensch weg.

## Was FEHLT (bewusst, zweiter Punkt)

Die Spalte `datei.text` -- der Volltext von rund 325.000 indizierten Dateien --
wird als NULL gesichert. Sie enthielt echte fremde Zugangsdaten (gemessen
2026-08-20: 15 AWS-Schluessel, ein GitHub-Token, zwei Slack-Token, ein privater
Schluessel) und ist als einziges Feld der ganzen DB aus der Platte NEU
HERSTELLBAR -- genau so ist sie hineingekommen. Der Dateiindex selbst
(Pruefsumme, Titel, Groesse, Zeitpunkt) ist vollstaendig gesichert.
Ein Rueckspielen liefert also den Dateikorpus ohne Volltext; die Volltextsuche
muss danach neu indiziert werden.

## Warum roher SQL-Text statt gzip

Bewusste Entscheidung: roh und unveraendert, NICHT gzip-komprimiert. Begruendung
im Backup-Report/Commit-Historie: bei taeglichen Snapshots ist der grosse
Teil des Inhalts von einem Tag zum naechsten UNVERAENDERT. rsync verlinkt eine
unveraenderte Datei hart in den neuen Schnappschuss -- sie kostet dann null
Bytes. Ein vorab gzip-komprimierter Dump waere bei JEDER kleinsten Aenderung
eine komplett neue Datei und muesste jedes Mal ganz neu abgelegt werden --
genau die Eigenschaft, die taegliche Schnappschuesse bezahlbar macht, waere
damit weg. (Vorher stand hier dieselbe Begruendung ueber Git-Packfiles; das
Argument traegt unveraendert, nur der Mechanismus heisst jetzt Hardlink.)
Der Preis: der initiale Commit ist gross (mehrere GB, dominiert von der
`datei`-Volltexttabelle). Das ist ein bewusster, dokumentierter Tradeoff --
kein Uebersehen.

Kein Passwort-/Tresorinhalt in diesem Backup (Secret-Gate scannt jede
Dump-Datei vor der Uebertragung; der Tresor liegt separat in /etc/entityos/tresor
und wird hier nicht gesichert).
"""


if __name__ == "__main__":
    if "--run" not in sys.argv:
        print("Nutzung: udb_backup.py --run", file=sys.stderr)
        sys.exit(1)
    sys.exit(main())
