#!/usr/bin/env python3

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_BASE = Path("docs") / "research" / "team-c-codex"
LAB_HOOK_DISPATCH = Path("/Users/jerry_hu/AI/toolbox/skills/hooks-codex/scripts/lab-dispatch.sh")
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
    inbox_cursors_dir: Path
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
        inbox_cursors_dir=team_dir / "runtime" / "inbox-cursors",
        archive_dir=team_dir / "archive",
        lock_file=team_dir / ".team.lock",
    )


def ensure_team_layout(paths: TeamPaths) -> None:
    paths.team_dir.mkdir(parents=True, exist_ok=True)
    paths.approvals_dir.mkdir(parents=True, exist_ok=True)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)
    paths.inbox_cursors_dir.mkdir(parents=True, exist_ok=True)
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


def cursor_file(paths: TeamPaths, consumer: str) -> Path:
    return paths.inbox_cursors_dir / f"{slugify(consumer)}.json"


def read_cursor(paths: TeamPaths, consumer: str) -> dict[str, Any]:
    return load_json(cursor_file(paths, consumer), {"last_read_index": 0, "acked_tokens": []})


def save_cursor(paths: TeamPaths, consumer: str, payload: dict[str, Any]) -> None:
    dump_json(cursor_file(paths, consumer), payload)


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
                f"- ack_token: `{message['ack_token']}`",
                f"- kind: `{message.get('kind', 'message')}`",
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
        lines.append(
            f"- {teammate['id']} role={teammate['role']} state={teammate['state']} worktree={teammate.get('worktree', False)}"
        )
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


def run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        text=True,
        capture_output=True,
    )


