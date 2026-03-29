#!/usr/bin/env node

import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { spawn, spawnSync } from "node:child_process";
import { homedir, tmpdir } from "node:os";
import path from "node:path";
import {
  directList,
  directRecall,
  directStats,
} from "./memory-direct-backend.mjs";

const DEFAULT_WRITE_SCOPE = process.env.OPENCLAW_MEMORY_SCOPE || "agent:main";
const DEFAULT_FALLBACK_LIMIT = Number.parseInt(
  process.env.OPENCLAW_BRIDGE_FALLBACK_LIMIT || "300",
  10,
);
const DEFAULT_OPENCLAW_TIMEOUT_MS = Number.parseInt(
  process.env.OPENCLAW_BRIDGE_TIMEOUT_MS || "15000",
  10,
);
const REMOTE_SERVER_URL = process.env.OPENCLAW_MEMORY_SERVER_URL?.trim() || "";
const AUTO_REMOTE_SERVER_URL = process.env.OPENCLAW_MEMORY_SERVER_AUTO_URL?.trim() || "http://127.0.0.1:4312";
const AUTO_REMOTE_SERVER_ENABLED = process.env.OPENCLAW_MEMORY_SERVER_AUTO !== "0";
const REMOTE_SERVER_TOKEN = process.env.OPENCLAW_MEMORY_SERVER_TOKEN?.trim() || "";
const REMOTE_SERVER_FOR_READS = process.env.OPENCLAW_MEMORY_SERVER_READS === "1";
const REMOTE_SERVER_TIMEOUT_MS = Number.parseInt(
  process.env.OPENCLAW_MEMORY_SERVER_TIMEOUT_MS || "20000",
  10,
);
const REMOTE_SERVER_HEALTH_TIMEOUT_MS = Number.parseInt(
  process.env.OPENCLAW_MEMORY_SERVER_HEALTH_TIMEOUT_MS || "400",
  10,
);
let remoteServerUrlPromise = null;

function resolveOpenClawBin() {
  if (process.env.OPENCLAW_BIN?.trim()) return process.env.OPENCLAW_BIN.trim();

  const which = spawnSync("which", ["openclaw"], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "ignore"],
  });
  const found = which.status === 0 ? which.stdout.trim() : "";
  return found || "openclaw";
}

const OPENCLAW_BIN = resolveOpenClawBin();

export class OpenClawCommandError extends Error {
  constructor(message, details) {
    super(message);
    this.name = "OpenClawCommandError";
    this.details = details;
  }
}

function normalizeReadScope(scope) {
  return typeof scope === "string" && scope.trim() ? scope.trim() : undefined;
}

function normalizeWriteScope(scope) {
  return typeof scope === "string" && scope.trim() ? scope.trim() : DEFAULT_WRITE_SCOPE;
}

function expandRecallQuery(query) {
  const original = String(query || "").trim();
  if (!original) return original;

  const expansions = new Set([original]);
  const lower = original.toLowerCase();

  const mapped = [];
  if (/\bwho\b|\buser\b|\bidentity\b|\bname\b/.test(lower)) mapped.push("用户 身份 名字 Jerry Hu");
  if (/\bpreference\b|\bpreferences\b|\bcall\b|\baddress\b/.test(lower)) mapped.push("称呼 偏好 哥");
  if (/你是谁|我是谁|身份|称呼|偏好|名字|哥|jerry/.test(original)) mapped.push("用户 身份 称呼 偏好 Jerry Hu 哥");

  for (const item of mapped) expansions.add(item);
  return Array.from(expansions).join(" ");
}

function shouldPreferLexicalRecall(query) {
  const text = String(query || "").trim();
  if (!text) return false;
  if (/你是谁|我是谁|身份|称呼|偏好|名字|哥|Jerry Hu/i.test(text)) return true;
  if (/\bwho\b|\bidentity\b|\bname\b|\bpreference\b|\bpreferences\b|\bcall\b|\baddress\b/i.test(text)) return true;
  return false;
}

function clampInt(value, min, max) {
  const parsed = Number.parseInt(String(value), 10);
  if (!Number.isFinite(parsed)) return min;
  return Math.max(min, Math.min(max, Math.trunc(parsed)));
}

function normalizeImportance(value, fallback = 0.7) {
  if (value === undefined || value === null || value === "") return fallback;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(0, Math.min(1, parsed));
}

