"""Windows isolation for learner programs and compiler tools (Job Objects + AppContainer).

Learner programs (``run_isolated``):
  1. Created *suspended*; a Job Object is attached before the first instruction runs:
     one process only (no children), memory cap, CPU-time cap, UI restrictions
     (no clipboard, no desktop switching, no ExitWindows), no crash dialogs, and the
     whole tree is killed when the job handle closes. If the job cannot be attached the
     process is terminated and never resumed (fail closed).
  2. When the OS allows it, the process also runs inside an AppContainer with *no*
     capabilities: no network (including loopback to the local API), no access to the
     user's files, low integrity. It can only read system DLLs and its own run folder.
     If AppContainer setup fails (very old Windows, policy), the run falls back to the
     Job Object alone and reports ``isolation == "job"``.
  3. A minimal environment block is passed (no API keys or user variables), and the
     program starts in a fresh, empty working folder that is removed afterwards.

Compiler/build tools (``run_tool``): created suspended inside a Job Object with
per-process and per-job memory caps and a process-count cap; on timeout the whole
process tree is terminated through the job.
"""
from __future__ import annotations

import ctypes
import msvcrt
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from ctypes import wintypes
from pathlib import Path
from types import SimpleNamespace

if os.name != "nt":  # pragma: no cover - imported only on Windows
    raise ImportError("sandbox_windows is Windows-only")

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
userenv = ctypes.WinDLL("userenv", use_last_error=True)
ole32 = ctypes.WinDLL("ole32")
ntdll = ctypes.WinDLL("ntdll")

HANDLE = wintypes.HANDLE
DWORD = wintypes.DWORD
BOOL = wintypes.BOOL

CREATE_SUSPENDED = 0x00000004
CREATE_UNICODE_ENVIRONMENT = 0x00000400
EXTENDED_STARTUPINFO_PRESENT = 0x00080000
CREATE_NO_WINDOW = 0x08000000
STARTF_USESTDHANDLES = 0x00000100
HANDLE_FLAG_INHERIT = 0x00000001
PROC_THREAD_ATTRIBUTE_HANDLE_LIST = 0x00020002
PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES = 0x00020009
WAIT_TIMEOUT = 0x00000102

JobObjectBasicUIRestrictions = 4
JobObjectExtendedLimitInformation = 9
JOB_OBJECT_LIMIT_PROCESS_TIME = 0x00000002
JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION = 0x00000400
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_UILIMIT_ALL = 0x000000FF  # handles, clipboard r/w, system params, display, atoms, desktop, ExitWindows

