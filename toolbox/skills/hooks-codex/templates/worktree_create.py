#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    payload = json.load(sys.stdin)
    repo_root = Path(payload["repo_root"]).expanduser().resolve()
    worktree_path = Path(payload["requested_path"]).expanduser().resolve()
    branch_name = payload["branch_name"]

    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "worktree", "add", "-b", branch_name, str(worktree_path)],
        check=True,
        text=True,
        capture_output=True,
    )

    print(json.dumps({"ok": True, "worktreePath": str(worktree_path), "branchName": branch_name}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
