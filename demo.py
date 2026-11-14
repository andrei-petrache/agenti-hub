"""Made-up data for demo mode (screenshots, presentations): python server.py --demo"""
import time


def _iso(seconds_ago):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - seconds_ago)) + ".000Z"


def _agent(id_, title, project, status, activity, age, prompt, text, feed, subagents=(), running=True,
           branch="main", mode="terminal", asks=None):
    now = time.time()
    return {
        "id": id_, "title": title, "has_title": True, "project": project,
        "cwd": f"C:\\Users\\demo\\{project.lower().replace(' ', '-')}", "cwd_start": None, "branch": branch,
        "model": "claude-opus-5-5", "wsl": False, "running": running, "live_name": title,
        "mode": mode if running else None, "pid": None, "job": id_[-8:], "asks": asks,
        "mtime": now - age, "age": age, "status": status, "activity": activity,
        "last_prompt": prompt, "last_text": text,
        "feed": [{"ts": _iso(s), "kind": k, "text": x, "tool": tool}
                 for s, k, x, tool in sorted(feed, key=lambda e: -e[0])],          # chronological, like real data
        "subagents": [{"id": f"s{i}", "description": d, "type": "general-purpose", "done": done,
                       "mtime": now - a, "age": a,
                       "now": None if done else {"tool": rest[0], "text": rest[1]} if rest else None}
                      for i, (d, done, a, *rest) in enumerate(subagents)],
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
                          ("Summarise open PRs", True, 900)]),
        _agent(_id(2), "backend", P, "working", tool("Edit", "payments.py"), 2,
               "implement card payments",
               "The /pay endpoint is done, writing the refund tests.",
               [(2, "tool", "payments.py", "Edit"), (30, "tool", "Run the tests", "Bash"),
                (70, "text", "Payment tests pass. Refunds are next.", None),
                (120, "tool", "→ review: PR #42 is ready for review", "SendMessage")], branch="feat/payments"),
        _agent(_id(9), "research", P, "working", tool("WebSearch", "SCA rules for online payments 2026"), 3,
               "find out what the law requires for card payments", "Found the PSD2 rules, checking SCA now.",
               [(3, "tool", "SCA rules for online payments 2026", "WebSearch"),
                (60, "text", "Found the PSD2 rules, checking SCA now.", None)]),
        _agent(_id(3), "frontend", P, "waiting", {"k": "idle", "mode": "background"}, 240,
               "build the cart page", "The cart page is done and tested on mobile. Shall I add coupons?",
               [(240, "text", "The cart page is done and tested on mobile.", None),
                (300, "tool", "Screenshot of the cart on mobile", "Bash"), (600, "tool", "Cart.tsx", "Write")],
               branch="feat/cart", mode="background"),
        _agent(_id(4), "review", P, "stuck", {"k": "asks", "kind": "approval", "mode": "background"}, 600,
               "review the team's PRs", "Starting with PR #42 from backend.",
               [(600, "tool", "gh pr checkout 42", "Bash"), (650, "text", "Starting with PR #42 from backend.", None)],
               mode="background", asks="approval"),
        _agent(_id(5), "docs", P, "sleeping", {"k": "closed"}, 5 * 3600,
               "write the install guide", "The guide is ready in docs/install.md.",
               [(5 * 3600, "text", "The guide is ready in docs/install.md.", None)], running=False),
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
        {"name": P, "emoji": "🛒", "color": "#f2a65a", "description": "ops, backend, frontend, review, research"},
        {"name": "Landing page", "emoji": "🌐", "color": "#8fb996", "description": "site + check"},
        {"name": "Platformer game", "emoji": "🎮", "color": "#b48ac7", "description": "levels and art"},
    ]
    for p in projects:
        p["agents"] = [a for a in agents if a["project"] == p["name"]]
    return {"now": time.time(), "projects": projects, "links": link_list, "live_ok": True}
