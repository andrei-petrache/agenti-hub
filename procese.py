"""Ce procese `claude` rulează acum pe PC și ce sesiune are fiecare (din linia de comandă).

E plasa de siguranță pentru sesiunile care nu apar în `claude agents` (de ex. pornite dintr-un
mediu „copil” al altei sesiuni). Doar citește lista de procese: fără tokeni, fără să pornească nimic.
"""
import os
import re
import subprocess
import time

_cache = {"t": 0.0, "val": []}
ARG = re.compile(r'(?:^|\s)(?:--resume|-r|--session-id)(?:=|\s+)(?:"([^"]+)"|(\S+))')


def claude_procese():
    """[(pid, linie_de_comandă)] pentru procesele claude interactive (fără -p, attach, gazde de fundal)."""
    if time.time() - _cache["t"] < 4:
        return _cache["val"]
    try:
        lst = _windows() if os.name == "nt" else _posix()
    except Exception:          # orice eroare de sistem: mai bine nimic decât un panou căzut
        lst = []
    out = []
    for pid, cmd in lst:
        c = f" {cmd} "
        if any(x in c for x in (" -p ", " --print ", " attach ", "--bg-pty-host", " agents ", " logs ",
                                " stop ", " mcp ", " --version ", " daemon ")):
            continue
        out.append((pid, cmd))
    _cache.update(t=time.time(), val=out)
    return out


def sesiuni():
    """{argument --resume/--session-id (id sau nume): pid}."""
    rez = {}
    for pid, cmd in claude_procese():
        m = ARG.search(cmd)
        if m:
            rez[(m.group(1) or m.group(2)).strip()] = pid
    return rez


# ---------------------------------------------------------------- Windows
def _windows():
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
        if e.szExeFile.lower() in (b"claude.exe", b"claude"):
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
            lungime = ctypes.cast(buf, ctypes.POINTER(ctypes.c_ushort))[0]
            ptr = ctypes.cast(ctypes.addressof(buf) + ctypes.sizeof(ctypes.c_void_p),
                              ctypes.POINTER(ctypes.c_void_p))[0]
            out.append((pid, ctypes.wstring_at(ptr, lungime // 2)))
        finally:
            k32.CloseHandle(h)
    return out


# ---------------------------------------------------------------- macOS / Linux
def _posix():
    r = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, timeout=5)
    out = []
    for ln in r.stdout.decode("utf-8", "replace").splitlines():
        ln = ln.strip()
        pid, _, cmd = ln.partition(" ")
        if pid.isdigit() and re.search(r"(^|/)claude(\s|$)|claude-code|@anthropic-ai", cmd):
            out.append((int(pid), cmd))
    return out
