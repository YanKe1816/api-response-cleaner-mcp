import json
import os
from collections import OrderedDict
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


JSONRPC_VERSION = "2.0"
PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {
    "name": "api-response-cleaner-mcp",
    "version": "0.1.0",
}
TOOL_NAME = "apiResponseCleaner"
TOOL_TITLE = "API Response Cleaner"
TOOL_DESCRIPTION = (
    "Deterministically filters a raw API response to include only the requested "
    "top-level target_fields."
)
TOOL_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "raw_response": {
            "type": "object",
            "description": "Input API response object to filter.",
        },
        "target_fields": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "description": "Exact top-level field names to retain in output order.",
        },
    },
    "required": ["raw_response", "target_fields"],
    "additionalProperties": False,
}
TOOL_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "cleaned_response": {
            "type": "object",
            "description": "Subset of raw_response containing only requested fields that exist.",
        },
        "missing_fields": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Requested fields not present in raw_response.",
        },
        "removed_fields": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Input fields omitted because they were not requested.",
        },
    },
    "required": ["cleaned_response", "missing_fields", "removed_fields"],
    "additionalProperties": False,
}
TOOL_ANNOTATIONS = {
    "purpose": "Filter a JSON object by exact top-level target_fields without transformation.",
    "input_contract": {
        "raw_response": "JSON object",
        "target_fields": "Array of non-empty strings",
    },
    "output_contract": {
        "cleaned_response": "JSON object",
        "missing_fields": "Array of strings",
        "removed_fields": "Array of strings",
    },
    "constraints": [
        "No external API calls",
        "No field generation",
        "No business explanations",
        "No transformations beyond filtering target_fields",
        "Deterministic output for identical input",
    ],
    "readOnlyHint": True,
    "openWorldHint": False,
    "destructiveHint": False,
}
TOOL_SAFETY_METADATA = {
    "audit": {
        "data_access": "Input-only",
        "network_access": "None",
        "side_effects": "None",
        "deterministic": True,
        "schema_enforced": True,
    }
}
SUPPORT_EMAIL = "sidcraigau@gmail.com"
EFFECTIVE_DATE = "2026-05-13"


def build_tool_definition():
    return {
        "name": TOOL_NAME,
        "title": TOOL_TITLE,
        "description": TOOL_DESCRIPTION,
        "inputSchema": TOOL_INPUT_SCHEMA,
        "outputSchema": TOOL_OUTPUT_SCHEMA,
        "annotations": TOOL_ANNOTATIONS,
        "meta": TOOL_SAFETY_METADATA,
    }


def build_initialize_result():
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "serverInfo": SERVER_INFO,
        "capabilities": {"tools": {}},
    }


def build_jsonrpc_result(request_id, result):
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}


def build_jsonrpc_error(request_id, code, message):
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def build_tool_result(structured_content):
    compact = json.dumps(structured_content, ensure_ascii=True, separators=(",", ":"))
    return {
        "content": [{"type": "text", "text": compact}],
        "structuredContent": structured_content,
        "isError": False,
    }


def validate_arguments(arguments):
    if not isinstance(arguments, dict):
        return "The 'arguments' field must be an object."

    expected_keys = {"raw_response", "target_fields"}
    actual_keys = set(arguments.keys())

    if "raw_response" not in arguments:
        return "The 'raw_response' field is required."
    if "target_fields" not in arguments:
        return "The 'target_fields' field is required."
    if actual_keys != expected_keys:
        return "Only 'raw_response' and 'target_fields' are allowed."
    if not isinstance(arguments["raw_response"], dict):
        return "The 'raw_response' field must be an object."
    if not isinstance(arguments["target_fields"], list):
        return "The 'target_fields' field must be an array of strings."

    for index, field_name in enumerate(arguments["target_fields"]):
        if not isinstance(field_name, str) or not field_name:
            return f"The 'target_fields[{index}]' field must be a non-empty string."

    return None


