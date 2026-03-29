#!/usr/bin/env node

import http from "node:http";

delete process.env.OPENCLAW_MEMORY_SERVER_URL;
delete process.env.OPENCLAW_MEMORY_SERVER_AUTO_URL;
process.env.OPENCLAW_MEMORY_SERVER_AUTO = "0";

const {
  forgetMemory,
  getMemoryStats,
  importMemories,
  listMemories,
  recallMemories,
  storeMemory,
  updateMemory,
} = await import("./openclaw-memory-client.mjs");

const HOST = process.env.OPENCLAW_MEMORY_SERVER_HOST || "127.0.0.1";
const PORT = Number.parseInt(process.env.OPENCLAW_MEMORY_SERVER_PORT || "4312", 10);
const TOKEN = process.env.OPENCLAW_MEMORY_SERVER_TOKEN?.trim() || "";

const handlers = {
  stats: (params) => getMemoryStats(params),
  list: (params) => listMemories(params),
  recall: (params) => recallMemories(params),
  store: (params) => storeMemory(params),
  import: (params) => importMemories(params.memories || [], params),
  forget: (params) => forgetMemory(params),
  update: (params) => updateMemory(params),
};

function logServerError(method, error) {
  const timestamp = new Date().toISOString();
  const message = error instanceof Error ? error.stack || error.message : String(error);
  console.error(`[${timestamp}] method=${method || "unknown"} ${message}`);
}

function writeJson(response, statusCode, payload) {
  response.writeHead(statusCode, { "content-type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(payload));
}

function readBody(request) {
  return new Promise((resolve, reject) => {
    let body = "";
    request.setEncoding("utf8");
    request.on("data", (chunk) => {
      body += chunk;
      if (body.length > 2_000_000) {
        reject(new Error("Request body too large."));
        request.destroy();
      }
    });
    request.on("end", () => resolve(body));
    request.on("error", reject);
  });
}

function isAuthorized(request) {
  if (!TOKEN) return true;
  const header = request.headers.authorization || "";
  return header === `Bearer ${TOKEN}`;
}

const server = http.createServer(async (request, response) => {
  let requestMethod = "";
  try {
    if (request.method === "GET" && request.url === "/health") {
      writeJson(response, 200, { ok: true, status: "ok" });
      return;
    }

    if (request.method !== "POST" || request.url !== "/rpc") {
      writeJson(response, 404, { ok: false, error: "Not found." });
      return;
    }

    if (!isAuthorized(request)) {
      writeJson(response, 401, { ok: false, error: "Unauthorized." });
      return;
    }

    const rawBody = await readBody(request);
    const payload = rawBody ? JSON.parse(rawBody) : {};
    const method = String(payload.method || "").trim();
    requestMethod = method;
    const params = payload.params && typeof payload.params === "object" ? payload.params : {};
    const handler = handlers[method];

    if (!handler) {
      writeJson(response, 400, { ok: false, error: `Unknown method: ${method}` });
      return;
    }

    const result = await handler(params);
    writeJson(response, 200, { ok: true, result });
  } catch (error) {
    logServerError(requestMethod, error);
    writeJson(response, 500, { ok: false, error: error.message || String(error) });
  }
});

server.listen(PORT, HOST, () => {
  console.log(`OpenClaw memory HTTP bridge listening on http://${HOST}:${PORT}`);
});
