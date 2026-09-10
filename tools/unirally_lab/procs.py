"""Bounded subprocess execution shared by every command."""

from __future__ import annotations

import os
import signal
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
    """Run a command with a hard timeout. Never raises for process failures.

    The child starts in its own session so that on timeout the whole process
    group (including grandchildren such as a test binary under ctest) is
    killed, not only the direct child.
    """
    start = time.monotonic()
    if timeout <= 0:
        return RunResult(command, None, "", f"invalid timeout {timeout}", 0.0, timed_out=True)
    posix = os.name == "posix"
    try:
        proc = subprocess.Popen(
            [str(c) for c in command],
            cwd=str(cwd) if cwd else None,
            env=env,
            stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=posix,
        )
    except (FileNotFoundError, PermissionError, NotADirectoryError) as exc:
        return RunResult(command, None, "", str(exc), time.monotonic() - start, missing=True)
    try:
        out, err = proc.communicate(stdin_text, timeout=timeout)
    except subprocess.TimeoutExpired:
        if posix:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        proc.kill()
        out, err = proc.communicate()
        return RunResult(command, None, out or "", err or "", time.monotonic() - start, timed_out=True)
    return RunResult(command, proc.returncode, out or "", err or "", time.monotonic() - start)
