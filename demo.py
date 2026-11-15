"""Made-up data for demo mode (screenshots, presentations): python server.py --demo"""
import time

import usage as _usage_mod


def _usage(day_m, total_m, ctx_k, sub_share=0.0, model="claude-opus-5-5", shape=(1, 3, 5, 4, 6, 8, 7, 9), tips=()):
    """Made-up but consistent usage numbers (millions of tokens, context in thousands)."""
    tok = int(total_m * 1e6)
    cr, cw, out = int(tok * 0.985), int(tok * 0.011), int(tok * 0.004)
    u = {"in": 0, "out": out, "cr": cr, "cw5": 0, "cw1h": cw}
    cost = _usage_mod.cost(model, u)
    day = int(day_m * 1e6)
    weights = list(shape) + [0] * (24 - len(shape))
    weights = weights[:24][::-1]
    spark = [int(day * w / sum(weights)) for w in weights]
    hist = [[0, 0] for _ in range(11)]
    for i, n in enumerate((40, 90, 120, 80, 50, 30, 12, 6, 2, 0, 0)):
        k = min(i, ctx_k // 100 + 1)
        hist[k][0] += n
        hist[k][1] += n * (k * 100_000 + 50_000)
    step = [0 if not w else int(ctx_k * 1000 * (0.8 + 0.05 * i)) for i, w in enumerate(weights)]
    return {"per_step": {"day": int(ctx_k * 1150), "week": int(ctx_k * 1250)}, "step_spark": step,
            "tok": tok, "cost": round(cost, 2), "in": 0, "out": out, "cr": cr, "cw": cw, "think": out // 3,
            "req": sum(h[0] for h in hist), "cache_hit": 0.99,
            "hour": {"tok": spark[-1], "cost": round(cost * spark[-1] / tok, 2)},
            "day": {"tok": day, "cost": round(cost * day / tok, 2)}, "spark": spark,
            "models": {model: {"tok": tok, "cost": round(cost, 2), "out": out, "req": 300}},
            "sub_tok": int(tok * sub_share), "sub_cost": round(cost * sub_share, 2), "subs": [],
            "context": ctx_k * 1000, "max_context": int(ctx_k * 1300), "rebuilds": 0, "rebuild_tok": 0,
            "cross_msgs": 4, "cross_tok": int(ctx_k * 4000), "ctx_hist": hist, "first": 0, "last": 0,
            "win": {"tok": day, "cost": round(cost * day / tok, 2), "req": 180, "cr": int(day * 0.985), "inp": int(day * 0.996),
                    "out": int(day * 0.004), "sub_tok": int(day * sub_share), "own_req": 150, "own_ctx": 150 * int(ctx_k * 1150),
                    "step": int(ctx_k * 1150), "active": 6 * 3600, "bins": [v // 2 for v in spark for _ in (0, 1)],
                    "models": {model: {"tok": day, "cost": round(cost * day / tok, 2)}}}}, list(tips)


def _iso(seconds_ago):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - seconds_ago)) + ".000Z"


def _agent(id_, title, project, status, activity, age, prompt, text, feed, subagents=(), running=True,
           branch="main", mode="terminal", asks=None, use=None):
    now = time.time()
    return {
        "id": id_, "title": title, "has_title": True, "project": project,
        "cwd": f"C:\\Users\\demo\\{project.lower().replace(' ', '-')}", "cwd_start": None, "branch": branch,
        "model": "claude-opus-5-5", "effort": "high" if title != "research" else "medium", "pending": None, "wsl": False, "running": running, "live_name": title,
        "mode": mode if running else None, "pid": None, "job": id_[-8:], "asks": asks,
        "mtime": now - age, "age": age, "status": status, "activity": activity,
        "last_prompt": prompt, "last_text": text,
        "feed": [{"ts": _iso(s), "kind": k, "text": x, "tool": tool}
                 for s, k, x, tool in sorted(feed, key=lambda e: -e[0])],          # chronological, like real data
        "subagents": [{"id": f"s{i}", "description": d, "type": "general-purpose", "done": done,
                       "mtime": now - a, "age": a,
                       "now": None if done else {"tool": rest[0], "text": rest[1]} if rest else None}
                      for i, (d, done, a, *rest) in enumerate(subagents)],
        "usage": use[0] if use else None,
        "cache_age": age + 60, "compact": None,
        "tips": [{"k": k, "p": p} for k, p in use[1]] if use else [],
    }


def _id(n):
    return f"00000000-0000-4000-8000-{n:012d}"


