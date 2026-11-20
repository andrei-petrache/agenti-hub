"""Codex (OpenAI) sessions next to the Claude ones.

Reads the sessions Codex writes in ~/.codex/sessions (one rollout-*.jsonl per thread, sub-agents included) and
drives them with the codex CLI: the one in PATH, or the one that ships inside the Codex desktop app.
Reading costs nothing; every command that makes Codex work uses the ChatGPT plan, not the Claude one.
"""
import json
import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

HOME = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
SESSIONS = HOME / "sessions"
NAMES = HOME / "session_index.jsonl"
NO_WIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
EFFORTS = ["low", "medium", "high", "xhigh", "max", "ultra"]
BUSY_STALE = 15 * 60        # s: a turn that wrote nothing for this long is not really running any more
OPEN_CALL_WAIT = 10 * 60    # s: a tool call with no result for this long is waiting for you (an approval in the app)
AWAKE = 3 * 3600

# Codex tool calls shown with the Claude tool they match (picks the spot in the workshop room)
ITEM_TOOL = {"CommandExecution": "Bash", "FileChange": "Edit", "Extension": "WebSearch", "ImageView": "Read",
             "McpToolCall": "MCP", "SubAgentActivity": "Agent"}


# ---------------------------------------------------------------- the codex command
_exe = {"t": 0, "v": None}


def exe():
    """Path of the codex CLI, or None. The desktop app keeps it in its (versioned) install folder."""
    if time.time() - _exe["t"] < 600:
        return _exe["v"]
    v = shutil.which("codex")
    if not v and os.name == "nt":
        try:
            r = subprocess.run(["powershell", "-NoProfile", "-Command",
                                "(Get-AppxPackage -Name OpenAI.Codex).InstallLocation"],
                               capture_output=True, timeout=30, creationflags=NO_WIN)
            for loc in r.stdout.decode("utf-8", "replace").strip().splitlines()[::-1]:
                c = Path(loc.strip()) / "app" / "resources" / "codex.exe"
                if loc.strip() and c.exists():
                    v = str(c)
                    break
        except (OSError, subprocess.SubprocessError):
            pass
    _exe.update(t=time.time(), v=v)
    return v


def available():
    return SESSIONS.is_dir() or bool(exe())


# ---------------------------------------------------------------- reading
def fix_text(s):
    """The desktop app sometimes stores Romanian text decoded twice (ă -> "Ä\\udc83"): undo that."""
    if not isinstance(s, str) or not re.search(r"[ÄČĂÈÃ]|[\udc80-\udcff]", s):
        return s
    for enc in ("cp1250", "cp1252", "latin-1"):
        try:
            return s.encode(enc, "surrogateescape").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    return s


def short(s, n=140):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


_meta = {}


def meta(f: Path):
    """session_meta of a rollout file (first line): id, cwd, parent, sub-agent kind..."""
    key = str(f)
    if key in _meta:
        return _meta[key]
    m = None
    try:
        with open(f, encoding="utf-8", errors="replace") as fh:
            d = json.loads(fh.readline())
        if d.get("type") == "session_meta":
            p = d.get("payload") or {}
            src = p.get("source")
            sub = src.get("subagent") if isinstance(src, dict) else None
            spawn = (sub or {}).get("thread_spawn") if isinstance(sub, dict) else None
            m = {"id": p.get("id"), "cwd": p.get("cwd"), "originator": p.get("originator"),
                 "parent": p.get("parent_thread_id") or (spawn or {}).get("parent_thread_id"),
                 "sub": bool(sub), "nickname": p.get("agent_nickname") or (spawn or {}).get("agent_nickname"),
                 "sub_kind": (sub or {}).get("other") if isinstance(sub, dict) else None,
                 "branch": (p.get("git") or {}).get("branch") if isinstance(p.get("git"), dict) else None,
                 "t": p.get("timestamp")}
    except (OSError, ValueError):
        m = None
    if m and m.get("id"):
        _meta[key] = m
    return m


def all_files():
    if not SESSIONS.is_dir():
        return []
    try:
        return list(SESSIONS.glob("*/*/*/rollout-*.jsonl"))
    except OSError:
        return []


_names = {"mt": None, "v": {}}


def names():
    """Thread names (what the app shows), from session_index.jsonl; the last line for an id wins."""
    try:
        mt = NAMES.stat().st_mtime
    except OSError:
        return {}
    if _names["mt"] != mt:
        v = {}
        try:
            for ln in open(NAMES, encoding="utf-8", errors="replace"):
                try:
                    d = json.loads(ln)
                except ValueError:
                    continue
                if d.get("id") and d.get("thread_name"):
                    v[d["id"]] = fix_text(d["thread_name"])
        except OSError:
            pass
        _names.update(mt=mt, v=v)
    return _names["v"]


