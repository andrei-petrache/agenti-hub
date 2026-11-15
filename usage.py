"""Token usage of every Claude Code session, from the `usage` block Claude writes into each transcript.

No API calls and no tokens: it only reads local files. Transcripts can be huge (hundreds of MB in
total), so each file is read once and then only its new bytes; the running totals are kept in
cache/usage.json between starts.

Each assistant message is written on several lines (one per content block) with the same usage, so
messages are counted once, by message id.
"""
import json
import re
import threading
import time
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE_FILE = HERE / "cache" / "usage.json"
VERSION = 7

CACHE_TTL = 3600            # Claude Code writes its prompt cache with a 1-hour lifetime
REBUILD_MIN = 20_000
SLOT = 600                  # usage is also kept in 10-minute buckets, for any period the user picks        # a cache write this big after a long pause = the whole context re-processed

# $ per million tokens: (input, output, cache read). Cache writes: 1.25x input (5 min), 2x input (1 h).
# Anthropic list prices (Nov 2026); an estimate only, subscriptions are not billed per token.
PRICES = [
    ("fable-5-2", 8, 40, 0.20), ("mythos-5-2", 8, 40, 0.20),
    ("fable-5-1", 10, 50, 0.25), ("mythos-5-1", 10, 50, 0.25),
    ("fable-5", 10, 50, 1.00), ("mythos-5", 10, 50, 1.00),
    ("opus-5-5", 4, 20, 0.20), ("opus-5", 5, 25, 0.50),
    ("opus-4-8", 5, 25, 0.50), ("opus-4-7", 5, 25, 0.50), ("opus-4-6", 5, 25, 0.50), ("opus-4-5", 5, 25, 0.50),
    ("opus-4", 15, 75, 1.50),
    ("sonnet-5-5", 2, 10, 0.10), ("sonnet-5", 2, 10, 0.20), ("sonnet-4", 3, 15, 0.30), ("sonnet-3", 3, 15, 0.30),
    ("haiku-5-5", 0.10, 0.50, 0.01), ("haiku-4-5", 1, 5, 0.10), ("haiku-3-5", 0.80, 4, 0.08), ("haiku", 0.25, 1.25, 0.03),
]


def price(model):
    m = (model or "").lower()
    for key, i, o, r in PRICES:
        if key in m:
            return i, o, r
    return None


def family(model):
    m = (model or "").lower()
    for f in ("fable", "mythos", "opus", "sonnet", "haiku"):
        if f in m:
            return f
    return "other"


def cost(model, u, fast=False):
    p = price(model)
    if not p:
        return 0.0
    i, o, r = p
    c = (u.get("in", 0) * i + u.get("out", 0) * o + u.get("cr", 0) * r
         + u.get("cw5", 0) * i * 1.25 + u.get("cw1h", 0) * i * 2) / 1e6
    return c * (2 if fast else 1)


def _empty():
    return {"in": 0, "out": 0, "cr": 0, "cw5": 0, "cw1h": 0, "think": 0, "req": 0, "cost": 0.0}


def _add(a, b):
    for k in ("in", "out", "cr", "cw5", "cw1h", "think", "req", "cost"):
        a[k] = a.get(k, 0) + b.get(k, 0)
    return a


def total(u):
    return u.get("in", 0) + u.get("out", 0) + u.get("cr", 0) + u.get("cw5", 0) + u.get("cw1h", 0)


