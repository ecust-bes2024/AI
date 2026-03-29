# OpenClaw Memory Bridge

This directory makes `memory-lancedb-pro` the single memory backend for:

- OpenClaw
- Claude Code, via a local MCP adapter
- Codex, via a local CLI bridge

## Files

- `claude-mcp-server.mjs`
  Claude-facing MCP server. It exposes `memory_store`, `memory_recall`, `memory_forget`, `memory_update`, and `memory_stats`, but delegates all persistence to `openclaw memory-pro`.
- `codex-memory.mjs`
  Local CLI for Codex-side memory operations.
- `memory-direct-backend.mjs`
  Fast read path for `stats/list/recall`. It reads LanceDB directly in-process instead of spawning `openclaw`.
- `memory-http-server.mjs`
  Localhost HTTP bridge for running memory operations outside the Codex sandbox.
- `start-memory-http-server.sh`
  Small launcher for the HTTP bridge.
- `install-claude-adapter.mjs`
  Repoints `~/.claude.json` to the bridge and optionally migrates old Claude memories into OpenClaw.
- `openclaw-memory-client.mjs`
  Shared client. Reads go through the direct backend by default; writes can be delegated to a localhost HTTP bridge via `OPENCLAW_MEMORY_SERVER_URL`.

## Quick Use

Install the Claude adapter:

```bash
node /Users/jerry_hu/AI/openclaw-memory-bridge/install-claude-adapter.mjs
```

Dry run:

```bash
node /Users/jerry_hu/AI/openclaw-memory-bridge/install-claude-adapter.mjs --dry-run
```

Use the Codex bridge:

```bash
node /Users/jerry_hu/AI/toolbox/mcp/openclaw-memory-bridge/codex-memory.mjs stats --json
node /Users/jerry_hu/AI/toolbox/mcp/openclaw-memory-bridge/codex-memory.mjs recall "哥" --json
```

## Running Writes Outside The Sandbox

When Codex can read the memory DB but cannot write `~/.openclaw/...`, run the HTTP bridge in your normal macOS shell:

```bash
nohup /Users/jerry_hu/AI/toolbox/mcp/openclaw-memory-bridge/start-memory-http-server.sh \
  >/tmp/openclaw-memory-http.log 2>&1 &
```

Then point Codex-side commands at it:

```bash
export OPENCLAW_MEMORY_SERVER_URL=http://127.0.0.1:4312
./codex-memory store "test memory" --category other --json
```

Notes:

- Reads still use the fast local direct backend by default.
- Writes (`store`, `forget`, `update`) use the HTTP bridge when `OPENCLAW_MEMORY_SERVER_URL` is set.
- Set `OPENCLAW_MEMORY_SERVER_TOKEN` on both sides if you want a bearer token.
- Set `OPENCLAW_MEMORY_SERVER_READS=1` only if you explicitly want `stats/list/recall` to go through the HTTP bridge too.

## Running As A launchd Agent

If you want the localhost memory bridge to survive reboots and login sessions, install it as a user LaunchAgent from your normal macOS shell:

```bash
/Users/jerry_hu/AI/toolbox/mcp/openclaw-memory-bridge/install-launch-agent.sh
```

Useful companion commands:

```bash
/Users/jerry_hu/AI/toolbox/mcp/openclaw-memory-bridge/status-launch-agent.sh
/Users/jerry_hu/AI/toolbox/mcp/openclaw-memory-bridge/uninstall-launch-agent.sh
```

Notes:

- Default label: `com.jerryhu.openclaw-memory-http`
- Default port: `4312`
- Logs: `~/Library/Logs/openclaw-memory-bridge/`
- The installer auto-detects the current `node` path and writes a plist into `~/Library/LaunchAgents/`
- If your Node path changes later, rerun the installer so launchd picks up the new absolute path