APPCONTAINER_NAME = "CppAdventure.Sandbox"
HRESULT_ALREADY_EXISTS = 0x800700B7


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("nLength", DWORD), ("lpSecurityDescriptor", ctypes.c_void_p), ("bInheritHandle", BOOL)]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount", "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong), ("LimitFlags", DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", DWORD), ("SchedulingClass", DWORD)]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION), ("IoInfo", IO_COUNTERS), ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]


class JOBOBJECT_BASIC_UI_RESTRICTIONS(ctypes.Structure):
    _fields_ = [("UIRestrictionsClass", DWORD)]


class SECURITY_CAPABILITIES(ctypes.Structure):
    _fields_ = [("AppContainerSid", ctypes.c_void_p), ("Capabilities", ctypes.c_void_p), ("CapabilityCount", DWORD), ("Reserved", DWORD)]


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [("cb", DWORD), ("lpReserved", wintypes.LPWSTR), ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR),
                ("dwX", DWORD), ("dwY", DWORD), ("dwXSize", DWORD), ("dwYSize", DWORD), ("dwXCountChars", DWORD), ("dwYCountChars", DWORD),
                ("dwFillAttribute", DWORD), ("dwFlags", DWORD), ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", HANDLE), ("hStdOutput", HANDLE), ("hStdError", HANDLE)]


class STARTUPINFOEXW(ctypes.Structure):
    _fields_ = [("StartupInfo", STARTUPINFOW), ("lpAttributeList", ctypes.c_void_p)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", HANDLE), ("hThread", HANDLE), ("dwProcessId", DWORD), ("dwThreadId", DWORD)]


def _proto(lib, name, restype, *argtypes):
    func = getattr(lib, name)
    func.restype, func.argtypes = restype, list(argtypes)
    return func


CreateJobObjectW = _proto(kernel32, "CreateJobObjectW", HANDLE, ctypes.c_void_p, wintypes.LPCWSTR)
SetInformationJobObject = _proto(kernel32, "SetInformationJobObject", BOOL, HANDLE, ctypes.c_int, ctypes.c_void_p, DWORD)
AssignProcessToJobObject = _proto(kernel32, "AssignProcessToJobObject", BOOL, HANDLE, HANDLE)
TerminateJobObject = _proto(kernel32, "TerminateJobObject", BOOL, HANDLE, wintypes.UINT)
CloseHandle = _proto(kernel32, "CloseHandle", BOOL, HANDLE)
CreatePipe = _proto(kernel32, "CreatePipe", BOOL, ctypes.POINTER(HANDLE), ctypes.POINTER(HANDLE), ctypes.POINTER(SECURITY_ATTRIBUTES), DWORD)
SetHandleInformation = _proto(kernel32, "SetHandleInformation", BOOL, HANDLE, DWORD, DWORD)
InitializeProcThreadAttributeList = _proto(kernel32, "InitializeProcThreadAttributeList", BOOL, ctypes.c_void_p, DWORD, DWORD, ctypes.POINTER(ctypes.c_size_t))
UpdateProcThreadAttribute = _proto(kernel32, "UpdateProcThreadAttribute", BOOL, ctypes.c_void_p, DWORD, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p)
DeleteProcThreadAttributeList = _proto(kernel32, "DeleteProcThreadAttributeList", None, ctypes.c_void_p)
CreateProcessW = _proto(kernel32, "CreateProcessW", BOOL, wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p, BOOL, DWORD,
                        ctypes.c_void_p, wintypes.LPCWSTR, ctypes.c_void_p, ctypes.POINTER(PROCESS_INFORMATION))
ResumeThread = _proto(kernel32, "ResumeThread", DWORD, HANDLE)
WaitForSingleObject = _proto(kernel32, "WaitForSingleObject", DWORD, HANDLE, DWORD)
GetExitCodeProcess = _proto(kernel32, "GetExitCodeProcess", BOOL, HANDLE, ctypes.POINTER(DWORD))
TerminateProcess = _proto(kernel32, "TerminateProcess", BOOL, HANDLE, wintypes.UINT)
LocalFree = _proto(kernel32, "LocalFree", ctypes.c_void_p, ctypes.c_void_p)
NtResumeProcess = _proto(ntdll, "NtResumeProcess", ctypes.c_long, HANDLE)
CreateAppContainerProfile = _proto(userenv, "CreateAppContainerProfile", ctypes.c_long, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                   ctypes.c_void_p, DWORD, ctypes.POINTER(ctypes.c_void_p))
DeriveAppContainerSidFromAppContainerName = _proto(userenv, "DeriveAppContainerSidFromAppContainerName", ctypes.c_long, wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p))
GetAppContainerFolderPath = _proto(userenv, "GetAppContainerFolderPath", ctypes.c_long, wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p))
ConvertSidToStringSidW = _proto(advapi32, "ConvertSidToStringSidW", BOOL, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))
CoTaskMemFree = _proto(ole32, "CoTaskMemFree", None, ctypes.c_void_p)


def _win_error(what: str) -> OSError:
    code = ctypes.get_last_error()
    return OSError(code, f"{what} failed: {ctypes.FormatError(code).strip()} ({code})")


def create_job(*, process_memory: int, active_processes: int, job_memory: int | None = None, cpu_seconds: float | None = None) -> int:
    """Create a configured Job Object and return its handle (caller closes it)."""
    job = CreateJobObjectW(None, None)
    if not job:
        raise _win_error("CreateJobObject")
    info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    flags = (JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_OBJECT_LIMIT_ACTIVE_PROCESS
             | JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)
    info.ProcessMemoryLimit = process_memory
    info.BasicLimitInformation.ActiveProcessLimit = active_processes
    if job_memory:
        flags |= JOB_OBJECT_LIMIT_JOB_MEMORY
        info.JobMemoryLimit = job_memory
    if cpu_seconds:
        flags |= JOB_OBJECT_LIMIT_PROCESS_TIME
        info.BasicLimitInformation.PerProcessUserTimeLimit = int(cpu_seconds * 10_000_000)  # 100 ns units
    info.BasicLimitInformation.LimitFlags = flags
    ui = JOBOBJECT_BASIC_UI_RESTRICTIONS(JOB_OBJECT_UILIMIT_ALL)
    if not SetInformationJobObject(job, JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info)) \
            or not SetInformationJobObject(job, JobObjectBasicUIRestrictions, ctypes.byref(ui), ctypes.sizeof(ui)):
        error = _win_error("SetInformationJobObject")
        CloseHandle(job)
        raise error
    return job


