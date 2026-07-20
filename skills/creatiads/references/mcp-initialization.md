# MCP Initialization

Run this gate before any TikTok API operation.

## Server Registry

| Platform | Default name | Remote URL |
| --- | --- | --- |
| TikTok | `tiktok-mcp` | `https://business-api.tiktok.com/open_mcp/tt-ads-mcp-layer` |

## Procedure

1. Run `codex mcp list`.
2. Match by remote URL first. If a matching URL already exists under another name, reuse that name.
3. If the TikTok URL is missing, run:

```bash
codex mcp add tiktok-mcp --url https://business-api.tiktok.com/open_mcp/tt-ads-mcp-layer
```

4. Run `codex mcp list` again and confirm the server is enabled.
5. First prefer the current agent runtime's native, already-authorized TikTok Ads MCP tool calls. In Codex,
   ChatGPT, Claude, OpenClaw, or similar agent hosts, do not assume Python must perform a separate OAuth flow.
6. Run login only when the user explicitly asks to refresh authorization, or when the native MCP call fails with
   an auth-required error:

```bash
codex mcp login <server-name>
```

Use the matched existing server name when the user already has one configured.



## Failure Handling

If add or login fails, stop the current platform task and return:

- platform
- server name
- remote URL
- failure summary
- next command to retry, usually `codex mcp login <server-name>`

Do not print tokens, authorization headers, OAuth callback secrets, browser callback URLs containing secrets, or MCP session metadata.
