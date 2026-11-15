"""Which `claude` processes are running right now and which session each one has (from its command line).

A safety net for sessions missing from `claude agents` (for example ones started from an environment
that inherited another session's variables). It only reads the process list: no tokens, starts nothing.
"""
import os
import re
import subprocess
import time

_cache = {"t": 0.0, "val": []}
ARG = re.compile(r'(?:^|\s)(?:--resume|-r|--session-id)(?:=|\s+)(?:"([^"]+)"|(\S+))')
SKIP = (" -p ", " --print ", " attach ", "--bg-pty-host", " agents ", " logs ", " stop ", " mcp ",
        " --version ", " daemon ")


def claude_processes():
    """[(pid, command line)] for interactive claude processes (no -p, attach, background hosts, daemon)."""
    if time.time() - _cache["t"] < 4:
        return _cache["val"]
    try:
        found = _windows() if os.name == "nt" else _posix()
    except Exception:          # any OS error: better nothing than a broken dashboard
        found = []
    out = [(pid, cmd) for pid, cmd in found if not any(x in f" {cmd} " for x in SKIP)]
    _cache.update(t=time.time(), val=out)
    return out


def sessions():
    """{--resume / --session-id argument (id or name): pid}."""
    out = {}
    for pid, cmd in claude_processes():
        m = ARG.search(cmd)
        if m:
            out[(m.group(1) or m.group(2)).strip()] = pid
    return out


# ---------------------------------------------------------------- Windows
def windows_of(script):
    """Windows only: pids of terminal windows (mintty) that BuzzzHub opened with this launcher script."""
    if os.name != "nt":
        return []
    try:
        return [pid for pid, cmd in _windows((b"mintty.exe",)) if script in cmd]
    except Exception:
        return []


def _windows(exes=(b"claude.exe", b"claude")):
    import ctypes
    from ctypes import wintypes as w

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    nt = ctypes.WinDLL("ntdll")

    class PE(ctypes.Structure):
        _fields_ = [("dwSize", w.DWORD), ("cntUsage", w.DWORD), ("th32ProcessID", w.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", w.DWORD),
                    ("cntThreads", w.DWORD), ("th32ParentProcessID", w.DWORD),
                    ("pcPriClassBase", ctypes.c_long), ("dwFlags", w.DWORD), ("szExeFile", ctypes.c_char * 260)]

    k32.CreateToolhelp32Snapshot.restype = w.HANDLE
    k32.OpenProcess.restype = w.HANDLE
    k32.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    k32.CloseHandle.argtypes = [w.HANDLE]
    k32.Process32First.argtypes = k32.Process32Next.argtypes = [w.HANDLE, ctypes.c_void_p]
    nt.NtQueryInformationProcess.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.ULONG,
                                             ctypes.POINTER(w.ULONG)]

    snap = k32.CreateToolhelp32Snapshot(2, 0)
    pids = []
    e = PE()
    e.dwSize = ctypes.sizeof(PE)
    ok = k32.Process32First(snap, ctypes.byref(e))
    while ok:
        if e.szExeFile.lower() in exes:
            pids.append(e.th32ProcessID)
        ok = k32.Process32Next(snap, ctypes.byref(e))
    k32.CloseHandle(snap)

    out = []
    for pid in pids:
        h = k32.OpenProcess(0x1000, False, pid)          # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            continue
        try:
            n = w.ULONG(0)
            nt.NtQueryInformationProcess(h, 60, None, 0, ctypes.byref(n))   # ProcessCommandLineInformation
            if not n.value:
                continue
            buf = ctypes.create_string_buffer(n.value)
            if nt.NtQueryInformationProcess(h, 60, buf, n.value, ctypes.byref(n)) != 0:
                continue
            length = ctypes.cast(buf, ctypes.POINTER(ctypes.c_ushort))[0]     # UNICODE_STRING.Length
            ptr = ctypes.cast(ctypes.addressof(buf) + ctypes.sizeof(ctypes.c_void_p),
                              ctypes.POINTER(ctypes.c_void_p))[0]             # UNICODE_STRING.Buffer
            out.append((pid, ctypes.wstring_at(ptr, length // 2)))
        finally:
            k32.CloseHandle(h)
    return out


# ---------------------------------------------------------------- macOS / Linux
def _posix():
    r = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, timeout=5)
    out = []
    for ln in r.stdout.decode("utf-8", "replace").splitlines():
        pid, _, cmd = ln.strip().partition(" ")
        if pid.isdigit() and re.search(r"(^|/)claude(\s|$)|claude-code|@anthropic-ai", cmd):
            out.append((int(pid), cmd))
    return out
