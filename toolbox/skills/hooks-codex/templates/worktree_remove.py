#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    payload = json.load(sys.stdin)
    repo_root = Path(payload["repo_root"]).expanduser().resolve()
    worktree_path = Path(payload["worktree_path"]).expanduser().resolve()
    force = bool(payload.get("force", False))

    args = ["git", "-C", str(repo_root), "worktree", "remove"]
    if force:
        args.append("--force")
    args.append(str(worktree_path))
    subprocess.run(args, check=True, text=True, capture_output=True)

    print(json.dumps({"ok": True, "removedPath": str(worktree_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
