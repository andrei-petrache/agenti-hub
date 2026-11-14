# Install guide

BuzzzHub is a small desktop app that shows every **Claude Code** session on your computer, grouped by project. It never sends your data anywhere: it reads the files Claude Code already keeps on your disk. The interface is in **English and Romanian** (switch with the EN / RO buttons at the top).

## You need

1. **Claude Code**, installed and used at least once. Typing `claude` in a terminal must start it. Setup: https://code.claude.com/docs/en/setup
2. **Python 3.10 or newer**: https://www.python.org/downloads/

## 🪟 Windows

1. **Install Python** from https://www.python.org/downloads/windows/. On the first installer screen **tick "Add python.exe to PATH"**, then click *Install Now*.
2. **Download BuzzzHub:** on the project page click the green **Code** button, then **Download ZIP**.
3. **Extract** the ZIP (right-click, *Extract All…*) wherever you like, for example in `Documents`.
4. Open the folder and **double-click `install.bat`**. It installs the only dependency (`pywebview`) and puts a **BuzzzHub** shortcut on your Desktop.
   - If Windows says "Windows protected your PC", click **More info**, then **Run anyway**. It happens because the file came from the internet.
5. Open **BuzzzHub** from the Desktop. Done! 🎉

> Have `git`? Clone the repo instead of steps 2–3:
> `git clone https://github.com/andrei-petrache/buzzzhub.git`

**WSL sessions:** if you also run Claude Code in WSL (Ubuntu), the app finds those sessions on its own.

**Opening agents in a terminal:** the 🖥️ button uses Git Bash if Git for Windows is installed, otherwise Windows Terminal, otherwise cmd. You can force one in `config.json` with `"terminal": "gitbash" | "wt" | "cmd"`.

## 🍎 macOS

1. **Install Python** from https://www.python.org/downloads/macos/ (Homebrew's `brew install python` works too).
2. **Download BuzzzHub:** the green **Code** button, then **Download ZIP**. Safari extracts it into *Downloads*.
3. Move the folder wherever you like, for example to *Documents*.
4. **Double-click `start.command`.**
   - The first time, macOS may say the file is from an "unidentified developer". **Right-click** the file, choose **Open**, then **Open** again. You only do this once.
   - The first launch takes about a minute: the script creates a private Python environment (`.venv`) and installs `pywebview`. After that it starts right away.
5. The **BuzzzHub** window opens. 🎉

If double-clicking does nothing, open **Terminal** in the app's folder and run:

```bash
bash start.command
```

**Want it in the Dock?** While it runs, right-click its Dock icon and choose *Options*, then *Keep in Dock*.

## First run

- Sessions that match no project show up under **Other**. To group them, open `config.json` in the app's folder (created on the first launch) and give each project the session names (`titles`), keywords (`keywords`) or a piece of the folder it works in (`paths`). The README has an example.
- You can also move a session by hand: click the agent, then pick the project in the side panel, under **project** (or **➕ new project…**).
- Top right: **EN / RO** for the language, three mascot families (🟠 blobs, 🤖 dev robots, 🦊 animals) and three themes (🍑 Cream, which follows the system light/dark setting, 🌙 Night and 🍵 Matcha).

## Common problems

| Problem | Fix |
|---|---|
| "Python not found" | Reinstall Python and tick *Add to PATH* (Windows). On a Mac, check that `python3 --version` works in Terminal. |
| No agents show up | Use Claude Code at least once: the app reads `~/.claude/projects`. Also check the period at the top right ("last 3 days"). |
| Status is not live / messages don't go out | The app needs the `claude` command on your PATH. Check that `claude --version` works in a terminal. |
| A session won't start in the background | Claude only starts background sessions in folders you trusted. Press 🖥️ Terminal instead: it opens the session interactively so you can trust the folder once. |
| The window is white (Windows) | Install the **Microsoft Edge WebView2 Runtime**: https://developer.microsoft.com/microsoft-edge/webview2/ (usually already on Windows 10/11). |
| I'd rather use a browser | Run `start-in-browser.bat` (Windows) or `python3 server.py` (Mac), then open http://127.0.0.1:4777 |

## Upgrading from an older version

Older versions kept their settings in `proiecte.json` and the message log in `mesaje.jsonl`. On the first start, BuzzzHub copies the settings into `config.json` (the old file stays as a backup) and renames the log to `messages.jsonl`. The Desktop shortcut keeps working.

## Uninstall

Delete the app's folder and the Desktop shortcut. Nothing else is installed, apart from the `pywebview` package on Windows, which you can remove with `python -m pip uninstall pywebview`.