def clean_response(raw_response, target_fields):
    cleaned_response = OrderedDict()
    missing_fields = []

    for field_name in target_fields:
        if field_name in raw_response:
            cleaned_response[field_name] = raw_response[field_name]
        else:
            missing_fields.append(field_name)

    target_field_set = set(target_fields)
    removed_fields = [field_name for field_name in raw_response if field_name not in target_field_set]

    return {
        "cleaned_response": dict(cleaned_response),
        "missing_fields": missing_fields,
        "removed_fields": removed_fields,
    }


def html_page(title, body_html):
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{escape(title)}</title>
  <style>
    :root {{
      --bg: #f5efe6;
      --panel: #fffdfa;
      --text: #1f2933;
      --muted: #52606d;
      --accent: #8b5e34;
      --border: #dccfbd;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, \"Times New Roman\", serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, #fff7ed 0%, transparent 28%),
        linear-gradient(180deg, #efe7da 0%, var(--bg) 100%);
    }}
    main {{
      max-width: 860px;
      margin: 0 auto;
      padding: 48px 20px 72px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 32px;
      box-shadow: 0 12px 32px rgba(31, 41, 51, 0.08);
    }}
    h1, h2 {{ line-height: 1.15; margin-top: 0; }}
    p, li {{ line-height: 1.6; color: var(--muted); }}
    a {{ color: var(--accent); }}
    code {{
      background: #f3e9d8;
      border-radius: 4px;
      padding: 0.12rem 0.35rem;
    }}
    nav {{
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      margin-top: 24px;
      padding-top: 20px;
      border-top: 1px solid var(--border);
    }}
    .eyebrow {{
      letter-spacing: 0.08em;
      text-transform: uppercase;
      font-size: 0.8rem;
      color: var(--accent);
      margin-bottom: 12px;
    }}
    ul {{ padding-left: 1.2rem; }}
  </style>
</head>
<body>
  <main>
    <section class=\"panel\">
      {body_html}
      <nav>
        <a href=\"/\">Home</a>
        <a href=\"/privacy\">Privacy</a>
        <a href=\"/terms\">Terms</a>
        <a href=\"/support\">Support</a>
      </nav>
    </section>
  </main>
</body>
</html>"""


def homepage_html():
    return html_page(
        "API Response Cleaner",
        f"""
        <div class=\"eyebrow\">API Response Cleaner</div>
        <h1>API Response Cleaner</h1>
        <p>Filter a raw API response so only the requested top-level fields are returned.</p>
        <h2>How to use it</h2>
        <ul>
          <li>Send a JSON-RPC request to <code>POST /mcp</code>.</li>
          <li>Call <code>{TOOL_NAME}</code> with <code>raw_response</code> and <code>target_fields</code>.</li>
          <li>The tool returns only <code>cleaned_response</code>, <code>missing_fields</code>, and <code>removed_fields</code>.</li>
        </ul>
        <p>Support email: <a href=\"mailto:{SUPPORT_EMAIL}\">{SUPPORT_EMAIL}</a></p>
        """,
    )


def privacy_html():
    return html_page(
        "Privacy",
        f"""
        <div class=\"eyebrow\">Privacy</div>
        <h1>Privacy</h1>
        <p>Effective date / last updated: {EFFECTIVE_DATE}</p>
        <p>This service processes only the data submitted in each request, including the source JSON object in <code>raw_response</code> and the requested field names in <code>target_fields</code>.</p>
        <p>The source of this data is the request payload sent by the user or connected client. The purpose of processing is limited to deterministic field filtering for the API Response Cleaner tool.</p>
        <p>This service does not intentionally store submitted request data after the response is returned and does not share submitted data with third parties or external APIs.</p>
        <p>Operational infrastructure may generate standard access or error logs as part of hosting operations.</p>
        <p>For deletion requests, privacy questions, or data handling inquiries, contact <a href=\"mailto:{SUPPORT_EMAIL}\">{SUPPORT_EMAIL}</a>.</p>
        """,
    )


def terms_html():
    return html_page(
        "Terms",
        f"""
        <div class=\"eyebrow\">Terms</div>
        <h1>Terms</h1>
        <p>Effective date / last updated: {EFFECTIVE_DATE}</p>
        <p>This service provides a deterministic tool for filtering top-level fields from a submitted JSON object through the API Response Cleaner MCP endpoint.</p>
        <p>Usage is limited to the defined tool contract and returned schema. The service is not professional, legal, financial, compliance, or operational advice.</p>
        <p>Prohibited uses include attempting to use the service for unrelated workflows, sending malicious payloads, relying on it for professional advice, or expecting behavior beyond the published schema and tool contract.</p>
        <p>Users are responsible for submitting accurate data, reviewing outputs, protecting sensitive information, and validating that the tool is suitable for their own internal workflow.</p>
        <p>Service details may change over time. Material updates will be reflected by updating this page.</p>
        <p>The service is provided as-is without guarantees of fitness for a particular purpose, uninterrupted availability, or suitability for high-risk decisions.</p>
        """,
    )


def support_html():
    return html_page(
        "Support",
        f"""
        <div class=\"eyebrow\">Support</div>
        <h1>API Response Cleaner Support</h1>
        <p>Support email: <a href=\"mailto:{SUPPORT_EMAIL}\">{SUPPORT_EMAIL}</a></p>
        <p>You can submit bug reports, deployment issues, tool behavior questions, route availability problems, privacy requests, and general feedback about the API Response Cleaner app.</p>
        <p>When reporting an exception or unexpected result, include the route used, the request shape, the expected behavior, the actual behavior, and any relevant error details so the issue can be reproduced safely.</p>
        <p>Support responses are provided on a reasonable-effort basis. Include enough detail to help triage the request efficiently.</p>
        """,
    )


def handle_initialize(request_id):
    return build_jsonrpc_result(request_id, build_initialize_result())


def handle_tools_list(request_id):
    return build_jsonrpc_result(request_id, {"tools": [build_tool_definition()]})


def handle_tools_call(request_id, params):
    if not isinstance(params, dict):
        return build_jsonrpc_error(request_id, -32602, "Invalid params")
    if params.get("name") != TOOL_NAME:
        return build_jsonrpc_error(request_id, -32602, f"Unknown tool: {params.get('name')}")

    validation_error = validate_arguments(params.get("arguments"))
    if validation_error is not None:
        return build_jsonrpc_error(request_id, -32602, validation_error)

    arguments = params["arguments"]
    structured_content = clean_response(
        raw_response=arguments["raw_response"],
        target_fields=arguments["target_fields"],
    )
    return build_jsonrpc_result(request_id, build_tool_result(structured_content))


def handle_mcp_request(payload):
    if not isinstance(payload, dict):
        return build_jsonrpc_error(None, -32600, "Invalid Request")

    request_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params", {})

    if method == "initialize":
        return handle_initialize(request_id)
    if method == "tools/list":
        return handle_tools_list(request_id)
    if method == "tools/call":
        return handle_tools_call(request_id, params)

    return build_jsonrpc_error(request_id, -32601, "Method not found")


class MCPRequestHandler(BaseHTTPRequestHandler):
    server_version = "APIResponseCleanerMCP/0.1.0"

    def _write_json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_html(self, status_code, html_text):
        body = html_text.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_text(self, status_code, text_value):
        body = text_value.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._write_html(200, homepage_html())
            return
        if self.path == "/privacy":
            self._write_html(200, privacy_html())
            return
        if self.path == "/terms":
            self._write_html(200, terms_html())
            return
        if self.path == "/support":
            self._write_html(200, support_html())
            return
        if self.path == "/health":
            self._write_json(200, {"status": "ok"})
            return
        if self.path == "/.well-known/openai-apps-challenge":
            self._write_text(200, os.environ.get("OPENAI_APPS_CHALLENGE", ""))
            return
        if self.path == "/mcp":
            self._write_json(405, {"error": "Method Not Allowed"})
            return

        self._write_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/mcp":
            self._write_json(404, {"error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            self._write_json(400, build_jsonrpc_error(None, -32700, "Parse error"))
            return

        self._write_json(200, handle_mcp_request(payload))

    def log_message(self, format_string, *args):
        return


def run():
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), MCPRequestHandler)
    try:
        print(f"Server running on port {port}...", flush=True)
        print(f"API Response Cleaner MCP server listening on http://127.0.0.1:{port}", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
