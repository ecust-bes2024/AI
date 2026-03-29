#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


DEFAULT_CONFIG = Path("/Users/jerry_hu/AI/toolbox/skills/hooks-codex/templates/hooks-codex.example.toml")


def load_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.payload_file:
        return json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
    if args.payload_json:
        return json.loads(args.payload_json)
    raw = sys.stdin.read().strip()
    return json.loads(raw) if raw else {}


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("rb") as handle:
        return tomllib.load(handle)


def matcher_matches(entry: dict[str, Any], payload: dict[str, Any]) -> bool:
    matcher = entry.get("matcher", {}) or {}
    event_name = payload.get("hook_event_name", "")
    tool_name = str(payload.get("tool_name", ""))

    raw_matcher = matcher.get("matcher")
    if raw_matcher and raw_matcher != "*":
        target = tool_name or str(payload.get("name") or payload.get("agent_type") or event_name)
        if not re.search(str(raw_matcher), target):
            return False

    exact_tool = matcher.get("tool_name")
    if exact_tool and tool_name != str(exact_tool):
        return False

    tool_regex = matcher.get("tool_name_regex")
    if tool_regex and not re.search(str(tool_regex), tool_name):
        return False

    return True


def iter_event_hooks(config: dict[str, Any], event_key: str) -> list[dict[str, Any]]:
    hooks = (((config or {}).get("hooks") or {}).get(event_key) or [])
    if isinstance(hooks, dict):
        return [hooks]
    return hooks


def parse_hook_output(stdout: str) -> dict[str, Any]:
    text = stdout.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    raise ValueError("Hook output was not valid JSON.")


def run_command_hook(entry: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    command = entry.get("command")
    if not command:
        raise ValueError("Command hook missing command.")
    if isinstance(command, str):
        cmd = [command]
    else:
        cmd = [str(part) for part in command]

    timeout = entry.get("timeout")
    proc = subprocess.run(
        cmd,
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        timeout=float(timeout) if timeout is not None else None,
        check=False,
    )

    if proc.returncode != 0:
        return {
            "ok": False,
            "decision": "deny" if proc.returncode == 2 else "error",
            "reason": proc.stderr.strip() or f"hook exited with code {proc.returncode}",
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    parsed = parse_hook_output(proc.stdout)
    parsed.setdefault("ok", True)
    parsed["stdout"] = proc.stdout
    parsed["stderr"] = proc.stderr
    return parsed


def merge_hook_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    reserved = {"ok", "decision", "reason", "additionalContext", "updatedInput", "stdout", "stderr"}
    merged: dict[str, Any] = {
        "ok": True,
        "decision": "allow",
        "reason": "",
        "additionalContext": [],
        "updatedInput": None,
        "results": results,
    }

    for result in results:
        decision = str(result.get("decision", "allow")).lower()
        ok = bool(result.get("ok", decision != "deny"))

        if result.get("additionalContext"):
            merged["additionalContext"].append(str(result["additionalContext"]))

        if result.get("updatedInput") is not None:
            merged["updatedInput"] = result["updatedInput"]

        for key, value in result.items():
            if key not in reserved:
                merged[key] = value

        if (not ok) or decision in {"deny", "block", "ask", "error"}:
            merged["ok"] = False
            merged["decision"] = "deny" if decision in {"deny", "block"} else decision
            merged["reason"] = str(result.get("reason") or "blocked by hook")
            break

    if not merged["additionalContext"]:
        merged.pop("additionalContext")
    else:
        merged["additionalContext"] = "\n".join(merged["additionalContext"])

    if merged["updatedInput"] is None:
        merged.pop("updatedInput")

    return merged


def command_dispatch(args: argparse.Namespace) -> int:
    payload = load_payload(args)
    event_key = args.event
    config = load_config(args.config)
    hooks = [
        entry for entry in iter_event_hooks(config, event_key)
        if matcher_matches(entry, payload)
    ]

    results = []
    for entry in hooks:
        if str(entry.get("type", "command")) != "command":
            continue
        results.append(run_command_hook(entry, payload))

    merged = merge_hook_results(results)
    print(json.dumps(merged, ensure_ascii=False, indent=2))
    return 0 if merged.get("ok", True) else 2


def command_emit_payload(args: argparse.Namespace) -> int:
    payload = load_payload(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="hooks-codex minimal command hook runtime")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dispatch = subparsers.add_parser("dispatch")
    dispatch.add_argument("--config", default=str(DEFAULT_CONFIG))
    dispatch.add_argument("--event", required=True)
    dispatch.add_argument("--payload-file")
    dispatch.add_argument("--payload-json")
    dispatch.set_defaults(handler=command_dispatch)

    emit = subparsers.add_parser("emit-payload")
    emit.add_argument("--payload-file")
    emit.add_argument("--payload-json")
    emit.set_defaults(handler=command_emit_payload)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
