#!/usr/bin/env python3

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import shutil
import sys
import textwrap
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_BASE = Path("docs") / "research" / "team-c-codex"
VALID_TASK_STATUSES = {"pending", "in_progress", "completed"}
VALID_PLAN_STATUSES = {"not_required", "required", "requested", "approved", "rejected"}
ACTIVE_TEAMMATE_STATES = {"active", "planning", "working", "idle"}
STOPPED_TEAMMATE_STATES = {"stopped", "shutdown", "completed"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    normalized = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    collapsed = "-".join(part for part in normalized.split("-") if part)
    return collapsed or "team"


@dataclass(frozen=True)
class TeamPaths:
    team_dir: Path
    manifest: Path
    task_board_json: Path
    task_board_md: Path
    mailbox_jsonl: Path
    mailbox_md: Path
    summary_md: Path
    approvals_dir: Path
    runtime_dir: Path
    logs_dir: Path
    archive_dir: Path
    lock_file: Path


def resolve_team_dir(base: Path, team_name: str) -> TeamPaths:
    base = Path(base).expanduser()
    if not base.is_absolute():
        base = (Path.cwd() / base).resolve()
    team_dir = base / slugify(team_name)
    return TeamPaths(
        team_dir=team_dir,
        manifest=team_dir / "team.json",
        task_board_json=team_dir / "task-board.json",
        task_board_md=team_dir / "task-board.md",
        mailbox_jsonl=team_dir / "mailbox.jsonl",
        mailbox_md=team_dir / "mailbox.md",
        summary_md=team_dir / "lead-summary.md",
        approvals_dir=team_dir / "approvals",
        runtime_dir=team_dir / "runtime",
        logs_dir=team_dir / "runtime" / "logs",
        archive_dir=team_dir / "archive",
        lock_file=team_dir / ".team.lock",
    )


def ensure_team_layout(paths: TeamPaths) -> None:
    paths.team_dir.mkdir(parents=True, exist_ok=True)
    paths.approvals_dir.mkdir(parents=True, exist_ok=True)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)
    paths.archive_dir.mkdir(parents=True, exist_ok=True)
    paths.lock_file.touch(exist_ok=True)


@contextlib.contextmanager
def team_lock(paths: TeamPaths):
    paths.lock_file.parent.mkdir(parents=True, exist_ok=True)
    paths.lock_file.touch(exist_ok=True)
    with paths.lock_file.open("r+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def load_manifest(paths: TeamPaths) -> dict[str, Any]:
    manifest = load_json(paths.manifest, None)
    if manifest is None:
      raise SystemExit(f"Team manifest not found: {paths.manifest}")
    return manifest


def save_manifest(paths: TeamPaths, manifest: dict[str, Any]) -> None:
    dump_json(paths.manifest, manifest)


def load_task_board(paths: TeamPaths) -> dict[str, Any]:
    return load_json(paths.task_board_json, {"tasks": []})


def save_task_board(paths: TeamPaths, board: dict[str, Any]) -> None:
    dump_json(paths.task_board_json, board)
    render_task_board(paths, board)


def read_mailbox(paths: TeamPaths) -> list[dict[str, Any]]:
    if not paths.mailbox_jsonl.exists():
        return []
    messages = []
    for line in paths.mailbox_jsonl.read_text(encoding="utf-8").splitlines():
        if line.strip():
            messages.append(json.loads(line))
    return messages


def append_mailbox(paths: TeamPaths, message: dict[str, Any]) -> None:
    paths.mailbox_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with paths.mailbox_jsonl.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(message, ensure_ascii=False) + "\n")
    render_mailbox(paths)


def save_mailbox(paths: TeamPaths, messages: list[dict[str, Any]]) -> None:
    paths.mailbox_jsonl.write_text(
        "".join(json.dumps(message, ensure_ascii=False) + "\n" for message in messages),
        encoding="utf-8",
    )
    render_mailbox(paths)


