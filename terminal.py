"""Deschide o sesiune Claude într-o fereastră de terminal vizibilă.

Pe Windows: Git Bash (mintty), apoi Windows Terminal, apoi cmd.
Pe macOS: Terminal.app. Pe Linux: x-terminal-emulator / gnome-terminal / xterm.
Comanda rulată și antetul cu detalii stau într-un script mic din releu/,
așa nu trec texte cu ghilimele prin linia de comandă a terminalului.
"""
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

AICI = Path(__file__).resolve().parent
SCRIPTURI = AICI / "releu"


# ---------------------------------------------------------------- care terminal
def git_bash():
    """Folderul Git for Windows (cel care are usr/bin/mintty.exe), sau None."""
    baze = [os.environ.get("ProgramFiles"), os.environ.get("ProgramW6432"),
            os.environ.get("ProgramFiles(x86)")]
    if os.environ.get("LOCALAPPDATA"):
        baze.append(str(Path(os.environ["LOCALAPPDATA"]) / "Programs"))
    cand = [Path(b) / "Git" for b in baze if b]
    g = shutil.which("git")
    if g:
        cand.append(Path(g).resolve().parent.parent)        # ...\Git\cmd\git.exe -> ...\Git
    for c in cand:
        if (c / "usr" / "bin" / "mintty.exe").exists():
            return c
    return None


def disponibile():
    if sys.platform == "darwin":
        return ["terminal"]
    if os.name != "nt":
        return ["linux"]
    out = []
    if git_bash():
        out.append("gitbash")
    if shutil.which("wt"):
        out.append("wt")
    out.append("cmd")
    return out


def alege(preferat):
    disp = disponibile()
    return preferat if preferat in disp else disp[0]


# ---------------------------------------------------------------- scripturi
def _curat(s, n=120):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s[:n]


def _nume_fisier(sid, ext):
    SCRIPTURI.mkdir(exist_ok=True)
    return SCRIPTURI / f"deschide-{sid[:8]}.{ext}"


def _script_bash(sid, titlu, antet, comanda, cwd):
    """comanda = listă de argumente; e citată pentru bash."""
    p = _nume_fisier(sid, "sh")
    linii = ["#!/usr/bin/env bash",
             f"printf '\\033]0;%s\\007' {shlex.quote(titlu)}",
             f"cd {shlex.quote(cwd)} 2>/dev/null"]
    linii.append("printf '\\n'")
    for i, l in enumerate(antet):
        cul = "1;33" if i == 0 else "0;37"
        linii.append(f"printf '\\033[{cul}m%s\\033[0m\\n' {shlex.quote(l)}")
    linii.append("printf '\\n'")
    linii.append(" ".join(shlex.quote(x) for x in comanda))
    linii += ["printf '\\n\\033[0;37m%s\\033[0m\\n' "
              + shlex.quote("Ai ieșit din sesiune. Poți închide fereastra."),
              "exec bash -i"]
    p.write_text("\n".join(linii) + "\n", encoding="utf-8", newline="\n")
    return p