def _ts(s):
    try:
        return time.mktime(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------- per-file state
def _new_state():
    return {"off": 0, "seen": [], "models": {}, "hours": {}, "first": 0, "last": 0, "context": 0,
            "max_context": 0, "rebuilds": 0, "rebuild_tokens": 0, "think": 0, "cross_msgs": 0,
            "cross_tokens": 0, "slots": {}, "ctx_hist": [[0, 0] for _ in range(11)]}


def _scan(path: Path, st, s):
    """Reads the new bytes of one transcript and adds them to state s."""
    size = st.st_size
    if size < s["off"]:
        s.clear()
        s.update(_new_state())
    if size == s["off"]:
        return s
    seen = deque(s["seen"], maxlen=64)
    pending_cross = False
    with open(path, "rb") as f:
        f.seek(s["off"])
        data = f.read(size - s["off"])
    end = data.rfind(b"\n") + 1
    for ln in data[:end].split(b"\n"):
        if b"cross-session-message" in ln and b'"type":"user"' in ln.replace(b" ", b""):
            pending_cross = True             # the next request is a turn started by another session
            s["cross_msgs"] += 1
            continue
        if b'"compact_boundary"' in ln and b'"compactMetadata"' in ln:
            try:                             # summarised: the next step re-reads only what is left
                post = (json.loads(ln).get("compactMetadata") or {}).get("postTokens")
                if post:
                    s["context"] = post
            except ValueError:
                pass
            continue
        if b'"usage"' not in ln or b'"assistant"' not in ln:
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        m = d.get("message") or {}
        mid = m.get("id") or d.get("requestId")
        u = m.get("usage")
        if not u or not mid or mid in seen:
            continue
        seen.append(mid)
        model = m.get("model") or "?"
        if model.startswith("<"):            # "<synthetic>" messages are not billed
            continue
        cc = u.get("cache_creation") or {}
        cw1h = cc.get("ephemeral_1h_input_tokens")
        cw5 = cc.get("ephemeral_5m_input_tokens")
        cw = u.get("cache_creation_input_tokens", 0) or 0
        if cw1h is None and cw5 is None:
            cw5, cw1h = cw, 0
        one = {"in": u.get("input_tokens", 0) or 0, "out": u.get("output_tokens", 0) or 0,
               "cr": u.get("cache_read_input_tokens", 0) or 0, "cw5": cw5 or 0, "cw1h": cw1h or 0,
               "think": ((u.get("output_tokens_details") or {}).get("thinking_tokens") or 0), "req": 1}
        one["cost"] = cost(model, one, u.get("speed") == "fast")
        _add(s["models"].setdefault(model, _empty()), one)
        t = _ts(d.get("timestamp"))
        if t:
            h = str(int(t // 3600))
            hb = s["hours"].setdefault(h, {"tok": 0, "cost": 0.0})
            hb["tok"] += total(one)
            hb["cost"] += one["cost"]
            hb["req"] = hb.get("req", 0) + 1            # for the average context read per step
            hb["ctx"] = hb.get("ctx", 0) + one["in"] + one["cr"] + one["cw5"] + one["cw1h"]
            sl = s.setdefault("slots", {}).setdefault(str(int(t // SLOT)), {"tok": 0, "cost": 0.0, "req": 0, "ctx": 0,
                                                                               "cr": 0, "inp": 0, "out": 0, "m": {}})
            sl["tok"] += total(one)                      # 10-minute buckets: any period can be added up
            sl["cost"] += one["cost"]
            sl["req"] += 1
            sl["ctx"] += one["in"] + one["cr"] + one["cw5"] + one["cw1h"]
            sl["cr"] += one["cr"]
            sl["inp"] += one["in"] + one["cr"] + one["cw5"] + one["cw1h"]
            sl["out"] += one["out"]
            mm = sl["m"].setdefault(model, [0, 0.0])
            mm[0] += total(one)
            mm[1] += one["cost"]
            gap = t - s["last"] if s["last"] else 0
            if gap > CACHE_TTL and one["cw5"] + one["cw1h"] > REBUILD_MIN:
                s["rebuilds"] += 1                       # cache had expired: whole context written again
                s["rebuild_tokens"] += one["cw5"] + one["cw1h"]
            s["first"] = s["first"] or t
            s["last"] = max(s["last"], t)
        ctx = one["in"] + one["cr"] + one["cw5"] + one["cw1h"]
        b = s["ctx_hist"][min(ctx // 100_000, 10)]      # context size per request, 100k buckets
        b[0] += 1
        b[1] += ctx
        if not d.get("isSidechain"):
            s["context"] = ctx
            s["max_context"] = max(s["max_context"], ctx)
        if pending_cross:
            s["cross_tokens"] += total(one)
            pending_cross = False
    s["off"] += end
    s["seen"] = list(seen)
    return s


# ---------------------------------------------------------------- the index
class Index:
    def __init__(self):
        self.lock = threading.Lock()
        self.files = {}
        self.ready = False
        try:
            raw = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if raw.get("v") == VERSION:
                self.files = raw.get("files", {})
        except (OSError, ValueError):
            pass
        self._dirty = False
        self._saved = time.time()

    def file(self, path: Path, st=None):
        """Usage state of one transcript, brought up to date (reads only new bytes)."""
        key = str(path)
        try:
            st = st or path.stat()
        except OSError:
            return None
        with self.lock:
            s = self.files.get(key)
            if s is None:
                s = self.files[key] = _new_state()
            if st.st_size != s["off"]:
                _scan(path, st, s)
                self._dirty = True
            return s

    def session(self, path: Path, st=None, rng=None):
        """The session's own usage plus its sub-agents' usage (subagents/*.jsonl next to it)."""
        own = self.file(path, st)
        if own is None:
            return None
        subs = []
        sd = path.with_suffix("") / "subagents"
        if sd.is_dir():
            try:
                for jl in sd.glob("*.jsonl"):
                    s = self.file(jl)
                    if s:
                        subs.append((jl.stem, s))
            except OSError:
                pass
        return summarize(own, subs, rng)

    def save(self, force=False):
        if not self._dirty or (not force and time.time() - self._saved < 30):
            return
        with self.lock:
            data = json.dumps({"v": VERSION, "files": self.files}, separators=(",", ":"))
            self._dirty = False
            self._saved = time.time()
        try:
            CACHE_FILE.parent.mkdir(exist_ok=True)
            tmp = CACHE_FILE.with_suffix(".tmp")
            tmp.write_text(data, encoding="utf-8")
            tmp.replace(CACHE_FILE)
        except OSError:
            pass

    def warm(self, roots):
        """Background: index every transcript once, so the first screen doesn't wait."""
        def run():
            for root in roots:
                try:
                    for f in root.glob("*/*.jsonl"):
                        self.session(f)
                except OSError:
                    pass
            self.ready = True
            self.save(force=True)
        threading.Thread(target=run, daemon=True).start()


def _merge_hours(dst, hours):
    for h, v in hours.items():
        b = dst.setdefault(h, {"tok": 0, "cost": 0.0})
        b["tok"] += v["tok"]
        b["cost"] += v["cost"]


def window_of(own, subs, rng):
    """Usage of the session (with its sub-agents) between rng = (start, end, bin seconds), from the 10-min buckets."""
    a, b, step = rng
    lo, hi = int(a // SLOT), int((b - 1) // SLOT)
    nb = max(1, int(-(-(b - a) // step)))
    w = {"tok": 0, "cost": 0.0, "req": 0, "cr": 0, "inp": 0, "out": 0, "sub_tok": 0, "own_req": 0, "own_ctx": 0,
         "models": {}, "bins": [0] * nb, "active": 0}
    active = set()
    for i, s in enumerate([own] + [x for _, x in subs]):
        for k, v in (s.get("slots") or {}).items():
            k = int(k)
            if not lo <= k <= hi:
                continue
            active.add(k)
            for f in ("tok", "cost", "req", "cr", "inp", "out"):
                w[f] += v[f]
            if i == 0:
                w["own_req"] += v["req"]
                w["own_ctx"] += v["ctx"]
            else:
                w["sub_tok"] += v["tok"]
            for m, (tk, c) in v["m"].items():
                x = w["models"].setdefault(m, {"tok": 0, "cost": 0.0})
                x["tok"] += tk
                x["cost"] += c
            j = min(nb - 1, max(0, int((k * SLOT - a) // step)))
            w["bins"][j] += v["tok"]
    w["active"] = len(active) * SLOT                     # seconds in which it actually worked
    w["cost"] = round(w["cost"], 4)
    w["step"] = round(w["own_ctx"] / w["own_req"]) if w["own_req"] else None
    for x in w["models"].values():
        x["cost"] = round(x["cost"], 4)
    return w


def summarize(own, subs, rng=None):
    """Compact usage summary of a session for the API (all numbers, no texts)."""
    now_h = int(time.time() // 3600)
    models = {}
    for m, u in own["models"].items():
        _add(models.setdefault(m, _empty()), u)
    sub_total = _empty()
    sub_list = []
    hours = {}
    _merge_hours(hours, own["hours"])
    for name, s in subs:
        st = _empty()
        for m, u in s["models"].items():
            _add(models.setdefault(m, _empty()), u)
            _add(st, u)
        _add(sub_total, st)
        _merge_hours(hours, s["hours"])
        sub_list.append({"id": name, "tok": total(st), "cost": round(st["cost"], 4)})
    all_ = _empty()
    for u in models.values():
        _add(all_, u)

    def window(n_hours):
        tok = cst = 0
        for h, v in hours.items():
            if now_h - int(h) < n_hours:
                tok += v["tok"]
                cst += v["cost"]
        return {"tok": tok, "cost": round(cst, 4)}

    def per_step(n_hours):
        """Average context read per step (each reply or tool call) of the session itself, sub-agents left out:
        the number that drops when the agent compacts or starts fresh."""
        req = ctx = 0
        for h, v in own["hours"].items():
            if now_h - int(h) < n_hours:
                req += v.get("req", 0)
                ctx += v.get("ctx", 0)
        return round(ctx / req) if req else None

    def step_spark():
        out = []
        for i in range(23, -1, -1):
            v = own["hours"].get(str(now_h - i)) or {}
            out.append(round(v["ctx"] / v["req"]) if v.get("req") else 0)
        return out

    inputs = all_["in"] + all_["cr"] + all_["cw5"] + all_["cw1h"]
    return {
        "per_step": {"day": per_step(24), "week": per_step(24 * 7)}, "step_spark": step_spark(),
        "tok": total(all_), "cost": round(all_["cost"], 4),
        "in": all_["in"], "out": all_["out"], "cr": all_["cr"], "cw": all_["cw5"] + all_["cw1h"],
        "think": all_["think"], "req": all_["req"],
        "cache_hit": round(all_["cr"] / inputs, 3) if inputs else None,
        "hour": window(1), "day": window(24),
        "spark": [hours.get(str(now_h - i), {}).get("tok", 0) for i in range(23, -1, -1)],
        "models": {m: {"tok": total(u), "cost": round(u["cost"], 4), "out": u["out"], "req": u["req"]}
                   for m, u in models.items()},
        "sub_tok": total(sub_total), "sub_cost": round(sub_total["cost"], 4),
        "subs": sorted(sub_list, key=lambda x: -x["tok"])[:20],
        "context": own["context"], "max_context": own["max_context"],
        "rebuilds": own["rebuilds"], "rebuild_tok": own["rebuild_tokens"],
        "cross_msgs": own["cross_msgs"], "cross_tok": own["cross_tokens"],
        "ctx_hist": _hist(own, subs),
        "first": own["first"], "last": own["last"],
        "hours": {h: v for h, v in hours.items() if now_h - int(h) < 24 * 31},
        "win": window_of(own, subs, rng) if rng else None,
    }


def _hist(own, subs):
    h = [[0, 0] for _ in range(11)]
    for s in [own] + [x for _, x in subs]:
        for i, (n, t) in enumerate(s.get("ctx_hist") or []):
            h[i][0] += n
            h[i][1] += t
    return h


def compact_saving(hist, window):
    """Context tokens saved if Claude compacted at `window` tokens. After a compaction the context
    restarts small and grows again, so requests that went past the window would average ~window/2."""
    saved = 0
    for i, (n, t) in enumerate(hist):
        if n and i * 100_000 >= window:
            saved += max(0, t - n * window / 2)
    return saved


def tips(u, model=None):
    """Local, rule-based suggestions for one session: list of (code, params). The UI writes the text."""
    if not u or not u["req"]:
        return []
    out = []
    if u["context"] >= 150_000:
        out.append(("big_context", {"k": round(u["context"] / 1000)}))
    if u["rebuilds"] >= 2 and u["rebuild_tok"] >= 200_000:
        out.append(("rebuilds", {"n": u["rebuilds"], "k": round(u["rebuild_tok"] / 1000)}))
    if u["tok"] and u["sub_tok"] / u["tok"] >= 0.4 and u["sub_tok"] >= 2_000_000:
        out.append(("subagents", {"p": round(100 * u["sub_tok"] / u["tok"])}))
    top = max(u["models"].items(), key=lambda kv: kv[1]["cost"], default=(None, None))[0]
    if top and family(top) in ("fable", "mythos") and u["cost"] >= 5:
        out.append(("pricey_model", {"m": top}))
    if u["out"] and u["think"] / max(u["out"], 1) >= 0.7 and u["out"] >= 200_000:
        out.append(("thinking", {"p": round(100 * u["think"] / u["out"])}))
    if u["cross_msgs"] >= 5 and u["cross_tok"] >= 1_000_000:
        out.append(("cross", {"n": u["cross_msgs"], "k": round(u["cross_tok"] / 1000)}))
    return out


INDEX = Index()