def render_task_board(paths: TeamPaths, board: dict[str, Any] | None = None) -> None:
    board = board or load_task_board(paths)
    tasks = board.get("tasks", [])
    lines = [
        "# Task Board",
        "",
        "| task_id | title | owner | status | depends_on | plan | deliverable |",
        "|---|---|---|---|---|---|---|",
    ]
    for task in tasks:
        depends_on = ", ".join(task.get("depends_on", [])) or "-"
        lines.append(
            "| {task_id} | {title} | {owner} | {status} | {depends_on} | {plan_status} | {deliverable} |".format(
                task_id=task["task_id"],
                title=task["title"].replace("|", "\\|"),
                owner=task.get("owner") or "-",
                status=task["status"],
                depends_on=depends_on,
                plan_status=task.get("plan_status", "not_required"),
                deliverable=task.get("deliverable") or "-",
            )
        )

    lines.extend(["", "## Notes", ""])
    for task in tasks:
        note_lines = [
            f"- `{task['task_id']}` {task['title']}",
            f"  owner: {task.get('owner') or '-'}",
            f"  status: {task['status']}",
        ]
        if task.get("plan_note"):
            note_lines.append(f"  plan_note: {task['plan_note']}")
        if task.get("notes"):
            note_lines.append(f"  notes: {task['notes']}")
        lines.extend(note_lines)

    paths.task_board_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def render_mailbox(paths: TeamPaths) -> None:
    messages = read_mailbox(paths)
    lines = ["# Mailbox", ""]
    if not messages:
        lines.extend(["No messages.", ""])
    for message in messages:
        lines.extend(
            [
                f"## {message['message_id']} [{message['status']}]",
                "",
                f"- sender: `{message['sender']}`",
                f"- recipient: `{message['recipient']}`",
                f"- sent_at: `{message['sent_at']}`",
                f"- subject: {message['subject']}",
                "",
                message["body"],
                "",
            ]
        )
    paths.mailbox_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def next_task_id(board: dict[str, Any]) -> str:
    existing = [int(task["task_id"][1:]) for task in board.get("tasks", []) if task.get("task_id", "").startswith("T")]
    return f"T{(max(existing) if existing else 0) + 1}"


def find_task(board: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in board.get("tasks", []):
        if task["task_id"] == task_id:
            return task
    raise SystemExit(f"Task not found: {task_id}")


def find_teammate(manifest: dict[str, Any], teammate_id: str) -> dict[str, Any]:
    for teammate in manifest.get("teammates", []):
        if teammate["id"] == teammate_id:
            return teammate
    raise SystemExit(f"Teammate not found: {teammate_id}")


def validate_status(status: str, allowed: set[str], label: str) -> None:
    if status not in allowed:
        raise SystemExit(f"Invalid {label}: {status}. Allowed: {', '.join(sorted(allowed))}")


def write_summary_stub(paths: TeamPaths, manifest: dict[str, Any]) -> None:
    if paths.summary_md.exists():
        return
    lines = [
        "# Lead Summary",
        "",
        f"- team_name: `{manifest['team_name']}`",
        f"- protocol: `{manifest['protocol']}`",
        f"- mode: `{manifest['mode']}`",
        "",
        "## Final synthesis",
        "",
        "Fill this in after teammates complete their work.",
        "",
    ]
    paths.summary_md.write_text("\n".join(lines), encoding="utf-8")


def render_dashboard(paths: TeamPaths) -> str:
    manifest = load_manifest(paths)
    board = load_task_board(paths)
    messages = read_mailbox(paths)
    lines = [
        f"team: {manifest['team_name']}",
        f"mode: {manifest['mode']}",
        f"lead: {manifest['lead']['id']} ({manifest['lead']['state']})",
        "",
        "teammates:",
    ]
    for teammate in manifest.get("teammates", []):
        lines.append(f"- {teammate['id']} role={teammate['role']} state={teammate['state']}")
    lines.extend(["", "tasks:"])
    for task in board.get("tasks", []):
        lines.append(
            f"- {task['task_id']} [{task['status']}] owner={task.get('owner') or '-'} plan={task.get('plan_status', 'not_required')} {task['title']}"
        )
    lines.extend(["", f"mailbox messages: {len(messages)}"])
    return "\n".join(lines)


def log_line(paths: TeamPaths, actor: str, text: str) -> Path:
    log_path = paths.logs_dir / f"{slugify(actor)}.log"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{now_iso()}] {text}\n")
    return log_path


