"""Structured run reports.

A report ties check outcomes to the exact source and input state they were
observed on. Outcomes are ``passed``, ``failed``, ``skipped``, ``missing``
(a prerequisite was unavailable) or ``timeout``. Only ``passed`` counts as
success; a required check with any other outcome blocks acceptance.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from . import __version__

SCHEMA_VERSION = 1
OUTCOMES = ("passed", "failed", "skipped", "missing", "timeout")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=repo_root(), capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def source_state() -> dict[str, Any]:
    """Commit and a digest of every uncommitted change, or nulls outside Git.

    Untracked (non-ignored) files count as dirty and their contents enter the
    digest, since a new test file or source file changes results just as a
    modified tracked file does.
    """
    commit = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain", "--untracked-files=all")
    dirty_digest = None
    untracked: list[str] = []
    if status:
        digest = hashlib.sha256((_git("diff", "HEAD") or "").encode())
        for line in status.splitlines():
            if line.startswith("??"):
                rel = line[3:]
                untracked.append(rel)
                path = repo_root() / rel
                digest.update(f"\n--- untracked {rel}\n".encode())
                try:
                    digest.update(path.read_bytes())
                except OSError:
                    digest.update(b"<unreadable>")
        dirty_digest = digest.hexdigest()
    return {"commit": commit, "dirty": bool(status), "dirty_diff_sha256": dirty_digest,
            "untracked_files": untracked}


def file_sha256(path: Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


class Report:
    def __init__(self, command: list[str], task_id: str | None = None) -> None:
        self.started = time.monotonic()
        self.data: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "run_id": uuid.uuid4().hex,
            "task_id": task_id,
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "command": command,
            "source": source_state(),
            "tools": {
                "unirally_lab": __version__,
                "python": platform.python_version(),
                "platform": platform.platform(),
                "machine": platform.machine(),
            },
            "inputs": {},
            "checks": [],
            "artifacts": [],
            "elapsed_seconds": None,
            "status": None,
        }

    def add_input(self, name: str, path: Path | None, sha256: str | None, **extra: Any) -> None:
        self.data["inputs"][name] = {"path": str(path) if path else None, "sha256": sha256, **extra}

    def add_check(self, name: str, outcome: str, required: bool = True, **detail: Any) -> None:
        if outcome not in OUTCOMES:
            raise ValueError(f"unknown outcome {outcome!r}")
        self.data["checks"].append({"name": name, "outcome": outcome, "required": required, **detail})

    def add_artifact(self, kind: str, path: Path) -> None:
        self.data["artifacts"].append(
            {"kind": kind, "path": str(path), "sha256": file_sha256(path) if path.is_file() else None}
        )

    def outcomes(self) -> dict[str, int]:
        counts = {o: 0 for o in OUTCOMES}
        for c in self.data["checks"]:
            counts[c["outcome"]] += 1
        return counts

    def required_failures(self) -> list[dict[str, Any]]:
        return [c for c in self.data["checks"] if c["required"] and c["outcome"] != "passed"]

    def finish(self, status: str) -> dict[str, Any]:
        self.data["elapsed_seconds"] = round(time.monotonic() - self.started, 3)
        self.data["status"] = status
        self.data["summary"] = self.outcomes()
        return self.data

    def write(self, path: Path | None) -> None:
        if path is None:
            return
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2, sort_keys=True)
            fh.write("\n")


def print_summary(report: Report, stream=sys.stderr) -> None:
    for c in report.data["checks"]:
        flag = "required" if c["required"] else "optional"
        line = f"[{c['outcome']:>7}] {c['name']} ({flag})"
        if c.get("detail"):
            line += f": {c['detail']}"
        print(line, file=stream)
    print(f"status={report.data['status']} elapsed={report.data['elapsed_seconds']}s", file=stream)
