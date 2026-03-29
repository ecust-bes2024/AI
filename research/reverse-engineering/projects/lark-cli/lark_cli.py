#!/usr/bin/env python3
"""
lark-cli — Standalone Lark/Feishu messaging CLI.
Usage:
    lark setup                          Setup cookie (guided)
    lark me                             Show current user info
    lark search <query>                 Search users/groups
    lark send --to <name> --msg <text>  Send message by user name
    lark send --chat-id <id> --msg <text>  Send message to chat
    lark notify <text>                  Send message to yourself
    lark watch [--json]                 Daemon: listen for new messages via WebSocket
"""
import argparse
import json
import os
import subprocess
import sys

CONFIG_PATH = os.path.expanduser("~/.config/lark-cli/config.json")


def load_cookie():
    cookie = os.environ.get("LARK_COOKIE")
    if cookie:
        return cookie
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        cookie = cfg.get("cookie")
        if cookie:
            return cookie
    print(
        "Error: No cookie found.\n"
        "Run 'lark setup' to configure your Feishu cookie,\n"
        "or set the LARK_COOKIE environment variable.",
        file=sys.stderr,
    )
    sys.exit(1)


def get_api():
    from lark_api import LarkAPI
    cookie = load_cookie()
    return LarkAPI(cookie)


def cmd_setup(_args):
    print("=== Feishu Cookie Setup ===\n")
    print("Steps to get your cookie:")
    print("  1. Open https://www.feishu.cn/messenger/ in Chrome")
    print("  2. Log in to your Feishu account")
    print("  3. Press F12 to open DevTools → Application → Cookies")
    print("  4. Copy ALL cookies as a single string")
    print("     (or use DevTools Console: document.cookie)\n")

    # Try clipboard first
    cookie = None
    try:
        clip = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2)
        clip_text = clip.stdout.strip()
        if clip_text and "session" in clip_text.lower():
            resp = input(f"Clipboard contains a cookie-like string ({len(clip_text)} chars). Use it? [Y/n] ")
            if resp.strip().lower() != "n":
                cookie = clip_text
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    if not cookie:
        print("Paste your cookie string (single line):")
        cookie = input("> ").strip()

    if not cookie:
        print("Error: Empty cookie.", file=sys.stderr)
        sys.exit(1)

    # Validate by attempting login
    print("\nValidating cookie...")
    try:
        from lark_api import LarkAPI
        api = LarkAPI(cookie)
        info = api.get_me()
        print(f"Login successful! Welcome, {info['user_name']} (ID: {info['user_id']})")
    except Exception as e:
        print(f"Error: Cookie validation failed — {e}", file=sys.stderr)
        sys.exit(1)

    # Save to config
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
    cfg["cookie"] = cookie
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"Cookie saved to {CONFIG_PATH}")


def cmd_me(_args):
    api = get_api()
    info = api.get_me()
    print(f"User: {info['user_name']}")
    print(f"  ID: {info['user_id']}")


def cmd_search(args):
    api = get_api()
    results = api.search(args.query)
    if not results:
        print("No results found.")
        return
    for r in results:
        print(f"[{r['type']:>5}] {r['id']}  {r.get('title', '')}")


def cmd_send(args):
    api = get_api()
    if args.to:
        chat_id = api.send_to_user(args.to, args.msg)
        print(f"Sent to '{args.to}' (chat_id: {chat_id})")
    elif args.chat_id:
        api.send_message(args.msg, args.chat_id)
        print(f"Sent to chat_id: {args.chat_id}")
    else:
        print("Error: --to or --chat-id required", file=sys.stderr)
        sys.exit(1)


def cmd_notify(args):
    api = get_api()
    # Load self chat_id from config, or create one
    self_chat_id = None
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        self_chat_id = cfg.get("self_chat_id")

    if not self_chat_id:
        self_chat_id = api.create_chat(api.me_id)
        if not self_chat_id:
            print("Error: Failed to create self-chat.", file=sys.stderr)
            sys.exit(1)
        cfg["self_chat_id"] = self_chat_id
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)

    api.send_message(args.text, self_chat_id)
    print(f"Notified self (chat_id: {self_chat_id})")


def cmd_watch(args):
    from lark_daemon import run_daemon
    api = get_api()
    run_daemon(api, output_json=args.json)


def main():
    parser = argparse.ArgumentParser(prog="lark", description="Lark/Feishu CLI messenger")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("setup", help="Setup Feishu cookie (guided)")
    sub.add_parser("me", help="Show current user info")

    p_search = sub.add_parser("search", help="Search users/groups")
    p_search.add_argument("query", help="Search keyword")

    p_send = sub.add_parser("send", help="Send a message")
    p_send.add_argument("--to", help="User name to search and send to")
    p_send.add_argument("--chat-id", help="Direct chat ID to send to")
    p_send.add_argument("--msg", required=True, help="Message text")

    p_notify = sub.add_parser("notify", help="Send a message to yourself")
    p_notify.add_argument("text", help="Notification text")

    p_watch = sub.add_parser("watch", help="Listen for new messages (daemon mode)")
    p_watch.add_argument("--json", action="store_true", help="Output JSON lines (like imsg watch --json)")

    args = parser.parse_args()

    if args.command == "setup":
        cmd_setup(args)
    elif args.command == "me":
        cmd_me(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "send":
        cmd_send(args)
    elif args.command == "notify":
        cmd_notify(args)
    elif args.command == "watch":
        cmd_watch(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
