"""Date inventate pentru modul demo (capturi de ecran, prezentări): python server.py --demo"""
import time


def _iso(sec_in_urma):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - sec_in_urma)) + ".000Z"


def _agent(id_, titlu, proiect, status, activitate, varsta, prompt, text, feed, subagenti=(), pornita=True,
           branch="main", fel="terminal", intrebare=None):
    acum = time.time()
    return {
        "id": id_, "titlu": titlu, "are_titlu": True, "proiect": proiect,
        "cwd": f"C:\\Users\\demo\\{proiect.lower().replace(' ', '-')}", "branch": branch,
        "model": "claude-opus-4", "wsl": False, "pornita": pornita, "nume_live": titlu,
        "fel": fel if pornita else None, "intrebare": intrebare, "cwd_start": None, "job": id_[-8:],
        "mtime": acum - varsta, "varsta": varsta, "status": status, "activitate": activitate,
        "ultimul_prompt": prompt, "ultimul_text": text,
        "feed": [{"ts": _iso(s), "tip": t, "text": x, "tool": tool}
                 for s, t, x, tool in sorted(feed, key=lambda e: -e[0])],          # cronologic, ca în realitate
        "subagenti": [{"id": f"s{i}", "descriere": d, "tip": "general-purpose", "terminat": f, "mtime": acum - v,
                       "varsta": v, "ce": None if f else (rest[0] if rest else "lucrează…"), "unealta": None}
                      for i, (d, f, v, *rest) in enumerate(subagenti)],
    }


def _id(n):
    return f"00000000-0000-4000-8000-{n:012d}"


def stare():
    P = "Magazin online"
    agenti = [
        _agent(_id(1), "ops", P, "lucreaza", "rulează Deploy pe staging", 4,
               "coordonează echipa: backend face plata, frontend coșul, review verifică",
               "Am împărțit sprintul: backend pe plăți, frontend pe coș. Pornesc deploy-ul pe staging.",
               [(9, "tool", "Deploy pe staging", "Bash"), (40, "text", "Backend a terminat endpoint-ul de plată, îl pun pe staging.", None),
                (95, "tool", "→ backend: plata e pe staging, verifică logurile", "SendMessage"),
                (300, "tu", "coordonează echipa: backend face plata, frontend coșul", None)],
               subagenti=[("Verifică config staging", False, 20, "citește staging.yaml"),
                          ("Testează plata pe staging", False, 8, "rulează npm run e2e"),
                          ("Rezumat PR-uri deschise", True, 900)]),
        _agent(_id(9), "cercetare", P, "lucreaza", "caută pe web plăți cu cardul în UE", 3,
               "află ce cere legea pentru plăți cu cardul", "Am găsit regulile PSD2, mai verific SCA.",
               [(3, "tool", "reguli SCA plăți online 2026", "WebSearch"),
                (60, "text", "Am găsit regulile PSD2, mai verific SCA.", None)]),
        _agent(_id(2), "backend", P, "lucreaza", "editează payments.py", 2,
               "implementează plata cu cardul",
               "Endpoint-ul /pay e gata, scriu testele pentru rambursări.",
               [(2, "tool", "payments.py", "Edit"), (30, "tool", "Rulează testele", "Bash"),
                (70, "text", "Testele de plată trec. Mai am rambursările.", None),
                (120, "tool", "→ review: PR #42 e gata de verificat", "SendMessage")], branch="feat/plati"),
        _agent(_id(3), "frontend", P, "asteapta", "rulează în fundal, liberă — deschide-o în terminal ca s-o vezi", 240,
               "fă pagina de coș", "Pagina de coș e gata și testată pe mobil. Vrei să adaug și cupoane?",
               [(240, "text", "Pagina de coș e gata și testată pe mobil.", None),
                (300, "tool", "Screenshot coș pe mobil", "Bash"), (600, "tool", "Cart.tsx", "Write")],
               branch="feat/cos", fel="fundal"),
        _agent(_id(4), "review", P, "blocat", "așteaptă să-i aprobi o acțiune — deschide-l în terminal ca să-i răspunzi", 600,
               "verifică PR-urile echipei", "Încep cu PR #42 de la backend.",
               [(600, "tool", "gh pr checkout 42", "Bash"), (650, "text", "Încep cu PR #42 de la backend.", None)],
               fel="fundal", intrebare="aprobare"),
        _agent(_id(5), "docs", P, "doarme", "doarme", 5 * 3600,
               "scrie ghidul de instalare", "Ghidul e gata în docs/instalare.md.",
               [(5 * 3600, "text", "Ghidul e gata în docs/instalare.md.", None)], pornita=False),
        _agent(_id(6), "site", "Site prezentare", "lucreaza", "scrie index.html", 6,
               "refă prima pagină", "Refac secțiunea de sus cu poza nouă.",
               [(6, "tool", "index.html", "Write")]),
        _agent(_id(7), "verificare", "Site prezentare", "asteapta", "pornită, te așteaptă", 900,
               "verifică site-ul pe mobil", "Totul arată bine, două imagini sunt prea mari.",
               [(900, "text", "Totul arată bine, două imagini sunt prea mari.", None)]),
        _agent(_id(8), "nivel-3", "Joc platformer", "doarme", "sesiune închisă", 30 * 3600,
               "fă nivelul 3", "Nivelul 3 e gata.", [], pornita=False),
    ]
    legaturi = [
        ("ops", "backend", 34, 95, "plata e pe staging, verifică logurile"),
        ("ops", "frontend", 28, 400, "după coș, fă pagina de checkout"),
        ("backend", "ops", 22, 60, "endpoint-ul /pay e gata"),
        ("backend", "review", 9, 120, "PR #42 e gata de verificat"),
        ("frontend", "ops", 17, 240, "coșul e gata"),
        ("frontend", "backend", 11, 2000, "ce format are răspunsul de la /cart?"),
        ("review", "backend", 7, 3000, "două observații la PR #40"),
        ("review", "ops", 5, 3500, "PR #40 aprobat"),
        ("ops", "review", 6, 700, "uită-te la #42 cu prioritate"),
        ("Tu", "ops", 4, 300, "coordonează echipa"),
        ("verificare", "site", 3, 900, "două imagini sunt prea mari"),
        ("site", "verificare", 2, 1200, "am refăcut prima pagină, verifici?"),
    ]
    leg = [{"de": a, "la": b, "n": n, "ultim": _iso(s), "recent": [{"ts": _iso(s), "text": t}]}
           for a, b, n, s, t in legaturi]
    proiecte = [
        {"nume": P, "emoji": "🛒", "culoare": "#f2a65a", "descriere": "ops, backend, frontend, review, docs"},
        {"nume": "Site prezentare", "emoji": "🌐", "culoare": "#8fb996", "descriere": "site + verificare"},
        {"nume": "Joc platformer", "emoji": "🎮", "culoare": "#b48ac7", "descriere": "nivele și grafică"},
    ]
    for p in proiecte:
        p["agenti"] = [a for a in agenti if a["proiect"] == p["nume"]]
    return {"acum": time.time(), "proiecte": proiecte, "legaturi": leg, "live_ok": True}