def parse_teammate_spec(value: str) -> dict[str, Any]:
    parts = [part.strip() for part in value.split(":")]
    role = parts[0]
    teammate_id = parts[1] if len(parts) > 1 and parts[1] else slugify(role)
    model = parts[2] if len(parts) > 2 and parts[2] else ""
    return {
        "id": slugify(teammate_id),
        "role": role,
        "model": model,
        "state": "active",
        "created_at": now_iso(),
        "artifact": f"{slugify(role)}.md",
        "notes": "",
    }


def command_init(args: argparse.Namespace) -> int:
    base = Path(args.base)
    paths = resolve_team_dir(base, args.team_name)
    if paths.manifest.exists() and not args.force:
        raise SystemExit(f"Team already exists: {paths.team_dir}")

    ensure_team_layout(paths)
    teammates = [parse_teammate_spec(value) for value in args.teammate]
    manifest = {
        "schema_version": 1,
        "protocol": "team-c",
        "team_name": slugify(args.team_name),
        "display_name": args.team_name,
        "created_at": now_iso(),
        "mode": args.mode,
        "lead": {
            "id": slugify(args.lead),
            "role": "team-lead",
            "state": "active",
        },
        "teammates": teammates,
        "settings": {
            "plan_approval_default": args.require_plan_approval,
        },
        "cleanup": {
            "cleaned_at": None,
        },
    }
    board = {"tasks": []}
    save_manifest(paths, manifest)
    save_task_board(paths, board)
    render_mailbox(paths)
    write_summary_stub(paths, manifest)

    for teammate in teammates:
        artifact_path = paths.team_dir / teammate["artifact"]
        artifact_path.write_text(
            textwrap.dedent(
                f"""\
                # {teammate['id']}

                - role: `{teammate['role']}`
                - state: `{teammate['state']}`
                - model: `{teammate['model'] or '-'}`

                ## Deliverable

                Fill this file with the teammate's output.
                """
            ),
            encoding="utf-8",
        )
        log_line(paths, teammate["id"], "teammate registered")

    print(paths.team_dir)
    return 0


def command_task_add(args: argparse.Namespace) -> int:
    paths = resolve_team_dir(Path(args.base), args.team_name)
    with team_lock(paths):
        board = load_task_board(paths)
        manifest = load_manifest(paths)
        owner = slugify(args.owner) if args.owner else ""
        if owner:
            find_teammate(manifest, owner)
        plan_status = "required" if args.require_plan else "not_required"
        task = {
            "task_id": next_task_id(board),
            "title": args.title,
            "owner": owner,
            "status": "pending",
            "depends_on": [task_id.strip() for task_id in args.depends_on if task_id.strip()],
            "deliverable": args.deliverable,
            "notes": args.notes,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "plan_status": plan_status,
            "plan_note": "",
            "plan_file": "",
        }
        board["tasks"].append(task)
        save_task_board(paths, board)
    print(task["task_id"])
    return 0


def command_task_update(args: argparse.Namespace) -> int:
    paths = resolve_team_dir(Path(args.base), args.team_name)
    with team_lock(paths):
        board = load_task_board(paths)
        manifest = load_manifest(paths)
        task = find_task(board, args.task_id)
        if args.owner is not None:
            task["owner"] = slugify(args.owner) if args.owner else ""
            if task["owner"]:
                find_teammate(manifest, task["owner"])
        if args.status:
            validate_status(args.status, VALID_TASK_STATUSES, "task status")
            task["status"] = args.status
        if args.notes is not None:
            task["notes"] = args.notes
        if args.deliverable is not None:
            task["deliverable"] = args.deliverable
        task["updated_at"] = now_iso()
        save_task_board(paths, board)
    return 0


def command_task_claim(args: argparse.Namespace) -> int:
    paths = resolve_team_dir(Path(args.base), args.team_name)
    with team_lock(paths):
        board = load_task_board(paths)
        manifest = load_manifest(paths)
        teammate = find_teammate(manifest, slugify(args.teammate))
        available = []
        for task in board.get("tasks", []):
            if task["status"] != "pending":
                continue
            if task.get("owner"):
                continue
            blockers = [dep for dep in task.get("depends_on", []) if find_task(board, dep)["status"] != "completed"]
            if blockers:
                continue
            available.append(task)
        if not available:
            raise SystemExit("No claimable task found.")
        task = available[0]
        task["owner"] = teammate["id"]
        task["status"] = "in_progress"
        task["updated_at"] = now_iso()
        save_task_board(paths, board)
    print(task["task_id"])
    return 0


