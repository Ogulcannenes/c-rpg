"""Local storage for AI provider API keys.

Windows: values are encrypted with DPAPI (CryptProtectData, current-user scope, app-specific
entropy) and written as ``<name>.dpapi``; only the same Windows user on the same machine can
decrypt them. A legacy plaintext ``<name>`` file from older versions is migrated to DPAPI on
first read and the plaintext copy is removed.

Other platforms (development only): plaintext file with 0600 permissions.
"""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from pathlib import Path

_ENTROPY = b"CppAdventure.secret-store.v1"
CRYPTPROTECT_UI_FORBIDDEN = 0x1


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _blob(data: bytes):
    buffer = ctypes.create_string_buffer(data, len(data))
    return _Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer


if os.name == "nt":
    _crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _CryptProtectData = _crypt32.CryptProtectData
    _CryptProtectData.argtypes = [ctypes.POINTER(_Blob), wintypes.LPCWSTR, ctypes.POINTER(_Blob), ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_Blob)]
    _CryptProtectData.restype = wintypes.BOOL
    _CryptUnprotectData = _crypt32.CryptUnprotectData
    _CryptUnprotectData.argtypes = [ctypes.POINTER(_Blob), ctypes.c_void_p, ctypes.POINTER(_Blob), ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_Blob)]
    _CryptUnprotectData.restype = wintypes.BOOL
    _LocalFree = _kernel32.LocalFree
    _LocalFree.argtypes = [ctypes.c_void_p]
    _LocalFree.restype = ctypes.c_void_p

    def protect(data: bytes) -> bytes:
        source, _keep1 = _blob(data)
        entropy, _keep2 = _blob(_ENTROPY)
        out = _Blob()
        if not _CryptProtectData(ctypes.byref(source), "C++ Adventure API key", ctypes.byref(entropy), None, None, CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(out)):
            raise OSError(ctypes.get_last_error(), "CryptProtectData failed")
        try:
            return ctypes.string_at(out.pbData, out.cbData)
        finally:
            _LocalFree(ctypes.cast(out.pbData, ctypes.c_void_p))

    def unprotect(data: bytes) -> bytes:
        source, _keep1 = _blob(data)
        entropy, _keep2 = _blob(_ENTROPY)
        out = _Blob()
        if not _CryptUnprotectData(ctypes.byref(source), None, ctypes.byref(entropy), None, None, CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(out)):
            raise OSError(ctypes.get_last_error(), "CryptUnprotectData failed")
        try:
            return ctypes.string_at(out.pbData, out.cbData)
        finally:
            _LocalFree(ctypes.cast(out.pbData, ctypes.c_void_p))

    ENCRYPTED = True
else:  # pragma: no cover - development platforms only
    def protect(data: bytes) -> bytes:
        return data

    def unprotect(data: bytes) -> bytes:
        return data

    ENCRYPTED = False


def _paths(directory: Path, name: str):
    return Path(directory) / f"{name}.dpapi", Path(directory) / name


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_bytes(data)
    try:
        os.chmod(temp, 0o600)
    except OSError:
        pass
    os.replace(temp, path)


def write_secret(directory: Path, name: str, value: str) -> None:
    encrypted, legacy = _paths(directory, name)
    if ENCRYPTED:
        _atomic_write(encrypted, protect(value.encode("utf-8")))
        legacy.unlink(missing_ok=True)
    else:  # pragma: no cover
        _atomic_write(legacy, value.encode("utf-8"))


def read_secret(directory: Path, name: str) -> str:
    """Return the stored value or "" (missing or undecryptable, e.g. copied from another user)."""
    encrypted, legacy = _paths(directory, name)
    if ENCRYPTED and encrypted.is_file():
        try:
            return unprotect(encrypted.read_bytes()).decode("utf-8").strip()
        except (OSError, UnicodeDecodeError):
            return ""
    if legacy.is_file():
        try:
            value = legacy.read_text(encoding="utf-8").strip()
        except OSError:
            return ""
        if ENCRYPTED and value:
            try:
                write_secret(directory, name, value)  # migrate the old plaintext file to DPAPI
            except OSError:
                pass
        return value
    return ""


def delete_secret(directory: Path, name: str) -> None:
    for path in _paths(directory, name):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
