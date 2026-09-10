"""Bounded subprocess execution shared by every command."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RunResult:
    command: list[str]
    returncode: int | None
    stdout: str
    stderr: str
    elapsed: float
    timed_out: bool = False
    missing: bool = False  # the executable could not be started
    env_overrides: dict[str, str] = field(default_factory=dict)

    @property
    def outcome(self) -> str:
        if self.missing:
            return "missing"
        if self.timed_out:
            return "timeout"
        return "passed" if self.returncode == 0 else "failed"

    def tail(self, limit: int = 2000) -> str:
        text = (self.stdout + ("\n" if self.stdout and self.stderr else "") + self.stderr).strip()
        return text[-limit:]


def run_bounded(
    command: list[str],
    timeout: float,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    stdin_text: str | None = None,
) -> RunResult:
    """Run a command with a hard timeout. Never raises for process failures."""
    start = time.monotonic()
    try:
        proc = subprocess.run(
            [str(c) for c in command],
            cwd=str(cwd) if cwd else None,
            env=env,
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return RunResult(command, None, out, err, time.monotonic() - start, timed_out=True)
    except (FileNotFoundError, PermissionError, NotADirectoryError) as exc:
        return RunResult(command, None, "", str(exc), time.monotonic() - start, missing=True)
    return RunResult(command, proc.returncode, proc.stdout, proc.stderr, time.monotonic() - start)
