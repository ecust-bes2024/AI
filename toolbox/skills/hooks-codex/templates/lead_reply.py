#!/usr/bin/env python3

import json
import sys


def main() -> int:
    payload = json.load(sys.stdin)
    recipient = payload.get("recipient", "")
    subject = payload.get("subject", "")
    print(
        json.dumps(
            {
                "ok": True,
                "additionalContext": f"Lead replied to {recipient}: {subject}. Sync task board or mailbox state if execution changed.",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