# ---------------------------------------------------------------- compiler / build tools

def run_tool(command, *, timeout: float, cwd, input_bytes: bytes | None = None, process_memory: int, job_memory: int,
             active_processes: int = 32, env=None) -> SimpleNamespace:
    """Run a trusted tool (g++, cmake, clang) inside a memory-capped Job Object."""
    job = create_job(process_memory=process_memory, job_memory=job_memory, active_processes=active_processes)
    try:
        proc = subprocess.Popen(command, stdin=subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=env,
                                creationflags=CREATE_SUSPENDED | CREATE_NO_WINDOW)
        if not AssignProcessToJobObject(job, int(proc._handle)):
            error = _win_error("AssignProcessToJobObject")
            proc.kill()
            proc.communicate()
            raise error
        if NtResumeProcess(int(proc._handle)) != 0:
            proc.kill()
            proc.communicate()
            raise OSError("NtResumeProcess failed")
        timed_out = False
        try:
            stdout, stderr = proc.communicate(input=input_bytes, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            TerminateJobObject(job, 1)  # kills cc1plus/as/ld/make children too
            stdout, stderr = proc.communicate()
        return SimpleNamespace(returncode=proc.returncode, stdout=stdout or b"", stderr=stderr or b"", timed_out=timed_out)
    finally:
        CloseHandle(job)


# ---------------------------------------------------------------- AppContainer profile

_AC_LOCK = threading.Lock()
_AC_STATE: dict = {"ready": False, "container": None, "error": None}


def appcontainer():
    """Create (once) or open the sandbox AppContainer profile. Returns None if unavailable."""
    with _AC_LOCK:
        if _AC_STATE["ready"]:
            return _AC_STATE["container"]
        _AC_STATE["ready"] = True
        try:
            sid = ctypes.c_void_p()
            hr = CreateAppContainerProfile(APPCONTAINER_NAME, "C++ Adventure Sandbox",
                                           "Runs learner C++ programs without network or file access.", None, 0, ctypes.byref(sid))
            if (hr & 0xFFFFFFFF) == HRESULT_ALREADY_EXISTS:
                hr = DeriveAppContainerSidFromAppContainerName(APPCONTAINER_NAME, ctypes.byref(sid))
            if hr != 0 or not sid.value:
                raise OSError(f"AppContainer profile unavailable (HRESULT 0x{hr & 0xFFFFFFFF:08X})")
            text_ptr = ctypes.c_void_p()
            if not ConvertSidToStringSidW(sid, ctypes.byref(text_ptr)):
                raise _win_error("ConvertSidToStringSid")
            sid_string = ctypes.wstring_at(text_ptr.value)
            LocalFree(text_ptr)
            path_ptr = ctypes.c_void_p()
            hr = GetAppContainerFolderPath(sid_string, ctypes.byref(path_ptr))
            if hr != 0 or not path_ptr.value:
                raise OSError(f"AppContainer folder unavailable (HRESULT 0x{hr & 0xFFFFFFFF:08X})")
            folder = Path(ctypes.wstring_at(path_ptr.value))
            CoTaskMemFree(path_ptr)
            runs = folder / "runs"
            runs.mkdir(parents=True, exist_ok=True)
            _sweep_stale_runs(runs)
            _AC_STATE["container"] = SimpleNamespace(sid=sid, sid_string=sid_string, runs=runs)
        except Exception as exc:  # noqa: BLE001 - any failure means "fall back to the job"
            _AC_STATE["error"] = str(exc)
        return _AC_STATE["container"]


def appcontainer_error() -> str | None:
    appcontainer()
    return _AC_STATE["error"]


def _sweep_stale_runs(runs: Path, max_age: float = 3600) -> None:
    cutoff = time.time() - max_age
    for entry in runs.iterdir():
        try:
            if entry.is_dir() and entry.stat().st_mtime < cutoff:
                shutil.rmtree(entry, ignore_errors=True)
        except OSError:
            pass


# ---------------------------------------------------------------- learner programs

RESOURCE_SUFFIXES = {".txt", ".dat", ".csv", ".in", ".json"}
MAX_RESOURCE_BYTES = 2 * 1024 * 1024


def _copy_resources(source_dir, target: Path) -> None:
    """Copy small data files (e.g. input.txt in a workspace) next to the staged program."""
    if not source_dir:
        return
    root, total = Path(source_dir), 0
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in RESOURCE_SUFFIXES or "build" in path.relative_to(root).parts:
            continue
        total += path.stat().st_size
        if total > MAX_RESOURCE_BYTES:
            break
        destination = target / path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)