def _script_cmd(sid, titlu, antet, comanda, cwd):
    p = _nume_fisier(sid, "cmd")
    esc = lambda s: re.sub(r'([&|<>^%"])', "", s)       # echo nu suportă ușor caracterele astea
    q = lambda a: a if re.fullmatch(r"[\w.:\\/-]+", a) else '"' + a.replace('"', "") + '"'
    linii = ["@echo off", "chcp 65001 >nul", f"title {esc(titlu)}", f'cd /d "{cwd}" 2>nul', "echo."]
    linii += [f"echo {esc(l)}" if l else "echo." for l in antet]
    linii += ["echo.", " ".join(q(x) for x in comanda), "echo.", "echo Ai iesit din sesiune. Poti inchide fereastra."]
    p.write_text("\r\n".join(linii) + "\r\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------- pornire
def deschide(sid, titlu, antet, comanda, cwd, preferat="auto"):
    """Deschide o fereastră nouă de terminal. Întoarce (ok, ce terminal / eroare)."""
    cwd = cwd if cwd and Path(cwd).is_dir() else str(Path.home())
    fel = alege(preferat)
    titlu_f = _curat(titlu, 60) + " · BuzzzHub"
    try:
        if fel == "gitbash":
            g = git_bash()
            s = _script_bash(sid, titlu_f, antet, comanda, cwd)
            env = dict(os.environ, MSYSTEM="MINGW64", CHERE_INVOKING="1")
            ico = g / "mingw64" / "share" / "git" / "git-for-windows.ico"
            cmd = [str(g / "usr" / "bin" / "mintty.exe"), "-t", titlu_f, "-s", "120,34"]
            if ico.exists():
                cmd += ["-i", str(ico)]
            cmd += ["--dir", cwd, "/usr/bin/bash", "-l", s.as_posix()]
            subprocess.Popen(cmd, cwd=cwd, env=env, close_fds=True)
            return True, "Git Bash"
        if fel == "wt":
            s = _script_cmd(sid, titlu_f, antet, comanda, cwd)
            subprocess.Popen(["wt", "-w", "new", "new-tab", "--title", titlu_f, "--suppressApplicationTitle",
                              "-d", cwd, "cmd", "/k", str(s)], cwd=cwd, close_fds=True)
            return True, "Windows Terminal"
        if fel == "cmd":
            s = _script_cmd(sid, titlu_f, antet, comanda, cwd)
            subprocess.Popen(["cmd", "/k", str(s)], cwd=cwd, close_fds=True,
                             creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
            return True, "cmd"
        s = _script_bash(sid, titlu_f, antet, comanda, cwd)
        s.chmod(0o755)
        if fel == "terminal":
            as_ = f'tell application "Terminal" to do script "bash {s.as_posix()}"'
            subprocess.Popen(["osascript", "-e", as_, "-e", 'tell application "Terminal" to activate'])
            return True, "Terminal"
        for t in (["x-terminal-emulator", "-e"], ["gnome-terminal", "--"], ["konsole", "-e"], ["xterm", "-e"]):
            if shutil.which(t[0]):
                subprocess.Popen(t + ["bash", str(s)], cwd=cwd, close_fds=True)
                return True, t[0]
        return False, "Nu găsesc niciun terminal pe sistem."
    except OSError as e:
        return False, f"Nu am putut deschide terminalul ({fel}): {e}"


# ---------------------------------------------------------------- fereastră existentă
def aduce_in_fata(pid, nume=None):
    """Încearcă să aducă în față fereastra terminalului în care rulează procesul pid (doar Windows).
    Întâi după lanțul de procese părinte; dacă e rupt (Git Bash își închide lansatorul),
    după titlul ferestrei: Claude pune în titlu numele sesiunii (ex. „◑ backend”)."""
    if os.name != "nt" or not (pid or nume):
        return False
    import ctypes
    from ctypes import wintypes as w

    k32, u32 = ctypes.windll.kernel32, ctypes.windll.user32

    class PE(ctypes.Structure):
        _fields_ = [("dwSize", w.DWORD), ("cntUsage", w.DWORD), ("th32ProcessID", w.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", w.DWORD),
                    ("cntThreads", w.DWORD), ("th32ParentProcessID", w.DWORD),
                    ("pcPriClassBase", ctypes.c_long), ("dwFlags", w.DWORD), ("szExeFile", ctypes.c_char * 260)]

    k32.CreateToolhelp32Snapshot.restype = w.HANDLE
    snap = k32.CreateToolhelp32Snapshot(2, 0)
    parinte = {}
    e = PE()
    e.dwSize = ctypes.sizeof(PE)
    ok = k32.Process32First(snap, ctypes.byref(e))
    while ok:
        parinte[e.th32ProcessID] = e.th32ParentProcessID
        ok = k32.Process32Next(snap, ctypes.byref(e))
    k32.CloseHandle(snap)

    lant, p = [], int(pid or 0)
    while p and p not in lant and len(lant) < 12:
        lant.append(p)
        p = parinte.get(p)

    ferestre, titluri = {}, []
    CB = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)

    def cb(hwnd, _):
        n = u32.GetWindowTextLengthW(hwnd)
        if u32.IsWindowVisible(hwnd) and n > 0:
            wp = w.DWORD()
            u32.GetWindowThreadProcessId(hwnd, ctypes.byref(wp))
            if wp.value in lant and wp.value not in ferestre:
                ferestre[wp.value] = hwnd
            buf = ctypes.create_unicode_buffer(n + 1)
            u32.GetWindowTextW(hwnd, buf, n + 1)
            titluri.append((hwnd, buf.value))
        return True

    u32.EnumWindows(CB(cb), 0)

    def arata(h):
        if u32.IsIconic(h):
            u32.ShowWindow(h, 9)                    # SW_RESTORE
        u32.keybd_event(0x12, 0, 0, 0)              # Alt apăsat: Windows permite schimbarea focusului
        u32.SetForegroundWindow(h)
        u32.keybd_event(0x12, 0, 2, 0)
        return True

    for p in lant:                      # cel mai apropiat strămoș cu fereastră
        if p in ferestre:
            return arata(ferestre[p])
    if nume:
        tinta = nume.strip().lower()
        curat = lambda t: re.sub(r"^[^\w]+", "", t, flags=re.U).strip().lower()   # „◑ backend” -> „backend”
        exacte = [h for h, t in titluri if curat(t) == tinta]
        if len(exacte) == 1:
            return arata(exacte[0])
    return False
