#!/usr/bin/env python3
"""Run SPARQL against the VeNiss Blazegraph endpoint. Stdlib only.

Usage (from the workspace root):
  python3 claude_veniss/scripts/sparql.py select    FILE|-   # SPARQL JSON
  python3 claude_veniss/scripts/sparql.py ask       FILE|-   # SPARQL JSON
  python3 claude_veniss/scripts/sparql.py construct FILE|-   # Turtle
  python3 claude_veniss/scripts/sparql.py describe  FILE|-   # Turtle
  python3 claude_veniss/scripts/sparql.py update    FILE|- --confirmed

Reads from the workspace-root .env (never printed):
  VENISS_SPARQL_ENDPOINT  e.g. https://veniss.net/sparql
  VENISS_SPARQL_USER      basic-auth username
  VENISS_SPARQL_PASS      basic-auth password
Optional:
  SPARQL_TIMEOUT_MS       default 30000

`update` needs --confirmed (pass it only after the user typed confirmation
for that exact query) and is refused on the prod profile.
"""

import argparse
import base64
import filecmp
import http.client
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# scripts/ sits in claude_veniss/, which sits in the workspace root.
ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
REPO = Path(__file__).resolve().parents[1]

ACCEPT = {
    "select": "application/sparql-results+json",
    "ask": "application/sparql-results+json",
    "construct": "text/turtle",
    "describe": "text/turtle",
}


def load_dotenv() -> None:
    """Load the root .env without overriding variables already set."""
    env_path = ROOT / ".env"
    try:
        lines = env_path.read_text().splitlines()
    except FileNotFoundError:
        return
    except PermissionError:
        sys.exit(
            "ERROR: cannot read .env (the Claude Code sandbox denies it). Run this script\n"
            "outside the sandbox: `/sandbox exclude` it, or run it yourself with `!`."
        )
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def is_prod() -> bool:
    local = REPO / ".claude" / "settings.local.json"
    prod = REPO / ".claude" / "settings.prod.json"
    return local.exists() and prod.exists() and filecmp.cmp(local, prod, shallow=False)


def post(field: str, query: str, accept: str) -> str:
    endpoint = os.environ["VENISS_SPARQL_ENDPOINT"]
    user = os.environ.get("VENISS_SPARQL_USER", "")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": accept,
        # Cloudflare on veniss.net bans urllib's default "Python-urllib/x.y" signature.
        "User-Agent": os.environ.get("SPARQL_USER_AGENT", "veniss-sparql-client/1.0 (+https://github.com/villaitatti/claude_veniss)"),
    }
    if user:
        token = base64.b64encode(f"{user}:{os.environ.get('VENISS_SPARQL_PASS', '')}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"
    # Form-encoded POST: most compatible with Blazegraph SPARQL 1.1.
    req = urllib.request.Request(
        endpoint, data=urllib.parse.urlencode({field: query}).encode(), headers=headers, method="POST"
    )
    timeout = int(os.environ.get("SPARQL_TIMEOUT_MS", "30000")) // 1000
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("kind", choices=[*ACCEPT, "update"])
    parser.add_argument("file", help="query file, or - for stdin")
    parser.add_argument("--confirmed", action="store_true", help="required for update")
    args = parser.parse_args()

    query = sys.stdin.read() if args.file == "-" else Path(args.file).read_text()

    # An endpoint already in the environment means anonymous/explicit use: skip .env.
    if "VENISS_SPARQL_ENDPOINT" not in os.environ:
        load_dotenv()
    if "VENISS_SPARQL_ENDPOINT" not in os.environ:
        print("ERROR: VENISS_SPARQL_ENDPOINT is not set. Check the workspace-root .env.", file=sys.stderr)
        return 2

    if args.kind == "update":
        if is_prod():
            print("ERROR: prod profile is read-only; update refused.", file=sys.stderr)
            return 2
        if not args.confirmed:
            print("ERROR: update needs --confirmed, after typed user confirmation.", file=sys.stderr)
            return 2

    try:
        if args.kind == "update":
            print(post("update", query, "application/json") or "Update executed.")
        else:
            # Reads are idempotent: retry when the connection drops mid-response
            # (seen intermittently through Cloudflare). Updates are never retried.
            for attempt in range(3):
                try:
                    result = post("query", query, ACCEPT[args.kind])
                    break
                except (http.client.IncompleteRead, ConnectionError) as e:
                    if attempt == 2:
                        raise
                    print(f"Connection dropped ({e!r}); retrying.", file=sys.stderr)
            print(result)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} {e.reason}\n{e.read().decode('utf-8', errors='replace')}", file=sys.stderr)
        if e.code == 403 and "cloudflare" in e.headers.get("Server", "").lower():
            print("Blocked by Cloudflare, not by Blazegraph auth.", file=sys.stderr)
        elif e.code in (401, 403):
            print("Auth failed: check VENISS_SPARQL_USER / VENISS_SPARQL_PASS in .env.", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        return 1
    except (http.client.IncompleteRead, ConnectionError, TimeoutError) as e:
        print(f"Connection dropped while reading the response: {e!r}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
