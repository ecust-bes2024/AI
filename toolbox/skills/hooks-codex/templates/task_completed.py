#!/usr/bin/env python3

import json
import sys


def main() -> int:
    payload = json.load(sys.stdin)
    task_id = payload.get("task_id", "")
    subject = payload.get("task_subject", "")
    print(
        json.dumps(
            {
                "ok": True,
                "additionalContext": f"Task {task_id} completed: {subject}. Ensure review and artifact updates are not skipped.",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