function jsonStartLooksValid(text, index) {
  const current = text[index];
  const next = text.slice(index + 1).trimStart()[0];
  if (current === "{") return next === '"' || next === "}";
  if (current !== "[") return false;
  return ['"', "{", "[", "]", "-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "t", "f", "n"].includes(next);
}

function extractJsonPayload(text) {
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if ((ch === "{" || ch === "[") && jsonStartLooksValid(text, i)) {
      const candidate = text.slice(i).trim();
      try {
        return JSON.parse(candidate);
      } catch {
        // keep scanning
      }
    }
  }
  return null;
}

function summarizeCommandFailure(details) {
  const combined = `${details.stdout || ""}\n${details.stderr || ""}`.trim();
  if (!combined) return `openclaw command failed with code ${details.code}`;
  const lastLines = combined
    .split(/\r?\n/)
    .filter(Boolean)
    .slice(-8)
    .join("\n");
  return `openclaw command failed with code ${details.code}\n${lastLines}`;
}

async function probeRemoteServer(baseUrl) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REMOTE_SERVER_HEALTH_TIMEOUT_MS);
  try {
    const response = await fetch(new URL("/health", baseUrl), {
      method: "GET",
      signal: controller.signal,
    });
    if (!response.ok) return "";
    const payload = await response.json().catch(() => null);
    return payload?.ok ? baseUrl : "";
  } catch {
    return "";
  } finally {
    clearTimeout(timer);
  }
}

async function resolveRemoteServerUrl() {
  if (REMOTE_SERVER_URL) return REMOTE_SERVER_URL;
  if (!AUTO_REMOTE_SERVER_ENABLED) return "";
  if (!remoteServerUrlPromise) {
    remoteServerUrlPromise = probeRemoteServer(AUTO_REMOTE_SERVER_URL);
  }
  return await remoteServerUrlPromise;
}

async function shouldUseRemoteServer() {
  return Boolean(await resolveRemoteServerUrl());
}

async function shouldUseRemoteServerForReads() {
  if (!REMOTE_SERVER_FOR_READS) return false;
  return await shouldUseRemoteServer();
}

async function buildRemoteUrl(pathname) {
  const baseUrl = await resolveRemoteServerUrl();
  if (!baseUrl) throw new Error("Remote memory server is not available.");
  return new URL(pathname, baseUrl).href;
}

