"""Safe local C++ concurrency simulation and compiler-output exploration."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def simulate_counter(workers: int = 2, increments: int = 3, use_mutex: bool = False) -> dict:
    workers = max(1, min(4, int(workers)))
    increments = max(1, min(5, int(increments)))
    steps = []
    counter = 0
    if use_mutex:
        for iteration in range(increments):
            for worker in range(1, workers + 1):
                before = counter
                counter += 1
                steps.append({"line": "lock → read → increment → unlock", "thread": f"T{worker}",
                              "value": counter, "text": f"Mutex: T{worker} tek başına kilit aldı ve sayacı {before} → {counter} yaptı.",
                              "text_ru": f"Mutex: T{worker} захватил блокировку и изменил счётчик {before} → {counter}.",
                              "iteration": iteration + 1})
    else:
        for iteration in range(increments):
            snapshot = counter
            reads = {}
            for worker in range(1, workers + 1):
                reads[worker] = snapshot
                steps.append({"line": "int local = counter;", "thread": f"T{worker}", "value": snapshot,
                              "text": f"T{worker} mevcut değeri {snapshot} okudu; diğer thread'lerin yazıları henüz yok.",
                              "text_ru": f"T{worker} прочитал значение {snapshot}; записи других потоков ещё не видны.",
                              "iteration": iteration + 1})
            for worker in range(1, workers + 1):
                previous = counter
                counter = reads[worker] + 1
                steps.append({"line": "counter = local + 1;", "thread": f"T{worker}", "value": counter,
                              "text": f"T{worker} {reads[worker]} + 1 yazar; son yazma {previous} değerini ezmiş olabilir.",
                              "text_ru": f"T{worker} записывает {reads[worker]} + 1; последняя запись могла затереть {previous}.",
                              "iteration": iteration + 1})
    expected = workers * increments
    return {"mode": "mutex" if use_mutex else "race", "workers": workers, "increments": increments,
            "final": counter, "expected": expected, "lost_updates": max(0, expected - counter), "steps": steps,
            "notice_tr": "Bu güvenli bir adım simülasyonudur; gerçek thread başlatılmaz.",
            "notice_ru": "Это безопасная пошаговая симуляция; реальные потоки не запускаются."}


def assembly_outputs(source: str, compiler: str | None, max_source: int = 20_000) -> dict:
    if not isinstance(source, str) or not source.strip():
        return {"ok": False, "error": "C++ kodu boş olamaz."}
    if len(source.encode("utf-8")) > max_source:
        return {"ok": False, "error": f"Kod {max_source} bayt sınırını aşıyor."}
    if not compiler:
        return {"ok": False, "error": "G++/Clang++ bulunamadı."}
    outputs = []
    with tempfile.TemporaryDirectory(prefix="cpp-adventure-asm-") as folder:
        root = Path(folder)
        cpp = root / "explore.cpp"
        cpp.write_text(source, encoding="utf-8")
        for opt in ("O0", "O2"):
            asm = root / f"{opt}.s"
            try:
                result = subprocess.run([compiler, "-std=c++20", "-S", f"-{opt}", "-masm=intel", "-fmax-errors=3", str(cpp), "-o", str(asm)],
                                        cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=12)
            except subprocess.TimeoutExpired:
                outputs.append({"optimization": opt, "ok": False, "assembly": "", "errors": "Derleme 12 saniye sınırını aştı."})
                continue
            except OSError as error:
                outputs.append({"optimization": opt, "ok": False, "assembly": "", "errors": str(error)[:2000]})
                continue
            text = asm.read_text(encoding="utf-8", errors="replace")[:12_000] if asm.exists() else ""
            outputs.append({"optimization": opt, "ok": result.returncode == 0, "assembly": text,
                            "errors": result.stderr[:4000], "truncated": len(text) >= 12_000})
    return {"ok": all(item["ok"] for item in outputs), "compiler": Path(compiler).name, "outputs": outputs,
            "notice_tr": "Çıktı bu bilgisayardaki derleyiciden üretildi; optimizasyon çıktısı derleyici sürümüne bağlıdır.",
            "notice_ru": "Вывод получен локальным компилятором; результат оптимизации зависит от версии компилятора."}
