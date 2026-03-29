#!/usr/bin/env node

import path from "node:path";
import { pathToFileURL } from "node:url";

import {
  forgetMemory,
  formatMemoryLine,
  getMemoryStats,
  recallMemories,
  storeMemory,
  updateMemory,
} from "./openclaw-memory-client.mjs";

const sdkRoot = process.env.CLAUDE_MCP_SDK_ROOT
  || "/Users/jerry_hu/.claude/plugins/memory-lancedb/node_modules/@modelcontextprotocol/sdk/dist/esm";
const zodRoot = process.env.CLAUDE_ZOD_ROOT
  || "/Users/jerry_hu/.claude/plugins/memory-lancedb/node_modules/zod";

const { McpServer } = await import(pathToFileURL(path.join(sdkRoot, "server/mcp.js")).href);
const { StdioServerTransport } = await import(pathToFileURL(path.join(sdkRoot, "server/stdio.js")).href);
const { z } = await import(pathToFileURL(path.join(zodRoot, "index.js")).href);

const CATEGORIES = ["preference", "fact", "decision", "entity", "reflection", "other"];
const server = new McpServer({
  name: "openclaw-memory-bridge",
  version: "1.0.0",
});

server.tool(
  "memory_store",
  "Store a memory into the OpenClaw memory-lancedb-pro backend.",
  {
    text: z.string().min(1).describe("Atomic memory text"),
    category: z.enum(CATEGORIES).optional().default("fact").describe("Memory category"),
    importance: z.number().min(0).max(1).optional().default(0.7).describe("Importance score 0-1"),
    scope: z.string().optional().describe("Target scope. Default uses OPENCLAW_MEMORY_SCOPE."),
  },
  async ({ text, category, importance, scope }) => {
    try {
      const entry = await storeMemory({ text, category, importance, scope });
      const suffix = entry ? ` ${formatMemoryLine(entry)}` : "";
      return {
        content: [
          {
            type: "text",
            text: `Stored memory in OpenClaw.${suffix}`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error: ${error.message}` }],
      };
    }
  },
);

server.tool(
  "memory_recall",
  "Search OpenClaw memory-lancedb-pro using hybrid retrieval, with lexical fallback if embeddings are unavailable.",
  {
    query: z.string().min(1).describe("Search query"),
    limit: z.number().min(1).max(20).optional().default(5).describe("Maximum number of results"),
    category: z.enum(CATEGORIES).optional().describe("Filter by category"),
    scope: z.string().optional().describe("Search within a specific scope"),
  },
  async ({ query, limit, category, scope }) => {
    try {
      const results = await recallMemories({ query, limit, category, scope });
      if (results.length === 0) {
        return { content: [{ type: "text", text: "No relevant memories found." }] };
      }

      const lines = results.map((result, index) => {
        const entry = result.entry || result;
        const score = Number(result.score || 0);
        return `${index + 1}. [${String(entry.id).slice(0, 8)}] score=${score.toFixed(3)} [${entry.category}:${entry.scope}]\n   ${entry.text}`;
      });

      return {
        content: [
          {
            type: "text",
            text: `Found ${results.length} memories:\n\n${lines.join("\n\n")}`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error: ${error.message}` }],
      };
    }
  },
);

server.tool(
  "memory_forget",
  "Delete a memory from the OpenClaw backend by ID or by query.",
  {
    memoryId: z.string().optional().describe("Memory ID or 8+ char prefix"),
    query: z.string().optional().describe("Search query to locate the memory"),
    scope: z.string().optional().describe("Scope for lookup and deletion"),
  },
  async ({ memoryId, query, scope }) => {
    try {
      if (memoryId) {
        const result = await forgetMemory({ memoryId, scope });
        return {
          content: [{
            type: "text",
            text: result.deleted
              ? `Deleted memory ${String(result.entry.id).slice(0, 8)}.`
              : `Memory ${memoryId.slice(0, 8)} not found.`,
          }],
        };
      }

      if (query) {
        const matches = await recallMemories({ query, limit: 3, scope });
        if (matches.length === 0) {
          return { content: [{ type: "text", text: "No matching memories found." }] };
        }

        if (matches.length === 1 && Number(matches[0].score || 0) > 0.9) {
          const entry = matches[0].entry || matches[0];
          await forgetMemory({ memoryId: entry.id, scope });
          return {
            content: [{
              type: "text",
              text: `Deleted memory ${String(entry.id).slice(0, 8)}: "${String(entry.text).slice(0, 100)}"`,
            }],
          };
        }

        const lines = matches.map((match, index) => {
          const entry = match.entry || match;
          return `${index + 1}. [${String(entry.id).slice(0, 8)}] score=${Number(match.score || 0).toFixed(3)} ${String(entry.text).slice(0, 120)}`;
        });
        return {
          content: [{
            type: "text",
            text: `Multiple matches found. Specify memoryId to delete:\n\n${lines.join("\n")}`,
          }],
        };
      }

      return { content: [{ type: "text", text: "Provide either memoryId or query." }] };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error: ${error.message}` }],
      };
    }
  },
);

server.tool(
  "memory_update",
  "Update a memory in the OpenClaw backend while preserving its ID and timestamp.",
  {
    memoryId: z.string().describe("Memory ID or 8+ char prefix"),
    text: z.string().optional().describe("New text content"),
    importance: z.number().min(0).max(1).optional().describe("New importance score"),
    category: z.enum(CATEGORIES).optional().describe("New category"),
    scope: z.string().optional().describe("Scope containing the memory"),
  },
  async ({ memoryId, text, importance, category, scope }) => {
    try {
      if (text === undefined && importance === undefined && category === undefined) {
        return { content: [{ type: "text", text: "No updates provided." }] };
      }

      const updated = await updateMemory({
        memoryId,
        text,
        importance,
        category,
        scope,
      });

      if (!updated) {
        return { content: [{ type: "text", text: `Memory ${memoryId.slice(0, 8)} not found.` }] };
      }

      return {
        content: [{
          type: "text",
          text: `Updated memory ${String(updated.id).slice(0, 8)} [${updated.category}] importance=${updated.importance}`,
        }],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error: ${error.message}` }],
      };
    }
  },
);

server.tool(
  "memory_stats",
  "Show summary stats from the OpenClaw memory backend.",
  {
    scope: z.string().optional().describe("Optional scope filter"),
  },
  async ({ scope }) => {
    try {
      const stats = await getMemoryStats({ scope });
      return {
        content: [{
          type: "text",
          text: JSON.stringify(stats, null, 2),
        }],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error: ${error.message}` }],
      };
    }
  },
);

const transport = new StdioServerTransport();
await server.connect(transport);
