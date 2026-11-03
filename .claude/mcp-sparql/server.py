#!/usr/bin/env python3
"""Minimal SPARQL MCP server — forwards queries to an external endpoint via env vars.

The endpoint is production Blazegraph. Reads go in the `query` parameter, which Blazegraph never
executes as an update. Writes take two calls: `update` runs the impact query, writes the record
to docs/audit/mcp-updates/ and returns the formatted update + impact (tool results keep their line
breaks; tool arguments are shown as one escaped string). `apply_update` then sends the staged update,
held in server memory so it can't be swapped, only after the human chooses Accept in an MCP
elicitation prompt; the model cannot answer that prompt, and a client without elicitation is refused.

Required env vars:
  VENISS_SPARQL_ENDPOINT  e.g. https://veniss.net/sparql
  VENISS_SPARQL_USER      basic-auth username
  VENISS_SPARQL_PASS      basic-auth password

Optional:
  SPARQL_TIMEOUT_MS       default 30000; also sent as X-BIGDATA-MAX-QUERY-MILLIS so Blazegraph
                          cancels the query itself instead of running on after the client gives up.
"""

import asyncio
import base64
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types


def _load_dotenv() -> None:
    """Load claude_veniss/.env if vars not already set.

    Resolve symlinks: the real file is claude_veniss/.claude/mcp-sparql/server.py, so this works
    whichever folder Claude was launched from (workspace root or a repo inside it).
    """
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = value


_load_dotenv()

if "VENISS_SPARQL_ENDPOINT" not in os.environ:
    sys.exit(
        "ERROR: VENISS_SPARQL_ENDPOINT is not set.\n"
        "Create .env at the workspace root (copy .env.example) and fill in the values."
    )

ENDPOINT = os.environ["VENISS_SPARQL_ENDPOINT"]
USER = os.environ.get("VENISS_SPARQL_USER", "")
PASS = os.environ.get("VENISS_SPARQL_PASS", "")
TIMEOUT_MS = int(os.environ.get("SPARQL_TIMEOUT_MS", "30000"))
# Client waits a little longer than the server limit, so Blazegraph's own timeout error comes back.
TIMEOUT = TIMEOUT_MS // 1000 + 10


def _headers(content_type: str, accept: str) -> dict:
    h = {
        "Content-Type": content_type,
        "Accept": accept,
        "X-BIGDATA-MAX-QUERY-MILLIS": str(TIMEOUT_MS),
        # Cloudflare in front of veniss.net bans urllib's default "Python-urllib" user agent.
        "User-Agent": "veniss-mcp-sparql/1.0",
    }
    if USER:
        token = base64.b64encode(f"{USER}:{PASS}".encode()).decode()
        h["Authorization"] = f"Basic {token}"
    return h


def _post_query(query: str, accept: str) -> str:
    """Form-encoded POST — most compatible with Blazegraph SPARQL 1.1."""
    body = urllib.parse.urlencode({"query": query}).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers=_headers("application/x-www-form-urlencoded", accept),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8")


def _post_update(query: str) -> str:
    """SPARQL UPDATE via form-encoded POST. Only called after a confirmed elicitation."""
    body = urllib.parse.urlencode({"update": query}).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers=_headers("application/x-www-form-urlencoded", "application/json"),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8") or "Update executed."


def _impact(impact_query: str) -> str:
    """Run the read-only impact SELECT and keep the head of it for the human to read."""
    lines = _post_query(impact_query, "text/tab-separated-values").splitlines()
    # Sorted rows: Blazegraph's GROUP BY order varies between runs, and apply_update compares the text.
    lines = lines[:1] + sorted(lines[1:])
    more = f"\n... ({len(lines) - 41} more rows)" if len(lines) > 41 else ""
    return "\n".join(lines[:41]) + more


RECORD_DIR = Path(__file__).resolve().parents[2] / "docs" / "audit" / "mcp-updates"


def _record(query: str, impact_query: str, impact: str) -> Path:
    """Write the full update and impact check to a file before asking: Claude Code shows only the
    first lines of the prompt, so the prompt points here. Doubles as the audit log."""
    RECORD_DIR.mkdir(parents=True, exist_ok=True)
    path = RECORD_DIR / f"{datetime.now(timezone.utc):%Y-%m-%dT%H-%M-%SZ}.md"
    path.write_text(
        f"# SPARQL UPDATE on {ENDPOINT}\n\n## Update\n```sparql\n{query}\n```\n\n"
        f"## Impact query\n```sparql\n{impact_query}\n```\n\n## Impact result\n```\n{impact}\n```\n"
    )
    return path


PENDING: dict[str, tuple[str, str, Path, str]] = {}  # id -> (update, impact query, record, impact); dropped only once sent


