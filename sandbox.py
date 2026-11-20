"""Limits for running untrusted student programs: time, output size, memory and processes."""
from __future__ import annotations

import os
import subprocess
import threading

MAX_PROGRAM_OUTPUT = 64_000
PROGRAM_MEMORY_LIMIT = 512 * 1024 * 1024

def normalize_output(text) -> str:
    """Compare program output without being fooled by CRLF or trailing spaces."""
    text = str(text if text is not None else "").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.strip().split("\n"))


def _posix_limits():
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (PROGRAM_MEMORY_LIMIT, PROGRAM_MEMORY_LIMIT))
        resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
        resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_PROGRAM_OUTPUT * 8, MAX_PROGRAM_OUTPUT * 8))
    except Exception:
        pass


def _assign_windows_job(proc):
    """Windows: cap memory and forbid child processes with a Job Object (best effort)."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in ("r_ops", "w_ops", "o_ops", "r_bytes", "w_bytes", "o_bytes")]

        class BASIC(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong), ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD), ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]

        class EXTENDED(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", BASIC), ("IoInfo", IO_COUNTERS), ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

        kernel = ctypes.windll.kernel32
        kernel.CreateJobObjectW.restype = wintypes.HANDLE
        kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        job = kernel.CreateJobObjectW(None, None)
        if not job:
            return None
        info = EXTENDED()
        info.BasicLimitInformation.LimitFlags = 0x100 | 0x8 | 0x2000  # process memory, active process, kill on close
        info.BasicLimitInformation.ActiveProcessLimit = 1
        info.ProcessMemoryLimit = PROGRAM_MEMORY_LIMIT
        kernel.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))
        kernel.AssignProcessToJobObject(job, wintypes.HANDLE(int(proc._handle)))
        return job
    except Exception:
        return None


def run_limited(command, input_text, timeout, cwd, creationflags=0, cap=MAX_PROGRAM_OUTPUT):
    """Run a student program with a time limit, an output cap and memory limits.

    Returns (result, timed_out, overflowed); result has returncode/stdout/stderr.
    """
    from types import SimpleNamespace
    kwargs = {"preexec_fn": _posix_limits} if os.name == "posix" else {"creationflags": creationflags}
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, **kwargs)
    job = _assign_windows_job(proc)
    buffers = {"out": bytearray(), "err": bytearray()}
    overflow = threading.Event()

    def pump(stream, key):
        try:
            while True:
                chunk = stream.read1(8192)
                if not chunk:
                    break
                room = cap - len(buffers[key])
                if room > 0:
                    buffers[key].extend(chunk[:room])
                if len(chunk) > room:
                    overflow.set()
                    proc.kill()
                    break
        except Exception:
            pass

    workers = [threading.Thread(target=pump, args=(proc.stdout, "out"), daemon=True), threading.Thread(target=pump, args=(proc.stderr, "err"), daemon=True)]
    for worker in workers:
        worker.start()
    try:
        proc.stdin.write(input_text.encode("utf-8", errors="replace"))
        proc.stdin.close()
    except Exception:
        pass
    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        proc.wait()
    for worker in workers:
        worker.join(timeout=1)
    for stream in (proc.stdout, proc.stderr):
        try:
            stream.close()
        except Exception:
            pass
    if job:
        try:
            __import__("ctypes").windll.kernel32.CloseHandle(job)
        except Exception:
            pass
    decode = lambda data: data.decode("utf-8", errors="replace").replace("\r\n", "\n")
    result = SimpleNamespace(returncode=proc.returncode, stdout=decode(buffers["out"]), stderr=decode(buffers["err"]))
    return result, timed_out, overflow.is_set()
