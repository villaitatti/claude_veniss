#!/usr/bin/env python3
"""Minimal SPARQL MCP server — forwards queries to an external endpoint via env vars.

Required env vars:
  VENISS_SPARQL_ENDPOINT  e.g. https://veniss.net/sparql
  VENISS_SPARQL_USER      basic-auth username
  VENISS_SPARQL_PASS      basic-auth password

Optional:
  SPARQL_TIMEOUT_MS       default 30000
"""

import asyncio
import base64
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types


def _load_dotenv() -> None:
    """Load .env from the workspace root if vars not already set.

    .claude is a symlink into claude_veniss/, so don't resolve symlinks:
    the root is two levels above the path we were launched with.
    """
    root = os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).absolute().parents[2]
    env_path = Path(root) / ".env"
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
TIMEOUT = int(os.environ.get("SPARQL_TIMEOUT_MS", "30000")) // 1000


def _headers(content_type: str, accept: str) -> dict:
    h = {"Content-Type": content_type, "Accept": accept}
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
    """SPARQL UPDATE via form-encoded POST."""
    body = urllib.parse.urlencode({"update": query}).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers=_headers("application/x-www-form-urlencoded", "application/json"),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8") or "Update executed."


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
        description="Run a SPARQL UPDATE (INSERT/DELETE/DROP/CLEAR). REQUIRES explicit user confirmation before calling — never call autonomously.",
        inputSchema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "SPARQL UPDATE query"}},
            "required": ["query"],
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
            result = _post_update(query)
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
