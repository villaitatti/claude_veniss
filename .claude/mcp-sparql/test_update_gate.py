"""Self-check of the update gate: `update` only stages (returns the formatted text, sends nothing);
`apply_update` sends the staged update once, and only when the human chooses Accept.
No network: _post_query, _post_update and the elicitation are faked; records go to a temp dir.
Run: uv run --with 'mcp>=1.20,<2' python .claude/mcp-sparql/test_update_gate.py
"""

import asyncio
import importlib.util
import tempfile
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location("srv", Path(__file__).with_name("server.py"))
srv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srv)

srv.RECORD_DIR = Path(tempfile.mkdtemp())
sent = []
srv._post_update = lambda q: sent.append(q) or "sent"
srv._post_query = lambda q, accept: "?n\n42"
UPDATE = "PREFIX x: <urn:x#>\nINSERT DATA {\n  <urn:a> <urn:b> <urn:c>\n}"
IMPACT = "SELECT (COUNT(*) AS ?n) WHERE { <urn:a> <urn:b> ?o }"


def call(name, args, elicit=None):
    ctx = SimpleNamespace(session=SimpleNamespace(elicit=elicit), request_id=1)
    type(srv.server).request_context = property(lambda self: ctx)
    return asyncio.run(srv.call_tool(name, args))[0].text


def stage(impact=IMPACT):
    srv.PENDING.clear()
    out = call("update", {"query": UPDATE, "impact_query": impact})
    assert not sent, "staging must not send"
    return out


def answer(action):
    async def elicit(**kw):
        assert "42" in kw["message"]  # impact counts in the prompt
        assert kw["requestedSchema"]["properties"] == {}  # buttons only, no typing
        return SimpleNamespace(action=action, content=None)
    return elicit


async def unsupported(**kw):
    raise RuntimeError("client does not support elicitation")


# staging returns the update with its real line breaks, plus the impact
out = stage()
assert UPDATE in out and IMPACT in out and "42" in out and "NOT run" in out, out
sid = out.split("id: ")[1].splitlines()[0]
record = Path(out.split("Record: ")[1])
assert UPDATE in record.read_text()

out = call("apply_update", {"id": sid}, answer("accept"))
assert out.startswith("sent") and sent == [UPDATE], out
assert "accepted" in record.read_text()
# once sent, the id is gone
assert call("apply_update", {"id": sid}, answer("accept")).startswith("Not run") and len(sent) == 1

for case in (answer("decline"), answer("cancel"), unsupported):
    sent.clear()
    sid = stage().split("id: ")[1].splitlines()[0]
    out = call("apply_update", {"id": sid}, case)
    assert out.startswith("Not run") and not sent, (case, out)
    assert "not run" in Path(out.split("Record: ")[1]).read_text()
    assert sid in srv.PENDING  # kept for a retry

# retry the same id after a decline: asked again, sent on accept
assert call("apply_update", {"id": sid}, answer("accept")).startswith("sent") and sent == [UPDATE]
assert sid not in srv.PENDING

# HTTP error while sending: still staged
sent.clear()
sid = stage().split("id: ")[1].splitlines()[0]
real_send = srv._post_update
srv._post_update = lambda q: (_ for _ in ()).throw(RuntimeError("502"))
assert call("apply_update", {"id": sid}, answer("accept")).startswith("Error") and sid in srv.PENDING
srv._post_update = real_send

# impact changed between staging and apply: refused, human never asked
sent.clear()
sid = stage().split("id: ")[1].splitlines()[0]
srv._post_query = lambda q, accept: "?n\n43"
out = call("apply_update", {"id": sid}, unsupported)  # unsupported would raise if asked
assert "impact changed" in out and "43" in out and not sent, out
assert "not run" in Path(out.split("Record: ")[1]).read_text()
# kept with the new counts: a retry asks (prompt shows 43) and sends on accept
async def sees_43(**kw):
    assert "43" in kw["message"]
    return SimpleNamespace(action="accept", content=None)
assert call("apply_update", {"id": sid}, sees_43).startswith("sent") and sent == [UPDATE]
sent.clear()
srv._post_query = lambda q, accept: "?n\n42"

# same rows in another order: not a change
srv._post_query = lambda q, accept: "?c\t?n\na\t1\nb\t2"
sid = stage().split("id: ")[1].splitlines()[0]
srv._post_query = lambda q, accept: "?c\t?n\nb\t2\na\t1"
async def accept_any(**kw):
    return SimpleNamespace(action="accept", content=None)
assert call("apply_update", {"id": sid}, accept_any).startswith("sent")
sent.clear()
srv._post_query = lambda q, accept: "?n\n42"

# unknown id, missing impact query: refused, nobody asked
assert call("apply_update", {"id": "nope"}, answer("accept")).startswith("Not run") and not sent
assert stage(impact="  ").startswith("Not run") and not srv.PENDING


# failing impact query: nothing staged
def boom(q, accept):
    raise RuntimeError("bad query")


srv._post_query = boom
assert stage().startswith("Error") and not srv.PENDING
print("update gate OK")
