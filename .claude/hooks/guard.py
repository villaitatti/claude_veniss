#!/usr/bin/env python3
"""PreToolUse guard for the VeNiss workspace.

Second line of defence behind permissions.deny and the sandbox:
- file tools may only touch the workspace folders (read from veniss.code-workspace),
  this repo's own config files, and Claude's own state/temp dirs;
- Bash may not push, hit the SPARQL endpoint directly, read stale .trig KPs,
  or reference out-of-scope paths.

Exit 2 + stderr message = block the tool call and tell Claude why.
"""

import json
import os
import re
import sys
from pathlib import Path

# Workspace root. .claude is a symlink into claude_veniss/, so don't resolve
# __file__ for the fallback: the root is two levels above the launch path.
ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).absolute().parents[2]).resolve()
REPO = "claude_veniss"

# Root entries Claude Code reads: symlinks into the claude_veniss repo.
ROOT_DIRS = [".claude"]
ROOT_FILES = ["CLAUDE.md", ".mcp.json"]

# Outside the root, Claude may still use its own state and temp dirs.
EXTRA_ALLOWED = [Path.home() / ".claude", Path("/tmp"), Path("/private/tmp"), Path(os.environ.get("TMPDIR", "/tmp"))]

FILE_TOOLS = {"Read", "Edit", "Write", "MultiEdit", "NotebookEdit", "Grep", "Glob"}


def workspace_folders():
    try:
        ws_file = next(p for p in (ROOT / REPO / "veniss.code-workspace", ROOT / "veniss.code-workspace") if p.exists())
        ws = json.loads(ws_file.read_text())
        folders = [(ws_file.parent / f["path"]).resolve() for f in ws.get("folders", [])]
        # Never let a folder entry widen scope to the whole root.
        return [f for f in folders if f != ROOT]
    except Exception:
        return [(ROOT / p).resolve() for p in ("apps/VeNiss", "metapolis-xdtiler", "researchspace", REPO)]


def block(reason):
    print(f"Blocked by .claude/hooks/guard.py: {reason}", file=sys.stderr)
    sys.exit(2)


def under(path, base):
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def check_path(raw, cwd, tool):
    p = Path(os.path.expanduser(raw))
    if not p.is_absolute():
        p = Path(cwd) / p
    p = p.resolve()

    if p.name == ".env" or p.name.startswith(".env.") and p.name != ".env.example":
        block(f"{raw} is a credentials file. Refer to variable names only.")
    if re.search(r"data/field-definitions/.*\.trig$", str(p)):
        block("field-definition .trig files are stale. Fetch Knowledge Patterns from Blazegraph via the sparql MCP.")

    # Searching from the root itself is fine; deny rules + gitignore filter the results.
    if p == ROOT and tool in ("Grep", "Glob"):
        return
    if any(under(p, f) for f in workspace_folders()):
        return
    if any(under(p, ROOT / d) for d in ROOT_DIRS) or p in [ROOT / f for f in ROOT_FILES]:
        return
    if any(under(p, base.resolve()) for base in EXTRA_ALLOWED):
        return
    block(f"{raw} is outside the workspace folders listed in veniss.code-workspace.")


BASH_RULES = [
    (r"\bgit\b[^|;&]*\bpush\b", "git push is reserved for the user."),
    (r"\bgit\b[^|;&]*\breset\s+--hard\b", "git reset --hard is not allowed."),
    (r"\bgit\b[^|;&]*\bclean\b\s+-\w*f", "git clean -f is not allowed."),
    (r"\brm\s+-\w*r\w*f|\brm\s+-\w*f\w*r", "rm -rf is not allowed."),
    (r"\bcurl\b.*(sparql|veniss\.net)", "use the sparql MCP server, not curl."),
    (r"\b(INSERT|DELETE|DROP|CLEAR)\b.*\bcurl\b|\bcurl\b.*\b(INSERT|DELETE|DROP|CLEAR)\b", "SPARQL updates only via the MCP with typed confirmation."),
    (r"\bpsql\b", "direct SQL is out of scope."),
    (r"field-definitions/[^\s]*\.trig", "field-definition .trig files are stale. Use the sparql MCP."),
    (r"\[Deprecated\]|Deprecated\]", "[Deprecated]/ is outside the workspace."),
    (r"map-uploader", "apps/map-uploader is outside the workspace."),
    (r"(^|[\s/'\"=<])\.env(\s|$|['\"])", "credentials file. Refer to variable names only."),
]


def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    inp = data.get("tool_input", {}) or {}
    cwd = data.get("cwd") or str(ROOT)

    if tool in FILE_TOOLS:
        for key in ("file_path", "notebook_path", "path"):
            if inp.get(key):
                check_path(inp[key], cwd, tool)
    elif tool == "Bash":
        cmd = inp.get("command", "")
        for pattern, reason in BASH_RULES:
            if re.search(pattern, cmd, re.IGNORECASE if "INSERT" in pattern else 0):
                block(reason)
    sys.exit(0)


if __name__ == "__main__":
    main()