def state():
    P = "Online shop"
    tool = lambda name, text: {"k": "tool", "tool": name, "text": text}
    agents = [
        _agent(_id(1), "ops", P, "working", tool("Bash", "Deploy to staging"), 4,
               "coordinate the team: backend does payments, frontend the cart, review checks",
               "I split the sprint: backend on payments, frontend on the cart. Deploying to staging.",
               [(9, "tool", "Deploy to staging", "Bash"),
                (40, "text", "Backend finished the payment endpoint, putting it on staging.", None),
                (95, "tool", "→ backend: payments are on staging, check the logs", "SendMessage"),
                (300, "you", "coordinate the team: backend does payments, frontend the cart", None)],
               subagents=[("Check staging config", False, 20, "Read", "staging.yaml"),
                          ("Test payments on staging", False, 8, "Bash", "npm run e2e"),
                          ("Summarise open PRs", True, 900)],
               use=_usage(46, 120, 380, 0.22, tips=[("big_context", {"k": 380})])),
        _agent(_id(2), "backend", P, "working", tool("Edit", "payments.py"), 2,
               "implement card payments",
               "The /pay endpoint is done, writing the refund tests.",
               [(2, "tool", "payments.py", "Edit"), (30, "tool", "Run the tests", "Bash"),
                (70, "text", "Payment tests pass. Refunds are next.", None),
                (120, "tool", "→ review: PR #42 is ready for review", "SendMessage")], branch="feat/payments",
               use=_usage(31, 64, 210)),
        _agent(_id(9), "research", P, "working", tool("WebSearch", "SCA rules for online payments 2026"), 3,
               "find out what the law requires for card payments", "Found the PSD2 rules, checking SCA now.",
               [(3, "tool", "SCA rules for online payments 2026", "WebSearch"),
                (60, "text", "Found the PSD2 rules, checking SCA now.", None)],
               use=_usage(9, 9, 90, shape=(2, 5, 3))),
        _agent(_id(3), "frontend", P, "waiting", {"k": "idle", "mode": "background"}, 240,
               "build the cart page", "The cart page is done and tested on mobile. Shall I add coupons?",
               [(240, "text", "The cart page is done and tested on mobile.", None),
                (300, "tool", "Screenshot of the cart on mobile", "Bash"), (600, "tool", "Cart.tsx", "Write")],
               branch="feat/cart", mode="background", use=_usage(12, 58, 160, shape=(0, 0, 0, 4, 8, 6))),
        _agent(_id(4), "review", P, "stuck", {"k": "asks", "kind": "approval", "mode": "background"}, 600,
               "review the team's PRs", "Starting with PR #42 from backend.",
               [(600, "tool", "gh pr checkout 42", "Bash"), (650, "text", "Starting with PR #42 from backend.", None)],
               mode="background", asks="approval", use=_usage(5, 22, 120, shape=(0, 1, 2, 3))),
        _agent(_id(5), "docs", P, "sleeping", {"k": "closed"}, 5 * 3600,
               "write the install guide", "The guide is ready in docs/install.md.",
               [(5 * 3600, "text", "The guide is ready in docs/install.md.", None)], running=False,
               use=_usage(3, 15, 70, shape=(0, 0, 0, 0, 0, 2, 3))),
        _agent(_id(6), "site", "Landing page", "working", tool("Write", "index.html"), 6,
               "redo the home page", "Redoing the top section with the new photo.",
               [(6, "tool", "index.html", "Write")]),
        _agent(_id(7), "check", "Landing page", "waiting", {"k": "idle", "mode": "terminal"}, 900,
               "check the site on mobile", "Everything looks fine, two images are too large.",
               [(900, "text", "Everything looks fine, two images are too large.", None)]),
        _agent(_id(8), "level-3", "Platformer game", "sleeping", {"k": "closed"}, 30 * 3600,
               "make level 3", "Level 3 is done.", [], running=False),
    ]
    links = [
        ("ops", "backend", 34, 95, "payments are on staging, check the logs"),
        ("ops", "frontend", 28, 400, "after the cart, build the checkout page"),
        ("backend", "ops", 22, 60, "the /pay endpoint is done"),
        ("backend", "review", 9, 120, "PR #42 is ready for review"),
        ("frontend", "ops", 17, 240, "the cart is done"),
        ("frontend", "backend", 11, 2000, "what does the /cart response look like?"),
        ("review", "backend", 7, 3000, "two comments on PR #40"),
        ("review", "ops", 5, 3500, "PR #40 approved"),
        ("ops", "review", 6, 700, "look at #42 first"),
        ("research", "backend", 3, 500, "SCA needs a second factor above 30 EUR"),
        ("@you", "ops", 4, 300, "coordinate the team"),
        ("check", "site", 3, 900, "two images are too large"),
        ("site", "check", 2, 1200, "I redid the home page, can you check?"),
    ]
    link_list = [{"from": a, "to": b, "n": n, "last": _iso(s), "recent": [{"ts": _iso(s), "text": t}]}
                 for a, b, n, s, t in links]
    projects = [
        {"name": P, "emoji": "🛒", "color": "#f2a65a", "description": "ops, backend, frontend, review, research",
         "prompt_suggestions": False},
        {"name": "Landing page", "emoji": "🌐", "color": "#8fb996", "description": "site + check"},
        {"name": "Platformer game", "emoji": "🎮", "color": "#b48ac7", "description": "levels and art"},
    ]
    for p in projects:
        p["agents"] = [a for a in agents if a["project"] == p["name"]]
    return {"now": time.time(), "projects": projects, "links": link_list, "live_ok": True,
            "range": {"from": time.time() - 86400, "to": time.time(), "step": 1800}}
