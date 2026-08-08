#!/usr/bin/env python3
"""Repo-native RAE research-room helper.

No daemon, socket or external room service is required. The repository is the
coordination substrate. Repository-based workers commit/push generated records;
connector-only workers perform equivalent GitHub create/update/CAS operations.

Hot coordination avoids one shared append-only file: immutable events use unique
files, while worker/cursor/lease/state records are materialized operational views.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
ROOMS_ROOT = ROOT / "research_entity" / "rooms"
REGISTRY_PATH = ROOMS_ROOT / "ROOM_REGISTRY.json"
ROOM_DIR = ROOMS_ROOT / "rooms"
CENTER_EVENTS = ROOMS_ROOT / "center_events"
ROLE_ORDER = ["CHEF", "ABYSS", "FORGE", "CARTOGRAPHER", "REPLICATOR", "SYNTHESIZER"]
DELIVERY = ["INTERRUPT_NEXT_SAFE_POINT", "NEXT_CHECKPOINT", "INDEX_ONLY"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp-{uuid.uuid4().hex}")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def create_json_exclusive(path: Path, data: Any) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    return True


def new_id(prefix: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{prefix}-{stamp}-{uuid.uuid4().hex[:8]}"


def registry() -> dict[str, Any]:
    data = read_json(REGISTRY_PATH)
    if not data:
        raise SystemExit(f"missing room registry: {REGISTRY_PATH}")
    return data


def all_room_config() -> dict[str, Any]:
    reg = registry()
    merged = dict(reg.get("rooms", {}))
    merged.update(reg.get("meta_rooms", {}))
    return merged


def room_for_trigger(trigger: str) -> str:
    trigger = trigger.strip().lower()
    reg = registry()
    for room_id, cfg in reg.get("rooms", {}).items():
        if cfg.get("trigger") == trigger:
            return room_id
    for room_id, cfg in reg.get("meta_rooms", {}).items():
        if trigger in cfg.get("triggers", []):
            return room_id
    raise SystemExit(f"unregistered trigger for research room: {trigger}")


def room_path(room_id: str) -> Path:
    return ROOM_DIR / room_id


def ensure_room(room_id: str) -> Path:
    cfgs = all_room_config()
    if room_id not in cfgs:
        raise SystemExit(f"unknown room: {room_id}")
    base = room_path(room_id)
    for rel in [
        "workers", "events", "tasks", "leases/roles", "leases/tasks", "cursors",
        "mailboxes", "challenges", "team_epochs", "state"
    ]:
        (base / rel).mkdir(parents=True, exist_ok=True)
    CENTER_EVENTS.mkdir(parents=True, exist_ok=True)
    room_file = base / "ROOM.json"
    if not room_file.exists():
        write_json(room_file, {
            "schema_version": "1.0",
            "room_id": room_id,
            "created_at": now(),
            "config": cfgs[room_id],
            "protocol": "research_entity/global/REPO_NATIVE_RESEARCH_CENTER_PROTOCOL.md",
            "persistent_chief": False,
        })
    return base


def worker_records(room_id: str) -> list[dict[str, Any]]:
    base = ensure_room(room_id)
    out: list[dict[str, Any]] = []
    for path in sorted((base / "workers").glob("*.json")):
        data = read_json(path)
        if data:
            out.append(data)
    return out


def active_workers(room_id: str, stale_minutes: int = 45) -> list[dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=stale_minutes)
    out: list[dict[str, Any]] = []
    for w in worker_records(room_id):
        if w.get("status") not in {"ACTIVE", "WAITING"}:
            continue
        try:
            pulse = parse_time(w.get("last_pulse_at") or w.get("joined_at"))
        except Exception:
            continue
        if pulse >= cutoff:
            out.append(w)
    return out


def index_cross_room_event(event: dict[str, Any]) -> None:
    targets = [r for r in event.get("affects_rooms", []) if r and r != event.get("room_id")]
    if not targets:
        return
    CENTER_EVENTS.mkdir(parents=True, exist_ok=True)
    ref = {
        "schema_version": "1.0",
        "event_id": event["event_id"],
        "origin_room": event["room_id"],
        "origin_worker": event["origin_worker"],
        "created_at": event["created_at"],
        "target_rooms": targets,
        "delivery": event["delivery"],
        "event_ref": f"research_entity/rooms/rooms/{event['room_id']}/events/{event['event_id']}.json",
        "affects_claims": event.get("affects_claims", []),
        "dependencies": event.get("dependencies", []),
        "artifact_refs": event.get("artifact_refs", []),
        "ancestry_family": event.get("ancestry_family", "UNKNOWN"),
    }
    create_json_exclusive(CENTER_EVENTS / f"{event['event_id']}.json", ref)

    # Best-effort lightweight mailboxes for workers currently visible in target rooms.
    # Future workers still discover the center-event index even if no mailbox existed yet.
    for room_id in targets:
        if room_id not in all_room_config():
            continue
        target_base = ensure_room(room_id)
        for w in active_workers(room_id):
            worker_id = w.get("worker_session_id")
            if not worker_id:
                continue
            mailbox = {
                "schema_version": "1.0",
                "worker_session_id": worker_id,
                "room_id": room_id,
                "event_id": event["event_id"],
                "delivery": event["delivery"],
                "event_ref": ref["event_ref"],
                "created_at": now(),
            }
            create_json_exclusive(target_base / "mailboxes" / worker_id / f"{event['event_id']}.json", mailbox)


def emit_event(room_id: str, worker: str, actor: str, trigger: str, event_type: str,
               canonical_revision: int, canonical_hash: str, payload: dict[str, Any] | None = None,
               affects_rooms: Iterable[str] = (), affects_claims: Iterable[str] = (),
               dependencies: Iterable[str] = (), artifact_refs: Iterable[str] = (),
               ancestry_family: str = "UNKNOWN", delivery: str = "NEXT_CHECKPOINT") -> dict[str, Any]:
    base = ensure_room(room_id)
    event_id = new_id("evt")
    event = {
        "schema_version": "1.0",
        "event_id": event_id,
        "room_id": room_id,
        "event_type": event_type,
        "origin_worker": worker,
        "origin_actor": actor,
        "trigger": trigger,
        "created_at": now(),
        "canonical_parent": {"revision": canonical_revision, "state_hash": canonical_hash},
        "affects_rooms": list(dict.fromkeys(affects_rooms)),
        "affects_claims": list(dict.fromkeys(affects_claims)),
        "dependencies": list(dict.fromkeys(dependencies)),
        "artifact_refs": list(dict.fromkeys(artifact_refs)),
        "ancestry_family": ancestry_family,
        "delivery": delivery,
        "payload": payload or {},
    }
    path = base / "events" / f"{event_id}.json"
    if not create_json_exclusive(path, event):
        raise RuntimeError("event id collision")
    index_cross_room_event(event)
    return event


def role_lease_path(room_id: str, role: str) -> Path:
    return ensure_room(room_id) / "leases" / "roles" / f"{role}.json"


def lease_active(lease: dict[str, Any] | None) -> bool:
    if not lease or lease.get("status") != "ACTIVE":
        return False
    try:
        return parse_time(lease["expires_at"]) > datetime.now(timezone.utc)
    except Exception:
        return False


def try_claim_role(room_id: str, worker: str, role: str, team_epoch: str, minutes: int = 45) -> tuple[bool, dict[str, Any] | None]:
    role = role.upper()
    if role not in ROLE_ORDER:
        raise SystemExit(f"unknown role {role}; expected one of {ROLE_ORDER}")
    path = role_lease_path(room_id, role)
    current = read_json(path)
    if lease_active(current):
        return current.get("holder_worker") == worker, current
    lease = {
        "schema_version": "1.0",
        "lease_type": "ROLE",
        "room_id": room_id,
        "subject_id": role,
        "holder_worker": worker,
        "team_epoch_id": team_epoch,
        "issued_at": now(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z"),
        "status": "ACTIVE",
        "truth_authority": False,
    }
    if not path.exists():
        if create_json_exclusive(path, lease):
            return True, lease
        return False, read_json(path)
    lease["supersedes_holder"] = current.get("holder_worker") if current else None
    lease["supersedes_expires_at"] = current.get("expires_at") if current else None
    # Local atomic replacement. A remote concurrent replacement still requires Git/CAS.
    write_json(path, lease)
    return True, lease


def current_team_epoch(room_id: str) -> str | None:
    chef = read_json(role_lease_path(room_id, "CHEF"))
    if lease_active(chef):
        return chef.get("team_epoch_id")
    return None


def choose_role(room_id: str, worker: str, team_epoch: str) -> dict[str, Any]:
    n = max(1, len(active_workers(room_id)))
    preferred = {
        1: ["CHEF"],
        2: ["CHEF", "ABYSS", "FORGE"],
        3: ["CHEF", "ABYSS", "FORGE"],
        4: ["CHEF", "ABYSS", "FORGE", "CARTOGRAPHER"],
        5: ["CHEF", "ABYSS", "FORGE", "CARTOGRAPHER", "REPLICATOR"],
    }.get(n, ROLE_ORDER)
    for role in preferred + [r for r in ROLE_ORDER if r not in preferred]:
        ok, lease = try_claim_role(room_id, worker, role, team_epoch)
        if ok and lease:
            return lease
    raise SystemExit("no role could be claimed")


def events_after(paths: list[Path], last_seen: str | None, id_field: str = "event_id") -> list[dict[str, Any]]:
    if not paths:
        return []
    seen = last_seen is None
    out: list[dict[str, Any]] = []
    for p in paths:
        data = read_json(p)
        if not data:
            continue
        current_id = data.get(id_field)
        if not seen:
            if current_id == last_seen:
                seen = True
            continue
        out.append(data)
    # If a cursor points to an event no longer reachable, fail open to current bounded
    # history rather than falsely returning no updates.
    if last_seen is not None and not seen:
        return [read_json(p) for p in paths if read_json(p)]
    return out


def cmd_join(args: argparse.Namespace) -> None:
    room_id = args.room or room_for_trigger(args.trigger)
    base = ensure_room(room_id)
    worker_id = args.worker or new_id("worker")
    worker = {
        "schema_version": "1.0",
        "room_id": room_id,
        "worker_session_id": worker_id,
        "actor_id": args.actor,
        "provider": args.provider,
        "model": args.model,
        "trigger": args.trigger,
        "status": "ACTIVE",
        "joined_at": now(),
        "last_pulse_at": now(),
        "canonical_parent": {"revision": args.canonical_revision, "state_hash": args.canonical_hash},
        "focus": args.focus or args.trigger,
        "ancestry_family": args.ancestry_family,
        "tools": args.tool,
        "trigger_loyalty": "PINNED" if room_id == args.trigger else "META_ROOM",
    }
    path = base / "workers" / f"{worker_id}.json"
    if path.exists():
        raise SystemExit(f"worker already exists: {worker_id}")
    write_json(path, worker)
    event = emit_event(room_id, worker_id, args.actor, args.trigger, "JOIN",
                       args.canonical_revision, args.canonical_hash,
                       payload={"focus": worker["focus"], "provider": args.provider, "model": args.model},
                       ancestry_family=args.ancestry_family)
    print(json.dumps({"worker": worker, "join_event": event}, ensure_ascii=False, indent=2))


def cmd_pulse(args: argparse.Namespace) -> None:
    room_id = args.room or room_for_trigger(args.trigger)
    base = ensure_room(room_id)
    worker_path = base / "workers" / f"{args.worker}.json"
    worker = read_json(worker_path)
    if not worker:
        raise SystemExit(f"unknown worker {args.worker} in room {room_id}")
    worker["last_pulse_at"] = now()
    worker["status"] = "ACTIVE"
    write_json(worker_path, worker)

    cursor_path = base / "cursors" / f"{args.worker}.json"
    cursor = read_json(cursor_path, {})
    local_paths = sorted((base / "events").glob("*.json"))
    local_events = events_after(local_paths, cursor.get("last_seen_event_id"))
    local_events = [e for e in local_events if e.get("origin_worker") != args.worker]

    center_paths = sorted(CENTER_EVENTS.glob("*.json")) if CENTER_EVENTS.exists() else []
    center_refs = events_after(center_paths, cursor.get("last_seen_center_event_id"))
    center_refs = [e for e in center_refs if room_id in e.get("target_rooms", [])]
    cross_events: list[dict[str, Any]] = []
    for ref in center_refs:
        ref_path = ROOT / ref.get("event_ref", "")
        event = read_json(ref_path)
        if event:
            cross_events.append(event)

    mailbox_dir = base / "mailboxes" / args.worker
    mailbox_refs = [read_json(p) for p in sorted(mailbox_dir.glob("*.json"))] if mailbox_dir.exists() else []
    mailbox_refs = [m for m in mailbox_refs if m]

    combined = local_events + cross_events
    combined.sort(key=lambda e: (e.get("created_at", ""), e.get("event_id", "")))
    if args.limit and len(combined) > args.limit:
        combined = combined[-args.limit:]

    newest_local = read_json(local_paths[-1]).get("event_id") if local_paths else cursor.get("last_seen_event_id")
    newest_center = read_json(center_paths[-1]).get("event_id") if center_paths else cursor.get("last_seen_center_event_id")
    cursor = {
        "schema_version": "1.1",
        "room_id": room_id,
        "worker_session_id": args.worker,
        "last_seen_event_id": newest_local,
        "last_seen_center_event_id": newest_center,
        "updated_at": now(),
    }
    write_json(cursor_path, cursor)
    print(json.dumps({
        "room_id": room_id,
        "worker": args.worker,
        "active_workers": active_workers(room_id),
        "new_events": combined,
        "mailbox_refs": mailbox_refs,
        "cursor": cursor,
    }, ensure_ascii=False, indent=2))


def cmd_auto_role(args: argparse.Namespace) -> None:
    room_id = args.room or room_for_trigger(args.trigger)
    active = active_workers(room_id)
    if len(active) <= 1:
        print(json.dumps({"room_id": room_id, "worker": args.worker, "mode": "SOLO", "role": "SOLO_RESEARCHER"}, indent=2))
        return
    team_epoch = args.team_epoch or current_team_epoch(room_id) or new_id("team")
    lease = choose_role(room_id, args.worker, team_epoch)
    epoch_path = ensure_room(room_id) / "team_epochs" / f"{team_epoch}.json"
    epoch = read_json(epoch_path, {
        "schema_version": "1.0",
        "team_epoch_id": team_epoch,
        "room_id": room_id,
        "created_at": now(),
        "status": "ACTIVE",
        "member_workers": [],
        "role_assignments": {},
        "shared_question": "derive from active trigger mission",
    })
    if args.worker not in epoch["member_workers"]:
        epoch["member_workers"].append(args.worker)
    epoch["role_assignments"][lease["subject_id"]] = args.worker
    write_json(epoch_path, epoch)
    print(json.dumps({"room_id": room_id, "worker": args.worker, "mode": "TEAM", "team_epoch": team_epoch, "lease": lease}, indent=2))


def cmd_publish(args: argparse.Namespace) -> None:
    room_id = args.room or room_for_trigger(args.trigger)
    payload = json.loads(args.payload) if args.payload else {}
    event = emit_event(
        room_id, args.worker, args.actor, args.trigger, args.event_type,
        args.canonical_revision, args.canonical_hash, payload=payload,
        affects_rooms=args.affects_room, affects_claims=args.affects_claim,
        dependencies=args.dependency, artifact_refs=args.artifact,
        ancestry_family=args.ancestry_family, delivery=args.delivery,
    )
    print(json.dumps(event, ensure_ascii=False, indent=2))


def cmd_challenge(args: argparse.Namespace) -> None:
    room_id = args.room or room_for_trigger(args.trigger)
    base = ensure_room(room_id)
    challenge_id = new_id("challenge")
    challenge = {
        "schema_version": "1.0",
        "challenge_id": challenge_id,
        "room_id": room_id,
        "challenger_worker": args.worker,
        "target_claim_or_artifact": args.target,
        "challenge_statement": args.statement,
        "evidence_or_counterexample_refs": args.artifact,
        "discriminating_test_or_falsifier": args.falsifier,
        "ancestry_family": args.ancestry_family,
        "status": "OPEN",
        "created_at": now(),
    }
    if not create_json_exclusive(base / "challenges" / f"{challenge_id}.json", challenge):
        raise RuntimeError("challenge id collision")
    emit_event(room_id, args.worker, args.actor, args.trigger, "CHALLENGE",
               args.canonical_revision, args.canonical_hash,
               payload={"challenge_id": challenge_id, "target": args.target, "falsifier": args.falsifier},
               artifact_refs=args.artifact, ancestry_family=args.ancestry_family,
               delivery="INTERRUPT_NEXT_SAFE_POINT")
    print(json.dumps(challenge, ensure_ascii=False, indent=2))


def cmd_leave(args: argparse.Namespace) -> None:
    room_id = args.room or room_for_trigger(args.trigger)
    base = ensure_room(room_id)
    path = base / "workers" / f"{args.worker}.json"
    worker = read_json(path)
    if not worker:
        raise SystemExit(f"unknown worker {args.worker}")
    worker["status"] = args.status
    worker["left_at"] = now()
    worker["last_pulse_at"] = now()
    write_json(path, worker)
    event = emit_event(room_id, args.worker, worker.get("actor_id", args.actor), args.trigger,
                       "LEAVE" if args.status == "LEFT" else "COMPLETE",
                       args.canonical_revision, args.canonical_hash,
                       payload={"status": args.status, "summary": args.summary},
                       ancestry_family=worker.get("ancestry_family", "UNKNOWN"))
    print(json.dumps({"worker": worker, "event": event}, ensure_ascii=False, indent=2))


def cmd_materialize(args: argparse.Namespace) -> None:
    room_id = args.room
    base = ensure_room(room_id)
    workers = worker_records(room_id)
    active = active_workers(room_id)
    tasks = [t for t in (read_json(p) for p in sorted((base / "tasks").glob("*.json"))) if t]
    leases = {p.stem: read_json(p) for p in sorted((base / "leases" / "roles").glob("*.json"))}
    event_paths = sorted((base / "events").glob("*.json"))
    latest = read_json(event_paths[-1]).get("event_id") if event_paths else None
    state = {
        "schema_version": "1.1",
        "room_id": room_id,
        "generated_at": now(),
        "active_workers": active,
        "all_workers_count": len(workers),
        "tasks": tasks,
        "role_leases": leases,
        "event_count": len(event_paths),
        "latest_event_id": latest,
        "projection_only": True,
    }
    write_json(base / "state" / "ROOM_STATE.json", state)
    print(json.dumps(state, ensure_ascii=False, indent=2))


def cmd_validate(args: argparse.Namespace) -> None:
    reg = registry()
    errors: list[str] = []
    expected_roles = set(ROLE_ORDER)
    actual_roles = {r.get("role") for r in reg.get("same_room_roles", [])}
    if expected_roles != actual_roles:
        errors.append(f"role registry mismatch expected={sorted(expected_roles)} actual={sorted(actual_roles)}")
    for room_id, cfg in reg.get("rooms", {}).items():
        if cfg.get("trigger") != room_id:
            errors.append(f"trigger loyalty mismatch for {room_id}: {cfg.get('trigger')}")
    if set(reg.get("delivery_classes", [])) != set(DELIVERY):
        errors.append("delivery class mismatch")
    result = {"ok": not errors, "errors": errors, "rooms": sorted(reg.get("rooms", {})), "meta_rooms": sorted(reg.get("meta_rooms", {}))}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


def add_common(sp: argparse.ArgumentParser, worker_optional: bool = True) -> None:
    sp.add_argument("--trigger", required=True)
    sp.add_argument("--room")
    sp.add_argument("--worker", required=not worker_optional)
    sp.add_argument("--actor", default="chatgpt-secondary")
    sp.add_argument("--canonical-revision", type=int, default=2)
    sp.add_argument("--canonical-hash", default="04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346")
    sp.add_argument("--ancestry-family", default="UNKNOWN")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="RAE repo-native research-room helper")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("join")
    add_common(sp, worker_optional=True)
    sp.add_argument("--provider", default="OpenAI")
    sp.add_argument("--model", default="unknown")
    sp.add_argument("--focus")
    sp.add_argument("--tool", action="append", default=[])
    sp.set_defaults(func=cmd_join)

    sp = sub.add_parser("pulse")
    add_common(sp, worker_optional=False)
    sp.add_argument("--limit", type=int, default=50)
    sp.set_defaults(func=cmd_pulse)

    sp = sub.add_parser("auto-role")
    add_common(sp, worker_optional=False)
    sp.add_argument("--team-epoch")
    sp.set_defaults(func=cmd_auto_role)

    sp = sub.add_parser("publish")
    add_common(sp, worker_optional=False)
    sp.add_argument("--event-type", default="DELTA")
    sp.add_argument("--payload", help="JSON object")
    sp.add_argument("--affects-room", action="append", default=[])
    sp.add_argument("--affects-claim", action="append", default=[])
    sp.add_argument("--dependency", action="append", default=[])
    sp.add_argument("--artifact", action="append", default=[])
    sp.add_argument("--delivery", choices=DELIVERY, default="NEXT_CHECKPOINT")
    sp.set_defaults(func=cmd_publish)

    sp = sub.add_parser("challenge")
    add_common(sp, worker_optional=False)
    sp.add_argument("--target", required=True)
    sp.add_argument("--statement", required=True)
    sp.add_argument("--falsifier", required=True)
    sp.add_argument("--artifact", action="append", default=[])
    sp.set_defaults(func=cmd_challenge)

    sp = sub.add_parser("leave")
    add_common(sp, worker_optional=False)
    sp.add_argument("--status", choices=["LEFT", "COMPLETE"], default="COMPLETE")
    sp.add_argument("--summary", default="")
    sp.set_defaults(func=cmd_leave)

    sp = sub.add_parser("materialize")
    sp.add_argument("--room", required=True)
    sp.set_defaults(func=cmd_materialize)

    sp = sub.add_parser("validate")
    sp.set_defaults(func=cmd_validate)

    return p


def main() -> int:
    args = build_parser().parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