async def _human_confirms(record: Path, impact: str) -> str | None:
    """Ask the human, not the model: Accept runs the update. Returns None when accepted,
    otherwise why not (decline, cancel, client without elicitation)."""
    ctx = server.request_context
    try:
        answer = await ctx.session.elicit(
            # The client cuts this to a few lines: file path first, then the impact counts.
            message=f"WRITE to PRODUCTION: update {record.stem} (full text in the previous tool result)\n{impact}",
            requestedSchema={"type": "object", "properties": {}},
            related_request_id=ctx.request_id,
        )
    except Exception as e:
        return f"the client could not show the prompt ({e})"
    return None if answer.action == "accept" else f"answer was {answer.action!r}"


server = Server("sparql")

_TOOLS = [
    types.Tool(
        name="select",
        description="Run a SPARQL SELECT query against the VeNiss Blazegraph endpoint. Returns SPARQL JSON.",
        inputSchema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "SPARQL SELECT query"}},
            "required": ["query"],
        },
    ),
    types.Tool(
        name="ask",
        description="Run a SPARQL ASK query. Returns JSON boolean.",
        inputSchema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "SPARQL ASK query"}},
            "required": ["query"],
        },
    ),
    types.Tool(
        name="construct",
        description="Run a SPARQL CONSTRUCT query. Returns Turtle.",
        inputSchema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "SPARQL CONSTRUCT query"}},
            "required": ["query"],
        },
    ),
    types.Tool(
        name="describe",
        description="Run a SPARQL DESCRIBE query. Returns Turtle.",
        inputSchema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "SPARQL DESCRIBE query (IRI or pattern)"}},
            "required": ["query"],
        },
    ),
    types.Tool(
        name="update",
        description=(
            "Stage a SPARQL UPDATE (INSERT/DELETE/...) for PRODUCTION; nothing is sent. Requires "
            "impact_query: a read-only SELECT counting what the update would touch, including what it "
            "should NOT touch (existing values replaced, duplicates, subjects outside the intended set). "
            "Returns an id plus the formatted update and impact result for the human to read. Then call "
            "apply_update with that id: the human chooses Accept or Decline."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SPARQL UPDATE query"},
                "impact_query": {
                    "type": "string",
                    "description": "Read-only SELECT counting the triples/subjects affected and any unwanted changes",
                },
            },
            "required": ["query", "impact_query"],
        },
    ),
    types.Tool(
        name="apply_update",
        description=(
            "Send an update staged with `update`, after the human chooses Accept in a prompt. "
            "The id stays staged until it is sent, so it can be retried after a decline or error."
        ),
        inputSchema={
            "type": "object",
            "properties": {"id": {"type": "string", "description": "id returned by update"}},
            "required": ["id"],
        },
    ),
]


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return _TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    query = arguments.get("query", "")
    try:
        if name == "select":
            result = _post_query(query, "application/sparql-results+json")
        elif name == "ask":
            result = _post_query(query, "application/sparql-results+json")
        elif name == "construct":
            result = _post_query(query, "text/turtle")
        elif name == "describe":
            result = _post_query(query, "text/turtle")
        elif name == "update":
            impact_query = arguments.get("impact_query", "").strip()
            if not impact_query:
                result = "Not run: impact_query is required (a read-only SELECT counting what the update touches)."
            else:
                # An HTTP error here (bad or non-SELECT query) falls to the handlers below: nothing is sent.
                impact = _impact(impact_query)
                record = _record(query, impact_query, impact)
                PENDING[record.stem] = (query, impact_query, record, impact)
                result = (
                    f"Staged, NOT run. id: {record.stem}\n\n--- Update ---\n{query}\n\n"
                    f"--- Impact query ---\n{impact_query}\n\n--- Impact result ---\n{impact}\n\n"
                    f"Record: {record}"
                )
        elif name == "apply_update":
            sid = arguments.get("id", "")
            staged = PENDING.get(sid)  # kept on decline/error/changed impact, so the same id can be retried
            if staged is None:
                result = "Not run: unknown or already sent id (stage it again with update)."
            else:
                query, impact_query, record, impact = staged
                # Re-run right before asking: data may have changed since staging.
                now = _impact(impact_query)
                if now != impact:
                    PENDING[sid] = (query, impact_query, record, now)  # next try asks with the new counts
                    refused = f"the impact changed since staging; retry the same id to be asked with these counts:\n{now}"
                else:
                    refused = await _human_confirms(record, now)
                if refused is None:
                    result = _post_update(query)  # an HTTP error here leaves it staged
                    del PENDING[sid]
                else:
                    result = f"Not run: {refused}. Still staged: retry apply_update {sid}."
                with record.open("a") as f:
                    f.write(f"\n## Outcome\n{'accepted' if refused is None else 'not run'}\n```\n{result}\n```\n")
                result += f"\nRecord: {record}"
        else:
            result = f"Unknown tool: {name}"
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        result = f"HTTP {e.code} {e.reason}\n{body}"
    except urllib.error.URLError as e:
        result = f"Connection error: {e.reason}"
    except Exception as e:
        result = f"Error: {e}"
    return [types.TextContent(type="text", text=result)]


async def main() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