def _environment_block(run_dir: Path) -> str:
    """Minimal environment: no user variables, no API keys.

    CreateProcess fails with ERROR_ENVVAR_NOT_FOUND (203) for AppContainer children unless
    LOCALAPPDATA is present (Windows rewrites it and TEMP to the container's own folder),
    so it is set to the run folder rather than the user's real path.
    """
    root = os.environ.get("SystemRoot", r"C:\Windows")
    env = {"SystemRoot": root, "WINDIR": root, "SystemDrive": os.environ.get("SystemDrive", "C:"),
           "TEMP": str(run_dir), "TMP": str(run_dir), "LOCALAPPDATA": str(run_dir), "PATH": root + r"\System32"}
    return "\0".join(f"{key}={value}" for key, value in sorted(env.items(), key=lambda item: item[0].upper())) + "\0\0"


def _remove_tree(path: Path) -> None:
    for attempt in range(6):
        try:
            shutil.rmtree(path)
            return
        except FileNotFoundError:
            return
        except OSError:
            time.sleep(0.05 * (attempt + 1))
    shutil.rmtree(path, ignore_errors=True)


def run_isolated(exe, input_bytes: bytes, *, timeout: float, cap: int, memory: int, resources_dir=None,
                 force_mode: str | None = None) -> SimpleNamespace:
    """Run a compiled learner program with the strongest available isolation."""
    mode = force_mode or os.environ.get("CPP_ADVENTURE_SANDBOX", "auto")
    container = appcontainer() if mode != "job" else None
    if container is not None:
        run_dir = container.runs / uuid.uuid4().hex
        run_dir.mkdir(parents=True)
        isolation = "appcontainer"
    else:
        run_dir = Path(tempfile.mkdtemp(prefix="cpp-adventure-run-"))
        isolation = "job"
    try:
        staged = run_dir / "program.exe"
        shutil.copyfile(exe, staged)
        _copy_resources(resources_dir, run_dir)
        result = _spawn(staged, run_dir, input_bytes, timeout=timeout, cap=cap, memory=memory,
                        sid=container.sid if container is not None else None)
        result.isolation = isolation
        return result
    finally:
        _remove_tree(run_dir)


