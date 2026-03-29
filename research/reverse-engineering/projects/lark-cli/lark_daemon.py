#!/usr/bin/env python3
"""
lark-cli daemon — WebSocket listener that outputs JSON lines.
Similar to `imsg watch --json`.

Output format (one JSON per line):
  {"from_id":"123","chat_id":"456","chat_type":1,"content":"hello","from_name":"张三","is_from_me":false}
"""
import asyncio
import json
import sys
import signal
import time

import websockets

from lark_proto import extract_packet_sid, build_ack_frame, decode_ws_message


async def watch(api, output_json=False):
    """Connect to WebSocket and stream incoming messages."""
    me_id = api.me_id
    ws_url = api.build_ws_url()

    # Name cache to avoid repeated lookups
    name_cache = {}

    def resolve_name(from_id, chat_id):
        if from_id in name_cache:
            return name_cache[from_id]
        try:
            name = api.get_user_name(from_id, chat_id)
        except Exception:
            name = None
        name_cache[from_id] = name or from_id
        return name_cache[from_id]

    def resolve_group(chat_id):
        if chat_id in name_cache:
            return name_cache[chat_id]
        try:
            name = api.get_group_name(chat_id)
        except Exception:
            name = None
        name_cache[chat_id] = name or chat_id
        return name_cache[chat_id]

    while True:
        try:
            if not output_json:
                print("[lark watch] Connecting...", file=sys.stderr)
            async with websockets.connect(ws_url) as ws:
                if not output_json:
                    print("[lark watch] Connected. Listening for messages...", file=sys.stderr)
                async for raw in ws:
                    try:
                        # ACK
                        sid = extract_packet_sid(raw)
                        await ws.send(build_ack_frame(sid))

                        # Decode
                        msg = decode_ws_message(raw)
                        if not msg or not msg.get("content"):
                            continue

                        is_from_me = (str(msg["from_id"]) == me_id)
                        from_name = resolve_name(msg["from_id"], msg["chat_id"]) if msg["from_id"] else None
                        # chat_type: 1=P2P, 2=GROUP
                        is_group = (msg.get("chat_type") == 2)
                        group_name = resolve_group(msg["chat_id"]) if is_group else None

                        out = {
                            "from_id": msg["from_id"],
                            "from_name": from_name,
                            "chat_id": msg["chat_id"],
                            "chat_type": "group" if is_group else "p2p",
                            "group_name": group_name,
                            "content": msg["content"],
                            "is_from_me": is_from_me,
                            "timestamp": int(time.time()),
                        }

                        if output_json:
                            print(json.dumps(out, ensure_ascii=False), flush=True)
                        else:
                            tag = f"[{group_name}]" if group_name else ""
                            me_tag = "(me)" if is_from_me else ""
                            print(f"{tag} {from_name}{me_tag}: {msg['content']}")

                    except Exception:
                        continue

        except (websockets.ConnectionClosed, ConnectionError, OSError) as e:
            if not output_json:
                print(f"[lark watch] Disconnected: {e}. Reconnecting in 5s...", file=sys.stderr)
            await asyncio.sleep(5)
            # Rebuild WS URL (ticket may expire)
            try:
                ws_url = api.build_ws_url()
            except Exception:
                pass
        except asyncio.CancelledError:
            break


def run_daemon(api, output_json=False):
    """Entry point for the daemon."""
    loop = asyncio.new_event_loop()

    def shutdown(*_):
        for task in asyncio.all_tasks(loop):
            task.cancel()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        loop.run_until_complete(watch(api, output_json))
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        loop.close()
        if not output_json:
            print("\n[lark watch] Stopped.", file=sys.stderr)
