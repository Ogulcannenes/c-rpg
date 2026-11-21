"""Running untrusted learner programs and the compiler with hard limits.

Public API (stable for callers):
- ``run_limited(command, input_text, timeout, cwd, creationflags=0, cap=..., resources_dir=None)``
  runs a compiled learner program -> ``(result, timed_out, overflowed)``; ``result`` has
  ``returncode``, ``stdout``, ``stderr`` (str) and ``isolation``.
- ``run_tool(command, timeout, cwd, input_text=None)`` runs g++/clang/cmake with memory and
  process-tree limits -> namespace with ``returncode``, ``stdout``, ``stderr`` (str), ``timed_out``.
- ``build_slot()`` limits how many compile+run jobs execute at once (``SandboxBusy`` if none frees up).
- ``source_policy_violation(source)`` rejects preprocessor tricks that read arbitrary files at
  compile time (absolute/parent ``#include``, ``#embed``, ``.incbin``).
- ``isolation_status()`` describes the isolation level actually available on this machine.

Windows (primary platform): see ``sandbox_windows`` — suspended start, Job Object attached
before execution, AppContainer with no capabilities when available, minimal environment.
POSIX (development only): rlimits, a new session/process group, minimal environment.
"""
from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

MAX_PROGRAM_OUTPUT = 64_000
PROGRAM_MEMORY_LIMIT = 512 * 1024 * 1024
COMPILER_PROCESS_MEMORY = 2 * 1024 * 1024 * 1024
COMPILER_JOB_MEMORY = 3 * 1024 * 1024 * 1024
MAX_PARALLEL_BUILDS = max(1, min(2, (os.cpu_count() or 2) // 2))
BUILD_SLOT_WAIT_SECONDS = 60

_BUILD_SLOTS = threading.BoundedSemaphore(MAX_PARALLEL_BUILDS)

if os.name == "nt":
    import sandbox_windows as _win
else:  # pragma: no cover - Windows is the shipped platform
    _win = None


class SandboxBusy(RuntimeError):
    """Raised when no build slot frees up in time."""


@contextmanager
def build_slot(wait: float = BUILD_SLOT_WAIT_SECONDS):
    """Bound concurrent compile/run work so the app stays responsive."""
    if not _BUILD_SLOTS.acquire(timeout=wait):
        raise SandboxBusy("Derleyici meşgul; biraz sonra tekrar dene. / Компилятор занят, попробуй чуть позже.")
    try:
        yield
    finally:
        _BUILD_SLOTS.release()


def normalize_output(text) -> str:
    """Compare program output without being fooled by CRLF or trailing spaces."""
    text = str(text if text is not None else "").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.strip().split("\n"))


# ---------------------------------------------------------------- compile-time file access policy

_SPLICE = re.compile(r"\\\r?\n")
_DIRECTIVE = re.compile(r"^[ \t]*(?:#|%:)[ \t]*(include_next|include|import|embed|pragma)\b(.*)$", re.MULTILINE)
_HAS_INCLUDE = re.compile(r"__has_(?:include|include_next|embed)\s*\(\s*([<\"])([^>\")]*)[>\"]")
_INCBIN = re.compile(r"incbin", re.IGNORECASE)
POLICY_MESSAGE = ("Güvenlik: #include/#embed yalnızca standart başlıklar ve proje içi göreli yollar için kullanılabilir. "
                  "/ Безопасность: #include/#embed разрешены только для стандартных заголовков и относительных путей проекта.")


_ASM_FILE_DIRECTIVE = re.compile(r"^[ \t]*\.(incbin|include)\b", re.IGNORECASE | re.MULTILINE)


def assembly_policy_violation(assembly: str) -> str | None:
    """Check compiler-generated assembly *before* it is assembled.

    Inline asm can hide ``.incbin``/``.include`` behind string concatenation or macros, so the
    only reliable place to look is the fully expanded ``-S`` output. Rejecting here means the
    assembler never opens the file, so its contents cannot leak through program output or
    assembler error messages.
    """
    return POLICY_MESSAGE if _ASM_FILE_DIRECTIVE.search(assembly) else None


def _unsafe_path(name: str) -> bool:
    name = name.strip().replace("\\", "/")
    return (not name or name.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", name) is not None
            or ".." in name.split("/"))


def source_policy_violation(source: str) -> str | None:
    """Return a bilingual error if the source tries to read files outside the project at compile time."""
    text = _SPLICE.sub("", source)  # line splices are removed before directives are parsed
    for kind, rest in _DIRECTIVE.findall(text):
        rest = rest.strip()
        if kind == "embed":
            return POLICY_MESSAGE
        if kind == "pragma":
            if re.match(r"GCC\s+dependency\b", rest):
                return POLICY_MESSAGE
            continue
        match = re.match(r"([<\"])([^>\"]*)[>\"]", rest)
        if not match or _unsafe_path(match.group(2)):  # computed "#include MACRO" or a path outside the project
            return POLICY_MESSAGE
    for _, name in _HAS_INCLUDE.findall(text):
        if _unsafe_path(name):
            return POLICY_MESSAGE
    if _INCBIN.search(text):
        return POLICY_MESSAGE
    return None


# ---------------------------------------------------------------- tools (compiler, cmake, clang)

def _posix_tool_limits():  # pragma: no cover - POSIX only
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (COMPILER_PROCESS_MEMORY, COMPILER_PROCESS_MEMORY))
    except Exception:
        pass