def _spawn(exe: Path, cwd: Path, input_bytes: bytes, *, timeout: float, cap: int, memory: int, sid) -> SimpleNamespace:
    security = SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), None, True)
    open_handles: list = []  # raw HANDLE objects we still own

    def make_pipe():
        read, write = HANDLE(), HANDLE()
        if not CreatePipe(ctypes.byref(read), ctypes.byref(write), ctypes.byref(security), 1 << 16):
            raise _win_error("CreatePipe")
        open_handles.extend((read, write))
        return read, write

    def release(handle):
        open_handles[:] = [item for item in open_handles if item is not handle]

    job = None
    pi = PROCESS_INFORMATION()
    started = False
    try:
        stdin_r, stdin_w = make_pipe()
        stdout_r, stdout_w = make_pipe()
        stderr_r, stderr_w = make_pipe()
        for handle in (stdin_w, stdout_r, stderr_r):  # parent ends must not leak into the child
            SetHandleInformation(handle, HANDLE_FLAG_INHERIT, 0)
        job = create_job(process_memory=memory, active_processes=1, cpu_seconds=timeout + 1)
        attribute_count = 2 if sid else 1
        size = ctypes.c_size_t(0)
        InitializeProcThreadAttributeList(None, attribute_count, 0, ctypes.byref(size))
        attributes = (ctypes.c_byte * size.value)()
        if not InitializeProcThreadAttributeList(attributes, attribute_count, 0, ctypes.byref(size)):
            raise _win_error("InitializeProcThreadAttributeList")
        try:
            inherit = (HANDLE * 3)(stdin_r, stdout_w, stderr_w)
            if not UpdateProcThreadAttribute(attributes, 0, PROC_THREAD_ATTRIBUTE_HANDLE_LIST, inherit, ctypes.sizeof(inherit), None, None):
                raise _win_error("UpdateProcThreadAttribute(handles)")
            capabilities = SECURITY_CAPABILITIES(sid, None, 0, 0)
            if sid and not UpdateProcThreadAttribute(attributes, 0, PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES,
                                                     ctypes.byref(capabilities), ctypes.sizeof(capabilities), None, None):
                raise _win_error("UpdateProcThreadAttribute(AppContainer)")
            startup = STARTUPINFOEXW()
            startup.StartupInfo.cb = ctypes.sizeof(STARTUPINFOEXW)
            startup.StartupInfo.dwFlags = STARTF_USESTDHANDLES
            startup.StartupInfo.hStdInput, startup.StartupInfo.hStdOutput, startup.StartupInfo.hStdError = stdin_r, stdout_w, stderr_w
            startup.lpAttributeList = ctypes.cast(attributes, ctypes.c_void_p)
            command_line = ctypes.create_unicode_buffer(f'"{exe}"')
            environment = ctypes.create_unicode_buffer(_environment_block(cwd))
            flags = EXTENDED_STARTUPINFO_PRESENT | CREATE_SUSPENDED | CREATE_NO_WINDOW | CREATE_UNICODE_ENVIRONMENT
            if not CreateProcessW(str(exe), command_line, None, None, True, flags, ctypes.cast(environment, ctypes.c_void_p),
                                  str(cwd), ctypes.byref(startup), ctypes.byref(pi)):
                raise _win_error("CreateProcess")
            started = True
        finally:
            DeleteProcThreadAttributeList(attributes)
        for handle in (stdin_r, stdout_w, stderr_w):  # the child owns these now; keeping them would block EOF
            CloseHandle(handle)
            release(handle)
        if not AssignProcessToJobObject(job, pi.hProcess):
            error = _win_error("AssignProcessToJobObject")
            TerminateProcess(pi.hProcess, 1)
            raise error  # fail closed: the program never ran
        if ResumeThread(pi.hThread) == 0xFFFFFFFF:
            TerminateProcess(pi.hProcess, 1)
            raise _win_error("ResumeThread")

        buffers = {"out": bytearray(), "err": bytearray()}
        overflow = threading.Event()
        out_fd = msvcrt.open_osfhandle(stdout_r.value, os.O_RDONLY)
        release(stdout_r)
        err_fd = msvcrt.open_osfhandle(stderr_r.value, os.O_RDONLY)
        release(stderr_r)
        in_fd = msvcrt.open_osfhandle(stdin_w.value, 0)
        release(stdin_w)

        def pump(fd, key):
            try:
                while True:
                    try:
                        chunk = os.read(fd, 65536)
                    except OSError:
                        break
                    if not chunk:
                        break
                    room = cap - len(buffers[key])
                    if room > 0:
                        buffers[key].extend(chunk[:room])
                    if len(chunk) > room:
                        overflow.set()
                        TerminateJobObject(job, 1)
                        break
            finally:
                os.close(fd)

        def feed(fd):
            try:
                os.write(fd, input_bytes)
            except OSError:
                pass
            finally:
                os.close(fd)

        workers = [threading.Thread(target=pump, args=(out_fd, "out"), daemon=True),
                   threading.Thread(target=pump, args=(err_fd, "err"), daemon=True),
                   threading.Thread(target=feed, args=(in_fd,), daemon=True)]
        for worker in workers:
            worker.start()
        timed_out = WaitForSingleObject(pi.hProcess, int(timeout * 1000)) == WAIT_TIMEOUT
        if timed_out:
            TerminateJobObject(job, 1)
            WaitForSingleObject(pi.hProcess, 5000)
        for worker in workers:
            worker.join(timeout=2)
        code = DWORD(0)
        GetExitCodeProcess(pi.hProcess, ctypes.byref(code))
        return SimpleNamespace(returncode=int(code.value), stdout=bytes(buffers["out"]), stderr=bytes(buffers["err"]),
                               timed_out=timed_out and not overflow.is_set(), overflowed=overflow.is_set())
    finally:
        if started:
            CloseHandle(pi.hThread)
            CloseHandle(pi.hProcess)
        for handle in list(open_handles):
            CloseHandle(handle)
        if job:
            CloseHandle(job)  # KILL_ON_JOB_CLOSE: nothing survives this point
