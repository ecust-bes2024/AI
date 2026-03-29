#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from team_runtime import DEFAULT_BASE, load_manifest, render_dashboard, resolve_team_dir


def clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def watch_dashboard(team_name: str, base: str, interval: float) -> int:
    paths = resolve_team_dir(Path(base), team_name)
    while True:
        clear_screen()
        print(render_dashboard(paths))
        time.sleep(interval)


def start_tmux(team_name: str, base: str, session_name: str | None) -> int:
    paths = resolve_team_dir(Path(base), team_name)
    manifest = load_manifest(paths)
    if not shutil_which("tmux"):
        raise SystemExit("tmux not found in PATH")

    session = session_name or f"team-c-{manifest['team_name']}"
    dashboard_cmd = f"python3 {Path(__file__).resolve()} watch {manifest['team_name']} --base {base}"
    subprocess.run(["tmux", "new-session", "-d", "-s", session, dashboard_cmd], check=True)

    for teammate in manifest.get("teammates", []):
        log_path = paths.logs_dir / f"{teammate['id']}.log"
        log_path.touch(exist_ok=True)
        subprocess.run(["tmux", "split-window", "-t", session, "-h", f"tail -f {log_path}"], check=True)
        subprocess.run(["tmux", "select-layout", "-t", session, "tiled"], check=True)

    print(session)
    return 0


def shutil_which(binary: str) -> str | None:
    for entry in os.environ.get("PATH", "").split(":"):
        candidate = Path(entry) / binary
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="team-c display helpers")
    parser.add_argument("--base", default=str(DEFAULT_BASE))
    subparsers = parser.add_subparsers(dest="command", required=True)

    watch_parser = subparsers.add_parser("watch")
    watch_parser.add_argument("team_name")
    watch_parser.add_argument("--interval", type=float, default=1.5)

    tmux_parser = subparsers.add_parser("tmux")
    tmux_parser.add_argument("team_name")
    tmux_parser.add_argument("--session-name")

    args = parser.parse_args()
    if args.command == "watch":
        return watch_dashboard(args.team_name, args.base, args.interval)
    if args.command == "tmux":
        return start_tmux(args.team_name, args.base, args.session_name)
    raise SystemExit("Unknown command")


if __name__ == "__main__":
    sys.exit(main())