async function callRemoteServer(method, params = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REMOTE_SERVER_TIMEOUT_MS);

  try {
    const headers = {
      "content-type": "application/json",
    };
    if (REMOTE_SERVER_TOKEN) {
      headers.authorization = `Bearer ${REMOTE_SERVER_TOKEN}`;
    }

    const rpcUrl = await buildRemoteUrl("/rpc");
    const response = await fetch(rpcUrl, {
      method: "POST",
      headers,
      body: JSON.stringify({ method, params }),
      signal: controller.signal,
    });

    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      const message = payload?.error || `Remote memory server returned HTTP ${response.status}`;
      throw new Error(message);
    }
    if (!payload?.ok) {
      throw new Error(payload?.error || "Remote memory server returned an invalid payload.");
    }
    return payload.result;
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new Error(`Remote memory server timed out after ${REMOTE_SERVER_TIMEOUT_MS}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export async function runOpenClaw(args, options = {}) {
  const finalArgs = ["--log-level", "silent", ...args];
  const env = { ...process.env, NO_COLOR: "1" };
  const timeoutMs = Number.isFinite(options.timeoutMs)
    ? Number(options.timeoutMs)
    : DEFAULT_OPENCLAW_TIMEOUT_MS;

  return await new Promise((resolve, reject) => {
    const child = spawn(OPENCLAW_BIN, finalArgs, {
      env,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";
    let settled = false;
    let timer = null;

    if (timeoutMs > 0) {
      timer = setTimeout(() => {
        if (settled) return;
        settled = true;
        child.kill("SIGTERM");
        reject(
          new OpenClawCommandError(`openclaw command timed out after ${timeoutMs}ms`, {
            args: finalArgs,
            code: null,
            stdout,
            stderr,
          }),
        );
      }, timeoutMs);
    }

    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });

    child.once("error", (error) => {
      if (settled) return;
      settled = true;
      if (timer) clearTimeout(timer);
      reject(
        new OpenClawCommandError(`failed to spawn ${OPENCLAW_BIN}: ${error.message}`, {
          args: finalArgs,
          code: null,
          stdout,
          stderr,
        }),
      );
    });

    child.once("close", (code) => {
      if (settled) return;
      settled = true;
      if (timer) clearTimeout(timer);
      const details = { args: finalArgs, code, stdout, stderr };
      if (code !== 0 && !options.allowFailure) {
        reject(new OpenClawCommandError(summarizeCommandFailure(details), details));
        return;
      }
      resolve(details);
    });
  });
}

function lexicalScore(text, query, timestamp) {
  const haystack = text.toLowerCase();
  const needle = query.trim().toLowerCase();
  if (!needle) return 0;

  let matched = false;
  let score = 0;
  if (haystack.includes(needle)) score += Math.min(0.8, 0.25 + needle.length / 40);
  if (haystack.includes(needle)) matched = true;

  const tokens = needle.includes(" ")
    ? needle.split(/\s+/).filter((token) => token.length > 1)
    : [needle];
  for (const token of tokens) {
    if (haystack.includes(token)) {
      matched = true;
      score += Math.min(0.15, token.length / 50);
    }
  }

  if (!matched) return 0;

  const ageDays = Math.max(0, (Date.now() - Number(timestamp || Date.now())) / 86_400_000);
  score += Math.max(0, 0.1 - ageDays / 3650);
  return Math.min(score, 0.99);
}

export async function listMemories(options = {}) {
  if (await shouldUseRemoteServerForReads()) {
    return await callRemoteServer("list", {
      scope: normalizeReadScope(options.scope),
      category: options.category,
      limit: clampInt(options.limit ?? 20, 1, 1000),
      offset: clampInt(options.offset ?? 0, 0, 1000000),
      forceReload: options.forceReload === true,
    });
  }
  return await directList({
    scope: normalizeReadScope(options.scope),
    category: options.category,
    limit: clampInt(options.limit ?? 20, 1, 1000),
    offset: clampInt(options.offset ?? 0, 0, 1000000),
    forceReload: options.forceReload === true,
  });
}

export async function getMemoryStats(options = {}) {
  if (await shouldUseRemoteServerForReads()) {
    return await callRemoteServer("stats", {
      scope: normalizeReadScope(options.scope),
      category: options.category,
      forceReload: options.forceReload === true,
    });
  }
  const payload = await directStats({
    scope: normalizeReadScope(options.scope),
    category: options.category,
    forceReload: options.forceReload === true,
  });
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("Failed to parse memory stats payload.");
  }
  return payload;
}

export async function lexicalRecall(options) {
  if (await shouldUseRemoteServerForReads()) {
    return await callRemoteServer("recall", {
      scope: normalizeReadScope(options.scope),
      category: options.category,
      query: expandRecallQuery(options.query),
      limit: clampInt(options.limit ?? 5, 1, 20),
      forceReload: options.forceReload === true,
    });
  }
  return await directRecall({
    scope: normalizeReadScope(options.scope),
    category: options.category,
    query: expandRecallQuery(options.query),
    limit: clampInt(options.limit ?? 5, 1, 20),
    forceReload: options.forceReload === true,
  });
}

export async function recallMemories(options) {
  if (await shouldUseRemoteServerForReads()) {
    return await callRemoteServer("recall", {
      query: options.query,
      scope: normalizeReadScope(options.scope),
      limit: clampInt(options.limit ?? 5, 1, 20),
      category: options.category,
      forceReload: options.forceReload === true,
    });
  }

  if (shouldPreferLexicalRecall(options.query)) {
    return await lexicalRecall(options);
  }

  const query = expandRecallQuery(options.query);
  const args = [
    "memory-pro",
    "search",
    query,
    "--limit",
    String(clampInt(options.limit ?? 5, 1, 20)),
    "--json",
  ];
  const scope = normalizeReadScope(options.scope);
  if (scope) args.push("--scope", scope);
  if (options.category) args.push("--category", options.category);

  try {
    const result = await runOpenClaw(args);
    const payload = extractJsonPayload(result.stdout) ?? extractJsonPayload(result.stderr);
    if (!Array.isArray(payload)) {
      throw new Error("Failed to parse memory search JSON.");
    }
    return payload;
  } catch (error) {
    const text = error instanceof OpenClawCommandError
      ? `${error.message}\n${error.details.stdout}\n${error.details.stderr}`
      : String(error);
    if (!/embedding|Connection error|fetch failed|Search failed|timed out/i.test(text)) {
      throw error;
    }
    return await lexicalRecall(options);
  }
}

export async function resolveMemory(memoryId, options = {}) {
  const scope = normalizeReadScope(options.scope);
  const memories = await listMemories({
    scope,
    limit: clampInt(options.limit ?? 1000, 1, 10000),
    forceReload: options.forceReload === true,
  });
  const target = String(memoryId || "").trim();
  if (!target) return null;

  return (
    memories.find((entry) => entry.id === target)
    || memories.find((entry) => target.length >= 8 && String(entry.id).startsWith(target))
    || null
  );
}

async function withImportFile(memories, callback) {
  const dir = await mkdtemp(path.join(tmpdir(), "openclaw-memory-bridge-"));
  const filePath = path.join(dir, "memories.json");

  try {
    await writeFile(
      filePath,
      JSON.stringify(
        {
          version: "1.0",
          exportedAt: new Date().toISOString(),
          count: memories.length,
          memories,
        },
        null,
        2,
      ),
      "utf8",
    );
    return await callback(filePath);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

export async function importMemories(memories, options = {}) {
  const scope = normalizeWriteScope(options.scope);

  if (await shouldUseRemoteServer()) {
    return await callRemoteServer("import", {
      memories,
      scope,
      dryRun: options.dryRun === true,
    });
  }

  try {
    return await withImportFile(memories, async (filePath) => {
      const args = ["memory-pro", "import", filePath, "--scope", scope];
      if (options.dryRun) args.push("--dry-run");
      const result = await runOpenClaw(args);
      return result.stdout.trim() || result.stderr.trim() || "Import completed.";
    });
  } catch (error) {
    if (
      error instanceof OpenClawCommandError
      && /timed out/i.test(error.message)
    ) {
      throw new Error(
        "Memory write timed out while calling openclaw. The memory-pro import may be slow, or the current environment may still be unable to access the OpenClaw DB path.",
      );
    }
    throw error;
  }
}

export async function storeMemory(options) {
  const scope = normalizeWriteScope(options.scope);
  const category = options.category || "fact";
  const importance = normalizeImportance(options.importance, 0.7);
  const text = String(options.text || "").trim();
  if (!text) throw new Error("text is required");

  await importMemories([
    {
      text,
      category,
      importance,
      metadata: "{}",
    },
  ], { scope });

  const recent = await listMemories({ scope, limit: 50 });
  return recent.find((entry) => entry.text === text && entry.category === category) || null;
}

export async function forgetMemory(options) {
  if (await shouldUseRemoteServer()) {
    return await callRemoteServer("forget", {
      memoryId: options.memoryId,
      scope: normalizeReadScope(options.scope),
    });
  }

  const scope = normalizeReadScope(options.scope);
  const resolved = await resolveMemory(options.memoryId, { scope });
  if (!resolved) return { deleted: false, entry: null };

  const deleteScope = resolved.scope || scope;
  const args = ["memory-pro", "delete", resolved.id];
  if (deleteScope) args.push("--scope", deleteScope);
  await runOpenClaw(args);
  return { deleted: true, entry: resolved };
}

export async function updateMemory(options) {
  if (await shouldUseRemoteServer()) {
    return await callRemoteServer("update", {
      memoryId: options.memoryId,
      text: options.text,
      category: options.category,
      importance: options.importance,
      scope: normalizeReadScope(options.scope),
    });
  }

  const scope = normalizeReadScope(options.scope);
  const existing = await resolveMemory(options.memoryId, { scope });
  if (!existing) return null;

  const updated = {
    ...existing,
    text: options.text !== undefined ? String(options.text).trim() : existing.text,
    importance: options.importance !== undefined
      ? normalizeImportance(options.importance, existing.importance)
      : existing.importance,
    category: options.category !== undefined ? options.category : existing.category,
    scope: existing.scope,
  };

  if (!updated.text) throw new Error("updated text cannot be empty");

  const deleteArgs = ["memory-pro", "delete", existing.id];
  if (existing.scope) deleteArgs.push("--scope", existing.scope);
  await runOpenClaw(deleteArgs);

  try {
    await importMemories([updated], { scope: existing.scope });
  } catch (error) {
    await importMemories([existing], { scope: existing.scope }).catch(() => {});
    throw error;
  }

  return await resolveMemory(existing.id, { scope: existing.scope, forceReload: true });
}

export async function migrateClaudeMemories(options = {}) {
  const sourceDb = options.sourceDb || path.join(homedir(), ".claude", "memory", "lancedb");
  const args = ["memory-pro", "reembed", "--source-db", sourceDb];
  if (options.skipExisting !== false) args.push("--skip-existing");
  if (options.dryRun) args.push("--dry-run");
  if (options.limit) args.push("--limit", String(clampInt(options.limit, 1, 1000000)));

  const result = await runOpenClaw(args, { allowFailure: true });
  if (result.code !== 0) {
    throw new OpenClawCommandError(summarizeCommandFailure(result), result);
  }
  return result.stdout.trim() || result.stderr.trim() || "Migration completed.";
}

export function formatMemoryLine(entry) {
  return `[${String(entry.id).slice(0, 8)}] [${entry.category}:${entry.scope}] ${entry.text}`;
}

export async function maybeReadJsonFile(filePath) {
  const content = await readFile(filePath, "utf8");
  return JSON.parse(content);
}
