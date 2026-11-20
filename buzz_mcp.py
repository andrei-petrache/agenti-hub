"""BuzzzHub bridge: an MCP server (stdio) that lets agents message each other through BuzzzHub, Claude and Codex alike.

Register it once in each tool, for example:
    claude mcp add --scope user buzzzhub -- python C:/path/to/buzzzhub/buzz_mcp.py
    codex mcp add buzzzhub -- python C:/path/to/buzzzhub/buzz_mcp.py

It only talks to the BuzzzHub that runs on this computer (the port it wrote in cache/port.txt); BuzzzHub must be open.
No dependencies: the protocol is JSON-RPC, one message per line.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERSION = "1.0"

TOOLS = [
    {"name": "list_agents",
     "description": "Lists the AI agents BuzzzHub sees on this computer (Claude Code and Codex sessions): name, engine, "
                    "project and status. Use it to find who to write to.",
     "inputSchema": {"type": "object", "properties": {
         "project": {"type": "string", "description": "Only agents of this project (optional)."}}}},
    {"name": "send_to_agent",
     "description": "Sends a message to another agent through BuzzzHub (Claude or Codex). It arrives as a new request "
                    "in that agent's conversation and may wake it up, so write only when you need it: one clear "
                    "request with the context it needs, no thanks or acknowledgements. Its answer is not returned here; "
                    "ask it to write back with this same tool if you need one.",
     "inputSchema": {"type": "object", "required": ["to", "text"], "properties": {
         "to": {"type": "string", "description": "The agent's name (as list_agents shows it) or its session id."},
         "text": {"type": "string", "description": "The message."},
         "from_name": {"type": "string", "description": "Your own name, so the other agent knows who wrote."}}}},
]


def port():
    try:
        return int((HERE / "cache" / "port.txt").read_text().strip())
    except (OSError, ValueError):
        return int(os.environ.get("BUZZZHUB_PORT") or 4777)


def hub(body):
    req = urllib.request.Request(f"http://127.0.0.1:{port()}/api/bridge", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as e:
        return {"ok": False, "error": f"BuzzzHub is not reachable ({e}). Is the BuzzzHub app open?"}


def call(name, args):
    if name == "list_agents":
        r = hub({"op": "list", "project": args.get("project") or ""})
        if not r.get("ok"):
            return r.get("error") or "failed", True
        lines = [f"- {a['title']} · {a['engine']} · {a['project']} · {a['status']}" for a in r["agents"]]
        return "\n".join(lines) or "No agents.", False
    if name == "send_to_agent":
        r = hub({"op": "send", "to": args.get("to") or "", "text": args.get("text") or "",
                 "from": args.get("from_name") or ""})
        return (r.get("info") or r.get("error") or "failed"), not r.get("ok")
    return f"Unknown tool: {name}", True


def reply(mid, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": mid}
    msg.update({"error": error} if error else {"result": result})
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main():
    for s in (sys.stdin, sys.stdout):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            m = json.loads(line)
        except ValueError:
            continue
        mid, method, params = m.get("id"), m.get("method"), m.get("params") or {}
        if mid is None:                    # a notification: nothing to answer
            continue
        if method == "initialize":
            reply(mid, {"protocolVersion": params.get("protocolVersion") or "2025-06-18",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "buzzzhub", "version": VERSION}})
        elif method == "tools/list":
            reply(mid, {"tools": TOOLS})
        elif method == "tools/call":
            text, err = call(params.get("name"), params.get("arguments") or {})
            reply(mid, {"content": [{"type": "text", "text": text}], "isError": err})
        elif method == "ping":
            reply(mid, {})
        else:
            reply(mid, error={"code": -32601, "message": f"Method not found: {method}"})


if __name__ == "__main__":
    main()
