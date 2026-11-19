"""Validated, data-only lesson plugins. Plugin code is never imported or executed."""
from __future__ import annotations

import json
import os
import re
import stat
import tempfile
from pathlib import Path


MAX_PLUGIN_BYTES = 100_000
PLUGIN_FIELDS = {"id", "version", "title", "description", "permissions", "lessons"}
LESSON_FIELDS = {"id", "title", "content"}
IDENTIFIER = re.compile(r"^[a-z][a-z0-9_-]{1,39}$")
VERSION = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class PluginError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _localized(value, maximum: int) -> bool:
    return isinstance(value, dict) and set(value) == {"tr", "ru"} and all(
        isinstance(value[key], str) and 0 < len(value[key].strip()) <= maximum
        for key in ("tr", "ru")
    )


def validate_manifest(raw) -> tuple[dict | None, str | None]:
    if not isinstance(raw, dict) or set(raw) - PLUGIN_FIELDS:
        return None, "manifest_fields"
    if not IDENTIFIER.fullmatch(str(raw.get("id", ""))) or not VERSION.fullmatch(str(raw.get("version", ""))):
        return None, "manifest_identity"
    if not _localized(raw.get("title"), 80) or not _localized(raw.get("description"), 300):
        return None, "manifest_localization"
    permissions = raw.get("permissions", [])
    if permissions != ["lessons.read"]:
        return None, "permission_denied"
    lessons = raw.get("lessons")
    if not isinstance(lessons, list) or not 1 <= len(lessons) <= 12:
        return None, "lesson_limit"
    clean = []
    ids = set()
    for lesson in lessons:
        if not isinstance(lesson, dict) or set(lesson) - LESSON_FIELDS:
            return None, "lesson_fields"
        if not IDENTIFIER.fullmatch(str(lesson.get("id", ""))) or lesson["id"] in ids:
            return None, "lesson_identity"
        if not _localized(lesson.get("title"), 100) or not _localized(lesson.get("content"), 3000):
            return None, "lesson_localization"
        ids.add(lesson["id"])
        clean.append({"id": lesson["id"], "title": lesson["title"], "content": lesson["content"]})
    normalized = {
        "id": raw["id"], "version": raw["version"], "title": raw["title"],
        "description": raw["description"], "permissions": ["lessons.read"], "lessons": clean,
    }
    try:
        if len(json.dumps(normalized, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) > MAX_PLUGIN_BYTES:
            return None, "size_limit"
    except (TypeError, ValueError):
        return None, "manifest_fields"
    return normalized, None


def _is_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    attrs = getattr(info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return stat.S_ISLNK(info.st_mode) or bool(attrs & reparse)


def _plugin_folder(directory: Path, create: bool = False) -> Path:
    directory = Path(directory)
    if _is_reparse(directory):
        raise PluginError("plugin_directory_unsafe")
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    if not directory.is_dir():
        raise PluginError("plugin_directory_unavailable")
    resolved = directory.resolve(strict=True)
    if _is_reparse(resolved):
        raise PluginError("plugin_directory_unsafe")
    return resolved


def _read_manifest(file: Path) -> tuple[dict | None, str | None]:
    if _is_reparse(file):
        return None, "symlink_rejected"
    try:
        info = file.stat()
        if not stat.S_ISREG(info.st_mode):
            return None, "file_rejected"
        if info.st_size > MAX_PLUGIN_BYTES:
            return None, "size_limit"
        if file.resolve(strict=True).parent != file.parent.resolve(strict=True):
            return None, "path_rejected"
        raw = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, "invalid_json"
    return validate_manifest(raw)


def discover_plugins(directories) -> tuple[list[dict], list[dict]]:
    found, errors, used_ids = [], [], set()
    for directory in directories:
        folder = Path(directory)
        if not folder.is_dir() or _is_reparse(folder):
            continue
        try:
            safe_folder = _plugin_folder(folder)
            files = sorted(safe_folder.glob("*.json"))
        except (OSError, PluginError):
            continue
        for file in files:
            manifest, error = _read_manifest(file)
            if error:
                errors.append({"file": file.name[:80], "reason": error})
                continue
            if file.stem != manifest["id"]:
                errors.append({"file": file.name[:80], "reason": "filename_mismatch"})
                continue
            if manifest["id"] in used_ids:
                errors.append({"file": file.name[:80], "reason": "duplicate_id"})
                continue
            used_ids.add(manifest["id"])
            found.append(manifest)
    return found, errors


def _version_tuple(value: str) -> tuple[int, int, int]:
    match = VERSION.fullmatch(value)
    if not match:
        raise PluginError("manifest_identity")
    return tuple(map(int, match.groups()))


def install_plugin(raw, bundled_directory: Path, user_directory: Path) -> tuple[dict | None, str | None]:
    manifest, error = validate_manifest(raw)
    if error:
        return None, error
    try:
        bundled, _ = discover_plugins([bundled_directory])
        if any(item["id"] == manifest["id"] for item in bundled):
            return None, "bundled_plugin_reserved"
        folder = _plugin_folder(user_directory, create=True)
        target = folder / f"{manifest['id']}.json"
        if _is_reparse(target):
            return None, "plugin_file_unsafe"
        current_plugins, _ = discover_plugins([folder])
        current = next((item for item in current_plugins if item["id"] == manifest["id"]), None)
        if current:
            if _version_tuple(manifest["version"]) <= _version_tuple(current["version"]):
                return None, "version_not_newer"
            result = "updated"
        else:
            if target.exists():
                return None, "plugin_file_unsafe"
            result = "installed"
        serialized = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
        if len(serialized) > MAX_PLUGIN_BYTES:
            return None, "size_limit"
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", dir=folder, prefix=f".{manifest['id']}.", suffix=".tmp", delete=False) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(serialized)
                temporary.flush()
                os.fsync(temporary.fileno())
            if temporary_path.resolve(strict=True).parent != folder:
                return None, "path_rejected"
            os.replace(temporary_path, target)
            temporary_path = None
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        return {**manifest, "source": "local"}, result
    except PluginError as exc:
        return None, exc.code
    except OSError:
        return None, "plugin_write_failed"


def remove_plugin(plugin_id: str, bundled_directory: Path, user_directory: Path) -> str | None:
    if not IDENTIFIER.fullmatch(str(plugin_id)):
        return "manifest_identity"
    try:
        bundled, _ = discover_plugins([bundled_directory])
        if any(item["id"] == plugin_id for item in bundled):
            return "bundled_plugin_reserved"
        folder = _plugin_folder(user_directory)
        target = folder / f"{plugin_id}.json"
        if _is_reparse(target):
            return "plugin_file_unsafe"
        manifest, error = _read_manifest(target)
        if error or not manifest or manifest["id"] != plugin_id:
            return error or "plugin_not_found"
        target.unlink()
        return None
    except PluginError as exc:
        return exc.code
    except OSError:
        return "plugin_remove_failed"
