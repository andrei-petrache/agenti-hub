"""Opens a Claude session in a visible terminal window.

Windows: Git Bash (mintty), then Windows Terminal, then cmd.
macOS: Terminal.app. Linux: x-terminal-emulator / gnome-terminal / konsole / xterm.
The command and the header with details go into a small script in relay/, so no quoted text has to
travel through the terminal's own command line.
"""
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE / "relay"


# ---------------------------------------------------------------- which terminal
def git_bash():
    """The Git for Windows folder (the one with usr/bin/mintty.exe), or None."""
    bases = [os.environ.get("ProgramFiles"), os.environ.get("ProgramW6432"), os.environ.get("ProgramFiles(x86)")]
    if os.environ.get("LOCALAPPDATA"):
        bases.append(str(Path(os.environ["LOCALAPPDATA"]) / "Programs"))
    candidates = [Path(b) / "Git" for b in bases if b]
    g = shutil.which("git")
    if g:
        candidates.append(Path(g).resolve().parent.parent)        # ...\Git\cmd\git.exe -> ...\Git
    for c in candidates:
        if (c / "usr" / "bin" / "mintty.exe").exists():
            return c
    return None


def available():
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


def pick(preferred):
    found = available()
    return preferred if preferred in found else found[0]


# ---------------------------------------------------------------- scripts
def _clean(s, n=120):
    return re.sub(r"\s+", " ", str(s or "")).strip()[:n]


def _script_path(sid, ext):
    SCRIPTS.mkdir(exist_ok=True)
    return SCRIPTS / f"open-{sid[:8]}.{ext}"


def _bash_script(sid, title, header, command, cwd, bye):
    """command = list of arguments, quoted for bash."""
    p = _script_path(sid, "sh")
    lines = ["#!/usr/bin/env bash",
             f"printf '\\033]0;%s\\007' {shlex.quote(title)}",
             f"cd {shlex.quote(cwd)} 2>/dev/null",
             "printf '\\n'"]
    for i, line in enumerate(header):
        colour = "1;33" if i == 0 else "0;37"
        lines.append(f"printf '\\033[{colour}m%s\\033[0m\\n' {shlex.quote(line)}")
    lines += ["printf '\\n'",
              " ".join(shlex.quote(x) for x in command),
              # Claude turns on mouse reporting; when it is killed (😴 sleep) it can't turn it off, and every
              # mouse move then lands at the bash prompt as text like "35;130;16M". Reset the terminal modes.
              "printf '\\033[?1000l\\033[?1002l\\033[?1003l\\033[?1005l\\033[?1006l\\033[?1015l"
              "\\033[?1004l\\033[?2004l\\033[?25h\\033[0m'; stty sane 2>/dev/null",
              f"printf '\\n\\033[0;37m%s\\033[0m\\n' {shlex.quote(bye)}",
              "exec bash -i"]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return p


def _cmd_script(sid, title, header, command, cwd, bye):
    p = _script_path(sid, "cmd")
    esc = lambda s: re.sub(r'([&|<>^%"])', "", s)       # echo cannot easily print these
    q = lambda a: a if re.fullmatch(r"[\w.:\\/-]+", a) else '"' + a.replace('"', "") + '"'
    lines = ["@echo off", "chcp 65001 >nul", f"title {esc(title)}", f'cd /d "{cwd}" 2>nul', "echo."]
    lines += [f"echo {esc(line)}" if line else "echo." for line in header]
    lines += ["echo.", " ".join(q(x) for x in command), "echo.", f"echo {esc(bye)}"]
    p.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------- opening
