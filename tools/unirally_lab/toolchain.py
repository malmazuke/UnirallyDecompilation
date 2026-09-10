"""Isolated, pinned CMake and Ninja from locked wheel artifacts.

The lock file names one artifact per supported platform with its origin URL
and SHA-256. ``bootstrap`` downloads into an ignored cache, verifies the
digest, extracts into an ignored install directory and writes a manifest of
resolved paths and observed versions. It never touches global settings.
Wheels are plain zip files; no Python package installation is involved.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import stat
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from .procs import run_bounded

LOCK_SCHEMA_VERSION = 1
MANIFEST_SCHEMA_VERSION = 1


class ToolchainError(Exception):
    pass


def platform_key() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if machine in ("amd64", "x86_64"):
        machine = "x86_64"
    elif machine in ("arm64", "aarch64"):
        machine = "aarch64" if system == "linux" else "arm64"
    return f"{system}-{machine}"


def load_lock(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ToolchainError(f"lock file not found: {path}")
    with open(path, encoding="utf-8") as fh:
        lock = json.load(fh)
    if lock.get("lock_schema_version") != LOCK_SCHEMA_VERSION:
        raise ToolchainError(f"unsupported lock schema {lock.get('lock_schema_version')!r} in {path}")
    return lock


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _download(url: str, dest: Path, timeout: float) -> str:
    """Fetch ``url`` to ``dest``. Returns the downloader used."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    if tmp.exists():
        tmp.unlink()
    if url.startswith("file://"):
        src = Path(urllib.request.url2pathname(url[len("file://"):]))
        if not src.is_file():
            raise ToolchainError(f"source file not found: {src}")
        shutil.copyfile(src, tmp)
        tmp.replace(dest)
        return "file-copy"
    curl = shutil.which("curl")
    if curl:
        result = run_bounded(
            [curl, "-fsSL", "--retry", "2", "--max-time", str(int(timeout)), "-o", str(tmp), url],
            timeout=timeout + 15,
        )
        if result.outcome == "passed":
            tmp.replace(dest)
            return f"curl ({curl})"
        detail = "timed out" if result.timed_out else result.tail(300)
        curl_error = f"curl failed: {detail}"
    else:
        curl_error = "curl not found"
    # Fallback: urllib. This can fail on Python builds without a CA bundle.
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp, open(tmp, "wb") as out:
            shutil.copyfileobj(resp, out)
    except Exception as exc:  # noqa: BLE001 - reported, not swallowed
        if tmp.exists():
            tmp.unlink()
        raise ToolchainError(f"download failed for {url}: {curl_error}; urllib: {exc}") from exc
    tmp.replace(dest)
    return "urllib"


def _extract(wheel: Path, prefix: str, dest: Path) -> int:
    """Extract members under ``prefix`` from the wheel into ``dest``; returns count."""
    count = 0
    with zipfile.ZipFile(wheel) as zf:
        for info in zf.infolist():
            if not info.filename.startswith(prefix) or info.filename.endswith("/"):
                continue
            rel = Path(info.filename[len(prefix):])
            if rel.is_absolute() or ".." in rel.parts:
                raise ToolchainError(f"refusing unsafe member path {info.filename}")
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
            mode = (info.external_attr >> 16) & 0o777
            if mode:
                os.chmod(target, mode)
            count += 1
    return count


def _mark_executable(path: Path) -> None:
    mode = path.stat().st_mode
    os.chmod(path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def bootstrap(lock: dict[str, Any], root: Path, timeout: float, checks: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Prepare every locked tool. Appends check dicts; returns the manifest or None on failure."""
    key = platform_key()
    cache_dir = root / lock["cache_dir"]
    install_dir = root / lock["install_dir"]
    manifest: dict[str, Any] = {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "platform": key,
        "lock_sha256": None,
        "tools": {},
    }
    ok = True
    for name, spec in lock["tools"].items():
        artifact = spec["artifacts"].get(key)
        if artifact is None:
            checks.append({"name": f"bootstrap_{name}", "outcome": "missing", "required": True,
                           "detail": f"no locked artifact for platform {key}"})
            ok = False
            continue
        wheel = cache_dir / artifact["filename"]
        try:
            if wheel.is_file() and sha256_of(wheel) == artifact["sha256"]:
                source = "cache"
            else:
                if wheel.exists():
                    wheel.unlink()
                source = _download(artifact["url"], wheel, timeout)
            observed = sha256_of(wheel)
            if observed != artifact["sha256"]:
                wheel.unlink()
                raise ToolchainError(
                    f"sha256 mismatch for {artifact['filename']}: expected {artifact['sha256']}, observed {observed}"
                )
            tool_dir = install_dir / f"{name}-{spec['version']}-{key}"
            stamp = tool_dir / ".installed.json"
            extracted = False
            if not (stamp.is_file() and json.loads(stamp.read_text()).get("sha256") == observed):
                if tool_dir.exists():
                    shutil.rmtree(tool_dir)
                tool_dir.mkdir(parents=True)
                count = _extract(wheel, spec["extract_prefix"], tool_dir)
                if count == 0:
                    raise ToolchainError(f"no members under {spec['extract_prefix']!r} in {wheel.name}")
                stamp.write_text(json.dumps({"sha256": observed, "members": count}) + "\n")
                extracted = True
            binaries = {}
            for bin_name, rel in spec["binaries"].items():
                path = tool_dir / rel
                if not path.is_file():
                    raise ToolchainError(f"expected binary missing after extraction: {path}")
                _mark_executable(path)
                binaries[bin_name] = str(path)
            probe = run_bounded([binaries[name], "--version"], timeout=30)
            if probe.outcome != "passed":
                raise ToolchainError(f"{name} --version failed: {probe.tail(300)}")
            version_line = probe.stdout.strip().splitlines()[0] if probe.stdout.strip() else ""
            if spec["version"] not in version_line:
                raise ToolchainError(f"{name} reported {version_line!r}, expected {spec['version']}")
            manifest["tools"][name] = {
                "version": spec["version"],
                "reported": version_line,
                "artifact": artifact["filename"],
                "sha256": observed,
                "url": artifact["url"],
                "binaries": binaries,
            }
            checks.append({"name": f"bootstrap_{name}", "outcome": "passed", "required": True,
                           "detail": f"{version_line}; source={source}; extracted={extracted}"})
        except (ToolchainError, OSError, zipfile.BadZipFile) as exc:
            checks.append({"name": f"bootstrap_{name}", "outcome": "failed", "required": True, "detail": str(exc)})
            ok = False
    if not ok:
        return None
    return manifest


def write_manifest(manifest: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")


def load_manifest(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except json.JSONDecodeError:
        return None
    if manifest.get("manifest_schema_version") != MANIFEST_SCHEMA_VERSION:
        return None
    if manifest.get("platform") != platform_key():
        return None
    for tool in manifest.get("tools", {}).values():
        for path_str in tool.get("binaries", {}).values():
            if not Path(path_str).is_file():
                return None
    return manifest


def tool_path(manifest: dict[str, Any] | None, tool: str, binary: str | None = None) -> Path | None:
    if manifest is None:
        return None
    entry = manifest.get("tools", {}).get(tool)
    if entry is None:
        return None
    path = entry["binaries"].get(binary or tool)
    return Path(path) if path else None