def command_plan_request(args: argparse.Namespace) -> int:
    paths = resolve_team_dir(Path(args.base), args.team_name)
    plan_file = Path(args.plan_file)
    if not plan_file.exists():
        raise SystemExit(f"Plan file not found: {plan_file}")
    with team_lock(paths):
        board = load_task_board(paths)
        task = find_task(board, args.task_id)
        target = paths.approvals_dir / f"{task['task_id']}-plan.md"
        shutil.copyfile(plan_file, target)
        task["plan_status"] = "requested"
        task["plan_file"] = str(target.relative_to(paths.team_dir))
        task["plan_note"] = args.note or ""
        task["updated_at"] = now_iso()
        save_task_board(paths, board)
    print(target)
    return 0


def command_plan_decide(args: argparse.Namespace, approved: bool) -> int:
    paths = resolve_team_dir(Path(args.base), args.team_name)
    with team_lock(paths):
        board = load_task_board(paths)
        task = find_task(board, args.task_id)
        task["plan_status"] = "approved" if approved else "rejected"
        task["plan_note"] = args.note or ""
        task["updated_at"] = now_iso()
        save_task_board(paths, board)
    return 0


def command_mailbox_send(args: argparse.Namespace) -> int:
    paths = resolve_team_dir(Path(args.base), args.team_name)
    with team_lock(paths):
        manifest = load_manifest(paths)
        sender = slugify(args.sender)
        if sender != manifest["lead"]["id"]:
            find_teammate(manifest, sender)

        recipients = [slugify(args.recipient)]
        if args.recipient == "broadcast":
            recipients = [teammate["id"] for teammate in manifest.get("teammates", [])]

        existing = read_mailbox(paths)
        next_id = len(existing) + 1
        for recipient in recipients:
            if recipient != "lead":
                if recipient != manifest["lead"]["id"]:
                    find_teammate(manifest, recipient)
            append_mailbox(
                paths,
                {
                    "message_id": f"M{next_id}",
                    "sender": sender,
                    "recipient": recipient,
                    "subject": args.subject,
                    "body": args.body,
                    "sent_at": now_iso(),
                    "status": "open",
                },
            )
            next_id += 1
    return 0


def command_mailbox_resolve(args: argparse.Namespace) -> int:
    paths = resolve_team_dir(Path(args.base), args.team_name)
    with team_lock(paths):
        messages = read_mailbox(paths)
        for message in messages:
            if message["message_id"] == args.message_id:
                message["status"] = "resolved"
                break
        else:
            raise SystemExit(f"Message not found: {args.message_id}")
        save_mailbox(paths, messages)
    return 0


def command_lifecycle_status(args: argparse.Namespace) -> int:
    paths = resolve_team_dir(Path(args.base), args.team_name)
    print(render_dashboard(paths))
    return 0


def command_lifecycle_set(args: argparse.Namespace) -> int:
    paths = resolve_team_dir(Path(args.base), args.team_name)
    with team_lock(paths):
        manifest = load_manifest(paths)
        teammate = find_teammate(manifest, slugify(args.teammate))
        teammate["state"] = args.state
        teammate["updated_at"] = now_iso()
        save_manifest(paths, manifest)
    log_line(paths, teammate["id"], f"state={args.state}")
    return 0


def command_lifecycle_heartbeat(args: argparse.Namespace) -> int:
    paths = resolve_team_dir(Path(args.base), args.team_name)
    with team_lock(paths):
        manifest = load_manifest(paths)
        teammate = find_teammate(manifest, slugify(args.teammate))
        teammate["last_heartbeat_at"] = now_iso()
        if args.note:
            teammate["notes"] = args.note
        save_manifest(paths, manifest)
    log_line(paths, teammate["id"], args.note or "heartbeat")
    return 0


