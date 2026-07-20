import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import express from "express";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

import { handleListCampaigns } from "./handlers/campaignList.js";
import { handleGetReporting } from "./handlers/reporting.js";
import { handleGetCampaignDetails } from "./handlers/campaignDetails.js";
import { handleGetAdgroupDetails } from "./handlers/adgroupDetails.js";
import { handleGetAdDetails } from "./handlers/adDetails.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const schema = JSON.parse(
  readFileSync(join(__dirname, "../schema/tools_schema.json"), "utf-8")
);

const server = new McpServer({
  name: "tiktok-optimization-advisor",
  version: "0.1.0",
});

const toolHandlers = {
  tiktok_list_campaigns: handleListCampaigns,
  tiktok_get_reporting: handleGetReporting,
  tiktok_get_campaign_details: handleGetCampaignDetails,
  tiktok_get_adgroup_details: handleGetAdgroupDetails,
  tiktok_get_ad_details: handleGetAdDetails,
};

for (const tool of schema.tools) {
  server.tool(tool.name, tool.description, tool.inputSchema.properties, async (args) => {
    const handler = toolHandlers[tool.name];
    if (!handler) {
      throw new Error(`No handler registered for tool: ${tool.name}`);
    }
    return handler(args);
  });
}

const PORT = process.env.PORT ?? 3000;
const app = express();
app.use(express.json());

const transports = {};

app.get("/sse", async (req, res) => {
  const transport = new SSEServerTransport("/messages", res);
  transports[transport.sessionId] = transport;
  res.on("close", () => delete transports[transport.sessionId]);
  await server.connect(transport);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId;
  const transport = transports[sessionId];
  if (!transport) {
    return res.status(404).json({ error: "Session not found" });
  }
  await transport.handlePostMessage(req, res);
});

app.listen(PORT, () => {
  console.log(`[tiktok-optimization-advisor] MCP server listening on http://localhost:${PORT}/sse`);
});