def rename(sid, name):
    """Same line the app writes when a thread is renamed."""
    with open(NAMES, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"id": sid, "thread_name": name,
                             "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                            ensure_ascii=False) + "\n")


def _item_text(it):
    t = it.get("type")
    if t == "CommandExecution":
        pc = it.get("parsed_cmd") or []
        cmd = pc[0].get("cmd") if pc and isinstance(pc[0], dict) else None
        if not cmd:
            c = it.get("command")
            cmd = c[-1] if isinstance(c, list) and c else c
        return short(cmd, 160)
    if t == "FileChange":
        ch = it.get("changes") or {}
        return short(", ".join(Path(k).name for k in list(ch)[:4]), 160)
    if t == "McpToolCall":
        a = it.get("arguments") or {}
        title = a.get("title") if isinstance(a, dict) else None
        return short(f"{it.get('server')}.{it.get('tool')}" + (f" · {fix_text(title)}" if title else ""), 160)
    if t == "Extension":
        return short(it.get("query") or it.get("tool") or it.get("kind"), 160)
    if t == "ImageView":
        return short(Path(str(it.get("path") or "").replace("file:///", "")).name, 160)
    if t == "SubAgentActivity":
        return short(f"{it.get('agent_path') or ''} {it.get('kind') or ''}", 160)
    return ""


def _content_text(content):
    out = []
    for c in content or []:
        if isinstance(c, dict) and isinstance(c.get("text"), str):
            out.append(c["text"])
    return fix_text("\n".join(out)).strip()


def parse(f: Path):
    m = meta(f) or {}
    first = last_prompt = last_text = model = effort = reply_ts = turn_ts = asks = rate = last_ts = None
    busy = False
    prompts, events, cwds, calls = [], [], {}, set()
    start = m.get("cwd")
    try:
        fh = open(f, encoding="utf-8", errors="replace")
    except OSError:
        fh = []
    for ln in fh:
        if not ln.startswith("{"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        typ, p, ts = d.get("type"), d.get("payload") or {}, d.get("timestamp")
        last_ts = ts or last_ts
        pt = p.get("type") if isinstance(p, dict) else None
        if typ == "turn_context":
            if p.get("cwd"):
                cwds[p["cwd"]] = cwds.get(p["cwd"], 0) + 1
            model = p.get("model") or model
            effort = p.get("effort") or effort
        elif typ == "response_item" and pt == "configuration_update":
            effort = (p.get("reasoning") or {}).get("effort") or effort
        elif typ == "response_item" and pt in ("custom_tool_call", "function_call", "local_shell_call"):
            if p.get("call_id"):
                calls.add(p["call_id"])
        elif typ == "response_item" and pt and pt.endswith("_output"):
            calls.discard(p.get("call_id"))
        elif typ == "event_msg":
            if pt == "thread_settings_applied":
                s = p.get("thread_settings") or {}
                model = s.get("model") or model
                effort = s.get("reasoning_effort") or effort
            elif pt == "task_started":
                busy, turn_ts, asks = True, ts, None
                calls.clear()
            elif pt in ("task_complete", "turn_aborted"):
                busy, asks, reply_ts = False, None, ts
                if p.get("last_agent_message"):
                    last_text = fix_text(p["last_agent_message"]).strip()
            elif pt == "token_count":
                rate = p.get("rate_limits") or rate
            elif "approval" in str(pt) and "request" in str(pt):
                asks = "approval"
            elif pt == "item_completed":
                it = p.get("item") or {}
                it_t = it.get("type")
                asks = None if it_t not in ("Reasoning",) else asks
                if it_t == "UserMessage":
                    txt = _content_text(it.get("content"))
                    if txt and not txt.startswith("<"):
                        first = first or txt
                        last_prompt = txt
                        if len(prompts) < 3:
                            prompts.append(txt[:600])
                        events.append((ts, "you", short(txt, 220), None))
                elif it_t == "AgentMessage":
                    txt = _content_text(it.get("content"))
                    if txt:
                        last_text = txt
                        events.append((ts, "text", short(txt, 220), None))
                elif it_t in ITEM_TOOL:
                    tool = ITEM_TOOL[it_t]
                    if it_t == "Extension" and "search" not in str(it.get("kind")):
                        tool = "MCP"
                    events.append((ts, "tool", _item_text(it), tool))
    if hasattr(fh, "close"):
        fh.close()
    from usage import _ts
    return {
        "title": names().get(m.get("id")),
        "first": short(first, 34) if first else None,
        "cwd": max(cwds, key=cwds.get) if cwds else start, "cwd_start": start,
        "cwds": sorted(cwds.items(), key=lambda kv: -kv[1]) or ([(start, 1)] if start else []),
        "branch": m.get("branch"), "model": model, "effort": effort,
        "reply_t": _ts(reply_ts) if reply_ts else 0,
        "prompts": prompts, "last_prompt": short(last_prompt, 1500) if last_prompt else None,
        "last_text": last_text[:1500] if last_text else None,
        "last_t": _ts(last_ts) if last_ts else 0,
        "busy": busy, "open_call": bool(calls) and busy, "turn_t": _ts(turn_ts) if turn_ts else 0, "asks": asks, "rate": rate,
        "feed": [{"ts": e[0], "kind": e[1], "text": e[2], "tool": e[3]} for e in events[-14:]],
    }


_cache = {}


def session(f: Path, st):
    key = str(f)
    c = _cache.get(key)
    if c and c[0] == (st.st_mtime, st.st_size):
        return c[1]
    p = parse(f)
    _cache[key] = ((st.st_mtime, st.st_size), p)
    return p


def threads(since):
    """[(file, stat, meta, [(sub file, stat, meta)])] for main threads written to since `since`."""
    files = all_files()
    stats, children = {}, {}
    for f in files:
        m = meta(f)
        if not m:
            continue
        try:
            stats[f] = f.stat()
        except OSError:
            continue
        if m["sub"] and m.get("parent"):
            children.setdefault(m["parent"], []).append(f)
    out = []
    for f, st in stats.items():
        m = meta(f)
        if m["sub"]:
            continue
        kids = [(k, stats[k], meta(k)) for k in children.get(m["id"], []) if k in stats]
        newest = max([st.st_mtime] + [k[1].st_mtime for k in kids])
        if newest >= since:
            out.append((f, st, m, kids))
    return out


def status(p, subs, mtime, now_t):
    age = now_t - mtime
    if p.get("asks"):
        return "stuck", {"k": "asks", "kind": "approval", "mode": "codex"}
    sub_active = any(not s["done"] for s in subs)
    if p.get("busy") and p.get("open_call") and OPEN_CALL_WAIT < age < AWAKE and not sub_active:
        return "stuck", {"k": "asks", "kind": "approval", "mode": "codex"}    # e.g. an approval shown in the app
    if p.get("busy") and age < (OPEN_CALL_WAIT if p.get("open_call") else BUSY_STALE) or sub_active:
        ev = next((e for e in reversed(p["feed"]) if e["kind"] == "tool"), None)
        if ev and age < 120:
            return "working", {"k": "tool", "tool": ev["tool"], "text": ev["text"]}
        return "working", {"k": "subagents" if sub_active else "thinking"}
    if age < AWAKE:
        return "waiting", {"k": "done"}
    return "sleeping", {"k": "sleeping"}


def subagents(kids, now_t):
    out = []
    for f, st, m in sorted(kids, key=lambda k: -k[1].st_mtime)[:14]:
        p = session(f, st)
        mt = max(st.st_mtime, p["last_t"])        # Windows updates mtime late for files kept open
        done = not p["busy"] or now_t - mt > BUSY_STALE
        ev = next((e for e in reversed(p["feed"]) if e["kind"] in ("tool", "text")), None)
        out.append({"id": m["id"], "description": m.get("nickname") or p.get("title")
                    or ("Guardian review" if m.get("sub_kind") == "guardian" else "sub-agent"),
                    "type": m.get("sub_kind"), "done": done, "mtime": mt, "age": now_t - mt,
                    "now": {"tool": ev["tool"], "text": ev["text"][:80]} if ev and not done else None})
    return out


def models():
    """[(slug, name, [efforts])] from the app's model cache."""
    try:
        d = json.loads((HOME / "models_cache.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    ms = d.get("models") if isinstance(d, dict) else d
    out = []
    for m in ms or []:
        if not isinstance(m, dict) or not m.get("slug") or "review" in m["slug"]:
            continue
        lv = [e.get("effort") if isinstance(e, dict) else e for e in m.get("supported_reasoning_levels") or []]
        out.append((m["slug"], m.get("display_name") or m["slug"], [e for e in lv if e]))
    return out


# ---------------------------------------------------------------- driving it
BG = {}                     # thread id -> Popen of a `codex exec` BuzzzHub started in the background
RELAY = Path(__file__).resolve().parent / "relay"


def flags(choice):
    out = []
    if (choice or {}).get("model"):
        out += ["-m", choice["model"]]
    if (choice or {}).get("effort") in EFFORTS:
        out += ["-c", f'model_reasoning_effort="{choice["effort"]}"']
    return out


def running(sid):
    pr = BG.get(sid)
    return bool(pr) and pr.poll() is None


def _spawn(args, cwd, tag):
    """Starts codex without a window; its JSON events go to relay/codex-<tag>.log. Returns (Popen, log)."""
    RELAY.mkdir(exist_ok=True)
    if not cwd or not Path(cwd).is_dir():
        cwd = str(Path.home())
    log = RELAY / f"codex-{tag}.log"
    fh = open(log, "wb")
    pr = subprocess.Popen([exe()] + args, cwd=cwd, stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT,
                          creationflags=NO_WIN)
    return pr, log


def thread_id_from(log, wait=40):
    """The thread id of a starting `codex exec --json` (its first event)."""
    end = time.time() + wait
    while time.time() < end:
        try:
            for ln in log.read_text(encoding="utf-8", errors="replace").splitlines():
                if '"thread.started"' in ln:
                    return json.loads(ln).get("thread_id")
        except (OSError, ValueError):
            pass
        time.sleep(0.5)
    return None


def resume_bg(sid, text, cwd, choice=None):
    """A message to a closed thread: `codex exec resume <id> <text>` in the background (same thread)."""
    if running(sid):
        return False, "codex_running", {}
    pr, _ = _spawn(["exec", "resume", sid, "--skip-git-repo-check", "--json"] + flags(choice) + [text],
                   cwd, sid[:8])
    BG[sid] = pr
    return True, "codex_started_msg", {}


def new_bg(text, cwd, choice=None):
    """A new thread working in the background; it may edit files inside its folder only."""
    tag = "new-" + str(int(time.time()))
    pr, log = _spawn(["exec", "-C", cwd, "--skip-git-repo-check", "-s", "workspace-write", "--json"]
                     + flags(choice) + [text], cwd, tag)
    tid = thread_id_from(log)
    if tid:
        BG[tid] = pr
    return pr, tid


def stop(sid):
    pr = BG.get(sid)
    if not pr or pr.poll() is not None:
        return False
    subprocess.run(["taskkill", "/PID", str(pr.pid), "/T", "/F"], capture_output=True, timeout=20,
                   creationflags=NO_WIN)
    return True


def cli(args, timeout=60):
    """Runs a short codex command; returns (ok, output)."""
    if not exe():
        return False, "codex not found"
    try:
        r = subprocess.run([exe()] + args, capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL,
                           creationflags=NO_WIN)
    except (OSError, subprocess.SubprocessError) as e:
        return False, str(e)
    return r.returncode == 0, (r.stdout + r.stderr).decode("utf-8", "replace").strip()


# ---------------------------------------------------------------- reviews of Claude's work
REVIEWS = {}                # Claude session id -> {"state": running|done|failed, "text", "t"}


def review(sid, cwd):
    """Codex reviews what an agent changed in its folder: uncommitted changes, else the last commit."""
    if (REVIEWS.get(sid) or {}).get("state") == "running":
        return False, "review_running", {}
    if not exe():
        return False, "no_codex", {}
    try:
        g = subprocess.run(["git", "status", "--porcelain"], cwd=cwd, capture_output=True, timeout=20,
                           creationflags=NO_WIN)
    except (OSError, subprocess.SubprocessError):
        return False, "review_no_git", {}
    if g.returncode != 0:
        return False, "review_no_git", {}
    what = ["--uncommitted"] if g.stdout.strip() else ["--commit", "HEAD"]
    RELAY.mkdir(exist_ok=True)
    out = RELAY / f"review-{sid[:8]}.md"
    REVIEWS[sid] = {"state": "running", "t": time.time(), "what": "uncommitted" if len(what) == 1 else "last_commit"}

    def run():
        try:
            out.unlink(missing_ok=True)
            r = subprocess.run([exe(), "exec", "review"] + what + ["--ephemeral", "--skip-git-repo-check", "-o", str(out)],
                               cwd=cwd, capture_output=True, timeout=1800, stdin=subprocess.DEVNULL,
                               creationflags=NO_WIN)
            text = out.read_text(encoding="utf-8", errors="replace").strip() if out.exists() else ""
            if r.returncode == 0 and text:
                REVIEWS[sid].update(state="done", text=text[:12000], t=time.time())
            else:
                err = (r.stdout + r.stderr).decode("utf-8", "replace").strip()
                REVIEWS[sid].update(state="failed", text=short(err, 400), t=time.time())
        except (OSError, subprocess.SubprocessError) as e:
            REVIEWS[sid].update(state="failed", text=str(e), t=time.time())

    threading.Thread(target=run, daemon=True).start()
    return True, "review_started", {}
