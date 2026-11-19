"""Windows desktop entry point for C++ Adventure (WebView2, no browser tab)."""
from __future__ import annotations

import socket
import threading
import ctypes
import traceback
from datetime import datetime, timezone
from pathlib import Path

import webview

import server


def log_startup(message: str) -> None:
    try:
        folder = server.DATA_ROOT / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / "startup.log").open("a", encoding="utf-8") as log:
            log.write(f"{datetime.now(timezone.utc).isoformat()} {message}\n")
    except OSError:
        pass


def available_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main() -> None:
    http_server = None
    try:
        log_startup("database initialization started")
        server.init_db()
        log_startup("database initialization complete")
        port = available_port()
        http_server = server.ThreadingHTTPServer(("127.0.0.1", port), server.Handler)
        log_startup(f"local HTTP listener created on 127.0.0.1:{port}")
        worker = threading.Thread(target=http_server.serve_forever, name="cpp-adventure-local", daemon=True)
        worker.start()
        log_startup("local HTTP service started")
        webview.create_window(
            "C++ Adventure",
            f"http://127.0.0.1:{port}",
            width=1440,
            height=920,
            min_size=(980, 680),
            background_color="#0b0d14",
        )
        log_startup("desktop window created")
        webview.start(debug=False)
        log_startup("desktop window closed normally")
    except Exception as error:
        detail = traceback.format_exc()
        log_startup(f"startup error: {error!r}\n{detail}")
        try:
            ctypes.windll.user32.MessageBoxW(
                None,
                "C++ Adventure başlatılamadı. Ayrıntılar yerel startup.log dosyasına kaydedildi.\n"
                "Не удалось запустить C++ Adventure. Подробности сохранены в локальном startup.log.",
                "C++ Adventure",
                0x10,
            )
        except Exception:
            pass
        raise
    finally:
        if http_server is not None:
            http_server.shutdown()
            http_server.server_close()


if __name__ == "__main__":
    main()
