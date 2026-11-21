"""Windows desktop entry point for C++ Adventure (WebView2, no browser tab).

Phase 11: one running copy per Windows user (a second launch brings the first window to the
front), a clear message when the WebView2 runtime is missing, and an uninstall helper
(``--remove-sandbox-profile``) that the installer runs to delete the sandbox AppContainer.
"""
from __future__ import annotations

import sys
import threading
import ctypes
import traceback
from datetime import datetime, timezone
from pathlib import Path

import server

WINDOW_TITLE = "C++ Adventure"
# Shared with the Inno Setup script (AppMutex), so setup can ask the user to close the app first.
SINGLE_INSTANCE_MUTEX = "Local\\CppAdventure.SingleInstance"
ERROR_ALREADY_EXISTS = 183
WEBVIEW2_CLIENT = r"Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
WEBVIEW2_DOWNLOAD = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"


def message_box(text: str, flags: int = 0x40) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(None, text, WINDOW_TITLE, flags)
    except Exception:
        pass


def webview2_version(registry=None) -> str:
    """Installed Evergreen WebView2 runtime version, or "" (machine-wide or per-user install)."""
    if registry is None:
        try:
            import winreg as registry
        except ImportError:  # pragma: no cover - not Windows
            return ""
    places = ((registry.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\" + WEBVIEW2_CLIENT),
              (registry.HKEY_LOCAL_MACHINE, "SOFTWARE\\" + WEBVIEW2_CLIENT),
              (registry.HKEY_CURRENT_USER, "Software\\" + WEBVIEW2_CLIENT))
    for hive, path in places:
        try:
            with registry.OpenKey(hive, path) as key:
                version, _ = registry.QueryValueEx(key, "pv")
        except OSError:
            continue
        if version and version != "0.0.0.0":
            return str(version)
    return ""


def acquire_single_instance(kernel32=None):
    """Return a mutex handle for this copy, or None when another copy already runs."""
    kernel32 = kernel32 or ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.CreateMutexW(None, False, SINGLE_INSTANCE_MUTEX)
    if handle and ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return None
    return handle or True  # if the mutex cannot be created, do not block the app


def focus_existing_window(user32=None) -> bool:
    user32 = user32 or ctypes.windll.user32
    hwnd = user32.FindWindowW(None, WINDOW_TITLE)
    if not hwnd:
        return False
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    user32.SetForegroundWindow(hwnd)
    return True


# A fixed loopback port keeps the page origin stable between launches, so the remembered profile,
# language, text size and motion settings (localStorage) survive a restart. Port 0 is the fallback.
PREFERRED_PORT = 47615


def bind_app_server(preferred: int = PREFERRED_PORT):
    try:
        return server.create_app_server(preferred)
    except OSError:
        return server.create_app_server(0)


def webview_storage_path() -> Path:
    """WebView2 profile folder. pywebview's default private mode forgets localStorage on every
    start, which sent the learner back to the profile picker each time."""
    folder = server.DATA_ROOT / "webview"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def remove_sandbox_profile() -> int:
    """Run by the uninstaller. Learner profiles and progress in %LOCALAPPDATA% are not touched."""
    try:
        import sandbox_windows
        return 0 if sandbox_windows.remove_appcontainer_profile() else 1
    except Exception:
        return 1


def log_startup(message: str) -> None:
    try:
        folder = server.DATA_ROOT / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / "startup.log").open("a", encoding="utf-8") as log:
            log.write(f"{datetime.now(timezone.utc).isoformat()} {message}\n")
    except OSError:
        pass


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--remove-sandbox-profile" in argv:
        return remove_sandbox_profile()
    instance = acquire_single_instance()
    if instance is None:
        log_startup("second launch: focusing the running window")
        focus_existing_window()
        return 0
    if not webview2_version():
        log_startup("WebView2 runtime not found")
        message_box("C++ Adventure için Microsoft Edge WebView2 Runtime gerekiyor. Ücretsiz kurulum sayfası:\n"
                    f"{WEBVIEW2_DOWNLOAD}\n\n"
                    "Для C++ Adventure нужен Microsoft Edge WebView2 Runtime. Бесплатная установка:\n"
                    f"{WEBVIEW2_DOWNLOAD}", 0x30)
        return 2
    import webview  # imported late so the checks above work even if pywebview fails to load

    http_server = None
    try:
        log_startup("database initialization started")
        server.init_db()
        log_startup("database initialization complete")
        # Port 0 is bound atomically by the OS (no probe-then-rebind race), and the start URL
        # carries a one-time code that gives this window the per-launch API session cookie.
        http_server, _auth, start_url = bind_app_server()
        port = http_server.server_address[1]
        log_startup(f"local HTTP listener created on 127.0.0.1:{port}")
        worker = threading.Thread(target=http_server.serve_forever, name="cpp-adventure-local", daemon=True)
        worker.start()
        log_startup("local HTTP service started")
        if not server.COMPILER:
            log_startup("no C++ compiler found; lessons work, code missions will explain how to install MSYS2 G++")
        webview.create_window(
            WINDOW_TITLE,
            start_url,
            width=1440,
            height=920,
            min_size=(980, 680),
            background_color="#0b0d14",
        )
        log_startup("desktop window created")
        webview.start(debug=False, private_mode=False, storage_path=str(webview_storage_path()))
        log_startup("desktop window closed normally")
        return 0
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
    sys.exit(main())
