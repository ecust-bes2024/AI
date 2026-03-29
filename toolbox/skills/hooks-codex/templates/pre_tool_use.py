#!/usr/bin/env python3

import json
import sys


def main() -> int:
    payload = json.load(sys.stdin)
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    cmd = ""
    if isinstance(tool_input, dict):
        cmd = str(tool_input.get("cmd", ""))

    if tool_name in {"shell", "exec"} and "rm -rf /" in cmd:
        print(json.dumps({"ok": False, "decision": "deny", "reason": "Refusing destructive root delete."}))
        return 0

    print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
