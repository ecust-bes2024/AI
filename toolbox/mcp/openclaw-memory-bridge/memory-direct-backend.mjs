#!/usr/bin/env node

import os from "node:os";
import path from "node:path";

const DB_PATH = process.env.OPENCLAW_MEMORY_DB_PATH
  || path.join(os.homedir(), ".openclaw", "memory", "lancedb-pro");
const LANCEDB_MODULE = process.env.LANCEDB_MODULE
  || "/Users/jerry_hu/.claude/plugins/memory-lancedb/node_modules/@lancedb/lancedb/dist/index.js";
const CACHE_TTL_MS = Number.parseInt(process.env.OPENCLAW_MEMORY_CACHE_TTL_MS || "1500", 10);

const lancedb = await import(LANCEDB_MODULE);

let db;
let table;
let cache = {
  loadedAt: 0,
  memories: [],
};

function clampInt(value, min, max) {
  const parsed = Number.parseInt(String(value), 10);
  if (!Number.isFinite(parsed)) return min;
  return Math.max(min, Math.min(max, Math.trunc(parsed)));
}

function normalizeReadScope(scope) {
  return typeof scope === "string" && scope.trim() ? scope.trim() : undefined;
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

function lexicalScore(text, query, timestamp) {
  const haystack = String(text || "").toLowerCase();
  const needle = String(query || "").trim().toLowerCase();
  if (!needle) return 0;

  let matched = false;
  let score = 0;
  if (haystack.includes(needle)) {
    matched = true;
    score += Math.min(0.8, 0.25 + needle.length / 40);
  }

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

async function ensureTable() {
  if (table) return table;
  db = await lancedb.connect(DB_PATH);
  table = await db.openTable("memories");
  return table;
}

function filterByScope(memories, scope) {
  if (!scope) return memories;
  return memories.filter((entry) => entry.scope === scope);
}

function filterByCategory(memories, category) {
  if (!category) return memories;
  return memories.filter((entry) => entry.category === category);
}

export async function loadMemories(force = false) {
  const now = Date.now();
  if (!force && cache.loadedAt > 0 && now - cache.loadedAt < CACHE_TTL_MS) {
    return cache.memories;
  }

  const activeTable = await ensureTable();
  const rows = await activeTable.query().toArray();
  rows.sort((left, right) => Number(right.timestamp || 0) - Number(left.timestamp || 0));
  cache = {
    loadedAt: now,
    memories: rows.map((row) => ({
      id: String(row.id),
      text: String(row.text || ""),
      vector: Array.isArray(row.vector) ? row.vector : [],
      category: String(row.category || "other"),
      scope: String(row.scope || "global"),
      importance: Number(row.importance ?? 0.7),
      timestamp: Number(row.timestamp ?? 0),
      metadata: typeof row.metadata === "string" ? row.metadata : JSON.stringify(row.metadata ?? {}),
    })),
  };
  return cache.memories;
}

export async function directStats(options = {}) {
  const scope = normalizeReadScope(options.scope);
  const category = typeof options.category === "string" ? options.category : undefined;
  const memories = await loadMemories(options.forceReload === true);
  const filtered = filterByCategory(filterByScope(memories, scope), category);
  const scopeCounts = {};
  const categoryCounts = {};
  for (const entry of filtered) {
    scopeCounts[entry.scope] = (scopeCounts[entry.scope] || 0) + 1;
    categoryCounts[entry.category] = (categoryCounts[entry.category] || 0) + 1;
  }
  return {
    memory: {
      totalCount: filtered.length,
      scopeCounts,
      categoryCounts,
    },
    cache: {
      loadedAt: cache.loadedAt,
      ttlMs: CACHE_TTL_MS,
    },
  };
}

export async function directList(options = {}) {
  const scope = normalizeReadScope(options.scope);
  const category = typeof options.category === "string" ? options.category : undefined;
  const memories = await loadMemories(options.forceReload === true);
  const filtered = filterByCategory(filterByScope(memories, scope), category);
  const offset = clampInt(options.offset ?? 0, 0, 1000000);
  const limit = clampInt(options.limit ?? 20, 1, 10000);
  return filtered.slice(offset, offset + limit);
}

export async function directRecall(options = {}) {
  const scope = normalizeReadScope(options.scope);
  const category = typeof options.category === "string" ? options.category : undefined;
  const memories = await loadMemories(options.forceReload === true);
  const filtered = filterByCategory(filterByScope(memories, scope), category);
  const expanded = expandRecallQuery(options.query);
  const limit = clampInt(options.limit ?? 5, 1, 100);

  return filtered
    .map((entry) => ({
      entry,
      score: lexicalScore(entry.text, expanded, entry.timestamp),
      sources: {
        bm25: { score: 0.5, rank: 0 },
        fused: { score: 0.5 },
      },
    }))
    .filter((result) => result.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, limit);
}