def run_tool(command, timeout, cwd, input_text: str | None = None) -> SimpleNamespace:
    """Run a trusted build tool with memory and process-tree limits. Output is decoded text."""
    data = input_text.encode("utf-8") if input_text is not None else None
    if _win is not None:
        raw = _win.run_tool(command, timeout=timeout, cwd=cwd, input_bytes=data,
                            process_memory=COMPILER_PROCESS_MEMORY, job_memory=COMPILER_JOB_MEMORY)
    else:  # pragma: no cover - POSIX only
        proc = subprocess.Popen(command, stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd,
                                preexec_fn=_posix_tool_limits, start_new_session=True)
        timed_out = False
        try:
            out, err = proc.communicate(input=data, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGKILL)
            out, err = proc.communicate()
        raw = SimpleNamespace(returncode=proc.returncode, stdout=out, stderr=err, timed_out=timed_out)
    decode = lambda value: (value or b"").decode("utf-8", errors="replace").replace("\r\n", "\n")
    return SimpleNamespace(returncode=raw.returncode, stdout=decode(raw.stdout), stderr=decode(raw.stderr), timed_out=raw.timed_out)


# ---------------------------------------------------------------- learner programs

def _posix_limits():  # pragma: no cover - POSIX only
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (PROGRAM_MEMORY_LIMIT, PROGRAM_MEMORY_LIMIT))
        resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
        resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_PROGRAM_OUTPUT * 8, MAX_PROGRAM_OUTPUT * 8))
    except Exception:
        pass


def _run_posix(command, input_text, timeout, cap):  # pragma: no cover - POSIX only
    run_dir = Path(tempfile.mkdtemp(prefix="cpp-adventure-run-"))
    try:
        staged = run_dir / "program"
        shutil.copy2(command[0], staged)
        env = {"PATH": "/usr/bin:/bin", "TMPDIR": str(run_dir), "HOME": str(run_dir), "LANG": "C.UTF-8"}
        proc = subprocess.Popen([str(staged), *command[1:]], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                cwd=run_dir, env=env, preexec_fn=_posix_limits, start_new_session=True)
        timed_out = overflowed = False
        try:
            out, err = proc.communicate(input=input_text.encode("utf-8", errors="replace"), timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGKILL)
            out, err = proc.communicate()
        if len(out) > cap or len(err) > cap:
            overflowed, out, err = True, out[:cap], err[:cap]
        return SimpleNamespace(returncode=proc.returncode, stdout=out, stderr=err, timed_out=timed_out and not overflowed,
                               overflowed=overflowed, isolation="posix")
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def run_limited(command, input_text, timeout, cwd=None, creationflags=0, cap=MAX_PROGRAM_OUTPUT, resources_dir=None):
    """Run a compiled learner program -> (result, timed_out, overflowed).

    The program is copied into a fresh, empty working folder; ``resources_dir`` (optional)
    supplies small data files such as ``input.txt`` from a multi-file workspace.
    ``cwd`` and ``creationflags`` are accepted for backward compatibility and ignored.
    """
    del cwd, creationflags
    if _win is not None:
        raw = _win.run_isolated(Path(command[0]), input_text.encode("utf-8", errors="replace"), timeout=timeout, cap=cap,
                                memory=PROGRAM_MEMORY_LIMIT, resources_dir=resources_dir)
    else:  # pragma: no cover - POSIX only
        raw = _run_posix(command, input_text, timeout, cap)
    decode = lambda data: data.decode("utf-8", errors="replace").replace("\r\n", "\n")
    result = SimpleNamespace(returncode=raw.returncode, stdout=decode(raw.stdout), stderr=decode(raw.stderr), isolation=raw.isolation)
    return result, raw.timed_out, raw.overflowed


def isolation_status() -> dict:
    """What protection learner programs actually get on this machine (for /api/health and the UI)."""
    if _win is None:
        return {"mode": "posix", "network_blocked": False, "files_blocked": False, "detail": "rlimits + process group"}
    forced = os.environ.get("CPP_ADVENTURE_SANDBOX", "auto") == "job"
    container = None if forced else _win.appcontainer()
    if container is not None:
        return {"mode": "appcontainer", "network_blocked": True, "files_blocked": True, "detail": ""}
    return {"mode": "job", "network_blocked": False, "files_blocked": False,
            "detail": "forced by CPP_ADVENTURE_SANDBOX=job" if forced else (_win.appcontainer_error() or "")}