def open_window(sid, title, header, command, cwd, preferred="auto", bye=""):
    """Opens a new terminal window. Returns (True, terminal name) or (False, error)."""
    cwd = cwd if cwd and Path(cwd).is_dir() else str(Path.home())
    kind = pick(preferred)
    full_title = _clean(title, 60) + " · BuzzzHub"
    try:
        if kind == "gitbash":
            g = git_bash()
            s = _bash_script(sid, full_title, header, command, cwd, bye)
            env = dict(os.environ, MSYSTEM="MINGW64", CHERE_INVOKING="1")
            icon = g / "mingw64" / "share" / "git" / "git-for-windows.ico"
            cmd = [str(g / "usr" / "bin" / "mintty.exe"), "-t", full_title, "-s", "120,34"]
            if icon.exists():
                cmd += ["-i", str(icon)]
            cmd += ["--dir", cwd, "/usr/bin/bash", "-l", s.as_posix()]
            subprocess.Popen(cmd, cwd=cwd, env=env, close_fds=True)
            return True, "Git Bash"
        if kind == "wt":
            s = _cmd_script(sid, full_title, header, command, cwd, bye)
            subprocess.Popen(["wt", "-w", "new", "new-tab", "--title", full_title, "--suppressApplicationTitle",
                              "-d", cwd, "cmd", "/k", str(s)], cwd=cwd, close_fds=True)
            return True, "Windows Terminal"
        if kind == "cmd":
            s = _cmd_script(sid, full_title, header, command, cwd, bye)
            subprocess.Popen(["cmd", "/k", str(s)], cwd=cwd, close_fds=True,
                             creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
            return True, "cmd"
        s = _bash_script(sid, full_title, header, command, cwd, bye)
        s.chmod(0o755)
        if kind == "terminal":
            script = f'tell application "Terminal" to do script "bash {s.as_posix()}"'
            subprocess.Popen(["osascript", "-e", script, "-e", 'tell application "Terminal" to activate'])
            return True, "Terminal"
        for t in (["x-terminal-emulator", "-e"], ["gnome-terminal", "--"], ["konsole", "-e"], ["xterm", "-e"]):
            if shutil.which(t[0]):
                subprocess.Popen(t + ["bash", str(s)], cwd=cwd, close_fds=True)
                return True, t[0]
        return False, "no terminal found"
    except OSError as e:
        return False, f"{kind}: {e}"


# ---------------------------------------------------------------- an existing window
def bring_to_front(pid, name=None):
    """Tries to bring forward the terminal window running process pid (Windows only).
    First by the parent-process chain; if that is broken (Git Bash's launcher exits), by the window
    title: Claude puts the session name in it (e.g. "◑ backend")."""
    if os.name != "nt" or not (pid or name):
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
    parent = {}
    e = PE()
    e.dwSize = ctypes.sizeof(PE)
    ok = k32.Process32First(snap, ctypes.byref(e))
    while ok:
        parent[e.th32ProcessID] = e.th32ParentProcessID
        ok = k32.Process32Next(snap, ctypes.byref(e))
    k32.CloseHandle(snap)

    chain, p = [], int(pid or 0)
    while p and p not in chain and len(chain) < 12:
        chain.append(p)
        p = parent.get(p)

    windows, titles = {}, []
    CB = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)

    def cb(hwnd, _):
        n = u32.GetWindowTextLengthW(hwnd)
        if u32.IsWindowVisible(hwnd) and n > 0:
            wp = w.DWORD()
            u32.GetWindowThreadProcessId(hwnd, ctypes.byref(wp))
            if wp.value in chain and wp.value not in windows:
                windows[wp.value] = hwnd
            buf = ctypes.create_unicode_buffer(n + 1)
            u32.GetWindowTextW(hwnd, buf, n + 1)
            titles.append((hwnd, buf.value))
        return True

    u32.EnumWindows(CB(cb), 0)

    def show(h):
        if u32.IsIconic(h):
            u32.ShowWindow(h, 9)                    # SW_RESTORE
        u32.keybd_event(0x12, 0, 0, 0)              # Alt down: Windows then allows the focus change
        u32.SetForegroundWindow(h)
        u32.keybd_event(0x12, 0, 2, 0)
        return True

    for p in chain:                     # closest ancestor that owns a window
        if p in windows:
            return show(windows[p])
    if name:
        target = name.strip().lower()
        clean = lambda t: re.sub(r"^[^\w]+", "", t, flags=re.U).strip().lower()   # "◑ backend" -> "backend"
        exact = [h for h, t in titles if clean(t) == target]
        if len(exact) == 1:
            return show(exact[0])
    return False
