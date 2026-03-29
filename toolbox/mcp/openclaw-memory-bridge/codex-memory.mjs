#!/usr/bin/env node

import {
  forgetMemory,
  getMemoryStats,
  listMemories,
  migrateClaudeMemories,
  recallMemories,
  storeMemory,
  updateMemory,
} from "./openclaw-memory-client.mjs";

function usage() {
  console.error(`Usage:
  node codex-memory.mjs stats [--scope <scope>] [--json]
  node codex-memory.mjs list [--scope <scope>] [--limit <n>] [--json]
  node codex-memory.mjs recall <query> [--scope <scope>] [--limit <n>] [--json]
  node codex-memory.mjs store <text> [--category <category>] [--importance <0-1>] [--scope <scope>] [--json]
  node codex-memory.mjs forget <memoryId> [--scope <scope>] [--json]
  node codex-memory.mjs update <memoryId> [--text <text>] [--category <category>] [--importance <0-1>] [--scope <scope>] [--json]
  node codex-memory.mjs migrate-claude [--dry-run] [--limit <n>]
`);
}

function parseArgs(argv) {
  const positional = [];
  const flags = {};

  for (let i = 0; i < argv.length; i += 1) {
    const current = argv[i];
    if (!current.startsWith("--")) {
      positional.push(current);
      continue;
    }

    const key = current.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      flags[key] = true;
      continue;
    }

    flags[key] = next;
    i += 1;
  }

  return { positional, flags };
}

function printResult(data, jsonMode) {
  if (jsonMode) {
    console.log(JSON.stringify(data, null, 2));
    return;
  }
  if (typeof data === "string") {
    console.log(data);
    return;
  }
  console.log(JSON.stringify(data, null, 2));
}

const { positional, flags } = parseArgs(process.argv.slice(2));
const [command, ...rest] = positional;

if (!command) {
  usage();
  process.exit(1);
}

try {
  if (command === "stats") {
    const result = await getMemoryStats({ scope: flags.scope });
    printResult(result, flags.json === true);
    process.exit(0);
  }

  if (command === "list") {
    const result = await listMemories({
      scope: flags.scope,
      limit: flags.limit || 20,
    });
    printResult(result, flags.json === true);
    process.exit(0);
  }

  if (command === "recall") {
    const query = rest.join(" ").trim();
    if (!query) throw new Error("recall requires a query");
    const result = await recallMemories({
      query,
      scope: flags.scope,
      limit: flags.limit || 5,
      category: flags.category,
    });
    printResult(result, flags.json === true);
    process.exit(0);
  }

  if (command === "store") {
    const text = rest.join(" ").trim();
    if (!text) throw new Error("store requires text");
    const result = await storeMemory({
      text,
      category: flags.category || "fact",
      importance: flags.importance,
      scope: flags.scope,
    });
    printResult(result || { stored: true }, flags.json === true);
    process.exit(0);
  }

  if (command === "forget") {
    const memoryId = rest[0];
    if (!memoryId) throw new Error("forget requires a memoryId");
    const result = await forgetMemory({ memoryId, scope: flags.scope });
    printResult(result, flags.json === true);
    process.exit(result.deleted ? 0 : 1);
  }

  if (command === "update") {
    const memoryId = rest[0];
    if (!memoryId) throw new Error("update requires a memoryId");
    const result = await updateMemory({
      memoryId,
      text: flags.text,
      category: flags.category,
      importance: flags.importance,
      scope: flags.scope,
    });
    if (!result) process.exit(1);
    printResult(result, flags.json === true);
    process.exit(0);
  }

  if (command === "migrate-claude") {
    const result = await migrateClaudeMemories({
      dryRun: flags["dry-run"] === true,
      limit: flags.limit,
    });
    printResult(result, false);
    process.exit(0);
  }

  usage();
  process.exit(1);
} catch (error) {
  console.error(error.message);
  process.exit(1);
}