def dispatch_lab_hook(event: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not LAB_HOOK_DISPATCH.exists():
        return {}
    proc = subprocess.run(
        [str(LAB_HOOK_DISPATCH), "--event", event, "--payload-json", json.dumps(payload, ensure_ascii=False)],
        check=False,
        text=True,
        capture_output=True,
    )
    stdout = proc.stdout.strip()
    if not stdout:
        raise RuntimeError(f"hooks-codex returned no output for {event}")
    data = json.loads(stdout)
    if proc.returncode != 0 or not data.get("ok", False):
        raise RuntimeError(f"hooks-codex blocked {event}: {data.get('reason') or proc.stderr.strip()}")
    return data


def detect_repo_root(explicit_repo: str | None) -> str:
    if explicit_repo:
        repo_root = Path(explicit_repo).expanduser().resolve()
    else:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=False,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            return ""
        repo_root = Path(result.stdout.strip()).resolve()
    if not repo_root.exists():
        raise SystemExit(f"Repository root not found: {repo_root}")
    return str(repo_root)


def build_worktree_path(repo_root: Path, team_name: str, teammate_id: str) -> Path:
    root = repo_root.parent / ".worktrees-codex" / repo_root.name / slugify(team_name)
    return root / slugify(teammate_id)


def create_teammate_worktree(repo_root: Path, team_name: str, teammate: dict[str, Any]) -> None:
    branch_name = f"{slugify(team_name)}-{teammate['id']}-codex"
    worktree_path = build_worktree_path(repo_root, team_name, teammate["id"])
    hook_result = dispatch_lab_hook(
        "worktree_create",
        {
            "hook_event_name": "WorktreeCreate",
            "name": teammate["id"],
            "team_name": slugify(team_name),
            "teammate_name": teammate["id"],
            "repo_root": str(repo_root),
            "requested_path": str(worktree_path),
            "branch_name": branch_name,
        },
    )
    teammate["worktree_path"] = hook_result.get("worktreePath", str(worktree_path))
    teammate["worktree_branch"] = hook_result.get("branchName", branch_name)
    teammate["worktree_created"] = True
    teammate["worktree_managed_by"] = "hooks-codex"


def remove_teammate_worktree(repo_root: Path, teammate: dict[str, Any], force: bool) -> None:
    worktree_path = teammate.get("worktree_path")
    if not worktree_path:
        return
    manager = teammate.get("worktree_managed_by")
    if manager == "hooks-codex":
        dispatch_lab_hook(
            "worktree_remove",
            {
                "hook_event_name": "WorktreeRemove",
                "worktree_path": worktree_path,
                "repo_root": str(repo_root),
                "force": force,
                "teammate_name": teammate["id"],
            },
        )
        return
    args = ["worktree", "remove"]
    if force:
        args.append("--force")
    args.append(worktree_path)
    run_git(repo_root, *args)


def parse_bool_text(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_teammate_spec(value: str) -> dict[str, Any]:
    parts = [part.strip() for part in value.split(":")]
    role = parts[0]
    teammate_id = parts[1] if len(parts) > 1 and parts[1] else slugify(role)
    model = parts[2] if len(parts) > 2 and parts[2] else ""
    worktree = parse_bool_text(parts[3]) if len(parts) > 3 and parts[3] else False
    return {
        "id": slugify(teammate_id),
        "role": role,
        "model": model,
        "worktree": worktree,
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
    repo_root = detect_repo_root(args.repo) if any(teammate["worktree"] for teammate in teammates) else ""
    if any(teammate["worktree"] for teammate in teammates) and not repo_root:
        raise SystemExit(
            "At least one teammate requested worktree=true, but no git repository root was detected. "
            "Pass --repo explicitly or run inside a git repo."
        )
    manifest = {
        "schema_version": 1,
        "protocol": "team-c",
        "team_name": slugify(args.team_name),
        "display_name": args.team_name,
        "created_at": now_iso(),
        "mode": args.mode,
        "repo_root": repo_root,
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

    if repo_root:
        repo_path = Path(repo_root)
        try:
            for teammate in teammates:
                if teammate["worktree"]:
                    create_teammate_worktree(repo_path, manifest["team_name"], teammate)
        except Exception:
            for teammate in teammates:
                if teammate.get("worktree_created"):
                    try:
                        remove_teammate_worktree(repo_path, teammate, force=True)
                    except Exception:
                        pass
            raise

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
                - worktree: `{teammate['worktree']}`
                - worktree_path: `{teammate.get('worktree_path', '-')}`

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
        previous_status = task["status"]
        if args.owner is not None:
            task["owner"] = slugify(args.owner) if args.owner else ""
            if task["owner"]:
                find_teammate(manifest, task["owner"])
        if args.status:
            validate_status(args.status, VALID_TASK_STATUSES, "task status")
            if args.status == "completed" and previous_status != "completed":
                hook_result = dispatch_lab_hook(
                    "task_completed",
                    {
                        "hook_event_name": "TaskCompleted",
                        "task_id": task["task_id"],
                        "task_subject": task["title"],
                        "task_description": task.get("notes", ""),
                        "team_name": manifest["team_name"],
                        "teammate_name": task.get("owner", ""),
                    },
                )
                if hook_result.get("additionalContext"):
                    existing_notes = task.get("notes", "")
                    addition = f"[hook] {hook_result['additionalContext']}"
                    task["notes"] = f"{existing_notes}\n{addition}".strip()
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
        task = find_task(board, args.task_id)
        blockers = [dep for dep in task.get("depends_on", []) if find_task(board, dep)["status"] != "completed"]
        if blockers:
            raise SystemExit(f"Task {task['task_id']} is blocked by: {', '.join(blockers)}")
        if task["status"] != "pending":
            raise SystemExit(f"Task {task['task_id']} is not pending.")
        if task.get("owner") and task["owner"] != teammate["id"]:
            raise SystemExit(f"Task {task['task_id']} is already owned by {task['owner']}.")
        task["owner"] = teammate["id"]
        task["status"] = "in_progress"
        task["updated_at"] = now_iso()
        save_task_board(paths, board)
    print(task["task_id"])
    return 0


def command_task_claim_next(args: argparse.Namespace) -> int:
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
                    "ack_token": f"ACK-{next_id}",
                    "kind": getattr(args, "kind", "message"),
                },
            )
            next_id += 1
    return 0


def command_ask_lead(args: argparse.Namespace) -> int:
    args.recipient = "lead"
    args.kind = "ask_lead"
    return command_mailbox_send(args)


def command_reply_lead(args: argparse.Namespace) -> int:
    paths = resolve_team_dir(Path(args.base), args.team_name)
    with team_lock(paths):
        manifest = load_manifest(paths)
        recipient = slugify(args.recipient)
        find_teammate(manifest, recipient)
        hook_result = dispatch_lab_hook(
            "lead_reply",
            {
                "hook_event_name": "LeadReply",
                "team_name": manifest["team_name"],
                "sender": manifest["lead"]["id"],
                "recipient": recipient,
                "subject": args.subject,
                "body": args.body,
            },
        )
        existing = read_mailbox(paths)
        next_id = len(existing) + 1
        append_mailbox(
            paths,
            {
                "message_id": f"M{next_id}",
                "sender": manifest["lead"]["id"],
                "recipient": recipient,
                "subject": args.subject,
                "body": args.body,
                "sent_at": now_iso(),
                "status": "open",
                "ack_token": f"ACK-{next_id}",
                "kind": "lead_reply",
            },
        )
        if hook_result.get("additionalContext"):
            note = f"[lead_reply hook] {hook_result['additionalContext']}"
            summary = paths.summary_md.read_text(encoding="utf-8") if paths.summary_md.exists() else "# Lead Summary\n\n"
            if note not in summary:
                paths.summary_md.write_text(summary.rstrip() + f"\n\n## Lead Reply Notes\n\n- {note}\n", encoding="utf-8")
    return 0


def command_mailbox_pop(args: argparse.Namespace) -> int:
    paths = resolve_team_dir(Path(args.base), args.team_name)
    with team_lock(paths):
        manifest = load_manifest(paths)
        consumer = slugify(args.recipient)
        if consumer != manifest["lead"]["id"]:
            find_teammate(manifest, consumer)
        messages = read_mailbox(paths)
        cursor = read_cursor(paths, consumer)
        last_read_index = int(cursor.get("last_read_index", 0))
        pending = []
        for index, message in enumerate(messages[last_read_index:], start=last_read_index):
            if message["recipient"] != consumer:
                continue
            if message["status"] not in {"open", "acked"}:
                continue
            pending.append(
                {
                    "message_id": message["message_id"],
                    "sender": message["sender"],
                    "recipient": message["recipient"],
                    "subject": message["subject"],
                    "body": message["body"],
                    "sent_at": message["sent_at"],
                    "status": message["status"],
                    "ack_token": message["ack_token"],
                    "kind": message.get("kind", "message"),
                    "index": index,
                }
            )
            if len(pending) >= args.limit:
                break
        if pending:
            cursor["last_read_index"] = max(item["index"] for item in pending) + 1
            save_cursor(paths, consumer, cursor)
    print(json.dumps({"messages": pending}, ensure_ascii=False, indent=2))
    return 0


def command_mailbox_ack(args: argparse.Namespace) -> int:
    paths = resolve_team_dir(Path(args.base), args.team_name)
    with team_lock(paths):
        messages = read_mailbox(paths)
        acked = []
        for token in args.ack_token:
            for message in messages:
                if message["ack_token"] == token:
                    message["status"] = "acked"
                    message["acked_at"] = now_iso()
                    acked.append(token)
                    break
        save_mailbox(paths, messages)
    print(json.dumps({"acked_tokens": acked}, ensure_ascii=False, indent=2))
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
        repo_root = manifest.get("repo_root", "")
        if repo_root:
            repo_path = Path(repo_root)
            for teammate in manifest.get("teammates", []):
                if teammate.get("worktree_created") and teammate.get("worktree_path"):
                    remove_teammate_worktree(repo_path, teammate, force=args.force)
                    teammate["worktree_removed_at"] = now_iso()
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
    init_parser.add_argument("--teammate", action="append", default=[], help="role[:id[:model[:worktree]]]")
    init_parser.add_argument("--repo", default="", help="Optional git repository root used when any teammate sets worktree=true")
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
    claim_parser.add_argument("task_id")
    claim_parser.add_argument("teammate")
    claim_parser.set_defaults(handler=command_task_claim)

    claim_next_parser = subparsers.add_parser("task-claim-next")
    claim_next_parser.add_argument("team_name")
    claim_next_parser.add_argument("teammate")
    claim_next_parser.set_defaults(handler=command_task_claim_next)

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
    send_parser.set_defaults(kind="message")
    send_parser.set_defaults(handler=command_mailbox_send)

    ask_lead_parser = subparsers.add_parser("ask-lead")
    ask_lead_parser.add_argument("team_name")
    ask_lead_parser.add_argument("--sender", required=True)
    ask_lead_parser.add_argument("--subject", required=True)
    ask_lead_parser.add_argument("--body", required=True)
    ask_lead_parser.set_defaults(handler=command_ask_lead)

    reply_lead_parser = subparsers.add_parser("reply-lead")
    reply_lead_parser.add_argument("team_name")
    reply_lead_parser.add_argument("--recipient", required=True)
    reply_lead_parser.add_argument("--subject", required=True)
    reply_lead_parser.add_argument("--body", required=True)
    reply_lead_parser.set_defaults(handler=command_reply_lead)

    resolve_parser = subparsers.add_parser("mail-resolve")
    resolve_parser.add_argument("team_name")
    resolve_parser.add_argument("message_id")
    resolve_parser.set_defaults(handler=command_mailbox_resolve)

    pop_parser = subparsers.add_parser("mail-pop")
    pop_parser.add_argument("team_name")
    pop_parser.add_argument("--recipient", required=True)
    pop_parser.add_argument("--limit", type=int, default=20)
    pop_parser.set_defaults(handler=command_mailbox_pop)

    ack_parser = subparsers.add_parser("mail-ack")
    ack_parser.add_argument("team_name")
    ack_parser.add_argument("ack_token", nargs="+")
    ack_parser.set_defaults(handler=command_mailbox_ack)

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