def command_cleanup(args: argparse.Namespace) -> int:
    paths = resolve_team_dir(Path(args.base), args.team_name)
    with team_lock(paths):
        manifest = load_manifest(paths)
        active = [member["id"] for member in manifest.get("teammates", []) if member["state"] not in STOPPED_TEAMMATE_STATES]
        if active and not args.force:
            raise SystemExit(f"Cleanup blocked. Active teammates: {', '.join(active)}")
        manifest["cleanup"]["cleaned_at"] = now_iso()
        save_manifest(paths, manifest)
    archive_note = paths.archive_dir / f"cleanup-{int(time.time())}.md"
    archive_note.write_text(
        f"# Cleanup\n\n- cleaned_at: `{manifest['cleanup']['cleaned_at']}`\n- forced: `{args.force}`\n",
        encoding="utf-8",
    )
    print(archive_note)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="team-c runtime helpers")
    parser.add_argument("--base", default=str(DEFAULT_BASE), help="Base directory for team artifacts")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("team_name")
    init_parser.add_argument("--lead", default="lead")
    init_parser.add_argument("--mode", default="in-process", choices=["in-process", "split-panes", "auto"])
    init_parser.add_argument("--teammate", action="append", default=[], help="role[:id[:model]]")
    init_parser.add_argument("--require-plan-approval", action="store_true")
    init_parser.add_argument("--force", action="store_true")
    init_parser.set_defaults(handler=command_init)

    task_parser = subparsers.add_parser("task-add")
    task_parser.add_argument("team_name")
    task_parser.add_argument("title")
    task_parser.add_argument("--owner", default="")
    task_parser.add_argument("--deliverable", default="")
    task_parser.add_argument("--notes", default="")
    task_parser.add_argument("--depends-on", action="append", default=[])
    task_parser.add_argument("--require-plan", action="store_true")
    task_parser.set_defaults(handler=command_task_add)

    update_parser = subparsers.add_parser("task-update")
    update_parser.add_argument("team_name")
    update_parser.add_argument("task_id")
    update_parser.add_argument("--owner")
    update_parser.add_argument("--status")
    update_parser.add_argument("--deliverable")
    update_parser.add_argument("--notes")
    update_parser.set_defaults(handler=command_task_update)

    claim_parser = subparsers.add_parser("task-claim")
    claim_parser.add_argument("team_name")
    claim_parser.add_argument("teammate")
    claim_parser.set_defaults(handler=command_task_claim)

    plan_request_parser = subparsers.add_parser("plan-request")
    plan_request_parser.add_argument("team_name")
    plan_request_parser.add_argument("task_id")
    plan_request_parser.add_argument("plan_file")
    plan_request_parser.add_argument("--note", default="")
    plan_request_parser.set_defaults(handler=command_plan_request)

    approve_parser = subparsers.add_parser("plan-approve")
    approve_parser.add_argument("team_name")
    approve_parser.add_argument("task_id")
    approve_parser.add_argument("--note", default="")
    approve_parser.set_defaults(handler=lambda args: command_plan_decide(args, approved=True))

    reject_parser = subparsers.add_parser("plan-reject")
    reject_parser.add_argument("team_name")
    reject_parser.add_argument("task_id")
    reject_parser.add_argument("--note", default="")
    reject_parser.set_defaults(handler=lambda args: command_plan_decide(args, approved=False))

    send_parser = subparsers.add_parser("mail-send")
    send_parser.add_argument("team_name")
    send_parser.add_argument("--sender", required=True)
    send_parser.add_argument("--recipient", required=True, help="teammate id, lead, or broadcast")
    send_parser.add_argument("--subject", required=True)
    send_parser.add_argument("--body", required=True)
    send_parser.set_defaults(handler=command_mailbox_send)

    resolve_parser = subparsers.add_parser("mail-resolve")
    resolve_parser.add_argument("team_name")
    resolve_parser.add_argument("message_id")
    resolve_parser.set_defaults(handler=command_mailbox_resolve)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("team_name")
    status_parser.set_defaults(handler=command_lifecycle_status)

    state_parser = subparsers.add_parser("set-state")
    state_parser.add_argument("team_name")
    state_parser.add_argument("teammate")
    state_parser.add_argument("state")
    state_parser.set_defaults(handler=command_lifecycle_set)

    heartbeat_parser = subparsers.add_parser("heartbeat")
    heartbeat_parser.add_argument("team_name")
    heartbeat_parser.add_argument("teammate")
    heartbeat_parser.add_argument("--note", default="")
    heartbeat_parser.set_defaults(handler=command_lifecycle_heartbeat)

    cleanup_parser = subparsers.add_parser("cleanup")
    cleanup_parser.add_argument("team_name")
    cleanup_parser.add_argument("--force", action="store_true")
    cleanup_parser.set_defaults(handler=command_cleanup)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
