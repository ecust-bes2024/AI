#!/usr/bin/env python3

import json
import sys


def main() -> int:
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {})
    cmd = ""
    if isinstance(tool_input, dict):
        cmd = str(tool_input.get("cmd", ""))

    if "git push --force" in cmd:
        print(json.dumps({"ok": False, "decision": "ask", "reason": "Force push requires explicit review."}))
        return 0

    print(json.dumps({"ok": True, "decision": "allow"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
