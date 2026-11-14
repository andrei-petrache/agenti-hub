# Ghid de instalare · Install guide

🇷🇴 [Română](#română) · 🇬🇧 [English](#english)

---

## Română

BuzzzHub e o aplicație mică de desktop care îți arată toate sesiunile **Claude Code** de pe calculator, grupate pe proiecte. Nu trimite nimic pe internet. Citește doar fișierele pe care Claude Code le ține deja pe disc.

### Ce îți trebuie

1. **Claude Code**, instalat și folosit cel puțin o dată. Dacă scrii `claude` în terminal, trebuie să pornească. Instalare: https://code.claude.com/docs/en/setup
2. **Python 3.10 sau mai nou**: https://www.python.org/downloads/

### 🪟 Windows

1. **Instalează Python** de pe https://www.python.org/downloads/windows/. La primul ecran al instalatorului **bifează „Add python.exe to PATH”**, apoi apasă *Install Now*.
2. **Descarcă BuzzzHub:** pe pagina proiectului apasă butonul verde **Code**, apoi **Download ZIP**.
3. **Dezarhivează** ZIP-ul: click dreapta, apoi *Extract All…*. Pune folderul unde vrei, de exemplu în `Documente`.
4. Deschide folderul și dă **dublu-click pe `instaleaza.bat`**. Scriptul instalează singura dependență (`pywebview`) și pune pe Desktop o scurtătură **BuzzzHub**.
   - Dacă Windows zice „Windows protected your PC”, apasă **More info**, apoi **Run anyway**. Se întâmplă pentru că fișierul vine de pe internet.
5. Deschide **BuzzzHub** de pe Desktop. Gata! 🎉

> Ai `git`? Atunci poți clona repo-ul în loc de pașii 2–3:
> `git clone https://github.com/andrei-petrache/buzzzhub.git`

**Sesiuni din WSL:** dacă rulezi Claude Code și în WSL (Ubuntu), aplicația le găsește singură.

### 🍎 macOS

1. **Instalează Python** de pe https://www.python.org/downloads/macos/. Merge și cel din Homebrew (`brew install python`).
2. **Descarcă BuzzzHub:** butonul verde **Code**, apoi **Download ZIP**. Safari îl dezarhivează singur în *Descărcări* (Downloads).
3. Mută folderul unde vrei, de exemplu în *Documente*.
4. **Dublu-click pe `porneste.command`.**
   - Prima dată macOS poate spune că fișierul e de la un „dezvoltator neidentificat”. Fă **click dreapta** pe fișier, alege **Open**, apoi încă o dată **Open**. Trebuie făcut o singură dată.
   - La prima pornire durează cam un minut: scriptul își face un mediu Python separat (`.venv`) și instalează `pywebview`. Data viitoare pornește imediat.
5. Se deschide fereastra **BuzzzHub**. 🎉

Dacă dublu-click-ul nu merge, deschide **Terminal** în folderul aplicației și scrie:

```bash
bash porneste.command
```

**Vrei aplicația în Dock?** Cât timp rulează, fă click dreapta pe iconița ei din Dock și alege *Options*, apoi *Keep in Dock*.

### Prima pornire

- Toate sesiunile tale apar în **Diverse**. Ca să le grupezi pe proiecte, deschide `proiecte.json` din folderul aplicației (se creează la prima pornire) și trece la fiecare proiect numele sesiunilor (`titluri`) sau o bucată din folderul în care lucrează (`cai`). Exemple sunt în README.
- Poți muta și manual o sesiune: click pe agent, apoi alegi proiectul din panou, la **proiect**.
- Sus în dreapta ai **trei teme**: 🍑 Cremă (urmează tema deschisă sau închisă a sistemului), 🌙 Noapte și 🍵 Matcha.

### Probleme frecvente

| Problemă | Soluție |
|---|---|
| „Nu găsesc Python” | Reinstalează Python și bifează *Add to PATH* (Windows). Pe Mac verifică în Terminal că `python3 --version` merge. |
| Nu apare niciun agent | Folosește Claude Code cel puțin o dată. Aplicația citește din `~/.claude/projects`. Verifică și perioada din dreapta sus („ultimele 3 zile”). |
| Stările nu sunt „live” / mesajele nu pleacă | Aplicația are nevoie de comanda `claude` în PATH. Verifică în terminal că `claude --version` merge. |
| Fereastra e albă (Windows) | Instalează **Microsoft Edge WebView2 Runtime**: https://developer.microsoft.com/microsoft-edge/webview2/ (pe Windows 10/11 e de obicei deja instalat). |
| Vreau să-l văd în browser | Pornește `porneste-in-browser.bat` (Windows) sau `python3 server.py` (Mac), apoi deschide http://127.0.0.1:4777 |

### Dezinstalare

Șterge folderul aplicației și scurtătura de pe Desktop. Aplicația nu instalează nimic altundeva, în afară de pachetul `pywebview` pe Windows. Pe acela îl scoți cu `python -m pip uninstall pywebview`.

---

## English

BuzzzHub is a small desktop app that shows all your **Claude Code** sessions, grouped by project. It never sends anything to the internet. It only reads the files Claude Code already keeps on your disk. (The interface is in Romanian.)

### You need

1. **Claude Code**, installed and used at least once (`claude` works in a terminal): https://code.claude.com/docs/en/setup
2. **Python 3.10+**: https://www.python.org/downloads/

### 🪟 Windows

1. Install Python from https://www.python.org/downloads/windows/ and **tick "Add python.exe to PATH"**.
2. On the project page click the green **Code** button, then **Download ZIP**, and extract it.
3. Double-click **`instaleaza.bat`**. It installs `pywebview` and creates an **BuzzzHub** shortcut on your Desktop. If SmartScreen warns you, click **More info**, then **Run anyway**.
4. Open **BuzzzHub** from the Desktop.

### 🍎 macOS

1. Install Python from https://www.python.org/downloads/macos/ (or `brew install python`).
2. Click **Code**, then **Download ZIP**, and move the folder wherever you like.
3. Double-click **`porneste.command`**. The first time, macOS may block it: right-click the file, choose **Open**, then **Open** again. The first launch takes about a minute while it creates a private `.venv` and installs `pywebview`.
4. If double-click does nothing, run `bash porneste.command` in Terminal from that folder.

### First run

- Sessions show up under **Diverse** ("misc"). Group them by editing `proiecte.json` (created on first launch): put session names in `titluri` and folder fragments in `cai`. You can also move a session from its side panel.
- Three themes are in the top-right corner: 🍑 Cream (follows system light/dark), 🌙 Night and 🍵 Matcha.
- Live status and sending messages require the `claude` command on your PATH.
