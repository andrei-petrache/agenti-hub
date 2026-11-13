<p align="center"><img src="agenti.png" width="120" alt="mascota Agenți Hub"></p>

<h1 align="center">Agenți Hub</h1>

<p align="center">Un panou mic de desktop pentru toți agenții <b>Claude Code</b> care lucrează în paralel pe PC-ul tău.<br>
Alegi proiectul și vezi fiecare agent ca o mascotă mică: ce face acum, dacă te așteaptă, cui scrie. Îi poți și trimite mesaje.</p>

---

## Ce face

- **Proiecte.** Sesiunile sunt grupate pe proiecte după numele sesiunii sau după folder. Pe prima pagină vezi câți agenți lucrează în fiecare proiect.
- **Agenți.** Fiecare sesiune are o mascotă animată după stare:
  - ⚡ **lucrează**: țopăie, iar steluța se învârte. Vezi și ce rulează, de exemplu „rulează Run all tests”.
  - 👋 **te așteaptă**: a terminat și îți face cu mâna.
  - 😅 **blocat?**: s-a oprit la o unealtă, poate așteaptă o permisiune.
  - 💤 **doarme**: sesiune închisă sau neatinsă de câteva ore.
- **Detalii.** Click pe un agent și vezi ultima ta cerere, ultimul lucru spus, ce a făcut recent (unelte, fișiere, mesaje), sub-agenții, branch-ul și comanda `claude --resume`.
- **🕸️ Legături.** O hartă cu cine cui a scris (`SendMessage`). Grosimea săgeții arată câte mesaje au fost, iar bulina care curge arată un mesaj din ultimele 15 minute. Treci cu mouse-ul peste o săgeată ca să vezi ultimele mesaje.
- **✈️ Mesaje.** Poți scrie unui agent direct din aplicație:
  - **sesiune pornită**: mesajul ajunge în ea prin unealta oficială `SendMessage`, printr-un releu scurt `claude -p` pe Haiku. Agentul îl vede ca mesaj de la un coleg, deci nu e echivalent cu o aprobare de-a ta;
  - **sesiune închisă**: o pornește în fundal cu mesajul tău (`claude --resume <id> --bg`).
- Se actualizează singur la 3 secunde. Citește sesiunile din Windows și din WSL.

## Cum funcționează

Aplicația doar **citește**. Nu modifică nimic din `~/.claude`:

| Ce arată | De unde vine |
|---|---|
| sesiuni, activitate, ultimele mesaje | transcrierile `~/.claude/projects/*/*.jsonl`, citite incremental |
| stare exactă pentru sesiunile pornite | `claude agents --json` |
| sub-agenți | `<sesiune>/subagents/*.meta.json` |
| legături | apelurile `SendMessage` din transcrieri. Adresele tehnice se traduc în nume din `~/.claude/sessions/*.json` și din mesajele primite. |

Pentru sesiunile din WSL, starea e estimată din cât de recent a scris sesiunea și din ultimul ei mesaj.

Serverul ascultă doar pe `127.0.0.1` și folosește numai biblioteca standard Python. Fereastra de desktop folosește [pywebview](https://pywebview.flowrl.com/) peste WebView2, care e deja inclus în Windows 10/11.

## Instalare

Ai nevoie de Windows, Python 3.10+ și Claude Code (`claude` în PATH).

```powershell
git clone https://github.com/andrei-petrache/agenti-hub.git
cd agenti-hub
pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File creeaza-scurtatura.ps1   # scurtătură pe Desktop
```

Apoi deschizi **Agenti Hub** de pe Desktop sau rulezi `porneste.bat`.

Dacă îl vrei în browser în loc de fereastră: `porneste-in-browser.bat` deschide http://127.0.0.1:4777. Portul se schimbă cu variabila `AGENTI_PORT`.

## Configurare

La prima pornire se creează `proiecte.json` din `proiecte.exemplu.json`. Fișierul e în `.gitignore`, pentru că e configurarea ta locală.

```json
{
  "numele_tau": "Andrei",
  "proiecte": [
    {
      "nume": "Aplicația mea",
      "emoji": "🚀",
      "culoare": "#f2a65a",
      "descriere": "backend, frontend, review",
      "titluri": ["backend", "frontend", "review"],
      "cai": ["aplicatia-mea"]
    }
  ],
  "alocari": {}
}
```

- `titluri`: numele sesiunilor (dat cu `/rename`) care țin de proiect.
- `cai`: bucăți din folderul de lucru al sesiunii.
- `alocari`: mutările manuale, salvate automat când alegi alt proiect din panoul unui agent.
- `numele_tau`: apare în mesajele trimise („de la …, prin Agenți Hub”).
- `cauta_wsl` / `radacini_extra`: unde mai caută transcrieri.

Ce nu se potrivește nicăieri ajunge în **Diverse**.

## Fișiere

| Fișier | Rol |
|---|---|
| `app.py` | fereastra de desktop (pywebview) |
| `server.py` | serverul local: citește sesiunile, calculează stările și legăturile, trimite mesaje |
| `index.html` | toată interfața (HTML/CSS/JS fără dependențe, mascote SVG) |
| `fa_iconita.py` | desenează iconița `agenti.ico` / `agenti.png` din cod, fără biblioteci |
| `proiecte.exemplu.json` | configurare de pornire |

## Limite

- Starea din WSL e estimată, nu exactă.
- Sesiunile din WSL nu pot primi mesaje din aplicație, pentru că acolo rulează alt `claude`.
- Un mesaj către o sesiune pornită costă puțin, pentru că pornește un releu scurt pe Haiku.
