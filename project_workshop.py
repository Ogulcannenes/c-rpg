"""Profile-scoped multi-file C++ workspace and bounded local build helpers."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath

from sandbox import run_limited


MAX_FILES = 24
MAX_FILE_CHARS = 20_000
MAX_WORKSPACE_CHARS = 100_000
SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9_. -]{1,64}$")
SOURCE_SUFFIXES = {".cpp", ".cc", ".cxx"}
HEADER_SUFFIXES = {".h", ".hpp", ".hh", ".txt"}


def resolve_cmake() -> str | None:
    found=shutil.which("cmake") or shutil.which("cmake.exe")
    if found: return found
    roaming=Path(os.environ.get("APPDATA", Path.home()/"AppData"/"Roaming"))
    base=roaming/"Python"
    if base.is_dir():
        current=base/f"Python{sys.version_info.major}{sys.version_info.minor}"/"site-packages"/"cmake"/"data"/"bin"/"cmake.exe"
        if current.is_file(): return str(current)
        for candidate in sorted(base.glob("Python*/site-packages/cmake/data/bin/cmake.exe"),reverse=True):
            if candidate.is_file(): return str(candidate)
    return None


def validate_files(files: object) -> tuple[dict[str, str] | None, str | None]:
    if not isinstance(files, dict) or not files or len(files) > MAX_FILES:
        return None, "Proje 1–24 dosya içermeli. / В проекте должно быть от 1 до 24 файлов."
    clean: dict[str, str] = {}
    total = 0
    for raw_path, content in files.items():
        if not isinstance(raw_path, str) or not isinstance(content, str):
            return None, "Dosya adı ve içeriği metin olmalı. / Имя и содержимое файла должны быть текстом."
        path = PurePosixPath(raw_path.replace("\\", "/"))
        if path.is_absolute() or len(path.parts) > 4 or any(part in {"", ".", ".."} or not SAFE_COMPONENT.fullmatch(part) for part in path.parts):
            return None, "Dosya yolu güvenli değil. / Небезопасный путь к файлу."
        if path.suffix.lower() not in SOURCE_SUFFIXES | HEADER_SUFFIXES and path.name != "CMakeLists.txt":
            return None, "Yalnızca C++ kaynak/header, metin ve CMakeLists.txt dosyaları destekleniyor. / Поддерживаются только файлы C++, заголовки, текст и CMakeLists.txt."
        if len(content) > MAX_FILE_CHARS:
            return None, "Bir dosya 20.000 karakteri aşamaz. / Файл не может превышать 20 000 символов."
        key = path.as_posix()
        if key in clean:
            return None, "Yinelenen dosya yolu. / Повторяющийся путь файла."
        clean[key] = content
        total += len(content)
    if total > MAX_WORKSPACE_CHARS:
        return None, "Proje toplamı 100.000 karakter sınırını aşıyor. / Проект превышает лимит в 100 000 символов."
    if not any(Path(name).suffix.lower() in SOURCE_SUFFIXES for name in clean):
        return None, "Projede en az bir .cpp kaynak dosyası olmalı. / В проекте нужен хотя бы один файл .cpp."
    return clean, None


def build_project(files: dict[str, str], input_text: str = "", mode: str = "g++") -> dict:
    compiler = shutil.which("g++") or shutil.which("clang++")
    cmake = resolve_cmake() if mode == "cmake" else None
    if mode not in {"g++", "cmake"}:
        return {"ok": False, "phase": "validate", "error": "Build modu geçersiz. / Неверный режим сборки."}
    if not compiler:
        return {"ok": False, "phase": "compiler_missing", "error": "G++/Clang++ bulunamadı. / Не найден G++/Clang++."}
    if mode == "cmake" and not cmake:
        return {"ok": False, "phase": "cmake_missing", "error": "CMake kurulu değil. G++ ile derleyebilir veya CMake kurabilirsiniz. / CMake не установлен. Можно собрать через G++."}
    if not isinstance(input_text, str) or len(input_text) > 2000:
        return {"ok": False, "phase": "validate", "error": "Girdi 2.000 karakteri aşamaz. / Ввод не может превышать 2 000 символов."}
    valid, error = validate_files(files)
    if error:
        return {"ok": False, "phase": "validate", "error": error}
    sources = sorted(name for name in valid if Path(name).suffix.lower() in SOURCE_SUFFIXES)
    started = time.perf_counter()
    no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    with tempfile.TemporaryDirectory(prefix="cpp-adventure-project-") as temp_dir:
        root = Path(temp_dir)
        for name, content in valid.items():
            if name == "CMakeLists.txt":
                continue
            target = root.joinpath(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        exe = root / ("adventure.exe" if os.name == "nt" else "adventure")
        if mode == "g++":
            command = [compiler, "-std=c++20", "-O0", "-pipe", "-I", str(root), "-I", str(root / "include"), *[str(root.joinpath(*PurePosixPath(name).parts)) for name in sources], "-o", str(exe)]
            cwd = str(root)
        else:
            source_names = " ".join(f'"{name}"' for name in sources)
            cmake_text = "\n".join(("cmake_minimum_required(VERSION 3.20)", "project(CppAdventureWorkspace LANGUAGES CXX)", "set(CMAKE_CXX_STANDARD 20)", "set(CMAKE_CXX_STANDARD_REQUIRED ON)", f"add_executable(adventure {source_names})", 'target_include_directories(adventure PRIVATE "${CMAKE_SOURCE_DIR}/include")', ""))
            (root / "CMakeLists.txt").write_text(cmake_text, encoding="utf-8")
            build_dir = root / "build"
            command = [cmake, "-S", str(root), "-B", str(build_dir), "-G", "MinGW Makefiles", f"-DCMAKE_CXX_COMPILER={compiler}", f"-DCMAKE_MAKE_PROGRAM={shutil.which('mingw32-make') or 'mingw32-make'}", "-DCMAKE_BUILD_TYPE=Debug"]
            try:
                configured = subprocess.run(command, capture_output=True, text=True, timeout=20, cwd=str(root), encoding="utf-8", errors="replace", creationflags=no_window)
                if configured.returncode:
                    return {"ok": False, "phase": "configure", "compile_ok": False, "compile_output": (configured.stdout + configured.stderr)[-6000:], "error": (configured.stdout + configured.stderr)[-6000:], "elapsed_ms": round((time.perf_counter()-started)*1000)}
                built = subprocess.run([cmake, "--build", str(build_dir), "--config", "Debug", "--parallel", "2"], capture_output=True, text=True, timeout=25, cwd=str(root), encoding="utf-8", errors="replace", creationflags=no_window)
            except subprocess.TimeoutExpired:
                return {"ok": False, "phase": "compile_timeout", "compile_ok": False, "compile_output": "", "error": "CMake derlemesi süre sınırını aştı. / Сборка CMake превысила лимит времени.", "elapsed_ms": round((time.perf_counter()-started)*1000)}
            if built.returncode:
                message = (built.stdout + built.stderr)[-6000:]
                return {"ok": False, "phase": "compile", "compile_ok": False, "compile_output": message, "error": message, "elapsed_ms": round((time.perf_counter()-started)*1000)}
            exe = build_dir / exe.name
            command = [str(exe)]
            cwd = str(root)
        if mode == "g++":
            try:
                built = subprocess.run(command, capture_output=True, text=True, timeout=20, cwd=cwd, encoding="utf-8", errors="replace", creationflags=no_window)
            except subprocess.TimeoutExpired:
                return {"ok": False, "phase": "compile_timeout", "compile_ok": False, "compile_output": "", "error": "Derleme 20 saniyede tamamlanmadı. / Компиляция не завершилась за 20 секунд.", "elapsed_ms": round((time.perf_counter()-started)*1000)}
            if built.returncode:
                message = (built.stdout + built.stderr)[-6000:]
                return {"ok": False, "phase": "compile", "compile_ok": False, "compile_output": message, "error": message, "elapsed_ms": round((time.perf_counter()-started)*1000)}
        run, timed_out, overflowed = run_limited(command if mode == "cmake" else [str(exe)], input_text, 3, cwd, no_window)
        if overflowed:
            return {"ok": False, "phase": "output_limit", "compile_ok": True, "compile_output": "", "stdout": run.stdout[-6000:], "stderr": "", "exit_code": None, "elapsed_ms": round((time.perf_counter()-started)*1000), "error": "Program çok fazla çıktı üretti (64 KB sınırı). / Программа вывела слишком много данных (лимит 64 КБ)."}
        if timed_out:
            return {"ok": False, "phase": "run_timeout", "compile_ok": True, "compile_output": "", "stdout": "", "stderr": "", "exit_code": None, "elapsed_ms": round((time.perf_counter()-started)*1000), "error": "Program 3 saniyede tamamlanmadı. / Программа превысила лимит 3 секунды."}
        return {"ok": run.returncode == 0, "phase": "complete" if run.returncode == 0 else "runtime", "compile_ok": True, "compile_output": "", "stdout": run.stdout[-6000:], "stderr": run.stderr[-3000:], "exit_code": run.returncode, "elapsed_ms": round((time.perf_counter()-started)*1000), "error": "" if run.returncode == 0 else f"Program {run.returncode} koduyla kapandı. / Программа завершилась с кодом {run.returncode}."}
