# API Response Cleaner MCP Server

This is a production-ready MCP app server for ChatGPT Developer Mode.

It provides:

- `GET /`
- `GET /privacy`
- `GET /terms`
- `GET /support`
- `GET /health`
- `GET /.well-known/openai-apps-challenge`
- `POST /mcp`

The server exposes a single tool: `apiResponseCleaner`

It deterministically:

- Extracts only the fields listed in `target_fields`
- Returns `cleaned_response` in `target_fields` order
- Lists requested fields not found in `missing_fields`
- Lists non-target raw response fields in `removed_fields`

## Start

```powershell
python server.py
```

Default listening address:

```text
http://127.0.0.1:8000
```

## Health Check

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Challenge Route

```powershell
$env:OPENAI_APPS_CHALLENGE='your-challenge-token'
Invoke-RestMethod http://127.0.0.1:8000/.well-known/openai-apps-challenge
```

## MCP Initialize

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/mcp `
  -Method Post `
  -ContentType 'application/json' `
  -Body '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

## List Tools

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/mcp `
  -Method Post `
  -ContentType 'application/json' `
  -Body '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

## Call the Tool

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/mcp `
  -Method Post `
  -ContentType 'application/json' `
  -Body '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"apiResponseCleaner","arguments":{"raw_response":{"name":"Alice","age":30,"city":"Paris","extra":"ignore"},"target_fields":["name","city"]}}}'
```

Expected structured output:

```json
{
  "cleaned_response": {
    "name": "Alice",
    "city": "Paris"
  },
  "missing_fields": [],
  "removed_fields": [
    "age",
    "extra"
  ]
}
```

## Local Testing

```powershell
python -m unittest -v
```

## Temporary Public Tunnel

After the local service is running, use either of the following:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

```powershell
ngrok http 8000
```

Append `/mcp` to the generated public URL and use it as the MCP endpoint in Developer Mode.

For the public app pages, use the root URL directly:

- `/`
- `/privacy`
- `/terms`
- `/support`
- `/health`
- `/.well-known/openai-apps-challenge`
