#!/usr/bin/env node

import { copyFile, readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import os from "node:os";
import path from "node:path";

import { migrateClaudeMemories } from "./openclaw-memory-client.mjs";

const args = new Set(process.argv.slice(2));
const dryRun = args.has("--dry-run");
const skipMigrate = args.has("--skip-migrate");

const home = os.homedir();
const claudeConfigPath = path.join(home, ".claude.json");
const bridgeDir = path.resolve(path.dirname(new URL(import.meta.url).pathname));
const bridgePath = path.join(bridgeDir, "claude-mcp-server.mjs");
const sdkRoot = "/Users/jerry_hu/.claude/plugins/memory-lancedb/node_modules/@modelcontextprotocol/sdk/dist/esm";
const zodRoot = "/Users/jerry_hu/.claude/plugins/memory-lancedb/node_modules/zod";

if (!existsSync(claudeConfigPath)) {
  throw new Error(`Claude config not found: ${claudeConfigPath}`);
}

const which = spawnSync("which", ["openclaw"], {
  encoding: "utf8",
  stdio: ["ignore", "pipe", "ignore"],
});
const openclawBin = which.status === 0 ? which.stdout.trim() : "openclaw";

const raw = await readFile(claudeConfigPath, "utf8");
const config = JSON.parse(raw);
const previousMemory = config?.mcpServers?.memory || null;
const backupPath = `${claudeConfigPath}.bak.${new Date().toISOString().replace(/[:.]/g, "-")}`;

const memoryEnv = {
  HOME: process.env.HOME || home,
  PATH: process.env.PATH || "",
  OPENCLAW_BIN: openclawBin,
  OPENCLAW_MEMORY_SCOPE: process.env.OPENCLAW_MEMORY_SCOPE || "agent:main",
  CLAUDE_MCP_SDK_ROOT: sdkRoot,
  CLAUDE_ZOD_ROOT: zodRoot,
};

for (const key of [
  "OPENCLAW_JINA_EMBEDDING_API_KEY_1",
  "OPENCLAW_JINA_EMBEDDING_API_KEY_2",
  "OPENCLAW_JINA_RERANK_API_KEY",
  "OPENCLAW_GATEWAY_TOKEN",
]) {
  if (process.env[key]) {
    memoryEnv[key] = process.env[key];
  }
}

const nextConfig = structuredClone(config);
nextConfig.mcpServers ||= {};
nextConfig.mcpServers.memory = {
  command: "node",
  args: [bridgePath],
  env: memoryEnv,
  type: "stdio",
};

console.log(`Claude config: ${claudeConfigPath}`);
console.log(`Backup path: ${backupPath}`);
console.log(`Bridge path: ${bridgePath}`);
console.log(`OpenClaw bin: ${openclawBin}`);
console.log("");
console.log("Existing memory server:");
console.log(JSON.stringify(previousMemory, null, 2));
console.log("");
console.log("New memory server:");
console.log(JSON.stringify(nextConfig.mcpServers.memory, null, 2));

if (dryRun) {
  console.log("");
  console.log("Dry run only. No files were changed.");
  process.exit(0);
}

await copyFile(claudeConfigPath, backupPath);
await writeFile(claudeConfigPath, `${JSON.stringify(nextConfig, null, 2)}\n`, "utf8");
console.log("");
console.log("Claude config updated.");

if (!skipMigrate) {
  console.log("");
  console.log("Running Claude -> OpenClaw memory migration...");
  const migration = await migrateClaudeMemories({ skipExisting: true });
  console.log(migration);
}
